"""Build the final Race2 atrium from source geometry and texture assets."""
import json
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/build-blender-scene'))
import atrium_scene
from scene_cleanup import organize_scene
from scene_assets import GENERATED_TEXTURES
from race2_collision import use_visual_colliders


def main():
    atrium_scene.main()
    configuration = use_visual_colliders()
    organize_scene(configuration)
    output = ROOT / 'blender/race2_atrium_recreation.blend'
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    output.with_suffix('.json').write_text(json.dumps(configuration, indent=2) + '\n')
    GENERATED_TEXTURES.cleanup()


if __name__ == '__main__':
    main()
