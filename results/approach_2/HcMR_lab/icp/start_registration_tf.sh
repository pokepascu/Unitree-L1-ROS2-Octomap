#!/usr/bin/env bash
set -euo pipefail
source /opt/ros/humble/setup.bash
ros2 run tf2_ros static_transform_publisher --x 0.470480828 --y -0.044209192 --z 0.010409157 --qx 0.000093799 --qy -0.000963033 --qz -0.011403532 --qw 0.999934509 --frame-id unilidar_lidar --child-frame-id scan_02 >/tmp/tf_scan_02.log 2>&1 &
ros2 run tf2_ros static_transform_publisher --x 0.191290925 --y 0.106231227 --z 0.010876358 --qx 0.001868574 --qy 0.002268273 --qz -0.028243924 --qw 0.999596741 --frame-id unilidar_lidar --child-frame-id scan_03 >/tmp/tf_scan_03.log 2>&1 &
