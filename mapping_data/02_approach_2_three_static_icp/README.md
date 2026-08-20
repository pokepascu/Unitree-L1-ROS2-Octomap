# 02 — Three stationary scans + ICP

Approach 2 is generated independently for `HcMR_lab` and `ISR_5th_floor` from `study_data/approach_2_three_static_icp/<environment>/scan_01..03/`.

## Completed pipeline

1. the three raw stationary PointCloud2 acquisitions and their selection metadata are retained;
2. each measured scan is reconstructed without synthesizing geometry;
3. measured odometry displacement is used only as a registration constraint/diagnostic where applicable;
4. rigid alignment is refined by Iterative Closest Point (ICP);
5. before/after registration evidence and quantitative transformations are retained;
6. the registered measured points are merged;
7. raw scans, registration and merged cloud are visualized in RViz2;
8. OctoMap is built with the registered sensor origins preserved rather than pretending all scans came from scan 01;
9. `.bt`, full `.ot`, RViz construction video, isometric/top/side screenshots and a 3D RViz orbit video are retained.

## Results actually present

For both environments, `results/approach_2/<environment>/` contains:

- `scan_01/`, `scan_02/`, `scan_03/`: raw accumulation MP4, final RViz isometric/top/side views, RViz configs and `selection.yaml`;
- `icp/`: before/after global registration screenshots, raw and registered XYZ clouds, `registration_metrics.json`, merged XYZ cloud and registration TF helper;
- `merged_cloud/`: merged registered XYZ plus isometric/top/side RViz evidence;
- `octomap/`: RViz build MP4, isometric/top/side screenshots, real 3D orbit MP4, `map.bt`, `map.ot`, RViz configs and registration metrics.

No undocumented LiDAR extrinsic rotation is introduced by this static registration method.

## Local evidence mirror

The generated user-facing evidence is now also available directly under `mapping_data/02_approach_2_three_static_icp/evidence/`, preserving the relative structure of `results/approach_2/`. RViz2 captures/videos, OctoMap map files, RViz configurations, registration metrics and compact metadata are mirrored; the source MCAP recordings are not duplicated.
