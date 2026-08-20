# Approach 3 extrinsic calibration status — fusion blocked

Translation `base_link -> unilidar_lidar` is fixed to exactly `(0, 0, 0) m`. The trajectory-derived rotation did not pass the cross-run physical-consistency gate, so odometry + LiDAR fusion remains deliberately blocked. Valid resolutions are: measure/recover the true mounting rotation; confirm explicitly that robot and LiDAR axes are physically aligned if that is true; or record a dedicated calibration trajectory with stronger rotational and translational excitation.
