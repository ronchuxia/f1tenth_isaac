"""Photographed hallway facades over the preserved, mapped Tepper scene."""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector, Matrix
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/build-blender-scene'))
import scene_assets as pc
from tepper_details import bevel, bsdf
C = None
M = {}
MODULES = []
CUTTERS = []

def box(name, center, size, material, angle=0, edge=0.001):
    o = pc.add_box('TH_' + name, center, size, material, C, rot_z=angle)
    o.data.uv_layers.active.name = 'st'
    if material == M.get('wood'):
        for q in o.data.uv_layers.active.data:
            q.uv = (-q.uv.y, q.uv.x)
    if edge:
        bevel(o, edge)
    return o

def point(a, b, t, z=0):
    return Vector((a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, z))

def frame_at(x, side):
    o = bpy.data.objects['Tepper_Corridor_' + side + '_Connected_Wall']
    direction = Vector((0, 1 if side == 'North' else -1, 0))
    origin = Vector((x, 0.035 * x + 0.95, 3.1))
    inv = o.matrix_world.inverted()
    (hit, p, n, face) = o.ray_cast(inv @ origin, inv.to_3x3() @ direction)
    assert hit, (x, side)
    p = o.matrix_world @ p
    n = o.matrix_world.to_3x3() @ n
    if n.dot(direction) > 0:
        n = -n
    t = Vector((-n.y, n.x, 0))
    if t.x < 0:
        t = -t
    return (p, t, n.normalized(), math.atan2(t.y, t.x))

def cut(o, cutter):
    a = [o.matrix_world @ Vector(v) for v in o.bound_box]
    b = [cutter.matrix_world @ Vector(v) for v in cutter.bound_box]
    if any((max((v[i] for v in a)) < min((v[i] for v in b)) or min((v[i] for v in a)) > max((v[i] for v in b)) for i in range(3))):
        return
    bpy.context.view_layer.objects.active = o
    mod = o.modifiers.new('Facade opening', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)

def duplicate(o, name):
    q = o.copy()
    q.data = o.data.copy()
    q.name = 'TH_' + name
    C.objects.link(q)
    q.hide_render = False
    q.hide_set(False)
    o.hide_render = True
    o.hide_set(True)
    return q

def pane(name, p, size, angle):
    return box(name, p, size, M['glass'], angle, 0.0005)

def cylinder(name, p, radius, depth, mat, rotation):
    return pc.add_cylinder('TH_' + name, p, radius, depth, mat, C, segments=20, rotation=rotation)

