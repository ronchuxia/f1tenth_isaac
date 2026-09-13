# ──────────────────────────────────────────────────────────────────────────────
# Base: NVIDIA CUDA 12.8 + cuDNN on Ubuntu 22.04
# ──────────────────────────────────────────────────────────────────────────────
FROM nvcr.io/nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04

LABEL maintainer="f1tenth-isaac"
LABEL description="F1Tenth Isaac Sim/Lab + ROS2 Humble development container"

# ─── Environment ──────────────────────────────────────────────────────────────
ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

ENV NVIDIA_DRIVER_CAPABILITIES=all

ENV ISAACSIM_PATH=/opt/isaac-sim \
    ISAACLAB_PATH=/opt/IsaacLab \
    ROS_DISTRO=humble

# ─── Base system packages ──────────────────────────────────────────────────────
# curl/gnupg2: ROS2 apt key.  wget/unzip: Isaac Sim download.  git: Isaac Lab clone.
# build-essential: compile any pip C-extensions during isaaclab.sh --install.
# glib/sm/fontconfig: runtime libs needed by Isaac Sim's GUI stack.
RUN apt-get update && apt-get install -y --no-install-recommends \
        locales curl wget git unzip \
        gnupg2 ca-certificates build-essential \
        libglib2.0-0 libsm6 libfontconfig1 \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# ─── X11 / OpenGL / EGL / Vulkan display libraries ────────────────────────────
# Required for Isaac Sim rendering through X11 forwarding to the host display.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1-mesa-dri libgl1-mesa-glx libglu1-mesa \
        libegl1 libegl-mesa0 \
        libvulkan1 mesa-vulkan-drivers \
        libxext6 libxrender1 libxrandr2 libxinerama1 \
        libxcursor1 libxi6 libxfixes3 libxcomposite1 libxdamage1 \
        libxkbcommon-x11-0 \
        xauth \
    && rm -rf /var/lib/apt/lists/*

# ─── ROS2 Humble ──────────────────────────────────────────────────────────────
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        | gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
        | tee /etc/apt/sources.list.d/ros2.list > /dev/null && \
    apt-get update && apt-get install -y --no-install-recommends \
        ros-humble-desktop \
        python3-colcon-common-extensions \
        python3-rosdep \
    && rosdep init \
    && rosdep update \
    && rm -rf /var/lib/apt/lists/*

# ─── Isaac Sim 6.1.0 (standalone) ─────────────────────────────────────────────
RUN wget -q -O /tmp/isaac-sim.zip \
        https://downloads.isaacsim.nvidia.com/isaac-sim-standalone-6.1.0-linux-x86_64.zip && \
    mkdir -p ${ISAACSIM_PATH} && \
    unzip -q /tmp/isaac-sim.zip -d ${ISAACSIM_PATH} && \
    rm /tmp/isaac-sim.zip && \
    cd ${ISAACSIM_PATH} && ./post_install.sh

# ─── Isaac Lab 3.0.0 (release/3.0.0 at tested commit) ───────────────────────
ARG ISAACLAB_COMMIT=3cd1279e63effc1b82b51f70ec3250cec10d21f5
RUN git init ${ISAACLAB_PATH} && \
    cd ${ISAACLAB_PATH} && \
    git remote add origin https://github.com/isaac-sim/IsaacLab.git && \
    git fetch --depth 1 origin ${ISAACLAB_COMMIT} && \
    git checkout --detach FETCH_HEAD

WORKDIR ${ISAACLAB_PATH}

# isaaclab.sh finds Isaac Sim through a `_isaac_sim` symlink in the repo root.
RUN ln -s ${ISAACSIM_PATH} ${ISAACLAB_PATH}/_isaac_sim && \
    ./isaaclab.sh --install

# ─── Omniverse Kit root guard ─────────────────────────────────────────────────
# Required for running Omniverse Kit as root in the container.
ENV OMNI_KIT_ALLOW_ROOT=1

# ─── Shell environment ─────────────────────────────────────────────────────────
RUN echo "source /opt/ros/humble/setup.bash" >> /etc/bash.bashrc && \
    echo "export ISAACSIM_PATH=${ISAACSIM_PATH}" >> /etc/bash.bashrc && \
    echo "export ISAACLAB_PATH=${ISAACLAB_PATH}" >> /etc/bash.bashrc && \
    echo "alias python-isaac='${ISAACSIM_PATH}/python.sh'" >> /etc/bash.bashrc

# ─── Default command ──────────────────────────────────────────────────────────
WORKDIR /workspace
CMD ["/bin/bash"]
