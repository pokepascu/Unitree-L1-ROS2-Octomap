from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    LogInfo,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EnvironmentVariable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Launch the Unitree L1 driver, monitor, and OctoMap as one ROS graph."""
    port = LaunchConfiguration("port")
    cloud_topic = LaunchConfiguration("cloud_topic")
    world_frame = LaunchConfiguration("world_frame")
    lidar_frame = LaunchConfiguration("lidar_frame")
    resolution = LaunchConfiguration("resolution")
    max_range = LaunchConfiguration("max_range")
    static_sensor = LaunchConfiguration("static_sensor")
    start_rviz = LaunchConfiguration("rviz")

    l1_launch = PathJoinSubstitution(
        [FindPackageShare("l1_bringup"), "launch", "unitree_l1.launch.py"]
    )
    octomap_launch = PathJoinSubstitution(
        [
            FindPackageShare("l1_octomap_bringup"),
            "launch",
            "l1_octomap.launch.py",
        ]
    )
    rviz_config = PathJoinSubstitution(
        [FindPackageShare("l1_octomap_bringup"), "config", "l1_octomap.rviz"]
    )

    # Both included launch files declare an argument named "rviz". Keep their
    # forced false values in scoped contexts so they cannot overwrite the
    # combined launch's public rviz argument before rviz_node is evaluated.
    start_l1 = GroupAction(
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(l1_launch),
                launch_arguments={
                    "port": port,
                    "cloud_topic": cloud_topic,
                    "cloud_frame": lidar_frame,
                    "monitor": "true",
                    "rviz": "false",
                }.items(),
            )
        ],
        scoped=True,
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config],
        output="screen",
        condition=IfCondition(start_rviz),
    )
    start_octomap = GroupAction(
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(octomap_launch),
                launch_arguments={
                    "cloud_topic": cloud_topic,
                    "world_frame": world_frame,
                    "lidar_frame": lidar_frame,
                    "resolution": resolution,
                    "max_range": max_range,
                    "static_sensor": static_sensor,
                    "rviz": "false",
                }.items(),
            )
        ],
        scoped=True,
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "port",
                default_value=EnvironmentVariable(
                    "LIDAR_PORT", default_value="/dev/unitree_lidar"
                ),
                description="Serial device exposed inside the Docker container.",
            ),
            DeclareLaunchArgument(
                "cloud_topic",
                default_value="/unilidar/cloud",
                description="PointCloud2 topic shared by the driver and OctoMap.",
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
                    "Use a bench-only identity world-to-lidar TF. Set false on a "
                    "moving robot and provide its pose TF externally."
                ),
            ),
            DeclareLaunchArgument(
                "rviz",
                default_value="false",
                choices=["true", "false"],
                description="Open the L1 cloud and OctoMap RViz profile.",
            ),
            LogInfo(
                condition=IfCondition(start_rviz),
                msg=(
                    "[l1_octomap_bringup] RViz uses Fixed Frame 'map' and shows "
                    "/unilidar/cloud plus the /occupied_cells_vis_array "
                    "OctoMap markers. Markers appear after OctoMap receives cloud "
                    "data with a valid map-to-lidar TF."
                ),
            ),
            start_l1,
            start_octomap,
            rviz_node,
        ]
    )
