#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ $# -eq 1 ]] || {
  printf 'Usage: START_RVIZ=true %s bags/<bag-directory>\n' "$0" >&2
  exit 2
}
bag_host="$(realpath -e -- "${1}")"
case "${bag_host}" in
  "${project_root}/bags/"*) ;;
  *) printf 'Bag must be inside %s/bags.\n' "${project_root}" >&2; exit 2 ;;
esac
test -f "${bag_host}/metadata.yaml"
bag_container="/workspace/bags/${bag_host#"${project_root}/bags/"}"
start_rviz="${START_RVIZ:-true}"
[[ "${start_rviz}" == true || "${start_rviz}" == false ]]
export HOST_UID="$(id -u)" HOST_GID="$(id -g)" START_RVIZ="${start_rviz}"
compose_files=(-f "${project_root}/docker/compose.yaml")
if [[ "${start_rviz}" == true ]]; then
  : "${DISPLAY:?DISPLAY is required when START_RVIZ=true}"
  : "${XAUTHORITY:?XAUTHORITY is required when START_RVIZ=true}"
  test -r "${XAUTHORITY}"
  export VIDEO_GID="$(stat -Lc '%g' /dev/dri/card0)"
  export RENDER_GID="$(stat -Lc '%g' /dev/dri/renderD128)"
  compose_files+=(-f "${project_root}/docker/compose.gui.yaml")
fi

docker compose "${compose_files[@]}" run --rm \
  -e BAG_PATH="${bag_container}" -e START_RVIZ="${start_rviz}" \
  -e REQUIRE_GUI="${start_rviz}" \
  dev bash -lc '
    set -e
    /workspace/scripts/assert-ros-container.sh
    monitor_pid=""
    rviz_pid=""
    cleanup() {
      [[ -z "$monitor_pid" ]] || kill -TERM "$monitor_pid" 2>/dev/null || true
      [[ -z "$rviz_pid" ]] || kill -TERM "$rviz_pid" 2>/dev/null || true
      [[ -z "$monitor_pid" ]] || wait "$monitor_pid" 2>/dev/null || true
      [[ -z "$rviz_pid" ]] || wait "$rviz_pid" 2>/dev/null || true
    }
    trap cleanup EXIT
    ros2 run l1_monitor l1_monitor --ros-args -p use_sim_time:=true & monitor_pid=$!
    if [[ "$START_RVIZ" == true ]]; then
      rviz_config="$(ros2 pkg prefix --share l1_bringup)/config/unitree_l1.rviz"
      rviz2 -d "$rviz_config" --ros-args -p use_sim_time:=true & rviz_pid=$!
    fi
    sleep 2
    ros2 bag play "$BAG_PATH" --clock
  '
