import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup

from custom_interfaces.action import RotateAngle
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist

import time

class ActionServerNode(Node):
    def __init__(self):
        super().__init__('patrol_bot_node')

        self.subscriber_group = MutuallyExclusiveCallbackGroup()
        self.main_group = MutuallyExclusiveCallbackGroup()

        # Publisher + Timer (Thread 2)
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(1.0, self.timer_callback, callback_group=self.main_group)

        # Subscriber (Thread 1)
        self.subscription = self.create_subscription(Odometry, 'odom', self.subscription_callback, 10, callback_group=self.subscriber_group)

        # Action Server (Thread 2)
        self.action_server = ActionServer(self, RotateAngle, 'rotate', self.my_action_callback, callback_group=self.main_group)

        self.orientacao = 0.0

    # -------------------------
    # THREAD 1
    # -------------------------
    def subscription_callback(self, msg):
        self.orientacao = msg.twist.twist.angular.z
        self.get_logger().info(f'Orientação: {self.orientacao:.3f}')

    # -------------------------
    # THREAD 2
    # -------------------------
    def timer_callback(self):
        msg = Twist()
        msg.angular.z = 0.5
        self.publisher.publish(msg)
        self.get_logger().info(f'Velocidade: {msg.angular.z:.2f}')

    # -------------------------
    # THREAD 2
    # -------------------------
    def my_action_callback(self, goal_handle):
        self.get_logger().info('Executing goal...')

        degrees = goal_handle.request.degrees
        success = False

        while rclpy.ok():
            current_angle = self.orientacao

            if current_angle >= degrees:
                success = True
                break

            feedback_msg = RotateAngle.Feedback()
            feedback_msg.degrees_remaining = degrees - current_angle
            goal_handle.publish_feedback(feedback_msg)

            self.get_logger().info(f'Remaining: {feedback_msg.degrees_remaining:.2f}')

            time.sleep(0.5)

        goal_handle.succeed()

        result = RotateAngle.Result()
        result.success = success

        self.get_logger().info('Goal succeeded!')
        return result

def main(args=None):
    rclpy.init(args=args)

    node = ActionServerNode()

    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)

    try:
        executor.spin()
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()