#!/usr/bin/env bash
set -euo pipefail

runtime_container="${RUNTIME_CONTAINER:-unitree_l1_runtime}"
static_sensor="${STATIC_SENSOR:-true}"
start_rviz="${OCTOMAP_RVIZ:-false}"
check_only=false

case "${1:-}" in
  "") ;;
  --check) check_only=true ;;
  *)
    printf 'Usage: %s [--check]\n' "$0" >&2
    exit 2
    ;;
esac

[[ "${runtime_container}" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]+$ ]] || {
  printf 'Invalid RUNTIME_CONTAINER name: %s\n' "${runtime_container}" >&2
  exit 2
}
[[ "${static_sensor}" == true || "${static_sensor}" == false ]] || {
  printf 'STATIC_SENSOR accepts only true or false.\n' >&2
  exit 2
}
[[ "${start_rviz}" == true || "${start_rviz}" == false ]] || {
  printf 'OCTOMAP_RVIZ accepts only true or false.\n' >&2
  exit 2
}

[[ "$(docker inspect -f '{{.State.Running}}' "${runtime_container}" 2>/dev/null || true)" == true ]] || {
  printf 'Runtime container is not active: %s\n' "${runtime_container}" >&2
  printf '%s\n' 'Start it with START_RVIZ=true ./scripts/lidar-launch.sh.' >&2
  exit 3
}

docker exec -e REQUIRE_GUI="${start_rviz}" "${runtime_container}" bash -lc '
  /workspace/scripts/assert-ros-container.sh
  source /opt/ros/humble/setup.bash
  source /workspace/ros2_ws/install/setup.bash
  set -euo pipefail
  test "$(ros2 pkg prefix l1_octomap_bringup)" = \
    /workspace/ros2_ws/install/l1_octomap_bringup
  if ros2 node list | grep -Fxq /octomap_server; then
    printf "%s\n" "OctoMap is already running in this ROS graph." >&2
    exit 4
  fi
'

printf 'OCTOMAP_LAUNCH_READY container=%s static_sensor=%s rviz=%s\n' \
  "${runtime_container}" "${static_sensor}" "${start_rviz}"
if [[ "${check_only}" == true ]]; then
  printf '%s\n' OCTOMAP_LAUNCH_CHECK_PASS
  exit 0
fi

if [[ "${static_sensor}" == true ]]; then
  printf '%s\n' 'Starting bench OctoMap; keep the L1 stationary and press Ctrl-C to stop.'
else
  printf '%s\n' 'Starting mobile OctoMap; a dynamic map-to-lidar TF is required. Press Ctrl-C to stop.'
fi
docker_options=()
if [[ -t 0 && -t 1 ]]; then
  docker_options=(-it)
fi

exec docker exec "${docker_options[@]}" \
  -e STATIC_SENSOR="${static_sensor}" \
  -e START_RVIZ="${start_rviz}" \
  -e REQUIRE_GUI="${start_rviz}" \
  "${runtime_container}" bash -lc '
    /workspace/scripts/assert-ros-container.sh
    source /opt/ros/humble/setup.bash
    source /workspace/ros2_ws/install/setup.bash
    set -euo pipefail
    exec ros2 launch l1_octomap_bringup l1_octomap.launch.py \
      static_sensor:="${STATIC_SENSOR}" rviz:="${START_RVIZ}"
  '
