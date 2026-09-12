"""Reference details over the existing mapped Tepper scene. Run in Blender."""
import bpy, math, sys
from pathlib import Path
import numpy as np
from mathutils import Vector, Matrix
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/build-blender-scene'))
import scene_assets as pc
from scene_assets import GENERATED_TEXTURES
OUT = Path(GENERATED_TEXTURES.name) / 'tepper_details'
OUT.mkdir(parents=True, exist_ok=True)

def bsdf(mat):
    return next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'))

def unlink(mat, socket, value=None):
    p = bsdf(mat)
    s = p.inputs[socket]
    for link in list(s.links):
        mat.node_tree.links.remove(link)
    if value is not None:
        s.default_value = value

def softened_image(mat, socket, name, target, mix):
    node = bsdf(mat).inputs[socket].links[0].from_node
    src = node.image
    a = np.empty(src.size[0] * src.size[1] * 4, np.float32)
    src.pixels.foreach_get(a)
    a = a.reshape(-1, 4)
    a[:, :3] = a[:, :3] * (1 - mix) + np.array(target) * mix
    im = bpy.data.images.new(name, width=src.size[0], height=src.size[1], alpha=True)
    im.pixels.foreach_set(a.reshape(-1))
    im.filepath_raw = str(OUT / (name + '.png'))
    im.file_format = 'PNG'
    im.save()
    node.image = im

def materials():
    m = bpy.data.materials
    softened_image(m['Tepper_Polished_Concrete'], 'Base Color', 'concrete_neutral', (0.14, 0.15, 0.155), 0.4)
    for n in m['Tepper_Polished_Concrete'].node_tree.nodes:
        if n.type == 'NORMAL_MAP':
            n.inputs['Strength'].default_value = 0.1
    softened_image(m['Tepper_Maple_Lockers'], 'Base Color', 'maple_neutral', (0.66, 0.56, 0.42), 0.45)
    unlink(m['Tepper_Maple_Lockers'], 'Roughness', 0.38)
    for n in m['Tepper_Maple_Lockers'].node_tree.nodes:
        if n.type == 'NORMAL_MAP':
            n.inputs['Strength'].default_value = 0.12
    for name in ('Tepper_Warm_White_Wall', 'Tepper_White_Ceiling'):
        softened_image(m[name], 'Base Color', name + '_smooth', (0.79, 0.805, 0.81), 0.95)
        unlink(m[name], 'Roughness', 0.58)
        unlink(m[name], 'Normal')
    unlink(m['Tepper_White_Baseboard'], 'Base Color', (0.78, 0.79, 0.8, 1))
    unlink(m['Tepper_White_Baseboard'], 'Metallic', 0)
    softened_image(m['Tepper_Concrete_Column'], 'Base Color', 'column_neutral', (0.45, 0.455, 0.45), 0.7)
    for n in m['Tepper_Concrete_Column'].node_tree.nodes:
        if n.type == 'NORMAL_MAP':
            n.inputs['Strength'].default_value = 0.12
    plinth = pc.simple_material('Tepper_Reference_Maple_Plinth', (0.46, 0.33, 0.2), 0.48)
    for o in bpy.data.objects:
        if o.name.startswith('Locker_Bank') and o.name.endswith('_Plinth'):
            o.data.materials[0] = plinth
    return dict(wood=m['Tepper_Maple_Lockers'], metal=m['Tepper_Padlock_Silver'], red=m['Tepper_Padlock_Red'], white=m['Tepper_White_Ceiling'], dark=pc.simple_material('Tepper_Reference_Seam', (0.045, 0.04, 0.03), 0.65), label=pc.simple_material('Tepper_Number_Brass', (0.34, 0.32, 0.24), 0.42, 0.55))

def bevel(o, width=0.001):
    mod = o.modifiers.new('Edge highlights', 'BEVEL')
    mod.width = width
    mod.segments = 2
    return o

