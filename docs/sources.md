# Technical sources

Accessed 29 July 2026.

- SRC-001 — ROS 2 Humble platforms and support period:
  <https://docs.ros.org/en/humble/Releases/Release-Humble-Hawksbill.html>
- SRC-002 — Official ROS Docker image:
  <https://hub.docker.com/_/ros/>
- SRC-003 — Docker Engine on Ubuntu:
  <https://docs.docker.com/engine/install/ubuntu/>
- SRC-004 — Unitree UniLiDAR SDK `v1.0.16`:
  <https://github.com/unitreerobotics/unilidar_sdk/tree/v1.0.16>
- SRC-005 — Unitree ROS 2 README and officially tested environment:
  <https://github.com/unitreerobotics/unilidar_sdk/blob/v1.0.16/unitree_lidar_ros2/src/unitree_lidar_ros2/README.md>
- SRC-006 — Official Unitree 4D LiDAR L1 manual:
  <https://oss-global-cdn.unitree.com/static/52b72f707b304d229d4321eea223738f.pdf>
  Relevant pages: p. 3 (11 Hz/250 Hz), p. 7 (12 V and 3.3 V TTL), p. 11
  (supplied adapter and cabling), p. 15 (12 V/1 A), and p. 16
  (TTL UART/2 Mbit/s).
- SRC-006A — Official L1 download centre:
  <https://www.unitree.com/download/LiDAR/>
- SRC-007 — Docker Compose service reference for `devices`, `group_add`, and
  security:
  <https://docs.docker.com/reference/compose-file/services/>
- SRC-008 — ROS 2 Humble QoS concepts:
  <https://docs.ros.org/en/humble/Concepts/Intermediate/About-Quality-of-Service-Settings.html>
- SRC-009 — ROS 2 `diagnostic_msgs/DiagnosticArray` message:
  <https://docs.ros.org/en/humble/p/diagnostic_msgs/msg/DiagnosticArray.html>
- SRC-010 — Official Unitree Point-LIO, currently ROS 1/Noetic:
  <https://github.com/unitreerobotics/point_lio_unilidar>
- SRC-011 — Community Point-LIO ROS 2 port to evaluate with the validated bag:
  <https://github.com/dfloreaa/point_lio_ros2>
- SRC-012 — Official OctoMap mapping ROS 2 release `2.3.1`:
  <https://github.com/OctoMap/octomap_mapping/tree/2.3.1>
- SRC-013 — Official `colcon` configuration, including workspace-local
  `colcon_defaults.yaml`:
  <https://colcon.readthedocs.io/en/released/user/configuration.html>
- SRC-014 — Official `colcon` discovery arguments, including `--base-paths`:
  <https://colcon.readthedocs.io/en/released/reference/discovery-arguments.html>
- SRC-015 — Pinned OctoMap mapping README, including `octomap_server` and the
  `octomap_saver_node` command:
  <https://github.com/OctoMap/octomap_mapping/blob/2.3.1/README.md>

The official manual documents the supplied adapter and separate power supply,
the 12 V / 1 A requirement, the TTL UART interface at 2,000,000 bit/s,
approximately 11 Hz azimuth scanning, and 250 Hz IMU reports. These values are
the initial reference. Validated measurements are approximately 8–10 Hz for the
cloud and 210–250 Hz for the IMU.
