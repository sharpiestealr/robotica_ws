import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    # Aqui agnt chama o gazebo_casa
    robot_simulator = IncludeLaunchDescription( # Roda o gazebo_casa.launch.py
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('rm_description'),
                'launch',
                'robot_simulation.launch.py'
            )
        )
    )
 # aqui agnt fz o no
    navigator_node = Node(
        package='aula8',
        executable='navigator',
        name='aula8_navigator',
        output='screen',
    )

    return LaunchDescription([
        robot_simulator,# chama o gazebo
        navigator_node, # chama o no
    ])
