import bpy
import math
import os
import numpy as np
from mathutils import Vector


BACK_WALL_EXTENSION_Y = 3.00
BLACK_DUCT_RADIUS = 0.20
BLACK_DUCT_RIB_RADIUS = BLACK_DUCT_RADIUS + 0.018
YELLOW_DUCT_RADIUS = 0.15
MIDDLE_TABLE_Y = 0.20
PILLAR_BEHIND_MIDDLE_TABLE_Y = 1.00
PILLAR_TARGET_Y = MIDDLE_TABLE_Y + PILLAR_BEHIND_MIDDLE_TABLE_Y
BACK_ASSEMBLY_FORWARD_SHIFT_Y = PILLAR_TARGET_Y - 8.25
LONG_PILLAR_LENGTH = 1.82
LEFT_PILLAR_WORLD_LOCATION = (-1.10, 2.20)
PERSON_LEFT_MID_LOCATION = (-3.5, -2.0, 0.0)
F1TENTH_CAR_ORIGIN = (-3.5, -4.0, 0.0)


def remove_collection(collection):
    for child in list(collection.children):
        remove_collection(child)
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def create_collection(name, parent):
    collection = bpy.data.collections.new(name)
    parent.children.link(collection)
    return collection


def move_to_collection(obj, collection):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def make_material(name, color, roughness=0.5, metallic=0.0, emission=None):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = color
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission is not None:
            emission_input = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
            if emission_input:
                emission_input.default_value = emission
            strength_input = bsdf.inputs.get("Emission Strength")
            if strength_input:
                strength_input.default_value = 3.0
    return material


def add_fabric_bump(material, scale=24.0, strength=0.2):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    bump = nodes.new("ShaderNodeBump")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.65
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.035
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def set_material(obj, material):
    obj.data.materials.append(material)


