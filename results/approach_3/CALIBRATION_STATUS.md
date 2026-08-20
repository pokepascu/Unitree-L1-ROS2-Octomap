# Approach 3 fixed-mount working extrinsic

Translation `base_link -> unilidar_lidar` is fixed to exactly `(0,0,0) m`. The LiDAR is rigidly mounted and a constant `+23.0 deg` yaw (`roll=0`, `pitch=0`) is used for the odometry + LiDAR mapping baseline. This value is user-supported and consistent with the three trajectory-derived estimates near +20 to +25 deg. It is not represented as an independently metrologically measured calibration.

The previous trajectory-derived rotation calibrations remain preserved as diagnostics and remain marked rejected under their original quantitative acceptance criteria.
