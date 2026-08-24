# Docker Setup

## Prerequisites

- Docker Engine
- Docker Compose
- Nvidia Container Toolkit

## Host GPU Setup

**CDI** (Container Device Interface) passes the GPU to the container.

Run the following command to generate the CDI list if it doesn't exist:

```bash
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
```

## Build

```bash
docker compose -f docker/docker-compose.yml build
```

## GUI Setup

The container renders through X11 forwarding to a GPU-backed X server on the host.

Run the following command **on the host** (any terminal — it edits the X server's
global access control list, not the shell's) to allow the container to reach the
X server.

```bash
xhost +local:docker
```

## Run

```bash
# Start the container in the background
docker compose -f docker/docker-compose.yml up -d

# Open an interactive shell inside the container.
docker exec -it f1tenth-isaac bash

# Stop and remove the container when done
docker compose -f docker/docker-compose.yml down
```