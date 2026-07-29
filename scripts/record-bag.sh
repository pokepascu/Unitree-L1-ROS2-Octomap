#!/usr/bin/env bash
set -euo pipefail

runtime_container="${RUNTIME_CONTAINER:-unitree_l1_runtime}"
label="${BAG_LABEL:-validation}"
duration="${BAG_DURATION_SEC:-0}"
[[ "${label}" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]] || {
  printf 'Invalid BAG_LABEL: %s\n' "${label}" >&2
  exit 2
}
[[ "${duration}" =~ ^[0-9]+$ ]] || {
  printf 'BAG_DURATION_SEC must be a whole number of seconds.\n' >&2
  exit 2
}
[[ "$(docker inspect -f '{{.State.Running}}' "${runtime_container}" 2>/dev/null || true)" == true ]] || {
  printf 'Runtime container is not active: %s\n' "${runtime_container}" >&2
  exit 2
}

bag_name="l1_${label}_$(date +%Y%m%d_%H%M%S)"
bag_path="/workspace/bags/${bag_name}"
printf 'Recording to %s\n' "${bag_path}"
if [[ "${duration}" == 0 ]]; then
  printf '%s\n' 'No duration set; stop cleanly with Ctrl-C.'
else
  printf 'Recording will stop cleanly after %s seconds.\n' "${duration}"
fi

exec_flags=(-i)
if [[ -t 0 && -t 1 ]]; then
  exec_flags+=(-t)
fi
docker exec "${exec_flags[@]}" \
  -e BAG_PATH="${bag_path}" -e BAG_DURATION_SEC="${duration}" \
  "${runtime_container}" bash -lc '
    /workspace/scripts/assert-ros-container.sh
    source /opt/ros/humble/setup.bash
    source /workspace/ros2_ws/install/setup.bash
    set -euo pipefail
    for topic in /unilidar/cloud /unilidar/imu; do
      timeout 15s ros2 topic echo "$topic" --once >/dev/null
    done
    topics=(/unilidar/cloud /unilidar/imu)
    available="$(ros2 topic list)"
    for optional in /diagnostics /tf /tf_static; do
      grep -Fxq "$optional" <<<"$available" && topics+=("$optional")
    done
    if [[ "$BAG_DURATION_SEC" == 0 ]]; then
      ros2 bag record --output "$BAG_PATH" "${topics[@]}"
    else
      set +e
      timeout --signal=INT --kill-after=10s "${BAG_DURATION_SEC}s" \
        ros2 bag record --output "$BAG_PATH" "${topics[@]}"
      rc=$?
      set -e
      test "$rc" -eq 0 || test "$rc" -eq 124
    fi
    ros2 bag info "$BAG_PATH"
  '