def add_box(name, location, dimensions, material, collection, bevel=0.0, rotation_z=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=(0.0, 0.0, rotation_z))
    obj = bpy.context.active_object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0.0:
        modifier = obj.modifiers.new("Soft edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    set_material(obj, material)
    move_to_collection(obj, collection)
    return obj


def add_capsule_prism(name, location, width, length, height, material, collection, cap_segments=12, bevel=0.0, rotation_z=0.0):
    radius = width * 0.5
    straight_half = max(0.0, (length - width) * 0.5)
    outline = []
    for index in range(cap_segments + 1):
        angle = math.pi * index / cap_segments
        outline.append((
            radius * math.cos(angle),
            straight_half + radius * math.sin(angle),
        ))
    for index in range(cap_segments + 1):
        angle = math.pi + math.pi * index / cap_segments
        outline.append((
            radius * math.cos(angle),
            -straight_half + radius * math.sin(angle),
        ))

    bottom_z = -height * 0.5
    top_z = height * 0.5
    vertices = [(x, y, bottom_z) for x, y in outline]
    vertices.extend((x, y, top_z) for x, y in outline)
    count = len(outline)
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((
            index,
            next_index,
            next_index + count,
            index + count,
        ))

    mesh = bpy.data.meshes.new(name + "_Data")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, rotation_z)
    collection.objects.link(obj)
    if bevel > 0.0:
        modifier = obj.modifiers.new("Soft edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    set_material(obj, material)
    return obj


def add_cylinder(name, location, radius, depth, material, collection, vertices=32, rotation=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    set_material(obj, material)
    move_to_collection(obj, collection)
    return obj


def add_uv_sphere(name, location, radius, material, collection):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=radius, location=location)
    obj = bpy.context.active_object
    obj.name = name
    set_material(obj, material)
    move_to_collection(obj, collection)
    bpy.ops.object.shade_smooth()
    return obj


def add_curve(name, points, radius, material, collection, cyclic=False):
    curve_data = bpy.data.curves.new(name + "_Data", "CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 2
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 4
    curve_data.resolution_u = 2
    curve_data.materials.append(material)
    spline = curve_data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for spline_point, point in zip(spline.points, points):
        spline_point.co = (point[0], point[1], point[2], 1.0)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve_data)
    collection.objects.link(obj)
    return obj


def build_tiled_floor(collection, materials, width=12.0, length=25.0, tile=1.0, center_y=1.25):
    vertices = []
    faces = []
    material_indices = []
    cols = math.ceil(width / tile)
    rows = math.ceil(length / tile)
    x0 = -cols * tile * 0.5
    y0 = center_y - rows * tile * 0.5
    pattern = [0, 0, 0, 1, 0, 2, 0, 3, 0, 0, 1, 0, 0, 2, 0, 0]
    for row in range(rows):
        for col in range(cols):
            x = x0 + col * tile
            y = y0 + row * tile
            base = len(vertices)
            vertices.extend([
                (x, y, 0.0),
                (x + tile, y, 0.0),
                (x + tile, y + tile, 0.0),
                (x, y + tile, 0.0),
            ])
            faces.append((base, base + 1, base + 2, base + 3))
            material_indices.append(pattern[(row * 5 + col * 3) % len(pattern)])
    mesh = bpy.data.meshes.new("Atrium_Carpet_Data")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Atrium_Carpet_Tiles", mesh)
    collection.objects.link(obj)
    for material in materials:
        mesh.materials.append(material)
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.material_index = material_index
    return obj


def catmull_rom(points, cyclic=False, subdivisions=4):
    if len(points) < 2:
        return points
    vectors = [Vector(point) for point in points]
    output = []
    segment_count = len(vectors) if cyclic else len(vectors) - 1
    for index in range(segment_count):
        p1 = vectors[index]
        p2 = vectors[(index + 1) % len(vectors)]
        p0 = vectors[(index - 1) % len(vectors)] if cyclic or index > 0 else p1
        p3 = vectors[(index + 2) % len(vectors)] if cyclic or index + 2 < len(vectors) else p2
        for step in range(subdivisions):
            t = step / subdivisions
            t2 = t * t
            t3 = t2 * t
            point = 0.5 * (
                2.0 * p1
                + (-p0 + p2) * t
                + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
                + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
            )
            output.append(tuple(point))
    if not cyclic:
        output.append(tuple(vectors[-1]))
    return output


def samples_along_polyline(points, spacing, cyclic=False):
    vectors = [Vector(point) for point in points]
    segments = list(zip(vectors, vectors[1:]))
    if cyclic:
        segments.append((vectors[-1], vectors[0]))
    samples = []
    carry = 0.0
    for start, end in segments:
        direction = end - start
        length = direction.length
        if length < 1e-5:
            continue
        tangent = direction.normalized()
        distance = spacing - carry if carry > 1e-6 else 0.0
        while distance <= length:
            samples.append((start + tangent * distance, tangent))
            distance += spacing
        carry = max(0.0, length - (distance - spacing))
    return samples


def add_ribs_mesh(name, samples, radius, width, material, collection, sides=12):
    vertices = []
    faces = []
    for center, tangent in samples:
        tangent = Vector((tangent.x, tangent.y, 0.0)).normalized()
        vertical = Vector((0.0, 0.0, 1.0))
        lateral = tangent.cross(vertical).normalized()
        base = len(vertices)
        for side in range(sides):
            angle = 2.0 * math.pi * side / sides
            radial = vertical * math.cos(angle) + lateral * math.sin(angle)
            vertices.append(tuple(center - tangent * width * 0.5 + radial * radius))
            vertices.append(tuple(center + tangent * width * 0.5 + radial * radius))
        for side in range(sides):
            next_side = (side + 1) % sides
            faces.append((
                base + side * 2,
                base + next_side * 2,
                base + next_side * 2 + 1,
                base + side * 2 + 1,
            ))
    if not vertices:
        return None
    mesh = bpy.data.meshes.new(name + "_Data")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(material)
    bevel = obj.modifiers.new("Rounded rib edges", "BEVEL")
    bevel.width = 0.012
    bevel.segments = 2
    return obj

















def add_area_light(name, location, energy, size, collection, color=(1.0, 0.91, 0.78)):
    data = bpy.data.lights.new(name + "_Data", "AREA")
    data.energy = energy
    data.shape = "RECTANGLE"
    data.size = size
    data.size_y = size * 0.55
    data.color = color
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, 0.0)
    collection.objects.link(obj)
    return obj


def point_camera(camera, target):
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()




