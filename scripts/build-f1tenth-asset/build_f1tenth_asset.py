"""Generate our NVIDIA-based vehicle override using Isaac Sim's Python."""
import os
import sys
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade

from f1tenth_lidar_asset import add_lidar

project = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project / 'scripts/utils'))
from asset_utils import set_contact_material

source = project / 'assets/robots/f1tenth/nvidia/F1Tenth.usd'
output = project / 'assets/robots/f1tenth/f1tenth.usda'

output.parent.mkdir(parents=True, exist_ok=True)

stage = Usd.Stage.CreateNew(str(output))
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

car = UsdGeom.Xform.Define(stage, '/F1Tenth').GetPrim()
car.GetReferences().AddReference(os.path.relpath(source, output.parent))
stage.SetDefaultPrim(car)

# Keep wheel physics material bindings inside the referenced car.
rubber = UsdShade.Material(stage.GetPrimAtPath('/F1Tenth/Rubber_Asphalt'))
set_contact_material(rubber.GetPrim(), 1.0, 0.8, 0.0)
for name in ('Wheel_Rear_Left', 'Wheel_Rear_Right', 'Wheel_Front_Left', 'Wheel_Front_Right'):
    wheel = stage.GetPrimAtPath('/F1Tenth/Rigid_Bodies/' + name)
    UsdShade.MaterialBindingAPI.Apply(wheel).Bind(rubber, materialPurpose='physics')

# Apply DriveAPI
for name in ('Wheel__Upright__Rear_Left', 'Wheel__Upright__Rear_Right',
             'Wheel__Knuckle__Front_Left', 'Wheel__Knuckle__Front_Right'):
    joint = stage.GetPrimAtPath(f'/F1Tenth/Joints/{name}')
    drive = UsdPhysics.DriveAPI.Apply(joint, 'angular')
    drive.GetTargetVelocityAttr().Set(0.0)

# Mirror the left shock's upper anchor.
right_shock = UsdPhysics.Joint(stage.GetPrimAtPath('/F1Tenth/Joints/Shock__Rear_Right'))
right_shock.GetLocalPos1Attr().Set(Gf.Vec3f(-15.200001, -5.7000003, 7))

# Add Xform base_link
chassis = stage.GetPrimAtPath('/F1Tenth/Rigid_Bodies/Chassis')
chassis_world = UsdGeom.XformCache().GetLocalToWorldTransform(chassis)

frame_world = Gf.Matrix4d(1).SetTranslate(Gf.Vec3d(-0.17, 0, 0.052))
frame = UsdGeom.Xform.Define(stage, chassis.GetPath().AppendChild('base_link'))
frame.AddTransformOp().Set(frame_world * chassis_world.GetInverse())

# Add OmniLidar
add_lidar(stage, chassis)

# Add OmniSensorAPI to Camera
for side in ('Left', 'Right'):
    camera = stage.GetPrimAtPath(chassis.GetPath().AppendChild('Camera_' + side))
    camera.AddAppliedSchema('OmniSensorAPI')
    camera.CreateAttribute('omni:sensor:tickRate', Sdf.ValueTypeNames.Float, custom=False).Set(30)

stage.GetRootLayer().Save()
print(output)
