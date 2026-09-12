import json
import sys
from pathlib import Path

import bpy
from pxr import Usd, UsdGeom, UsdLux, UsdPhysics


BLENDER_COLLISION = "f1tenth_collision"
USD_COLLISION = f"userProperties:{BLENDER_COLLISION}"
BLENDER_COLLISION_ONLY = "f1tenth_collision_only"
USD_COLLISION_ONLY = f"userProperties:{BLENDER_COLLISION_ONLY}"
GEOMETRY_TYPES = {"MESH", "CURVE"}

DEFAULT_LIGHT_INTENSITY_SCALE = 683.0


def read_paths():
    arguments = sys.argv[sys.argv.index("--") + 1 :]
    blend_path = Path(arguments[0]).resolve()
    usd_path = (
        Path(arguments[1]).resolve()
        if len(arguments) > 1
        else (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "scenes"
            / f"{blend_path.stem}.usdc"
        )
    )
    return blend_path, blend_path.with_suffix(".json"), usd_path


def visible_objects(scene):
    objects = set()

    def visit(collection, parent_visible):
        collection_visible = parent_visible and not collection.hide_render
        if collection_visible:
            objects.update(
                obj for obj in collection.objects if not obj.hide_render
            )
        for child in collection.children:
            visit(child, collection_visible)

    visit(scene.collection, True)
    return objects


def collision_objects(configuration):
    selected = set()

    for name in configuration["collision_collections"]:
        selected.update(
            obj
            for obj in bpy.data.collections[name].all_objects
            if obj.type in GEOMETRY_TYPES
        )

    for name in configuration["collision_objects"]:
        selected.add(bpy.data.objects[name])

    return selected


def prepare_export(scene, configuration):
    source_objects = visible_objects(scene)
    configured_colliders = collision_objects(configuration)
    geometry = sorted(
        (obj for obj in source_objects | configured_colliders if obj.type in GEOMETRY_TYPES),
        key=lambda obj: obj.name,
    )
    lights = sorted(
        (obj for obj in source_objects if obj.type == "LIGHT"),
        key=lambda obj: obj.name,
    )

    export_collection = bpy.data.collections.new("F1TENTH_USD_Export")
    scene.collection.children.link(export_collection)
    dependency_graph = bpy.context.evaluated_depsgraph_get()
    export_objects = []

    for index, source in enumerate(geometry):
        source_name = source.name
        evaluated = source.evaluated_get(dependency_graph)
        mesh = bpy.data.meshes.new_from_object(
            evaluated,
            preserve_all_data_layers=True,
            depsgraph=dependency_graph,
        )
        matrix_world = evaluated.matrix_world.copy()
        source.name = f"F1TENTH_Source_{index}"

        temporary = bpy.data.objects.new(source_name, mesh)
        temporary.matrix_world = matrix_world
        if source in configured_colliders:
            temporary[BLENDER_COLLISION] = True
            if source not in source_objects:
                temporary[BLENDER_COLLISION_ONLY] = True
        export_collection.objects.link(temporary)
        export_objects.append(temporary)

    for index, source in enumerate(lights):
        source_name = source.name
        matrix_world = source.matrix_world.copy()
        source.name = f"F1TENTH_Source_Light_{index}"

        temporary = bpy.data.objects.new(source_name, source.data.copy())
        temporary.matrix_world = matrix_world
        export_collection.objects.link(temporary)
        export_objects.append(temporary)

    bpy.ops.object.select_all(action="DESELECT")
    for obj in export_objects:
        obj.select_set(True)

    return len(geometry), len(lights)


def author_collision(stage):
    collider_count = 0

    for prim in stage.Traverse():
        marker = prim.GetAttribute(USD_COLLISION)
        if not marker or marker.Get() is not True:
            continue

        mesh_prim = next(
            descendant
            for descendant in Usd.PrimRange(prim)
            if descendant.IsA(UsdGeom.Mesh)
        )
        UsdPhysics.CollisionAPI.Apply(mesh_prim)
        mesh_api = UsdPhysics.MeshCollisionAPI.Apply(mesh_prim)
        mesh_api.CreateApproximationAttr().Set("none")
        collision_only = prim.GetAttribute(USD_COLLISION_ONLY)
        if collision_only and collision_only.Get():
            UsdGeom.Imageable(mesh_prim).CreateVisibilityAttr().Set("invisible")
            prim.RemoveProperty(USD_COLLISION_ONLY)
        prim.RemoveProperty(USD_COLLISION)
        collider_count += 1

    return collider_count


def author_light_intensity(stage, scale):
    scaled_count = 0

    for prim in stage.Traverse():
        light = UsdLux.LightAPI(prim)
        if not light:
            continue

        intensity = light.GetIntensityAttr()
        intensity.Set(intensity.Get() * scale)
        scaled_count += 1

    return scaled_count


def main():
    blend_path, configuration_path, usd_path = read_paths()
    if Path(bpy.data.filepath).resolve() != blend_path:
        bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    with configuration_path.open(encoding="utf-8") as file:
        configuration = json.load(file)

    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene.unit_settings.scale_length = 1.0

    mesh_count, light_count = prepare_export(scene, configuration)
    usd_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.usd_export(
        filepath=str(usd_path),
        selected_objects_only=True,
        export_animation=False,
        export_materials=True,
        export_textures_mode="NEW",
        overwrite_textures=True,
        export_custom_properties=True,
        export_lights=True,
        export_cameras=False,
        convert_scene_units="METERS",
    )

    intensity_scale = configuration.get(
        "light_intensity_scale",
        DEFAULT_LIGHT_INTENSITY_SCALE,
    )
    stage = Usd.Stage.Open(str(usd_path))
    authored_collider_count = author_collision(stage)
    scaled_light_count = author_light_intensity(stage, intensity_scale)
    stage.GetRootLayer().Save()

    print(
        json.dumps(
            {
                "usd_file": str(usd_path),
                "exported_meshes": mesh_count,
                "exported_lights": light_count,
                "authored_colliders": authored_collider_count,
                "scaled_lights": scaled_light_count,
                "light_intensity_scale": intensity_scale,
            }
        )
    )


main()
