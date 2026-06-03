#!/usr/bin/env python3
"""Battery simulator for a Nav2-based robot.

Behavior:
- drains 1.0 %/s while the robot is moving (|cmd_vel.linear.x| > 0.05)
- drains 0.1 %/s while the robot is standing still
- charges 2.0 %/s when it is within 0.5 m of the charging hub
- when battery <= 20%, cancels the active route and drives to the charging hub

Expected YAML format (same file can also contain rooms for concierge_server.py):

charging_pose:
  x: 1.0
  y: 2.0
  yaw: 0.0
"""

from __future__ import annotations

import math
import os
import threading
from typing import Optional

import yaml

import rclpy
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, Twist
from std_msgs.msg import Float32, String
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from ament_index_python.packages import get_package_share_directory


LOW_BATTERY_THRESHOLD = 20.0
CHARGE_RADIUS_M = 0.5
MOVING_THRESHOLD = 0.05
MOVING_DRAIN_PER_S = 1.0
IDLE_DRAIN_PER_S = 0.1
CHARGE_PER_S = 2.0


def _load_charging_pose(yaml_path: str) -> dict:
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

    if 'charging_pose' not in data:
        raise KeyError(
            f"Missing 'charging_pose' in {yaml_path}. Expected keys: x, y, optional yaw."
        )

    pose = data['charging_pose']
    return {
        'x': float(pose['x']),
        'y': float(pose['y']),
        'yaw': float(pose.get('yaw', 0.0)),
    }


def _make_pose(nav: BasicNavigator, x: float, y: float, yaw: float = 0.0) -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = nav.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.orientation.w = math.cos(yaw / 2.0)
    return pose


