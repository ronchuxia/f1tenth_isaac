"""Final restaurant openings, lobby, doors and window walls."""
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT = Path('/Users/xiachu/Files/projects/f1tenth_isaac')
sys.path.insert(0, str(ROOT / 'scripts/build-blender-scene'))
from atrium_surfaces import box, material, surface_uv
from atrium_architecture import tube, FRONT, BACK, WALL
from scene_assets import get_collection, add_cylinder, simple_material
PREFIX = 'NSH_Detail_'
SERVICES = [(-12.0, 6.0), (-5.1, 6.4)]
SIDE_DOORS = [(0.45, 1.02), (4.7, 0.96), (6.15, 0.96)]

def block(name, loc, size, mat, col, wall=False, radius=0.003):
    o = box(PREFIX + name, loc, size, mat, col, radius)
    if wall:
        o['nsh_wall'] = True
    return o

def wall_grid(side, openings, col, brick):
    """Partition the wall around openings, so no solid wall crosses a pane."""
    zs = sorted(set([0, WALL] + [z for (_, _, a, b) in openings for z in (a, b)]))
    for (za, zb) in zip(zs, zs[1:]):
        intervals = sorted(((a, b) for (a, b, z0, z1) in openings if z0 < (za + zb) / 2 < z1))
        cursor = FRONT
        for (a, b) in intervals + [(BACK, BACK)]:
            if a > cursor:
                o = block('Side_Wall', (side * 6.13, (cursor + a) / 2, (za + zb) / 2), (0.28, a - cursor, zb - za), brick, col, True, 0.001)
                surface_uv(o, 1.04)
            cursor = b

def windows(col):
    brick = bpy.data.materials['Cream_Brick']
    frame = bpy.data.materials['NSH_Window_Frame']
    glass = bpy.data.materials['NSH_Window_Glass']
    sill = bpy.data.materials['NSH_Limestone']
    ys = [FRONT + 1.8 + 2.75 * i for i in range(12) if FRONT + 1.8 + 2.75 * i + 1.24 < BACK - 0.25]
    for side in (-1, 1):
        apertures = []
        for y in ys:
            for (za, zb) in ((0.72, 3.1), (6.73, 8.78)):
                if side == -1 and za < 1 and (y > -16):
                    continue
                (lo, hi) = (y - 0.84, y + 1.24)
                apertures.append((lo, hi, za, zb))
                pane = block('Window_Pane', (side * 6.065, (lo + hi) / 2, (za + zb) / 2), (0.018, hi - lo - 0.08, zb - za - 0.08), glass, col)
                pane['nsh_window_aperture'] = [side, lo, hi, za, zb]
                for yy in (lo + 0.035, (lo + hi) / 2, hi - 0.035):
                    block('Window_Mullion', (side * 6.005, yy, (za + zb) / 2), (0.18, 0.07, zb - za), frame, col)
                for z in (za + 0.04, za + 0.62, zb - 0.04):
                    block('Window_Transom', (side * 6.005, (lo + hi) / 2, z), (0.18, hi - lo, 0.075), frame, col)
                for z in (za, zb):
                    block('Window_Stone_Sill', (side * 5.91, (lo + hi) / 2, z), (0.35, hi - lo + 0.1, 0.075), sill, col, radius=0.004)
                for z in [za + 0.12 + 0.07 * i for i in range(int((zb - za - 0.2) / 0.07))]:
                    block('Blind', (side * 6.105, (lo + hi) / 2, z), (0.018, hi - lo - 0.1, 0.017), sill, col, radius=0.001)
        if side == -1:
            apertures += [(y - w / 2, y + w / 2, 0, 2.65) for (y, w) in SERVICES]
            apertures += [(y - w / 2, y + w / 2, 0, 2.32) for (y, w) in SIDE_DOORS]
        wall_grid(side, apertures, col, brick)
        for y in ys:
            panel = block('Soldier_Panel', (side * 5.983, y + 0.2, 4.65), (0.02, 1.96, 1.62), brick, col, radius=0.001)
            surface_uv(panel, 1.04, True)
            pier_y = y - 1.175
            bottom = 3.1 if side == -1 and any((abs(pier_y - c) < w / 2 + 0.16 for (c, w) in SERVICES + SIDE_DOORS)) else 0
            pier = block('Brick_Pilaster', (side * 5.94, pier_y, (WALL + bottom) / 2), (0.19, 0.27, WALL - bottom), brick, col, True, 0.001)
            surface_uv(pier, 1.04)

