#!/usr/bin/env python3
"""Generate ROS 2 static TF commands from accepted Approach-2 transforms."""
import argparse, json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

ap=argparse.ArgumentParser(); ap.add_argument('--metrics',required=True); ap.add_argument('--out',required=True)
a=ap.parse_args(); d=json.loads(Path(a.metrics).read_text())
if not d.get('accepted', False):
    raise SystemExit('Approach 2 registration rejected by physical/cycle acceptance gates; refusing to publish registration TFs')
lines=['#!/usr/bin/env bash','set -euo pipefail','source /opt/ros/humble/setup.bash']
for name in ('scan_02','scan_03'):
    T=np.asarray(d['scans'][name]['registration_to_scan_01']['transform_source_to_scan01'],dtype=float)
    q=Rotation.from_matrix(T[:3,:3]).as_quat()
    t=T[:3,3]
    lines.append(
        "ros2 run tf2_ros static_transform_publisher "
        f"--x {t[0]:.9f} --y {t[1]:.9f} --z {t[2]:.9f} "
        f"--qx {q[0]:.9f} --qy {q[1]:.9f} --qz {q[2]:.9f} --qw {q[3]:.9f} "
        f"--frame-id unilidar_lidar --child-frame-id {name} >/tmp/tf_{name}.log 2>&1 &"
    )
Path(a.out).write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
