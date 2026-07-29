# Version lock

## Reproducible inputs

| Component | Version or identifier | Lock location |
|---|---|---|
| Base image | `ros:humble-ros-base-jammy` | `docker/Dockerfile` |
| Base image digest | `sha256:5c793b92e0b12d6babb438cb20eed7766495fde6419a21e3d2e918464f09dc17` | `docker/Dockerfile` |
| Container OS | Ubuntu 22.04 Jammy, amd64 | base image |
| ROS 2 | Humble | base image and apt package names |
| Unitree UniLiDAR SDK | `v1.0.16` | `config/dependencies.repos` |
| Unitree commit | `1bd7d95d8ab7ce7a22058d2bb07e39fd62612aa6` | `config/dependencies.repos` |
| OctoMap mapping | `2.3.1` | `config/dependencies.repos` |
| OctoMap mapping commit | `f79da9a9a1fcdf82e72dab4df288d6cc27c6e163` | `config/dependencies.repos` |

`scripts/fetch-dependencies.sh` verifies the two dependency commits and rejects
dirty vendor checkouts before a build.

## Validated compatibility

The current container stack has been validated with:

- GCC/G++ 11.4 and the Unitree x86_64 vendor archive built with GCC 9.4;
- PCL 1.12, Eigen 3.4, and Boost 1.74;
- OctoMap C++ 1.9.7, `octomap_msgs` 2.0.1, and `octomap_ros` 0.4.4;
- Python 3.10, CMake 3.22, RViz2 11.2, colcon, rosdep, and vcstool from
  Ubuntu Jammy/ROS 2 Humble packages.

The base image and Git dependencies are immutable. Individual apt packages
installed by `docker/Dockerfile` are not pinned to repository snapshot versions,
so a future image rebuild is source-reproducible but not guaranteed to be
byte-for-byte identical.
