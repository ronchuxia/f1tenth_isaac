"""Atrium stairs, walkways, envelope and roof geometry."""
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
ROOT = Path('/Users/xiachu/Files/projects/f1tenth_isaac')
sys.path.insert(0, str(ROOT / 'scripts/build-blender-scene'))
from atrium_surfaces import box, material, image, normal_image, surface_uv
from scene_assets import add_polydata, add_cylinder, get_collection, simple_material
LANDING = 3.12
UPPER = 6.24
WALL = 10.6
FRONT = -21.0
BACK = 12.2
WALK_INNER = -3.6

def tube(name, points, radius, mat, col):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for (p, co) in zip(spline.points, points):
        p.co = (*co, 1)
    obj = bpy.data.objects.new(name, curve)
    col.objects.link(obj)
    curve.materials.append(mat)
    return obj

def slab(name, outline, top, depth, mat, col):
    n = len(outline)
    vertices = [(x, y, z) for z in (top - depth, top) for (x, y) in outline]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return add_polydata(name, vertices, faces, mat, col)

def rail(name, path, mat, col):
    points = [Vector(p) for p in path]
    for (h, r) in ((0.08, 0.022), (0.93, 0.021), (1.1, 0.03)):
        tube(name + '_Horizontal', [(p.x, p.y, p.z + h) for p in points], r, mat, col)
    distance = 0
    for (a, b) in zip(points, points[1:]):
        length = (b - a).length
        n = max(1, math.ceil(length / 0.12))
        for j in range(n):
            p = a.lerp(b, j / n)
            tube(name + '_Baluster', [(p.x, p.y, p.z + 0.09), (p.x, p.y, p.z + 0.94)], 0.009, mat, col)
        distance += length
    for p in points[::max(1, len(points) // 8)] + [points[-1]]:
        tube(name + '_Post', [(p.x, p.y, p.z), (p.x, p.y, p.z + 1.11)], 0.025, mat, col)
        box(name + '_Foot', (p.x, p.y, p.z + 0.014), (0.1, 0.1, 0.028), mat, col, 0.003)

def finishes():
    size = 1024
    rng = np.random.default_rng(67)
    (y, x) = np.mgrid[:size, :size] / size
    row = np.floor(y * 16).astype(int)
    bx = x * 4 + row % 2 * 0.5
    joint = (y * 16 % 1 < 0.055) | (bx % 1 < 0.025)
    shades = rng.uniform(0.94, 1.055, (16, 6))
    variation = shades[row, np.floor(bx).astype(int)]
    grain = rng.normal(0, 0.005, (size, size))
    rgb = np.array((0.67, 0.59, 0.43)) * variation[:, :, None] + grain[:, :, None]
    rgb[joint] = (0.39, 0.37, 0.31)
    normal = normal_image('nsh_brick_normal', -joint.astype(float) * 0.15 + grain * 0.2, 0.9)
    brick = material('Cream_Brick', image('nsh_buff_brick', rgb), normal=normal, roughness=0.78)
    noise = rng.normal(0, 0.012, (size, size))
    tile_joint = (x % 0.25 < 0.002) | (y % 0.25 < 0.002)
    tile = np.repeat((0.43 + noise)[:, :, None], 3, 2) * np.array((0.99, 1, 1.02))
    tile[tile_joint] = (0.25, 0.26, 0.26)
    stone = material('NSH_Gray_Tile', image('nsh_gray_tile', tile), normal=normal_image('nsh_tile_normal', noise * 0.05 - tile_joint * 0.15, 1), roughness=0.57)
    cream = material('NSH_Cream_Structure', base=(0.72, 0.7, 0.62), roughness=0.69)
    teal = material('CMU_Teal', base=(0.04, 0.13, 0.12), roughness=0.43, metallic=0.18)
    tread = material('NSH_Step_Stone', image('nsh_step_stone', np.repeat((0.38 + noise)[:, :, None], 3, 2)), normal=normal_image('nsh_step_normal', noise, 0.3), roughness=0.63)
    return (brick, stone, cream, teal, tread)

def stairs(col, stone, cream, teal, tread):
    front = [(x, 0.1 + 0.57 * (x / 2) ** 2) for x in np.linspace(-2, 2, 65)]
    outline = front + [(2, 3.45), (-2, 3.45)]
    landing = slab('NSH_Intermediate_Landing', outline, LANDING, 0.18, cream, col)
    cap = slab('NSH_Landing_Tiles', outline, LANDING + 0.014, 0.014, stone, col)
    surface_uv(cap, 2)
    perimeter = [(-1.95, 3.45), (-2, 3.45)] + list(front) + [(2, 3.45), (1.95, 3.45)]
    rail('NSH_Landing_Perimeter', [(x, y, LANDING + 0.02) for (x, y) in perimeter], teal, col)
    rail('NSH_Landing_Center', [(-0.39, 3.45, LANDING + 0.02), (0.39, 3.45, LANDING + 0.02)], teal, col)
    for (a, b) in zip(front, front[1:]):
        slab('NSH_Landing_Rim', [a, b, (b[0], b[1] + 0.05), (a[0], a[1] + 0.05)], LANDING + 0.12, 0.15, teal, col)
    for upper in (False, True):
        count = 18
        edges = []
        for i in range(count + 1):
            t = i / count
            y = 3.45 + 4.05 * t
            x = (1.17 - 0.78 * t * t) * (1 if upper else -1)
            z = LANDING + (LANDING * t if upper else -LANDING * t)
            edges.append((x, y, z))
        for (i, (a, b)) in enumerate(zip(edges, edges[1:])):
            top = b[2] if upper else a[2]
            (xa, ya, _) = a
            (xb, yb, _) = b
            outline = [(xa - 0.76, ya), (xa + 0.76, ya), (xb + 0.76, yb), (xb - 0.76, yb)]
            step = slab('NSH_Upper_Step' if upper else 'NSH_Lower_Step', outline, top, LANDING / count, tread, col)
            surface_uv(step, 1)
            yn = ya + 0.012 if upper else yb - 0.06
            nose = box('NSH_Nosing', ((xa + xb) / 2, yn, top + 0.002), (1.47, 0.052, 0.009), stone, col, 0.002)
            for dy in (0.009, 0.026, 0.043):
                box('NSH_Nosing_Groove', ((xa + xb) / 2, yn - 0.026 + dy, top + 0.007), (1.42, 0.003, 0.002), teal, col, 0.0004)
        for side in (-1, 1):
            path = [(x + side * 0.78, y, z + 0.02) for (x, y, z) in edges]
            rail('NSH_Upper_Rail' if upper else 'NSH_Lower_Rail', path, teal, col)
            vertices = []
            for (x, y, z) in edges:
                vertices.extend([(x + side * 0.78, y, z - 0.02), (x + side * 0.78, y, z - 0.3)])
            stringer = add_polydata('NSH_Stair_Stringer', vertices, [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(count)], teal, col)
            mod = stringer.modifiers.new('Plate thickness', 'SOLIDIFY')
            mod.thickness = 0.035
    rear = box('NSH_Upper_Floor', (0, (7.5 + BACK) / 2, UPPER - 0.2), (12, BACK - 7.5, 0.4), cream, col, 0.006)
    cap = box('NSH_Upper_Floor_Tile', (0, (7.5 + BACK) / 2, UPPER + 0.01), (12, BACK - 7.5, 0.02), stone, col, 0.002)
    surface_uv(cap, 2)
    rail('NSH_Connected_Upper_Edge', [(-0.39, 7.5, UPPER + 0.02), (WALK_INNER, 7.5, UPPER + 0.02), (WALK_INNER, FRONT + 2.2, UPPER + 0.02), (6, FRONT + 2.2, UPPER + 0.02)], teal, col)
    rail('NSH_Upper_Rear_Right', [(1.17, 7.5, UPPER + 0.02), (6, 7.5, UPPER + 0.02)], teal, col)
    bpy.context.scene['nsh_landing_height_m'] = LANDING
    bpy.context.scene['nsh_upper_floor_height_m'] = UPPER
    bpy.context.scene['nsh_landing_back_y_m'] = 3.45

def envelope(col, brick, stone, cream, teal):
    frame = material('NSH_Window_Frame', base=(0.17, 0.24, 0.23), metallic=0.5, roughness=0.32)
    glass = material('NSH_Window_Glass', base=(0.075, 0.115, 0.13), metallic=0.32, roughness=0.18)
    sill = material('NSH_Limestone', base=(0.62, 0.61, 0.54), roughness=0.72)
    wood = bpy.data.materials['Door_Wood']
    box('NSH_Hall_Ceiling', (0, (7.5 + BACK) / 2, WALL - 0.09), (12, BACK - 7.5, 0.18), cream, col, 0.004)
    for x in (-4, 0, 4):
        door = box('NSH_Upper_Door', (x, BACK - 0.18, UPPER + 1.12), (1.6, 0.055, 2.24), wood, col, 0.006)
        surface_uv(door, 1.83, False)
    for x in (-4, 0, 4):
        for xx in (x - 0.84, x + 0.84):
            box('NSH_Upper_Door_Jamb', (xx, BACK - 0.25, UPPER + 1.15), (0.075, 0.13, 2.3), frame, col, 0.003)
        box('NSH_Upper_Door_Header', (x, BACK - 0.25, UPPER + 2.31), (1.76, 0.13, 0.075), frame, col, 0.003)
        tube('NSH_Upper_Door_Handle', [(x + 0.6, BACK - 0.3, UPPER + 0.9), (x + 0.6, BACK - 0.3, UPPER + 1.25)], 0.012, frame, col)
    for x in (-3.3, 3.3):
        box('NSH_Hall_Column', (x, BACK - 0.3, (UPPER + WALL) / 2), (0.34, 0.4, WALL - UPPER), cream, col, 0.008)
    box('NSH_Wall_Passage', ((-6 + WALK_INNER) / 2, (FRONT + 7.5) / 2, UPPER - 0.2), (6 + WALK_INNER, 7.5 - FRONT, 0.4), cream, col, 0.008)
    cap = box('NSH_Wall_Passage_Tile', ((-6 + WALK_INNER) / 2, (FRONT + 7.5) / 2, UPPER + 0.01), (6 + WALK_INNER, 7.5 - FRONT, 0.02), stone, col, 0.002)
    surface_uv(cap, 2)
    box('NSH_End_Passage', (0, FRONT + 1.1, UPPER - 0.2), (12, 2.2, 0.4), cream, col, 0.008)
    cap = box('NSH_End_Passage_Tile', (0, FRONT + 1.1, UPPER + 0.01), (12, 2.2, 0.02), stone, col, 0.002)
    surface_uv(cap, 2)
    for y in (-17.3, -10.7, -4.0, 3.6):
        add_cylinder('NSH_Wall_Column', (-5.45, y, UPPER / 2), 0.1, UPPER, teal, col, segments=32)
    clear = bpy.data.materials['Race2_Clear_Glass']
    box('NSH_End_Glass', (0, FRONT - 0.13, WALL / 2), (12, 0.024, WALL), clear, col, 0.001)
    for x in np.arange(-5.8, 5.9, 1.45):
        box('NSH_End_Mullion', (x, FRONT - 0.06, WALL / 2), (0.08, 0.12, WALL), frame, col, 0.003)
    for z in (0.1, 1.0, 3.0, 4.9, 6.3, 8.0, 9.17):
        box('NSH_End_Transom', (0, FRONT - 0.06, z), (12, 0.12, 0.085), frame, col, 0.003)

def ceiling(col, cream, teal):
    maroon = bpy.data.materials['Maroon_Steel']
    metal = bpy.data.materials['Race2_Table_Steel']
    glass = bpy.data.materials['Race2_Clear_Glass']

    def roof(x):
        return WALL + 1.15 * (1 - (x / 2.8) ** 2)
    for side in (-1, 1):
        box('NSH_Ceiling_Deck', (side * 4.4, (FRONT + BACK) / 2, WALL + 0.08), (3.2, BACK - FRONT, 0.16), cream, col, 0.003)
        for x in np.arange(2.86, 6, 0.16):
            box('NSH_Deck_Seam', (side * x, (FRONT + BACK) / 2, WALL - 0.013), (0.025, BACK - FRONT, 0.025), cream, col, 0.002)
        box('NSH_White_Roof_Fascia', (side * 2.8, (FRONT + BACK) / 2, WALL - 0.38), (0.15, BACK - FRONT, 0.76), cream, col, 0.005)
        for y in np.arange(FRONT + 0.7, BACK, 2.6):
            for z in (WALL - 0.16, WALL - 0.46):
                box('NSH_Beam_Flange', (side * 4.4, y, z), (3.2, 0.22, 0.045), maroon, col, 0.003)
            box('NSH_Beam_Web', (side * 4.4, y, WALL - 0.31), (3.2, 0.065, 0.29), maroon, col, 0.003)
            triangle = [(side * 5.94, y - 0.13, WALL - 0.5), (side * 5.25, y - 0.13, WALL - 0.5), (side * 5.94, y - 0.13, WALL - 1.05)]
            obj = add_polydata('NSH_Corbel', triangle, [(0, 1, 2)], teal, col)
            mod = obj.modifiers.new('Steel width', 'SOLIDIFY')
            mod.thickness = 0.26
            add_cylinder('NSH_Beam_Bolt', (side * 5.71, y - 0.15, WALL - 0.61), 0.018, 0.035, metal, col, segments=12, rotation=(math.pi / 2, 0, 0))
    xs = np.linspace(-2.8, 2.8, 49)
    verts = [(x, y, roof(x)) for x in xs for y in (FRONT - 0.15, BACK + 0.15)]
    add_polydata('NSH_Vault_Glass', verts, [(i * 2, i * 2 + 1, i * 2 + 3, i * 2 + 2) for i in range(48)], glass, col, smooth=True)
    for y in np.arange(FRONT + 0.2, BACK, 1.3):
        tube('NSH_Glazing_Arc', [(x, y, roof(x) - 0.03) for x in xs], 0.026, metal, col)
    for y in np.arange(FRONT + 0.7, BACK, 2.6):
        vertices = []
        for x in xs:
            vertices += [(x, y - 0.055, roof(x) - 0.1), (x, y + 0.055, roof(x) - 0.1), (x, y + 0.055, roof(x) - 0.34), (x, y - 0.055, roof(x) - 0.34)]
        add_polydata('NSH_Curved_Roof_Rib', vertices, [(4 * i + j, 4 * (i + 1) + j, 4 * (i + 1) + (j + 1) % 4, 4 * i + (j + 1) % 4) for i in range(48) for j in range(4)], teal, col)
    for x in np.linspace(-2.7, 2.7, 7):
        box('NSH_Glazing_Long', (x, (FRONT + BACK) / 2, roof(x) - 0.025), (0.038, BACK - FRONT, 0.05), metal, col, 0.002)
    for (y, mat) in ((BACK, cream), (FRONT - 0.13, glass)):
        add_polydata('NSH_Roof_End', [(x, y, roof(x)) for x in xs], [tuple(range(len(xs)))], mat, col)
    shade = simple_material('NSH_Pendant_Diffuser', (0.7, 0.72, 0.7), roughness=0.6, emission=(1, 0.91, 0.77), emission_strength=0.3)
    for x in (-4.2, 4.2):
        for y in np.arange(FRONT + 2, BACK - 1, 4.1):
            tube('NSH_Pendant_Cable', [(x, y, WALL - 0.58), (x, y, WALL - 0.48)], 0.007, metal, col)
            add_cylinder('NSH_Pendant_Shade', (x, y, WALL - 0.83), 0.17, 0.5, shade, col, segments=40, caps=False)
            add_cylinder('NSH_Pendant_Top', (x, y, WALL - 0.57), 0.175, 0.025, metal, col, segments=32)
            add_cylinder('NSH_Pendant_Lens', (x, y, WALL - 1.08), 0.16, 0.01, shade, col, segments=32)
            data = bpy.data.lights.new('NSH_Pendant_Light', 'AREA')
            data.energy = 75
            data.shape = 'DISK'
            data.size = 0.3
            data.color = (1, 0.9, 0.76)
            obj = bpy.data.objects.new(data.name, data)
            obj.location = (x, y, WALL - 1.1)
            col.objects.link(obj)
    for y in (-17, -10, -3, 4, 10):
        data = bpy.data.lights.new('NSH_Skylight', 'AREA')
        data.energy = 1500
        data.shape = 'RECTANGLE'
        data.size = 5
        data.size_y = 6
        data.color = (0.9, 0.95, 1)
        obj = bpy.data.objects.new(data.name, data)
        obj.location = (0, y, WALL + 0.4)
        col.objects.link(obj)
    for y in (-7, -2, 3):
        for yy in (y - 0.75, y + 0.75):
            tube('NSH_Linear_Suspension', [(-4.9, yy, 3.5), (-4.9, yy, 5.9)], 0.004, metal, col)
        box('NSH_Linear_Lamp', (-4.9, y, 3.5), (0.055, 1.6, 0.06), shade, col, 0.014)
    for (x, y, z) in ((0, 2.2, 2.9), (0, 8.6, 6.0)):
        data = bpy.data.lights.new('NSH_Entry_Light', 'AREA')
        data.energy = 180
        data.size = 2
        data.color = (1, 0.88, 0.72)
        obj = bpy.data.objects.new(data.name, data)
        obj.location = (x, y, z)
        col.objects.link(obj)

def main():
    col = get_collection('Race2_Video_Refinement_NSH', bpy.data.collections['Race2_Video_Refinement'])
    (brick, stone, cream, teal, tread) = finishes()
    stairs(col, stone, cream, teal, tread)
    envelope(col, brick, stone, cream, teal)
    ceiling(col, cream, teal)
    for o in bpy.data.objects:
        if o.name.startswith('Pillar_Door_') and o.name[-1] in '1' and (o.type == 'MESH'):
            surface_uv(o, 1.83, False)
    scene = bpy.context.scene
    for (name, loc, target, lens) in (('Race2_Hero_Camera', (5, -8.4, 3.8), (0, 2.5, 3.8), 22), ('Race2_NSH_Stair_Camera', (-3.3, 0.7, 4.9), (0, 5.7, 4.7), 23), ('Race2_NSH_Atrium_Camera', (1.5, 0.65, 4.85), (-0.5, -11, 3.2), 20)):
        obj = bpy.data.objects.get(name)
        if obj is None:
            data = bpy.data.cameras.new(name)
            obj = bpy.data.objects.new(name, data)
            col.objects.link(obj)
        obj.location = loc
        obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()
        obj.data.lens = lens
    scene.view_settings.exposure = 0.3
    scene.camera = bpy.data.objects['Race2_Hero_Camera']
    from atrium_interior import main as refine_marked
    refine_marked()
    bpy.context.view_layer.update()
