#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"

docker compose -f "${project_root}/docker/compose.yaml" run --rm dev \
  bash -lc 'set -euo pipefail
    /workspace/scripts/assert-ros-container.sh
    test "$ROS_DISTRO" = humble
    grep -q "VERSION_ID=\"22.04\"" /etc/os-release
    command -v ros2
    command -v colcon
    command -v rviz2
    ros2 pkg prefix unitree_lidar_ros2
    ros2 pkg executables unitree_lidar_ros2 | grep -q unitree_lidar_ros2_node
    ros2 pkg executables l1_monitor | grep -q "l1_monitor l1_monitor"
    ros2 launch l1_bringup unitree_l1.launch.py --show-args
    ldd /workspace/ros2_ws/install/unitree_lidar_ros2/lib/unitree_lidar_ros2/unitree_lidar_ros2_node
    ros2 interface show sensor_msgs/msg/PointCloud2 >/dev/null
    printf "%s\n" "SMOKE_TEST_PASS"'
