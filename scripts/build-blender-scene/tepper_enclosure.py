import bpy
import bmesh
import math
from pathlib import Path
from mathutils import Vector, Matrix
import scene_assets as pc
from tepper_details import bevel, bsdf
from tepper_recycling_mark import add_mark
ROOT = Path(__file__).resolve().parents[2]

def model_notice():
    notice = bpy.data.objects['TB_Door_Notice']
    collection = notice.users_collection[0]
    points = [notice.matrix_world @ v.co for v in notice.data.vertices]
    center = sum(points, Vector()) / len(points)
    wall = bpy.data.objects['Tepper_Lobby_Wall_Protrusion']
    tangent = -wall.matrix_world.col[0].to_3d().normalized()
    normal = wall.matrix_world.col[1].to_3d().normalized()
    up = Vector((0, 0, 1))
    for obj in list(collection.objects):
        if obj.name.startswith('TB_Notice_'):
            bpy.data.objects.remove(obj, do_unlink=True)
    white = bpy.data.materials.new('TB_Notice_White')
    white.use_nodes = True
    shader = white.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (0.88, 0.88, 0.88, 1)
    shader.inputs['Roughness'].default_value = 0.72
    notice.data.materials.clear()
    notice.data.materials.append(white)
    size = 0.245
    c = center + normal * 0.0012
    mesh = bpy.data.meshes.new('TB_Notice_Official_Logo_Mesh')
    mesh.from_pydata([c - tangent * size / 2 - up * size / 2, c + tangent * size / 2 - up * size / 2, c + tangent * size / 2 + up * size / 2, c - tangent * size / 2 + up * size / 2], [], [(0, 1, 2, 3)])
    layer = mesh.uv_layers.new(name='UVMap')
    for (item, uv) in zip(layer.data, [(0, 0), (1, 0), (1, 521 / 563), (0, 521 / 563)]):
        item.uv = uv
    material = bpy.data.materials.new('TB_Official_CMU_Logo')
    material.use_nodes = True
    image = bpy.data.images.load(str(Path(__file__).resolve().parents[2] / 'blender/assets/tepper/university_logo.png'), check_existing=True)
    image.pack()
    node = material.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = image
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = 0.72
    material.node_tree.links.new(node.outputs['Color'], shader.inputs['Base Color'])
    mesh.materials.append(material)
    obj = bpy.data.objects.new('TB_Notice_Official_Logo', mesh)
    collection.objects.link(obj)
    notice['wording'] = 'Carnegie Mellon University'
    notice['logo_source'] = 'https://brand.cmu.edu/resources/downloads'
    notice['notice_mapping'] = 'Official Carnegie Mellon logo asset on white placard'

