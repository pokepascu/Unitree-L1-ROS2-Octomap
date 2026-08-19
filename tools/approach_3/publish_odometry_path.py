#!/usr/bin/env python3
import argparse,csv,time
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped

ap=argparse.ArgumentParser(); ap.add_argument('--csv',required=True); ap.add_argument('--topic',default='/recorded_odom_path'); ap.add_argument('--frame-id',default='odom'); ap.add_argument('--hold',type=float,default=8.0)
a=ap.parse_args()
rows=list(csv.DictReader(open(a.csv,newline='')))
rclpy.init(); node=Node('recorded_odometry_path_publisher'); pub=node.create_publisher(Path,a.topic,1)
msg=Path(); msg.header.frame_id=a.frame_id; msg.header.stamp=node.get_clock().now().to_msg()
for r in rows:
    p=PoseStamped(); p.header.frame_id=a.frame_id; p.header.stamp=msg.header.stamp
    p.pose.position.x=float(r['x_m']); p.pose.position.y=float(r['y_m']); p.pose.position.z=float(r['z_m'])
    p.pose.orientation.x=float(r['qx']); p.pose.orientation.y=float(r['qy']); p.pose.orientation.z=float(r['qz']); p.pose.orientation.w=float(r['qw'])
    msg.poses.append(p)
end=time.time()+a.hold
while time.time()<end:
    msg.header.stamp=node.get_clock().now().to_msg(); pub.publish(msg); rclpy.spin_once(node,timeout_sec=0.1); time.sleep(0.2)
node.destroy_node(); rclpy.shutdown()