def bay(tag, x, width, side, wall, opening_only=False):
    (p, t, n, angle) = frame_at(x, side)
    p.z = 0

    def loc(u, d, z):
        return p + t * u + n * d + Vector((0, 0, z))
    cutter = box(tag + '_Opening_Cutter', loc(0, -0.08, 1.49), (width, 0.5, 2.94), M['white'], angle, 0)
    bpy.context.view_layer.update()
    cut(wall, cutter)
    CUTTERS.append(cutter)
    if opening_only:
        return
    fixed = x > -20.15 and tag != 'South_Bay_05'
    framewidth = 0.044
    for u in (-width / 2 + 0.025, width / 2 - 0.025):
        box(tag + '_Jamb', loc(u, -0.04, 1.51), (0.05, 0.075, 2.98), M['silver'], angle)
    for z in (0.06, 2.54, 2.96):
        box(tag + '_Rail', loc(0, -0.04, z), (width, 0.075, 0.052), M['silver'], angle)
    woodwidth = min(0.57, width * 0.22)
    woodleft = -width / 2 + 0.05
    doorleft = woodleft + woodwidth + 0.045
    doorwidth = min(0.92, width * 0.38)
    doorright = doorleft + doorwidth
    if side == 'North':
        box(tag + '_Wood_Panel', loc(woodleft + woodwidth / 2, -0.052, 1.51), (woodwidth, 0.025, 2.85), M['wood'], angle)
    elif not fixed:
        pane(tag + '_Full_Height_Sidelight', loc(woodleft + woodwidth / 2, -0.052, 1.51), (woodwidth, 0.012, 2.85), angle)
    if fixed:
        left = -width / 2 + 0.05 + (woodwidth if side == 'North' else 0)
        right = width / 2 - 0.05
        pane('Fixed_' + tag, loc((left + right) / 2, -0.055, 1.3), (right - left, 0.012, 2.4), angle)
        if right - left > 1.45:
            box('Fixed_Mullion_' + tag, loc((left + right) / 2, -0.035, 1.3), (0.036, 0.065, 2.45), M['silver'], angle)
    else:
        for u in (doorleft, doorright):
            box(tag + '_Door_Stile', loc(u, -0.04, 1.29), (0.04, 0.067, 2.48), M['silver'], angle)
        pane(tag + '_Door_Glass', loc((doorleft + doorright) / 2, -0.052, 1.29), (doorwidth - 0.044, 0.012, 2.4), angle)
        for z in (0.1, 2.51):
            box(tag + '_Door_Crossrail', loc((doorleft + doorright) / 2, -0.035, z), (doorwidth, 0.07, 0.045), M['silver'], angle)
        rest = width / 2 - 0.055 - doorright
        if rest > 0.1:
            pane(tag + '_Sidelight', loc(doorright + rest / 2, -0.055, 1.3), (rest - 0.025, 0.012, 2.4), angle)
            if rest > 1.05:
                box(tag + '_Sidelight_Mullion', loc(doorright + rest / 2, -0.035, 1.51), (0.04, 0.065, 2.9), M['silver'], angle)
    pane(tag + '_Transom', loc((woodleft + woodwidth + width / 2) / 2, -0.055, 2.75), (width - woodwidth - 0.11, 0.012, 0.34), angle)
    if not fixed:
        hu = doorright - 0.12
        box(tag + '_Handle_Rose', loc(hu, 0.004, 1.04), (0.046, 0.018, 0.14), M['silver'], angle, 0.006)
        box(tag + '_Lever_Stem', loc(hu, 0.035, 1.08), (0.021, 0.062, 0.022), M['silver'], angle, 0.006)
        box(tag + '_Lever', loc(hu - 0.065, 0.068, 1.08), (0.15, 0.022, 0.022), M['silver'], angle, 0.007)
        for z in (0.34, 1.36, 2.25):
            box(tag + '_Hinge', loc(doorleft, 0.0, z), (0.025, 0.033, 0.082), M['silver'], angle, 0.004)
        box(tag + '_Closer', loc((doorleft + doorright) / 2, 0.009, 2.47), (0.23, 0.07, 0.06), M['silver'], angle, 0.005)
        box(tag + '_Closer_Arm', loc((doorleft + doorright) / 2 + 0.15, 0.053, 2.43), (0.33, 0.013, 0.014), M['silver'], angle)
    if side == 'North' and (tag == 'North_Bay_03' or tag.startswith('Classroom_Entrance_')):
        display(tag, loc(woodleft + woodwidth / 2, 0.07, 1.61), angle, n)
    MODULES.append({'tag': tag, 'side': side, 'center': list(p), 'width': width, 'tangent': list(t), 'inward_normal': list(n), 'region': 'before_marked' if x < -26 else 'marked_or_between'})

def display(tag, p, angle, n):
    box(tag + '_Display_Case', p, (0.43, 0.08, 0.64), M['black'], angle, 0.005)
    box(tag + '_Display_Bezel', p + n * 0.043, (0.393, 0.009, 0.595), M['bezel'], angle, 0.002)
    box(tag + '_Display_Screen', p + n * 0.05, (0.351, 0.004, 0.55), M['screen'], angle, 0.001)

def area(name, loc, energy, sizex, sizey):
    data = bpy.data.lights.new('TH_' + name, 'AREA')
    data.energy = energy
    data.shape = 'RECTANGLE'
    data.size = sizex
    data.size_y = sizey
    data.color = (1, 0.96, 0.88)
    o = bpy.data.objects.new(data.name, data)
    C.objects.link(o)
    o.location = loc
    return o

