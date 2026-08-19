# HcMr laboratory ISR mapping data

This directory contains the Unitree L1 mapping session captured in the HcMr
laboratory at ISR on 2026-08-04.

## Raw ROS 2 data

- `l1_run_01.zip` contains the ROS 2 bag database and its original metadata.
  The archive is tracked with Git LFS because it is larger than GitHub's normal
  per-file limit.
- `metadata.yaml` is also provided outside the archive for quick inspection.
- The bag lasts 477.70 seconds and contains 111,709 messages: 4,105 point-cloud
  messages on `/unilidar/cloud` and 107,604 IMU messages on `/unilidar/imu`.

## RViz and OctoMap media

- `00_verification.png` through `05_fin_60s.png` show the live room map at
  several points during the capture.
- `cartographie_rviz_octomap_60s.webm` is the complete 59.96-second RViz
  recording at 1854 x 1011 and 15 frames per second.
- `cartographie_rviz_octomap_partie_00.webm` and
  `cartographie_rviz_octomap_partie_01.webm` are shorter clips from the same
  recording.

The live session used ROS 2 Humble, an OctoMap resolution of 0.10 m, a 15.0 m
maximum sensor range, and `unilidar_lidar` as the fixed frame.
