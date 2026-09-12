"""Build the glazed robot display, continuous wall corners and ceiling lights."""
import bpy, bmesh, math, sys
from pathlib import Path
from mathutils import Vector
import scene_assets as pc
from tepper_wall_corners import miter_corners

def main():
    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT / 'scripts/build-blender-scene'))
    C = bpy.data.collections.new('Tepper_Intersection_Refinement')
    bpy.context.scene.collection.children.link(C)
    white = bpy.data.materials['Tepper_Warm_White_Wall']
    silver = bpy.data.materials['TH_Anodized_Aluminum']

    def box(name, p, size, mat=white, angle=0):
        return pc.add_box('TI_' + name, p, size, mat, C, rot_z=angle)

    def hide(o):
        o.hide_render = True
        o.hide_set(True)

    def duplicate(o):
        q = o.copy()
        q.data = o.data.copy()
        q.name = 'TI_' + o.name
        C.objects.link(q)
        q.hide_render = False
        q.hide_set(False)
        hide(o)
        return q

    def boolean(o, operand, operation):
        bpy.context.view_layer.objects.active = o
        m = o.modifiers.new('Continuous solid', 'BOOLEAN')
        m.operation = operation
        m.solver = 'EXACT'
        m.use_self = True
        if isinstance(operand, bpy.types.Collection):
            m.operand_type = 'COLLECTION'
            m.collection = operand
        else:
            m.object = operand
        bpy.ops.object.modifier_apply(modifier=m.name)
    for o in list(bpy.data.objects):
        if o.name.startswith('Tepper_Robot_Area_Glass_Wall_'):
            hide(o)
    return_wall = duplicate(bpy.data.objects['Tepper_Locker_West_Connected_Wall'])
    cutter = box('Glazing_Opening_Cutter', (-0.04, 3.95, 1.47), (0.5, 2.5, 2.94))
    bpy.context.view_layer.update()
    boolean(return_wall, cutter, 'DIFFERENCE')
    bpy.data.objects.remove(cutter, do_unlink=True)
    base = duplicate(bpy.data.objects['Tepper_Locker_West_Connected_Baseboard'])
    cutter = box('Base_Opening_Cutter', (-0.04, 3.95, 0.08), (0.5, 2.5, 0.3))
    bpy.context.view_layer.update()
    boolean(base, cutter, 'DIFFERENCE')
    bpy.data.objects.remove(cutter, do_unlink=True)
    glass = pc.simple_material('TI_Clear_Display_Glass', (0.94, 0.97, 1), 0.035)
    p = next((n for n in glass.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'))
    p.inputs['Transmission Weight'].default_value = 1
    p.inputs['IOR'].default_value = 1.45
    glass.diffuse_color = (0.8, 0.9, 1, 0.18)
    panes = []

    def glazing(tag, start, end, count):
        a = Vector((*start, 0))
        b = Vector((*end, 0))
        t = (b - a).normalized()
        L = (b - a).length
        ang = math.atan2(t.y, t.x)

        def at(u, z):
            return a + t * u + Vector((0, 0, z))
        for i in range(count + 1):
            box(tag + '_Upright_' + str(i), at(L * i / count, 1.49), (0.065, 0.1, 2.9), silver, ang)
        for z in (0.075, 2.29, 2.925):
            box(tag + '_Rail_' + str(z), at(L / 2, z), (L, 0.1, 0.065), silver, ang)
        for i in range(count):
            for (j, (z0, z1)) in enumerate(((0.108, 2.2575), (2.3225, 2.8925))):
                o = box(tag + '_Pane_' + str(i) + '_' + str(j), at(L * (i + 0.5) / count, (z0 + z1) / 2), (L / count - 0.065, 0.012, z1 - z0), glass, ang)
                panes.append(o.name)
    glazing('Front', (-2.77, 2.610784), (-0.04, 2.7), 3)
    glazing('Return', (-0.04, 2.7), (-0.04, 5.12), 2)
    box('Return_End_Jamb', (-0.04, 5.18, 1.49), (0.16, 0.1, 2.98))
    box('Display_Back_Wall', (-1.57, 5.16, 1.6), (3.02, 0.08, 3.2))
    box('Display_Side_Wall', (-3.06, 3.92, 1.6), (0.08, 2.48, 3.2))
    box('Display_Ceiling', (-1.56, 3.92, 3.16), (2.88, 2.48, 0.08), bpy.data.materials['Tepper_White_Ceiling'])
    for o in list(bpy.data.objects):
        if o.name.startswith('Tepper_Robot_Arm'):
            hide(o)
    robotwhite = pc.simple_material('TI_Robot_White', (0.77, 0.79, 0.8), 0.28)
    robotjoint = pc.simple_material('TI_Robot_Joint', (0.2, 0.22, 0.24), 0.35)
    basecenter = Vector((-0.7, 4.45, 0))
    verts = []
    faces = []
    rings = [(0.025, 0.19), (0.06, 0.22), (0.14, 0.205), (0.22, 0.13), (0.3, 0.1)]
    for (z, r) in rings:
        for i in range(48):
            verts.append(basecenter + Vector((r * math.cos(i * math.tau / 48), r * math.sin(i * math.tau / 48), z)))
    faces = [tuple(range(47, -1, -1)), tuple(range(192, 240))]
    for j in range(4):
        for i in range(48):
            faces.append((48 * j + i, 48 * j + (i + 1) % 48, 48 * (j + 1) + (i + 1) % 48, 48 * (j + 1) + i))
    o = pc.add_polydata('TI_Robot_Pedestal', verts, faces, robotwhite, C)
    for p in o.data.polygons:
        p.use_smooth = True
    points = [basecenter + Vector(q) for q in [(0, 0, 0.29), (-0.1, 0.02, 0.52), (0.06, 0.01, 0.88), (0.01, -0.23, 1.01), (0.01, -0.31, 0.8)]]
    for (i, p) in enumerate(points):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.085 if i < 3 else 0.066, location=p)
        o = bpy.context.object
        o.name = 'TI_Robot_Joint_' + str(i)
        for c in list(o.users_collection):
            c.objects.unlink(o)
        C.objects.link(o)
        o.data.materials.append(robotwhite)
        for f in o.data.polygons:
            f.use_smooth = True
    for (i, (a, b)) in enumerate(zip(points, points[1:])):
        d = b - a
        o = pc.add_cylinder('TI_Robot_Link_' + str(i), (a + b) / 2, 0.06 if i < 2 else 0.045, d.length, robotwhite, C, segments=32)
        o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    box('Robot_End_Effector', points[-1] + Vector((0, 0, -0.055)), (0.1, 0.06, 0.04), robotjoint)
    dark = pc.simple_material('TI_Sign_Charcoal', (0.045, 0.048, 0.052), 0.45)
    red = pc.simple_material('TI_Sign_Red', (0.37, 0.012, 0.022), 0.5)
    letter = pc.simple_material('TI_Sign_Lettering', (0.91, 0.92, 0.92), 0.5)
    sign_center = bpy.data.objects['TI_Return_Pane_1_0'].location.copy()
    sign_center.z = 1.65
    box('MakerSpace_Sign', (0.024, sign_center.y, sign_center.z), (0.006, 0.98, 0.46), dark)
    box('MakerSpace_Sign_Red_Band', (0.028, sign_center.y, sign_center.z - 0.19), (0.006, 0.98, 0.08), red)

    def text(name, body, p, size):
        curve = bpy.data.curves.new(name, 'FONT')
        curve.body = body
        curve.size = size
        curve.align_x = 'CENTER'
        curve.align_y = 'CENTER'
        curve.extrude = 0.0001
        o = bpy.data.objects.new('TI_' + name, curve)
        C.objects.link(o)
        o.location = p
        o.rotation_euler = (math.pi / 2, 0, math.pi / 2)
        curve.materials.append(letter)
    text('MakerSpace_Title', 'AI MakerSpace', (0.033, sign_center.y, sign_center.z + 0.04), 0.105)
    walls = [o for o in list(bpy.data.objects) if o.type == 'MESH' and (not o.hide_render) and (o.name != 'TB_Rounded_Enclosure') and (white in list(o.data.materials)) and (o.dimensions.z > 0.25) and ('Wall' in o.name or 'Header' in o.name or o == return_wall)]
    sources = []
    operands = bpy.data.collections.new('TI_Wall_Operands')
    bpy.context.scene.collection.children.link(operands)
    for old in walls:
        q = old.copy()
        q.data = old.data.copy()
        q.matrix_world = old.matrix_world.copy()
        operands.objects.link(q)
        q.hide_set(False)
        q.hide_render = False
        sources.append(old.name)
        hide(old)
    union = box('Continuous_Visible_Walls', (100, 100, -10), (0.01, 0.01, 0.01))
    boolean(union, operands, 'UNION')
    for o in list(operands.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(operands)
    bm = bmesh.new()
    bm.from_mesh(union.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if (union.matrix_world @ v.co).x > 90], context='VERTS')
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-05)
    bmesh.ops.dissolve_limit(bm, angle_limit=0.0001, verts=list(bm.verts), edges=list(bm.edges))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(union.data)
    bm.free()
    corners = miter_corners(union)
    pc.box_uv(union)
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and (not o.hide_render) and o.name.startswith('Tepper_') and ('Baseboard' in o.name):
            q = duplicate(o)
            boolean(q, union, 'INTERSECT')
    lighting = []
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.name.startswith(('TH_Aligned_South_Wash_', 'TH_Continuous_North_Wash_')):
            old = o.data.energy
            o.data.energy *= 2.0
            lighting.append([o.name, old, o.data.energy])

    def area(name, p, power, size, size_y):
        d = bpy.data.lights.new('TI_' + name, 'AREA')
        d.energy = power
        d.shape = 'RECTANGLE'
        d.size = size
        d.size_y = size_y
        d.color = (1, 0.95, 0.88)
        o = bpy.data.objects.new(d.name, d)
        C.objects.link(o)
        o.location = p
        o.visible_glossy = False
        return o
    area('Intersection_Ceiling', (-1.7, 1.15, 3.02), 180, 3, 1.8)
    area('Return_Ceiling', (0.8, 4.0, 3.02), 100, 1.4, 2.4)
    area('Display_Ceiling_Light', (-1.55, 3.9, 3.0), 65, 2.3, 1.8)
    area('Side_Corridor_Ceiling', (0.6, -2.8, 3.0), 85, 1.1, 3.5)
    bpy.context.view_layer.update()
    bpy.data.use_autopack = True
