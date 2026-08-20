# Fixed-mount odometry + LiDAR OctoMap

This map uses the project working extrinsic  with translation exactly , roll , pitch , and constant yaw . The LiDAR is rigidly mounted, so this transform is constant throughout the acquisition. The +23 deg yaw is user-supported and consistent with the three trajectory-derived estimates, but is not described as an independently metrologically measured calibration.

OctoMap parameters: resolution , maximum sensor range , fixed frame . Resolution is an occupancy-grid parameter and is not a LiDAR accuracy claim.

The trajectory-derived calibration JSON files remain preserved separately as diagnostic evidence.
