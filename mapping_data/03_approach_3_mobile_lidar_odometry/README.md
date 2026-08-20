# 03 — Mobile LiDAR + robot odometry

Continuous source recordings are referenced, never duplicated:
- `HcMR_lab` → `bags/raw/HcMR_lab_2026-08-07_21-13-45/`
- `ISR_5th_floor_run_1` → `bags/raw/ISR_5th_floor_run_1_2026-08-07_21-31-58/`
- `ISR_5th_floor_run_2` → `bags/raw/ISR_5th_floor_run_2_2026-08-07_21-48-31/`

Each run has a `source.yaml` manifest in this folder. Generated evidence is written under `results/approach_3/<run>/`.

## Fixed robot/LiDAR mounting geometry used for the mapping baseline

The LiDAR is rigidly fixed to the robot, so one constant rigid transform is used throughout each acquisition. The working project geometry is:

```text
base_link -> unilidar_lidar
translation = [0.0, 0.0, 0.0] m
roll        = 0.0 deg
pitch       = 0.0 deg
yaw         = +23.0 deg
```

The zero translation is a known project constraint. The constant `+23.0 deg` yaw is a user-supported fixed-mount working constraint and is consistent with the three independent trajectory-derived yaw-like estimates (about +20 to +25 deg). It is **not** represented as an independently metrologically measured calibration.

The earlier trajectory hand-eye estimates and their rejected quantitative gates remain preserved under `results/approach_3/<run>/calibration/` and `results/approach_3/common_extrinsic_rotation.json`. They are diagnostic evidence and are not silently rewritten as accepted calibration measurements.

## Generated evidence groups

- `raw_lidar/`: raw mobile PointCloud2 RViz evidence;
- `odometry/`: recorded robot trajectory and TF audit;
- `kiss_icp/`: independent LiDAR-only KISS-ICP v1.3.0 trajectory/local-map evidence;
- `calibration/`: zero-translation constraint plus the earlier trajectory-derived rotation diagnostics and residuals;
- `odometry_lidar_fusion/`: generated fixed-mount odometry + LiDAR baseline using `(0,0,0) m` and `+23 deg` yaw;
- `loam_like/`: LiDAR-inertial / LOAM-family method status; no unsupported inertial extrinsic is fabricated.

For each of the three mobile runs, `odometry_lidar_fusion/` contains the RViz build video, final isometric/top/side RViz captures, a 3D RViz orbit video, `map.bt`, `map.ot`, the RViz configurations, the exact mapping parameters, and a copy of the fixed-mount transform used.

## OctoMap baseline parameters

The odometry + LiDAR baseline uses:

```text
fixed frame             = odom
OctoMap resolution      = 0.10 m
sensor-model max range  = 15.0 m
input cloud             = /fused_cloud
```

The `0.10 m` value is an occupancy-map resolution and must not be interpreted as Unitree L1 measurement accuracy.

The fusion publisher associates each incoming LiDAR cloud with the nearest recorded odometry pose within the configured synchronization tolerance; it does not claim continuous-time trajectory interpolation or LiDAR deskew.

## Local evidence mirror

The generated user-facing evidence is now also available directly under `mapping_data/03_approach_3_mobile_lidar_odometry/evidence/`, preserving the relative structure of `results/approach_3/`. In particular, each run's `odometry_lidar_fusion/` RViz build video, final isometric/top/side captures, 3D orbit video, `.bt`, `.ot`, RViz configs and mapping parameters are locally mirrored. Raw MCAP recordings remain referenced from `bags/raw/` and are never duplicated here.
