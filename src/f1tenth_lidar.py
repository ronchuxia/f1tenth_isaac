"""Python readout for the project vehicle's planar RTX LiDAR."""
import numpy as np
from isaacsim.core.experimental.utils import app as app_utils
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor, parse_generic_model_output_data


class F1TenthLidar:
    def __init__(self, car_path, visualize=False):
        if visualize:
            app_utils.enable_extension('isaacsim.sensors.rtx.nodes')

        lidar = Lidar(car_path + '/Rigid_Bodies/Chassis/base_link/lidar',
                      reset_xform_op_properties=False)
        self.sensor = LidarSensor(lidar, annotators=['generic-model-output'])

        if visualize:
            self.sensor.attach_writer('draw-point-cloud', color=[0, 1, 0, 1], size=0.01)

    def read(self):
        """Return increasing angles and actual beam time offsets, or None before a scan."""
        data, _ = self.sensor.get_data('generic-model-output')
        if data is None:
            return None
        
        output = parse_generic_model_output_data(data)
        if not output.numElements:
            return None

        # Isaac Sim 6.1 returns CCW profile in increasing angle order.
        ranges = output.z

        # invalid ranges
        ranges[ranges == 0] = np.inf
        
        return dict(timestamp_ns=int(output.timestampNs),
                    angles=np.deg2rad(output.x),
                    ranges=ranges,
                    time_offsets_ns=output.timeOffsetNs)
