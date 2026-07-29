#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
"${project_root}/scripts/fetch-dependencies.sh"

docker compose -f "${project_root}/docker/compose.yaml" run --rm dev \
  bash -lc 'set -euo pipefail
    /workspace/scripts/assert-ros-container.sh
    cd /workspace/ros2_ws
    rosdep install \
      --from-paths src/l1_bringup src/l1_monitor src/l1_octomap_bringup \
        src/octomap_mapping \
        src/unilidar_sdk/unitree_lidar_ros2 \
      --ignore-src --rosdistro humble \
      --skip-keys "ament_python pcl" -r -y
    colcon build \
      --base-paths src/l1_bringup src/l1_monitor src/l1_octomap_bringup \
        src/octomap_mapping \
        src/unilidar_sdk/unitree_lidar_ros2 \
      --symlink-install --event-handlers console_cohesion+'
