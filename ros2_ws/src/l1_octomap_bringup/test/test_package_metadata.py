from pathlib import Path
from xml.etree import ElementTree


def test_package_has_runtime_dependencies_without_driver_coupling():
    package_file = Path(__file__).parents[1] / "package.xml"
    root = ElementTree.parse(package_file).getroot()
    dependencies = {item.text for item in root.findall("exec_depend")}

    assert {
        "launch",
        "launch_ros",
        "l1_bringup",
        "octomap_server",
        "rviz2",
        "tf2_ros",
    } <= dependencies
    assert "unitree_lidar_ros2" not in dependencies
