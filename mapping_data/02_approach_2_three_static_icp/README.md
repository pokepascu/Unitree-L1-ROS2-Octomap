# 02 — Three stationary scans + ICP

Two environments are processed independently: `HcMR_lab` and `ISR_5th_floor`.

Source segments: `study_data/approach_2_three_static_icp/<environment>/scan_01..03/`.

Pipeline:
1. retain the three raw stationary PointCloud2 acquisitions and their selection metadata;
2. reconstruct each scan without inventing geometry;
3. use measured odometry translation only as a coarse registration aid where appropriate, not as a fabricated LiDAR rotation;
4. refine rigid alignment with Iterative Closest Point (ICP);
5. record before/after registration metrics and transformations;
6. merge the registered measured points;
7. visualize the three scans, registration and merged cloud in RViz2;
8. construct and save OctoMap (`.bt` and `.ot`) from the merged cloud;
9. save wide isometric/top/side RViz screenshots and a 3D orbit video.

Expected result structure: `results/approach_2/<environment>/{scan_01,scan_02,scan_03,icp,merged_cloud,octomap}/`.
