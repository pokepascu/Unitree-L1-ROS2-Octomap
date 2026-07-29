# Decision log

## DEC-001 — Isolate ROS 2 Humble in Docker

- Status: accepted.
- Constraint: the host runs Ubuntu 24.04 Noble, while the Humble binaries target
  Ubuntu 22.04 Jammy.
- Options considered: Jammy repositories on the host, a native Noble build, and
  a Jammy/Humble container.
- Decision: leave the Noble host unchanged and use Docker with Jammy/Humble.
- Rationale: compatibility, isolation, and a documented reconstruction path.
- Revisit only if Humble must later run without Docker.

## DEC-002 — Keep the vendor SDK unchanged

- Status: accepted.
- Decision: pin `unilidar_sdk` to a commit and place adaptations in a separate
  `l1_bringup` package.
- Rationale: clearly distinguish Unitree code from project code.

## DEC-003 — Separate the hardware Compose overlay

- Status: accepted.
- Decision: keep the base Compose service independent of the LiDAR; an overlay
  adds one serial device and its GID.
- Rationale: an absent `/dev/ttyUSB0` would otherwise prevent every test from
  starting and encourage unjustified use of privileged mode.

## DEC-004 — Do not use host networking by default

- Status: accepted.
- Decision: use Docker bridge networking while all ROS nodes run in the same
  container and the L1 uses its serial interface.
- Rationale: reduce exposure. Reconsider `network_mode: host` only for
  inter-host DDS or an explicitly identified serial-to-UDP adapter.

## DEC-005 — Mount X11 authorisation read-only

- Status: accepted.
- Decision: mount `${XAUTHORITY}` and `/tmp/.X11-unix` without `xhost +`.
- Rationale: run RViz2 without opening the X server globally.

## DEC-006 — Add an `l1_bringup` package

- Status: accepted.
- Decision: wrap the Unitree node in a configurable project launch file.
- Rationale: the vendor launch file hard-codes the port and topics. A separate
  layer keeps the vendor tree clean and supports `/dev/unitree_lidar`.

## DEC-007 — Validate Humble with PCL 1.12

- Status: accepted and validated with the physical L1.
- Context: Unitree documents Ubuntu 20.04, Foxy, and PCL 1.10 for this version.
- Evidence: successful compilation and linking without a patch, no missing
  libraries, compatibility between the GCC 9.4 vendor archive and the available
  GCC 11.4/GLIBCXX runtime, followed by reception of real cloud and IMU data.

## DEC-008 — Add a non-intrusive monitor

- Status: accepted.
- Decision: `l1_monitor` subscribes without republishing or filtering raw data
  and publishes two statuses on `/diagnostics`.
- QoS: Reliable, Volatile, KeepLast(10), matching the driver contract.
- Provisional thresholds: 2 s report period, 3 s timeout, 1 s header age, 5 Hz
  cloud rate, 20 Hz IMU rate, and a 100-message window.
- Rationale: these values are conservative alarm thresholds, not Unitree
  specifications. Re-evaluate them if the transport, driver, or sensor rate
  changes.

## DEC-009 — Isolate the project's ROS domain

- Status: accepted.
- Decision: default to `ROS_DOMAIN_ID=42` to avoid mixing the project graph with
  other local ROS experiments. The isolated audit used domain 187.
- Limitation: every process that must communicate needs to share the domain.

## DEC-010 — Skip only two rosdep keys

- Status: accepted.
- Decision: after verifying their installation, `workspace-build.sh` skips
  `ament_python` and `pcl`, for which these manifests provide no usable rosdep
  resolution.
- Rationale: keep the vendor manifest unchanged and let `rosdep` check every
  other dependency.

## DEC-011 — Separate GUI and hardware access

- Status: accepted.
- Decision: keep `compose.yaml` usable without a display or sensor;
  `compose.gui.yaml` adds X11/DRI, and `compose.lidar.yaml` adds one tty and GID.
- Rationale: headless operation, least privilege, and explicit failures.

## DEC-012 — Evaluate Point-LIO with real data

- Status: hardware prerequisite satisfied; Point-LIO integration pending.
- Decision: select and tune a Point-LIO port using the validated bag and its L1
  PointCloud2 fields, timestamps, rates, units, and extrinsics.
- Rationale: these properties determine the appropriate branch and parameters.
  The choice must be based on data rather than assumed compatibility.

## DEC-013 — Keep the repository source-focused

- Status: accepted and revised after the structure audit.
- Decision: version the code, reproducible configuration, and concise technical
  documentation. Exclude build and install trees, caches, raw logs, bags, maps,
  exports, generated reports, and copies of upstream manuals.
- Rationale: these outputs are reproducible, machine-specific, or large. Keeping
  them in the repository obscures meaningful changes and can expose local
  hardware details.

## DEC-014 — Restrict `colcon` discovery to the ROS 2 workspace

- Status: accepted and validated.
- Problem: the Unitree repository also contains `unitree_lidar_ros` (ROS
  1/catkin) and a raw CMake SDK without an install target.
- Decision: use absolute container paths in `ros2_ws/colcon_defaults.yaml` for
  discovery and the `build`, `install`, and `log` outputs. Keep the same roots in
  `workspace-build.sh`.
- Rationale: plain `colcon build` discovers neither catkin nor the raw CMake SDK
  and cannot create output beneath `ros2_ws/src`.

## DEC-015 — Integrate OctoMap through a separate project layer

- Status: accepted and validated with real data.
- Decision: pin `octomap_mapping` 2.3.1 as an external dependency and keep the
  remapping, parameters, launch files, and RViz profile in
  `l1_octomap_bringup`.
- Rationale: Unitree and OctoMap remain unchanged, while the project explicitly
  controls `/unilidar/cloud -> cloud_in`, frames, and resolution.

## DEC-016 — Separate bench mapping from mobile mapping

- Status: accepted.
- Bench: `static_sensor:=true` publishes an identity
  `map -> unilidar_lidar` transform only while the sensor is stationary.
- Mobile: `static_sensor:=false` requires a dynamic transform from external
  odometry or SLAM.
- Rationale: OctoMap builds 3D occupancy but is not a pose estimator by itself.

## DEC-017 — Define the OctoMap/SLAM boundary

- Status: accepted and validated with stationary real-world data.
- Decision: treat `octomap_server` as the 3D mapping layer, not as a pose
  estimator or complete SLAM system.
- Rationale: the validated pipeline receives `PointCloud2` and requires a
  `map -> unilidar_lidar` transform. Dynamic pose must come from odometry or a
  future SLAM system such as Point-LIO or SLAM Toolbox.

## DEC-018 — Control map saving

- Status: accepted and validated.
- Decision: use `scripts/save-octomap.sh` to call the official saver, refuse to
  overwrite an existing file, and verify a non-empty `.bt` or `.ot` file under
  `maps/`.
- Rationale: a map is generated data and can be large. It remains outside Git,
  while the wrapper and its checks are versioned.
