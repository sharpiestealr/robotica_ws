import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, LifecycleNode


def generate_launch_description():
    pkg_share = get_package_share_directory('rm_project')
    nav2_yaml = os.path.join(pkg_share, 'config', 'rooms.yaml')
    nav2_launch = os.path.join(
        get_package_share_directory('rm_navigation'), 'launch', 'navigation.launch.py')
    
    # Concierge Server
    concierge_server = Node(
        package='rm_project',
        executable='concierge_server',
        name='concierge_server',
        output='screen',
        parameters=[{'use_sim_time': True}],
    )

    return LaunchDescription([
        concierge_server,
    ])
