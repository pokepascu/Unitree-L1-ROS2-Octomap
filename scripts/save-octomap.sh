#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_container="${RUNTIME_CONTAINER:-unitree_l1_runtime}"
map_name="${1:-l1_octomap_$(date +%Y%m%d_%H%M%S).bt}"

[[ "${runtime_container}" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]+$ ]] || {
  printf 'Invalid RUNTIME_CONTAINER name: %s\n' "${runtime_container}" >&2
  exit 2
}
[[ "${map_name}" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*\.(bt|ot)$ ]] || {
  printf 'Map name must contain only safe characters and end in .bt or .ot: %s\n' \
    "${map_name}" >&2
  exit 2
}

map_host="${project_root}/maps/${map_name}"
map_container="/workspace/maps/${map_name}"
[[ "${map_host}" != */../* ]] || {
  printf 'Refusing a map path outside the project maps directory.\n' >&2
  exit 2
}
[[ "$(docker inspect -f '{{.State.Running}}' "${runtime_container}" 2>/dev/null || true)" == true ]] || {
  printf 'Runtime container is not active: %s\n' "${runtime_container}" >&2
  printf '%s\n' 'Start the L1 + OctoMap launch before saving a map.' >&2
  exit 2
}

mkdir -p "${project_root}/maps"
[[ ! -e "${map_host}" ]] || {
  printf 'Map file already exists; choose a new name: %s\n' "${map_host}" >&2
  exit 3
}
printf 'Requesting OctoMap save to %s\n' "${map_host}"

docker exec -e MAP_CONTAINER="${map_container}" "${runtime_container}" bash -lc '
  /workspace/scripts/assert-ros-container.sh
  source /opt/ros/humble/setup.bash
  source /workspace/ros2_ws/install/setup.bash
  set -euo pipefail
  ros2 service list | grep -Fxq /octomap_binary
  ros2 run octomap_server octomap_saver_node --ros-args \
    -p octomap_path:="${MAP_CONTAINER}"
'

test -s "${map_host}" || {
  printf 'OctoMap saver returned without a non-empty file: %s\n' "${map_host}" >&2
  exit 1
}
printf 'OCTOMAP_SAVE_PASS file=%s bytes=%s\n' \
  "${map_host}" "$(stat -c '%s' "${map_host}")"
