ARG ROS_BASE=ros:humble-ros-base-jammy@sha256:5c793b92e0b12d6babb438cb20eed7766495fde6419a21e3d2e918464f09dc17
FROM ${ROS_BASE}

ARG DEBIAN_FRONTEND=noninteractive
ARG HOST_UID=1000
ARG HOST_GID=1000
ARG PROJECT_USER=ros

ENV ROS_DISTRO=humble \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    QT_X11_NO_MITSHM=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
      bash-completion \
      build-essential \
      ca-certificates \
      cmake \
      git \
      iproute2 \
      iputils-ping \
      libboost-system-dev \
      libgl1-mesa-dri \
      liblz4-dev \
      liboctomap-dev \
      libpcl-dev \
      mesa-utils \
      ninja-build \
      pkg-config \
      python3-colcon-common-extensions \
      python3-pip \
      python3-rosdep \
      python3-vcstool \
      ros-humble-launch-ros \
      ros-humble-octomap-msgs \
      ros-humble-octomap-ros \
      ros-humble-pcl-conversions \
      ros-humble-pcl-ros \
      ros-humble-ros2bag \
      ros-humble-ros2doctor \
      ros-humble-rviz2 \
      ros-humble-tf2-ros \
      usbutils \
      x11-utils \
      xauth \
    && rm -rf /var/lib/apt/lists/*

RUN if [[ ! -e /etc/ros/rosdep/sources.list.d/20-default.list ]]; then rosdep init; fi

RUN groupadd --gid "${HOST_GID}" "${PROJECT_USER}" \
    && useradd --uid "${HOST_UID}" --gid "${HOST_GID}" --create-home \
      --shell /bin/bash "${PROJECT_USER}" \
    && mkdir -p /workspace/ros2_ws \
    && chown -R "${HOST_UID}:${HOST_GID}" /workspace

COPY --chmod=0755 docker/entrypoint.sh /usr/local/bin/unitree-entrypoint

USER ${PROJECT_USER}
WORKDIR /workspace/ros2_ws
RUN rosdep update --rosdistro humble

ENTRYPOINT ["/usr/local/bin/unitree-entrypoint"]
CMD ["bash"]
