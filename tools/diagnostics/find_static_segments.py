#!/usr/bin/env python3
import argparse, math
from pathlib import Path
import numpy as np
from mcap.reader import make_reader
from mcap_ros2.decoder import DecoderFactory

LIN_THR = 0.02      # m/s
ANG_THR = 0.02      # rad/s
MAX_GAP_NS = 500_000_000
MIN_SEG_S = 3.0


def yaw(q):
    return math.atan2(2*(q.w*q.z + q.x*q.y), 1 - 2*(q.y*q.y + q.z*q.z))


def read_odom(path):
    rows=[]
    with open(path,'rb') as f:
        r=make_reader(f, decoder_factories=[DecoderFactory()])
        for _,_,msg,ros in r.iter_decoded_messages(topics=['/odom']):
            p=ros.pose.pose.position; q=ros.pose.pose.orientation; tw=ros.twist.twist
            lin=math.sqrt(tw.linear.x**2 + tw.linear.y**2 + tw.linear.z**2)
            ang=math.sqrt(tw.angular.x**2 + tw.angular.y**2 + tw.angular.z**2)
            rows.append((int(msg.log_time),p.x,p.y,p.z,yaw(q),lin,ang))
    return np.asarray(rows,float)


def count_clouds(path,start_ns,end_ns):
    n=0
    with open(path,'rb') as f:
        r=make_reader(f)
        for _ in r.iter_messages(start_time=int(start_ns), end_time=int(end_ns), topics=['/unilidar/cloud']):
            n+=1
    return n


def segments(a):
    if len(a)==0: return []
    t=a[:,0].astype(np.int64)
    good=(a[:,5] <= LIN_THR) & (a[:,6] <= ANG_THR)
    out=[]; s=None; prev=None
    for i,g in enumerate(good):
        if g and (s is None or (prev is not None and t[i]-t[prev] > MAX_GAP_NS)):
            if s is not None and prev is not None: out.append((s,prev))
            s=i
        elif not g and s is not None:
            out.append((s,i-1)); s=None
        if g: prev=i
    if s is not None: out.append((s,prev))
    return out


def describe(a,i0,i1):
    w=a[i0:i1+1]; t=w[:,0].astype(np.int64); xyz=w[:,1:4]
    center=np.median(xyz,axis=0)
    path=float(np.sum(np.linalg.norm(np.diff(xyz,axis=0),axis=1))) if len(xyz)>1 else 0.0
    radius=float(np.max(np.linalg.norm(xyz-center,axis=1))) if len(xyz) else 0.0
    yspan=float(np.ptp(np.unwrap(w[:,4]))) if len(w)>1 else 0.0
    return {
        'start_ns':int(t[0]), 'end_ns':int(t[-1]), 'duration_s':(t[-1]-t[0])/1e9,
        'samples':len(w), 'path_m':path, 'radius_m':radius, 'yaw_span_rad':yspan,
        'lin_p95':float(np.percentile(w[:,5],95)), 'ang_p95':float(np.percentile(w[:,6],95)),
        'x':float(center[0]), 'y':float(center[1]), 'z':float(center[2])
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('bags', nargs='+'); args=ap.parse_args()
    for bag in args.bags:
        a=read_odom(bag)
        print(f'\n=== {Path(bag).name} ===')
        print(f'odom_samples={len(a)} thresholds: lin<={LIN_THR} m/s ang<={ANG_THR} rad/s')
        segs=[]
        for i0,i1 in segments(a):
            d=describe(a,i0,i1)
            if d['duration_s'] >= MIN_SEG_S:
                d['clouds']=count_clouds(bag,d['start_ns'],d['end_ns'])
                segs.append(d)
        segs.sort(key=lambda d:d['start_ns'])
        if not segs:
            print('NO stationary segment >= 3 s')
            continue
        for k,d in enumerate(segs,1):
            print(f"{k:02d} dur={d['duration_s']:.2f}s clouds={d['clouds']} path={d['path_m']:.4f}m radius={d['radius_m']:.4f}m yaw_span={d['yaw_span_rad']:.4f}rad pose=({d['x']:.3f},{d['y']:.3f},{d['z']:.3f}) start={d['start_ns']} end={d['end_ns']}")

if __name__=='__main__': main()
