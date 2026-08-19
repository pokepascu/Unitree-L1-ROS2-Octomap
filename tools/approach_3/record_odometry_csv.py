#!/usr/bin/env python3
import argparse,csv,time
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry

ap=argparse.ArgumentParser(); ap.add_argument('--topic',required=True); ap.add_argument('--out',required=True); ap.add_argument('--timeout',type=float,default=900)
a=ap.parse_args(); rclpy.init(); node=Node('odometry_csv_recorder'); rows=[]; last=time.time()
def cb(m):
    global last
    p=m.pose.pose.position; q=m.pose.pose.orientation
    rows.append([m.header.stamp.sec+m.header.stamp.nanosec*1e-9,p.x,p.y,p.z,q.x,q.y,q.z,q.w,m.header.frame_id,m.child_frame_id]); last=time.time()
sub=node.create_subscription(Odometry,a.topic,cb,50); start=time.time()
while rclpy.ok() and time.time()-start<a.timeout:
    rclpy.spin_once(node,timeout_sec=0.2)
    if rows and time.time()-last>5: break
with open(a.out,'w',newline='') as f:
    w=csv.writer(f); w.writerow(['time_s','x_m','y_m','z_m','qx','qy','qz','qw','frame_id','child_frame_id']); w.writerows(rows)
print('ODOMETRY_SAMPLES',len(rows)); node.destroy_node(); rclpy.shutdown()