def box(name, loc, size, mat, rot=0):
    return pc.add_box(name, loc, size, mat, C, rot_z=rot)

def cylinder(name, loc, r, d, mat, rot):
    return bevel(pc.add_cylinder(name, loc, r, d, mat, C, segments=24, rotation=(0, math.pi / 2, rot)), 0.0008)

def locker_details(m):
    originals = [o for o in bpy.data.objects if o.name.startswith('Locker_Bank') and '_Door_' in o.name]
    for o in list(bpy.data.objects):
        if o.name.startswith('Locker_Bank') and any((s in o.name for s in ('_Door_', '_Latch_', '_Padlock_'))):
            o.hide_render = True
            o.hide_set(True)
    for (index, old) in enumerate(originals):
        bank = old.name.split('_West_')[0].split('_East_')[0]
        body = bpy.data.objects[bank + '_Body']
        side = -1 if '_West_' in old.name else 1
        r = old.rotation_euler.z
        R = Matrix.Rotation(r, 3, 'Z')
        center = old.location.copy()
        width = max((v.co.y for v in old.data.vertices)) - min((v.co.y for v in old.data.vertices))
        height = max((v.co.z for v in old.data.vertices)) - min((v.co.z for v in old.data.vertices))
        sx = old.scale.x
        sy = old.scale.y
        sz = old.scale.z
        width *= sy
        height *= sz
        half = width / 2
        bot = -height / 2
        top = max(((body.matrix_world @ v.co).z for v in body.data.vertices)) - center.z - 0.015
        g = 0.002
        polygons = [[(-half, top), (half, top), (half, -0.16), (g, -0.16), (g, 0.16), (-half, 0.16)], [(-half, bot), (half, bot), (half, -0.16 - g), (-g, -0.16 - g), (-g, 0.16 - g), (-half, 0.16 - g)]]
        for (level, poly) in enumerate(polygons):
            verts = [center + R @ Vector((x, y, z)) for x in (-0.01, 0.01) for (y, z) in poly]
            n = len(poly)
            faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, n * 2))] + [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
            ob = bevel(pc.add_polydata(f'Tepper_Ref_Door_{index:03d}_{level}', verts, faces, m['wood'], C), 0.0015)
            uv = ob.data.uv_layers.new(name='st')
            for p in ob.data.polygons:
                for li in p.loop_indices:
                    q = R.inverted() @ (ob.data.vertices[ob.data.loops[li].vertex_index].co - center)
                    uv.data[li].uv = (-q.z + index * 0.137, q.y + index * 0.371)
            ob.data.uv_layers.active = uv
            uv.active_render = True

        def world(x, y, z):
            return center + R @ Vector((x * side, y, z - center.z))
        for (level, z) in enumerate((1.76, 0.5)):
            prefix = f'Tepper_Ref_Lock_{index:03d}_{level}'
            y = width * 0.2
            bevel(box(prefix + '_Hasp', world(0.021, y, z + 0.045), (0.012, 0.025, 0.065), m['metal'], r), 0.003)
            cylinder(prefix + '_Disc', world(0.038, y, z), 0.024, 0.016, m['metal'], r)
            dial = m['red'] if (index + level) % 5 else m['metal']
            cylinder(prefix + '_Dial', world(0.048, y, z), 0.016, 0.005, dial, r)
            cylinder(prefix + '_Dial_Grip', world(0.053, y, z), 0.008, 0.007, dial, r)
            for k in range(12):
                t = k * math.tau / 12
                cylinder(prefix + f'_Tick{k}', world(0.051, y + 0.012 * math.sin(t), z + 0.012 * math.cos(t)), 0.0008, 0.001, m['metal'], r)
            for zz in (z + 0.025, z + 0.068):
                cylinder(prefix + f'_Screw_{zz:.3f}_Head', world(0.029, y, zz), 0.002, 0.002, m['metal'], r)
            points = [world(0.038, y - 0.014, z + 0.009), world(0.038, y - 0.014, z + 0.029)]
            points += [world(0.038, y + 0.014 * math.cos(t), z + 0.029 + 0.014 * math.sin(t)) for t in np.linspace(math.pi, 0, 13)]
            points += [world(0.038, y + 0.014, z + 0.009)]
            curve = bpy.data.curves.new(prefix + '_Shackle', 'CURVE')
            curve.dimensions = '3D'
            curve.bevel_depth = 0.0025
            curve.bevel_resolution = 2
            curve.use_fill_caps = True
            sp = curve.splines.new('POLY')
            sp.points.add(len(points) - 1)
            for (p, co) in zip(sp.points, points):
                p.co = (*co, 1)
            ob = bpy.data.objects.new(prefix + '_Shackle', curve)
            C.objects.link(ob)
            curve.materials.append(m['metal'])
            cylinder(prefix + '_Number_Plaque', world(0.012, -width * 0.2, 2.1 if level == 0 else 0.83), 0.016, 0.0015, m['label'], r)
    return len(originals) * 2

class Batch:

    def __init__(self):
        self.verts = []
        self.faces = []

    def box(self, loc, size):
        n = len(self.verts)
        (x, y, z) = loc
        (a, b, c) = [d / 2 for d in size]
        self.verts.extend(((x + dx * a, y + dy * b, z + dz * c) for (dx, dy, dz) in [(-1, -1, -1), (-1, -1, 1), (-1, 1, -1), (-1, 1, 1), (1, -1, -1), (1, -1, 1), (1, 1, -1), (1, 1, 1)]))
        self.faces.extend((tuple((n + i for i in f)) for f in [(0, 4, 6, 2), (1, 3, 7, 5), (0, 1, 5, 4), (2, 6, 7, 3), (0, 2, 3, 1), (4, 5, 7, 6)]))

    def finish(self, name, mat):
        o = pc.add_polydata(name, self.verts, self.faces, mat, C)
        o.data.uv_layers.active.name = 'st'
        return o

def floor_polygons(o):
    z = min(((o.matrix_world @ v.co).z for v in o.data.vertices))
    return [[o.matrix_world @ o.data.vertices[i].co for i in p.vertices] for p in o.data.polygons if all((abs((o.matrix_world @ o.data.vertices[i].co).z - z) < 0.0001 for i in p.vertices))]

def intervals(polys, x, axis):
    spans = []
    other = 1 - axis
    for poly in polys:
        hits = []
        for (a, b) in zip(poly, poly[1:] + poly[:1]):
            if a[axis] <= x < b[axis] or b[axis] <= x < a[axis]:
                hits.append(a[other] + (x - a[axis]) * (b[other] - a[other]) / (b[axis] - a[axis]))
        hits.sort()
        spans.extend(zip(hits[::2], hits[1::2]))
    merged = []
    for (lo, hi) in sorted(spans):
        if merged and lo <= merged[-1][1] + 0.001:
            merged[-1][1] = max(hi, merged[-1][1])
        else:
            merged.append([lo, hi])
    return merged

def ceilings(m):
    wood = Batch()
    grid = Batch()
    frame = Batch()
    for name in ('Tepper_Corridor_Connected_Ceiling', 'Tepper_Side_Corridor_Ceiling', 'Tepper_Locker_Room_Ceiling'):
        o = bpy.data.objects[name]
        polys = floor_polygons(o)
        pts = [p for poly in polys for p in poly]
        z = min((p.z for p in pts))
        room = 'Locker_Room' in name
        for x in np.arange(min((p.x for p in pts)) + 0.025, max((p.x for p in pts)), 0.065):
            for (lo, hi) in intervals(polys, x, 0):
                end = min(hi, 5 + 0.43 * x) if room else hi
                if end - lo > 0.04:
                    wood.box((x, (lo + end) / 2, z - 0.075), (0.04, end - lo - 0.02, 0.07))
        if room:
            for axis in (0, 1):
                for p in np.arange(min((v[axis] for v in pts)) + 0.025, max((v[axis] for v in pts)), 0.035):
                    for (lo, hi) in intervals(polys, p, axis):
                        if axis == 0:
                            lo = max(lo, 5 + 0.43 * p)
                        else:
                            hi = min(hi, (p - 5) / 0.43)
                        if hi - lo > 0.03:
                            loc = (p, (lo + hi) / 2, z - 0.07) if axis == 0 else ((lo + hi) / 2, p, z - 0.07)
                            size = (0.0015, hi - lo - 0.02, 0.006) if axis == 0 else (hi - lo - 0.02, 0.0015, 0.006)
                            grid.box(loc, size)
                for p in np.arange(min((v[axis] for v in pts)) + 0.025, max((v[axis] for v in pts)), 1.2):
                    for (lo, hi) in intervals(polys, p, axis):
                        if axis == 0:
                            lo = max(lo, 5 + 0.43 * p)
                        else:
                            hi = min(hi, (p - 5) / 0.43)
                        if hi - lo > 0.03:
                            frame.box((p, (lo + hi) / 2, z - 0.05) if axis == 0 else ((lo + hi) / 2, p, z - 0.05), (0.022, hi - lo - 0.02, 0.07) if axis == 0 else (hi - lo - 0.02, 0.022, 0.07))
    wood.finish('Tepper_Ref_Wood_Ceiling_Ribs', m['wood'])
    grid.finish('Tepper_Ref_Open_White_Ceiling_Grid', m['white'])
    frame.finish('Tepper_Ref_Ceiling_Panel_Frames', m['white'])
    led = pc.simple_material('Tepper_LED_Emission', (1, 1, 1), roughness=0.5,
                             emission=(1, 0.98, 0.94), emission_strength=8.0)
    for o in bpy.data.collections['Tepper_Lighting'].objects:
        if o.type == 'LIGHT':
            o.data.energy = 200 if 'Locker' in o.name else 150
            o.data.color = (1, 0.98, 0.94)
            o.location.z -= 0.13
            o.data.shape = 'RECTANGLE'
            o.data.size_y = 0.12
            box('Tepper_Ref_' + o.name.replace('_Area', '_Panel'),
                o.location + Vector((0, 0, 0.06)), (1.8, 0.055, 0.025),
                led)
    emission = bsdf(bpy.data.materials['Tepper_LED_Emission'])
    emission.inputs['Emission Color'].default_value = (1, 0.98, 0.94, 1)

def camera(name, loc, target, lens=28):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    o = bpy.data.objects.new(name, data)
    C.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - o.location).to_track_quat('-Z', 'Y').to_euler()
    return o

def main():
    global C
    C = bpy.data.collections.new('Tepper_Reference_Refinement')
    bpy.data.collections['Tepper_Hallway_Recreation'].children.link(C)
    m = materials()
    doors = locker_details(m)
    ceilings(m)
    camera('Tepper_Reference_Aisle_Camera', (3.8, 7.5, 1.65), (3.2, 13.7, 1.35), 25)
    camera('Tepper_Reference_Lobby_Camera', (11.7, 7.4, 1.7), (2.4, 5.8, 1.65), 23)
    lock = min((o for o in C.objects if o.name.endswith('_0_Disc') and o.location.x > 2.5 and (o.location.x < 3.4)), key=lambda o: abs(o.location.y - 8))
    camera('Tepper_Reference_Lock_Camera', lock.location + Vector((0.65, -0.16, 0.09)), lock.location, 55)
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    scene.camera = bpy.data.objects['Tepper_Reference_Lobby_Camera']
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 256
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = '//renders/tepper_reference/lobby.png'
    bpy.ops.file.make_paths_relative()
