#!/usr/bin/env python3
"""Republish Unitree L1 clouds with a zero-translation odometry/LiDAR extrinsic.

The base<-LiDAR rotation comes from an accepted calibration JSON.  For each raw
cloud, the nearest recorded /odom pose is used to broadcast odom->fused_lidar.
The point samples are not altered or inpainted; only their frame association is
changed.  New current-time stamps are used so TF2/OctoMap can consume historical
bag data during CI replay without old-data cache failures.
"""
import argparse
import csv
import json
import math
import time

import numpy as np
import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import PointCloud2
from tf2_ros import TransformBroadcaster


def q_to_R(q):
    x,y,z,w=q; n=math.sqrt(x*x+y*y+z*z+w*w); x,y,z,w=x/n,y/n,z/n,w/n
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]],float)


def R_to_q(R):
    t=float(np.trace(R))
    if t>0:
        s=math.sqrt(t+1)*2; q=np.array([(R[2,1]-R[1,2])/s,(R[0,2]-R[2,0])/s,(R[1,0]-R[0,1])/s,.25*s])
    else:
        i=int(np.argmax(np.diag(R)))
        if i==0:
            s=math.sqrt(max(1e-16,1+R[0,0]-R[1,1]-R[2,2]))*2; q=np.array([.25*s,(R[0,1]+R[1,0])/s,(R[0,2]+R[2,0])/s,(R[2,1]-R[1,2])/s])
        elif i==1:
            s=math.sqrt(max(1e-16,1+R[1,1]-R[0,0]-R[2,2]))*2; q=np.array([(R[0,1]+R[1,0])/s,.25*s,(R[1,2]+R[2,1])/s,(R[0,2]-R[2,0])/s])
        else:
            s=math.sqrt(max(1e-16,1+R[2,2]-R[0,0]-R[1,1]))*2; q=np.array([(R[0,2]+R[2,0])/s,(R[1,2]+R[2,1])/s,.25*s,(R[1,0]-R[0,1])/s])
    q=q/np.linalg.norm(q)
    if q[3]<0:q=-q
    return q


def load_odom(path):
    rows=[]
    with open(path,newline='') as f:
        for r in csv.DictReader(f):
            rows.append([float(r['time_s']),float(r['x_m']),float(r['y_m']),float(r['z_m']),float(r['qx']),float(r['qy']),float(r['qz']),float(r['qw'])])
    a=np.asarray(rows,float)
    if len(a)<2: raise RuntimeError('odometry CSV is empty')
    return a


class Fusion(Node):
    def __init__(self,args):
        super().__init__('zero_translation_odom_lidar_fusion')
        self.O=load_odom(args.odom)
        rep=json.load(open(args.extrinsic))
        if not rep.get('canonical_fusion_allowed',False):
            raise RuntimeError('extrinsic calibration is not accepted; canonical fusion refused')
        if any(abs(float(x))>1e-12 for x in rep.get('translation_m',[1,1,1])):
            raise RuntimeError('this node requires the project zero-translation constraint')
        self.Rbl=np.asarray(rep['rotation_matrix_base_from_lidar'],float)
        self.parent=args.parent_frame; self.child=args.child_frame; self.maxdt=args.max_sync_s
        qos_in=QoSProfile(depth=20,history=HistoryPolicy.KEEP_LAST,reliability=ReliabilityPolicy.BEST_EFFORT,durability=DurabilityPolicy.VOLATILE)
        qos_out=QoSProfile(depth=20,history=HistoryPolicy.KEEP_LAST,reliability=ReliabilityPolicy.RELIABLE,durability=DurabilityPolicy.VOLATILE)
        self.pub=self.create_publisher(PointCloud2,args.output_topic,qos_out)
        self.tf=TransformBroadcaster(self)
        self.sub=self.create_subscription(PointCloud2,args.input_topic,self.cb,qos_in)
        self.count=0; self.dropped=0
    def nearest(self,t):
        k=int(np.searchsorted(self.O[:,0],t)); k=min(max(k,1),len(self.O)-1)
        if abs(self.O[k-1,0]-t)<=abs(self.O[k,0]-t):k-=1
        return k,abs(self.O[k,0]-t)
    def cb(self,m):
        source_t=float(m.header.stamp.sec)+float(m.header.stamp.nanosec)*1e-9
        k,dt=self.nearest(source_t)
        if dt>self.maxdt:
            self.dropped+=1
            if self.dropped<5:self.get_logger().warning(f'drop cloud: nearest odom dt={dt:.3f}s')
            return
        o=self.O[k]; Rwb=q_to_R(o[4:8]); Rwl=Rwb@self.Rbl; q=R_to_q(Rwl)
        stamp=self.get_clock().now().to_msg()
        tr=TransformStamped(); tr.header.stamp=stamp; tr.header.frame_id=self.parent; tr.child_frame_id=self.child
        tr.transform.translation.x=float(o[1]); tr.transform.translation.y=float(o[2]); tr.transform.translation.z=float(o[3])
        tr.transform.rotation.x=float(q[0]); tr.transform.rotation.y=float(q[1]); tr.transform.rotation.z=float(q[2]); tr.transform.rotation.w=float(q[3])
        self.tf.sendTransform(tr)
        m.header.stamp=stamp; m.header.frame_id=self.child
        self.pub.publish(m); self.count+=1
        if self.count%250==0:self.get_logger().info(f'published {self.count} fused clouds, dropped {self.dropped}')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--odom',required=True); ap.add_argument('--extrinsic',required=True)
    ap.add_argument('--input-topic',default='/unilidar/cloud'); ap.add_argument('--output-topic',default='/fused_cloud')
    ap.add_argument('--parent-frame',default='odom'); ap.add_argument('--child-frame',default='fused_lidar')
    ap.add_argument('--max-sync-s',type=float,default=.08)
    a=ap.parse_args(); rclpy.init(); n=Fusion(a)
    try:rclpy.spin(n)
    except KeyboardInterrupt:pass
    print(f'FUSED_CLOUDS {n.count} DROPPED {n.dropped}')
    n.destroy_node(); rclpy.shutdown()

if __name__=='__main__':main()