def create_shared_materials():
    materials = {
        "carpet": [
            make_material("Carpet_Charcoal", (0.16, 0.17, 0.18, 1.0), 0.92),
            make_material("Carpet_Blue", (0.22, 0.42, 0.52, 1.0), 0.92),
            make_material("Carpet_Tan", (0.48, 0.39, 0.29, 1.0), 0.92),
            make_material("Carpet_Orange", (0.69, 0.36, 0.17, 1.0), 0.92),
        ],
        "cream": make_material("Cream_Brick", (0.73, 0.64, 0.49, 1.0), 0.78),
        "teal": make_material("CMU_Teal", (0.11, 0.30, 0.30, 1.0), 0.42, metallic=0.15),
        "glass": make_material("Window_Glass", (0.08, 0.18, 0.21, 1.0), 0.15, metallic=0.25),
        "wood": make_material("Door_Wood", (0.42, 0.23, 0.11, 1.0), 0.52),
        "metal": make_material("Dark_Metal", (0.08, 0.10, 0.11, 1.0), 0.28, metallic=0.8),
        "dark_floor": make_material("Dark_Floor", (0.10, 0.11, 0.12, 1.0), 0.70),
        "table": make_material("Table_White", (0.68, 0.69, 0.67, 1.0), 0.55),
        "chair_red": make_material("Chair_Red", (0.66, 0.10, 0.07, 1.0), 0.65),
        "chair_gray": make_material("Chair_Gray", (0.34, 0.36, 0.35, 1.0), 0.65),
        "chair_blue": make_material("Chair_Blue", (0.16, 0.29, 0.42, 1.0), 0.65),
        "shirt_blue": make_material("Shirt_Blue", (0.08, 0.18, 0.28, 1.0), 0.75),
        "shirt_gray": make_material("Shirt_Gray", (0.38, 0.40, 0.42, 1.0), 0.75),
        "shirt_white": make_material("Shirt_White", (0.72, 0.72, 0.69, 1.0), 0.75),
        "pants_dark": make_material("Pants_Dark", (0.05, 0.06, 0.07, 1.0), 0.78),
        "pants_tan": make_material("Pants_Tan", (0.43, 0.35, 0.23, 1.0), 0.78),
        "skin": make_material("Skin", (0.64, 0.42, 0.28, 1.0), 0.72),
        "black": make_material("RC_Black", (0.025, 0.028, 0.03, 1.0), 0.46),
        "orange": make_material("Lidar_Orange", (1.0, 0.30, 0.02, 1.0), 0.40),
        "red": make_material("Wire_Red", (0.55, 0.02, 0.015, 1.0), 0.46),
        "blue_emission": make_material(
            "Controller_Blue_LED",
            (0.02, 0.18, 0.5, 1.0),
            0.28,
            emission=(0.02, 0.15, 1.0, 1.0),
        ),
    }
    duct_materials = {
        "yellow_duct": make_material(
            "Yellow_Duct_Fabric",
            (0.95, 0.54, 0.015, 1.0),
            0.72,
        ),
        "black_duct": make_material(
            "Black_Duct_Fabric",
            (0.018, 0.022, 0.026, 1.0),
            0.62,
        ),
        "yellow_rings": make_material(
            "Yellow_Duct_Rings",
            (0.025, 0.025, 0.022, 1.0),
            0.50,
        ),
        "black_rings": make_material(
            "Black_Duct_Rings",
            (0.018, 0.022, 0.026, 1.0),
            0.42,
            metallic=0.1,
        ),
    }
    add_fabric_bump(duct_materials["yellow_duct"], 32.0, 0.20)
    add_fabric_bump(duct_materials["black_duct"], 26.0, 0.16)
    return materials, duct_materials


