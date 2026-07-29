#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
map_name=""
check_only=false

usage() {
  printf 'Usage: %s MAP_NAME.bt|MAP_NAME.ot [--check]\n' "$0"
}

while (($#)); do
  case "$1" in
    --check) check_only=true ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      if [[ -n "${map_name}" ]]; then
        usage >&2
        exit 2
      fi
      map_name="$1"
      ;;
  esac
  shift
done

[[ -n "${map_name}" ]] || {
  usage >&2
  exit 2
}
"${project_root}/scripts/inspect-octomap.sh" "${map_name}"

viewer_container="${MAP_VIEWER_CONTAINER:-unitree_l1_map_viewer}"
viewer_domain="${MAP_VIEWER_ROS_DOMAIN_ID:-43}"
start_rviz="${MAP_VIEWER_RVIZ:-true}"

[[ "${viewer_container}" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]+$ ]] || {
  printf 'Invalid MAP_VIEWER_CONTAINER name: %s\n' "${viewer_container}" >&2
  exit 2
}
[[ "${viewer_domain}" =~ ^[0-9]+$ ]] && ((viewer_domain <= 232)) || {
  printf 'MAP_VIEWER_ROS_DOMAIN_ID must be an integer from 0 to 232.\n' >&2
  exit 2
}
[[ "${start_rviz}" == true || "${start_rviz}" == false ]] || {
  printf 'MAP_VIEWER_RVIZ accepts only true or false.\n' >&2
  exit 2
}

if [[ "${check_only}" == true ]]; then
  printf 'VIEW_OCTOMAP_CHECK_PASS map=%s domain=%s rviz=%s\n' \
    "${map_name}" "${viewer_domain}" "${start_rviz}"
  exit 0
fi

if docker container inspect "${viewer_container}" >/dev/null 2>&1; then
  printf 'Viewer container name already exists: %s\n' "${viewer_container}" >&2
  printf '%s\n' 'Inspect and stop the earlier viewer before retrying.' >&2
  exit 3
fi

export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
compose_files=(-f "${project_root}/docker/compose.yaml")

if [[ "${start_rviz}" == true ]]; then
  : "${DISPLAY:?DISPLAY is required for RViz2}"
  : "${XAUTHORITY:?XAUTHORITY is required for RViz2}"
  [[ -r "${XAUTHORITY}" ]] || {
    printf 'X11 cookie is not readable: %s\n' "${XAUTHORITY}" >&2
    exit 3
  }
  [[ -c /dev/dri/card0 && -c /dev/dri/renderD128 ]] || {
    printf '%s\n' 'Required DRI devices are absent.' >&2
    exit 3
  }
  export VIDEO_GID="$(stat -Lc '%g' /dev/dri/card0)"
  export RENDER_GID="$(stat -Lc '%g' /dev/dri/renderD128)"
  compose_files+=(-f "${project_root}/docker/compose.gui.yaml")
fi

docker compose "${compose_files[@]}" config --quiet
printf 'VIEW_SAVED_OCTOMAP_READY map=%s domain=%s rviz=%s\n' \
  "${map_name}" "${viewer_domain}" "${start_rviz}"
printf '%s\n' 'Press Ctrl-C to close the saved-map server and RViz2.'

exec docker compose "${compose_files[@]}" run --rm \
  --name "${viewer_container}" \
  -e ROS_DOMAIN_ID="${viewer_domain}" \
  -e OCTOMAP_PATH="/workspace/maps/${map_name}" \
  -e START_RVIZ="${start_rviz}" \
  -e REQUIRE_GUI="${start_rviz}" \
  dev bash -lc '
    /workspace/scripts/assert-ros-container.sh
    source /opt/ros/humble/setup.bash
    source /workspace/ros2_ws/install/setup.bash
    set -euo pipefail
    exec ros2 launch l1_octomap_bringup view_saved_octomap.launch.py \
      map_path:="${OCTOMAP_PATH}" rviz:="${START_RVIZ}"
  '
