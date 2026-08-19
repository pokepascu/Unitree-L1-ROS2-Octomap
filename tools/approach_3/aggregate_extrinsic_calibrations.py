#!/usr/bin/env python3
"""Build one common base<-LiDAR rotation from independent Approach-3 runs.

The physical extrinsic is constant across recordings. Translation is fixed to
exactly zero by the project constraint. We accept a canonical common rotation
only when at least two independently accepted trajectory calibrations agree
within a configurable angular tolerance.
"""
import argparse, json, math
from pathlib import Path
import numpy as np


def angle_deg(R):
    c=float(np.clip((np.trace(R)-1.0)*0.5,-1.0,1.0))
    return math.degrees(math.acos(c))


def R_to_q(R):
    t=float(np.trace(R))
    if t>0:
        s=math.sqrt(t+1.0)*2; q=np.array([(R[2,1]-R[1,2])/s,(R[0,2]-R[2,0])/s,(R[1,0]-R[0,1])/s,.25*s])
    else:
        i=int(np.argmax(np.diag(R)))
        if i==0:
            s=math.sqrt(max(1e-16,1+R[0,0]-R[1,1]-R[2,2]))*2
            q=np.array([.25*s,(R[0,1]+R[1,0])/s,(R[0,2]+R[2,0])/s,(R[2,1]-R[1,2])/s])
        elif i==1:
            s=math.sqrt(max(1e-16,1+R[1,1]-R[0,0]-R[2,2]))*2
            q=np.array([(R[0,1]+R[1,0])/s,.25*s,(R[1,2]+R[2,1])/s,(R[0,2]-R[2,0])/s])
        else:
            s=math.sqrt(max(1e-16,1+R[2,2]-R[0,0]-R[1,1]))*2
            q=np.array([(R[0,2]+R[2,0])/s,(R[1,2]+R[2,1])/s,.25*s,(R[1,0]-R[0,1])/s])
    q=q/np.linalg.norm(q)
    if q[3]<0:q=-q
    return q


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',action='append',required=True,help='run_name=path/to/extrinsic_rotation_estimate.json')
    ap.add_argument('--out',required=True)
    ap.add_argument('--max-angle-deg',type=float,default=10.0)
    a=ap.parse_args()
    runs={}
    accepted=[]
    for item in a.input:
        name,path=item.split('=',1)
        d=json.loads(Path(path).read_text())
        R=np.asarray(d['rotation_matrix_base_from_lidar'],float)
        runs[name]={
            'status':d.get('status'),
            'canonical_fusion_allowed':bool(d.get('canonical_fusion_allowed',False)),
            'rotation_matrix_base_from_lidar':R.tolist(),
            'rotation_quaternion_xyzw_base_from_lidar':d.get('rotation_quaternion_xyzw_base_from_lidar'),
            'metrics':d.get('metrics',{}),
        }
        if d.get('canonical_fusion_allowed',False): accepted.append((name,R))

    pairwise={}
    angles=[]
    for i,(ni,Ri) in enumerate(accepted):
        for nj,Rj in accepted[i+1:]:
            ang=angle_deg(Ri.T@Rj); pairwise[f'{ni}__{nj}']=ang; angles.append(ang)

    enough=len(accepted)>=2
    consistent=enough and (not angles or max(angles)<=a.max_angle_deg)
    if consistent:
        M=sum(R for _,R in accepted)
        U,_,Vt=np.linalg.svd(M)
        D=np.eye(3); D[2,2]=np.sign(np.linalg.det(U@Vt))
        R=U@D@Vt
        q=R_to_q(R)
    else:
        R=np.eye(3); q=R_to_q(R)

    report={
        'transform':'base_link_from_unilidar_lidar',
        'translation_m':[0.0,0.0,0.0],
        'translation_source':'project_geometry_constraint_from_user',
        'rotation_matrix_base_from_lidar':R.tolist(),
        'rotation_quaternion_xyzw_base_from_lidar':q.tolist(),
        'rotation_source':'consensus_of_independently_accepted_recorded_odom_vs_KISS_ICP_hand_eye_estimates' if consistent else 'no_canonical_common_rotation',
        'canonical_fusion_allowed':bool(consistent),
        'status':'accepted_common' if consistent else 'rejected_common',
        'accepted_runs':[n for n,_ in accepted],
        'minimum_required_accepted_runs':2,
        'max_allowed_pairwise_rotation_difference_deg':a.max_angle_deg,
        'pairwise_rotation_difference_deg':pairwise,
        'maximum_pairwise_rotation_difference_deg':max(angles) if angles else None,
        'runs':runs,
        'notes':[
            'Translation is fixed to exactly zero and is never estimated.',
            'A common rotation is required because the robot/LiDAR extrinsic is a physical constant across runs.',
            'At least two independently accepted trajectory calibrations must agree before any odometry+LiDAR map is labelled canonical.',
        ],
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
