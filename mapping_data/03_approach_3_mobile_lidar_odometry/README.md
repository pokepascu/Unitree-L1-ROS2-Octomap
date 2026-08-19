# 03 — Mobile LiDAR + robot odometry

Continuous source recordings are referenced, never duplicated:
- `HcMR_lab` → `bags/raw/HcMR_lab_2026-08-07_21-13-45/`
- `ISR_5th_floor_run_1` → `bags/raw/ISR_5th_floor_run_1_2026-08-07_21-31-58/`
- `ISR_5th_floor_run_2` → `bags/raw/ISR_5th_floor_run_2_2026-08-07_21-48-31/`

Each run has a `source.yaml` manifest in this folder. Generated evidence is written under `results/approach_3/<run>/`.

## Robot/LiDAR extrinsic constraint

The translation from `base_link` to `unilidar_lidar` is fixed by the project to exactly:

`[0.0, 0.0, 0.0] m`

No non-zero LiDAR translation is used anywhere in Approach 3. The rotational extrinsic is not directly recorded in the source TF graph and is therefore not silently set to identity. The pipeline estimates only that rotation from relative-motion agreement between the recorded `/odom` trajectory and KISS-ICP. The estimate is labelled derived calibration and must pass quantitative residual/observability gates before odometry+LiDAR fusion is accepted as canonical.

## Evidence groups

- `raw_lidar/`: raw mobile PointCloud2 RViz video and still evidence;
- `odometry/`: recorded robot trajectory and TF audit;
- `kiss_icp/`: independent LiDAR-only KISS-ICP v1.3.0 trajectory/local-map evidence;
- `calibration/`: zero-translation constraint plus derived rotation estimate and residuals;
- `odometry_lidar_fusion/`: 0.10 m / 15 m OctoMap and RViz evidence only when calibration is accepted, otherwise an explicit blocker;
- `loam_like/`: compatibility/calibration status for LiDAR-inertial or LOAM-family methods.

A missing or rejected rotation calibration is not replaced by a guessed value. The corresponding map remains explicitly blocked and the resolution path is documented.
