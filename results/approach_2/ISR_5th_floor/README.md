# Approach 2 — three stationary scans + ICP

The three original stationary PointCloud2 scans are retained with RViz videos and final views. `icp/` contains geometry-driven rigid registration, quantitative metrics, transformations and separate before/after RViz sessions. `merged_cloud/` contains only measured points after registration. `octomap/` integrates the three raw registered scans while preserving their distinct ICP-estimated sensor origins and includes native `.bt/.ot` maps plus RViz views.

No undocumented LiDAR extrinsic rotation is introduced.
