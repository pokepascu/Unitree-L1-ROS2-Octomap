import ast
import importlib.util
from pathlib import Path

from launch import LaunchDescription, LaunchService
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.launch_description_source import LaunchDescriptionSource


def test_launch_file_is_valid_python_and_exposes_expected_interface():
    launch_file = Path(__file__).parents[1] / "launch" / "l1_octomap.launch.py"
    text = launch_file.read_text(encoding="utf-8")

    ast.parse(text)
    for argument in (
        "cloud_topic",
        "world_frame",
        "lidar_frame",
        "resolution",
        "max_range",
        "static_sensor",
        "rviz",
    ):
        assert f'DeclareLaunchArgument(\n                "{argument}"' in text

    assert 'package="octomap_server"' in text
    assert 'executable="octomap_server_node"' in text
    assert 'remappings=[("cloud_in", cloud_topic)]' in text
    assert 'package="tf2_ros"' in text
    assert 'package="rviz2"' in text
    assert '"config", "l1_octomap.rviz"' in text
    assert "BENCH USE ONLY" in text
    assert 'Path("/.dockerenv").is_file()' in text
    assert "Docker-only project" in text


def test_combined_launch_includes_driver_and_octomap():
    launch_file = (
        Path(__file__).parents[1] / "launch" / "unitree_l1_octomap.launch.py"
    )
    text = launch_file.read_text(encoding="utf-8")

    ast.parse(text)
    assert 'FindPackageShare("l1_bringup")' in text
    assert '"monitor": "true"' in text
    assert '"rviz": "false"' in text
    assert 'FindPackageShare("l1_octomap_bringup")' in text
    assert '"LIDAR_PORT", default_value="/dev/unitree_lidar"' in text
    assert 'package="rviz2"' in text
    assert '"config", "l1_octomap.rviz"' in text
    assert "/occupied_cells_vis_array" in text
    assert text.count("GroupAction(") == 2
    assert text.count("scoped=True") == 2
    assert text.count('"rviz": "false"') == 2


def test_combined_launch_scopes_child_rviz_arguments():
    launch_file = (
        Path(__file__).parents[1] / "launch" / "unitree_l1_octomap.launch.py"
    )
    text = launch_file.read_text(encoding="utf-8")

    assert "cannot overwrite" in text
    assert text.index("start_l1 = GroupAction(") < text.index("rviz_node = Node(")
    assert text.index("start_octomap = GroupAction(") < text.rindex("rviz_node,")


def test_combined_rviz_value_survives_both_included_launches(monkeypatch):
    launch_file = (
        Path(__file__).parents[1] / "launch" / "unitree_l1_octomap.launch.py"
    )
    spec = importlib.util.spec_from_file_location(
        "combined_rviz_scope_test", launch_file
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    child_values = []
    parent_values = []

    def record_child(context):
        child_values.append(context.launch_configurations["rviz"])
        return []

    def stub_launch_source(_location):
        return LaunchDescriptionSource(
            launch_description=LaunchDescription(
                [
                    DeclareLaunchArgument("rviz", default_value="false"),
                    OpaqueFunction(function=record_child),
                ]
            )
        )

    def stub_parent_node(**kwargs):
        def record_parent(context):
            parent_values.append(context.launch_configurations["rviz"])
            return []

        return OpaqueFunction(
            function=record_parent,
            condition=kwargs.get("condition"),
        )

    monkeypatch.setattr(
        module, "PythonLaunchDescriptionSource", stub_launch_source
    )
    monkeypatch.setattr(module, "Node", stub_parent_node)

    service = LaunchService(noninteractive=True)
    service.context.launch_configurations["rviz"] = "true"
    service.include_launch_description(module.generate_launch_description())

    assert service.run() == 0
    assert child_values == ["false", "false"]
    assert parent_values == ["true"]
    assert service.context.launch_configurations["rviz"] == "true"


def test_rviz_profile_shows_cloud_and_octomap_in_map_frame():
    rviz_file = Path(__file__).parents[1] / "config" / "l1_octomap.rviz"
    text = rviz_file.read_text(encoding="utf-8")

    assert "Fixed Frame: map" in text
    assert "Class: rviz_default_plugins/PointCloud2" in text
    assert "Value: /unilidar/cloud" in text
    assert "Class: rviz_default_plugins/MarkerArray" in text
    assert "Value: /occupied_cells_vis_array" in text
    assert "Durability Policy: Transient Local" in text


def test_saved_map_launch_and_rviz_profile():
    package_root = Path(__file__).parents[1]
    launch_text = (
        package_root / "launch" / "view_saved_octomap.launch.py"
    ).read_text(encoding="utf-8")
    rviz_text = (package_root / "config" / "saved_octomap.rviz").read_text(
        encoding="utf-8"
    )

    ast.parse(launch_text)
    assert '"octomap_path": map_path' in launch_text
    assert 'executable="octomap_server_node"' in launch_text
    assert 'Path("/.dockerenv").is_file()' in launch_text
    assert '"config",\n            "saved_octomap.rviz"' in launch_text
    assert "Fixed Frame: map" in rviz_text
    assert "Class: rviz_default_plugins/MarkerArray" in rviz_text
    assert "Value: /occupied_cells_vis_array" in rviz_text
    assert "Class: rviz_default_plugins/PointCloud2" not in rviz_text
