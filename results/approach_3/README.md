# Approach 3 — mobile LiDAR + robot odometry

## Completed evidence

The three mobile runs are retained independently:

- `HcMR_lab/`
- `ISR_5th_floor_run_1/`
- `ISR_5th_floor_run_2/`

For each run, the repository contains:

- `raw_lidar/` — raw mobile Unitree L1 PointCloud2 RViz evidence;
- `odometry/` — recorded robot odometry trajectory, RViz view and TF audit;
- `kiss_icp/` — KISS-ICP v1.3.0 LiDAR-only trajectory and RViz evidence;
- `calibration/` — zero-translation robot/LiDAR constraint and run-specific rotational hand-eye estimate;
- `odometry_lidar_fusion/` — explicit calibration blocker because the rotation quality gate did not pass;
- `loam_like/` — method/calibration status; no unsupported LiDAR-inertial result is fabricated.

## Extrinsic geometry

`base_link -> unilidar_lidar` translation is fixed to exactly:

```text
x = 0.0 m
y = 0.0 m
z = 0.0 m
```

No translation is estimated and no non-zero translation is used anywhere in Approach 3.

The rotational extrinsic is not present in the recorded TF graph. It was therefore estimated independently from relative-motion agreement between recorded robot odometry and KISS-ICP, rather than assumed.

## Rotation-calibration result

The three fitted rotations are predominantly yaw-like and broadly similar:

- HcMR: approximately `+23.13 deg` yaw-equivalent;
- ISR run 1: approximately `+20.01 deg` yaw-equivalent;
- ISR run 2: approximately `+24.89 deg` yaw-equivalent.

These values are **diagnostic estimates, not accepted calibration constants**. All three run-level quality gates rejected the trajectory-derived calibration.

Key residuals:

| Run | synchronized samples | translation direction median | translation RMSE | rotation conjugacy median | rotation conjugacy p90 | status |
|---|---:|---:|---:|---:|---:|---|
| HcMR | 1515 | 31.57 deg | 0.415 m | 4.33 deg | 9.50 deg | rejected |
| ISR run 1 | 5349 | 63.73 deg | 3.094 m | 5.68 deg | 27.04 deg | rejected |
| ISR run 2 | 4153 | 40.59 deg | 1.378 m | 3.25 deg | 11.62 deg | rejected |

The aggregate file `common_extrinsic_rotation.json` therefore records:

```text
canonical_fusion_allowed = false
status = rejected_common
accepted_runs = []
```

The identity matrix stored in the rejected aggregate is a sentinel for **no canonical common rotation**; it must not be interpreted as a measured identity mounting rotation.

## Consequence for the odometry + LiDAR map

A canonical mobile OctoMap combining robot odometry with the LiDAR is deliberately **not generated**, because doing so would require selecting an unvalidated rotational extrinsic. Producing a visually plausible map by relaxing the gate would not make it metrically trustworthy.

KISS-ICP remains the completed LiDAR-only mobile mapping/trajectory baseline, while recorded odometry remains available independently.

## Valid resolution paths

1. Recover or directly measure the physical mounting rotation between `base_link` and `unilidar_lidar`.
2. If the sensor axes are physically co-oriented, establish that fact explicitly; only then may the identity rotation be used as a documented geometry constraint.
3. Record a dedicated calibration trajectory with stronger non-degenerate rotational and translational excitation, then rerun the supplied zero-translation hand-eye calibration.

Until one of these conditions is met, the fusion blocker is an intended scientific safeguard rather than a missing implementation.