def build_track_components(collection, duct_specs, map_to_world, duct_materials):
    summaries = []
    for duct in duct_specs:
        radius = duct["radius"]
        source_points = duct["source_points"]
        world_points = [map_to_world(point, radius) for point in source_points]
        point_transform = duct.get("point_transform")
        if point_transform:
            world_points = point_transform(world_points)
        subdivisions = duct.get("subdivisions", 5)
        cyclic = duct.get("cyclic", False)
        smooth_points = catmull_rom(
            world_points,
            cyclic=cyclic,
            subdivisions=subdivisions,
        )
        smooth_point_transform = duct.get("smooth_point_transform")
        if smooth_point_transform:
            smooth_points = smooth_point_transform(smooth_points)
        add_curve(
            duct["name"],
            smooth_points,
            radius,
            duct_materials[duct["material"]],
            collection,
            cyclic=cyclic,
        )
        samples = samples_along_polyline(
            smooth_points,
            spacing=duct["spacing"],
            cyclic=cyclic,
        )
        add_ribs_mesh(
            duct["name"] + "_Ribs",
            samples,
            duct["rib_radius"],
            duct.get("rib_width", 0.028),
            duct_materials[duct["rib_material"]],
            collection,
        )
        summaries.append({
            "name": duct["name"],
            "source_points": len(source_points),
            "source_start": list(source_points[0]),
            "source_end": list(source_points[-1]),
            "cyclic": cyclic,
            "radius": radius,
            "material": duct["material"],
            "map_alignment": duct.get("map_alignment", "centerline follows map contour"),
        })
    return summaries


def load_pgm_map(image_path):
    with open(image_path, 'rb') as source:
        assert source.readline().strip() == b'P5'
        dimensions = source.readline()
        while dimensions.startswith(b'#'):
            dimensions = source.readline()
        width, height = map(int, dimensions.split())
        assert source.readline().strip() == b'255'
        gray = np.frombuffer(source.read(), dtype=np.uint8).reshape(height, width)
    pixels = np.ones((height, width, 4), dtype=np.float32)
    pixels[:, :, :3] = gray[::-1, :, None] / 255
    image = bpy.data.images.new(os.path.basename(image_path), width, height)
    image.pixels.foreach_set(pixels.ravel())
    image['source_path'] = image_path
    image.pack()
    return image


def build_image_overlay(
    name,
    collection,
    image_path,
    map_to_world,
    resolution,
    alignment,
    render_height=0.012,
    render_visible=False,
    highlight_color=None,
):
    image = load_pgm_map(image_path)
    width, height = image.size
    corners = [
        map_to_world((0, 0), render_height),
        map_to_world((0, height), render_height),
        map_to_world((width, height), render_height),
        map_to_world((width, 0), render_height),
    ]
    mesh = bpy.data.meshes.new(name + "_Data")
    mesh.from_pydata(corners, [], [(0, 1, 2, 3)])
    mesh.update()
    uv_layer = mesh.uv_layers.new(name=name + "_UV")
    uvs = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    for loop in mesh.loops:
        uv_layer.data[loop.index].uv = uvs[loop.vertex_index]

    material = bpy.data.materials.new(name + "_Material")
    material.use_nodes = True
    material.diffuse_color = highlight_color or (1.0, 1.0, 1.0, 0.55)
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    mix = nodes.new("ShaderNodeMixShader")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    emission = nodes.new("ShaderNodeEmission")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Closest"
    material.node_tree.links.new(transparent.outputs[0], mix.inputs[1])
    material.node_tree.links.new(emission.outputs[0], mix.inputs[2])
    material.node_tree.links.new(mix.outputs[0], output.inputs[0])
    if highlight_color:
        grayscale = nodes.new("ShaderNodeRGBToBW")
        threshold = nodes.new("ShaderNodeMath")
        threshold.operation = "LESS_THAN"
        threshold.inputs[1].default_value = 0.25
        emission.inputs[0].default_value = highlight_color
        if emission.inputs.get("Strength"):
            emission.inputs["Strength"].default_value = 2.0
        material.node_tree.links.new(texture.outputs[0], grayscale.inputs[0])
        material.node_tree.links.new(grayscale.outputs[0], threshold.inputs[0])
        material.node_tree.links.new(threshold.outputs[0], mix.inputs[0])
    else:
        mix.inputs[0].default_value = 0.55
        material.node_tree.links.new(texture.outputs[0], emission.inputs[0])

    overlay = bpy.data.objects.new(name, mesh)
    collection.objects.link(overlay)
    mesh.materials.append(material)
    overlay.hide_render = not render_visible
    overlay["source_path"] = image_path
    overlay["resolution_m_per_pixel"] = resolution
    overlay["alignment"] = alignment
    overlay["render_height_m"] = render_height
    overlay["render_visible"] = render_visible
    overlay.show_in_front = True

    return overlay


