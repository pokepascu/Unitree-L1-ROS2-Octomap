#!/usr/bin/env bash
set -euo pipefail

require_gui="${REQUIRE_GUI:-false}"
[[ "${require_gui}" == true || "${require_gui}" == false ]] || {
  printf 'REQUIRE_GUI accepts only true or false.\n' >&2
  exit 2
}

[[ -f /.dockerenv ]] || {
  printf '%s\n' \
    'DOCKER_RUNTIME_ASSERT_FAIL: ROS 2 and RViz2 must not run on the Ubuntu 24.04 host.' >&2
  exit 40
}
[[ -r /etc/os-release ]] || {
  printf '%s\n' 'DOCKER_RUNTIME_ASSERT_FAIL: /etc/os-release is unreadable.' >&2
  exit 41
}

# shellcheck disable=SC1091
source /etc/os-release
[[ "${ID:-}" == ubuntu && "${VERSION_ID:-}" == 22.04 ]] || {
  printf 'DOCKER_RUNTIME_ASSERT_FAIL: expected Ubuntu 22.04, found %s %s.\n' \
    "${ID:-unknown}" "${VERSION_ID:-unknown}" >&2
  exit 42
}

[[ -r /opt/ros/humble/setup.bash ]] || {
  printf '%s\n' 'DOCKER_RUNTIME_ASSERT_FAIL: ROS 2 Humble setup is missing.' >&2
  exit 43
}
# shellcheck disable=SC1091
set +u
source /opt/ros/humble/setup.bash
set -u
[[ "${ROS_DISTRO:-}" == humble ]] || {
  printf 'DOCKER_RUNTIME_ASSERT_FAIL: expected ROS_DISTRO=humble, found %s.\n' \
    "${ROS_DISTRO:-unset}" >&2
  exit 44
}

ros2_path="$(command -v ros2)"
rviz2_path="$(command -v rviz2)"
[[ "${ros2_path}" == /opt/ros/humble/* ]] || {
  printf 'DOCKER_RUNTIME_ASSERT_FAIL: unexpected ros2 path: %s\n' \
    "${ros2_path}" >&2
  exit 45
}
[[ "${rviz2_path}" == /opt/ros/humble/* ]] || {
  printf 'DOCKER_RUNTIME_ASSERT_FAIL: unexpected rviz2 path: %s\n' \
    "${rviz2_path}" >&2
  exit 46
}

if [[ "${require_gui}" == true ]]; then
  [[ -n "${DISPLAY:-}" && -n "${XAUTHORITY:-}" ]] || {
    printf '%s\n' \
      'DOCKER_RUNTIME_ASSERT_FAIL: container DISPLAY or XAUTHORITY is missing.' >&2
    exit 47
  }
  [[ -r "${XAUTHORITY}" ]] || {
    printf 'DOCKER_RUNTIME_ASSERT_FAIL: container X11 cookie is unreadable: %s\n' \
      "${XAUTHORITY}" >&2
    exit 48
  }
  [[ -c /dev/dri/renderD128 ]] || {
    printf '%s\n' \
      'DOCKER_RUNTIME_ASSERT_FAIL: container GPU render device is missing.' >&2
    exit 49
  }
fi

printf 'DOCKER_ROS_RUNTIME_PASS container=%s os=ubuntu-%s ros=%s ros2=%s rviz2=%s gui=%s\n' \
  "$(hostname)" "${VERSION_ID}" "${ROS_DISTRO}" "${ros2_path}" \
  "${rviz2_path}" "${require_gui}"
