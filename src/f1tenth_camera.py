"""RGB readout for the vehicle's existing left and right cameras."""
from isaacsim.sensors.experimental.rtx import CameraSensor, RtxCamera


class F1TenthCamera:
    def __init__(self, car_path, side, resolution=(480, 640)):
        camera = RtxCamera(car_path + '/Rigid_Bodies/Chassis/Camera_' + side,
                           reset_xform_op_properties=False)
        self.sensor = CameraSensor(camera, resolution=resolution, annotators=['rgb'])

    def read(self):
        """Return an RGB NumPy image, or None before an image."""
        data, _ = self.sensor.get_data('rgb')
        if data is None:
            return None
        return data.numpy()
