ARG ROS_BASE=ros:humble-perception-jammy@sha256:d89271d71fb7cefd5c39481b012172e4e8378835b8e6f23b19769b55a06dac35
FROM ${ROS_BASE}

ARG DEBIAN_FRONTEND=noninteractive
ARG HOST_UID=1000
ARG HOST_GID=1000
ARG UNITREE_SDK_COMMIT=1bd7d95d8ab7ce7a22058d2bb07e39fd62612aa6

ENV ROS_DISTRO=humble \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    QT_X11_NO_MITSHM=1 \
    LIBGL_ALWAYS_SOFTWARE=1 \
    PYTHONDONTWRITEBYTECODE=1

LABEL org.opencontainers.image.title="Unitree L1 ROS 2" \
      org.opencontainers.image.description="ROS 2 Humble, Unitree L1, OctoMap, RViz2, MCAP replay and headless evidence capture" \
      io.unitree-l1.sdk.commit="${UNITREE_SDK_COMMIT}"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Keep the entire RViz capture stack inside the reproducible project image.
# GitHub runners therefore only need Docker and Git LFS; their host X11/apt
# state no longer affects the visual-evidence workflow.
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg \
      libgl1-mesa-dri \
      python3-numpy \
      ros-humble-octomap-server \
      ros-humble-rosbag2-storage-mcap \
      ros-humble-rviz2 \
      xdotool \
      xvfb \
    && rm -rf /var/lib/apt/lists/*

# Pin the vendor source instead of silently building whatever is newest.
RUN mkdir -p /opt/unitree_ws/src \
    && git clone --filter=blob:none --no-checkout \
      https://github.com/unitreerobotics/unilidar_sdk.git \
      /opt/unitree_ws/src/unilidar_sdk \
    && git -C /opt/unitree_ws/src/unilidar_sdk checkout --detach \
      "${UNITREE_SDK_COMMIT}" \
    && test "$(git -C /opt/unitree_ws/src/unilidar_sdk rev-parse HEAD)" \
      = "${UNITREE_SDK_COMMIT}" \
    && rm -rf /opt/unitree_ws/src/unilidar_sdk/.git

COPY ros2_ws/src/l1_bringup /opt/unitree_ws/src/l1_bringup
COPY ros2_ws/src/l1_octomap_bringup /opt/unitree_ws/src/l1_octomap_bringup

RUN source /opt/ros/humble/setup.bash \
    && colcon --log-base /tmp/unitree_colcon_log build \
      --base-paths \
        /opt/unitree_ws/src/unilidar_sdk/unitree_lidar_ros2 \
        /opt/unitree_ws/src/l1_bringup \
        /opt/unitree_ws/src/l1_octomap_bringup \
      --build-base /tmp/unitree_colcon_build \
      --install-base /opt/unitree_ws/install \
      --merge-install \
      --packages-select unitree_lidar_ros2 l1_bringup l1_octomap_bringup \
      --event-handlers console_direct+ \
    && source /opt/unitree_ws/install/setup.bash \
    && ros2 pkg prefix unitree_lidar_ros2 \
    && ros2 pkg prefix l1_bringup \
    && ros2 pkg prefix l1_octomap_bringup \
    && ros2 pkg prefix rosbag2_storage_mcap \
    && python3 -c 'import numpy' \
    && command -v Xvfb \
    && command -v ffmpeg \
    && command -v xdotool \
    && ros2 pkg executables octomap_server | grep -F \
      "octomap_server octomap_server_node" \
    && ros2 launch l1_bringup unitree_l1.launch.py --show-args \
    && ros2 launch l1_octomap_bringup unitree_l1_octomap.launch.py --show-args \
    && rm -rf /tmp/unitree_colcon_build /tmp/unitree_colcon_log

RUN groupadd --gid "${HOST_GID}" ros \
    && useradd --uid "${HOST_UID}" --gid "${HOST_GID}" \
      --create-home --shell /bin/bash ros \
    && mkdir -p /workspace \
    && chown "${HOST_UID}:${HOST_GID}" /workspace

COPY docker/ros2-profile.sh /etc/profile.d/unitree-ros2.sh

USER ros
WORKDIR /workspace
CMD ["bash"]
