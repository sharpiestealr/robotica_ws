#!/usr/bin/env python3
"""Concierge server that remembers interrupted navigation goals.

Behavior:
- accepts GoToRoom action goals as before
- stores the active room target while navigation is in progress
- if Nav2 is canceled because the battery node sends the robot to charge,
  the server waits for the battery to report 'normal' again and then
  reissues the same goal automatically
"""

from __future__ import annotations

import math
import os
import threading
import time
from typing import Any, Dict, Optional

import yaml

import rclpy
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32, String
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from ament_index_python.packages import get_package_share_directory

from custom_interfaces.action import GoToRoom


BATTERY_NORMAL_STATE = 'normal'
BATTERY_RETURNING_STATE = 'returning_to_charge'
BATTERY_CHARGING_STATE = 'charging'


def _make_pose(nav: BasicNavigator, x: float, y: float, yaw: float = 0.0) -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = nav.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.orientation.w = math.cos(yaw / 2.0)
    return pose


def _load_rooms_from_yaml(yaml_path: str) -> Dict[str, Dict[str, float]]:
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

    rooms = data.get('rooms', {})
    if not isinstance(rooms, dict):
        raise TypeError(f'Expected "rooms" to be a mapping in {yaml_path}')
    return rooms


class ConciergeServer(Node):
    def __init__(self, nav: BasicNavigator, rooms: dict):
        super().__init__('concierge_server')
        self._nav = nav
        self._rooms = rooms
        self._busy = False
        self._lock = threading.Lock()

        self._active_goal_name: Optional[str] = None
        self._active_target: Optional[Dict[str, float]] = None
        self._paused_goal_name: Optional[str] = None
        self._paused_target: Optional[Dict[str, float]] = None
        self._battery_state = BATTERY_NORMAL_STATE
        self._battery_level = 100.0

        cb_group = ReentrantCallbackGroup()
        self._action_server = ActionServer(
            self,
            GoToRoom,
            '/concierge/go_to_room',
            execute_callback=self._execute_cb,
            goal_callback=self._goal_cb,
            cancel_callback=self._cancel_cb,
            callback_group=cb_group,
        )

        self._battery_state_sub = self.create_subscription(
            String,
            '/battery_state',
            self._on_battery_state,
            10,
        )
        self._battery_level_sub = self.create_subscription(
            Float32,
            '/battery_level',
            self._on_battery_level,
            10,
        )

        self.get_logger().info(
            f'Concierge pronto. Cômodos disponíveis: {list(self._rooms.keys())}'
        )

    def _on_battery_state(self, msg: String) -> None:
        with self._lock:
            previous = self._battery_state
            self._battery_state = msg.data

            if (
                previous in {BATTERY_RETURNING_STATE, BATTERY_CHARGING_STATE}
                and msg.data == BATTERY_NORMAL_STATE
                and self._paused_goal_name is not None
                and self._paused_target is not None
            ):
                self.get_logger().info('Bateria carregada. Retomando rota.')

    def _on_battery_level(self, msg: Float32) -> None:
        with self._lock:
            self._battery_level = float(msg.data)

    def _goal_cb(self, goal_request):
        room_name = goal_request.room_name
        with self._lock:
            if room_name not in self._rooms:
                self.get_logger().warn(
                    f'Cômodo desconhecido: "{room_name}". Cômodos disponíveis: {list(self._rooms.keys())}'
                )
                return GoalResponse.REJECT
            if self._busy:
                self.get_logger().warn('Já existe uma entrega em andamento.')
                return GoalResponse.REJECT

            self._busy = True
            self._active_goal_name = room_name
            self._active_target = dict(self._rooms[room_name])
            self._paused_goal_name = None
            self._paused_target = None

        return GoalResponse.ACCEPT

    def _cancel_cb(self, goal_handle):
        self.get_logger().info('Cancelamento solicitado pelo cliente.')
        self._nav.cancelTask()
        return CancelResponse.ACCEPT

    def _wait_for_battery_to_be_normal(self) -> None:
        while rclpy.ok():
            with self._lock:
                battery_state = self._battery_state
                battery_level = self._battery_level

            if battery_state == BATTERY_NORMAL_STATE and battery_level >= 99.5:
                return
            time.sleep(0.2)

    def _send_goal_to_room(self, room_name: str, room: Dict[str, float]) -> None:
        target = _make_pose(self._nav, room['x'], room['y'], room.get('yaw', 0.0))
        self._nav.goToPose(target)
        self.get_logger().info(f'Navegando para "{room_name}" -> {room}')

    def _execute_cb(self, goal_handle):
        room_name = goal_handle.request.room_name
        room = self._rooms[room_name]

        feedback_msg = GoToRoom.Feedback()
        feedback_msg.phase = 'Indo_para_o_cômodo'

        with self._lock:
            self._active_goal_name = room_name
            self._active_target = dict(room)

        while rclpy.ok():
            self._send_goal_to_room(room_name, room)

            while rclpy.ok() and not self._nav.isTaskComplete():
                nav_fb = self._nav.getFeedback()
                if nav_fb is not None:
                    feedback_msg.distance_remaining = float(nav_fb.distance_remaining)
                    goal_handle.publish_feedback(feedback_msg)
                time.sleep(0.05)

            nav_result = self._nav.getResult()
            if nav_result == TaskResult.SUCCEEDED:
                self.get_logger().info(f'Chegou em "{room_name}".')
                result = GoToRoom.Result()
                result.success = True
                result.message = f'Chegou em {room_name} com sucesso.'
                goal_handle.succeed()
                with self._lock:
                    self._busy = False
                    self._active_goal_name = None
                    self._active_target = None
                    self._paused_goal_name = None
                    self._paused_target = None
                return result

            if nav_result == TaskResult.CANCELED:
                with self._lock:
                    battery_state = self._battery_state
                    battery_level = self._battery_level
                    self._paused_goal_name = self._active_goal_name
                    self._paused_target = dict(self._active_target) if self._active_target else None

                if battery_state in {BATTERY_RETURNING_STATE, BATTERY_CHARGING_STATE} or battery_level <= 20.0:
                    self.get_logger().warn(
                        'Navegação interrompida. Aguardando a bateria carregar para retomar a rota.'
                    )
                    self._wait_for_battery_to_be_normal()
                    continue

                self.get_logger().warn('Navegação cancelada.')
                result = GoToRoom.Result()
                result.success = False
                result.message = 'Navegação cancelada.'
                goal_handle.canceled()
                with self._lock:
                    self._busy = False
                    self._active_goal_name = None
                    self._active_target = None
                    self._paused_goal_name = None
                    self._paused_target = None
                return result

            self.get_logger().error('Navegação falhou.')
            result = GoToRoom.Result()
            result.success = False
            result.message = 'Navegação falhou.'
            goal_handle.abort()
            with self._lock:
                self._busy = False
                self._active_goal_name = None
                self._active_target = None
                self._paused_goal_name = None
                self._paused_target = None
            return result

        result = GoToRoom.Result()
        result.success = False
        result.message = 'Execução interrompida.'
        goal_handle.abort()
        with self._lock:
            self._busy = False
            self._active_goal_name = None
            self._active_target = None
            self._paused_goal_name = None
            self._paused_target = None
        return result


def main(args=None):
    rclpy.init(args=args)

    pkg_share = get_package_share_directory('rm_project')
    rooms_yaml = os.path.join(pkg_share, 'config', 'rooms.yaml')
    rooms = _load_rooms_from_yaml(rooms_yaml)

    nav = BasicNavigator()
    server = ConciergeServer(nav, rooms)

    nav.get_logger().info('Aguardando Nav2 ficar ativo...')
    nav.waitUntilNav2Active()
    server.get_logger().info(
        f'Nav2 ativo. Concierge pronto para receber goals. Cômodos disponíveis: {list(server._rooms.keys())}'
    )

    executor = MultiThreadedExecutor()
    executor.add_node(nav)
    executor.add_node(server)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        server.destroy_node()
        nav.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
