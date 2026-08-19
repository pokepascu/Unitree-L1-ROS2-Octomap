#!/usr/bin/env python3
"""Approach 1: stationary Unitree L1 PointCloud2 reconstruction and conservative cleaning.

The script never edits the source rosbag. It writes derived clouds, masks,
metrics and visualisations. Human contamination is treated conservatively:
low-persistence foreground is flagged separately, while persistent compact
foreground is reported as ambiguous and is NOT automatically deleted.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d
import yaml
from mcap.reader import make_reader
from mcap_ros2.decoder import DecoderFactory
from scipy.spatial import cKDTree

PF = {1:'i1',2:'u1',3:'i2',4:'u2',5:'i4',6:'u4',7:'f4',8:'f8'}


def pointcloud_dtype(msg):
    names=[]; formats=[]; offsets=[]
    endian='>' if msg.is_bigendian else '<'
    for f in msg.fields:
        if f.datatype not in PF:
            continue
        names.append(f.name)
        base=np.dtype(endian+PF[f.datatype])
        formats.append(base if f.count == 1 else (base,(f.count,)))
        offsets.append(int(f.offset))
    return np.dtype({'names':names,'formats':formats,'offsets':offsets,'itemsize':int(msg.point_step)})


def decode_xyz(msg):
    dt=pointcloud_dtype(msg)
    if not all(k in dt.names for k in ('x','y','z')):
        raise RuntimeError(f'PointCloud2 fields do not contain x/y/z: {dt.names}')
    arr=np.frombuffer(msg.data,dtype=dt,count=int(msg.width)*int(msg.height))
    xyz=np.column_stack((arr['x'],arr['y'],arr['z'])).astype(np.float64,copy=False)
    extra={}
    for key in ('intensity','reflectivity','ring','time','t','offset_time'):
        if key in dt.names:
            v=np.asarray(arr[key])
            if v.ndim==1: extra[key]=v.astype(np.float64,copy=False)
    return xyz,extra,dt


def voxel_unique(points, voxel):
    keys=np.floor(points/voxel).astype(np.int64)
    _,idx=np.unique(keys,axis=0,return_index=True)
    return points[idx],keys[idx]


def write_ply(path, points):
    pc=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points.astype(np.float64)))
    o3d.io.write_point_cloud(str(path),pc,write_ascii=False,compressed=True)


def plane_metrics(points, max_planes=4, threshold=0.03):
    remain=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    planes=[]
    for _ in range(max_planes):
        if len(remain.points)<1000: break
        model,inds=remain.segment_plane(distance_threshold=threshold,ransac_n=3,num_iterations=1200)
        if len(inds)<500: break
        p=np.asarray(remain.points)[inds]
        a,b,c,d=model
        dist=np.abs(p@np.array([a,b,c])+d)/max(1e-12,math.sqrt(a*a+b*b+c*c))
        planes.append({'model':[float(x) for x in model],'inliers':int(len(inds)),
                       'rmse_m':float(np.sqrt(np.mean(dist*dist))),
                       'p95_abs_residual_m':float(np.percentile(dist,95))})
        remain=remain.select_by_index(inds,invert=True)
    return planes,np.asarray(remain.points)


def split_half_distance(a,b,max_points=100000):
    if len(a)==0 or len(b)==0:return {}
    if len(a)>max_points: a=a[np.linspace(0,len(a)-1,max_points).astype(int)]
    if len(b)>max_points: b=b[np.linspace(0,len(b)-1,max_points).astype(int)]
    ta=cKDTree(a); tb=cKDTree(b)
    da,_=tb.query(a,k=1,workers=-1); db,_=ta.query(b,k=1,workers=-1)
    d=np.concatenate([da,db])
    return {'median_m':float(np.median(d)),'p90_m':float(np.percentile(d,90)),
            'p95_m':float(np.percentile(d,95)),'rmse_m':float(np.sqrt(np.mean(d*d)))}


def plot_xy(points,path,title,max_points=250000):
    if len(points)>max_points:
        points=points[np.linspace(0,len(points)-1,max_points).astype(int)]
    fig,ax=plt.subplots(figsize=(8,8)); sc=ax.scatter(points[:,0],points[:,1],s=.25,c=points[:,2])
    ax.set_aspect('equal','box'); ax.set_xlabel('x [m]'); ax.set_ylabel('y [m]'); ax.set_title(title)
    fig.colorbar(sc,ax=ax,label='z [m]'); fig.tight_layout(); fig.savefig(path,dpi=180); plt.close(fig)


def plot_hist(data,path,xlabel,title,bins=80):
    fig,ax=plt.subplots(figsize=(8,4.5)); ax.hist(data,bins=bins); ax.set_xlabel(xlabel); ax.set_ylabel('count'); ax.set_title(title)
    fig.tight_layout(); fig.savefig(path,dpi=180); plt.close(fig)


def plot_overlay(base,flagged,path,title,max_points=180000):
    if len(base)>max_points: base=base[np.linspace(0,len(base)-1,max_points).astype(int)]
    if len(flagged)>max_points//2: flagged=flagged[np.linspace(0,len(flagged)-1,max_points//2).astype(int)]
    fig,ax=plt.subplots(figsize=(8,8)); ax.scatter(base[:,0],base[:,1],s=.2,label='conservative cleaned cloud')
    if len(flagged): ax.scatter(flagged[:,0],flagged[:,1],s=1.0,label='dynamic/foreground candidates')
    ax.set_aspect('equal','box'); ax.set_xlabel('x [m]'); ax.set_ylabel('y [m]'); ax.set_title(title); ax.legend(markerscale=4)
    fig.tight_layout(); fig.savefig(path,dpi=180); plt.close(fig)


def rotating_video(points,out_dir,name):
    frames=out_dir/'video_frames'; frames.mkdir(exist_ok=True)
    if len(points)>80000: points=points[np.linspace(0,len(points)-1,80000).astype(int)]
    for i,az in enumerate(np.linspace(0,355,48)):
        fig=plt.figure(figsize=(8,6)); ax=fig.add_subplot(111,projection='3d')
        ax.scatter(points[:,0],points[:,1],points[:,2],s=.2,c=points[:,2])
        ax.set_xlabel('x [m]'); ax.set_ylabel('y [m]'); ax.set_zlabel('z [m]'); ax.view_init(elev=25,azim=az)
        ax.set_title(name); fig.tight_layout(); fig.savefig(frames/f'{i:03d}.png',dpi=110); plt.close(fig)
    try:
        subprocess.run(['ffmpeg','-y','-framerate','12','-i',str(frames/'%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p',str(out_dir/f'{name}.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except Exception as exc:
        print('VIDEO_WARNING',exc)


def process(bag:Path,out:Path,cfg:dict):
    out.mkdir(parents=True,exist_ok=True)
    frames=[]; times=[]; schema=None; extras=set(); frame_ids=[]; raw_counts=[]
    with bag.open('rb') as f:
        r=make_reader(f,decoder_factories=[DecoderFactory()])
        for _,channel,msg,ros in r.iter_decoded_messages(topics=['/unilidar/cloud']):
            xyz,extra,dt=decode_xyz(ros)
            schema=ros
            extras.update(extra.keys()); frame_ids.append(ros.header.frame_id); raw_counts.append(len(xyz)); times.append(int(msg.log_time))
            frames.append(xyz)
    if not frames: raise RuntimeError(f'No /unilidar/cloud frames in {bag}')
    t0=min(times); t1=max(times); duration=(t1-t0)/1e9
    schema_report={'frame_id_values':sorted(set(frame_ids)),'frame_count':len(frames),'duration_s':duration,
        'effective_hz':len(frames)/duration if duration>0 else None,'width':int(schema.width),'height':int(schema.height),
        'point_step':int(schema.point_step),'row_step':int(schema.row_step),'is_bigendian':bool(schema.is_bigendian),'is_dense':bool(schema.is_dense),
        'fields':[{'name':f.name,'offset':int(f.offset),'datatype':int(f.datatype),'count':int(f.count)} for f in schema.fields],
        'extra_numeric_fields_found':sorted(extras),'raw_points_total':int(sum(raw_counts)),
        'raw_points_per_frame_median':float(np.median(raw_counts))}
    (out/'pointcloud2_schema.json').write_text(json.dumps(schema_report,indent=2))

    min_range=float(cfg['min_range_m']); max_range=float(cfg['max_range_m']); voxel=float(cfg['voxel_m'])
    block_s=float(cfg['temporal_block_s'])
    block_vox=defaultdict(set); global_sum=defaultdict(lambda:np.zeros(3)); global_n=defaultdict(int)
    first_pts=[]; second_pts=[]; valid_total=0; range_total=0; ranges=[]
    for xyz,t in zip(frames,times):
        finite=np.isfinite(xyz).all(axis=1); xyz=xyz[finite]; valid_total+=len(xyz)
        rr=np.linalg.norm(xyz,axis=1); mask=(rr>=min_range)&(rr<=max_range); xyz=xyz[mask]; rr=rr[mask]; range_total+=len(xyz)
        if len(rr): ranges.append(rr)
        vp,keys=voxel_unique(xyz,voxel)
        b=int(((t-t0)/1e9)//block_s)
        for p,k in zip(vp,keys):
            kt=tuple(int(x) for x in k); block_vox[b].add(kt); global_sum[kt]+=p; global_n[kt]+=1
        (first_pts if t < (t0+t1)//2 else second_pts).append(vp)
    keys=list(global_n); centers=np.array([global_sum[k]/global_n[k] for k in keys])
    nblocks=max(1,len(block_vox)); block_count=defaultdict(int)
    for s in block_vox.values():
        for k in s:block_count[k]+=1
    persistence=np.array([block_count[k]/nblocks for k in keys])
    observations=np.array([global_n[k] for k in keys])

    pc=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(centers))
    _,sor_idx=pc.remove_statistical_outlier(nb_neighbors=int(cfg['sor_neighbors']),std_ratio=float(cfg['sor_std_ratio']))
    sor_mask=np.zeros(len(centers),bool); sor_mask[np.asarray(sor_idx,dtype=int)]=True
    sor=centers[sor_mask]; sor_p=persistence[sor_mask]
    # Radius filter on the SOR-retained cloud.
    p2=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(sor))
    _,ror_idx=p2.remove_radius_outlier(nb_points=int(cfg['ror_min_points']),radius=float(cfg['ror_radius_m']))
    ror_mask=np.zeros(len(sor),bool); ror_mask[np.asarray(ror_idx,dtype=int)]=True
    clean=sor[ror_mask]; clean_p=sor_p[ror_mask]

    # Dynamic candidate mask: low temporal persistence, restricted to near/mid field.
    c_range=np.linalg.norm(clean,axis=1)
    dyn=(clean_p < float(cfg['dynamic_persistence_threshold'])) & (c_range <= float(cfg['dynamic_candidate_max_range_m']))
    dynamic_candidates=clean[dyn]
    conservative=clean  # Dynamic candidates remain in the conservative cloud; mask is separate.

    # Ambiguous compact foreground: remove dominant planes only for segmentation, not from final cloud.
    planes,nonplanar=plane_metrics(conservative,max_planes=int(cfg['max_planes']),threshold=float(cfg['plane_threshold_m']))
    ambiguous=[]
    if len(nonplanar)>50:
        near=nonplanar[np.linalg.norm(nonplanar,axis=1)<=float(cfg['human_review_max_range_m'])]
        if len(near)>30:
            npc=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(near))
            labels=np.asarray(npc.cluster_dbscan(eps=float(cfg['cluster_eps_m']),min_points=int(cfg['cluster_min_points']),print_progress=False))
            for lab in sorted(set(labels)):
                if lab<0: continue
                q=near[labels==lab]; ext=q.max(0)-q.min(0); ctr=np.median(q,0)
                # Broad human-like geometry only; not a truth label.
                if 0.25<=max(ext[0],ext[1])<=1.5 and 0.7<=ext[2]<=2.4:
                    ambiguous.append({'label':int(lab),'points':int(len(q)),'extent_m':[float(x) for x in ext],'centroid_m':[float(x) for x in ctr]})

    # Quality metrics.
    first=np.vstack(first_pts) if first_pts else np.empty((0,3)); second=np.vstack(second_pts) if second_pts else np.empty((0,3))
    first,_=voxel_unique(first,voxel) if len(first) else (first,None); second,_=voxel_unique(second,voxel) if len(second) else (second,None)
    split=split_half_distance(first,second)
    metrics={'source_bag':str(bag),'frames':len(frames),'duration_s':duration,'valid_points_total':valid_total,'range_kept_points_total':range_total,
        'global_voxels':int(len(centers)),'after_sor_voxels':int(len(sor)),'after_ror_voxels':int(len(clean)),
        'sor_removed_fraction':float(1-len(sor)/max(1,len(centers))),'ror_removed_fraction_of_sor':float(1-len(clean)/max(1,len(sor))),
        'temporal_blocks':int(nblocks),'dynamic_candidate_voxels':int(dyn.sum()),'dynamic_candidate_fraction':float(dyn.mean()) if len(dyn) else 0.0,
        'persistence_median':float(np.median(clean_p)) if len(clean_p) else None,'persistence_p10':float(np.percentile(clean_p,10)) if len(clean_p) else None,
        'split_half_symmetric_nn':split,'dominant_planes':planes,'ambiguous_compact_vertical_clusters':ambiguous,
        'note':'Dynamic candidates are flagged, not automatically deleted. Ambiguous compact vertical clusters are review candidates only.'}
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2))
    (out/'config_used.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))

    write_ply(out/'raw_voxelized.ply',centers); write_ply(out/'conservative_cleaned.ply',conservative)
    write_ply(out/'dynamic_foreground_candidates.ply',dynamic_candidates)
    np.savez_compressed(out/'analysis_arrays.npz',centers=centers,persistence=persistence,observations=observations,clean=clean,clean_persistence=clean_p,dynamic_mask=dyn)
    plot_xy(centers,out/'01_raw_topdown.png','Raw stationary cloud - voxelized')
    plot_xy(conservative,out/'02_conservative_cleaned_topdown.png','Conservative cleaned cloud')
    plot_overlay(conservative,dynamic_candidates,out/'03_dynamic_candidates_overlay.png','Dynamic/foreground candidates - not automatically removed')
    if ranges: plot_hist(np.concatenate(ranges),out/'04_range_histogram.png','range [m]','Point range distribution')
    plot_hist(clean_p,out/'05_persistence_histogram.png','temporal block persistence','Voxel persistence distribution')
    rotating_video(conservative,out,'conservative_cleaned_rotation')
    print(json.dumps(metrics,indent=2))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--bag',required=True); ap.add_argument('--config',required=True); ap.add_argument('--out',required=True)
    args=ap.parse_args(); cfg=yaml.safe_load(Path(args.config).read_text()); process(Path(args.bag),Path(args.out),cfg)
if __name__=='__main__': main()
