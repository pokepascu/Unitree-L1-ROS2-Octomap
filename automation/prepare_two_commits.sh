#!/usr/bin/env bash
set -euo pipefail

BASE_SHA=$(git rev-parse HEAD)
echo "$BASE_SHA" > /tmp/base_sha

# ---- Commit 1: immutable source bags ----
git rm -f \
  bags/rosbag2_2026_08_07-21_13_45_0.mcap \
  bags/rosbag2_2026_08_07-21_31_58_0.mcap \
  bags/rosbag2_2026_08_07-21_48_31_0.mcap \
  bags/README.txt 2>/dev/null || true
rm -f bags/.gitkeep

grep -qxF 'bags/**/*.mcap filter=lfs diff=lfs merge=lfs -text' .gitattributes || \
  echo 'bags/**/*.mcap filter=lfs diff=lfs merge=lfs -text' >> .gitattributes
grep -qxF 'study_data/**/*.mcap filter=lfs diff=lfs merge=lfs -text' .gitattributes || \
  echo 'study_data/**/*.mcap filter=lfs diff=lfs merge=lfs -text' >> .gitattributes

mkdir -p \
  bags/raw/HcMR_lab_2026-08-07_21-13-45 \
  bags/raw/ISR_5th_floor_run_1_2026-08-07_21-31-58 \
  bags/raw/ISR_5th_floor_run_2_2026-08-07_21-48-31

cp /tmp/nas_download/rosbag2_2026_08_07-21_13_45/rosbag2_2026_08_07-21_13_45_0.mcap \
  bags/raw/HcMR_lab_2026-08-07_21-13-45/
cp /tmp/nas_download/rosbag2_2026_08_07-21_13_45/metadata.yaml \
  bags/raw/HcMR_lab_2026-08-07_21-13-45/
cp /tmp/nas_download/rosbag2_2026_08_07-21_31_58/rosbag2_2026_08_07-21_31_58_0.mcap \
  bags/raw/ISR_5th_floor_run_1_2026-08-07_21-31-58/
cp /tmp/nas_download/rosbag2_2026_08_07-21_31_58/metadata.yaml \
  bags/raw/ISR_5th_floor_run_1_2026-08-07_21-31-58/
cp /tmp/nas_download/rosbag2_2026_08_07-21_48_31/rosbag2_2026_08_07-21_48_31_0.mcap \
  bags/raw/ISR_5th_floor_run_2_2026-08-07_21-48-31/
cp /tmp/nas_download/rosbag2_2026_08_07-21_48_31/metadata.yaml \
  bags/raw/ISR_5th_floor_run_2_2026-08-07_21-48-31/
cp /tmp/nas_download/download_manifest.json bags/raw/download_manifest.json

cat > bags/README.md <<'EOF'
# Unitree L1 mobile mapping datasets

This directory contains the **raw ROS 2 Humble recordings** used for the HcMR / ISR 3D mapping study with the **Unitree L1 3D LiDAR** and a mobile robot platform.

## Source recordings

| Directory | Environment | Role |
|---|---|---|
| `raw/HcMR_lab_2026-08-07_21-13-45/` | HcMR laboratory, ISR | Laboratory mobile acquisition |
| `raw/ISR_5th_floor_run_1_2026-08-07_21-31-58/` | ISR building, **5th floor** | Continuous mobile acquisition, run 1 |
| `raw/ISR_5th_floor_run_2_2026-08-07_21-48-31/` | ISR building, **5th floor** | Continuous mobile acquisition, run 2 |

**Correction:** older notes called these recordings “Floor 4”. The confirmed acquisition location is the **5th floor of the ISR building**.

Each source directory contains the original binary `.mcap` and its original `metadata.yaml`. The raw recordings are treated as immutable source data; study subsets are derived under `../study_data/`. `raw/download_manifest.json` records exact downloaded sizes and locally computed SHA-256 digests.

## Topics used by the study

The recordings contain the data needed by the mapping study, including:

- `/unilidar/cloud` — `sensor_msgs/msg/PointCloud2`: Unitree L1 3D point cloud.
- `/unilidar/imu` — `sensor_msgs/msg/Imu`: Unitree L1 inertial data.
- `/odom` — `nav_msgs/msg/Odometry`: mobile-platform odometry.
- `/tf` — `tf2_msgs/msg/TFMessage`: recorded dynamic transforms.
- `/cmd_vel` — `geometry_msgs/msg/Twist`: commanded platform velocity.

