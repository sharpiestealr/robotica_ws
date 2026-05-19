from unittest import case

import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from custom_interfaces.action import RotateAngle
from custom_interfaces.action import GoToRoom
import sys
import time
from rooms.yaml import rooms

class ActionServer(Node):
    def __init__(self):
        super().__init__('projeto_srv_server')
        self.srv_server = self.create_service(SetBool, 'busy', self.srv_callback)
        self.subscription = self.create_subscription(LaserScan, 'scan', self.subscription_callback, 10)
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.action_server = ActionServer(self, Aula10, 'aula10_action', self.my_action_callback)

    def my_action_callback(self, goal_handle):
        self.get_logger().info('Executing goal...')

        count_up_to = goal_handle.request.count_up_to
        current_number = 0

        while current_number < count_up_to:

            feedback_msg = Aula10.Feedback()
            feedback_msg.current_number = current_number
            goal_handle.publish_feedback(feedback_msg)
            self.get_logger().info(f'Publishing feedback: {current_number}')

            current_number += 1

            time.sleep(1)

        goal_handle.succeed()
        result = Aula10.Result()
        result.final_count = current_number
        self.get_logger().info('Goal succeeded!')
        return result

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
            self.orientacao = msg.twist.twist.angular.z
        
        self.get_logger().info(f'Orientação: {self.orientacao:.3f}')
        self.get_logger().info(f'Velocidade: {msg.angular.z:.2f}')

        
    def timer_callback(self):
        msg = Twist()
        msg.linear.x = 0
        if (self.srv_server): msg.linear.x = 0.5
        self.publisher.publish(msg)
        self.get_logger().info(f'Velocidade: {msg.linear.x:.2f}')
        
    def send_goal(self):
        self.get_logger().info('Sending goal...')
        goal_msg = GoToRoom.Goal()
        goal_msg.room_name = self.room

        self.action_client.wait_for_server()

        self.send_goal_future = self.action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        self.send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if self.room not in rooms:
            self.get_logger().info('Goal rejected: sala inválida ou não existe')
            return
        elif self.busy == True:
            self.get_logger().info('Goal rejected: já existe uma entrega em andamento')
            return

        self.get_logger().info('Goal accepted')
        self.get_result_future = goal_handle.get_result_async()
        self.get_result_future.add_done_callback(self.get_result_callback)

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(f'Fase: {feedback.phase}\nMetros até {self.room}: {feedback.distance_remaining}')
        if feedback.distance_remaining > 0: self.busy = True

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Missão: {result.success} - {result.message}')
        rclpy.shutdown()

def main(args=None):    
    """ estado = 'idle'
    
    match estado:
        case 'idle':
            node = ActionClient()
            node.busy = False
            estado = 'espera ordem'
        case 'espera ordem':
            node.room = rooms[input('Para onde vai o robô?')]
            estado = 'anda frente'
        case 'anda frente':
             node.timer = node.create_timer(0.5, node.timer_callback)
             node.feedback_callback()
             if feedback.distance_remaining > 0: estado = 'verifica obstaculo'  
             else: estado = 'idle'
        case 'verifica obstaculo':
            node.subscription = node.create_subscription(LaserScan, 'scan', node.subscription_callback, 10)
            node.get_logger().info('Verificando obstáculos...')
            node.feedback_callback()
            estado = 'gira'
        case 'gira':
            node.action_client = ActionClient(node, RotateAngle, 'rotate')
            node.send_goal()
            node.feedback_callback()
            estado = 'anda frente'  """    
            
    rclpy.init(args=args)
    action_server = ActionServerNode()
    rclpy.spin(action_server)
    rclpy.shutdown()
    
    class ActionServerNode(Node):
    def __init__(self):
        super().__init__('aula10_action_server')

    def my_action_callback(self, goal_handle):
        self.get_logger().info('Executing goal...')

        count_up_to = goal_handle.request.count_up_to
        current_number = 0

        while current_number < count_up_to:

            feedback_msg = Aula10.Feedback()
            feedback_msg.current_number = current_number
            goal_handle.publish_feedback(feedback_msg)
            self.get_logger().info(f'Publishing feedback: {current_number}')

            current_number += 1

            time.sleep(1)

        goal_handle.succeed()
        result = Aula10.Result()
        result.final_count = current_number
        self.get_logger().info('Goal succeeded!')
        return result
