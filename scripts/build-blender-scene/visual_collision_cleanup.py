"""Finalize Race3 and Tepper using their visible geometry for simulation."""
from pathlib import Path

import bpy

from race_atrium_common import load_pgm_map


def bake_mesh(obj):
    graph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(graph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=graph).copy()
    evaluated.to_mesh_clear()
    active = obj.data.uv_layers.active
    render = next((uv.name for uv in obj.data.uv_layers if uv.active_render), None)
    if active:
        mesh.uv_layers.active = mesh.uv_layers[active.name]
    if render:
        mesh.uv_layers[render].active_render = True
    obj.modifiers.clear()
    obj.data = mesh


def bake_path_motion(objects):
    """Preserve every rendered frame before removing path constraints."""
    if not objects:
        return
    scene = bpy.context.scene
    original_frame = scene.frame_current
    frames = range(scene.frame_start, scene.frame_end + 1)
    matrices = {obj: [] for obj in objects}
    for frame in frames:
        scene.frame_set(frame)
        for obj in objects:
            assert obj.parent is None, obj.name
            matrices[obj].append(obj.matrix_world.copy())
    interpolation = bpy.context.preferences.edit.keyframe_new_interpolation_type
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
    try:
        for obj in objects:
            obj.constraints.clear()
            obj.animation_data_clear()
            obj.rotation_mode = 'QUATERNION'
            previous = None
            for frame, matrix in zip(frames, matrices[obj]):
                location, rotation, scale = matrix.decompose()
                if previous is not None and rotation.dot(previous) < 0:
                    rotation.negate()
                previous = rotation.copy()
                obj.location, obj.rotation_quaternion, obj.scale = location, rotation, scale
                for path in ('location', 'rotation_quaternion', 'scale'):
                    obj.keyframe_insert(data_path=path, frame=frame)
        for index, frame in enumerate(frames):
            scene.frame_set(frame)
            for obj in objects:
                error = max(abs(a-b) for row_a, row_b in
                            zip(obj.matrix_world, matrices[obj][index])
                            for a, b in zip(row_a, row_b))
                assert error < 1e-5, (obj.name, frame, error)
    finally:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = interpolation
        scene.frame_set(original_frame)


def finalize_visual_collision(configuration, prefix):
    """Run after organize_scene, so all final visual collections are available."""
    assert prefix in {'Race3', 'Tepper'}
    scene = bpy.context.scene
    overlay_name, image_name = (
        ('Race3_Map_Ground_Overlay', 'race3_clean.pgm') if prefix == 'Race3'
        else ('Tepper_Hallway_Map_Overlay', 'hallway.pgm'))
    overlay = bpy.data.objects[overlay_name]
    visible = {obj for obj in scene.objects if not obj.hide_render}
    obsolete = {obj for obj in scene.objects if obj.hide_render and obj != overlay}

    # Capture users before mutations, and reject unhandled dependencies.
    users = bpy.data.user_map()
    dependents = {owner for obj in obsolete for owner in users.get(obj, ())
                  if isinstance(owner, bpy.types.Object) and owner not in obsolete}
    animated = sorted((obj for obj in dependents if obj.constraints), key=lambda o: o.name)
    bake_path_motion(animated)
    baked = []
    for obj in sorted(dependents, key=lambda o: o.name):
        if obj.type == 'MESH' and obj.modifiers:
            bake_mesh(obj)
            baked.append(obj.name)
    users = bpy.data.user_map()
    for obj in obsolete:
        remaining = [owner.name for owner in users.get(obj, ())
                     if isinstance(owner, bpy.types.Object) and owner not in obsolete]
        assert not remaining, (obj.name, remaining)

    if prefix == 'Race3':
        names = set(configuration['collision_objects'])
        names.difference_update({'Atrium_Column_-1.45', 'Atrium_Column_+1.45'})
        names.update({'Pillar_Visual_-1', 'Pillar_Visual_1'})
    else:
        names = {obj.name for group in ('Architecture', 'Furniture', 'Lockers')
                 for obj in bpy.data.collections[prefix + '_' + group].all_objects
                 if obj in visible and obj.type in {'MESH', 'CURVE'}}
    assert all(bpy.data.objects[name] in visible for name in names)
    removed = sorted(obj.name for obj in obsolete)
    for obj in obsolete:
        bpy.data.objects.remove(obj, do_unlink=True)
    for name in (prefix + '_Collision', prefix + '_Helpers'):
        collection = bpy.data.collections.get(name)
        if collection and not collection.objects and not collection.children:
            bpy.data.collections.remove(collection)

    path = Path(__file__).resolve().parents[2] / 'maps' / image_name
    image = load_pgm_map(str(path))
    for material in overlay.data.materials:
        if material and material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type == 'TEX_IMAGE':
                    node.image = image
    overlay['source_path'] = str(path)
    overlay.hide_render = True
    overlay.hide_viewport = False
    overlay.hide_set(False)
    bpy.context.view_layer.update()
    assert overlay.visible_get()
    assert visible == {obj for obj in scene.objects if not obj.hide_render}
    assert all(bpy.data.objects[name].visible_get() for name in names)
    configuration['collision_collections'] = []
    configuration['collision_objects'] = sorted(names)
    return {'removed': removed, 'baked_meshes': baked,
            'baked_motion': [obj.name for obj in animated], 'colliders': len(names)}
