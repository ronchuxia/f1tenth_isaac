"""Publish an occupancy map using the system ROS 2 installation."""
import os
from contextlib import contextmanager
from pathlib import Path
import signal
import subprocess
import sys


@contextmanager
def publish_map(map_path):
    """Publish a map while the surrounding context is active."""
    map_server_process = subprocess.Popen(
        [
            'bash',
            '-c',
            'unset PYTHONHOME PYTHONPATH LD_LIBRARY_PATH; '
            'source /opt/ros/humble/setup.bash; '
            'exec /usr/bin/python3 "$@"',
            'f1tenth-map',
            str(Path(__file__).resolve()),
            str(map_path),
        ],
        start_new_session=True)
    try:
        yield
    finally:
        os.killpg(map_server_process.pid, signal.SIGINT)
        map_server_process.wait()


def main(map_path):
    """Launch and activate the ROS 2 map server."""
    from launch import LaunchDescription, LaunchService
    from launch_ros.actions import Node

    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        parameters=[{
            'yaml_filename': str(map_path),
            'topic_name': 'map',
            'frame_id': 'map',
            'use_sim_time': True,
        }],
        output='screen',
    )

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='map_lifecycle_manager',
        parameters=[{
            'autostart': True,
            'node_names': ['map_server'],
        }],
        output='screen',
    )

    launch_service = LaunchService(argv=[])
    launch_service.include_launch_description(
        LaunchDescription([map_server, lifecycle_manager])
    )
    
    return launch_service.run()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
