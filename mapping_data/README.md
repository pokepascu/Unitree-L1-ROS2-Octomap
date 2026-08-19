# Mapping data organization

This directory is the user-facing organization of the Unitree L1 mapping study. Raw recordings remain immutable in `bags/raw/` and verified extracted stationary segments remain in `study_data/`; this directory groups provenance, method outputs, RViz evidence and reopen instructions by experiment.

## Layout

- `00_preliminary_data/` — legacy/preliminary HcMR experiment from 2026-08-04. These files are retained as historical evidence and are not used as canonical results for the three final approaches.
- `01_approach_1_single_static/` — one verified stationary scan per environment, PointCloud2 accumulation, conservative processing and OctoMap.
- `02_approach_2_three_static_icp/` — three verified stationary scans, rigid registration by Iterative Closest Point (ICP), merged cloud and OctoMap.
- `03_approach_3_mobile_lidar_odometry/` — continuous mobile LiDAR with odometry/TF, odometry baseline, KISS-ICP and LOAM-like comparison when the required frame transform is available from recorded or documented data.

## Evidence rule

Canonical visual evidence is produced in RViz2. Analytical Matplotlib/Open3D figures may exist as secondary diagnostics but do not replace RViz evidence. Raw evidence is retained; derived cleaned or registered data are clearly labelled. Unknown/occluded surfaces are never synthesized.

## Source-of-truth data

Large MCAP files are not copied here. Manifests in each approach point to the immutable source under `bags/raw/` or to verified segments under `study_data/`. Generated maps live under `results/` and are mirrored/referenced here by method documentation.
