# Odometry + LiDAR metric fusion — rotation calibration pending

The project constraint is now explicit: `base_link -> unilidar_lidar` translation is exactly `(0, 0, 0) m`.

The recorded TF graph does not contain the robot/LiDAR rotation, so a fused metric cloud must not assume an arbitrary orientation. The remaining extrinsic unknown is **rotation only**.

The repository now includes a zero-translation hand-eye calibration pipeline that estimates this rotation independently from recorded robot odometry and KISS-ICP relative motions on HcMR, ISR run 1 and ISR run 2, and accepts it only if the three estimates are physically consistent.

If that cross-run calibration gate fails, valid resolutions are: recover/measure the mounting rotation, explicitly confirm aligned robot/LiDAR axes if physically true, or record a dedicated calibration trajectory. Translation is not a blocker.