def trim(walls):
    originals = list(bpy.data.objects)
    for o in originals:
        if o.type != 'MESH' or 'Baseboard' not in o.name:
            continue
        if not any((s in o.name for s in ('Corridor_North', 'Corridor_South', 'Short_Room_Corridor', 'Elevator_Entrance'))):
            continue
        q = duplicate(o, o.name + '_Visible')
        if 'Left_Wall' in o.name or 'Left_Return' in o.name:
            q.location.x += 0.085
        elif 'Right_Wall' in o.name or 'Right_Return' in o.name:
            q.location.x -= 0.085
        else:
            q.location.y += 0.085 if 'South' in o.name or 'Elevator' in o.name else -0.085
        bpy.context.view_layer.update()
        for cutter in CUTTERS:
            cut(q, cutter)
    for idx in (1, 2):
        prefix = f'Tepper_Short_Room_Corridor_{idx:02d}_Room_Door'
        door = bpy.data.objects[prefix]
        a = door.rotation_euler.z
        t = Vector((math.cos(a), math.sin(a), 0))
        n = Vector((math.sin(a), -math.cos(a), 0))
        p = door.location.copy()
        p.z = 0
        for o in originals:
            if o.name.startswith(prefix):
                o.hide_render = True
                o.hide_set(True)
        for u in (-0.505, 0.505):
            box(f'Recess_{idx}_Stile', p + t * u + Vector((0, 0, 1.23)), (0.044, 0.07, 2.46), M['silver'], a)
        for z in (0.055, 2.45):
            box(f'Recess_{idx}_Rail', p + Vector((0, 0, z)), (1.05, 0.07, 0.045), M['silver'], a)
        pane(f'Recess_{idx}_Glass', p + Vector((0, 0, 1.24)), (0.975, 0.012, 2.35), a)
        box(f'Recess_{idx}_Lever', p + t * 0.37 + n * 0.07 + Vector((0, 0, 1.08)), (0.15, 0.025, 0.025), M['silver'], a, 0.007)
        box(f'Recess_{idx}_Mat', p + n * 0.48 + Vector((0, 0, 0.027)), (0.68, 0.42, 0.012), M['mat'], a, 0.006)

def ceiling():
    p = Vector((-3.85, 1.4, 2.9))
    box('Exit_Case', p, (0.055, 0.33, 0.17), M['white'])
    for sign in (-1, 1):
        data = bpy.data.curves.new('TH_Exit_Text', 'FONT')
        data.body = 'EXIT'
        data.size = 0.095
        data.align_x = 'CENTER'
        data.align_y = 'CENTER'
        data.extrude = 0.0003
        o = bpy.data.objects.new('TH_Exit_Lettering', data)
        C.objects.link(o)
        o.location = p + Vector((sign * 0.029, 0, 0))
        o.rotation_euler = (math.pi / 2, 0, sign * math.pi / 2)
        data.materials.append(M['green'])

def camera(name, x, target):
    (p1, _, _, _) = frame_at(x, 'North')
    (p2, _, _, _) = frame_at(x, 'South')
    p = (p1 + p2) / 2
    p.z = 1.5
    d = bpy.data.cameras.new('TH_' + name)
    d.lens = 25
    o = bpy.data.objects.new(d.name, d)
    C.objects.link(o)
    o.location = p
    o.rotation_euler = (Vector(target) - p).to_track_quat('-Z', 'Y').to_euler()
    return o

