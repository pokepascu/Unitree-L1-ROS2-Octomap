from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Start the Unitree driver and optionally its rate view and RViz2."""
    port = LaunchConfiguration("port")
    start_monitor = LaunchConfiguration("monitor")
    start_rviz = LaunchConfiguration("rviz")

    package_share = FindPackageShare("l1_bringup")
    driver_config = PathJoinSubstitution(
        [package_share, "config", "unitree_l1.yaml"]
    )
    rviz_config = PathJoinSubstitution(
        [package_share, "config", "unitree_l1.rviz"]
    )

    driver = Node(
        package="unitree_lidar_ros2",
        executable="unitree_lidar_ros2_node",
        name="unitree_lidar_ros2_node",
        output="screen",
        parameters=[driver_config, {"port": port}],
    )

    # This is the standard ROS 2 CLI rate display, not a custom node/package.
    cloud_rate = ExecuteProcess(
        cmd=["ros2", "topic", "hz", "/unilidar/cloud"],
        output="screen",
        emulate_tty=True,
        condition=IfCondition(start_monitor),
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config],
        output="screen",
        condition=IfCondition(start_rviz),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "port",
                default_value="/dev/unitree_lidar",
                description="Serial device path inside the container.",
            ),
            DeclareLaunchArgument(
                "monitor",
                default_value="true",
                choices=["true", "false"],
                description="Print /unilidar/cloud frequency with ros2 topic hz.",
            ),
            DeclareLaunchArgument(
                "rviz",
                default_value="true",
                choices=["true", "false"],
                description="Start RViz2 with the L1 point-cloud view.",
            ),
            driver,
            cloud_rate,
            rviz,
        ]
    )
