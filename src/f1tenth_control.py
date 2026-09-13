"""F1TENTH articulation."""
from isaacsim.core.experimental.prims import Articulation
from isaacsim.robot.experimental.wheeled_robots.controllers.ackermann_controller import AckermannController


class F1TenthControl:
    def __init__(self, prim_path):
        self.robot = Articulation(prim_path)

        self.steering = self.robot.get_dof_indices([
            'Knuckle__Upright__Front_Left', 'Knuckle__Upright__Front_Right'])
        
        self.wheels = self.robot.get_dof_indices([
            'Wheel__Knuckle__Front_Left', 'Wheel__Knuckle__Front_Right',
            'Wheel__Upright__Rear_Left', 'Wheel__Upright__Rear_Right'])
        
        self.controller = AckermannController(
            wheel_base=0.32, 
            track_width=0.24,
            front_wheel_radius=0.052, 
            back_wheel_radius=0.052,
            max_wheel_rotation_angle=0.523599
        )

    def set_command(self, speed, steering_angle):
        """Set rear-axle speed (m/s) and virtual front-wheel angle (rad)."""
        angles, velocities = self.controller.forward([steering_angle, 0, speed, 0, 0])
        self.robot.set_dof_position_targets([angles], dof_indices=self.steering)
        self.robot.set_dof_velocity_targets([velocities], dof_indices=self.wheels)
        return angles, velocities

    def stop(self):
        self.set_command(0, 0)
