# Unitree 4D LiDAR L1 — ROS 2 Humble and OctoMap

Reproducible Docker environment for building, running, visualising, recording,
and mapping Unitree L1 data with ROS 2 Humble. The Ubuntu 24.04 host remains free
of ROS packages; the complete ROS stack runs in an Ubuntu 22.04 container.

## Current status

- Unitree UniLiDAR SDK `v1.0.16` is pinned to commit
  `1bd7d95d8ab7ce7a22058d2bb07e39fd62612aa6`.
- OctoMap mapping `2.3.1` is pinned to commit
  `f79da9a9a1fcdf82e72dab4df288d6cc27c6e163`.
- The L1 cloud, IMU, RViz2, rosbag2, and stationary-sensor OctoMap pipeline have
  been validated with real hardware.
- Mobile mapping still requires a dynamic pose source such as odometry or SLAM.
  OctoMap creates the occupancy map; it does not estimate the robot pose.

## Project structure

```text
.
├── config/
│   └── dependencies.repos       # pinned third-party repositories
├── docker/
│   ├── Dockerfile               # Ubuntu 22.04 + ROS 2 Humble image
│   ├── compose.yaml             # base development service
│   ├── compose.gui.yaml         # opt-in X11 and DRI access
│   ├── compose.lidar.yaml       # opt-in serial-device access
│   └── entrypoint.sh
├── docs/                        # concise design, hardware, and validation docs
├── ros2_ws/
│   ├── colcon_defaults.yaml     # the six permitted ROS 2 packages
│   └── src/
│       ├── l1_bringup/          # configurable driver launch and RViz profile
│       ├── l1_monitor/          # cloud and IMU diagnostics
│       └── l1_octomap_bringup/  # OctoMap launch, configuration, and RViz
├── scripts/                     # executable setup and runtime commands
├── .dockerignore
├── .gitignore
├── LICENSE
└── README.md
```

The following paths are generated locally and are deliberately not versioned:

- `ros2_ws/src/unilidar_sdk/` and `ros2_ws/src/octomap_mapping/` are recreated
  from `config/dependencies.repos`;
- `ros2_ws/build/`, `ros2_ws/install/`, and `ros2_ws/log/` are colcon outputs;
- `bags/`, `maps/`, `logs/`, and non-manual `exports/` contain runtime data.
  The three reviewed PDFs in `exports/manuals/` are tracked publications.

There must never be a `build`, `install`, or `log` directory inside
`ros2_ws/src`. Always invoke colcon from `ros2_ws`, or use
`./scripts/workspace-build.sh`. The build wrapper and repository hygiene checks
scan recursively for accidental generated output under `src`.

## Requirements

- Docker Engine with Docker Compose;
- an X11 session and `/dev/dri` for RViz2;
- the Unitree adapter and a separately powered L1 for live operation.

Do not install ROS 2 Humble on the Ubuntu 24.04 host. Do not use
`privileged: true`, `chmod 777`, or a global `xhost +`.

## Build

From the repository root:

```bash
./scripts/docker-build.sh
./scripts/workspace-build.sh
./scripts/smoke-test.sh
```

`workspace-build.sh` fetches and verifies the pinned dependencies before
building. To fetch them without compiling:

```bash
./scripts/fetch-dependencies.sh
```

To work interactively inside the Humble container:

```bash
./scripts/docker-shell.sh --no-gui --no-lidar
```

The explicit flags keep build-only work independent of X11, DRI, and hardware.
Use `./scripts/docker-shell.sh --help` for opt-in GUI and LiDAR access.

The Compose environment sets `COLCON_DEFAULTS_FILE` to the workspace
configuration. From `/workspace/ros2_ws`, plain colcon commands therefore
discover only the intended ROS 2 packages:

```bash
colcon list
colcon build
source install/setup.bash
```

## Docker-only runtime

ROS 2, the Unitree driver, OctoMap, and RViz2 run inside Docker. Only the X11
socket, DRI devices, and the selected serial device cross the container
boundary. Every runtime wrapper calls `scripts/assert-ros-container.sh`; the
project launch files enforce the same boundary.

After starting a graphical workflow, verify the process location with:

```bash
./scripts/verify-docker-only.sh
```

The expected verdicts include `HOST_NATIVE_RVIZ_ABSENT` and
`DOCKER_ONLY_PIPELINE_PASS`.

## Live LiDAR

Read [the hardware runbook](docs/hardware-runbook.md) before powering or wiring
the sensor. The normal validation sequence is:

```bash
./scripts/check-lidar.sh
START_RVIZ=false ./scripts/lidar-launch.sh
```

In a second terminal:

```bash
./scripts/lidar-validate.sh
```

After message and frequency validation, restart with RViz2:

```bash
START_RVIZ=true ./scripts/lidar-launch.sh
```

Record a bounded sample:

```bash
BAG_LABEL=validation BAG_DURATION_SEC=30 ./scripts/record-bag.sh
```

The `bags/` and `logs/` directories are created on demand and remain ignored by
Git.

## OctoMap

For a perfectly stationary sensor, start the live stack and then:

```bash
OCTOMAP_RVIZ=true ./scripts/octomap-launch.sh
./scripts/evaluate-octomap.sh
./scripts/save-octomap.sh my_room_01.bt
```

Inspect or reopen a saved map:

```bash
./scripts/inspect-octomap.sh my_room_01.bt
./scripts/view-octomap.sh my_room_01.bt
```

Do not use the stationary transform while the sensor or robot is moving. With
the host wrapper, set `STATIC_SENSOR=false`; with a direct ROS launch, pass
`static_sensor:=false`. Both modes require a dynamic transform from the chosen
pose estimator.

## Documentation

- [Project structure](docs/project-structure.md): ownership, generated paths,
  and out-of-source build rules.
- [Hardware runbook](docs/hardware-runbook.md): wiring, validation, recording,
  and replay.
- [Architecture decisions](docs/decisions.md): design choices and rationale.
- [Validation matrix](docs/validation-matrix.md): reproducible checks and
  hardware-dependent verdicts.
- [Version lock](docs/versions-lock.md): pinned images, packages, and commits.
- [Technical sources](docs/sources.md): authoritative upstream references.
- [Engineering manual (PDF)](exports/manuals/UNITREE_L1_ENGINEERING_MANUAL.pdf)
- [First-run tutorial (PDF)](exports/manuals/UNITREE_L1_FIRST_RUN_TUTORIAL.pdf)
- [File organization reference (PDF)](exports/manuals/UNITREE_L1_FILE_ORGANIZATION_REFERENCE.pdf)
- [Manual sources and rendering](docs/manuals/README.md)

Generated reports, raw logs, bags, maps, build trees, and copied upstream
manuals are intentionally excluded from the repository. The three
project-authored PDFs linked above are the publication exception.