def area(name, loc, power, size, color, col):
    d = bpy.data.lights.new(PREFIX + name, 'AREA')
    d.energy = power
    d.shape = 'RECTANGLE'
    d.size = size
    d.size_y = 0.35
    d.color = color
    o = bpy.data.objects.new(d.name, d)
    o.location = loc
    col.objects.link(o)

def service_counters(col):
    cream = bpy.data.materials['NSH_Cream_Structure']
    stone = bpy.data.materials['NSH_Gray_Tile']
    metal = bpy.data.materials['Race2_Table_Steel']
    laminate = material('NSH_Counter_Laminate', base=(0.48, 0.33, 0.15), roughness=0.5)
    dark = material('NSH_Counter_Charcoal', base=(0.055, 0.062, 0.057), roughness=0.36)
    tile = material('NSH_Kitchen_Tile', base=(0.48, 0.47, 0.41), roughness=0.5)
    glass = bpy.data.materials['Race2_Clear_Glass']
    lamp = simple_material('NSH_Counter_Lamp', (0.75, 0.7, 0.56), roughness=0.4, emission=(1, 0.84, 0.61), emission_strength=2)
    lo = SERVICES[0][0] - SERVICES[0][1] / 2
    hi = SERVICES[-1][0] + SERVICES[-1][1] / 2
    cy = (lo + hi) / 2
    length = hi - lo
    block('Kitchen_Back', (-10.2, cy, 1.4), (0.15, length, 2.8), tile, col, True)
    for yy in (lo, hi):
        block('Kitchen_Return', (-8.1, yy, 1.4), (4.2, 0.12, 2.8), tile, col, True)
    floor = block('Kitchen_Floor', (-8.1, cy, 0.006), (4.2, length, 0.012), stone, col)
    surface_uv(floor, 2)
    block('Kitchen_Ceiling', (-8.1, cy, 2.76), (4.2, length, 0.16), cream, col, True)
    block('Back_Workbench', (-9.56, cy, 0.94), (0.64, length - 0.16, 0.06), metal, col)
    gap_lo = SERVICES[0][0] + SERVICES[0][1] / 2
    gap_hi = SERVICES[1][0] - SERVICES[1][1] / 2
    connector = block('Counter_Connection', (-7.97, (gap_lo + gap_hi) / 2, 0.947), (1.02, gap_hi - gap_lo + 0.12, 0.055), dark, col, radius=0.009)
    block('Counter_Connection_Base', (-8.04, (gap_lo + gap_hi) / 2, 0.5), (0.8, gap_hi - gap_lo + 0.12, 0.8), laminate, col)
    for (index, (y, w)) in enumerate(SERVICES):
        block('Hatch_Header', (-5.93, y, 2.88), (0.36, w + 0.1, 0.46), cream, col, True)
        for z in (2.56, 2.59, 2.62):
            block('Shutter_Slat', (-6.02, y, z), (0.04, w - 0.08, 0.025), metal, col)
        before = set(col.objects)
        block('Cabinet_Platform', (-6.34, y, 0.09), (0.8, w - 0.12, 0.18), dark, col)
        n = 6 if index == 0 else 5
        block('Counter_Base', (-6.34, y, 0.5), (0.8, w - 0.12, 0.8), laminate, col)
        block('Worktop', (-6.27, y, 0.947), (1.02, w - 0.04, 0.055), dark, col, radius=0.009)
        block('Worktop_Edge', (-5.755, y, 0.925), (0.035, w - 0.04, 0.075), metal, col, radius=0.005)
        for j in range(n - 1):
            cy = y - w / 2 + 0.55 + j * 0.65
            block('Food_Well', (-6.23, cy, 0.982), (0.43, 0.51, 0.045), metal, col)
            block('Food_Pan_Inside', (-6.23, cy, 1.008), (0.36, 0.43, 0.013), dark, col)
            for xx in (-6.44, -6.02):
                block('Pan_Rim', (xx, cy, 1.024), (0.024, 0.53, 0.025), metal, col)
            for yy in (cy - 0.255, cy + 0.255):
                block('Pan_Rim', (-6.23, yy, 1.024), (0.43, 0.024, 0.025), metal, col)
        for cy in (y - w / 2 + 0.18, y, y + w / 2 - 0.18):
            tube(PREFIX + 'Counter_Guard_Post', [(-6.0, cy, 1.0), (-6.0, cy, 1.39)], 0.014, metal, col)
        block('Counter_Guard', (-5.99, y, 1.3), (0.012, w - 0.25, 0.18), glass, col, radius=0.001)
        tube(PREFIX + 'Counter_Guard_Rail', [(-5.99, y - w / 2 + 0.12, 1.4), (-5.99, y + w / 2 - 0.12, 1.4)], 0.014, metal, col)
        for cy in (y - 0.7, y + 0.5):
            block('Kitchen_Appliance', (-7.52, cy, 1.2), (0.43, 0.55, 0.48), metal, col, radius=0.015)
            block('Appliance_Front', (-7.295, cy, 1.2), (0.012, 0.47, 0.32), dark, col)
            for yy in (cy - 0.16, cy + 0.16):
                add_cylinder(PREFIX + 'Appliance_Knob', (-7.27, yy, 1.34), 0.024, 0.022, dark, col, segments=16, rotation=(0, math.pi / 2, 0))
        for cy in (y + w / 2 - 0.35, y + w / 2 - 0.64):
            add_cylinder(PREFIX + 'Coffee_Urn', (-6.48, cy, 1.2), 0.11, 0.43, metal, col, segments=24)
            add_cylinder(PREFIX + 'Coffee_Lid', (-6.48, cy, 1.43), 0.12, 0.027, dark, col, segments=24)
            tube(PREFIX + 'Coffee_Spout', [(-6.35, cy, 1.1), (-6.27, cy, 1.1)], 0.013, dark, col)
        for obj in set(col.objects) - before:
            obj.location.x -= 1.7
        block('Under_Header_Lamp', (-6.25, y, 2.51), (0.08, w - 0.25, 0.045), lamp, col)
        area('Kitchen_Light', (-8.0, y, 2.5), 95, w - 0.3, (1, 0.87, 0.69), col)
    block('Tray_Return_Top', (-5.36, -1.5, 0.92), (0.6, 0.5, 0.055), dark, col)
    for x in (-5.61, -5.11):
        for y in (-1.69, -1.31):
            block('Tray_Return_Leg', (x, y, 0.46), (0.034, 0.034, 0.9), dark, col)
    block('Tray_Return_Shelf', (-5.36, -1.5, 0.14), (0.54, 0.44, 0.035), dark, col)

