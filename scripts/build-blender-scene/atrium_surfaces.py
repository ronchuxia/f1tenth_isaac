"""Atrium materials, duct surfaces, furniture details and lighting."""
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
ROOT = Path('/Users/xiachu/Files/projects/f1tenth_isaac')
sys.path.insert(0, str(ROOT / 'scripts/build-blender-scene'))
from scene_assets import add_box, add_cylinder, add_polydata, box_uv, get_collection, reset_material
from scene_assets import GENERATED_TEXTURES
OUT = Path(GENERATED_TEXTURES.name) / 'atrium_surfaces'
NAME = 'Race2_Video_Refinement'

def scanned(asset, suffix, size=1024):
    path = ROOT / f'blender/assets/polyhaven/textures/{asset}/{asset}_{suffix}_2k.jpg'
    im = bpy.data.images.load(str(path), check_existing=False)
    im.colorspace_settings.name = 'sRGB' if suffix == 'diff' else 'Non-Color'
    im.scale(size, size)
    pixels = np.empty(size * size * 4, dtype=np.float32)
    im.pixels.foreach_get(pixels)
    bpy.data.images.remove(im)
    return pixels.reshape(size, size, 4)[:, :, :3].copy()

def image(name, rgb, data=False):
    (h, w) = rgb.shape[:2]
    im = bpy.data.images.get(name) or bpy.data.images.new(name, w, h)
    im.scale(w, h)
    im.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(rgb, 0, 1)
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = str(OUT / (name + '.png'))
    im.file_format = 'PNG'
    im.save()
    return im

def normal_image(name, height, strength):
    (dy, dx) = np.gradient(height)
    xyz = np.stack((-dx * strength, -dy * strength, np.ones_like(dx)), axis=2)
    xyz /= np.linalg.norm(xyz, axis=2, keepdims=True)
    return image(name, xyz * 0.5 + 0.5, True)

