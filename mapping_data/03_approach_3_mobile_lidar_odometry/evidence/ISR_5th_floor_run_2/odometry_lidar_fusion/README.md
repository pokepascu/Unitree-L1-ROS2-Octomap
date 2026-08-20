# Fixed-mount odometry + LiDAR OctoMap

This map uses the project working extrinsic `base_link_from_unilidar_lidar` with translation exactly `(0,0,0) m`, roll `0 deg`, pitch `0 deg`, and constant yaw `+23.0 deg`. The LiDAR is rigidly mounted, so this transform is constant throughout the acquisition. The +23 deg yaw is user-supported and consistent with the three trajectory-derived estimates, but is not described as an independently metrologically measured calibration.

OctoMap parameters: resolution `0.10 m`, maximum sensor range `15 m`, fixed frame `odom`. Resolution is an occupancy-grid parameter and is not a LiDAR accuracy claim.

The trajectory-derived calibration JSON files remain preserved separately as diagnostic evidence.
