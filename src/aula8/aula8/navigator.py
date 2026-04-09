import rclpy
from rclpy.node import Node
from custom_interfaces.msg import Aula8
import time

class Publisher(Node):
    def __init__(self):
        super().__init__('aula8_publisher')
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.subscription = self.create_subscription(LaserScan, 'scan', self.subscription_callback, 10)
        self.srv_server = self.create_service(std_srvs/srv/SetBool, '/start_navigation', self.srv_callback)
        self.timer = self.create_timer(1.0, self.timer_callback)
     
    def estado(status):
        match status:
            case 1:
                self.timer_callback()
            case 2:
                self.subscription_callback()
            case 3:
                self.girar()
            case _:
                msg = Twist()
                msg.linear.x = 0
                self.publisher.publish(msg)
        
    def timer_callback(self):
        msg = Twist()
        msg.linear.x = 0.5
        self.publisher.publish(msg)        

    def subscription_callback(self, msg):
        start_time = time.perf_counter()
        distancia = msg.range_min        
        if (distancia >= 0.5): 
            while (time.perf_counter()-start_time > 2):
                status = 3
        else:
            status = 1
        return status
        
    def girar(self):
        msg = Twist()
        msg.angular.z = 0.5
        self.publisher.publish(msg)
    
def main(args=None):
    rclpy.init(args=args)
    publisher = Publisher()
    rclpy.spin(publisher)
    publisher.destroy_node()
    rclpy.shutdown()