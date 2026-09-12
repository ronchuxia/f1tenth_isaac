"""Construct the shared final atrium around the original Race2 map geometry."""
import bpy
import race_atrium_common as common
import race2_track


def main(race='Race2'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'METERS'
    scene.unit_settings.scale_length = 1.0
    root = common.create_collection('Race2_Recreation', scene.collection)
    architecture = common.create_collection('Race2_Architecture', root)
    track = common.create_collection('Race2_Track', root)
    measurement = common.create_collection('Race2_Measurement', root)
    cameras = common.create_collection('Race2_Lighting', root)
    materials, ducts = common.create_shared_materials()
    back = 13.35 + common.BACK_ASSEMBLY_FORWARD_SHIFT_Y + common.BACK_WALL_EXTENSION_Y + .15
    common.build_tiled_floor(architecture, materials['carpet'], length=back + 11,
                            center_y=(back - 11) * .5)
    for suffix, x in [('+1.45', 1.1), ('-1.45', -1.1)]:
        common.add_capsule_prism('Atrium_Column_' + suffix, (x, 2.2, 1.475),
                                 .41, 1.82, 2.95, materials['cream'], architecture, bevel=.04)
    if race == 'Race2':
        race2_track.build_shared_race2_track(track, ducts)
        race2_track.build_map_overlay(measurement)
    for name in ['Hero', 'Overhead']:
        data = bpy.data.cameras.new('Race2_' + name + '_Camera_Data')
        camera = bpy.data.objects.new('Race2_' + name + '_Camera', data)
        cameras.objects.link(camera)
        if name == 'Overhead':
            data.type = 'ORTHO'
        else:
            scene.camera = camera
    scene.world = bpy.data.worlds.new('Atrium_World')
    scene.world.use_nodes = True
    import atrium_assets
    atrium_assets.main()
    import atrium_surfaces
    atrium_surfaces.main(build_ducts=race == 'Race2')
    import atrium_camera
    atrium_camera.main()
