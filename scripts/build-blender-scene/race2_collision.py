"""Use Race2's finished visual meshes for collision and remove source helpers."""
import bpy


def use_visual_colliders():
    stems = ['Black_Duct_Outer', 'Yellow_Duct_Left_Hook',
             'Yellow_Duct_Upper_Hook', 'Yellow_Duct_Pillar_Connected',
             'Yellow_Duct_Lower_Hook']
    pillars = ['Pillar_Visual_-1', 'Pillar_Visual_1']
    names = ['Atrium_Carpet_Tiles', 'NSH_Detail_Atrium_Extension_Floor',
             *pillars, *(stem + suffix for stem in stems
                         for suffix in ('_Video_Sleeve', '_Fine_Ribs'))]
    colliders = [bpy.data.objects[name] for name in names]
    assert all(o.type == 'MESH' and not o.hide_render for o in colliders)

    # Bake the full stack in order, preserving the bevel before the door Boolean.
    # Applying only the Boolean out of order could change the finished surface.
    graph = bpy.context.evaluated_depsgraph_get()
    for name in pillars:
        obj = bpy.data.objects[name]
        if not obj.modifiers:
            continue
        active_uv = obj.data.uv_layers.active.name if obj.data.uv_layers.active else None
        render_uv = next((uv.name for uv in obj.data.uv_layers if uv.active_render), None)
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh(
            preserve_all_data_layers=True, depsgraph=graph).copy()
        evaluated.to_mesh_clear()
        if active_uv:
            mesh.uv_layers.active = mesh.uv_layers[active_uv]
        if render_uv:
            mesh.uv_layers[render_uv].active_render = True
        obj.modifiers.clear()
        obj.data = mesh

    obsolete = ['Atrium_Column_+1.45', 'Atrium_Column_-1.45',
                'Pillar_Door_Recess_-1', 'Pillar_Door_Recess_1',
                'Race2_Map_Reference', 'Race2_Tour_Path',
                *(stem + suffix for stem in stems for suffix in ('', '_Ribs'))]
    for name in obsolete:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)
    for name in ('Race2_Collision', 'Race2_Helpers', 'Race2_Maps'):
        collection = bpy.data.collections.get(name)
        if collection is not None and not collection.objects and not collection.children:
            bpy.data.collections.remove(collection)
    return {'collision_collections': [], 'collision_objects': sorted(names)}
