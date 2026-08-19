#!/usr/bin/env bash
set -euo pipefail
source /opt/ros/humble/setup.bash
ros2 run tf2_ros static_transform_publisher --x 2.092804177 --y -0.827533503 --z -0.019208834 --qx -0.000089858 --qy -0.002795856 --qz 0.002021813 --qw 0.999994044 --frame-id unilidar_lidar --child-frame-id scan_02 >/tmp/tf_scan_02.log 2>&1 &
ros2 run tf2_ros static_transform_publisher --x 4.398262297 --y -2.001553987 --z -0.026951800 --qx 0.002426488 --qy -0.002443769 --qz -0.027012712 --qw 0.999629158 --frame-id unilidar_lidar --child-frame-id scan_03 >/tmp/tf_scan_03.log 2>&1 &
