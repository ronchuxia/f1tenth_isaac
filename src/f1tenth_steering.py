"""Convert planar wheel headings to the NVIDIA rig's inclined hinge angles."""
import numpy as np
import omni.usd
from pxr import Gf, UsdPhysics
from scipy.spatial.transform import Rotation
from isaacsim.core.experimental.prims import RigidPrim


class F1TenthSteering:
    def __init__(self, root, robot):
        self.robot = robot

        steering_joint_names = [
            'Knuckle__Upright__Front_Left',
            'Knuckle__Upright__Front_Right',
        ]
        self.joint_indices = robot.get_dof_indices(steering_joint_names)

        body_names = [
            'Wheel_Front_Left',
            'Wheel_Front_Right',
            'Upright_Front_Left',
            'Upright_Front_Right',
            'Chassis',
        ]
        self.bodies = RigidPrim(
            [root + '/Rigid_Bodies/' + name for name in body_names],
            reset_xform_op_properties=False,
        )

        stage = omni.usd.get_context().get_stage()

        self.wheel_axle_axes_local = []
        self.steering_hinge_axes_local = []
        for side in ('Left', 'Right'):
            wheel = UsdPhysics.Joint(stage.GetPrimAtPath(root + '/Joints/Wheel__Knuckle__Front_' + side))
            hinge = UsdPhysics.Joint(stage.GetPrimAtPath(root + '/Joints/Knuckle__Upright__Front_' + side))

            self.wheel_axle_axes_local.append(Gf.Rotation(wheel.GetLocalRot0Attr().Get()).TransformDir(Gf.Vec3d.ZAxis()))
            self.steering_hinge_axes_local.append(-Gf.Rotation(hinge.GetLocalRot1Attr().Get()).TransformDir(Gf.Vec3d.ZAxis()))

    def joint_targets(self, headings):
        quaternions = self.bodies.get_world_poses()[1].numpy()
        rotations = Rotation.from_quat(quaternions[:, [1, 2, 3, 0]])

        wheel_axle_axes_world = rotations[:2].apply(self.wheel_axle_axes_local)
        steering_hinge_axes_world = rotations[2:4].apply(self.steering_hinge_axes_local)

        # desired wheel travel directions in world space
        forward = rotations[4].apply([1, 0, 0])
        yaw = np.arctan2(forward[1], forward[0]) + np.asarray(headings)
        rolling = np.column_stack((np.cos(yaw), np.sin(yaw), np.zeros(2)))

        parallel = steering_hinge_axes_world * np.sum(
            steering_hinge_axes_world * wheel_axle_axes_world, axis=1
        )[:, None]
        a = np.sum((wheel_axle_axes_world - parallel) * rolling, axis=1)
        b = np.sum(np.cross(steering_hinge_axes_world, wheel_axle_axes_world) * rolling, axis=1)
        c = np.sum(parallel * rolling, axis=1)

        phase = np.arctan2(b, a)
        offset = np.arccos(-c / np.hypot(a, b))
        candidates = (np.column_stack((phase + offset, phase - offset)) + np.pi) % (2 * np.pi) - np.pi

        change = candidates[np.arange(2), np.argmin(abs(candidates), axis=1)]
        current = self.robot.get_dof_positions(dof_indices=self.joint_indices).numpy()[0]

        return current + change