def build_facades():
    global C, M, MODULES, CUTTERS
    MODULES = []
    CUTTERS = []
    C = bpy.data.collections.new('Tepper_Hallway_Refinement')
    bpy.data.collections['Tepper_Hallway_Recreation'].children.link(C)
    mats = bpy.data.materials
    M = {'white': mats['Tepper_Warm_White_Wall'], 'wood': mats['Tepper_Maple_Lockers'], 'glass': mats['Tepper_Glass'], 'floor': mats['Tepper_Polished_Concrete'], 'silver': mats['Tepper_Brushed_Aluminum'], 'door': mats['Tepper_Painted_Door']}
    M['silver'] = M['silver'].copy()
    M['silver'].name = 'TH_Anodized_Aluminum'
    bsdf(M['silver']).inputs['Base Color'].default_value = (0.42, 0.44, 0.46, 1)
    M['glass'] = M['glass'].copy()
    M['glass'].name = 'TH_Architectural_Glass'
    bsdf(M['glass']).inputs['Alpha'].default_value = 0.22
    M['black'] = pc.simple_material('TH_Display_Frame', (0.009, 0.011, 0.013), 0.33)
    M['bezel'] = pc.simple_material('TH_Display_Bezel', (0.018, 0.021, 0.024), 0.2)
    M['screen'] = pc.simple_material('TH_Display_Screen', (0.02, 0.034, 0.06), 0.15, emission=(0.016, 0.023, 0.039), emission_strength=0.18)
    M['mat'] = pc.simple_material('TH_Door_Mat', (0.14, 0.026, 0.018), 0.96)
    M['emitter'] = pc.simple_material('TH_Cove_Light', (1, 0.95, 0.8), 0.4, emission=(1, 0.94, 0.8), emission_strength=7)
    M['green'] = pc.simple_material('TH_Exit_Green', (0.008, 0.24, 0.04), 0.4, emission=(0.01, 0.6, 0.06), emission_strength=2)
    walls = {side: duplicate(bpy.data.objects['Tepper_Corridor_' + side + '_Connected_Wall'], side + '_Visible_Wall') for side in ('North', 'South')}
    for (side, items) in [('North', [(-35.3, 2.7), (-31.9, 2.7), (-28.2, 2.6), (-19.05, 1.65), (-14.8, 2.7), (-11.4, 2.7)]), ('South', [(-37.5, 2.9), (-33.5, 2.9), (-29.5, 2.9), (-25.5, 2.9), (-21.5, 2.9), (-17.5, 2.9), (-14, 1.9)])]:
        for (i, (x, w)) in enumerate(items):
            bay(f'{side}_Bay_{i:02d}', x, w, side, walls[side], opening_only=side == 'North' and i != 3)
    for (prefix, x, w) in [('Tepper_Corridor_West_Glass_Wall', -38.5, 2.48), ('Tepper_Corridor_Middle_Glass_Wall', -7.85, 2.45)]:
        for o in list(bpy.data.objects):
            if o.name.startswith(prefix):
                o.hide_render = True
                o.hide_set(True)
        bay(prefix, x, w, 'North', walls['North'], opening_only=True)
    trim(walls)
    for o in CUTTERS:
        bpy.data.objects.remove(o, do_unlink=True)
    ceiling()
    camera('Marked_West_Camera', -29, (-18, 0.4, 1.4))
    camera('Marked_East_Camera', -18, (-2, 1.4, 1.4))
    camera('Earlier_Hallway_Camera', -38, (-26, -0.1, 1.4))
    camera('East_Close_Camera', -12.7, (-2, 1.5, 1.35))
    bpy.context.view_layer.update()
    s = bpy.context.scene
    s.camera = bpy.data.objects['TH_Marked_East_Camera']
    s.render.filepath = '//renders/tepper_hallway/marked_east.png'
    s.cycles.samples = 256
    return list(MODULES)
NORTH = [(-40, 0.415), (-17.65, 1.292), (-6.6, 1.95), (-3.35, 2.6), (0.2, 2.892)]
SOUTH = [(-40, -1.636), (-17.6, -0.961), (-17.5, -0.919), (-2.5, -0.051), (-0.5, 0.011)]

def y_at(x, points):
    for ((a, b), (c, d)) in zip(points, points[1:]):
        if a <= x <= c:
            return b + (d - b) * (x - a) / (c - a)
    raise ValueError(x)

def curtain(module, collection, mat):
    p = Vector(module['center'])
    n = Vector(module['inward_normal'])
    t = Vector(module['tangent'])
    w = module['width'] + 0.065
    steps = math.ceil(w / 0.015)
    verts = []
    faces = []
    for (j, z) in enumerate((0.016, 3.045)):
        for i in range(steps + 1):
            u = -w / 2 + w * i / steps
            fold = 0.018 * math.cos(u * math.tau / 0.09)
            verts.append(p + t * u + n * (-0.13 + fold) + Vector((0, 0, z)))
    for i in range(steps):
        faces.append((i, i + 1, steps + 2 + i, steps + 1 + i))
    o = pc.add_polydata('THC_Curtain_' + module['tag'], verts, faces, mat, collection, smooth=True)
    mod = o.modifiers.new('Opaque fabric thickness', 'SOLIDIFY')
    mod.thickness = 0.004
    o['hallway_curtain'] = True
    o['covers_glazing_module'] = module['tag']
    return o

