"""The approved thirty second rising camera tour."""
import bpy, sys
from pathlib import Path
from mathutils import Vector
ROOT = Path('/Users/xiachu/Files/projects/f1tenth_isaac')
sys.path.insert(0, str(ROOT / 'scripts/build-blender-scene'))
TOUR_KEYS = [(1, (0, -19, 1.7), (0, -4, 0.2)), (145, (0, -12, 2.1), (0, -3, 0.2)), (289, (1, -6, 2.8), (0, 1, 0.25)), (409, (3.1, 0, 4.8), (0, 5, 5.0)), (505, (3.2, 4.8, 6.8), (0, 8, 7.5)), (601, (2.8, 6.4, 7.8), (0, 0, 8.2)), (720, (0, 10.4, 8.8), (0, -9, 8.8))]

def sample(keys, frame, index):
    for k in range(len(keys) - 1):
        if frame <= keys[k + 1][0]:
            break
    (a, b) = (keys[k], keys[k + 1])
    dt = b[0] - a[0]
    t = (frame - a[0]) / dt
    (pa, pb) = (Vector(a[index]), Vector(b[index]))
    va = Vector((0, 0, 0)) if k == 0 else (pb - Vector(keys[k - 1][index])) / (b[0] - keys[k - 1][0])
    vb = Vector((0, 0, 0)) if k + 2 == len(keys) else (Vector(keys[k + 2][index]) - pa) / (keys[k + 2][0] - a[0])
    return (2 * t ** 3 - 3 * t * t + 1) * pa + (t ** 3 - 2 * t * t + t) * dt * va + (-2 * t ** 3 + 3 * t * t) * pb + (t ** 3 - t * t) * dt * vb

def main():
    s = bpy.context.scene
    col = bpy.data.collections.new('Race2_Camera_Tour')
    bpy.data.collections['Race2_Video_Refinement'].children.link(col)
    data = bpy.data.cameras.new('Race2_Tour_Camera')
    camera = bpy.data.objects.new(data.name, data)
    col.objects.link(camera)
    data.lens = 22
    data.clip_start = 0.05
    data.clip_end = 200
    data.dof.use_dof = False
    target = bpy.data.objects.new('Race2_Tour_Look_Target', None)
    col.objects.link(target)
    target.empty_display_size = 0.2
    constraint = camera.constraints.new('TRACK_TO')
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'
    keys = TOUR_KEYS
    points = []
    for frame in range(1, 721):
        camera.location = sample(keys, frame, 1)
        target.location = sample(keys, frame, 2)
        camera.keyframe_insert(data_path='location', frame=frame)
        target.keyframe_insert(data_path='location', frame=frame)
        points.append(tuple(camera.location))
    curve = bpy.data.curves.new('Race2_Tour_Path', 'CURVE')
    curve.dimensions = '3D'
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for (point, co) in zip(spline.points, points):
        point.co = (*co, 1)
    path = bpy.data.objects.new(curve.name, curve)
    col.objects.link(path)
    path.hide_render = True
    path.show_in_front = True
    path['description'] = 'Viewport guide for the baked camera animation, frames 1 through 720.'
    s.camera = camera
    s.frame_start = 1
    s.frame_end = 720
    s.render.fps = 24
    s.render.fps_base = 1
    s.render.resolution_x = 1920
    s.render.resolution_y = 1080
    s.render.resolution_percentage = 100
    s.render.use_border = False
    s.render.use_crop_to_border = False
    s.render.image_settings.media_type = 'VIDEO'
    s.render.image_settings.file_format = 'FFMPEG'
    s.render.ffmpeg.format = 'MPEG4'
    s.render.ffmpeg.codec = 'H264'
    s.render.ffmpeg.constant_rate_factor = 'HIGH'
    s.render.filepath = '//renders/race2_atrium_tour.mp4'
    s.render.use_file_extension = True
    s.cycles.samples = 128
    s.cycles.adaptive_threshold = 0.015
    for (frame, name) in [(1, 'Far atrium'), (145, 'Race track approach'), (289, 'Platform approach'), (409, 'Rise beside platform'), (601, 'Upper level'), (720, 'Atrium overview')]:
        s.timeline_markers.new(name, frame=frame)
    s.frame_set(1)
    bpy.context.view_layer.update()
