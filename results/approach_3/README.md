# Approach 3 — mobile LiDAR + robot odometry

## Current result

The three mobile runs are retained and processed independently:

- `HcMR_lab/`
- `ISR_5th_floor_run_1/`
- `ISR_5th_floor_run_2/`

For each run, the repository contains:

- `raw_lidar/` — raw mobile Unitree L1 PointCloud2 RViz evidence;
- `odometry/` — recorded robot odometry trajectory, RViz view and TF audit;
- `kiss_icp/` — KISS-ICP v1.3.0 LiDAR-only trajectory and RViz evidence;
- `calibration/` — the zero-translation constraint and the earlier trajectory-derived rotational hand-eye estimate with its residuals;
- `odometry_lidar_fusion/` — the completed fixed-mount odometry + LiDAR OctoMap baseline and canonical RViz evidence;
- `loam_like/` — LiDAR-inertial / LOAM-family method and calibration status; unsupported inertial calibration is not fabricated.

## Fixed mounting geometry used for fusion

The LiDAR is rigidly attached to the robot. The mapping baseline therefore uses one constant transform throughout each acquisition:

```text
transform: base_link_from_unilidar_lidar
translation = [0.0, 0.0, 0.0] m
roll        = 0.0 deg
pitch       = 0.0 deg
yaw         = +23.0 deg
```

The zero translation is a known project constraint. The `+23.0 deg` yaw is a user-supported fixed-mount working constraint that is consistent with all three trajectory-derived yaw-like estimates. It is not described as an independently metrologically measured mounting calibration.

The exact working transform is stored in `fixed_mount_extrinsic_23deg.json` and copied into every `odometry_lidar_fusion/` result folder.

## Preserved trajectory-derived calibration diagnostics

Before the fixed mounting orientation was supplied, rotation was estimated independently from relative-motion agreement between recorded robot odometry and KISS-ICP. The three estimates were predominantly yaw-like:

- HcMR: approximately `+23.13 deg`;
- ISR run 1: approximately `+20.01 deg`;
- ISR run 2: approximately `+24.89 deg`.

These remain **diagnostic estimates, not accepted metrological calibration constants**. Their original run-level quality gates rejected them because the odometry/KISS-ICP trajectory residuals were too large for an independent calibration claim.

Key preserved residuals:

| Run | synchronized samples | translation direction median | translation RMSE | rotation conjugacy median | rotation conjugacy p90 | diagnostic status |
|---|---:|---:|---:|---:|---:|---|
| HcMR | 1515 | 31.57 deg | 0.415 m | 4.33 deg | 9.50 deg | rejected |
| ISR run 1 | 5349 | 63.73 deg | 3.094 m | 5.68 deg | 27.04 deg | rejected |
| ISR run 2 | 4153 | 40.59 deg | 1.378 m | 3.25 deg | 11.62 deg | rejected |

`common_extrinsic_rotation.json` is retained unchanged as the result of that earlier diagnostic gate. Its identity matrix is a sentinel for **no independently accepted common trajectory calibration**; it is not the transform used by the completed +23 deg mapping baseline.

## Completed odometry + LiDAR baseline

For every mobile run, `odometry_lidar_fusion/` now contains:

```text
01_build_rviz.mp4
02_final_isometric.png
03_final_top.png
04_final_side.png
05_3d_orbit_rviz.mp4
README.md
fixed_mount_extrinsic_23deg.json
map.bt
map.ot
octomap_isometric.rviz
octomap_top.rviz
octomap_side.rviz
parameters.yaml
```

The generated OctoMaps use:

```text
fixed frame             = odom
resolution              = 0.10 m
sensor-model max range  = 15.0 m
filter_ground_plane     = false
input                    = /fused_cloud
```

The `0.10 m` resolution is an OctoMap occupancy discretization parameter, not a claim about LiDAR measurement precision.

The current fusion implementation assigns each LiDAR cloud to the nearest recorded odometry sample when the time difference is within the configured tolerance (`0.08 s` by default). It does not claim continuous-time pose interpolation or scan deskew.

## Interpretation

The fixed +23 deg result is a reproducible **working mapping baseline** supported by the known rigid mounting and by the approximate agreement of the three independent trajectory-derived yaw estimates. It should not be promoted to an independently measured extrinsic calibration unless the physical mounting angle is later measured directly.

KISS-ICP remains available as an independent LiDAR-only mobile baseline, allowing the odometry-fused result to be compared against a method that does not depend on the robot/LiDAR mounting yaw in the same way.
