# Approach 3 extrinsic calibration — fusion blocked

Translation `base_link -> unilidar_lidar` is fixed to exactly `(0,0,0) m`. The trajectory-derived robot/LiDAR rotation did not pass the cross-run physical-consistency gate. Canonical odometry + LiDAR fusion is therefore not generated.

Valid resolutions: recover or measure the real mounting rotation; explicitly confirm that robot and LiDAR axes are physically aligned if that is true; or record a dedicated calibration trajectory with stronger non-degenerate rotational and translational excitation.
