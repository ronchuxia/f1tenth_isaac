"""Keep render and simulation dependencies and organize objects by purpose."""
import bpy


def organize_scene(configuration):
    scene = bpy.context.scene
    visible = set()

    def visit(collection):
        if collection.hide_render:
            return
        visible.update(o for o in collection.objects if not o.hide_render)
        for child in collection.children:
            visit(child)

    visit(scene.collection)
    colliders = {bpy.data.objects[n] for n in configuration['collision_objects']}
    for name in configuration['collision_collections']:
        colliders.update(o for o in bpy.data.collections[name].all_objects
                         if o.type in {'MESH', 'CURVE'})
    guides = {o for o in scene.objects if 'Map_' in o.name or 'Tour_' in o.name
              or 'Trajectory' in o.name or o.type == 'CAMERA'}
    keep = visible | colliders | guides
    # Blender's user map includes parents, constraints, modifiers and drivers.
    users = bpy.data.user_map()
    pending = list(keep)
    visited = set()
    dependencies = {}
    for dependency, owners in users.items():
        for owner in owners:
            dependencies.setdefault(owner, set()).add(dependency)
    while pending:
        owner = pending.pop()
        if owner in visited or isinstance(owner, (bpy.types.Scene, bpy.types.Collection)):
            continue
        visited.add(owner)
        if isinstance(owner, bpy.types.Object):
            keep.add(owner)
        pending.extend(dependencies.get(owner, ()))
    removed = [o.name for o in bpy.data.objects if o not in keep]
    for name in removed:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

    prefix = 'Tepper' if 'Tepper_Hallway_Recreation' in bpy.data.collections else (
        'Race3' if 'Race3_Recreation' in bpy.data.collections else 'Race2')
    root = bpy.data.collections.new(prefix + '_Scene')
    scene.collection.children.link(root)
    groups = {}
    for name in ('Architecture', 'Track', 'Furniture', 'Lockers', 'Lighting',
                 'Cameras', 'Maps', 'Collision', 'Helpers'):
        collection = bpy.data.collections.new(prefix + '_' + name + '_Final')
        root.children.link(collection)
        groups[name] = collection
    old_collections = [c for c in bpy.data.collections if c not in {root, *groups.values()}]
    for obj in list(scene.objects):
        original = [c.name for c in obj.users_collection]
        if obj.type == 'LIGHT':
            group = 'Lighting'
        elif obj.type == 'CAMERA' or 'Tour_' in obj.name or 'Trajectory' in obj.name:
            group = 'Cameras'
        elif 'Map_' in obj.name:
            group = 'Maps'
        elif obj not in visible:
            group = 'Collision' if obj in colliders else 'Helpers'
        elif any('Track' in n or n.endswith('_Ducts') for n in original):
            group = 'Track'
        elif any('Locker' in n for n in original) or obj.name.startswith('Locker_'):
            group = 'Lockers'
        elif any('Furniture' in n or 'Props' in n or 'Bins_Wall' in n for n in original):
            group = 'Furniture'
        else:
            group = 'Architecture'
        groups[group].objects.link(obj)
        for collection in list(obj.users_collection):
            if collection != groups[group]:
                collection.objects.unlink(obj)
        obj.hide_render = obj not in visible
    for collection in old_collections:
        bpy.data.collections.remove(collection)
    for name, collection in groups.items():
        if not collection.objects:
            bpy.data.collections.remove(collection)
        else:
            collection.name = prefix + '_' + name
    configuration['collision_collections'] = []
    configuration['collision_objects'] = sorted(o.name for o in colliders)
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    bpy.ops.file.pack_all()
    bpy.data.use_autopack = True
    return removed
