from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import (
    EnvironmentVariable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _require_docker_runtime():
    """Refuse a direct ROS launch on the Ubuntu host."""
    if not Path("/.dockerenv").is_file():
        raise RuntimeError(
            "Docker-only project: launch through scripts/lidar-launch.sh."
        )


def generate_launch_description():
    _require_docker_runtime()
    port = LaunchConfiguration("port")
    cloud_topic = LaunchConfiguration("cloud_topic")
    imu_topic = LaunchConfiguration("imu_topic")
    cloud_frame = LaunchConfiguration("cloud_frame")
    imu_frame = LaunchConfiguration("imu_frame")
    start_rviz = LaunchConfiguration("rviz")
    start_monitor = LaunchConfiguration("monitor")

    default_config = PathJoinSubstitution(
        [FindPackageShare("l1_bringup"), "config", "unitree_l1.yaml"]
    )
    rviz_config = PathJoinSubstitution(
        [FindPackageShare("l1_bringup"), "config", "unitree_l1.rviz"]
    )

    lidar_node = Node(
        package="unitree_lidar_ros2",
        executable="unitree_lidar_ros2_node",
        name="unitree_lidar_ros2_node",
        output="screen",
        parameters=[
            default_config,
            {
                "port": port,
                "cloud_topic": cloud_topic,
                "imu_topic": imu_topic,
                "cloud_frame": cloud_frame,
                "imu_frame": imu_frame,
            },
        ],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config],
        output="screen",
        condition=IfCondition(start_rviz),
    )

    monitor_node = Node(
        package="l1_monitor",
        executable="l1_monitor",
        name="l1_monitor",
        output="screen",
        parameters=[
            default_config,
            {
                "cloud_topic": cloud_topic,
                "imu_topic": imu_topic,
            },
        ],
        condition=IfCondition(start_monitor),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "port",
                default_value=EnvironmentVariable(
                    "LIDAR_PORT", default_value="/dev/ttyUSB0"
                ),
                description="Serial device exposed to the container.",
            ),
            DeclareLaunchArgument(
                "cloud_topic",
                default_value="unilidar/cloud",
                description="PointCloud2 topic name.",
            ),
            DeclareLaunchArgument(
                "imu_topic",
                default_value="unilidar/imu",
                description="IMU topic name.",
            ),
            DeclareLaunchArgument(
                "cloud_frame",
                default_value="unilidar_lidar",
                description="Point cloud frame_id.",
            ),
            DeclareLaunchArgument(
                "imu_frame",
                default_value="unilidar_imu",
                description="IMU frame_id.",
            ),
            DeclareLaunchArgument(
                "rviz",
                default_value="false",
                choices=["true", "false"],
                description="Start RViz2 with the Unitree view.",
            ),
            DeclareLaunchArgument(
                "monitor",
                default_value="true",
                choices=["true", "false"],
                description="Start the read-only L1 diagnostics monitor.",
            ),
            lidar_node,
            monitor_node,
            rviz_node,
        ]
    )
