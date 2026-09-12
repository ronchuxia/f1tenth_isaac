"""Build the final Tepper scene from its mapped geometry and source assets."""
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/build-blender-scene'))

import tepper_geometry
import tepper_materials
import tepper_details
import tepper_facades
import tepper_enclosure
import tepper_display
from scene_cleanup import organize_scene
from visual_collision_cleanup import finalize_visual_collision
from scene_assets import GENERATED_TEXTURES


def main():
    tepper_geometry.main()
    tepper_materials.main()
    tepper_details.main()
    tepper_facades.main()
    tepper_enclosure.main()
    tepper_display.main()
    scene = bpy.context.scene
    bpy.data.objects['Tepper_Hallway_Map_Overlay'].location.z = .26
    scene.frame_set(154)
    configuration = {
        'collision_collections': ['Tepper_Architecture', 'Tepper_Lockers',
                                  'Tepper_Props', 'Tepper_Hallway_Curtains'],
        'collision_objects': [],
    }
    organize_scene(configuration)
    finalize_visual_collision(configuration, 'Tepper')
    output = ROOT / 'blender/tepper_hallway_recreation.blend'
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    output.with_suffix('.json').write_text(json.dumps(configuration, indent=2) + '\n')
    GENERATED_TEXTURES.cleanup()


if __name__ == '__main__':
    main()
