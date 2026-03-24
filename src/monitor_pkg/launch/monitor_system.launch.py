from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    publisher_node = Node(
        package='monitor_pkg',
        executable='publisher',
        name='ai_publisher',
        output='screen',
    )

    subscriber_node = Node(
        package='monitor_pkg',
        executable='subscriber',
        name='ai_subscriber',
        output='screen',
    )
    
    service_node = Node(
        package='monitor_pkg',
        executable='service server',
        name='ai_publisher',
        output='screen',
    )

    return LaunchDescription([
        publisher_node,
        subscriber_node,
        service_node,
    ])