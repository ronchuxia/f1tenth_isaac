"""Build the shared atrium with Race3's own mapped track and overlay."""
import json
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/build-blender-scene'))
import atrium_scene
import race3_track
from scene_cleanup import organize_scene
from visual_collision_cleanup import finalize_visual_collision
from scene_assets import GENERATED_TEXTURES


def main():
    atrium_scene.main('Race3')
    for name in ['Race2_Track', 'Race2_Video_Refinement_Ducts', 'Race2_Measurement']:
        collection = bpy.data.collections[name]
        for obj in list(collection.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
    root = bpy.data.collections['Race2_Recreation']
    track = bpy.data.collections.new('Race3_Track')
    root.children.link(track)
    maps = bpy.data.collections.new('Race3_Measurement')
    root.children.link(maps)
    import atrium_assets
    materials = {
        'yellow_duct': atrium_assets.duct_material('Yellow_Duct_Fabric', (1.0, .60, .03)),
        'black_duct': atrium_assets.duct_material('Black_Duct_Fabric', (.016,.016,.018), dust=.22),
        'yellow_rings': atrium_assets.duct_material('Yellow_Duct_Rings', (.018,.018,.02), dust=.2),
        'black_rings': atrium_assets.duct_material('Black_Duct_Rings', (.014,.014,.016), dust=.2),
    }
    race3_track.build_race3_track(track, materials)
    race3_track.build_race3_overlay(maps)
    atrium_assets.RACE = 'Race3'
    for obj in track.objects:
        if obj.type == 'CURVE':
            for spline in obj.data.splines:
                spline.use_smooth = True
    atrium_assets.refine_track_tessellation()
    race3_track.apply_barrier_materials(track)
    for collection in list(bpy.data.collections):
        if collection.name.startswith('Race2'):
            collection.name = collection.name.replace('Race2', 'Race3', 1)
    for obj in bpy.data.objects:
        if obj.type == 'CAMERA' or obj.name.startswith('Race2_Tour'):
            obj.name = obj.name.replace('Race2', 'Race3', 1)
    bpy.context.scene.render.filepath = '//renders/race3_atrium_tour.mp4'
    configuration = {
        'collision_collections': ['Race3_Track'],
        'collision_objects': ['Atrium_Carpet_Tiles', 'Atrium_Column_+1.45',
                              'Atrium_Column_-1.45', 'NSH_Detail_Atrium_Extension_Floor'],
    }
    organize_scene(configuration)
    finalize_visual_collision(configuration, 'Race3')
    output = ROOT / 'blender/race3_atrium_recreation.blend'
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    output.with_suffix('.json').write_text(json.dumps(configuration, indent=2) + '\n')
    GENERATED_TEXTURES.cleanup()


if __name__ == '__main__':
    main()
