# 03 — Mobile LiDAR + odometry

Continuous source recordings are referenced, not duplicated:
- HcMR: `bags/raw/HcMR_lab_2026-08-07_21-13-45/`
- ISR run 1: `bags/raw/ISR_5th_floor_run_1_2026-08-07_21-31-58/`
- ISR run 2: `bags/raw/ISR_5th_floor_run_2_2026-08-07_21-48-31/`

Required evidence groups:
- `raw_lidar/`: raw mobile PointCloud2 RViz evidence;
- `odometry/`: measured robot trajectory and TF diagnostics;
- `odometry_baseline/`: LiDAR map transformed with recorded/documented poses only;
- `kiss_icp/`: KISS-ICP trajectory/cloud/map comparison;
- `loam_like/`: compatible LiDAR-odometry method comparison;
- `octomap/`: occupancy representation generated from a metrically valid registered mobile cloud.

A mobile fusion is generated only if the transform chain needed to place `unilidar_lidar` in the odometry frame is present in recorded or explicitly documented data. The known 1 m translation alone is not sufficient to invent an unknown LiDAR rotation. If the rotation is absent, the audit output records this as a blocking calibration item rather than fabricating a map.

Expected generated structure: `results/approach_3/<environment-or-run>/...`, with RViz screenshots/videos, trajectories, transformations, map files and reproducibility instructions.
