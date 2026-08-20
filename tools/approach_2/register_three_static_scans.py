#!/usr/bin/env python3
"""Approach 2: globally register three stationary Unitree L1 scans.

The LiDAR origin is coincident with the robot base origin (project constraint:
base_link -> unilidar_lidar translation = 0). Therefore the norm of every
rigid transform translation between two stationary LiDAR scans must equal the
recorded odometry displacement between the two stops, independently of the
unknown constant LiDAR/base rotation.

We use that measured displacement as a hard physical constraint, while the
rotation and translation direction are estimated from point-cloud geometry.
Global FPFH/FGR/RANSAC hypotheses plus geometry multistart hypotheses are
refined with a translation-norm-constrained ICP. Three pairwise registrations
(2->1, 3->2, 3->1) are selected jointly using pose-cycle consistency.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np
import open3d as o3d
import yaml
from mcap.reader import make_reader
from mcap_ros2.decoder import DecoderFactory
from scipy.spatial import cKDTree

PF={1:'i1',2:'u1',3:'i2',4:'u2',5:'i4',6:'u4',7:'f4',8:'f8'}


def pointcloud_dtype(msg):
    names=[]; formats=[]; offsets=[]
    endian='>' if msg.is_bigendian else '<'
    for f in msg.fields:
        if f.datatype not in PF:
            continue
        names.append(f.name); offsets.append(int(f.offset))
        base=np.dtype(endian+PF[f.datatype])
        formats.append(base if f.count==1 else (base,(f.count,)))
    return np.dtype({'names':names,'formats':formats,'offsets':offsets,'itemsize':int(msg.point_step)})


def decode_xyz(msg):
    dt=pointcloud_dtype(msg)
    arr=np.frombuffer(msg.data,dtype=dt,count=int(msg.width)*int(msg.height))
    return np.column_stack((arr['x'],arr['y'],arr['z'])).astype(np.float64,copy=False)


def voxel(points,size):
    if len(points)==0:
        return points
    key=np.floor(points/size).astype(np.int64)
    _,idx=np.unique(key,axis=0,return_index=True)
    return points[np.sort(idx)]


def load_cloud(scan_dir:Path,voxel_m:float,min_range:float,max_range:float):
    bag=scan_dir/'static_segment.mcap'; chunks=[]; frame_ids=set(); frames=0
    with bag.open('rb') as f:
        r=make_reader(f,decoder_factories=[DecoderFactory()])
        for _,_,_,ros in r.iter_decoded_messages(topics=['/unilidar/cloud']):
            p=decode_xyz(ros); p=p[np.isfinite(p).all(axis=1)]
            rr=np.linalg.norm(p,axis=1); p=p[(rr>=min_range)&(rr<=max_range)]
            chunks.append(p); frame_ids.add(ros.header.frame_id); frames+=1
    if not chunks:
        raise RuntimeError(f'No cloud in {bag}')
    p=voxel(np.vstack(chunks),voxel_m)
    sel=yaml.safe_load((scan_dir/'selection.yaml').read_text())
    return p,sel,sorted(frame_ids),frames


def T_yaw(yaw):
    c=math.cos(yaw); s=math.sin(yaw)
    T=np.eye(4); T[:3,:3]=[[c,-s,0],[s,c,0],[0,0,1]]
    return T


def transform(p,T):
    return p@T[:3,:3].T+T[:3,3]


def kabsch(src,dst):
    cs=src.mean(0); cd=dst.mean(0)
    H=(src-cs).T@(dst-cd)
    U,_,Vt=np.linalg.svd(H); R=Vt.T@U.T
    if np.linalg.det(R)<0:
        Vt[-1]*=-1; R=Vt.T@U.T
    t=cd-R@cs
    T=np.eye(4); T[:3,:3]=R; T[:3,3]=t
    return T


def project_translation_norm(T,expected_m,fallback=None):
    T=T.copy(); t=T[:3,3]; n=float(np.linalg.norm(t))
    if n<1e-9:
        if fallback is None:
            fallback=np.array([1.0,0.0,0.0])
        f=np.asarray(fallback,float); fn=float(np.linalg.norm(f))
        if fn<1e-9:
            f=np.array([1.0,0.0,0.0]); fn=1.0
        T[:3,3]=f/fn*expected_m
    else:
        T[:3,3]=t/n*expected_m
    return T


def fixed_norm_icp(source,target,T0,expected_m,max_corr,iters,sample):
    si=np.linspace(0,len(source)-1,min(len(source),sample)).astype(int)
    ti=np.linspace(0,len(target)-1,min(len(target),sample)).astype(int)
    src=source[si]; tgt=target[ti]; tree=cKDTree(tgt)
    T=project_translation_norm(T0,expected_m)
    prev=np.inf
    for _ in range(iters):
        q=transform(src,T); d,idx=tree.query(q,k=1,workers=-1); m=d<max_corr
        if int(m.sum())<120:
            break
        dT=kabsch(q[m],tgt[idx[m]])
        candidate=dT@T
        candidate=project_translation_norm(candidate,expected_m,fallback=T[:3,3])
        T=candidate
        rmse=float(np.sqrt(np.mean(d[m]**2)))
        if abs(prev-rmse)<2e-5:
            break
        prev=rmse
    return T


def evaluate(source,target,T,threshold=0.35,sample=45000):
    si=np.linspace(0,len(source)-1,min(len(source),sample)).astype(int)
    ti=np.linspace(0,len(target)-1,min(len(target),sample)).astype(int)
    src=source[si]; tgt=target[ti]; tree=cKDTree(tgt)
    q=transform(src,T); d,_=tree.query(q,k=1,workers=-1); m=d<threshold
    fit=float(m.mean())
    rmse=float(np.sqrt(np.mean(d[m]**2))) if m.any() else float('inf')
    p90=float(np.percentile(d[m],90)) if m.any() else float('inf')
    return fit,rmse,p90,int(m.sum())


def o3d_prepare(points,feature_voxel=0.20):
    pc=o3d.geometry.PointCloud()
    pc.points=o3d.utility.Vector3dVector(points)
    down=pc.voxel_down_sample(feature_voxel)
    down.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=feature_voxel*2.5,max_nn=40))
    fpfh=o3d.pipelines.registration.compute_fpfh_feature(
        down,o3d.geometry.KDTreeSearchParamHybrid(radius=feature_voxel*5.0,max_nn=100))
    return down,fpfh


def global_hypotheses(source,target,expected_m,feature_voxel=0.20):
    hs=[]
    cs=source.mean(0); ct=target.mean(0)
    # Transparent geometry multistart. Centre displacement supplies direction only;
    # its norm is replaced by the physically measured odometry displacement.
    for deg in range(0,360,30):
        T=T_yaw(math.radians(deg)); guess=ct-T[:3,:3]@cs
        T[:3,3]=guess
        T=project_translation_norm(T,expected_m,fallback=guess)
        hs.append((f'yaw_{deg:03d}_fixed_norm',T))

    sd,sf=o3d_prepare(source,feature_voxel)
    td,tf=o3d_prepare(target,feature_voxel)
    reg=o3d.pipelines.registration

    try:
        fgr=reg.registration_fgr_based_on_feature_matching(
            sd,td,sf,tf,
            reg.FastGlobalRegistrationOption(
                maximum_correspondence_distance=feature_voxel*2.0,
                iteration_number=96,
                tuple_scale=0.90,
                maximum_tuple_count=2000))
        hs.append(('FPFH_FGR',project_translation_norm(np.asarray(fgr.transformation),expected_m)))
    except Exception as e:
        hs.append((f'FPFH_FGR_ERROR:{type(e).__name__}',np.eye(4)))

    for seed in (7,19,43):
        try:
            o3d.utility.random.seed(seed)
            rr=reg.registration_ransac_based_on_feature_matching(
                sd,td,sf,tf,True,
                feature_voxel*2.5,
                reg.TransformationEstimationPointToPoint(False),
                3,
                [
                    reg.CorrespondenceCheckerBasedOnEdgeLength(0.85),
                    reg.CorrespondenceCheckerBasedOnDistance(feature_voxel*2.5),
                ],
                reg.RANSACConvergenceCriteria(60000,0.999))
            hs.append((f'FPFH_RANSAC_seed_{seed}',project_translation_norm(np.asarray(rr.transformation),expected_m)))
        except Exception as e:
            hs.append((f'FPFH_RANSAC_seed_{seed}_ERROR:{type(e).__name__}',np.eye(4)))
    return hs


def candidate_set(source,target,expected_m,label):
    raw=[]
    for method,T0 in global_hypotheses(source,target,expected_m):
        if '_ERROR:' in method:
            continue
        T=fixed_norm_icp(source,target,T0,expected_m,max_corr=1.0,iters=22,sample=12000)
        fit,rmse,p90,n=evaluate(source,target,T,threshold=0.45,sample=24000)
        score=fit-0.45*min(1.0,rmse/0.45)
        raw.append({'method':method,'T':T,'fitness_coarse':fit,'rmse_coarse_m':rmse,'score_coarse':score,'corr_coarse':n})

    raw.sort(key=lambda x:x['score_coarse'],reverse=True)
    fine=[]
    for c in raw[:7]:
        T=fixed_norm_icp(source,target,c['T'],expected_m,max_corr=0.40,iters=70,sample=40000)
        fit,rmse,p90,n=evaluate(source,target,T,threshold=0.30,sample=45000)
        score=fit-0.60*min(1.0,rmse/0.30)
        fine.append({
            'method':c['method'],'T':T,'fitness':fit,'rmse_m':rmse,'p90_m':p90,
            'correspondences':n,'score':score,'translation_norm_m':float(np.linalg.norm(T[:3,3])),
            'expected_translation_norm_m':float(expected_m),
            'translation_norm_error_m':abs(float(np.linalg.norm(T[:3,3]))-float(expected_m)),
        })
    fine.sort(key=lambda x:x['score'],reverse=True)
    if not fine:
        raise RuntimeError(f'no registration candidates for {label}')
    return fine[:5]


def rotation_angle_deg(R):
    return math.degrees(math.acos(float(np.clip((np.trace(R)-1.0)*0.5,-1.0,1.0))))


def cycle_metrics(T21,T32,T31,d31):
    chain=T21@T32
    delta=np.linalg.inv(T31)@chain
    return {
        'translation_cycle_error_m':float(np.linalg.norm(delta[:3,3])),
        'rotation_cycle_error_deg':rotation_angle_deg(delta[:3,:3]),
        'chain_scan03_to_scan01_translation_norm_m':float(np.linalg.norm(chain[:3,3])),
        'recorded_scan03_to_scan01_displacement_m':float(d31),
        'chain_displacement_norm_error_m':abs(float(np.linalg.norm(chain[:3,3]))-float(d31)),
    }


def compact_candidate(c):
    return {k:v for k,v in c.items() if k!='T'}


def save_xyz(path,p):
    np.savetxt(path,p,fmt='%.6f')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--environment-dir',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--voxel',type=float,default=0.05)
    ap.add_argument('--min-range',type=float,default=0.25)
    ap.add_argument('--max-range',type=float,default=15.0)
    a=ap.parse_args()
    root=Path(a.environment_dir); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)

    scans=[]; sels=[]
    report={
        'method':'FPFH global hypotheses + odometry-displacement-constrained ICP + three-edge cycle selection',
        'reference':'scan_01',
        'voxel_m':a.voxel,
        'range_m':[a.min_range,a.max_range],
        'base_to_lidar_translation_m':[0.0,0.0,0.0],
        'base_to_lidar_translation_source':'project_constraint',
        'extrinsic_rotation_assumed':False,
        'physical_constraint_explanation':'With coincident robot and LiDAR origins, the norm of each inter-scan transform translation equals the recorded robot-origin displacement, regardless of the unknown constant LiDAR/base rotation.',
        'scans':{}
    }
    for i in range(1,4):
        name=f'scan_{i:02d}'
        p,sel,frames,frame_count=load_cloud(root/name,a.voxel,a.min_range,a.max_range)
        scans.append(p); sels.append(sel); save_xyz(out/f'{name}_raw.xyz',p)
        report['scans'][name]={
            'points':len(p),'cloud_frames':frame_count,'frame_ids':frames,
            'selection_pose_xyz_m':sel.get('pose')
        }

    p=[np.asarray(s.get('pose',[0,0,0]),float) for s in sels]
    d21=float(np.linalg.norm(p[1]-p[0]))
    d32=float(np.linalg.norm(p[2]-p[1]))
    d31=float(np.linalg.norm(p[2]-p[0]))

    C21=candidate_set(scans[1],scans[0],d21,'scan02_to_scan01')
    C32=candidate_set(scans[2],scans[1],d32,'scan03_to_scan02')
    C31=candidate_set(scans[2],scans[0],d31,'scan03_to_scan01')

    best=None
    for a21,a32,a31 in itertools.product(C21,C32,C31):
        cyc=cycle_metrics(a21['T'],a32['T'],a31['T'],d31)
        # Individual geometric quality plus strong consistency penalties.
        total=(a21['score']+a32['score']+a31['score']
               -0.85*cyc['translation_cycle_error_m']
               -0.015*cyc['rotation_cycle_error_deg']
               -0.85*cyc['chain_displacement_norm_error_m'])
        if best is None or total>best[0]:
            best=(total,a21,a32,a31,cyc)

    total,a21,a32,a31,cyc=best
    T21=a21['T']; T31=a31['T']
    registered=[scans[0],transform(scans[1],T21),transform(scans[2],T31)]

    report['pairwise_validation']={
        'scan02_to_scan01_candidates':[compact_candidate(c) for c in C21],
        'scan03_to_scan02_candidates':[compact_candidate(c) for c in C32],
        'scan03_to_scan01_candidates':[compact_candidate(c) for c in C31],
        'selected_scan03_to_scan02':compact_candidate(a32),
        'cycle':cyc,
        'joint_score':float(total),
    }

    def reg_record(c,expected,T):
        return {
            **compact_candidate(c),
            'recorded_stationary_position_displacement_m':float(expected),
            'translation_constraint_applied':True,
            'transform_source_to_scan01':T.tolist(),
        }

    report['scans']['scan_02']['registration_to_scan_01']=reg_record(a21,d21,T21)
    report['scans']['scan_03']['registration_to_scan_01']=reg_record(a31,d31,T31)

    # Conservative acceptance gates: all three geometry edges must have overlap,
    # and the independently estimated 3->1 transform must agree with 3->2->1.
    selected=(a21,a32,a31)
    min_fit=min(c['fitness'] for c in selected)
    max_rmse=max(c['rmse_m'] for c in selected)
    accepted=(
        min_fit>=0.25 and
        max_rmse<=0.22 and
        cyc['translation_cycle_error_m']<=0.75 and
        cyc['rotation_cycle_error_deg']<=20.0 and
        cyc['chain_displacement_norm_error_m']<=0.75
    )
    report['acceptance']={
        'accepted':bool(accepted),
        'minimum_pair_fitness':float(min_fit),
        'maximum_pair_rmse_m':float(max_rmse),
        'thresholds':{
            'min_pair_fitness':0.25,
            'max_pair_rmse_m':0.22,
            'max_cycle_translation_m':0.75,
            'max_cycle_rotation_deg':20.0,
            'max_chain_displacement_norm_error_m':0.75,
        }
    }
    report['accepted']=bool(accepted)

    save_xyz(out/'scan_01_registered.xyz',registered[0])
    save_xyz(out/'scan_02_registered.xyz',registered[1])
    save_xyz(out/'scan_03_registered.xyz',registered[2])
    merged=voxel(np.vstack(registered),a.voxel)
    save_xyz(out/'merged_registered.xyz',merged)
    report['merged_points']=len(merged)
    report['caution']=(
        'The zero-translation base/LiDAR constraint is used only to constrain inter-scan '
        'translation magnitudes to measured odometry displacements. No LiDAR/base rotation '
        'is assumed. The merged cloud/OctoMap is canonical only when acceptance.accepted is true.'
    )
    (out/'registration_metrics.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