def add_curtains_and_lighting(modules):
    global C, M
    C = bpy.data.collections['Tepper_Hallway_Refinement']
    M = {'white': bpy.data.materials['Tepper_Warm_White_Wall'], 'glass': bpy.data.materials['TH_Architectural_Glass'], 'silver': bpy.data.materials['TH_Anodized_Aluminum'], 'black': bpy.data.materials['TH_Display_Frame'], 'emitter': bpy.data.materials['TH_Cove_Light']}
    light_centers = []
    for (side, points, sign) in [('South', SOUTH, 1)]:
        for (i, ((x1, y1), (x2, y2))) in enumerate(zip(points, points[1:])):
            if x2 <= -39 or x1 >= -3.5:
                continue
            a = max(x1, -39)
            b = min(x2, -3.5)
            v1 = Vector((a, y_at(a, points) + sign * 0.09, 3.09))
            v2 = Vector((b, y_at(b, points) + sign * 0.09, 3.09))
            d = v2 - v1
            ang = math.atan2(d.y, d.x)
            box(f'Aligned_{side}_Cove_Profile_{i}', (v1 + v2) / 2, (d.length, 0.085, 0.035), M['white'], ang)
            box(f'Aligned_{side}_Cove_LED_{i}', (v1 + v2) / 2 + Vector((0, sign * 0.028, -0.002)), (d.length, 0.02, 0.01), M['emitter'], ang)
            count = math.ceil(d.length / 3)
            for j in range(count):
                p = v1 + d * ((j + 0.5) / count) + Vector((0, sign * 0.055, -0.05))
                light = area(f'Aligned_{side}_Wash_{i}_{j}', p, 42 * d.length / count / 3, d.length / count, 0.09)
                light.rotation_euler.z = ang
    for (i, x) in enumerate(range(-38, -3, 2)):
        center = (y_at(x, NORTH) + y_at(x, SOUTH)) / 2
        p = Vector((x, center, 3.083))
        light_centers.append(list(p))
        cylinder(f'Aligned_Downlight_Trim_{i}', p, 0.029, 0.009, M['black'], (0, 0, 0))
        cylinder(f'Aligned_Downlight_Lens_{i}', p - Vector((0, 0, 0.006)), 0.013, 0.005, M['emitter'], (0, 0, 0))
    curtains = bpy.data.collections.new('Tepper_Hallway_Curtains')
    bpy.data.collections['Tepper_Hallway_Recreation'].children.link(curtains)
    mat = pc.simple_material('Tepper_Opaque_Curtain', (0.48, 0.5, 0.51), 0.94)
    bsdf(mat).inputs['Alpha'].default_value = 1
    bsdf(mat).inputs['Transmission Weight'].default_value = 0
    curtain_names = [curtain(m, curtains, mat).name for m in modules if m['side'] == 'South']
    bpy.context.view_layer.update()
    bpy.context.scene.camera = bpy.data.objects['TH_Marked_East_Camera']