def curve_enclosure():
    wall = bpy.data.objects['Tepper_Lobby_Wall_Protrusion']
    frame = wall.matrix_world.copy()
    frame.translation.z = 0
    inv = frame.inverted()
    collection = bpy.data.collections['Tepper_Bins_Wall_Refinement']
    mirror = frame @ Matrix.Diagonal((-1, 1, 1, 1)) @ inv
    for o in list(collection.objects):
        if o.name == 'TB_Graphic_Return' or o.name.startswith('TB_Return_Line_'):
            copy = o.copy()
            copy.data = o.data.copy()
            copy.name = o.name.replace('TB_Graphic_Return', 'TB_Graphic_Opposite_Return').replace('TB_Return_Line_', 'TB_Opposite_Return_Line_')
            collection.objects.link(copy)
            copy.matrix_world = mirror @ o.matrix_world
    objects = [o for o in bpy.data.collections['Tepper_Bins_Wall_Refinement'].objects if not o.name.startswith(('TB_Corridor_', 'TB_Lobby_'))]
    paper = bpy.data.objects['TB_Door_Notice']
    points = [paper.matrix_world @ v.co for v in paper.data.vertices]
    center = sum(points, Vector()) / len(points)
    p = inv @ center
    target = Vector((0, p.y, 1.0))
    delta = frame @ target - center
    for name in ('TB_Door_Notice', 'TB_Notice_Official_Logo'):
        bpy.data.objects[name].matrix_world.translation += delta

    def warp(v):
        p = inv @ v
        factor = 1 - 0.085 * (p.z - 1) ** 2
        p.x *= factor
        return frame @ p
    rigid_prefix = ('TB_Door_Hinge', 'TB_Door_Lock', 'TB_Door_Lever')
    for o in objects:
        if o.name.startswith(rigid_prefix):
            c = o.matrix_world.translation.copy()
            o.matrix_world.translation += warp(c) - c
        elif o.type == 'CURVE':
            inverse = o.matrix_world.inverted()
            for spline in o.data.splines:
                for p in spline.points:
                    p.co = (*inverse @ warp(o.matrix_world @ p.co.to_3d()), 1)
        elif o.type == 'MESH':
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=24, use_grid_fill=True)
            bm.to_mesh(o.data)
            bm.free()
            inverse = o.matrix_world.inverted()
            for v in o.data.vertices:
                v.co = inverse @ warp(o.matrix_world @ v.co)
            o.data.update()
            for poly in o.data.polygons:
                poly.use_smooth = abs(poly.normal.z) < 0.85
    for name in ('TB_Door_Notice', 'TB_Notice_Official_Logo'):
        bpy.data.objects[name].location.z += 0.1
    target.z += 0.1
    bpy.context.view_layer.update()
    shell = bpy.data.objects['TB_Rounded_Enclosure']
    shell['surface_profile'] = 'Only the two colorful side panels bow vertically; front and back remain planar'
    paper['centered_on_front'] = True
    evaluated = shell.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    local = [inv @ (evaluated.matrix_world @ v.co) for v in mesh.vertices]
    assert max((abs(v.x) for v in local)) <= 1.02501
    assert max((abs(v.y) for v in local)) <= 0.82501
    assert abs(max((v.z for v in local)) - 2) < 0.001
    evaluated.to_mesh_clear()
    return {'height': 2.0, 'maximum_front_bow_metres': 0.0, 'maximum_side_bow_metres': 1.025 * 0.085, 'logo_center_local': list(target), 'footprint_preserved': True}

