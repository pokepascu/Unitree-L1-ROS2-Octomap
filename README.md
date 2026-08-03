# Unitree L1: minimal ROS 2 Docker project

This project does three things:

1. reads a Unitree 4D LiDAR L1 with the vendor ROS 2 driver;
2. displays the cloud and builds a live OctoMap while the L1 is stationary;
3. records the cloud and IMU topics with standard `ros2 bag` commands.

There are no runtime wrapper scripts, custom processing nodes, or SLAM
packages. The two small project packages contain only launch, parameter, and
RViz files. The image installs the released ROS 2 Humble `octomap_server`
binary; it does not clone or modify OctoMap source.

## What runs

`docker compose up -d` creates one container whose only project command is
`sleep infinity`. Docker's small init process supervises that idle child so
`docker compose down` stops cleanly. Neither process reads the LiDAR; they only
keep the named container available to two terminals.

The raw launch starts:

- `unitree_lidar_ros2_node` — reads the serial port and publishes cloud + IMU;
- `ros2 topic hz /unilidar/cloud` — only when `monitor:=true`;
- `rviz2` — only when `rviz:=true`.

The combined OctoMap launch starts the same driver and monitor, plus:

- `octomap_server_node` — consumes `/unilidar/cloud`;
- one map-oriented `rviz2` — displays the cloud and occupied voxels.

The OctoMap fixed frame is `unilidar_lidar`, the cloud's own frame. This avoids
inventing a pose or running a TF publisher. Keep the L1 body stationary:
OctoMap is occupancy mapping, not localization or SLAM.

Recording is a separate command that you start in Terminal B. The launch file
does not record automatically.

## Host requirements

- Docker Engine and Docker Compose;
- an X11 graphical desktop (`DISPLAY` and `XAUTHORITY` must be set);
- `/dev/dri` for accelerated RViz2 rendering;
- the Unitree adapter and the L1's separate specified power supply;
- a host serial device, normally `/dev/ttyUSB0`.

The project defaults match this computer: user/group `1000:1000`, serial group
20, video group 44, and render group 992. The manuals show how to inspect and
override those values when they differ.

## One-time image build

From the repository root:

```bash
cd /home/isr/unitree_l1_project
docker compose build
```

The Dockerfile checks out Unitree UniLiDAR SDK v1.0.16 at commit
`1bd7d95d8ab7ce7a22058d2bb07e39fd62612aa6`, copies `l1_bringup`, and builds
exactly these three ROS 2 packages into the image:

```text
unitree_lidar_ros2
l1_bringup
l1_octomap_bringup
```

Rebuild the image only after changing the Dockerfile or either bringup package.

## Start the container

Connect and separately power the L1, then confirm the serial path:

```bash
ls -l /dev/ttyUSB*
```

For the normal `/dev/ttyUSB0` case:

```bash
docker compose up -d
docker compose ps
```

If the path or group differs, export the actual values before `up`:

```bash
export LIDAR_DEVICE=/dev/ttyUSB1
export LIDAR_GID="$(stat -Lc '%g' "$LIDAR_DEVICE")"
docker compose up -d
```

Compose always exposes the chosen host device inside the container as
`/dev/unitree_lidar`.

## Terminal A: launch the LiDAR, OctoMap, and RViz2

```bash
docker compose exec ros bash -l
ros2 launch l1_octomap_bringup unitree_l1_octomap.launch.py \
  port:=/dev/unitree_lidar \
  monitor:=true \
  rviz:=true
```

Leave the launch running. Expected interfaces are:

| Topic | Type | Frame |
|---|---|---|
| `/unilidar/cloud` | `sensor_msgs/msg/PointCloud2` | `unilidar_lidar` |
| `/unilidar/imu` | `sensor_msgs/msg/Imu` | `unilidar_imu` |
| `/occupied_cells_vis_array` | `visualization_msgs/msg/MarkerArray` | `unilidar_lidar` |
| `/octomap_binary` | `octomap_msgs/msg/Octomap` | `unilidar_lidar` |

RViz2 uses `unilidar_lidar` as its fixed frame and displays the point cloud
plus `/occupied_cells_vis_array`. This launch publishes no TF because the
cloud and map use the same stationary sensor frame.

For the raw cloud without OctoMap, use this alternative instead:

```bash
ros2 launch l1_bringup unitree_l1.launch.py \
  port:=/dev/unitree_lidar monitor:=true rviz:=true
```

Do not run both launches together; each one starts the LiDAR driver.

## Terminal B: inspect and record

Open a second host terminal:

```bash
cd /home/isr/unitree_l1_project
docker compose exec ros bash -l
ros2 topic list --no-daemon
ros2 topic echo /unilidar/cloud --field width --once
ros2 bag record \
  -o /workspace/bags/l1_run_01 \
  /unilidar/cloud \
  /unilidar/imu
```

Use a new bag name for each run. Stop recording with `Ctrl+C`; this cleanly
writes `metadata.yaml`. Then inspect it:

```bash
ros2 bag info /workspace/bags/l1_run_01
```

The bag appears on the host at `bags/l1_run_01/`.

## Stop

1. In Terminal B, stop `ros2 bag record` with `Ctrl+C`, then `exit`.
2. In Terminal A, stop `ros2 launch` with `Ctrl+C`, then `exit`.
3. On the host, remove the idle container:

```bash
docker compose down
```

## Manuals

- [Engineering manual](exports/manuals/UNITREE_L1_ENGINEERING_MANUAL.pdf)
- [User manual](exports/manuals/UNITREE_L1_USER_MANUAL.pdf)
- [Structure and organisation](exports/manuals/UNITREE_L1_STRUCTURE_AND_ORGANISATION.pdf)
- [Editable manual sources](docs/manuals/README.md)

Live sensor validation is still pending for this revision because no LiDAR
serial device is connected at the time of the software rebuild. The Docker
build, ROS package graph, GUI path, and rosbag command can be verified without
claiming live hardware data.