def finish_glazing(modules):
    global C, M, MODULES, CUTTERS
    MODULES = []
    CUTTERS = []
    C = bpy.data.collections['Tepper_Hallway_Refinement']
    m = bpy.data.materials
    M = {k: m[v] for (k, v) in {'white': 'Tepper_Warm_White_Wall', 'wood': 'Tepper_Maple_Lockers', 'glass': 'TH_Architectural_Glass', 'floor': 'Tepper_Polished_Concrete', 'silver': 'TH_Anodized_Aluminum', 'door': 'Tepper_Painted_Door', 'black': 'TH_Display_Frame', 'bezel': 'TH_Display_Bezel', 'screen': 'TH_Display_Screen'}.items()}
    wall = bpy.data.objects['TH_North_Visible_Wall']
    for (tag, x, w) in [('Classroom_Entrance_1', -36.9, 5.78), ('Classroom_Entrance_2', -30.12, 6.34)]:
        bay(tag, x, w, 'North', wall)
    (p, t, n, a) = frame_at(-11.42, 'North')
    p.z = 0
    w = 9.56
    cutter = box('Lockerward_Glass_Cutter', p - n * 0.08 + Vector((0, 0, 1.49)), (w, 0.7, 2.94), M['white'], a, 0)
    bpy.context.view_layer.update()
    cut(wall, cutter)
    CUTTERS.append(cutter)
    for u in (-w / 2 + 0.025, w / 2 - 0.025):
        box('Lockerward_Glass_Jamb', p + t * u - n * 0.04 + Vector((0, 0, 1.51)), (0.05, 0.075, 2.98), M['silver'], a)
    for z in (0.06, 2.96):
        box('Lockerward_Glass_Rail', p - n * 0.04 + Vector((0, 0, z)), (w, 0.075, 0.052), M['silver'], a)
    pane('Lockerward_Continuous_Glass', p - n * 0.055 + Vector((0, 0, 1.51)), (w - 0.1, 0.012, 2.84), a)
    MODULES.append({'tag': 'Lockerward_Continuous', 'center': list(p), 'width': w, 'tangent': list(t), 'inward_normal': list(n), 'side': 'North'})
    target = bpy.data.objects['Tepper_Corridor_Glass_Door_Glass']
    origin = target.location.copy()
    angle = target.rotation_euler.z
    source = bpy.data.objects['TH_South_Bay_05_Door_Glass']
    center = source.location.copy()
    delta = angle - source.rotation_euler.z
    transform = Matrix.Translation(origin) @ Matrix.Rotation(angle, 4, 'Z') @ Matrix.Diagonal((0.9 / 0.92, -1, 1, 1)) @ Matrix.Rotation(-source.rotation_euler.z, 4, 'Z') @ Matrix.Translation(-center)
    for o in list(bpy.data.objects):
        if o.name.startswith('Tepper_Corridor_Glass_Door_'):
            o.hide_render = True
            o.hide_set(True)
        if o.name.startswith('TH_South_Bay_05_') and any((k in o.name for k in ('_Door_', '_Handle_', '_Lever', '_Hinge', '_Closer'))):
            q = o.copy()
            q.data = o.data.copy()
            q.name = o.name.replace('TH_South_Bay_05_', 'TH_Single_Room_')
            C.objects.link(q)
            q.matrix_world = transform @ o.matrix_world
    left = list(MODULES) + [v for v in modules if v['tag'] == 'North_Bay_03']
    for (tag, obj, w) in [('Single_Room', target, 0.99)] + [(f'Recess_{i}', bpy.data.objects[f'TH_Recess_{i}_Glass'], 1.06) for i in (1, 2)]:
        a = obj.rotation_euler.z
        p = obj.location.copy()
        p.z = 0
        left.append({'tag': tag, 'center': list(p), 'width': w, 'tangent': [math.cos(a), math.sin(a), 0], 'inward_normal': [math.sin(a), -math.cos(a), 0], 'side': 'North'})
    curtains_collection = bpy.data.collections['Tepper_Hallway_Curtains']
    for v in left:
        curtain(v, curtains_collection, m['Tepper_Opaque_Curtain'])
    for o in list(C.objects):
        if 'Baseboard' in o.name and 'North' in o.name:
            for cutter in CUTTERS:
                cut(o, cutter)
    for o in CUTTERS:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()
    bpy.context.scene.camera = bpy.data.objects['TH_Marked_West_Camera']
    return left

def finish_junctions():
    global C, M, MODULES, CUTTERS
    C = bpy.data.collections['Tepper_Hallway_Refinement']
    M = {'white': bpy.data.materials['Tepper_Warm_White_Wall'], 'silver': bpy.data.materials['TH_Anodized_Aluminum'], 'emitter': bpy.data.materials['TH_Cove_Light']}
    gaps = [(-40, -39.79), (-34.01, -33.29), (-26.95, -26.06)]
    for (i, (a, b)) in enumerate(gaps):
        (p, t, n, ang) = frame_at((a + b) / 2, 'North')
        p.z = 1.6
        box('Junction_Wall_' + str(i), p - n * 0.078 + n * 0.001, ((b - a) / t.x + 0.01, 0.16, 3.2), M['white'], ang)
    glass = bpy.data.objects['TH_Lockerward_Continuous_Glass']
    p = glass.location.copy()
    ang = glass.rotation_euler.z
    t = Vector((math.cos(ang), math.sin(ang), 0))
    n = Vector((math.sin(ang), -math.cos(ang), 0))
    for i in range(1, 6):
        u = -9.56 / 2 + 9.56 * i / 6
        box('Lockerward_Mullion_' + str(i), p + t * u + n * 0.025, (0.04, 0.075, 2.9), M['silver'], ang)

