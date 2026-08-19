#!/usr/bin/env python3
"""Approach 2: register three stationary Unitree L1 scans without inventing extrinsics.

The three PointCloud2 streams are decoded in their own `unilidar_lidar` frames.
Scan 1 is the reference. Scans 2 and 3 are aligned geometrically using a
multi-start point-to-point ICP. Recorded stationary selection positions are
used only as a scale/displacement diagnostic; they are not converted into a
sensor-frame rotation because the fixed LiDAR rotation is not explicitly
known in the project data.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import yaml
from mcap.reader import make_reader
from mcap_ros2.decoder import DecoderFactory
from scipy.spatial import cKDTree

PF={1:'i1',2:'u1',3:'i2',4:'u2',5:'i4',6:'u4',7:'f4',8:'f8'}


def pointcloud_dtype(msg):
    names=[]; formats=[]; offsets=[]
    endian='>' if msg.is_bigendian else '<'
    for f in msg.fields:
        if f.datatype not in PF: continue
        names.append(f.name); offsets.append(int(f.offset))
        base=np.dtype(endian+PF[f.datatype])
        formats.append(base if f.count==1 else (base,(f.count,)))
    return np.dtype({'names':names,'formats':formats,'offsets':offsets,'itemsize':int(msg.point_step)})


def decode_xyz(msg):
    dt=pointcloud_dtype(msg)
    arr=np.frombuffer(msg.data,dtype=dt,count=int(msg.width)*int(msg.height))
    return np.column_stack((arr['x'],arr['y'],arr['z'])).astype(np.float64,copy=False)


def voxel(points, size):
    if len(points)==0:return points
    key=np.floor(points/size).astype(np.int64)
    _,idx=np.unique(key,axis=0,return_index=True)
    return points[np.sort(idx)]


def load_cloud(scan_dir:Path, voxel_m:float, min_range:float, max_range:float):
    bag=scan_dir/'static_segment.mcap'; chunks=[]; frame_id=set(); frames=0
    with bag.open('rb') as f:
        r=make_reader(f,decoder_factories=[DecoderFactory()])
        for _,_,_,ros in r.iter_decoded_messages(topics=['/unilidar/cloud']):
            p=decode_xyz(ros); p=p[np.isfinite(p).all(axis=1)]
            rr=np.linalg.norm(p,axis=1); p=p[(rr>=min_range)&(rr<=max_range)]
            chunks.append(p); frame_id.add(ros.header.frame_id); frames+=1
    if not chunks: raise RuntimeError(f'No cloud in {bag}')
    p=voxel(np.vstack(chunks),voxel_m)
    sel=yaml.safe_load((scan_dir/'selection.yaml').read_text())
    return p,sel,sorted(frame_id),frames


def T_yaw(yaw):
    c=math.cos(yaw); s=math.sin(yaw)
    T=np.eye(4); T[:3,:3]=[[c,-s,0],[s,c,0],[0,0,1]]
    return T


def transform(p,T): return p@T[:3,:3].T+T[:3,3]


def kabsch(src,dst):
    cs=src.mean(0); cd=dst.mean(0); H=(src-cs).T@(dst-cd)
    U,_,Vt=np.linalg.svd(H); R=Vt.T@U.T
    if np.linalg.det(R)<0: Vt[-1]*=-1; R=Vt.T@U.T
    t=cd-R@cs; T=np.eye(4); T[:3,:3]=R; T[:3,3]=t; return T


def icp(source,target,T0,max_corr=0.45,iters=60,sample=45000):
    src=source if len(source)<=sample else source[np.linspace(0,len(source)-1,sample).astype(int)]
    tgt=target if len(target)<=sample else target[np.linspace(0,len(target)-1,sample).astype(int)]
    tree=cKDTree(tgt); T=T0.copy(); prev=np.inf
    for _ in range(iters):
        q=transform(src,T); d,idx=tree.query(q,k=1,workers=-1); m=d<max_corr
        if m.sum()<100: break
        dT=kabsch(q[m],tgt[idx[m]]); T=dT@T
        rmse=float(np.sqrt(np.mean(d[m]**2)))
        if abs(prev-rmse)<1e-5: break
        prev=rmse
    q=transform(src,T); d,_=tree.query(q,k=1,workers=-1); m=d<max_corr
    fitness=float(m.mean()); rmse=float(np.sqrt(np.mean(d[m]**2))) if m.any() else float('inf')
    return T,fitness,rmse,int(m.sum())


def multistart(source,target):
    cs=source.mean(0); ct=target.mean(0); best=None
    # Geometry-only coarse hypotheses: centre alignment plus yaw hypotheses.
    for deg in range(0,360,30):
        T=T_yaw(math.radians(deg)); T[:3,3]=ct-T[:3,:3]@cs
        Tc,fit,rmse,n=icp(source,target,T,max_corr=1.0,iters=35)
        Tf,fit2,rmse2,n2=icp(source,target,Tc,max_corr=0.35,iters=70)
        score=(fit2,-rmse2)
        if best is None or score>best[0]: best=(score,Tf,fit2,rmse2,n2,deg)
    _,T,fit,rmse,n,deg=best
    return T,{'fitness':fit,'rmse_m':rmse,'correspondences':n,'initial_yaw_hypothesis_deg':deg}


def save_xyz(path,p): np.savetxt(path,p,fmt='%.6f')


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--environment-dir',required=True); ap.add_argument('--out',required=True)
    ap.add_argument('--voxel',type=float,default=0.05); ap.add_argument('--min-range',type=float,default=0.25); ap.add_argument('--max-range',type=float,default=15.0)
    a=ap.parse_args(); root=Path(a.environment_dir); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    scans=[]; sels=[]; report={'method':'multi-start point-to-point ICP','reference':'scan_01','voxel_m':a.voxel,'range_m':[a.min_range,a.max_range],'extrinsic_rotation_assumed':False,'scans':{}}
    for i in range(1,4):
        name=f'scan_{i:02d}'; p,sel,frames,frame_count=load_cloud(root/name,a.voxel,a.min_range,a.max_range)
        scans.append(p); sels.append(sel); save_xyz(out/f'{name}_raw.xyz',p)
        report['scans'][name]={'points':len(p),'cloud_frames':frame_count,'frame_ids':frames,'selection_pose_xyz_m':sel.get('pose')}
    ref=scans[0]; registered=[ref]; transforms=[np.eye(4)]
    for i in (1,2):
        T,m=multistart(scans[i],ref); registered.append(transform(scans[i],T)); transforms.append(T)
        p0=np.asarray(sels[0].get('pose',[0,0,0]),float); pi=np.asarray(sels[i].get('pose',[0,0,0]),float)
        m['recorded_stationary_position_displacement_m']=float(np.linalg.norm(pi-p0))
        m['icp_translation_norm_m']=float(np.linalg.norm(T[:3,3])); m['transform_source_to_scan01']=T.tolist()
        report['scans'][f'scan_{i+1:02d}']['registration_to_scan_01']=m
        save_xyz(out/f'scan_{i+1:02d}_registered.xyz',registered[i])
    save_xyz(out/'scan_01_registered.xyz',ref)
    merged=voxel(np.vstack(registered),a.voxel); save_xyz(out/'merged_registered.xyz',merged)
    report['merged_points']=len(merged)
    report['caution']='ICP estimates sensor-frame rigid transforms from measured geometry. Recorded stop positions are diagnostics only; no unknown LiDAR rotation was invented.'
    (out/'registration_metrics.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
