""""
Envie um goal com o ângulo desejado (ex: 180°).
Receba e exiba o feedback (graus restantes) no terminal.
Ao final, exiba se concluiu com sucesso.
"""
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from custom_interfaces.action import RotateAngle
import sys

class ActionClientNode(Node):
    def __init__(self):
        super().__init__('rotate_action_client')
        self.action_client = ActionClient(self, RotateAngle, 'patrol_bot_action')

    def send_goal(self, degrees_remaining):
        self.get_logger().info('Sending goal...')
        goal_msg = RotateAngle.Goal()
        goal_msg.degrees_remaining = degrees_remaining

        self.action_client.wait_for_server()

        self.send_goal_future = self.action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        self.send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            return

        self.get_logger().info('Goal accepted')
        self.get_result_future = goal_handle.get_result_async()
        self.get_result_future.add_done_callback(self.get_result_callback)

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(f'Received feedback: {feedback.current_number}')

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Final Result: {result.final_count}')
        rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    action_client = ActionClientNode()
    action_client.send_goal(int(sys.argv[1]))
    rclpy.spin(action_client)