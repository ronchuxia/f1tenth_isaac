"""Imported furniture, the mapped floor and original duct tessellation."""
import math
import bmesh
import bpy
from mathutils import Vector
from scene_assets import *
RACE = 'Race2'
DUCT_BEVEL_RESOLUTION = 12
RIB_MAJOR_SEGMENTS = 32
RIB_MINOR_SEGMENTS = 8
RIB_MINOR_RADIUS = .014
TABLE_X = 5.15
TABLE_YS = (-4.8, -2.3, .2, 2.7)

def race_collection(suffix):
    """Builder collection for this race; balcony and stairs collections may
    carry a numeric suffix in some files, so fall back to a prefix match."""
    exact = bpy.data.collections.get(f'{RACE}_{suffix}')
    if exact is not None:
        return exact
    return next((c for c in bpy.data.collections if c.name.startswith(f'{RACE}_{suffix}')))

def rib_samples_from_mesh(mesh):
    """Recover ring centre, tangent, and radius from the builder's 12 sided rib bands."""
    samples = []
    vertices = [v.co.copy() for v in mesh.vertices]
    for start in range(0, len(vertices), 24):
        ring = vertices[start:start + 24]
        if len(ring) < 24:
            break
        near = sum((ring[i] for i in range(0, 24, 2)), Vector()) / 12.0
        far = sum((ring[i] for i in range(1, 24, 2)), Vector()) / 12.0
        center = (near + far) * 0.5
        tangent = (far - near).normalized()
        radius = sum(((ring[i] - near).length for i in range(0, 24, 2))) / 12.0
        samples.append((center, tangent, radius))
    return samples

def rebuild_ribs(obj):
    if 'photoreal_rib_samples' in obj:
        flat = list(obj['photoreal_rib_samples'])
        samples = [(Vector(flat[i:i + 3]), Vector(flat[i + 3:i + 6]), flat[i + 6]) for i in range(0, len(flat), 7)]
    else:
        samples = rib_samples_from_mesh(obj.data)
        obj['photoreal_rib_samples'] = [value for (center, tangent, radius) in samples for value in (*center, *tangent, radius)]
    vertices = []
    faces = []
    vertical = Vector((0.0, 0.0, 1.0))
    for (center, tangent, outer_radius) in samples:
        tangent = Vector((tangent.x, tangent.y, 0.0)).normalized()
        lateral = tangent.cross(vertical).normalized()
        major = outer_radius - RIB_MINOR_RADIUS
        base = len(vertices)
        for i in range(RIB_MAJOR_SEGMENTS):
            a = 2.0 * math.pi * i / RIB_MAJOR_SEGMENTS
            radial = vertical * math.cos(a) + lateral * math.sin(a)
            for j in range(RIB_MINOR_SEGMENTS):
                b = 2.0 * math.pi * j / RIB_MINOR_SEGMENTS
                vertices.append(center + radial * (major + RIB_MINOR_RADIUS * math.cos(b)) + tangent * (RIB_MINOR_RADIUS * math.sin(b)))
        for i in range(RIB_MAJOR_SEGMENTS):
            for j in range(RIB_MINOR_SEGMENTS):
                a0 = base + i * RIB_MINOR_SEGMENTS + j
                a1 = base + i * RIB_MINOR_SEGMENTS + (j + 1) % RIB_MINOR_SEGMENTS
                b0 = base + (i + 1) % RIB_MAJOR_SEGMENTS * RIB_MINOR_SEGMENTS + j
                b1 = base + (i + 1) % RIB_MAJOR_SEGMENTS * RIB_MINOR_SEGMENTS + (j + 1) % RIB_MINOR_SEGMENTS
                faces.append((a0, b0, b1, a1))
    mesh = bpy.data.meshes.new(obj.name + '_Photoreal_Data')
    mesh.from_pydata([tuple(v) for v in vertices], [], faces)
    finalize_mesh(mesh, smooth=True)
    for material in obj.data.materials:
        mesh.materials.append(material)
    old = obj.data
    obj.data = mesh
    if old.users == 0:
        bpy.data.meshes.remove(old)
    for modifier in list(obj.modifiers):
        obj.modifiers.remove(modifier)

def refine_track_tessellation():
    for obj in race_collection('Track').objects:
        if obj.type == 'CURVE':
            obj.data.bevel_resolution = DUCT_BEVEL_RESOLUTION
        elif obj.type == 'MESH' and obj.name.endswith('_Ribs'):
            rebuild_ribs(obj)

