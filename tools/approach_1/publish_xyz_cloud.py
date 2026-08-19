#!/usr/bin/env python3
"""Publish a cleaned XYZ cloud in deterministic chunks as sensor_msgs/PointCloud2.

This is used only for derived Approach-1 OctoMap construction. The source
rosbag remains unchanged. Each cleaned point is published once from the
unilidar_lidar sensor origin so OctoMap can integrate occupied endpoints and
free-space rays without repeatedly overweighting the same accumulated cloud.
"""
import argparse
import time
from pathlib import Path

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import Header


def cloud_msg(points: np.ndarray, frame_id: str, stamp) -> PointCloud2:
    xyz = np.asarray(points, dtype=np.float32)
    if not xyz.flags['C_CONTIGUOUS']:
        xyz = np.ascontiguousarray(xyz)
    msg = PointCloud2()
    msg.header = Header(stamp=stamp, frame_id=frame_id)
    msg.height = 1
    msg.width = int(len(xyz))
    msg.fields = [
        PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
        PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
        PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
    ]
    msg.is_bigendian = False
    msg.point_step = 12
    msg.row_step = msg.point_step * msg.width
    msg.data = xyz[:, :3].tobytes(order='C')
    msg.is_dense = True
    return msg


class Publisher(Node):
    def __init__(self, topic: str):
        super().__init__('cleaned_static_cloud_publisher')
        self.pub = self.create_publisher(PointCloud2, topic, 10)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xyz', required=True)
    ap.add_argument('--topic', default='/cleaned_cloud')
    ap.add_argument('--frame-id', default='unilidar_lidar')
    ap.add_argument('--chunk-points', type=int, default=4000)
    ap.add_argument('--period', type=float, default=0.20)
    args = ap.parse_args()

    pts = np.loadtxt(Path(args.xyz), dtype=np.float32)
    pts = np.atleast_2d(pts)
    if pts.shape[1] < 3:
        raise RuntimeError('XYZ input must contain at least three columns')
    pts = pts[:, :3]
    pts = pts[np.isfinite(pts).all(axis=1)]

    rclpy.init()
    node = Publisher(args.topic)
    # Give DDS discovery a moment before the first chunk.
    for _ in range(10):
        rclpy.spin_once(node, timeout_sec=0.1)
    total = len(pts)
    for start in range(0, total, args.chunk_points):
        chunk = pts[start:start + args.chunk_points]
        node.pub.publish(cloud_msg(chunk, args.frame_id, node.get_clock().now().to_msg()))
        node.get_logger().info(f'published points {start}:{start + len(chunk)} / {total}')
        rclpy.spin_once(node, timeout_sec=0.05)
        time.sleep(args.period)
    # Allow final delivery before shutdown.
    end = time.time() + 2.0
    while time.time() < end:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
