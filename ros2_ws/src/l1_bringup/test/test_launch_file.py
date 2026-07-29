from pathlib import Path


def test_launch_file_exposes_serial_port():
    launch_file = Path(__file__).parents[1] / "launch" / "unitree_l1.launch.py"
    text = launch_file.read_text(encoding="utf-8")
    assert 'DeclareLaunchArgument(\n                "port"' in text
    assert 'LaunchConfiguration("port")' in text
    assert 'EnvironmentVariable(\n                    "LIDAR_PORT"' in text
    assert 'LaunchConfiguration("monitor")' in text
    assert 'package="l1_monitor"' in text
    assert 'Path("/.dockerenv").is_file()' in text
    assert "Docker-only project" in text
