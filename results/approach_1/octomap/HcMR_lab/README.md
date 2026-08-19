# Approach 1 — final wide RViz OctoMap evidence

`raw_pointcloud/` is the canonical sensor reference and retains all measured points, including transient scene content. `conservative_cleaned/` is a derived comparison using range filtering, 5 cm voxelization, Statistical Outlier Removal and Radius Outlier Removal; no low-persistence foreground is silently removed. Both maps use 0.10 m OctoMap resolution, 15 m max range and the stationary `unilidar_lidar` frame.

Each mode contains a real RViz build video, wide isometric/top/side screenshots, a real RViz orbit video, native `.bt` and `.ot` maps, parameters and the RViz configs used to reopen the result.
