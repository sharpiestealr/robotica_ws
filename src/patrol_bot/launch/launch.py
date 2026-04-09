import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():

    xacro_file = "robot.urdf.xacro"
    description_package_name = "rm_description"
    description_package_path = os.path.join(get_package_share_directory(description_package_name))
    xacro_file_path = os.path.join(description_package_path, 'urdf', xacro_file)

    # convert XACRO file into URDF
    doc = xacro.parse(open(xacro_file_path))
    xacro.process_doc(doc)
    params = {'robot_description': doc.toxml(), 'use_sim_time': True}

    # Include the Gazebo launch file, provided by the gazebo_ros package
    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')]),
            )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[params]
    )

    # RVIZ Configuration
    rviz_config_dir = os.path.join(get_package_share_directory(description_package_name), 'rviz', 'robot_vis.rviz')
    rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            output='screen',
            name='rviz_node',
            parameters=[{'use_sim_time': True}],
            arguments=['-d', rviz_config_dir]
        )
    
    spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py',
                        arguments=['-entity', 'rm', '-x', '0.0', '-y', '0.0', '-z', '0.2',
                                '-topic', 'robot_description'],
                        output='screen')
    
    
    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        rviz_node,
        spawn_entity,
    ])

