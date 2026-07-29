from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def _require_docker_runtime():
    """Refuse a direct ROS launch on the Ubuntu host."""
    if not Path("/.dockerenv").is_file():
        raise RuntimeError(
            "Docker-only project: launch through scripts/octomap-launch.sh."
        )


def generate_launch_description():
    """Launch OctoMap for an existing Unitree L1 PointCloud2 stream."""
    _require_docker_runtime()
    cloud_topic = LaunchConfiguration("cloud_topic")
    world_frame = LaunchConfiguration("world_frame")
    lidar_frame = LaunchConfiguration("lidar_frame")
    resolution = LaunchConfiguration("resolution")
    max_range = LaunchConfiguration("max_range")
    static_sensor = LaunchConfiguration("static_sensor")
    start_rviz = LaunchConfiguration("rviz")

    default_config = PathJoinSubstitution(
        [FindPackageShare("l1_octomap_bringup"), "config", "octomap.yaml"]
    )
    rviz_config = PathJoinSubstitution(
        [FindPackageShare("l1_octomap_bringup"), "config", "l1_octomap.rviz"]
    )

    static_transform = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="l1_static_lidar_transform",
        arguments=[
            "--x",
            "0",
            "--y",
            "0",
            "--z",
            "0",
            "--roll",
            "0",
            "--pitch",
            "0",
            "--yaw",
            "0",
            "--frame-id",
            world_frame,
            "--child-frame-id",
            lidar_frame,
        ],
        output="screen",
        condition=IfCondition(static_sensor),
    )

    octomap_server = Node(
        package="octomap_server",
        executable="octomap_server_node",
        name="octomap_server",
        output="screen",
        parameters=[
            default_config,
            {
                "frame_id": world_frame,
                "base_frame_id": lidar_frame,
                "resolution": ParameterValue(resolution, value_type=float),
                "sensor_model.max_range": ParameterValue(
                    max_range, value_type=float
                ),
            },
        ],
        remappings=[("cloud_in", cloud_topic)],
    )
    rviz_node = Node(
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
                "cloud_topic",
                default_value="/unilidar/cloud",
                description="Input sensor_msgs/PointCloud2 topic.",
            ),
            DeclareLaunchArgument(
                "world_frame",
                default_value="map",
                description="World frame in which OctoMap accumulates observations.",
            ),
            DeclareLaunchArgument(
                "lidar_frame",
                default_value="unilidar_lidar",
                description="Frame carried by the Unitree L1 point cloud.",
            ),
            DeclareLaunchArgument(
                "resolution",
                default_value="0.10",
                description="OctoMap voxel size in metres.",
            ),
            DeclareLaunchArgument(
                "max_range",
                default_value="15.0",
                description="Maximum sensor ray length in metres.",
            ),
            DeclareLaunchArgument(
                "static_sensor",
                default_value="true",
                choices=["true", "false"],
                description=(
                    "Publish a bench-only identity transform from world to lidar. "
                    "Disable this on a moving robot and provide pose TF externally."
                ),
            ),
            DeclareLaunchArgument(
                "rviz",
                default_value="false",
                choices=["true", "false"],
                description="Open the live cloud and occupied-voxel profile.",
            ),
            LogInfo(
                condition=IfCondition(static_sensor),
                msg=[
                    "[l1_octomap_bringup] static_sensor=true: publishing identity "
                    "TF ",
                    world_frame,
                    " -> ",
                    lidar_frame,
                    ". BENCH USE ONLY; this transform is invalid if the sensor "
                    "or robot moves.",
                ],
            ),
            LogInfo(
                condition=UnlessCondition(static_sensor),
                msg=[
                    "[l1_octomap_bringup] static_sensor=false: expecting an "
                    "external time-varying TF from ",
                    world_frame,
                    " to ",
                    lidar_frame,
                    ".",
                ],
            ),
            static_transform,
            octomap_server,
            rviz_node,
        ]
    )
