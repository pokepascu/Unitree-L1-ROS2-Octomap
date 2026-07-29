#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HOST_UID="$(id -u)" HOST_GID="$(id -g)"

docker compose -f "${project_root}/docker/compose.yaml" run --rm dev bash -lc '
  /workspace/scripts/assert-ros-container.sh
  source /workspace/ros2_ws/install/setup.bash
  set -eo pipefail
  pids=()
  cleanup() {
    for pid in "${pids[@]}"; do kill -TERM "$pid" 2>/dev/null || true; done
    for pid in "${pids[@]}"; do wait "$pid" 2>/dev/null || true; done
  }
  trap cleanup EXIT

  ros2 run l1_monitor l1_monitor --ros-args \
    -p report_period_sec:=0.5 -p timeout_sec:=1.0 >/tmp/monitor.log 2>&1 &
  pids+=("$!")
  ros2 topic pub -r 10 /unilidar/cloud sensor_msgs/msg/PointCloud2 \
    "{header: {stamp: now, frame_id: unilidar_lidar}, height: 1, width: 4,
      fields: [{name: x, offset: 0, datatype: 7, count: 1},
               {name: y, offset: 4, datatype: 7, count: 1},
               {name: z, offset: 8, datatype: 7, count: 1}],
      is_bigendian: false, point_step: 12, row_step: 48,
      data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], is_dense: true}" \
    >/tmp/cloud-publisher.log 2>&1 &
  pids+=("$!")
  ros2 topic pub -r 30 /unilidar/imu sensor_msgs/msg/Imu \
    "{header: {stamp: now, frame_id: unilidar_imu}}" \
    >/tmp/imu-publisher.log 2>&1 &
  pids+=("$!")

  sleep 5
  timeout 10s ros2 topic echo /diagnostics \
    diagnostic_msgs/msg/DiagnosticArray --once >/tmp/diagnostics.txt
  cat /tmp/monitor.log
  grep -E "level:|name: unitree_l1/|message:|key: point_count|key: fields|value:" \
    /tmp/diagnostics.txt
  test "$(grep -c "message: stream healthy" /tmp/diagnostics.txt)" -eq 2
  grep -A1 "key: point_count" /tmp/diagnostics.txt | grep -q "value: .4."
  grep -A1 "key: fields" /tmp/diagnostics.txt | grep -q "x,y,z"
  printf "%s\n" MONITOR_SYNTHETIC_HEALTH_PASS
'
