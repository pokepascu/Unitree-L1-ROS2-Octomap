# 01 — Single stationary scan

Approach 1 is generated for both `HcMR_lab` and `ISR_5th_floor` from the verified stationary sources:

- HcMR: `study_data/approach_1_single_static/HcMR_lab/scan_01/`
- ISR: `study_data/approach_1_single_static/ISR_5th_floor/scan_01/`

## Canonical RViz2 PointCloud2 evidence — present

For both environments, `results/approach_1/rviz_evidence/<environment>/pointcloud/` contains:

- temporal raw PointCloud2 accumulation video;
- fitted/wide final isometric screenshot;
- fitted/wide final top screenshot;
- fitted/wide final side screenshot;
- the RViz configurations needed to reopen the view.

The fitted camera configurations use the reduced evidence distances selected after visual review (approximately 26 m isometric, 28 m top and 26 m side) so the measured cloud occupies substantially more of the image while retaining its full visible extent.

## OctoMap evidence — present

For HcMR and ISR, `results/approach_1/octomap/<environment>/` contains both:

- `raw_pointcloud/` — OctoMap built from the raw stationary PointCloud2 stream;
- `conservative_cleaned/` — derived conservative comparison, without deleting ambiguous stable geometry.

Each map set retains the RViz construction video, isometric/top/side screenshots, 3D RViz orbit video, `map.bt`, full `map.ot`, RViz configurations and parameters/reopen information.

Raw evidence remains the reference. Cleaned data are explicitly derived and never replace the raw acquisition. The source rosbag is never modified.

## Local evidence mirror

The generated user-facing evidence is now also available directly under `mapping_data/01_approach_1_single_static/evidence/`, preserving the relative structure of `results/approach_1/`. This includes RViz2 screenshots/videos, OctoMap `.bt`/`.ot` files, RViz configurations and compact parameters/metadata. The source MCAP recordings remain only under `study_data/`/`bags/raw/`.
