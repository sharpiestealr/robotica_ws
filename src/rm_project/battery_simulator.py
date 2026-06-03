'''
Drena ~1.0 %/s quando o robô está se movendo (|/cmd_vel.linear.x| > 0.05);
Drena ~0.1 %/s parado;
Recarrega +2.0 %/s quando está dentro de 0.5 m da charging_pose;
Bateria inicial configurável (default 100%).
'''

import os
import math
import yaml
import threading

import rclpy
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from ament_index_python.packages import get_package_share_directory

from custom_interfaces.action import GoToRoom



class BatterySimulator(Node):
    
    def __init__(self, nav: BasicNavigator, rooms_yaml: str):
        super().__init__('battery_simulator')
        self._nav = nav
        self._rooms, self._charging_pose = _get_rooms_from_yaml(rooms_yaml)
        self._battery_level = 100.0
        self._lock = threading.Lock()
        self._timer = self.create_timer(1.0, self._update_battery)
    
    def _get_rooms_from_yaml(yaml_path):
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    return data['rooms'], data['charging_pose']

    def _update_battery(self):
        with self._lock:
            # Verifica se o robô está perto da estação de recarga
            if self._is_near_charging_pose():
                self._battery_level = min(100.0, self._battery_level + 2.0)
            # Verifica se o robô está se movendo
            elif abs(self._nav.getCurrentTwist().linear.x) > 0.05:
                self._battery_level = max(0.0, self._battery_level - 1.0)
            else:
                self._battery_level = max(0.0, self._battery_level - 0.1)
        self.get_logger().info(f'Bateria: {self._battery_level:.1f}%')
        return self._battery_level
        
    def _is_near_charging_pose(self):
        current_pose = self._nav.getCurrentPose()
        dx = current_pose.pose.position.x - self._charging_pose['x']
        dy = current_pose.pose.position.y - self._charging_pose['y']
        distance = math.hypot(dx, dy)
        return distance < 0.5

    def get_battery_level(self):
        with self._lock:
            return self._battery_level
    
    def go_charge(self):
        charging_pose_stamped = PoseStamped()
        charging_pose_stamped.header.frame_id = 'map'
        charging_pose_stamped.pose.position.x = self._charging_pose['x']
        charging_pose_stamped.pose.position.y = self._charging_pose['y']
        charging_pose_stamped.pose.orientation.z = math.sin(self._charging_pose['yaw'] / 2.0)
        charging_pose_stamped.pose.orientation.w = math.cos(self._charging_pose['yaw'] / 2.0)
        self._nav.goToPose(charging_pose_stamped)
        
        if self._nav.waitUntilNav2Active():
            self.get_logger().info('Indo recarregar bateria...')
            self._nav.waitUntilNav2Idle()
            self.get_logger().info('Chegou na estação de recarga.')
        else:
            self.get_logger().error('Falha ao ativar Nav2 para recarga.')
            
        if self._busy == True:
            cancel_response = self._nav.cancelTask()
            if cancel_response:
                self.get_logger().info('Navegação atual cancelada para recarga.')
                go_charge()

def main(args=None):
    rclpy.init(args=args)
    
    # Carrega os cômodos e a posição de recarga do arquivo YAML
    pkg_share = get_package_share_directory('rm_project')
    rooms_yaml = os.path.join(pkg_share, 'config', 'rooms.yaml')
    rooms, charging_pose = _get_rooms_from_yaml(rooms_yaml)

    # Inicializa o BasicNavigator e o BatterySimulator
    nav = BasicNavigator()
    battery_simulator = BatterySimulator(nav, rooms_yaml)

    # Espera o Nav2 ficar ativo antes de começar a simular a bateria, para evitar que o robô comece a perder bateria antes de poder se mover.
    nav.get_logger().info('Aguardando Nav2 ficar ativo...')
    nav.waitUntilNav2Active()
            
            
