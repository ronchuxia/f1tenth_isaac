from pathlib import Path

from pxr import Gf, UsdGeom


def load_scene(stage, scene, spawn_pose, world_to_map):
    project = Path(__file__).resolve().parents[1]

    environment = stage.DefinePrim('/World/Environment', 'Xform')
    environment.GetReferences().AddReference(str(scene))

    spawn = UsdGeom.Xform.Define(stage, '/World/Spawn')
    spawn.AddTranslateOp().Set(Gf.Vec3d(*spawn_pose[:3]))
    spawn.AddRotateZOp().Set(spawn_pose[3])

    car = UsdGeom.Xform.Define(stage, '/World/Spawn/Car')
    car.GetPrim().GetReferences().AddReference(str(project / 'assets/robots/f1tenth/f1tenth_ros.usda'))

    # move base_link to spawn
    base = stage.GetPrimAtPath(str(car.GetPath()) + '/Rigid_Bodies/Chassis/base_link')

    transforms = UsdGeom.XformCache()
    base_to_world = transforms.GetLocalToWorldTransform(base)
    spawn_to_world = transforms.GetLocalToWorldTransform(spawn.GetPrim())
    world_to_spawn = spawn_to_world.GetInverse()
    base_to_spawn = base_to_world * world_to_spawn
    base_in_spawn = base_to_spawn.ExtractTranslation()

    car_translation = car.GetPrim().GetAttribute('xformOp:translate')
    car_translation.Set(car_translation.Get() - base_in_spawn)

    # overwrite world to map transform publisher node
    x, y, yaw = world_to_map
    transform = Gf.Matrix4d(Gf.Rotation(Gf.Vec3d.ZAxis(), yaw), Gf.Vec3d(x, y, 0))
    stage.GetAttributeAtPath(str(car.GetPath()) + '/ROS/State/WorldToMap.inputs:value').Set(transform)

    return car.GetPrim()
