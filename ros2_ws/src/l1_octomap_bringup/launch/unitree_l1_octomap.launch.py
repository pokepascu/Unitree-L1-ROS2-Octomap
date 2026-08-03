from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Start the Unitree L1, live OctoMap, and optionally RViz2."""
    port = LaunchConfiguration("port")
    monitor = LaunchConfiguration("monitor")
    start_rviz = LaunchConfiguration("rviz")
    resolution = LaunchConfiguration("resolution")
    max_range = LaunchConfiguration("max_range")

    l1_launch = PathJoinSubstitution(
        [FindPackageShare("l1_bringup"), "launch", "unitree_l1.launch.py"]
    )
    octomap_config = PathJoinSubstitution(
        [FindPackageShare("l1_octomap_bringup"), "config", "octomap.yaml"]
    )
    rviz_config = PathJoinSubstitution(
        [FindPackageShare("l1_octomap_bringup"), "config", "l1_octomap.rviz"]
    )

    # The child launch starts the driver and optional rate monitor. Its raw
    # RViz view is disabled because this launch owns one map-oriented view.
    lidar = GroupAction(
        scoped=True,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(l1_launch),
                launch_arguments={
                    "port": port,
                    "monitor": monitor,
                    "rviz": "false",
                }.items(),
            )
        ],
    )

    octomap = Node(
        package="octomap_server",
        executable="octomap_server_node",
        name="octomap_server",
        output="screen",
        parameters=[
            octomap_config,
            {
                "resolution": ParameterValue(resolution, value_type=float),
                "sensor_model.max_range": ParameterValue(
                    max_range, value_type=float
                ),
            },
        ],
        remappings=[("cloud_in", "/unilidar/cloud")],
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="octomap_rviz2",
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
                description="Start RViz2 with the live cloud and occupied voxels.",
            ),
            DeclareLaunchArgument(
                "resolution",
                default_value="0.10",
                description="OctoMap voxel size in metres.",
            ),
            DeclareLaunchArgument(
                "max_range",
                default_value="15.0",
                description="Maximum inserted sensor range in metres.",
            ),
            octomap,
            lidar,
            rviz,
        ]
    )
