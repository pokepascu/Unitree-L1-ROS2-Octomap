#!/usr/bin/env python3
"""Estimate base_link <- unilidar_lidar rotation from recorded odometry and KISS-ICP.

Translation is constrained to exactly zero by project geometry.  The estimate is
therefore a rotation-only hand-eye calibration.  Relative translations and
relative rotation vectors obey the same mapping when t_base_lidar == 0:

    t_base(i,j) ~= R_base_lidar @ t_lidar(i,j)
    w_base(i,j) ~= R_base_lidar @ w_lidar(i,j)

The script is deliberately conservative: it writes quantitative residuals and a
status.  Downstream fusion is permitted only when status == "accepted".
"""
import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


def read_traj(path):
    rows=[]
    with open(path,newline='') as f:
        for r in csv.DictReader(f):
            rows.append([
                float(r['time_s']), float(r['x_m']), float(r['y_m']), float(r['z_m']),
                float(r['qx']), float(r['qy']), float(r['qz']), float(r['qw'])])
    a=np.asarray(rows,dtype=float)
    if len(a)<3: raise RuntimeError(f'not enough trajectory samples in {path}')
    return a


def q_to_R(q):
    x,y,z,w=q
    n=math.sqrt(x*x+y*y+z*z+w*w)
    if n<1e-12: return np.eye(3)
    x,y,z,w=x/n,y/n,z/n,w/n
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]],dtype=float)


def R_to_q(R):
    t=float(np.trace(R))
    if t>0:
        s=math.sqrt(t+1.0)*2; w=.25*s
        x=(R[2,1]-R[1,2])/s; y=(R[0,2]-R[2,0])/s; z=(R[1,0]-R[0,1])/s
    else:
        i=int(np.argmax(np.diag(R)))
        if i==0:
            s=math.sqrt(max(1e-16,1+R[0,0]-R[1,1]-R[2,2]))*2
            x=.25*s; y=(R[0,1]+R[1,0])/s; z=(R[0,2]+R[2,0])/s; w=(R[2,1]-R[1,2])/s
        elif i==1:
            s=math.sqrt(max(1e-16,1+R[1,1]-R[0,0]-R[2,2]))*2
            y=.25*s; x=(R[0,1]+R[1,0])/s; z=(R[1,2]+R[2,1])/s; w=(R[0,2]-R[2,0])/s
        else:
            s=math.sqrt(max(1e-16,1+R[2,2]-R[0,0]-R[1,1]))*2
            z=.25*s; x=(R[0,2]+R[2,0])/s; y=(R[1,2]+R[2,1])/s; w=(R[1,0]-R[0,1])/s
    q=np.array([x,y,z,w],dtype=float); q/=np.linalg.norm(q)
    if q[3]<0: q=-q
    return q


def rotvec(R):
    c=np.clip((np.trace(R)-1.0)*0.5,-1.0,1.0); a=math.acos(float(c))
    if a<1e-8: return np.zeros(3)
    if abs(math.pi-a)<1e-4:
        vals,vecs=np.linalg.eig(R); axis=np.real(vecs[:,np.argmin(np.abs(vals-1))]); axis/=np.linalg.norm(axis)
        return axis*a
    axis=np.array([R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1]])/(2*math.sin(a))
    return axis*a


def angle_R(R):
    return math.degrees(math.acos(float(np.clip((np.trace(R)-1)*.5,-1,1))))


def fit_R(src,dst,w):
    H=np.zeros((3,3))
    for s,d,ww in zip(src,dst,w): H += ww*np.outer(d,s)
    U,S,Vt=np.linalg.svd(H)
    D=np.eye(3); D[2,2]=np.sign(np.linalg.det(U@Vt))
    return U@D@Vt,S


def nearest_indices(ref_t, query_t):
    idx=np.searchsorted(ref_t,query_t)
    idx=np.clip(idx,1,len(ref_t)-1)
    left=idx-1; choose=np.where(np.abs(ref_t[left]-query_t)<=np.abs(ref_t[idx]-query_t),left,idx)
    return choose


