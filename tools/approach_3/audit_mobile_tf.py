#!/usr/bin/env python3
"""Audit mobile Unitree L1 rosbag TF/odometry before any LiDAR+odom fusion."""
import argparse,csv,json
from collections import Counter,defaultdict,deque
from pathlib import Path
from mcap.reader import make_reader
from mcap_ros2.decoder import DecoderFactory

ap=argparse.ArgumentParser(); ap.add_argument('--bag',required=True); ap.add_argument('--out',required=True)
a=ap.parse_args(); bag=Path(a.bag); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)

topics=Counter(); edges=defaultdict(lambda:{'count':0,'translations':[],'rotations':[]}); odom=[]; cloud_frames=Counter()
with bag.open('rb') as f:
    r=make_reader(f,decoder_factories=[DecoderFactory()])
    for _,channel,msg,ros in r.iter_decoded_messages():
        topics[channel.topic]+=1
        if channel.topic in ('/tf','/tf_static'):
            for tr in ros.transforms:
                p=tr.header.frame_id.strip('/'); c=tr.child_frame_id.strip('/'); k=f'{p}->{c}'
                e=edges[k]; e['count']+=1
                if len(e['translations'])<20:
                    t=tr.transform.translation; q=tr.transform.rotation
                    e['translations'].append([t.x,t.y,t.z]); e['rotations'].append([q.x,q.y,q.z,q.w])
        elif channel.topic=='/odom':
            p=ros.pose.pose.position; q=ros.pose.pose.orientation
            odom.append([msg.log_time/1e9,p.x,p.y,p.z,q.x,q.y,q.z,q.w,ros.header.frame_id,ros.child_frame_id])
        elif channel.topic=='/unilidar/cloud':
            cloud_frames[ros.header.frame_id]+=1

# Connectivity graph, treating each TF edge as traversable both directions.
g=defaultdict(set)
for k in edges:
    p,c=k.split('->',1); g[p].add(c); g[c].add(p)

def path(src,dst):
    q=deque([(src,[src])]); seen={src}
    while q:
        n,pth=q.popleft()
        if n==dst:return pth
        for x in g[n]:
            if x not in seen: seen.add(x); q.append((x,pth+[x]))
    return None

sensor='unilidar_lidar'; base='base_link'; odom_frame='odom'
base_sensor_path=path(base,sensor); odom_sensor_path=path(odom_frame,sensor)
report={
 'source_bag':str(bag), 'topic_counts':dict(topics), 'pointcloud_frame_ids':dict(cloud_frames),
 'tf_edges':dict(edges), 'odom_samples':len(odom),
 'base_to_sensor_tf_path':base_sensor_path, 'odom_to_sensor_tf_path':odom_sensor_path,
 'full_recorded_tf_chain_available':bool(odom_sensor_path),
 'direct_base_sensor_edge_recorded': any(k in edges for k in (f'{base}->{sensor}',f'{sensor}->{base}')),
 'fusion_policy':'Fuse LiDAR into odom only when recorded/documented TF supplies a complete metric transform chain. Never invent missing LiDAR rotation.'
}
(out/'tf_audit.json').write_text(json.dumps(report,indent=2))
with (out/'odometry_trajectory.csv').open('w',newline='') as f:
    w=csv.writer(f); w.writerow(['time_s','x_m','y_m','z_m','qx','qy','qz','qw','frame_id','child_frame_id']); w.writerows(odom)
print(json.dumps({k:report[k] for k in ('pointcloud_frame_ids','odom_samples','base_to_sensor_tf_path','odom_to_sensor_tf_path','full_recorded_tf_chain_available','direct_base_sensor_edge_recorded')},indent=2))
