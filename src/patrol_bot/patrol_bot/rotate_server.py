import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from custom_interfaces.action import RotateAngle
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
import time

class ActionServerNode(Node):
    def __init__(self):
        super().__init__('rotate_action_server')
        self.action_server = ActionServer(
            self,
            RotateAngle,
            'patrol_bot_action',
            self.my_action_callback
        )
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10) 
        self.subscription = self.create_subscription(Odometry, 'odom', self.subscription_callback, 10)

    def subscription_callback(self, dist):
        yaw = twist.angular.z
        self.yaw = yaw
        self.get_logger().info('Yaw: "%i"' % (yaw)) # bota no terminal
        
    def timer_callback(self, vel, distancia_min):
        vel = Twist()
        vel.angular.z = 0.5
        self.publisher.publish(vel)
        self.get_logger().info('Velocidade: "%i"' % (msg.angular.z))
        
    def my_action_callback(self, goal_handle):
        self.get_logger().info('Executing goal...')

        degrees = goal_handle.request.degrees
        current_angle = self.yaw

        while (current_angle < degrees):
            if current_angle == degrees:
                succes = True
                break
            
            self.create_timer(1.0, self.timer_callback)
              
            feedback_msg = RotateAngle.Feedback()
            feedback_msg.degrees_remaining = degrees_remaining
            goal_handle.publish_feedback(feedback_msg)
            self.get_logger().info(f'Publishing feedback: {degrees_remaining}')

            current_angle = msg.twist.angular.z

            time.sleep(1)

        goal_handle.succeed()
        result = RotateAngle.Result()
        result.success = success
        self.get_logger().info('Goal succeeded!')
        return result
        
def main(args=None):
    rclpy.init(args=args)
    action_server = ActionServerNode()
    rclpy.spin(action_server)
    rclpy.shutdown()