def main():
    C = bpy.data.collections.new('Tepper_Bins_Wall_Refinement')
    bpy.data.collections['Tepper_Hallway_Recreation'].children.link(C)

    def mat(n, c, rough=0.45, metal=0):
        m = pc.simple_material(n, c, rough)
        bsdf(m).inputs['Metallic'].default_value = metal
        return m
    blue = mat('TB_Molded_Blue', (0.018, 0.065, 0.24), 0.34)
    grey = mat('TB_Molded_Grey', (0.3, 0.32, 0.33), 0.48)
    black = mat('TB_Black_Lid', (0.017, 0.019, 0.022), 0.33)
    blackbag = mat('TB_Black_Liner', (0.009, 0.01, 0.012), 0.17)
    clear = mat('TB_Clear_Liner', (0.72, 0.75, 0.79), 0.22)
    bsdf(clear).inputs['Transmission Weight'].default_value = 0.65
    bsdf(clear).inputs['Alpha'].default_value = 0.38
    white = mat('TB_White_Print', (0.85, 0.86, 0.86), 0.62)
    silver = mat('TB_Brushed_Hardware', (0.47, 0.49, 0.51), 0.27, 0.8)

    def rect(w, d, r, N=8):
        return [(cx + r * math.cos(a), cy + r * math.sin(a)) for (cx, cy, start) in [(w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)] for a in [math.radians(start + j * 90 / N) for j in range(N)]]

    def mesh(n, v, f, m, T):
        return pc.add_polydata(n, [T @ Vector(p) for p in v], f, m, C)

    def box(n, p, s, m, T, edge=0.003):
        o = pc.add_box(n, (0, 0, 0), s, m, C)
        o.matrix_world = T @ Matrix.Translation(Vector(p))
        if edge:
            bevel(o, edge)
        return o

    def loops(n, rings, m, T, caps=True):
        verts = []
        for (w, d, z) in rings:
            verts += [(x, y, z) for (x, y) in rect(w, d, min(0.027, d / 4))]
        N = 32
        faces = []
        for k in range(len(rings) - 1):
            for j in range(N):
                faces.append((k * N + j, k * N + (j + 1) % N, (k + 1) * N + (j + 1) % N, (k + 1) * N + j))
        if caps:
            faces += [tuple(reversed(range(N))), tuple(range((len(rings) - 1) * N, len(rings) * N))]
        o = mesh(n, verts, faces, m, T)
        bevel(o, 0.002)
        return o

    def line(n, points, radius, m, T):
        d = bpy.data.curves.new(n, 'CURVE')
        d.dimensions = '3D'
        d.bevel_depth = radius
        d.bevel_resolution = 2
        s = d.splines.new('POLY')
        s.points.add(len(points) - 1)
        for (a, p) in zip(s.points, points):
            a.co = (*p, 1)
        o = bpy.data.objects.new(n, d)
        C.objects.link(o)
        o.matrix_world = T
        d.materials.append(m)
        return o

    def cut(o, c):
        bpy.context.view_layer.objects.active = o
        mod = o.modifiers.new('Opening', 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = c
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(c, do_unlink=True)
    frames = []
    for body in [o for o in bpy.data.objects if o.name.startswith('Slim_Bin_') and o.name.endswith('_Body')]:
        prefix = body.name[:-5]
        T = body.matrix_world.copy()
        recycle = 'Recycling' in prefix
        name = prefix.replace('Slim_Bin', 'TB')
        m = blue if recycle else grey
        for o in bpy.data.objects:
            if o.name.startswith(prefix + '_'):
                o.hide_render = True
                o.hide_set(True)
        frames.append({'prefix': name, 'matrix': [list(v) for v in T], 'recycling': recycle})
        loops(name + '_Tapered_Shell', [(0.505, 0.23, 0), (0.54, 0.258, 0.07), (0.557, 0.278, 0.69), (0.56, 0.28, 0.752), (0.538, 0.258, 0.752), (0.483, 0.208, 0.035)], m, T)
        for side in (-1, 1):
            pts = []
            for (x, z) in rect(0.4, 0.59, 0.025):
                pts.append((x, side * (0.135 + 0.003), z + 0.37))
            line(name + '_Molded_Panel_' + str(side), pts + [pts[0]], 0.003, m, T)
            for x in (-0.245, 0.245):
                box(name + '_Molded_Rib', (x, side * 0.135, 0.38), (0.016, 0.014, 0.6), m, T, 0.006)
        loops(name + '_Rim', [(0.568, 0.288, 0.738), (0.57, 0.29, 0.774), (0.543, 0.263, 0.782)], m, T)
        vertices = []
        N = 192
        rim = rect(0.585, 0.305, 0.03, 16)
        segments = [math.dist(rim[q], rim[(q + 1) % len(rim)]) for q in range(len(rim))]
        perimeter = sum(segments)

        def rim_point(f):
            d = f * perimeter
            for (q, length) in enumerate(segments):
                if d <= length:
                    u = d / length
                    return (rim[q][0] * (1 - u) + rim[(q + 1) % len(rim)][0] * u, rim[q][1] * (1 - u) + rim[(q + 1) % len(rim)][1] * u)
                d -= length
            return rim[0]
        for k in range(5):
            for j in range(N):
                theta = math.tau * j / N
                (x, y) = rim_point(j / N)
                fold = 0.0035 * math.sin(theta * 17 + k * 1.3) + 0.0014 * math.sin(theta * 31 - k * 0.7)
                z = 0.783 - k * (0.085 if recycle else 0.052) / 4 + 0.013 * math.sin(theta * 3 + k * 0.6) + 0.005 * math.sin(theta * 11 + k)
                vertices.append((x + fold * math.cos(theta), y + fold * math.sin(theta), z))
        faces = [(k * N + j, k * N + (j + 1) % N, (k + 1) * N + (j + 1) % N, (k + 1) * N + j) for k in range(4) for j in range(N)]
        mesh(name + '_Wrinkled_Liner', vertices, faces, clear if recycle else blackbag, T)
        lid = loops(name + '_Raised_Lid', [(0.57, 0.29, 0.782), (0.57, 0.29, 0.801), (0.515, 0.248, 0.829 if recycle else 0.805)], blue if recycle else black, T)
        if recycle:
            center = T @ Vector((-0.12, 0, 0.81))
            c = pc.add_cylinder(name + '_Hole_Cutter', center, 0.061, 0.2, None, C, segments=64)
            cut(lid, c)
            c = box(name + '_Slot_Cutter', (0.105, 0, 0.82), (0.19, 0.055, 0.2), None, T, 0.02)
            bpy.context.view_layer.objects.active = c
            for mod in list(c.modifiers):
                bpy.ops.object.modifier_apply(modifier=mod.name)
            cut(lid, c)
            box(name + '_Opening_Darkness', (0, 0, 0.74), (0.48, 0.21, 0.006), black, T)
            label = bpy.data.objects[prefix + '_Label']
            label.name = name + '_Side_Label'
            C.objects.link(label)
            label.hide_render = False
            label.hide_set(False)
            R = Matrix.Rotation(-math.pi / 2, 4, 'Z')
            label.matrix_world = T @ Matrix.Translation(Vector((0.286, 0, 0.53))) @ R
            add_mark(name + '_Recycling_Mark', T, C, white)
        else:
            for x in (-0.25, 0.25):
                box(name + '_Handle', (x, 0.157, 0.75), (0.052, 0.035, 0.018), grey, T, 0.007)
            box(name + '_Small_Red_Badge', (0, 0.148, 0.686), (0.046, 0.004, 0.016), mat(name + '_Badge', (0.22, 0.025, 0.025)), T)
    wall = bpy.data.objects['Tepper_Lobby_Wall_Protrusion']
    W = wall.matrix_world
    a = W @ Vector((1.025, 0.825, -1.6))
    b = W @ Vector((-1.025, 0.825, -1.6))
    t = (b - a).normalized()
    n = Vector((t.y, -t.x, 0))
    L = (b - a).length
    a -= n * 0.089
    b -= n * 0.089
    T = Matrix(((t.x, n.x, 0, a.x), (t.y, n.y, 0, a.y), (0, 0, 1, 0), (0, 0, 0, 1)))
    height = 2.72
    wall.hide_render = True
    wall.hide_set(True)
    body_frame = W.copy()
    body_frame.translation.z = 0
    enclosure = box('TB_Rounded_Enclosure', (0, 0, height / 2), (2.05, 1.65, height), bpy.data.materials['Tepper_Warm_White_Wall'], body_frame, 0.075)
    enclosure.modifiers[-1].segments = 12
    laminate = mat('TB_Graphic_Laminate', (0.32, 0.3, 0.34), 0.57)
    ink = mat('TB_Graphic_Lines', (0.6, 0.6, 0.64), 0.65)
    left = 0.55
    right = 1.5
    top = 2.43
    box('TB_Patterned_Surround_Left', ((left + 0.075) / 2, 0.089, (height - 0.075) / 2), (left - 0.075, 0.016, height - 0.075), laminate, T)
    box('TB_Patterned_Surround_Right', ((right + L - 0.075) / 2, 0.089, (height - 0.075) / 2), (L - right - 0.075, 0.016, height - 0.075), laminate, T)
    box('TB_Patterned_Surround_Header', ((left + right) / 2, 0.089, (top + height - 0.075) / 2), (right - left, 0.016, height - top - 0.075), laminate, T)
    box('TB_Door_Reveal', ((left + right) / 2, 0.086, top / 2), (right - left, 0.02, top), black, T)
    box('TB_Graphic_Door', ((left + right) / 2, 0.083, (top + 0.015) / 2), (right - left - 0.016, 0.028, top - 0.015), laminate, T, 0.002)
    for i in range(49):
        pts = []
        for j in range(121):
            x = L * j / 120
            z = -0.7 + i * 0.079 + 0.34 * math.sin(x * 1.5 + i * 0.035) + 0.1 * x
            if 0.015 < z < height - 0.075 and 0.075 < x < L - 0.075:
                y = 0.0985
                pts.append((x, y, z))
        if len(pts) > 1:
            line('TB_Graphic_Wave_' + str(i), pts, 0.00065, ink, T)
    for i in range(63):
        pts = []
        for j in range(100):
            z = 0.02 + (height - 0.095) * j / 99
            x = -1.5 + i * 0.071 + 0.43 * math.sin(z * 1.4) + 0.34 * z
            if 0.075 < x < L - 0.075:
                pts.append((x, 0.0985, z))
        if len(pts) > 1:
            line('TB_Graphic_Crosswave_' + str(i), pts, 0.00065, ink, T)
    for z in (0.28, 1.23, 2.17):
        box('TB_Door_Hinge', (right - 0.02, 0.128, z), (0.055, 0.043, 0.11), silver, T, 0.004)
    box('TB_Door_Lock_Plate', (left + 0.1, 0.126, 1.03), (0.072, 0.024, 0.22), silver, T, 0.006)
    box('TB_Door_Lever_Stem', (left + 0.1, 0.163, 1.01), (0.022, 0.075, 0.024), silver, T, 0.005)
    box('TB_Door_Lever', (left + 0.16, 0.202, 1.01), (0.15, 0.022, 0.026), silver, T, 0.007)
    vertices = [T @ Vector(p) for p in [(1.08, .099, 1.47), (.76, .099, 1.47), (.76, .099, 1.98), (1.08, .099, 1.98)]]
    normal = (vertices[1] - vertices[0]).cross(vertices[3] - vertices[0]).normalized()
    paper = pc.add_polydata('TB_Door_Notice', [v - normal * .002 for v in vertices], [(0, 1, 2, 3)], white, C)
    thickness = paper.modifiers.new('Paper thickness', 'SOLIDIFY')
    thickness.thickness = .001
    for index in (1, 2, 3, 4):
        o = bpy.data.objects['Tepper_Lobby_Wall_Protrusion_Baseboard_' + str(index)]
        o.hide_render = True
        o.hide_set(True)
    box('TB_Metal_Threshold', (L / 2, 0.11, 0.025), (L, 0.028, 0.05), silver, T, 0.001)
    s = W @ Vector((1.025, -0.825, -1.6))
    e = W @ Vector((1.025, 0.825, -1.6))
    d = (e - s).normalized()
    normal = Vector((d.y, -d.x, 0))
    s -= normal * 0.089
    e -= normal * 0.089
    S = Matrix(((d.x, normal.x, 0, s.x), (d.y, normal.y, 0, s.y), (0, 0, 1, 0), (0, 0, 0, 1)))
    side = mat('TB_Dark_Graphic_Return', (0.025, 0.035, 0.06), 0.6)
    box('TB_Graphic_Return', ((e - s).length / 2, 0.089, height / 2), ((e - s).length - 0.15, 0.016, height - 0.15), side, S)
    palette = [mat('TB_Return_Ink_' + str(i), c, 0.65) for (i, c) in enumerate(((0.1, 0.3, 0.31), (0.12, 0.21, 0.38), (0.38, 0.1, 0.16), (0.36, 0.28, 0.18)))]
    for family in range(2):
        for i in range(65):
            pts = []
            for j in range(61):
                x = (e - s).length * j / 60
                z = -0.55 + i * 0.057 + (0.22 * x + 0.19 * math.sin(x * 1.8 + i * 0.018) if family == 0 else -0.37 * x + 0.12 * math.sin(x * 2.1 + i * 0.03))
                if 0.075 < z < height - 0.075 and 0.075 < x < (e - s).length - 0.075:
                    pts.append((x, 0.0985, z))
            if len(pts) > 1:
                line('TB_Return_Line_' + str(family) + '_' + str(i), pts, 0.0014, palette[i % 4], S)
    for o in C.objects:
        if not o.name.startswith(('TB_Corridor_', 'TB_Lobby_')):
            o.matrix_world = Matrix.Diagonal((1, 1, 2.0 / height, 1)) @ o.matrix_world
    height = 2.0
    paper.data.transform(paper.matrix_world)
    paper.matrix_world = Matrix.Identity(4)
    model_notice()
    curve_enclosure()
    bpy.context.view_layer.update()
    bpy.data.use_autopack = True
