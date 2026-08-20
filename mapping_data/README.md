# Mapping data organization

This directory is the user-facing organization of the Unitree L1 mapping study. Raw recordings remain immutable in `bags/raw/` and verified stationary segments remain in `study_data/`; `mapping_data/` organizes provenance and points to the canonical generated evidence under `results/` without duplicating multi-hundred-megabyte source recordings.

## Layout and current status

- `00_preliminary_data/` — legacy/preliminary HcMR experiment from 2026-08-04, retained as historical evidence and not used as canonical output for the three final approaches.
- `01_approach_1_single_static/` — **complete** for HcMR and ISR: raw stationary PointCloud2 RViz evidence, raw and conservative-cleaned OctoMaps, fitted RViz views, videos, `.bt`, `.ot`, configs and parameters.
- `02_approach_2_three_static_icp/` — **complete** for HcMR and ISR: three raw stationary scans, global ICP before/after evidence, registered/merged clouds and final OctoMaps with RViz videos/views and map files.
- `03_approach_3_mobile_lidar_odometry/` — raw mobile LiDAR, recorded odometry and KISS-ICP v1.3.0 outputs are **complete for HcMR, ISR run 1 and ISR run 2**. Robot/LiDAR translation is fixed to exactly `(0,0,0) m`. A trajectory-derived rotational calibration was attempted on all three runs and rejected by the quantitative quality gates, so canonical odometry+LiDAR OctoMap fusion remains explicitly blocked rather than being generated with an invented rotation. Full metrics are in `results/approach_3/common_extrinsic_rotation.json` and each run's `calibration/` directory.

## Canonical evidence rule

Canonical visual evidence is produced in RViz2. Analytical Matplotlib/Open3D figures may exist as secondary diagnostics but do not replace RViz evidence. Raw evidence is retained; derived cleaned, registered or calibration products are clearly labelled. Unknown or occluded surfaces are never synthesized.

## Approach 3 blocker and valid resolution paths

The translation is not a blocker: `base_link -> unilidar_lidar = (0,0,0) m` is enforced. The remaining blocker is rotational calibration. The three trajectory fits return broadly similar yaw-like rotations but none satisfies the run-level residual/observability acceptance gate, so the common calibration contains `canonical_fusion_allowed: false`.

Valid ways to complete a canonical odometry+LiDAR fusion are:

1. recover or measure the real physical robot/LiDAR mounting rotation;
2. explicitly establish that robot and LiDAR axes are physically co-oriented, if that is in fact the mounting geometry; or
3. record a dedicated calibration trajectory with stronger non-degenerate motion, then rerun the supplied zero-translation calibration and fusion workflow.

The repository intentionally does not relax these gates merely to force a visually plausible map.

## Source-of-truth data

Large MCAP files are not copied into each method directory. Manifests point to the immutable source under `bags/raw/` or to verified segments under `study_data/`. Generated evidence and maps live under `results/` and are referenced from each method README.
