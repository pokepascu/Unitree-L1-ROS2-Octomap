#!/usr/bin/env python3
"""Generate organized visual verification videos for Approach 1 static LiDAR analysis.

Outputs four videos per environment:
1. raw accumulation from /unilidar/cloud;
2. conservative cleaned 3D rotation from derived PLY;
3. dynamic/foreground candidate overlay evolution;
4. odometry stationarity verification from /odom.

The source rosbag is never modified.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d
import yaml
from mcap.reader import make_reader
from mcap_ros2.decoder import DecoderFactory

PF = {1:'i1',2:'u1',3:'i2',4:'u2',5:'i4',6:'u4',7:'f4',8:'f8'}


def pointcloud_dtype(msg):
    names=[]; formats=[]; offsets=[]
    endian='>' if msg.is_bigendian else '<'
    for f in msg.fields:
        if f.datatype not in PF: continue
        names.append(f.name)
        base=np.dtype(endian+PF[f.datatype])
        formats.append(base if f.count==1 else (base,(f.count,)))
        offsets.append(int(f.offset))
    return np.dtype({'names':names,'formats':formats,'offsets':offsets,'itemsize':int(msg.point_step)})


def decode_xyz(msg):
    dt=pointcloud_dtype(msg)
    arr=np.frombuffer(msg.data,dtype=dt,count=int(msg.width)*int(msg.height))
    return np.column_stack((arr['x'],arr['y'],arr['z'])).astype(np.float64,copy=False)


def voxel(points,v):
    if len(points)==0: return points
    k=np.floor(points/v).astype(np.int64)
    _,idx=np.unique(k,axis=0,return_index=True)
    return points[idx]


def encode(frames_dir,out,fps=12):
    subprocess.run(['ffmpeg','-y','-framerate',str(fps),'-i',str(frames_dir/'%04d.png'),
                    '-c:v','libx264','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],
                   check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


def safe_limits(points,p=99.5,pad=.08):
    lo=np.percentile(points,100-p,axis=0); hi=np.percentile(points,p,axis=0)
    span=np.maximum(hi-lo,1e-3); return lo-pad*span,hi+pad*span


def load_cloud_and_odom(bag,min_range,max_range):
    clouds=[]; ct=[]; od=[]
    with bag.open('rb') as f:
        r=make_reader(f,decoder_factories=[DecoderFactory()])
        for schema,channel,msg,ros in r.iter_decoded_messages(topics=['/unilidar/cloud','/odom']):
            if channel.topic=='/unilidar/cloud':
                xyz=decode_xyz(ros); xyz=xyz[np.isfinite(xyz).all(axis=1)]
                rr=np.linalg.norm(xyz,axis=1); xyz=xyz[(rr>=min_range)&(rr<=max_range)]
                clouds.append(xyz); ct.append(int(msg.log_time))
            elif channel.topic=='/odom':
                p=ros.pose.pose.position; tw=ros.twist.twist
                lin=math.sqrt(tw.linear.x**2+tw.linear.y**2+tw.linear.z**2)
                ang=math.sqrt(tw.angular.x**2+tw.angular.y**2+tw.angular.z**2)
                od.append((int(msg.log_time),float(p.x),float(p.y),float(p.z),lin,ang))
    return clouds,np.asarray(ct,dtype=np.int64),np.asarray(od,dtype=float)


def video_raw_accumulation(clouds,times,out,cfg,title):
    work=out.parent/'_raw_frames'; shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    v=float(cfg['voxel_m']); accum=[]
    every=max(1,len(clouds)//70)
    sample_ids=list(range(0,len(clouds),every));
    if sample_ids[-1]!=len(clouds)-1: sample_ids.append(len(clouds)-1)
    union=np.vstack([voxel(x,v) for x in clouds]); union=voxel(union,v)
    lo,hi=safe_limits(union[:,:2])
    for fi,i in enumerate(sample_ids):
        accum.append(voxel(clouds[i],v)); pts=voxel(np.vstack(accum),v)
        if len(pts)>160000: pts=pts[np.linspace(0,len(pts)-1,160000).astype(int)]
        fig,ax=plt.subplots(figsize=(8,7)); sc=ax.scatter(pts[:,0],pts[:,1],c=pts[:,2],s=.35)
        ax.set_xlim(lo[0],hi[0]); ax.set_ylim(lo[1],hi[1]); ax.set_aspect('equal','box')
        ax.set_xlabel('x [m]'); ax.set_ylabel('y [m]');
        elapsed=(times[i]-times[0])/1e9
        ax.set_title(f'{title}\nRaw PointCloud2 accumulation - t={elapsed:.1f}s, frames={i+1}')
        fig.colorbar(sc,ax=ax,label='z [m]'); fig.tight_layout(); fig.savefig(work/f'{fi:04d}.png',dpi=120); plt.close(fig)
    encode(work,out,12); shutil.rmtree(work)


def video_clean_rotation(clean_ply,out,title):
    work=out.parent/'_rot_frames'; shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    pts=np.asarray(o3d.io.read_point_cloud(str(clean_ply)).points)
    if len(pts)>90000: pts=pts[np.linspace(0,len(pts)-1,90000).astype(int)]
    lo,hi=safe_limits(pts)
    for i,az in enumerate(np.linspace(0,355,72)):
        fig=plt.figure(figsize=(8,6)); ax=fig.add_subplot(111,projection='3d')
        ax.scatter(pts[:,0],pts[:,1],pts[:,2],c=pts[:,2],s=.25)
        ax.set_xlim(lo[0],hi[0]); ax.set_ylim(lo[1],hi[1]); ax.set_zlim(lo[2],hi[2])
        ax.set_xlabel('x [m]'); ax.set_ylabel('y [m]'); ax.set_zlabel('z [m]'); ax.view_init(elev=25,azim=az)
        ax.set_title(f'{title}\nConservative cleaned cloud - 3D inspection')
        fig.tight_layout(); fig.savefig(work/f'{i:04d}.png',dpi=120); plt.close(fig)
    encode(work,out,12); shutil.rmtree(work)


def dynamic_keys(clouds,times,cfg):
    v=float(cfg['voxel_m']); block_s=float(cfg['temporal_block_s'])
    t0=int(times[0]); byblock=defaultdict(set); sums=defaultdict(lambda:np.zeros(3)); n=defaultdict(int)
    for xyz,t in zip(clouds,times):
        vp=voxel(xyz,v); keys=np.floor(vp/v).astype(np.int64); b=int(((int(t)-t0)/1e9)//block_s)
        for p,k in zip(vp,keys):
            kt=tuple(int(x) for x in k); byblock[b].add(kt); sums[kt]+=p; n[kt]+=1
    bc=defaultdict(int)
    for s in byblock.values():
        for k in s: bc[k]+=1
    nb=max(1,len(byblock)); pts={k:sums[k]/n[k] for k in n}
    dyn={k for k in n if bc[k]/nb < float(cfg['dynamic_persistence_threshold']) and np.linalg.norm(pts[k])<=float(cfg['dynamic_candidate_max_range_m'])}
    return dyn,pts


def video_dynamic_evolution(clouds,times,out,cfg,title):
    work=out.parent/'_dyn_frames'; shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    v=float(cfg['voxel_m']); dyn,_=dynamic_keys(clouds,times,cfg)
    allv=voxel(np.vstack([voxel(x,v) for x in clouds]),v); lo,hi=safe_limits(allv[:,:2])
    every=max(1,len(clouds)//70); ids=list(range(0,len(clouds),every));
    if ids[-1]!=len(clouds)-1: ids.append(len(clouds)-1)
    accum=[]
    for fi,i in enumerate(ids):
        accum.append(voxel(clouds[i],v)); pts=voxel(np.vstack(accum),v); keys=np.floor(pts/v).astype(np.int64)
        flag=np.array([tuple(int(x) for x in k) in dyn for k in keys],dtype=bool)
        base=pts[~flag]; fg=pts[flag]
        if len(base)>140000: base=base[np.linspace(0,len(base)-1,140000).astype(int)]
        if len(fg)>70000: fg=fg[np.linspace(0,len(fg)-1,70000).astype(int)]
        fig,ax=plt.subplots(figsize=(8,7)); ax.scatter(base[:,0],base[:,1],s=.25,label='higher-persistence structure')
        if len(fg): ax.scatter(fg[:,0],fg[:,1],s=1.2,label='low-persistence candidate')
        ax.set_xlim(lo[0],hi[0]); ax.set_ylim(lo[1],hi[1]); ax.set_aspect('equal','box'); ax.legend(markerscale=4)
        elapsed=(times[i]-times[0])/1e9; ax.set_title(f'{title}\nTemporal foreground candidates - t={elapsed:.1f}s')
        ax.set_xlabel('x [m]'); ax.set_ylabel('y [m]'); fig.tight_layout(); fig.savefig(work/f'{fi:04d}.png',dpi=120); plt.close(fig)
    encode(work,out,12); shutil.rmtree(work)


def video_odometry(odom,out,title):
    work=out.parent/'_odom_frames'; shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    if len(odom)==0: return
    t=(odom[:,0]-odom[0,0])/1e9; x=odom[:,1]; y=odom[:,2]; lin=odom[:,4]; ang=odom[:,5]
    ids=np.linspace(1,len(odom)-1,min(90,len(odom)-1)).astype(int)
    for fi,i in enumerate(ids):
        fig=plt.figure(figsize=(10,7)); gs=fig.add_gridspec(2,2)
        ax0=fig.add_subplot(gs[:,0]); ax1=fig.add_subplot(gs[0,1]); ax2=fig.add_subplot(gs[1,1])
        ax0.plot(x[:i+1],y[:i+1]); ax0.scatter([x[i]],[y[i]],s=40); ax0.set_aspect('equal','box'); ax0.set_xlabel('odom x [m]'); ax0.set_ylabel('odom y [m]'); ax0.set_title('Recorded odometry trajectory')
        ax1.plot(t[:i+1],lin[:i+1]); ax1.axhline(0.02,ls='--'); ax1.set_ylabel('|linear velocity| [m/s]'); ax1.set_xlim(t[0],t[-1]); ax1.set_ylim(bottom=0)
        ax2.plot(t[:i+1],ang[:i+1]); ax2.axhline(0.02,ls='--'); ax2.set_ylabel('|angular velocity| [rad/s]'); ax2.set_xlabel('time [s]'); ax2.set_xlim(t[0],t[-1]); ax2.set_ylim(bottom=0)
        fig.suptitle(f'{title}\nStationarity verification from /odom - t={t[i]:.1f}s'); fig.tight_layout(); fig.savefig(work/f'{fi:04d}.png',dpi=120); plt.close(fig)
    encode(work,out,15); shutil.rmtree(work)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--bag',required=True); ap.add_argument('--config',required=True); ap.add_argument('--analysis-dir',required=True); ap.add_argument('--evidence-dir',required=True); ap.add_argument('--label',required=True)
    a=ap.parse_args(); bag=Path(a.bag); cfg=yaml.safe_load(Path(a.config).read_text()); ad=Path(a.analysis_dir); ev=Path(a.evidence_dir); ev.mkdir(parents=True,exist_ok=True)
    clouds,times,odom=load_cloud_and_odom(bag,float(cfg['min_range_m']),float(cfg['max_range_m']))
    video_raw_accumulation(clouds,times,ev/'01_raw_pointcloud_accumulation.mp4',cfg,a.label)
    video_clean_rotation(ad/'conservative_cleaned.ply',ev/'02_conservative_cleaned_rotation.mp4',a.label)
    video_dynamic_evolution(clouds,times,ev/'03_dynamic_foreground_evolution.mp4',cfg,a.label)
    video_odometry(odom,ev/'04_odometry_stationarity.mp4',a.label)
    manifest={
      'environment':a.label,'source_bag':str(bag),'videos':[
       {'file':'01_raw_pointcloud_accumulation.mp4','purpose':'Verify decoding and temporal accumulation of /unilidar/cloud in the stationary LiDAR frame. Moving foreground may appear as changing or smeared geometry.'},
       {'file':'02_conservative_cleaned_rotation.mp4','purpose':'Inspect the 3D geometry retained after range, voxel, Statistical Outlier Removal and Radius Outlier Removal filtering.'},
       {'file':'03_dynamic_foreground_evolution.mp4','purpose':'Visualize low-temporal-persistence foreground candidates. These are candidates only and are not automatically classified as people.'},
       {'file':'04_odometry_stationarity.mp4','purpose':'Verify the selected interval using /odom position and linear/angular speeds against the 0.02 m/s and 0.02 rad/s stationarity thresholds.'}
      ],
      'limitations':['No camera ground truth is available for human labels.','Persistent people can be indistinguishable from static objects.','Occluded surfaces are not reconstructed from a single viewpoint.']}
    (ev/'manifest.json').write_text(json.dumps(manifest,indent=2))

if __name__=='__main__': main()
