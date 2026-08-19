#!/usr/bin/env bash
set -euo pipefail
source /opt/ros/humble/setup.bash
ros2 run tf2_ros static_transform_publisher --x 1.960823922 --y -0.461347103 --z -0.020212202 --qx 0.002631698 --qy -0.001185326 --qz 0.164593115 --qw 0.986357327 --frame-id unilidar_lidar --child-frame-id scan_02 >/tmp/tf_scan_02.log 2>&1 &
ros2 run tf2_ros static_transform_publisher --x 1.318522980 --y -0.746341508 --z -0.002923280 --qx 0.010951736 --qy 0.002717976 --qz 0.999842838 --qw 0.013673718 --frame-id unilidar_lidar --child-frame-id scan_03 >/tmp/tf_scan_03.log 2>&1 &