def side_doors(col):
    """The restaurant side has brick and doors, opposite the window wall."""
    frame = bpy.data.materials['NSH_Window_Frame']
    wood = bpy.data.materials['Door_Wood']
    metal = bpy.data.materials['Race2_Table_Steel']
    dark = bpy.data.materials['NSH_Counter_Charcoal']
    for (y, w) in SIDE_DOORS:
        door = block('Restaurant_Side_Door', (-6.17, y, 1.145), (0.055, w - 0.065, 2.29), wood, col, radius=0.004)
        surface_uv(door, 1.83)
        door['nsh_side_door'] = True
        for yy in (y - w / 2 + 0.016, y + w / 2 - 0.016):
            block('Side_Door_Jamb', (-6.025, yy, 1.16), (0.2, 0.065, 2.32), frame, col)
        block('Side_Door_Header', (-6.025, y, 2.32), (0.2, w + 0.035, 0.065), frame, col)
        block('Side_Door_Kickplate', (-6.138, y, 0.16), (0.009, w - 0.14, 0.23), metal, col)
        tube(PREFIX + 'Side_Door_Handle', [(-6.07, y + w * 0.3, 0.98), (-6.07, y + w * 0.3, 1.17)], 0.012, metal, col)
        block('Door_Plaque', (-5.975, y + w / 2 + 0.19, 1.48), (0.02, 0.14, 0.18), dark, col)
        block('Door_Plaque_Inset', (-5.961, y + w / 2 + 0.19, 1.48), (0.008, 0.095, 0.12), metal, col)

