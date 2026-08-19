# Approach 2 — three stationary scans + ICP — complete RViz evidence

Each original stationary scan retains its source selection plus a real RViz accumulation video and fitted isometric/top/side screenshots. `icp/` retains raw and registered XYZ point sets, quantitative rigid transforms and isolated before/after RViz evidence. `merged_cloud/` contains only measured points after ICP, with three RViz perspectives. `octomap/` integrates the three registered raw scans using their three distinct ICP-estimated sensor origins, and contains a real build video, isometric/top/side screenshots, a real RViz 3D orbit, and native `.bt/.ot` maps.

No undocumented robot/LiDAR rotation is used in this static method and no unobserved surfaces are reconstructed.
