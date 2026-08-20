# Approach 3 — mobile LiDAR + odometry

`raw_lidar/` is the unregistered mobile sensor evidence (short decay prevents a false pose-free map). `odometry/` contains the measured robot trajectory and a TF audit. `odometry_baseline/` contains a metric odom-frame OctoMap only when the recorded TF graph reaches the LiDAR frame; otherwise it contains an explicit calibration blocker. `kiss_icp/` contains an independent generic LiDAR-odometry result generated with KISS-ICP v1.3.0 using the LiDAR frame as its base frame. `loam_like/` records validation status rather than fabricating unsupported output.
