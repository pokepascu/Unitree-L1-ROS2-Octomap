#!/usr/bin/env python3
"""Measure the actual occupied-cell bounds published by octomap_server.

The script subscribes to the latched/transient-local MarkerArray used by RViz,
applies each marker pose to its CUBE_LIST points, expands point centers by half
of the marker scale, and writes an evidence JSON.  It does not alter the map.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from visualization_msgs.msg import Marker, MarkerArray


def quat_rotation(x: float, y: float, z: float, w: float) -> np.ndarray:
    n = math.sqrt(x * x + y * y + z * z + w * w)
    if n < 1e-12:
        return np.eye(3)
    x, y, z, w = x / n, y / n, z / n, w / n
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=float,
    )


class BoundsNode(Node):
    def __init__(self, topic: str) -> None:
        super().__init__("octomap_marker_bounds")
        qos = QoSProfile(
            depth=1,
            history=HistoryPolicy.KEEP_LAST,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.sub = self.create_subscription(MarkerArray, topic, self.cb, qos)
        self.bounds = None
        self.summary = None

    def cb(self, msg: MarkerArray) -> None:
        lows = []
        highs = []
        point_count = 0
        marker_count = 0
        namespaces = set()
        scales = set()
        frame_ids = set()
        marker_types = set()

        for marker in msg.markers:
            if marker.action in (Marker.DELETE, Marker.DELETEALL):
                continue
            if not marker.points:
                continue
            marker_count += 1
            namespaces.add(marker.ns)
            frame_ids.add(marker.header.frame_id)
            marker_types.add(int(marker.type))
            sx, sy, sz = float(marker.scale.x), float(marker.scale.y), float(marker.scale.z)
            scales.add((sx, sy, sz))
            half = np.array([sx, sy, sz], dtype=float) * 0.5

            pose = marker.pose
            R = quat_rotation(
                float(pose.orientation.x),
                float(pose.orientation.y),
                float(pose.orientation.z),
                float(pose.orientation.w),
            )
            t = np.array(
                [float(pose.position.x), float(pose.position.y), float(pose.position.z)],
                dtype=float,
            )
            pts = np.array([[float(p.x), float(p.y), float(p.z)] for p in marker.points], dtype=float)
            if pts.size == 0:
                continue
            transformed = pts @ R.T + t
            lows.append(transformed - half)
            highs.append(transformed + half)
            point_count += int(len(pts))

        if not lows:
            return
        lo = np.vstack(lows).min(axis=0)
        hi = np.vstack(highs).max(axis=0)
        center = 0.5 * (lo + hi)
        span = hi - lo
        self.bounds = (lo, hi)
        self.summary = {
            "source_topic": self.sub.topic_name,
            "frame_ids": sorted(frame_ids),
            "marker_count_with_points": marker_count,
            "occupied_cell_centers_count": point_count,
            "marker_types": sorted(marker_types),
            "marker_namespaces": sorted(namespaces),
            "marker_scales_xyz_m": [list(v) for v in sorted(scales)],
            "occupied_bounds_m": {
                "min_xyz": lo.tolist(),
                "max_xyz": hi.tolist(),
                "center_xyz": center.tolist(),
                "span_xyz": span.tolist(),
            },
            "method": "MarkerArray point centers transformed by marker pose and expanded by half marker scale",
        }
        self.get_logger().info(
            f"measured {point_count} occupied cell centers: "
            f"min={lo.tolist()} max={hi.tolist()} span={span.tolist()}"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", default="/occupied_cells_vis_array")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--timeout", type=float, default=15.0)
    args = ap.parse_args()

    rclpy.init()
    node = BoundsNode(args.topic)
    deadline = time.monotonic() + args.timeout
    try:
        while rclpy.ok() and time.monotonic() < deadline and node.summary is None:
            rclpy.spin_once(node, timeout_sec=0.25)
        if node.summary is None:
            raise RuntimeError(f"no non-empty MarkerArray received on {args.topic} within {args.timeout}s")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(node.summary, indent=2) + "\n", encoding="utf-8")
        print(args.out.read_text(encoding="utf-8"))
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