def lobby(col):
    cream = bpy.data.materials['NSH_Cream_Structure']
    wood = bpy.data.materials['Door_Wood']
    brick = bpy.data.materials['Cream_Brick']
    frame = bpy.data.materials['NSH_Window_Frame']
    stone = bpy.data.materials['NSH_Gray_Tile']
    metal = bpy.data.materials['Race2_Table_Steel']
    dark = bpy.data.materials['NSH_Counter_Charcoal']
    block('Lobby_Drop_Fascia', (0, 8.3, 5.34), (11.9, 0.1, 1.0), cream, col, True)
    block('Lobby_Left_Soffit', (-4.8, 7.83, 5.54), (2.4, 1.16, 0.6), cream, col, True)
    block('Fascia_Teal_Rim', (0, 7.482, 6.19), (11.9, 0.04, 0.16), bpy.data.materials['CMU_Teal'], col)
    o = block('Rear_Upper_Wall', (0, BACK + 0.15, (3.2 + WALL) / 2), (12.3, 0.3, WALL - 3.2), brick, col, True)
    surface_uv(o, 1.04)
    openings = [(-3.77, -2.73, 2.3), (-0.75, 1.05, 2.32), (2.7, 4.18, 2.65)]
    cursor = -6
    for (lo, hi, top) in openings + [(6, 6, 3.2)]:
        if lo > cursor:
            block('Lobby_Wall', ((cursor + lo) / 2, BACK + 0.1, 1.6), (lo - cursor, 0.3, 3.2), cream, col, True)
        if hi > lo:
            block('Lobby_Door_Head', ((lo + hi) / 2, BACK + 0.1, (top + 3.2) / 2), (hi - lo, 0.3, 3.2 - top), cream, col, True)
        cursor = hi
    for x in (-2.1, 2.22):
        block('Lobby_Pier', (x, BACK - 0.55, 1.575), (0.32, 1.02, 3.15), cream, col, True)
        block('Lobby_Pier_Base', (x, BACK - 0.55, 0.09), (0.34, 1.04, 0.18), dark, col)
    floor = block('Lobby_Floor', (0, (7.51 + BACK) / 2, 0.006), (11.9, BACK - 7.51, 0.012), stone, col)
    surface_uv(floor, 2)
    for (index, (lo, hi, top)) in enumerate(openings[:2]):
        c = (lo + hi) / 2
        for x in (lo, hi):
            block('Lobby_Jamb', (x, BACK + 0.08, top / 2), (0.065, 0.26, top), frame, col)
        block('Lobby_Transom', (c, BACK + 0.08, top), (hi - lo + 0.07, 0.26, 0.065), frame, col)
        count = 1 if index == 0 else 2
        width = (hi - lo - 0.07) / count
        for j in range(count):
            x = lo + 0.035 + width * (j + 0.5)
            door = block('Lobby_Door', (x, BACK + 0.2, (top - 0.055) / 2), (width - 0.008, 0.045, top - 0.055), wood, col, radius=0.004)
            surface_uv(door, 1.83, False)
            block('Lobby_Door_Kickplate', (x, BACK + 0.171, 0.16), (width - 0.08, 0.008, 0.23), metal, col)
            handle_x = x + width * 0.31 * (-1 if j else 1)
            tube(PREFIX + 'Lobby_Door_Handle', [(handle_x, BACK + 0.11, 0.95), (handle_x, BACK + 0.11, 1.18)], 0.011, metal, col)
            if index == 0:
                block('Lobby_Vision_Frame', (x, BACK + 0.165, 1.59), (0.28, 0.018, 0.31), frame, col)
                block('Lobby_Vision_Glass', (x, BACK + 0.15, 1.59), (0.23, 0.011, 0.26), dark, col)
    block('Passage_Back', (3.44, BACK + 2, 1.35), (1.5, 0.15, 2.7), cream, col, True)
    for x in (2.68, 4.2):
        block('Passage_Return', (x, BACK + 0.95, 1.35), (0.12, 2.1, 2.7), cream, col, True)
    block('Passage_Floor', (3.44, BACK + 0.95, 0.01), (1.5, 2.1, 0.02), stone, col)
    lamp = simple_material('NSH_Lobby_Sconce', (0.78, 0.7, 0.52), roughness=0.45, emission=(1, 0.75, 0.43), emission_strength=2)
    for x in (-4.15, -1.25, 1.75, 4.5):
        block('Sconce_Mount', (x, BACK - 0.1, 2.16), (0.15, 0.07, 0.4), frame, col)
        add_cylinder(PREFIX + 'Lobby_Sconce', (x, BACK - 0.16, 2.16), 0.056, 0.29, lamp, col, segments=24)
        data = bpy.data.lights.new(PREFIX + 'Sconce_Light', 'POINT')
        data.energy = 11
        data.color = (1, 0.76, 0.46)
        data.shadow_soft_size = 0.08
        o = bpy.data.objects.new(data.name, data)
        o.location = (x, BACK - 0.31, 2.16)
        col.objects.link(o)
    area('Lobby_Linear_Light', (0, BACK - 0.7, 3.1), 100, 2.5, (1, 0.86, 0.64), col)

