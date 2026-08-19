# Approach 1 - single stationary Unitree L1 scan

This directory contains the reproducible outputs of the first mapping approach: a single stationary Unitree L1 acquisition, conservative point-cloud reconstruction, quality assessment, and visual verification.

## Source datasets

| Environment | LiDAR frames | Effective duration | Effective LiDAR rate |
|---|---:|---:|---:|
| HcMR laboratory | 115 | 14.874 s | 7.73 Hz |
| ISR 5th floor | 272 | 35.175 s | 7.73 Hz |

The HcMR acquisition is shorter than the original approximately 30 s target. The source MCAPs remain unchanged under `study_data/approach_1_single_static/`.

## PointCloud2 decoding

Both subsets decode in frame `unilidar_lidar`. Recorded fields are `x`, `y`, `z`, `intensity`, `ring`, and `time` with a 32-byte point step. Exact schema reports are stored in each environment's `pointcloud2_schema.json`.

## Conservative cleaning

Applied parameters are recorded in `config_used.yaml`. Current baseline:

1. finite XYZ validation;
2. range gate 0.25-15.0 m;
3. 0.05 m voxelization;
4. Statistical Outlier Removal: 30 neighbours, standard-deviation ratio 2.0;
5. Radius Outlier Removal: radius 0.12 m, minimum 2 neighbours.

Resulting voxel counts:

| Environment | Voxelized | After SOR | After ROR |
|---|---:|---:|---:|
| HcMR | 71,417 | 68,940 | 68,303 |
| ISR 5th floor | 64,355 | 62,094 | 61,938 |

The conservative cleaned cloud is the principal reconstruction. Dynamic/foreground candidates are **not automatically removed**.

## Quality measurements

Split-half temporal repeatability compares the first and second halves of each static acquisition with symmetric nearest-neighbour distances.

| Metric | HcMR | ISR 5th floor |
|---|---:|---:|
| Median discrepancy | 2.92 cm | 2.71 cm |
| 95th percentile | 8.56 cm | 8.26 cm |
| RMSE | 4.65 cm | 6.27 cm |

Dominant RANSAC planes have local residual RMSE values of approximately 1.1-1.6 cm in both environments. These are internal consistency measurements, **not absolute ground-truth mapping accuracy**.

## Two people in the HcMR room

Two people were known to be present, often near the robot. The processing therefore avoids any unsupported semantic deletion.

The initial low-persistence diagnostic flags 49.5% of HcMR voxels and 73.4% of ISR voxels. These high fractions demonstrate that the current 5 cm / 1 s / 0.20 persistence rule is sensitive to sparse LiDAR sampling and must **not** be interpreted as a percentage of people or moving objects. The mask is retained only as a diagnostic layer for visual review.

A persistent standing person can be indistinguishable from static furniture using a single LiDAR viewpoint. Surfaces hidden behind an occluder are never reconstructed or hallucinated.

## Static image evidence

Each environment directory contains the same numbered verification images:

- `01_raw_topdown.png` - raw stationary PointCloud2 accumulation after voxelization;
- `02_conservative_cleaned_topdown.png` - geometry retained by conservative cleaning;
- `03_dynamic_candidates_overlay.png` - initial low-persistence foreground candidates overlaid on the retained cloud;
- `04_range_histogram.png` - measured range distribution;
- `05_persistence_histogram.png` - temporal voxel-persistence distribution.

## Video evidence

`evidence/` is reserved for the standardized video audit trail:

1. `01_raw_pointcloud_accumulation.mp4` - sequential `/unilidar/cloud` accumulation;
2. `02_conservative_cleaned_rotation.mp4` - 360-degree 3D inspection of the cleaned cloud;
3. `03_dynamic_foreground_evolution.mp4` - evolution of low-persistence foreground candidates;
4. `04_odometry_stationarity.mp4` - `/odom` position and linear/angular speed verification.

The evidence README explains what each video verifies and its limitations. MP4 files are tracked with Git LFS.

## Reproducibility

- analysis script: `tools/approach_1/analyze_static_cloud.py`;
- video generator: `tools/approach_1/generate_evidence_videos.py`;
- parameters: `config/approach_1/`;
- numerical results: `metrics.json` and `pointcloud2_schema.json` beside each environment;
- automated execution: `.github/workflows/approach1_static_analysis.yml` and `.github/workflows/approach1_evidence_videos.yml`.

## Next step

Generate OctoMap occupancy maps from the conservative static reconstructions, quantify occupied/free/unknown space and resolution sensitivity, and then proceed to Approach 2 with three static views and Iterative Closest Point (ICP) registration.
