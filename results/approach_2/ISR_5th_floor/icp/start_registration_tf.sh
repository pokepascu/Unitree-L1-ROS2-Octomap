#!/usr/bin/env bash
set -euo pipefail
source /opt/ros/humble/setup.bash
ros2 run tf2_ros static_transform_publisher --x 2.040767832 --y -0.505779771 --z -0.022438376 --qx 0.000800856 --qy 0.000486891 --qz 0.164010841 --qw 0.986458091 --frame-id unilidar_lidar --child-frame-id scan_02 >/tmp/tf_scan_02.log 2>&1 &
ros2 run tf2_ros static_transform_publisher --x 3.922837550 --y -1.832429626 --z -0.036840429 --qx -0.002796627 --qy -0.001509819 --qz -0.012818169 --qw 0.999912793 --frame-id unilidar_lidar --child-frame-id scan_03 >/tmp/tf_scan_03.log 2>&1 &
