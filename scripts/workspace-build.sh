#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"

assert_clean_source_tree() {
  local forbidden_output
  forbidden_output="$(
    find "${project_root}/ros2_ws/src" -mindepth 1 \
      \( -name build -o -name install -o -name log \) -print -quit
  )"
  [[ -z "${forbidden_output}" ]] || {
    printf 'Refusing to build while generated output exists inside src: %s\n' \
      "${forbidden_output}" >&2
    printf '%s\n' \
      'Remove the accidental output and run this script from the repository root.' >&2
    exit 3
  }
}

assert_clean_source_tree

"${project_root}/scripts/fetch-dependencies.sh"
assert_clean_source_tree

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
      --symlink-install --event-handlers console_cohesion+
    test -z "$(
      find src -mindepth 1 \
        \( -name build -o -name install -o -name log \) -print -quit
    )"'