def build_furniture(collection, materials):
    chairs = ModelInstancer('SchoolChair_01', collection)
    trees = ModelInstancer('tree_small_02', collection)
    alarms = ModelInstancer('fire_alarm', collection)
    chair_scale = 0.98 / chairs.size.z
    for (index, y) in enumerate(TABLE_YS):
        chairs.place(f'Cafe_Chair_{index:02d}_South', (TABLE_X + 0.05, y - 0.72, 0.0), rotation_z=facing_yaw((0.0, 1.0)) + math.radians(6.0), scale=chair_scale)
        chairs.place(f'Cafe_Chair_{index:02d}_North', (TABLE_X - 0.04, y + 0.72, 0.0), rotation_z=facing_yaw((0.0, -1.0)) - math.radians(8.0), scale=chair_scale)
        if index in (0, 2):
            chairs.place(f'Cafe_Chair_{index:02d}_West', (TABLE_X - 0.74, y + 0.02, 0.0), rotation_z=facing_yaw((1.0, 0.0)) + math.radians(5.0), scale=chair_scale)
    tree_scale = 2.7 / trees.size.z
    for (index, (x, y)) in enumerate(((-4.85, 6.6), (4.75, 6.9))):
        add_cylinder(f'Planter_{index:02d}', (x, y, 0.24), 0.38, 0.48, materials['planter'], collection, segments=40)
        add_cylinder(f'Planter_Soil_{index:02d}', (x, y, 0.455), 0.36, 0.02, materials['soil'], collection, segments=40)
        trees.place(f'Indoor_Tree_{index:02d}', (x, y, 0.45), rotation_z=index * 1.9, scale=tree_scale)
    alarms.place('Fire_Alarm_Left_Wall', (-5.97, 1.9, 1.35), rotation_z=math.radians(90.0), scale=1.0)

def extend_floor():
    floor = bpy.data.objects["Atrium_Carpet_Tiles"]
    target_rows = int(math.ceil(4.0))
    applied_rows = int(floor.get("photoreal_extra_rows", 0))
    if target_rows > applied_rows:
        mesh = floor.data
        pattern = [0, 0, 0, 1, 0, 2, 0, 3, 0, 0, 1, 0, 0, 2, 0, 0]
        y_max = max(vertex.co.y for vertex in mesh.vertices)
        x_min = min(vertex.co.x for vertex in mesh.vertices)
        columns = int(round(max(vertex.co.x for vertex in mesh.vertices) - x_min))
        existing_rows = int(round(y_max - min(vertex.co.y for vertex in mesh.vertices)))
        bm = bmesh.new()
        bm.from_mesh(mesh)
        for k in range(target_rows - applied_rows):
            row = existing_rows + k
            y = y_max + k
            for column in range(columns):
                x = x_min + column
                verts = [bm.verts.new((x, y, 0.0)), bm.verts.new((x + 1.0, y, 0.0)), bm.verts.new((x + 1.0, y + 1.0, 0.0)), bm.verts.new((x, y + 1.0, 0.0))]
                face = bm.faces.new(verts)
                face.material_index = pattern[(row * 5 + column * 3) % len(pattern)]
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        floor["photoreal_extra_rows"] = target_rows


def main():
    extend_floor()
    for name in ('Atrium_Carpet_Tiles', 'Atrium_Column_+1.45', 'Atrium_Column_-1.45'):
        box_uv(bpy.data.objects[name])
    for obj in bpy.data.collections['Race2_Track'].objects:
        if obj.type == 'CURVE':
            for spline in obj.data.splines:
                spline.use_smooth = True
    refine_track_tessellation()
    root = get_collection('Race2_Photoreal', bpy.context.scene.collection)
    architecture = get_collection('Race2_Photoreal_Architecture', root)
    furniture = get_collection('Race2_Photoreal_Furniture', root)
    materials = {
        'planter': simple_material('Planter_Charcoal', (.05,.05,.05), roughness=.55),
        'soil': simple_material('Planter_Soil', (.08,.06,.045), roughness=.95),
    }
    ground = simple_material('Exterior_Ground', (.25,.27,.2), roughness=.9)
    base = simple_material('Rubber_Baseboard', (.06,.06,.065), roughness=.7)
    add_box('Exterior_Ground', (0,0,-.08), (120,120,.1), ground, architecture, uv=False)
    for side, x in [('Left', -5.992), ('Right', 5.992)]:
        add_box('Baseboard_'+side, (x,1.225,.05), (.016,24.45,.1), base, architecture)
    build_furniture(furniture, materials)
    setup_render('//renders/race2_atrium.png')