def extended_atrium(col):
    import random
    from scene_assets import add_polydata
    floor = bpy.data.objects['Atrium_Carpet_Tiles']
    old_front = min(((floor.matrix_world @ Vector(v)).y for v in floor.bound_box))
    vertices = []
    faces = []
    ny = math.ceil((old_front - FRONT) / 0.75)
    nx = 16
    for j in range(ny):
        ya = FRONT + (old_front - FRONT) * j / ny
        yb = FRONT + (old_front - FRONT) * (j + 1) / ny
        for i in range(nx):
            xa = -6 + 12 * i / nx
            xb = xa + 12 / nx
            n = len(vertices)
            vertices.extend([(xa, ya, 0), (xb, ya, 0), (xb, yb, 0), (xa, yb, 0)])
            faces.append((n, n + 1, n + 2, n + 3))
    mats = [bpy.data.materials['Carpet_' + n] for n in ('Charcoal', 'Blue', 'Tan', 'Orange')]
    obj = add_polydata(PREFIX + 'Atrium_Extension_Floor', vertices, faces, mats[0], col)
    for m in mats[1:]:
        obj.data.materials.append(m)
    rng = random.Random(88)
    for face in obj.data.polygons:
        face.material_index = rng.choices(range(4), [0.66, 0.15, 0.13, 0.06])[0]
    surface_uv(obj, 0.75)
    steel = bpy.data.materials['Race2_Table_Steel']
    teal = bpy.data.materials['CMU_Teal']
    for (y, w) in SERVICES:
        block('Restaurant_Vent_Recess', (-5.975, y, 3.76), (0.025, w - 0.4, 0.22), teal, col)
        for z in (3.68, 3.72, 3.76, 3.8, 3.84):
            block('Restaurant_Vent_Slat', (-5.95, y, z), (0.04, w - 0.42, 0.012), steel, col)

def main():
    parent = bpy.data.collections['Race2_Video_Refinement_NSH']
    col = get_collection('Race2_Video_Refinement_Marked', parent)
    for o in bpy.data.collections['Race2_Video_Refinement_Furniture'].objects:
        if o.name.startswith(('Waste_Station_', 'Waste_Label_')):
            o.hide_render = False
            o.hide_set(False)
            if not o.get('nsh_waste_repositioned'):
                o.location.y += 1.75
                o['nsh_waste_repositioned'] = True
    windows(col)
    service_counters(col)
    side_doors(col)
    lobby(col)
    extended_atrium(col)
    for (name, loc, target, lens) in (('Race2_Service_Camera', (-1.8, 1.8, 1.9), (-6.15, -2.6, 1.35), 25), ('Race2_Lobby_Camera', (-1.25, 3.25, 4.4), (0.3, 11.2, 1.5), 24), ('Race2_Window_Camera', (3.5, 7.1, 1.8), (6.0, 7.1, 1.8), 20), ('Race2_Restaurant_Wall_Camera', (1.7, -1.8, 2.0), (-5.6, 2.5, 1.65), 23), ('Race2_Restaurant_Interior_Camera', (-6.7, -2.2, 1.8), (-8, -8, 1.4), 24), ('Race2_Upper_Walk_Camera', (-4.7, 5.9, 7.9), (-4.6, -8, 7.6), 22)):
        o = bpy.data.objects.get(name)
        if o is None:
            d = bpy.data.cameras.new(name)
            o = bpy.data.objects.new(name, d)
            col.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector(target) - o.location).to_track_quat('-Z', 'Y').to_euler()
        o.data.lens = lens
    bpy.context.view_layer.update()
