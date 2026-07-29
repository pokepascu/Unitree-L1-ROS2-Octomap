#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_container="${RUNTIME_CONTAINER:-unitree_l1_runtime}"
stamp="$(date +%Y%m%d_%H%M%S)"
log_file="${project_root}/logs/tests/lidar-validation-${stamp}.log"

[[ "$(docker inspect -f '{{.State.Running}}' "${runtime_container}" 2>/dev/null || true)" == true ]] || {
  printf 'Runtime container is not active: %s\n' "${runtime_container}" >&2
  printf '%s\n' 'Start ./scripts/lidar-launch.sh in another terminal.' >&2
  exit 2
}

printf 'Validation output will be retained in %s\n' "${log_file}"
docker exec "${runtime_container}" bash -lc '
  /workspace/scripts/assert-ros-container.sh
  source /opt/ros/humble/setup.bash
  source /workspace/ros2_ws/install/setup.bash
  set -eo pipefail

  ros2 node list
  ros2 topic list -t
  ros2 param get /unitree_lidar_ros2_node port
  ros2 topic info -v /unilidar/cloud
  ros2 topic info -v /unilidar/imu

  for specification in "/unilidar/cloud sensor_msgs/msg/PointCloud2" \
                       "/unilidar/imu sensor_msgs/msg/Imu"; do
    read -r topic expected_type <<<"$specification"
    actual_type="$(ros2 topic type "$topic")"
    test "$actual_type" = "$expected_type"
    timeout 15s ros2 topic echo "$topic" "$expected_type" --once >/dev/null
    printf "MESSAGE_PASS topic=%s type=%s\n" "$topic" "$actual_type"
  done

  for topic in /unilidar/cloud /unilidar/imu; do
    set +e
    output="$(PYTHONUNBUFFERED=1 timeout --signal=INT --kill-after=3s 12s \
      ros2 topic hz "$topic" 2>&1)"
    rc=$?
    set -e
    printf "%s\n" "$output"
    test "$rc" -eq 124 || test "$rc" -eq 0
    grep -q "average rate:" <<<"$output"
    printf "RATE_PASS topic=%s\n" "$topic"
  done

  timeout 10s ros2 topic echo /diagnostics \
    diagnostic_msgs/msg/DiagnosticArray --once
  printf "%s\n" LIDAR_DATA_VALIDATION_PASS
' 2>&1 | tee "${log_file}"