def duct_material(name, base_color, dust=0.3):
    """Matte woven cloth duct: base colour modulated by a 5 cm fabric weave,
    fabric sheen instead of a coat, crease and sag bumps, and a dust gradient
    that greys the lowest 14 cm."""
    (material, tree, bsdf) = reset_material(name)
    (nodes, links) = (tree.nodes, tree.links)
    coord = nodes.new('ShaderNodeTexCoord')
    coord.location = (-1400, 0)
    weave = add_pbr_textures(tree, bsdf, 'denim_fabric', projection='OBJECT', size_m=0.05, saturation=0.0, value=1.0, roughness_scale=0.3, roughness_offset=0.62, normal_strength=0.7, ao_strength=0.0)
    for link in list(links):
        if link.to_socket == bsdf.inputs['Base Color']:
            links.remove(link)
    weave_tone = nodes.new('ShaderNodeMapRange')
    weave_tone.location = (-700, 1150)
    weave_tone.inputs['From Min'].default_value = 0.2
    weave_tone.inputs['From Max'].default_value = 0.8
    weave_tone.inputs['To Min'].default_value = 0.82
    weave_tone.inputs['To Max'].default_value = 1.06
    links.new(weave['hsv'].outputs['Color'], weave_tone.inputs['Value'])
    variation = nodes.new('ShaderNodeTexNoise')
    variation.location = (-900, 900)
    variation.inputs['Scale'].default_value = 2.5
    variation.inputs['Detail'].default_value = 4.0
    links.new(coord.outputs['Object'], variation.inputs['Vector'])
    variation_range = nodes.new('ShaderNodeMapRange')
    variation_range.location = (-700, 900)
    variation_range.inputs['To Min'].default_value = 0.9
    variation_range.inputs['To Max'].default_value = 1.08
    links.new(variation.outputs['Fac'], variation_range.inputs['Value'])
    base = nodes.new('ShaderNodeRGB')
    base.location = (-700, 1400)
    base.outputs[0].default_value = (base_color[0], base_color[1], base_color[2], 1.0)
    woven = nodes.new('ShaderNodeMix')
    woven.data_type = 'RGBA'
    woven.blend_type = 'MULTIPLY'
    woven.location = (-500, 1250)
    woven.inputs['Factor'].default_value = 1.0
    links.new(base.outputs[0], woven.inputs[6])
    links.new(weave_tone.outputs['Result'], woven.inputs[7])
    varied = nodes.new('ShaderNodeMix')
    varied.data_type = 'RGBA'
    varied.blend_type = 'MULTIPLY'
    varied.location = (-500, 1000)
    varied.inputs['Factor'].default_value = 1.0
    links.new(woven.outputs[2], varied.inputs[6])
    links.new(variation_range.outputs['Result'], varied.inputs[7])
    separate = nodes.new('ShaderNodeSeparateXYZ')
    separate.location = (-900, 650)
    links.new(coord.outputs['Object'], separate.inputs['Vector'])
    dust_range = nodes.new('ShaderNodeMapRange')
    dust_range.location = (-700, 650)
    dust_range.inputs['From Min'].default_value = 0.01
    dust_range.inputs['From Max'].default_value = 0.14
    dust_range.inputs['To Min'].default_value = dust
    dust_range.inputs['To Max'].default_value = 0.0
    links.new(separate.outputs['Z'], dust_range.inputs['Value'])
    dusty = nodes.new('ShaderNodeMix')
    dusty.data_type = 'RGBA'
    dusty.blend_type = 'MIX'
    dusty.location = (-300, 900)
    dusty.inputs[7].default_value = (0.3, 0.28, 0.25, 1.0)
    links.new(dust_range.outputs['Result'], dusty.inputs['Factor'])
    links.new(varied.outputs[2], dusty.inputs[6])
    links.new(dusty.outputs[2], bsdf.inputs['Base Color'])
    creases = nodes.new('ShaderNodeTexNoise')
    creases.location = (-900, -900)
    creases.inputs['Scale'].default_value = 7.0
    creases.inputs['Detail'].default_value = 6.0
    creases.inputs['Roughness'].default_value = 0.6
    links.new(coord.outputs['Object'], creases.inputs['Vector'])
    crease_bump = nodes.new('ShaderNodeBump')
    crease_bump.location = (-100, -700)
    crease_bump.inputs['Strength'].default_value = 0.35
    crease_bump.inputs['Distance'].default_value = 0.02
    links.new(creases.outputs['Fac'], crease_bump.inputs['Height'])
    links.new(weave['normal_map'].outputs['Normal'], crease_bump.inputs['Normal'])
    sag = nodes.new('ShaderNodeTexNoise')
    sag.location = (-900, -1200)
    sag.inputs['Scale'].default_value = 2.0
    sag.inputs['Detail'].default_value = 2.0
    links.new(coord.outputs['Object'], sag.inputs['Vector'])
    sag_bump = nodes.new('ShaderNodeBump')
    sag_bump.location = (100, -900)
    sag_bump.inputs['Strength'].default_value = 0.25
    sag_bump.inputs['Distance'].default_value = 0.03
    links.new(sag.outputs['Fac'], sag_bump.inputs['Height'])
    links.new(crease_bump.outputs['Normal'], sag_bump.inputs['Normal'])
    links.new(sag_bump.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Specular IOR Level'].default_value = 0.3
    bsdf.inputs['Coat Weight'].default_value = 0.0
    bsdf.inputs['Sheen Weight'].default_value = 0.6
    bsdf.inputs['Sheen Roughness'].default_value = 0.55
    bsdf.inputs['Sheen Tint'].default_value = (0.8, 0.8, 0.8, 1.0)
    return material
