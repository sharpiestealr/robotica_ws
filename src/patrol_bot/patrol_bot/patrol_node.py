import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from custom_interfaces.action import RotateAngle
import sys
import time

class ActionClient(Node):
    def __init__(self):
        super().__init__('patrol_bot_srv_server')
        self.srv_server = self.create_service(SetBool, 'start_patrol', self.srv_callback)
        self.subscription = self.create_subscription(LaserScan, 'scan', self.subscription_callback, 10)
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.action_client = ActionClient(self, RotateAngle, 'rotate')

    def srv_callback(self, request, response):
        response.success = False
        if (request.data):
            response.success = True
        return response
    
    def subscription_callback(self, msg):
        start_time = time.perf_counter()
        distancia = msg.range_min        
        if (distancia >= 0.5): 
            while (time.perf_counter()-start_time > 2):
                msg = Twist()
                msg.angular.z = 0.5
                self.publisher.publish(msg)
        self.get_logger().info(f'Orientação: {self.orientacao:.3f}')
        
    def timer_callback(self):
        msg = Twist()
        msg.linear.x = 0
        if (self.srv_server): msg.linear.x = 0.5
        self.publisher.publish(msg)
        self.get_logger().info(f'Velocidade: {msg.linear.x:.2f}')
        
    def send_goal(self, count_up_to):
        self.get_logger().info('Sending goal...')
        goal_msg = Aula10.Goal()
        goal_msg.count_up_to = count_up_to

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
    
    estado = 'idle'
    
    match estado:
        case 'idle':
            node = ActionClient()
            estado = 'anda frente'
        case 'anda frente':
             node.timer = node.create_timer(0.5, node.timer_callback)
             estado = 'verifica obstaculo'  
        case 'verifica obstaculo':
            node.subscription = node.create_subscription(LaserScan, 'scan', node.subscription_callback, 10)
            node.get_logger().info('Verificando obstáculos...')
            estado = 'gira'
        case 'gira':
            node.action_client = ActionClient(node, RotateAngle, 'rotate')
            node.send_goal(90)
            estado = 'anda frente'     
    
    srv_server = SrvServer()
    srv_server.send_goal(int(sys.argv[1]))
    rclpy.spin(srv_server)
    node.destroy_node()
    rclpy.shutdown()