class BatterySimulator(Node):
    def __init__(
        self,
        nav: BasicNavigator,
        charging_pose: dict,
        initial_battery: float = 100.0,
        low_battery_threshold: float = LOW_BATTERY_THRESHOLD,
        charge_radius_m: float = CHARGE_RADIUS_M,
        moving_threshold: float = MOVING_THRESHOLD,
    ):
        super().__init__('battery_simulator')
        self._nav = nav
        self._charging_pose = charging_pose
        self._low_battery_threshold = float(low_battery_threshold)
        self._charge_radius_m = float(charge_radius_m)
        self._moving_threshold = float(moving_threshold)

        self._battery_level = float(initial_battery)
        self._lock = threading.Lock()
        self._last_update_time = self.get_clock().now()

        self._latest_pose: Optional[PoseWithCovarianceStamped] = None
        self._latest_cmd_vel: Optional[Twist] = None

        self._mode = 'normal'  # normal | returning_to_charge | charging
        self._charging_goal_sent = False

        self._pose_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self._on_pose,
            10,
        )
        self._cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self._on_cmd_vel,
            10,
        )

        self._battery_pub = self.create_publisher(Float32, '/battery_level', 10)
        self._state_pub = self.create_publisher(String, '/battery_state', 10)

        self._timer = self.create_timer(0.2, self._tick)

        self.get_logger().info(
            f'Battery simulator started. Initial battery={self._battery_level:.1f}%, '
            f'low-battery threshold={self._low_battery_threshold:.1f}%, '
            f'charging hub={self._charging_pose}'
        )

    def _on_pose(self, msg: PoseWithCovarianceStamped) -> None:
        with self._lock:
            self._latest_pose = msg

    def _on_cmd_vel(self, msg: Twist) -> None:
        with self._lock:
            self._latest_cmd_vel = msg

    def _get_battery(self) -> float:
        with self._lock:
            return self._battery_level

    def _set_battery(self, value: float) -> None:
        with self._lock:
            self._battery_level = max(0.0, min(100.0, value))

    def _get_current_pose(self) -> Optional[PoseWithCovarianceStamped]:
        with self._lock:
            return self._latest_pose

    def _get_current_cmd_vel(self) -> Optional[Twist]:
        with self._lock:
            return self._latest_cmd_vel

    def _distance_to_charging_hub(self) -> Optional[float]:
        pose = self._get_current_pose()
        if pose is None:
            return None
        dx = pose.pose.pose.position.x - self._charging_pose['x']
        dy = pose.pose.pose.position.y - self._charging_pose['y']
        return math.hypot(dx, dy)

    def _is_moving(self) -> bool:
        cmd_vel = self._get_current_cmd_vel()
        if cmd_vel is None:
            return False
        return abs(cmd_vel.linear.x) > self._moving_threshold

    def _send_charging_goal(self) -> None:
        charging_pose = _make_pose(
            self._nav,
            self._charging_pose['x'],
            self._charging_pose['y'],
            self._charging_pose.get('yaw', 0.0),
        )
        self._nav.goToPose(charging_pose)
        self._charging_goal_sent = True
        self._mode = 'returning_to_charge'
        self.get_logger().warn(
            f'Battery low ({self._battery_level:.1f}%). '
            f'Cancelling current task and driving to charging hub.'
        )

    def _arrived_at_charger(self, distance: Optional[float]) -> bool:
        return distance is not None and distance <= self._charge_radius_m

    def _tick(self) -> None:
        now = self.get_clock().now()
        dt = (now - self._last_update_time).nanoseconds / 1e9
        if dt <= 0.0:
            return
        self._last_update_time = now

        battery_before = self._get_battery()
        distance = self._distance_to_charging_hub()

        # Trigger the charging mission once the battery crosses the threshold.
        if (
            self._mode == 'normal'
            and battery_before <= self._low_battery_threshold
            and not self._charging_goal_sent
        ):
            self._nav.cancelTask()
            self._send_charging_goal()

        # If we are already returning and get close enough, stop the route and start charging.
        if self._mode == 'returning_to_charge' and self._arrived_at_charger(distance):
            if not self._nav.isTaskComplete():
                self._nav.cancelTask()
            self._mode = 'charging'
            self.get_logger().info('Charging hub reached (within 0.5 m). Starting recharge.')

        # Battery update rule.
        if self._mode == 'charging' or self._arrived_at_charger(distance):
            delta = CHARGE_PER_S * dt
        elif self._is_moving():
            delta = -MOVING_DRAIN_PER_S * dt
        else:
            delta = -IDLE_DRAIN_PER_S * dt

        self._set_battery(battery_before + delta)
        battery_after = self._get_battery()

        # If we are not charging yet, but crossed the threshold on this tick, request charging now.
        if (
            self._mode == 'normal'
            and battery_after <= self._low_battery_threshold
            and not self._charging_goal_sent
        ):
            self._nav.cancelTask()
            self._send_charging_goal()

        # If we are charging and the battery is full, go back to normal mode.
        if self._mode == 'charging' and battery_after >= 100.0:
            self._mode = 'normal'
            self._charging_goal_sent = False
            self.get_logger().info('Battery fully recharged.')

        self._publish_state()

    def _publish_state(self) -> None:
        battery_msg = Float32()
        battery_msg.data = self._get_battery()
        self._battery_pub.publish(battery_msg)

        state_msg = String()
        state_msg.data = self._mode
        self._state_pub.publish(state_msg)

        self.get_logger().info(f'Battery: {battery_msg.data:.1f}% | mode={state_msg.data}')

    def request_return_to_charger(self) -> None:
        """Optional external trigger if another node wants to force charging."""
        if self._charging_goal_sent:
            return
        self._nav.cancelTask()
        self._send_charging_goal()


def main(args=None):
    rclpy.init(args=args)

    pkg_share = get_package_share_directory('rm_project')
    rooms_yaml = os.path.join(pkg_share, 'config', 'rooms.yaml')
    charging_pose = _load_charging_pose(rooms_yaml)

    nav = BasicNavigator()
    nav.get_logger().info('Waiting for Nav2 to become active...')
    nav.waitUntilNav2Active()

    battery_simulator = BatterySimulator(nav, charging_pose)

    executor = MultiThreadedExecutor()
    executor.add_node(nav)
    executor.add_node(battery_simulator)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        battery_simulator.destroy_node()
        nav.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