def percentile(x,p):
    return float(np.percentile(np.asarray(x,dtype=float),p)) if len(x) else None


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--odom',required=True); ap.add_argument('--kiss',required=True); ap.add_argument('--out',required=True)
    ap.add_argument('--max-sync-s',type=float,default=0.08)
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    O=read_traj(args.odom); K=read_traj(args.kiss)
    oi=nearest_indices(O[:,0],K[:,0]); sync=np.abs(O[oi,0]-K[:,0]); valid=sync<=args.max_sync_s
    if valid.sum()<30: raise RuntimeError(f'only {valid.sum()} synchronized KISS samples within {args.max_sync_s}s')
    # Keep KISS samples with a reliable nearest odometry sample.
    kk=np.where(valid)[0]; K=K[kk]; Omatch=O[oi[kk]]; sync=sync[kk]
    RK=np.stack([q_to_R(q) for q in K[:,4:8]]); RO=np.stack([q_to_R(q) for q in Omatch[:,4:8]])
    trans_pairs=[]; rot_pairs=[]; motions=[]
    windows=(0.5,1.0,2.0,3.0)
    for i in range(len(K)):
        for win in windows:
            j=int(np.searchsorted(K[:,0],K[i,0]+win))
            if j>=len(K) or abs((K[j,0]-K[i,0])-win)>0.20: continue
            # Relative motion expressed in the starting body / LiDAR frame.
            tA=RO[i].T@(Omatch[j,1:4]-Omatch[i,1:4]); RA=RO[i].T@RO[j]
            tB=RK[i].T@(K[j,1:4]-K[i,1:4]); RB=RK[i].T@RK[j]
            na=float(np.linalg.norm(tA)); nb=float(np.linalg.norm(tB))
            wA=rotvec(RA); wB=rotvec(RB); aa=float(np.linalg.norm(wA)); ab=float(np.linalg.norm(wB))
            if na>0.08 and nb>0.08:
                trans_pairs.append((tB,tA,min(2.0,max(.2,min(na,nb)))))
            if aa>math.radians(2.0) and ab>math.radians(2.0):
                rot_pairs.append((wB,wA,min(2.0,max(.2,min(aa,ab)*3))))
            motions.append((tA,tB,RA,RB))
    if len(trans_pairs)<12: raise RuntimeError(f'insufficient translational excitation: {len(trans_pairs)} motion pairs')
    src=[]; dst=[]; ww=[]; kinds=[]
    for b,a,w in trans_pairs:
        src.append(b/np.linalg.norm(b)); dst.append(a/np.linalg.norm(a)); ww.append(w); kinds.append('translation')
    for b,a,w in rot_pairs:
        src.append(b/np.linalg.norm(b)); dst.append(a/np.linalg.norm(a)); ww.append(w); kinds.append('rotation')
    src=np.asarray(src); dst=np.asarray(dst); ww=np.asarray(ww)
    keep=np.ones(len(src),dtype=bool)
    R=np.eye(3); S=np.zeros(3)
    for _ in range(4):
        R,S=fit_R(src[keep],dst[keep],ww[keep])
        pred=(R@src.T).T
        dots=np.clip(np.sum(pred*dst,axis=1),-1,1); err=np.degrees(np.arccos(dots))
        cutoff=min(30.0,float(np.percentile(err[keep],85))+2.0)
        new=err<=cutoff
        if new.sum()<max(12,int(.55*len(src))): break
        keep=new
    R,S=fit_R(src[keep],dst[keep],ww[keep])
    q=R_to_q(R)
    # Validation on original metric relative motions.
    terr=[]; tdir=[]; scale=[]; rerr=[]
    for tA,tB,RA,RB in motions:
        na=np.linalg.norm(tA); nb=np.linalg.norm(tB)
        if na>.08 and nb>.08:
            p=R@tB; terr.append(float(np.linalg.norm(tA-p)))
            tdir.append(math.degrees(math.acos(float(np.clip(np.dot(tA,p)/(na*np.linalg.norm(p)),-1,1)))))
            scale.append(float(na/nb))
        if angle_R(RA)>2 and angle_R(RB)>2:
            rerr.append(angle_R(RA.T@(R@RB@R.T)))
    med_motion=percentile([np.linalg.norm(x[0]) for x in motions if np.linalg.norm(x[0])>.08],50) or 1.0
    rmse=float(math.sqrt(np.mean(np.square(terr)))) if terr else 1e9
    nrmse=rmse/max(.05,med_motion)
    obs=float(S[-1]/S[0]) if len(S)==3 and S[0]>1e-12 else 0.0
    scale_med=percentile(scale,50)
    metrics={
      'synchronized_samples':int(len(K)), 'sync_error_s_median':percentile(sync,50), 'sync_error_s_p95':percentile(sync,95),
      'translation_motion_pairs':len(trans_pairs), 'rotation_motion_pairs':len(rot_pairs), 'combined_vectors_kept':int(keep.sum()),
      'observability_singular_ratio':obs,
      'translation_direction_error_deg_median':percentile(tdir,50), 'translation_direction_error_deg_p90':percentile(tdir,90),
      'translation_rmse_m':rmse, 'translation_normalized_rmse':nrmse, 'translation_scale_ratio_median_odom_over_kiss':scale_med,
      'rotation_conjugacy_error_deg_median':percentile(rerr,50), 'rotation_conjugacy_error_deg_p90':percentile(rerr,90)
    }
    accepted=(len(trans_pairs)>=30 and len(rot_pairs)>=8 and obs>=0.015 and
              metrics['translation_direction_error_deg_median'] is not None and metrics['translation_direction_error_deg_median']<15 and
              nrmse<0.45 and scale_med is not None and .70<scale_med<1.30 and
              metrics['rotation_conjugacy_error_deg_median'] is not None and metrics['rotation_conjugacy_error_deg_median']<10)
    provisional=(not accepted and len(trans_pairs)>=20 and obs>=0.008 and
                 metrics['translation_direction_error_deg_median'] is not None and metrics['translation_direction_error_deg_median']<25 and
                 nrmse<0.70 and scale_med is not None and .55<scale_med<1.45)
    status='accepted' if accepted else ('provisional_not_canonical' if provisional else 'rejected')
    report={
      'transform':'base_link_from_unilidar_lidar',
      'translation_m':[0.0,0.0,0.0],
      'translation_source':'project_geometry_constraint_from_user',
      'rotation_matrix_base_from_lidar':R.tolist(),
      'rotation_quaternion_xyzw_base_from_lidar':q.tolist(),
      'rotation_source':'derived_hand_eye_alignment_of_recorded_robot_odometry_and_KISS-ICP_relative_motions',
      'status':status,
      'canonical_fusion_allowed':bool(accepted),
      'metrics':metrics,
      'method_notes':[
        'No translation is estimated; it is fixed to exactly zero.',
        'No identity rotation is assumed.',
        'The estimate is derived from trajectory agreement, not a laboratory extrinsic calibration.',
        'Canonical odometry/LiDAR fusion is gated by quantitative residual and observability tests.'
      ]
    }
    (out/'extrinsic_rotation_estimate.json').write_text(json.dumps(report,indent=2))
    with (out/'motion_pair_residuals.csv').open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['type','angular_direction_error_deg'])
        pred=(R@src.T).T; errs=np.degrees(np.arccos(np.clip(np.sum(pred*dst,axis=1),-1,1)))
        for k,e in zip(kinds,errs): w.writerow([k,float(e)])
    print(json.dumps({'status':status,'quaternion_xyzw':q.tolist(),'metrics':metrics},indent=2))

if __name__=='__main__': main()
