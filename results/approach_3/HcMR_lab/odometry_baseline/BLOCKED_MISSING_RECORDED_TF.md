# Odometry + LiDAR metric fusion not generated

The recorded TF graph does not provide a complete `odom -> ... -> unilidar_lidar` transform chain. The project confirms the LiDAR translation but does not explicitly establish the missing rotation. A metric fused cloud or OctoMap would therefore require inventing an extrinsic rotation, which this pipeline deliberately refuses to do. See `../odometry/tf_audit.json` for the recorded evidence.
