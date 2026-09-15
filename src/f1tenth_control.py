"""F1TENTH articulation."""
from isaacsim.core.experimental.prims import Articulation
from isaacsim.robot.experimental.wheeled_robots.controllers.ackermann_controller import AckermannController
from isaacsim.core.simulation_manager import SimulationEvent, SimulationManager
from f1tenth_steering import F1TenthSteering


class F1TenthControl:
    def __init__(self, prim_path):
        self.robot = Articulation(prim_path)

        self.headings = (0, 0)
        self.geometry = F1TenthSteering(prim_path, self.robot)
        self.steering_subscription = SimulationManager.register_callback(
            self._update_steering, 
            event=SimulationEvent.PHYSICS_PRE_STEP
        )

        self.steering = self.geometry.joint_indices
        self.wheels = self.robot.get_dof_indices([
            'Wheel__Knuckle__Front_Left',
            'Wheel__Knuckle__Front_Right',
            'Wheel__Upright__Rear_Left',
            'Wheel__Upright__Rear_Right'
        ])
        
        self.controller = AckermannController(
            wheel_base=0.32, 
            track_width=0.24,
            front_wheel_radius=0.052, 
            back_wheel_radius=0.052,
            max_wheel_rotation_angle=0.523599
        )

    def set_command(self, speed, steering_angle):
        """Set rear-axle speed (m/s) and virtual front-wheel angle (rad)."""
        headings, velocities = self.controller.forward([steering_angle, 0, speed, 0, 0])
        self.headings = headings

        # set steering
        self._update_steering(0)

        # set velocity
        self.robot.set_dof_velocity_targets([velocities], dof_indices=self.wheels)

    def _update_steering(self, dt, context=None):
        targets = self.geometry.joint_targets(self.headings)
        self.robot.set_dof_position_targets([targets], dof_indices=self.steering)

    def stop(self):
        self.set_command(0, 0)