def material(name, color=None, rough=None, normal=None, base=(0.3, 0.3, 0.3), roughness=0.6, metallic=0, uv='st'):
    (mat, tree, shader) = reset_material(name)
    shader.inputs['Base Color'].default_value = (*base, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    coords = tree.nodes.new('ShaderNodeUVMap')
    coords.uv_map = uv
    for (im, socket) in ((color, 'Base Color'), (rough, 'Roughness'), (normal, 'Normal')):
        if im is None:
            continue
        tex = tree.nodes.new('ShaderNodeTexImage')
        tex.image = im
        tree.links.new(coords.outputs['UV'], tex.inputs['Vector'])
        output = tex.outputs['Color']
        if socket == 'Normal':
            n = tree.nodes.new('ShaderNodeNormalMap')
            n.uv_map = uv
            tree.links.new(output, n.inputs['Color'])
            output = n.outputs['Normal']
        tree.links.new(output, shader.inputs[socket])
    return mat

def surface_uv(obj, size, rotate=False):
    box_uv(obj, 'st')
    for item in obj.data.uv_layers['st'].data:
        (u, v) = item.uv
        item.uv = ((-v if rotate else u) / size, (u if rotate else v) / size)

def surfaces():
    rng = np.random.default_rng(22)
    size = 1024
    (y, x) = np.mgrid[0:size, 0:size] / size
    scan = scanned('dirty_carpet', 'diff').mean(axis=2)
    scan /= scan.mean()
    strands = rng.uniform(0.74, 1.25, size)[None, :]
    weave = 1 + 0.055 * np.sin(y * math.tau * 350)
    tone = (0.65 + 0.35 * scan) * strands * weave
    tone *= 1 - 0.1 * np.cos(x * math.tau * 17) ** 14
    normal = normal_image('race2_carpet_normal', tone, 2.8)
    rough = image('race2_carpet_rough', np.repeat((0.84 + 0.04 * scan)[:, :, None], 3, 2), True)
    tints = {'Carpet_Charcoal': (0.19, 0.175, 0.16), 'Carpet_Blue': (0.2, 0.37, 0.43), 'Carpet_Tan': (0.46, 0.38, 0.28), 'Carpet_Orange': (0.55, 0.3, 0.16)}
    for (name, tint) in tints.items():
        diffuse = image('race2_' + name.lower(), tone[:, :, None] * tint)
        material(name, diffuse, rough, normal)
    floor = bpy.data.objects['Atrium_Carpet_Tiles']
    layer = floor.data.uv_layers.get('st') or floor.data.uv_layers.new(name='st')
    floor.data.uv_layers.active = layer
    layer.active_render = True
    for poly in floor.data.polygons:
        points = [floor.data.vertices[floor.data.loops[i].vertex_index].co for i in poly.loop_indices]
        (ox, oy) = (min((p.x for p in points)), min((p.y for p in points)))
        turn = int(round(ox) + round(oy)) % 2
        for (idx, p) in zip(poly.loop_indices, points):
            (u, v) = (p.x - ox, p.y - oy)
            layer.data[idx].uv = (v, u) if turn else (u, v)
    course = y * 16
    brick_x = (x * 4 + np.floor(course) % 2 * 0.5) % 1
    mortar = ((course % 1 < 0.065) | (brick_x < 0.022)).astype(float)
    noise = rng.normal(0, 0.004, (size, size))
    color = np.zeros((size, size, 3)) + (0.62, 0.49, 0.29)
    color += noise[:, :, None]
    color = color * (1 - mortar[:, :, None]) + mortar[:, :, None] * (0.31, 0.29, 0.23)
    brick = image('race2_buff_brick_color', color)
    brick_normal = normal_image('race2_buff_brick_normal', -mortar + noise, 1.0)
    material('Cream_Brick', brick, normal=brick_normal, roughness=0.77)
    plaster = scanned('white_plaster_02', 'diff')
    plaster = 0.93 * np.array((0.66, 0.59, 0.46)) + 0.07 * plaster
    column_mat = material('Race2_Painted_Column', image('race2_column_paint', plaster), roughness=0.68)
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        names = [m.name for m in obj.data.materials if m]
        if 'Cream_Brick' in names:
            surface_uv(obj, 1.04)
        if obj.name.startswith('Atrium_Column_'):
            obj.data.materials.clear()
            obj.data.materials.append(column_mat)
            surface_uv(obj, 1.0)
    for (name, asset, tile, gain) in (('Door_Wood', 'oak_veneer_01', 1.83, (1.12, 0.92, 0.65)), ('White_Plaster', 'white_plaster_02', 1.0, (1, 1, 0.96))):
        diff = image('race2_' + name + '_color', scanned(asset, 'diff') * gain)
        normal = image('race2_' + name + '_normal', scanned(asset, 'nor_gl') * 0.25 + np.array((0.5, 0.5, 1)) * 0.75, True)
        material(name, diff, normal=normal, roughness=0.65)
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and any((m and m.name == name for m in obj.data.materials)):
                surface_uv(obj, tile, name == 'Door_Wood')
    material('CMU_Teal', base=(0.1, 0.28, 0.25), roughness=0.42, metallic=0.18)
    material('Dark_Metal', base=(0.09, 0.1, 0.1), roughness=0.36, metallic=0.6)
    material('Maroon_Steel', base=(0.26, 0.055, 0.045), roughness=0.43, metallic=0.15)

def duct_fabric_images(name, distances, yellow):
    """Generate final fabric color and normal pixels for direct texture export."""
    OUT.mkdir(parents=True, exist_ok=True)
    length = distances[-1]
    pitch = 0.06 if yellow else 0.033
    (width, height) = (4096, 512) if length > 8 else (2048, 512)
    (v, u) = np.mgrid[0:height, 0:width] / np.array([height, width])[:, None, None]
    along = np.interp(u, np.linspace(0, 1, len(distances)), distances)
    phase = along / pitch + 0.08 * np.sin(v * math.tau * 5 + along * 4)
    folds = np.cos(math.tau * phase)
    fine = np.sin(v * math.tau * 63 + along * 21) * 0.045
    shade = 0.9 + 0.08 * folds + fine
    base = np.array((0.9, 0.76, 0.004) if yellow else (0.012, 0.013, 0.014))
    diff = image(name + '_fabric_color', shade[:, :, None] * base)
    normal = normal_image(name + '_fabric_normal', folds + fine, 0.6 if yellow else 0.5)
    return diff, normal


def ducts(collection):
    wire = material('Race2_Duct_Wire', base=(0.013, 0.012, 0.01), roughness=0.36, metallic=0.18)
    ring_count = 0
    for obj in bpy.data.collections['Race2_Track'].objects:
        if obj.name.endswith('_Ribs'):
            obj.hide_render = True
            obj.hide_set(True)
        if obj.type != 'CURVE':
            continue
        points = np.array([list(p.co)[:3] for p in obj.data.splines[0].points])
        distances = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
        length = distances[-1]
        yellow = obj.name.startswith('Yellow')
        pitch = 0.06 if yellow else 0.033
        diff, normal = duct_fabric_images(obj.name, distances, yellow)
        mat = material(obj.name + '_Video_Fabric', diff, normal=normal, roughness=0.4 if yellow else 0.34, uv='UVMap')
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        obj.hide_render = True
        obj.hide_set(True)
        (shell_vertices, shell_faces, shell_uv) = ([], [], [])
        samples = np.linspace(0, length, math.ceil(length / 0.012) + 1)
        for d in samples:
            i = min(np.searchsorted(distances, d, side='right') - 1, len(points) - 2)
            t = (d - distances[i]) / (distances[i + 1] - distances[i])
            center = Vector(points[i] * (1 - t) + points[i + 1] * t)
            tangent = Vector(points[i + 1] - points[i]).normalized()
            lateral = tangent.cross(Vector((0, 0, 1))).normalized()
            for a in range(40):
                angle = a * math.tau / 40
                phase = d / pitch + 0.08 * math.sin(angle * 5 + d * 4)
                crease = (0.5 - 0.5 * math.cos(math.tau * phase)) ** 0.7
                depth = (0.012 if yellow else 0.003) * crease
                depth += (0.002 if yellow else 0.0008) * (1 + math.sin(angle * 9 + d * 37))
                radial = Vector((0, 0, 1)) * math.cos(angle) + lateral * math.sin(angle)
                shell_vertices.append(center + radial * (obj.data.bevel_depth - depth))
                shell_uv.append(((i + t) / (len(points) - 1), a / 40))
        for row in range(len(samples) - 1):
            for a in range(40):
                shell_faces.append((row * 40 + a, (row + 1) * 40 + a, (row + 1) * 40 + (a + 1) % 40, row * 40 + (a + 1) % 40))
        sleeve = add_polydata(obj.name + '_Video_Sleeve', shell_vertices, shell_faces, mat, collection, smooth=True, uv=False)
        sleeve.matrix_world = obj.matrix_world.copy()
        uv_layer = sleeve.data.uv_layers.new(name='UVMap')
        for poly in sleeve.data.polygons:
            seam = any((sleeve.data.loops[k].vertex_index % 40 == 39 for k in poly.loop_indices))
            for k in poly.loop_indices:
                index = sleeve.data.loops[k].vertex_index
                (u, v) = shell_uv[index]
                uv_layer.data[k].uv = (u, 1.0 if seam and index % 40 == 0 else v)
        (vertices, faces) = ([], [])
        for d in np.arange(0.01, length, pitch):
            i = min(np.searchsorted(distances, d, side='right') - 1, len(points) - 2)
            t = (d - distances[i]) / (distances[i + 1] - distances[i])
            center = Vector(points[i] * (1 - t) + points[i + 1] * t)
            tangent = Vector(points[i + 1] - points[i]).normalized()
            vertical = Vector((0, 0, 1))
            lateral = tangent.cross(vertical).normalized()
            wire_radius = 0.0028 if yellow else 0.0016
            radius = obj.data.bevel_depth + 0.001
            start = len(vertices)
            for a in range(40):
                radial = vertical * math.cos(a * math.tau / 40) + lateral * math.sin(a * math.tau / 40)
                for b in range(6):
                    p = center + radial * (radius + wire_radius * math.cos(b * math.tau / 6)) + tangent * wire_radius * math.sin(b * math.tau / 6)
                    vertices.append(p)
            for a in range(40):
                for b in range(6):
                    faces.append(tuple((start + aa * 6 + bb for (aa, bb) in ((a, b), ((a + 1) % 40, b), ((a + 1) % 40, (b + 1) % 6), (a, (b + 1) % 6)))))
            ring_count += 1
        detail = add_polydata(obj.name + '_Fine_Ribs', vertices, faces, wire, collection, smooth=True, uv=False)
        detail.matrix_world = obj.matrix_world.copy()
    return ring_count

def box(name, center, dimensions, mat, collection, radius=0.008, rotation=0):
    obj = add_box(name, center, dimensions, mat, collection, rot_z=rotation)
    bevel = obj.modifiers.new('Manufactured edge', 'BEVEL')
    (bevel.width, bevel.segments) = (radius, 3)
    return obj

def furniture(collection):
    white = material('Race2_Table_Laminate', base=(0.73, 0.71, 0.66), roughness=0.48)
    metal = material('Race2_Table_Steel', base=(0.32, 0.34, 0.35), roughness=0.3, metallic=1)
    dark = material('Race2_Equipment_Plastic', base=(0.015, 0.018, 0.022), roughness=0.42)
    screen = material('Race2_Laptop_Display', base=(0.018, 0.035, 0.049), roughness=0.26)
    for (index, y) in enumerate((-4.8, -2.3, 0.2, 2.7)):
        box(f'Race_Table_{index}', (5.15, y, 0.745), (1.25, 1.65, 0.05), white, collection, 0.025)
        for x in (4.68, 5.62):
            for yy in (y - 0.64, y + 0.64):
                add_cylinder(f'Race_Table_{index}_Leg', (x, yy, 0.36), 0.021, 0.72, metal, collection, segments=16)
                add_cylinder(f'Race_Table_{index}_Foot', (x, yy, 0.022), 0.027, 0.044, dark, collection, segments=16)
        box(f'Laptop_{index}_Base', (5.04, y, 0.79), (0.34, 0.24, 0.019), dark, collection, 0.005)
        panel = box(f'Laptop_{index}_Lid', (5.04, y + 0.13, 0.905), (0.34, 0.016, 0.23), dark, collection, 0.005)
        panel.rotation_euler.x = math.radians(-12)
        display = box(f'Laptop_{index}_Screen', (5.04, y + 0.113, 0.905), (0.309, 0.002, 0.192), screen, collection, 0.002)
        display.rotation_euler.x = panel.rotation_euler.x
        for row in range(5):
            for col in range(11):
                box(f'Laptop_{index}_Key_{row}_{col}', (4.909 + col * 0.025, y - 0.071 + row * 0.023, 0.802), (0.019, 0.016, 0.002), metal, collection, 0.001)
        box(f'Equipment_Case_{index}', (5.33, y - 0.45, 0.847), (0.39, 0.26, 0.15), dark, collection, 0.016)
        box(f'Equipment_Case_{index}_Handle', (5.33, y - 0.586, 0.847), (0.14, 0.022, 0.035), metal, collection, 0.005)
    chair_source = bpy.data.materials['SchoolChair_01']
    for (index, color) in enumerate(((0.45, 0.025, 0.02), (0.6, 0.58, 0.53))):
        mat = material('Race2_Chair_' + str(index), base=color, roughness=0.48)
        for root in [o for o in bpy.data.objects if o.type == 'EMPTY' and o.name.startswith(f'Cafe_Chair_0{index}')]:
            for obj in root.children_recursive:
                if obj.type == 'MESH':
                    obj.data = obj.data.copy()
                    for slot in obj.material_slots:
                        if slot.material == chair_source:
                            slot.material = mat

def architecture(collection):
    wood = bpy.data.materials['Door_Wood']
    steel = bpy.data.materials['Race2_Table_Steel']
    trim = material('Race2_Door_Trim', base=(0.28, 0.25, 0.2), roughness=0.5)
    for side in (-1, 1):
        source = bpy.data.objects['Atrium_Column_+1.45' if side > 0 else 'Atrium_Column_-1.45']
        source.hide_render = True
        source.hide_set(True)
        visual = source.copy()
        visual.data = source.data.copy()
        visual.name = f'Pillar_Visual_{side}'
        collection.objects.link(visual)
        visual.hide_render = False
        visual.hide_set(False)
        cutter = add_box(f'Pillar_Door_Recess_{side}', (side * 0.9, 2.24, 1.16), (0.13, 1.18, 2.3), None, collection, uv=False)
        cutter.hide_render = True
        cutter.hide_set(True)
        boolean = visual.modifiers.new('Inset door opening', 'BOOLEAN')
        boolean.operation = 'DIFFERENCE'
        boolean.object = cutter
        obj = box(f'Pillar_Door_{side}', (side * 0.947, 2.24, 1.16), (0.016, 1.16, 2.28), wood, collection, 0.003)
        surface_uv(obj, 1.83, True)
        for y in (1.63, 2.85):
            box(f'Pillar_Door_Jamb_{side}', (side * 0.925, y, 1.17), (0.03, 0.055, 2.34), trim, collection, 0.003)
        box(f'Pillar_Door_Header_{side}', (side * 0.925, 2.24, 2.33), (0.03, 1.27, 0.055), trim, collection, 0.003)
        box(f'Pillar_Door_Kickplate_{side}', (side * 0.932, 2.24, 0.16), (0.012, 1.12, 0.29), trim, collection, 0.002)
        box(f'Pillar_Door_Pushbar_{side}', (side * 0.919, 2.24, 1.09), (0.045, 0.79, 0.052), steel, collection, 0.005)
    paint = bpy.data.materials['Race2_Painted_Column']
    header = box('Entry_Door_Header', (0, 2.24, 2.73), (1.79, 1.2, 0.42), paint, collection, 0.008)
    surface_uv(header, 1)
    sign = material('Race2_Exit_Housing', base=(0.65, 0.65, 0.59), roughness=0.5)
    box('Entry_Exit_Sign', (0, 1.625, 2.77), (0.34, 0.045, 0.15), sign, collection, 0.006)
    red = material('Race2_Exit_Letters', base=(0.5, 0.018, 0.005), roughness=0.5)
    text = bpy.data.curves.new('Exit_Letters', 'FONT')
    text.body = 'EXIT'
    text.size = 0.115
    text.align_x = 'CENTER'
    text.extrude = 0.001
    obj = bpy.data.objects.new('Entry_EXIT', text)
    collection.objects.link(obj)
    obj.scale = (1.1124603748321533,) * 3
    obj.location = (0, 1.597, 2.723)
    obj.rotation_euler = (math.pi / 2, 0, 0)
    obj.data.materials.append(red)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')

def upper_atrium(collection):
    """Window bays and the glazed end visible in the published atrium photograph.

    Dimensions fit the existing metric room envelope; photographs establish the
    architectural arrangement, not a surveyed set of dimensions.
    """
    teal = bpy.data.materials['CMU_Teal']
    plaster = bpy.data.materials['White_Plaster']
    frame = material('Race2_Window_Aluminum', base=(0.54, 0.56, 0.54), metallic=0.65, roughness=0.27)
    glass = material('Race2_Clear_Glass', base=(0.84, 0.92, 0.92), roughness=0.08)
    shader = next((n for n in glass.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'))
    shader.inputs['Transmission Weight'].default_value = 1
    shader.inputs['IOR'].default_value = 1.45
    recess = material('Race2_Interior_Window', base=(0.028, 0.046, 0.045), roughness=0.22, metallic=0.35)

def utility_props(collection):
    dark = material('Race2_Bin_Paint', base=(0.065, 0.084, 0.08), roughness=0.5, metallic=0.12)
    metal = bpy.data.materials['Race2_Table_Steel']
    black = bpy.data.materials['Race2_Equipment_Plastic']
    for (i, y) in enumerate((0.0, 0.62, 1.24)):
        box('Waste_Station_Cabinet', (-5.64, y, 0.49), (0.57, 0.6, 0.98), dark, collection, 0.013)
        box('Waste_Station_Lid', (-5.61, y, 1.005), (0.62, 0.61, 0.06), metal, collection, 0.012)
        opening = add_cylinder('Waste_Station_Opening', (-5.57, y, 1.039), 0.09, 0.006, black, collection, segments=32)
        color = (0.03, 0.14, 0.4) if i == 0 else (0.02, 0.25, 0.085)
        label = material(f'Race2_Bin_Label_{i}', base=color, roughness=0.65)
        box('Waste_Station_Label', (-5.34, y, 0.9), (0.006, 0.38, 0.11), label, collection, 0.001)

def exportable_foliage():
    mat = material('tree_small_02_leaves', bpy.data.images['tree_small_02_leaves_diff.png'], bpy.data.images['tree_small_02_leaves_rough.png'], bpy.data.images['tree_small_02_leaves_nor_gl.png'], uv='UVMap')
    tree = mat.node_tree
    uv = next((n for n in tree.nodes if n.type == 'UVMAP'))
    shader = next((n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED'))
    alpha = tree.nodes.new('ShaderNodeTexImage')
    alpha.image = bpy.data.images['tree_small_02_leaves_alpha.png']
    tree.links.new(uv.outputs['UV'], alpha.inputs['Vector'])
    tree.links.new(alpha.outputs['Color'], shader.inputs['Alpha'])

def lighting(collection):
    (width, height) = (512, 256)
    (v, u) = np.mgrid[0:height, 0:width] / np.array([height, width])[:, None, None]
    dome = np.zeros((height, width, 3)) + np.array((0.64, 0.71, 0.8))
    dome *= (0.55 + 0.45 * np.sin(v * math.pi))[:, :, None]
    sky = image('race2_overcast_sky', dome)
    world = bpy.context.scene.world
    world.node_tree.nodes.clear()
    (nodes, links) = (world.node_tree.nodes, world.node_tree.links)
    env = nodes.new('ShaderNodeTexEnvironment')
    env.image = sky
    bg = nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = 0.6
    output = nodes.new('ShaderNodeOutputWorld')
    links.new(env.outputs['Color'], bg.inputs['Color'])
    links.new(bg.outputs[0], output.inputs[0])
    scene = bpy.context.scene
    hero = bpy.data.objects['Race2_Hero_Camera']
    hero.location = (4.3, -8.8, 3.0)
    hero.rotation_euler = (Vector((0, 0.0, 1.0)) - hero.location).to_track_quat('-Z', 'Y').to_euler()
    overhead = bpy.data.objects['Race2_Overhead_Camera']
    overhead.location = (0, -0.7, 18)
    overhead.data.ortho_scale = 27
    scene.camera.data.dof.use_dof = False
    scene.cycles.samples = 256
    scene.cycles.adaptive_threshold = 0.015
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0.35
    data = bpy.data.cameras.new('Race2_Video_Camera')
    camera = bpy.data.objects.new('Race2_Video_Camera', data)
    collection.objects.link(camera)
    camera.location = (0.1, -7.5, 1.65)
    camera.rotation_euler = (Vector((0.1, 2.1, 1.4)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    data.lens = 22
    scene['race2_video_reference'] = 'blender/references/Race2 Video.mov; 3, 10, 15, 19 seconds'

def main(build_ducts=True):
    OUT.mkdir(parents=True, exist_ok=True)
    root = get_collection(NAME, bpy.data.collections['Race2_Recreation'])
    detail = get_collection(NAME + '_Ducts', root)
    props = get_collection(NAME + '_Furniture', root)
    arch = get_collection(NAME + '_Architecture', root)
    lights = get_collection(NAME + '_Lighting', root)
    surfaces()
    if build_ducts:
        ducts(detail)
    furniture(props)
    architecture(arch)
    upper_atrium(arch)
    utility_props(props)
    exportable_foliage()
    lighting(lights)
    from atrium_architecture import main as refine_nsh
    refine_nsh()
    from atrium_furniture import main as optimize_atrium
    optimize_atrium()
    bpy.context.view_layer.update()
