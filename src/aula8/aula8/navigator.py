
import rclpy # biblioteca principal do ROS2 para Python.
from rclpy.node import Node # classe base para criar nós ROS2.

# Definição do nó
class Publisher(Node):
    def __init__(self):
        super().__init__('aula8_publisher') #inicializa o nó com o nome aula8_publisher.
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10) 
        self.subscription = self.create_subscription(LaserScan, 'scan', self.subscription_callback, 10)
        self.timer = self.create_timer(1.0, self.timer_callback) # chama timer_callback a cada 1 segundo.
    
        
def subscription_callback(self, dist):
    dist = LaserScan()
    distancia_min = dist.range_min
    
def timer_callback(self, vel, distancia_min):
    vel = Twist()
    vel.linear.x = 0.03
    if dist.range_min < 0.5:
        self.contador += 1
        if self.contador <= 10:
            vel.linear.x = 0
            vel.angular.z = 0.05
        else:
            self.contador = 0
            vel.linear.x = 0.03
    else:
        vel.linear.x = 0.03
        
    self.publisher.publish(vel)