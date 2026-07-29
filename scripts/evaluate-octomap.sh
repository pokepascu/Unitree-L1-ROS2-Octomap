#!/usr/bin/env bash
set -euo pipefail

runtime_container="${RUNTIME_CONTAINER:-unitree_l1_runtime}"

[[ "${runtime_container}" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]+$ ]] || {
  printf 'Invalid RUNTIME_CONTAINER name: %s\n' "${runtime_container}" >&2
  exit 2
}
[[ "$(docker inspect -f '{{.State.Running}}' "${runtime_container}" 2>/dev/null || true)" == true ]] || {
  printf 'Runtime container is not active: %s\n' "${runtime_container}" >&2
  exit 3
}

docker exec "${runtime_container}" bash -lc '
  /workspace/scripts/assert-ros-container.sh
  source /opt/ros/humble/setup.bash
  source /workspace/ros2_ws/install/setup.bash
  set -euo pipefail

  nodes="$(ros2 node list)"
  printf "%s\n" "${nodes}" | grep -Fxq /octomap_server
  if printf "%s\n" "${nodes}" | grep -Fxq /l1_static_lidar_transform; then
    mode=stationary_bench_mapping
  elif printf "%s\n" "${nodes}" | grep -Fxq /unitree_lidar_ros2_node; then
    mode=mobile_mapping_external_pose_required
  else
    mode=saved_map_replay
  fi
  printf "mapping_mode=%s\n" "${mode}"

  python3 - <<PY
import time

import rclpy
from octomap_msgs.msg import Octomap
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from visualization_msgs.msg import MarkerArray

rclpy.init()
node = rclpy.create_node("octomap_self_evaluation")
qos = QoSProfile(depth=1)
qos.reliability = ReliabilityPolicy.RELIABLE
qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
markers_received = []
maps_received = []


def marker_callback(message):
    markers_received.append(message)


def map_callback(message):
    maps_received.append(message)


node.create_subscription(
    MarkerArray, "/occupied_cells_vis_array", marker_callback, qos
)
node.create_subscription(Octomap, "/octomap_binary", map_callback, qos)
deadline = time.monotonic() + 10.0
while time.monotonic() < deadline and not (markers_received and maps_received):
    rclpy.spin_once(node, timeout_sec=0.25)

if not markers_received:
    raise SystemExit("OCTOMAP_EVALUATION_FAIL missing_marker_array")
if not maps_received:
    raise SystemExit("OCTOMAP_EVALUATION_FAIL missing_binary_map")

markers = markers_received[-1].markers
occupied_markers = sum(1 for marker in markers if marker.points)
occupied_points = sum(len(marker.points) for marker in markers)
map_message = maps_received[-1]
if occupied_markers < 1 or occupied_points < 1 or len(map_message.data) < 1:
    raise SystemExit("OCTOMAP_EVALUATION_FAIL empty_map")

frames = sorted({marker.header.frame_id for marker in markers if marker.header.frame_id})
frame_text = ",".join(frames)
print(
    "OCTOMAP_MAPPING_HEALTH_PASS "
    f"markers={len(markers)} occupied_markers={occupied_markers} "
    f"occupied_points={occupied_points} resolution_m={map_message.resolution} "
    f"binary_payload_bytes={len(map_message.data)} "
    f"map_id={map_message.id} frames={frame_text}"
)
node.destroy_node()
rclpy.shutdown()
PY
'

printf '%s\n' \
  'This health check validates non-empty mapping output; it does not measure SLAM trajectory accuracy.'