The complete bags are retained because Approach 3 requires the continuous LiDAR, odometry, TF and motion-command history. The same source recordings are searched for low-motion intervals to derive reproducible 30 s subsets for Approaches 1 and 2.

## Unitree L1 mounting transform

Confirmed LiDAR-origin translation relative to `base_link`:

```text
base_link -> unilidar_lidar
x = 0.0 m
y = 0.0 m
z = 1.0 m
```

The mounting **rotation has not yet been explicitly measured/confirmed**. No non-zero rotation is invented here. Before quantitative mobile mapping, the LiDAR-to-base rotational extrinsic must be confirmed; if the sensor axes were physically aligned with `base_link`, that should be documented explicitly as identity rotation.

## Experimental comparison

1. **Single static scan (~30 s)** → accumulated Unitree L1 point cloud → OctoMap.
2. **Three static scans (~30 s each)** from different poses → Iterative Closest Point (ICP) registration → merged cloud → OctoMap.
3. **Continuous mobile mapping** → LiDAR + robot motion/odometry, with candidate methods including odometry-based cloud accumulation, KISS-ICP and suitable LiDAR(-inertial) SLAM pipelines.

## Visualisation and storage

`unitree_l1.rviz` is retained as an RViz2 starting configuration. Large `.mcap` datasets are tracked with **Git LFS**.
EOF

git add .gitattributes bags
git commit -m "Add raw Unitree L1 rosbags for HcMR lab and ISR 5th floor"

# ---- Commit 2: derived static material ----
mkdir -p tools
cp /tmp/automation/extract_static_rosbags.py tools/extract_static_rosbags.py
python3 tools/extract_static_rosbags.py

find study_data -type f -name '*.mcap' -print0 | while IFS= read -r -d '' f; do
  mcap doctor "$f"
done

cat > study_data/README.md <<'EOF'
# Static datasets derived for mapping Approaches 1 and 2

These are **derived 30-second ROS 2 MCAP subsets** extracted from the immutable recordings in `bags/raw/`. Every subset preserves the recorded messages inside its selected time interval, including LiDAR, IMU, odometry, TF and velocity commands when present.

## Approach 1 — single static scan

- `approach_1_single_static/HcMR_lab/scan_01/static_30s.mcap`
- `approach_1_single_static/ISR_5th_floor/scan_01/static_30s.mcap`

Purpose: accumulate a stationary Unitree L1 point cloud for approximately 30 s, inspect LiDAR quality and generate an occupancy representation with OctoMap without introducing a continuously estimated trajectory.

## Approach 2 — three static scans + ICP

- `approach_2_three_static_icp/HcMR_lab/scan_01..03/`
- `approach_2_three_static_icp/ISR_5th_floor/scan_01..03/`

Purpose: independently accumulate three stationary clouds, use known/estimated scanner poses as initial information, refine cloud-to-cloud registration with **Iterative Closest Point (ICP)**, merge the registered clouds and generate an OctoMap.

## Reproducible static-window selection

`tools/extract_static_rosbags.py` evaluates sliding 30 s windows using `/odom`. Lower scores correspond to lower observed motion and combine:

- positional spread around the median pose;
- accumulated odometric path length;
- yaw variation;
- 95th-percentile linear speed;
- 95th-percentile angular speed.

The selector avoids overlapping windows and preferentially chooses spatially distinct poses. `selection.yaml` beside each derived bag contains the exact source, absolute start/end timestamps and residual-motion metrics. `static_selection_report.csv` summarizes the three selected stations per environment.

**Scientific limitation:** “static” here means *supported by recorded robot odometry as a low-motion interval*. It is not external motion-capture ground truth. Before the three poses are used as absolute geometric ground truth, their physical locations should be independently measured/documented.

## LiDAR extrinsic available for later mobile mapping

Confirmed translation `base_link -> unilidar_lidar`: **(0.0, 0.0, 1.0) m**. The rotational extrinsic remains to be explicitly confirmed.
EOF

git add study_data tools/extract_static_rosbags.py
git commit -m "Add static rosbags for single-scan and three-scan ICP studies"

# Require exactly two commits relative to the main SHA from which this run started.
test "$(git rev-list --count "$BASE_SHA"..HEAD)" -eq 2