def build_north_cove():
    global C, M, MODULES, CUTTERS
    C = bpy.data.collections['Tepper_Hallway_Refinement']
    path = [Vector(p) for p in [(-39, 0.454239, 0), (-17.65, 1.292, 0), (-6.6, 1.95, 0), (-6.55, 2.45, 0), (-3.55, 3.3, 0), (-3.35, 2.6, 0)]]
    normals = []
    for (a, b) in zip(path, path[1:]):
        d = (b - a).normalized()
        normals.append(Vector((d.y, -d.x, 0)))

    def offset(distance):
        v = [path[0] + normals[0] * distance]
        for i in range(1, len(path) - 1):
            bis = (normals[i - 1] + normals[i]).normalized()
            v.append(path[i] + bis * (distance / bis.dot(normals[i])))
        return v + [path[-1] + normals[-1] * distance]

    def strip(name, inner, outer, z, height, mat):
        a = offset(inner)
        b = offset(outer)
        verts = []
        for (p, q) in zip(a, b):
            verts.extend([p + Vector((0, 0, z)), q + Vector((0, 0, z)), q + Vector((0, 0, z + height)), p + Vector((0, 0, z + height))])
        faces = [(3, 2, 1, 0)]
        for i in range(len(path) - 1):
            for j in range(4):
                faces.append((4 * i + j, 4 * i + (j + 1) % 4, 4 * (i + 1) + (j + 1) % 4, 4 * (i + 1) + j))
        n = 4 * (len(path) - 1)
        faces.append((n, n + 1, n + 2, n + 3))
        return pc.add_polydata(name, verts, faces, mat, C)
    profile = strip('TH_North_Continuous_Cove', 0.08, 0.165, 3.0725, 0.035, bpy.data.materials['Tepper_Warm_White_Wall'])
    strip('TH_North_Continuous_Cove_Emitter', 0.148, 0.165, 3.068, 0.006, bpy.data.materials['TH_Cove_Light'])
    centers = offset(0.195)
    for (i, (a, b)) in enumerate(zip(centers, centers[1:])):
        d = b - a
        count = math.ceil(d.length / 3)
        for j in range(count):
            p = a + d * ((j + 0.5) / count)
            p.z = 3.04
            o = area(f'Continuous_North_Wash_{i}_{j}', p, 42 * d.length / count / 3, d.length / count, 0.09)
            o.rotation_euler.z = math.atan2(d.y, d.x)

def build_headers(modules, left):
    global C, M, MODULES, CUTTERS
    modules = list(left) + [v for v in modules if v['side'] == 'South']
    C = bpy.data.collections['Tepper_Hallway_Refinement']
    mat = bpy.data.materials['Tepper_Warm_White_Wall']
    headers = []
    for v in modules:
        tag = v['tag']
        p = Vector(v['center'])
        n = Vector(v['inward_normal'])
        t = Vector(v['tangent'])
        a = math.atan2(t.y, t.x)
        bottom = 2.46 if tag.startswith('Recess_') else 2.56 if tag == 'Single_Room' else 2.98
        top = 3.22
        o = pc.add_box('TH_Header_' + tag, p - n * (0 if tag.startswith('Recess_') or tag == 'Single_Room' else 0.08) + Vector((0, 0, (bottom + top) / 2)), (v['width'] + 0.055, 0.16, top - bottom), mat, C, rot_z=a)
        headers.append({'object': o.name, 'center': v['center'], 'normal': v['inward_normal'], 'tangent': v['tangent'], 'width': v['width'], 'bottom': bottom, 'top': top})
    bpy.context.view_layer.update()

def main():
    modules = build_facades()
    add_curtains_and_lighting(modules)
    left = finish_glazing(modules)
    finish_junctions()
    build_north_cove()
    build_headers(modules, left)
