# Mapping data organization

`mapping_data/` is the user-facing organization of the Unitree L1 mapping study. The immutable source recordings remain under `bags/raw/`, and verified stationary extracts remain under `study_data/`. Large MCAP source recordings are never duplicated here.

## Layout

- `00_preliminary_data/` — legacy/preliminary HcMR material retained only as historical evidence.
- `01_approach_1_single_static/` — one verified stationary scan per environment, with local mirrored PointCloud2 and OctoMap evidence.
- `02_approach_2_three_static_icp/` — three stationary scans per environment, rigid registration by Iterative Closest Point (ICP), merged cloud and OctoMap evidence.
- `03_approach_3_mobile_lidar_odometry/` — mobile LiDAR, robot odometry, KISS-ICP diagnostics and the fixed-mount odometry + LiDAR OctoMap baseline for HcMR and the two ISR runs.

## Evidence mirror policy

Each numbered approach contains an `evidence/` tree mirroring the generated evidence from its corresponding `results/approach_*` directory. The mirror keeps RViz2 PNG screenshots, MP4 recordings, OctoMap `.bt`/`.ot` files, RViz configurations, parameters and compact metadata/metrics needed to interpret or reopen the evidence.

`results/` remains the computational source of truth. `mapping_data/*/evidence/` is the organized browsing/delivery view. The mirrored files are byte-identical copies before Git staging; MP4 and OctoMap binaries are stored with Git LFS so identical objects are deduplicated.

No `.mcap` source recording is copied into the evidence mirror.

## Canonical visual evidence rule

Canonical visual evidence is produced in RViz2. Analytical Matplotlib/Open3D figures may remain as secondary diagnostics, but do not replace RViz evidence. Raw evidence is retained and derived cleaned/registered/calibration products remain explicitly labelled.

## Approach 3 fixed-mount baseline

The current project working transform for the mobile odometry + LiDAR baseline is constant over each acquisition:

```text
base_link -> unilidar_lidar
translation = [0.0, 0.0, 0.0] m
roll        = 0.0 deg
pitch       = 0.0 deg
yaw         = +23.0 deg
```

The `+23.0 deg` yaw is a user-supported fixed-mount working constraint consistent with the trajectory-derived yaw-like estimates, not an independently metrologically measured calibration. Earlier rejected trajectory-derived calibration fits remain preserved as diagnostics.

The odometry + LiDAR OctoMap baseline uses fixed frame `odom`, OctoMap resolution `0.10 m` and maximum inserted sensor range `15 m`. The `0.10 m` value is occupancy-map resolution, not Unitree L1 ranging accuracy.
