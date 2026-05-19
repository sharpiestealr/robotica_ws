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

class ActionClient(Node):
    def __init__(self):
        self.action_client = ActionClient(self, RotateAngle, 'rotate')
        self.go_to_room_client = ActionClient(self, GoToRoom, 'go_to_room')