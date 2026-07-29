from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _require_docker_runtime():
    """Refuse a direct ROS launch on the Ubuntu host."""
    if not Path("/.dockerenv").is_file():
        raise RuntimeError(
            "Docker-only project: launch through scripts/view-octomap.sh."
        )


def generate_launch_description():
    """Load one saved OctoMap and optionally display it in RViz2."""
    _require_docker_runtime()
    map_path = LaunchConfiguration("map_path")
    frame_id = LaunchConfiguration("frame_id")
    start_rviz = LaunchConfiguration("rviz")

    octomap_config = PathJoinSubstitution(
        [FindPackageShare("l1_octomap_bringup"), "config", "octomap.yaml"]
    )
    rviz_config = PathJoinSubstitution(
        [
            FindPackageShare("l1_octomap_bringup"),
            "config",
            "saved_octomap.rviz",
        ]
    )

    map_server = Node(
        package="octomap_server",
        executable="octomap_server_node",
        name="octomap_server",
        output="screen",
        parameters=[
            octomap_config,
            {
                "octomap_path": map_path,
                "frame_id": frame_id,
                "base_frame_id": frame_id,
            },
        ],
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="saved_octomap_rviz2",
        arguments=["-d", rviz_config],
        output="screen",
        condition=IfCondition(start_rviz),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "map_path",
                description="Absolute container path to a .bt or .ot map.",
            ),
            DeclareLaunchArgument(
                "frame_id",
                default_value="map",
                description="Fixed frame stored on the published map topics.",
            ),
            DeclareLaunchArgument(
                "rviz",
                default_value="true",
                choices=["true", "false"],
                description="Open the saved-map RViz2 profile.",
            ),
            LogInfo(msg=["Loading saved OctoMap: ", map_path]),
            map_server,
            rviz_node,
        ]
    )
