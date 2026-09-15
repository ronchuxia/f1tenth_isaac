import bpy
import math
import os
import sys
from pathlib import Path
from mathutils import Vector


SCRIPT_DIR = os.path.dirname(__file__)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import race_atrium_common as common


PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
BLENDER_OUTPUT_DIR = PROJECT_ROOT + "/blender"
RENDER_OUTPUT_DIR = BLENDER_OUTPUT_DIR + "/renders"
MAP_OVERLAY_PATH = PROJECT_ROOT + "/maps/hallway.pgm"
VIDEO_PATH = PROJECT_ROOT + "/blender/references/16663 lab5 pure pursuit.mov"
PREVIEW_PATH = RENDER_OUTPUT_DIR + "/tepper_hallway_preview.png"

MAP_RESOLUTION = 0.05
MAP_ANCHOR_PIXEL = (850.0, 350.0)

CEILING_HEIGHT = 3.20
LOCKER_BANK_WIDTH = 1.10
LOCKER_HEIGHT = 2.35

SHORT_ROOM_CORRIDORS = (
    {
        "name": "Tepper_Short_Room_Corridor_01",
        "outline": (
            (-25.95, 1.00),
            (-25.90, 2.00),
            (-23.90, 2.00),
            (-23.85, 1.05),
        ),
    },
    {
        "name": "Tepper_Short_Room_Corridor_02",
        "outline": (
            (-22.30, 1.10),
            (-22.20, 2.70),
            (-20.25, 2.75),
            (-20.15, 1.20),
        ),
    },
)

ELEVATOR_ENTRANCES = (
    {
        "name": "Tepper_Elevator_Entrance_01",
        "outline": (
            (-12.25, -0.55),
            (-12.20, -1.10),
            (-11.15, -1.10),
            (-11.10, -0.50),
        ),
    },
    {
        "name": "Tepper_Elevator_Entrance_02",
        "outline": (
            (-9.40, -0.40),
            (-9.35, -0.95),
            (-8.30, -0.90),
            (-8.25, -0.35),
        ),
    },
    {
        "name": "Tepper_Elevator_Entrance_03",
        "outline": (
            (-6.60, -0.25),
            (-6.50, -0.80),
            (-5.40, -0.80),
            (-5.35, -0.20),
        ),
    },
)

WALL_PROTRUSION_CENTER = (5.78, 4.03)
WALL_PROTRUSION_SIZE = (2.05, 1.65)
WALL_PROTRUSION_ROTATION = math.radians(34.0)
LOBBY_PILLAR_CENTER = (3.875, 3.100)
LOBBY_PILLAR_RADIUS = 0.425
MULTISTREAM_RECYCLING_CENTER = (3.112823, 1.718411)
MULTISTREAM_RECYCLING_LENGTH = 1.23
MULTISTREAM_RECYCLING_WIDTH = 0.65
MULTISTREAM_RECYCLING_HEIGHT_SCALE = 0.70
MULTISTREAM_RECYCLING_ROTATION = math.radians(33.7)
ROBOT_ARM_CENTER = (-0.95, 3.80)
ROBOT_ARM_ROTATION = math.radians(34.0)
ROBOT_GLASS_WALL_START = (-3.10, 2.60)
ROBOT_GLASS_WALL_END = (-0.04, 2.70)
ROBOT_AREA_PILLAR_CENTER = (-3.10, 2.60)
ROBOT_AREA_PILLAR_RADIUS = 0.35
ROBOT_AREA_FLOOR_BACK_Y = 5.20
GLASS_WALL_FRAME_TOP = 2.92
GLASS_DOOR_FRAME_TOP = 2.62
ROOM_DOOR_FRAME_TOP = 2.52
ELEVATOR_FRAME_TOP = 2.74
CORRIDOR_JOIN_OVERLAP = 0.10
DIAGONAL_BLEND_DISTANCE = 0.85
DIAGONAL_BLEND_SAMPLES = 16
LOCKER_WEST_BLEND_DISTANCE = 0.85
LOCKER_WEST_BLEND_SAMPLES = 16
WEST_GLASS_WALL_START = (-39.75, 0.425)
WEST_GLASS_WALL_END = (-37.25, 0.523)
CORRIDOR_GLASS_DOOR_START = (-17.75, 1.288)
CORRIDOR_GLASS_DOOR_END = (-16.85, 1.306)
MIDDLE_GLASS_WALL_START = (-9.10, 1.799)
MAPPED_WHITE_WALL_CENTERLINE = (
    (-6.60, 1.95),
    (-6.55, 2.45),
    (-3.55, 3.30),
    (-3.35, 2.60),
)
MIDDLE_GLASS_WALL_END = MAPPED_WHITE_WALL_CENTERLINE[0]
CHANGING_ROOM_FRONTAGE_X_RANGE = (1.65, 10.10)
CHANGING_ROOM_FRONTAGE_START = (1.65, 15.21)
CHANGING_ROOM_FRONTAGE_ANGLE = math.radians(3.0)
CHANGING_ROOM_FRONTAGE_END = (
    CHANGING_ROOM_FRONTAGE_X_RANGE[1],
    CHANGING_ROOM_FRONTAGE_START[1]
    + (
        CHANGING_ROOM_FRONTAGE_X_RANGE[1]
        - CHANGING_ROOM_FRONTAGE_START[0]
    )
    * math.tan(CHANGING_ROOM_FRONTAGE_ANGLE),
)
CHANGING_ROOM_BACK_Y = 17.35
CHANGING_ROOM_WIDTH = 1.40
CHANGING_ROOM_DOOR_HALF_OPENING = 0.57
CHANGING_ROOMS = (
    {
        "name": "Tepper_Changing_Room_01",
        "door_center_x": 5.50,
        "door_open_angle_degrees": 0.0,
        "door_hinge_side": "RIGHT",
    },
    {
        "name": "Tepper_Changing_Room_02",
        "door_center_x": 7.15,
        "door_open_angle_degrees": 83.0,
        "door_hinge_side": "RIGHT",
    },
    {
        "name": "Tepper_Changing_Room_03",
        "door_center_x": 8.80,
        "door_open_angle_degrees": 87.0,
        "door_hinge_side": "RIGHT",
    },
)
CHANGING_ROOM_STOOL_CENTERS = (
    (6.85, 16.65),
    (9.075, 16.90),
)
CHANGING_ROOM_STOOL_RADIUS = 0.30
CHANGING_ROOM_STOOL_HEIGHT = 0.45
NORTH_ENCLOSURE_WALLS = (
    {
        "name": "Tepper_North_West_Enclosure_Wall",
        "centerline": (
            (-0.85, CHANGING_ROOM_BACK_Y),
            (1.65, CHANGING_ROOM_BACK_Y),
            CHANGING_ROOM_FRONTAGE_START,
        ),
    },
    {
        "name": "Tepper_North_East_Enclosure_Wall",
        "centerline": (
            CHANGING_ROOM_FRONTAGE_END,
            (10.10, CHANGING_ROOM_BACK_Y),
            (12.25, CHANGING_ROOM_BACK_Y),
        ),
    },
)


def changing_room_frontage_point(x, normal_offset=0.0):
    start_x, start_y = CHANGING_ROOM_FRONTAGE_START
    end_x, end_y = CHANGING_ROOM_FRONTAGE_END
    parameter = (x - start_x) / (end_x - start_x)
    y = start_y + parameter * (end_y - start_y)
    return (
        x - math.sin(CHANGING_ROOM_FRONTAGE_ANGLE) * normal_offset,
        y + math.cos(CHANGING_ROOM_FRONTAGE_ANGLE) * normal_offset,
    )

LOCKER_BANKS = (
    {
        "name": "Locker_Bank_01",
        "center": (2.300, 9.763),
        "length": 8.044,
        "width": 1.151,
        "count": 26,
        "rotation_degrees": 3.922,
    },
    {
        "name": "Locker_Bank_02",
        "center": (4.913, 10.350),
        "length": 7.116,
        "width": 1.176,
        "count": 23,
        "rotation_degrees": 3.828,
    },
    {
        "name": "Locker_Bank_03",
        "center": (7.638, 10.975),
        "length": 6.159,
        "width": 1.176,
        "count": 20,
        "rotation_degrees": 3.026,
    },
    {
        "name": "Locker_Bank_04",
        "center": (10.363, 11.563),
        "length": 5.230,
        "width": 1.226,
        "count": 17,
        "rotation_degrees": 2.466,
    },
)

REFERENCE_VIDEO_FPS = 24
REFERENCE_VIDEO_FRAME_COUNT = 1061
CAMERA_TRAJECTORY_FPS = 60
CAMERA_TRAJECTORY_END_FRAME = 2351
CAMERA_TRAJECTORY_LOOK_DISTANCE = 5.0
CAMERA_TRAJECTORY_LOOK_HEIGHT = 0.65
CAMERA_TRAJECTORY_KEYFRAMES = (
    (1, "Corridor start", (-38.50, -0.55, 1.55)),
    (213, "Corridor west", (-29.00, -0.20, 1.55)),
    (425, "Corridor middle", (-18.00, 0.10, 1.55)),
    (594, "Corridor east", (-9.00, 0.55, 1.55)),
    (721, "Approach locker turn", (-3.20, 1.05, 1.55)),
    (841, "Locker turn entry", (-0.30, 1.45, 1.55)),
    (931, "Turn left into lockers", (0.55, 3.15, 1.55)),
    (1021, "West locker aisle", (0.70, 6.00, 1.55)),
    (1261, "Approach changing rooms", (0.80, 12.80, 1.55)),
    (1381, "Turn right at changing rooms", (1.55, 14.30, 1.55)),
    (1561, "Pass changing rooms", (6.00, 14.65, 1.55)),
    (1711, "Approach last locker", (10.45, 14.75, 1.55)),
    (1801, "Turn right at last locker", (11.60, 13.65, 1.55)),
    (1951, "East locker aisle", (11.60, 9.20, 1.55)),
    (1981, "Last locker south end", (11.55, 8.55, 1.55)),
    (2041, "Turn right toward lobby", (10.40, 8.15, 1.55)),
    (2161, "Cross locker lobby", (7.40, 6.20, 1.55)),
    (2206, "Clear wall protrusion east", (6.55, 5.85, 1.55)),
    (2251, "Clear wall protrusion north", (5.00, 5.70, 1.55)),
    (2286, "Pass wall protrusion west", (3.90, 5.05, 1.55)),
    (2316, "Approach pillar", (2.80, 4.10, 1.55)),
    (2331, "Pass pillar and recycling", (2.40, 3.45, 1.55)),
    (2351, "Finish at corner", (0.65, 3.05, 1.55)),
)
CAMERA_TRAJECTORY_LOOK_DIRECTIONS = (
    (1.00, 0.00),
    (1.00, 0.00),
    (1.00, 0.00),
    (1.00, 0.00),
    (1.00, 0.00),
    (0.85, 0.35),
    (0.25, 1.00),
    (0.00, 1.00),
    (0.00, 1.00),
    (0.45, 0.90),
    (1.00, 0.10),
    (1.00, 0.00),
    (0.15, -1.00),
    (0.00, -1.00),
    (0.00, -1.00),
    (-0.95, -0.20),
    (-0.85, -0.50),
    (-1.00, -0.30),
    (-1.00, -0.20),
    (-0.87, -0.50),
    (-0.87, -0.50),
    (-0.87, -0.50),
    (-0.87, -0.50),
)


def map_to_world(point, z):
    return (
        (point[0] - MAP_ANCHOR_PIXEL[0]) * MAP_RESOLUTION,
        (MAP_ANCHOR_PIXEL[1] - point[1]) * MAP_RESOLUTION,
        z,
    )


def clear_scene():
    scene = bpy.context.scene
    for view_layer in list(scene.view_layers)[1:]:
        scene.view_layers.remove(view_layer)
    scene.view_layers[0].name = "ViewLayer"
    for child in list(scene.collection.children):
        common.remove_collection(child)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def make_glass_material(name, color):
    material = common.make_material(name, color, roughness=0.12)
    material.diffuse_color = color
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        transmission = (
            bsdf.inputs.get("Transmission Weight")
            or bsdf.inputs.get("Transmission")
        )
        if transmission:
            transmission.default_value = 0.65
        alpha = bsdf.inputs.get("Alpha")
        if alpha:
            alpha.default_value = color[3]
        ior = bsdf.inputs.get("IOR")
        if ior:
            ior.default_value = 1.45
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    return material


def add_noise_bump(material, scale, strength, distance):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    texture = nodes.new("ShaderNodeTexNoise")
    texture.inputs["Scale"].default_value = scale
    texture.inputs["Detail"].default_value = 4.0
    texture.inputs["Roughness"].default_value = 0.72
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = distance
    links.new(texture.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def build_materials():
    materials = {
        "concrete": common.make_material(
            "Tepper_Polished_Concrete",
            (0.32, 0.30, 0.27, 1.0),
            roughness=0.24,
        ),
        "wall": common.make_material(
            "Tepper_Warm_White_Wall",
            (0.78, 0.77, 0.73, 1.0),
            roughness=0.62,
        ),
        "ceiling": common.make_material(
            "Tepper_White_Ceiling",
            (0.90, 0.90, 0.87, 1.0),
            roughness=0.74,
            emission=(0.04, 0.04, 0.035, 1.0),
        ),
        "baseboard": common.make_material(
            "Tepper_White_Baseboard",
            (0.90, 0.90, 0.88, 1.0),
            roughness=0.38,
        ),
        "maple": common.make_material(
            "Tepper_Maple_Lockers",
            (0.66, 0.47, 0.28, 1.0),
            roughness=0.42,
        ),
        "maple_edge": common.make_material(
            "Tepper_Maple_Edges",
            (0.48, 0.30, 0.16, 1.0),
            roughness=0.48,
        ),
        "aluminum": common.make_material(
            "Tepper_Brushed_Aluminum",
            (0.42, 0.46, 0.49, 1.0),
            roughness=0.26,
            metallic=0.72,
        ),
        "elevator": common.make_material(
            "Tepper_Elevator_Dark_Metal",
            (0.19, 0.20, 0.20, 1.0),
            roughness=0.34,
            metallic=0.58,
        ),
        "lock_red": common.make_material(
            "Tepper_Padlock_Red",
            (0.50, 0.025, 0.018, 1.0),
            roughness=0.34,
            metallic=0.15,
        ),
        "black": common.make_material(
            "Tepper_Car_Black",
            (0.018, 0.022, 0.026, 1.0),
            roughness=0.44,
        ),
        "orange": common.make_material(
            "Tepper_Lidar_Orange",
            (0.86, 0.18, 0.018, 1.0),
            roughness=0.38,
        ),
        "blue_emission": common.make_material(
            "Tepper_Controller_Blue",
            (0.02, 0.12, 0.36, 1.0),
            roughness=0.28,
            emission=(0.02, 0.18, 1.0, 1.0),
        ),
        "bin_gray": common.make_material(
            "Tepper_Trash_Gray",
            (0.24, 0.27, 0.28, 1.0),
            roughness=0.55,
        ),
        "bin_blue": common.make_material(
            "Tepper_Recycling_Blue",
            (0.02, 0.16, 0.42, 1.0),
            roughness=0.48,
        ),
        "kiosk": common.make_material(
            "Tepper_Kiosk_Charcoal",
            (0.11, 0.105, 0.10, 1.0),
            roughness=0.40,
        ),
        "feature_red": common.make_material(
            "Tepper_Feature_Red",
            (0.46, 0.012, 0.018, 1.0),
            roughness=0.36,
        ),
        "light": common.make_material(
            "Tepper_LED_Emission",
            (1.0, 0.93, 0.82, 1.0),
            roughness=0.20,
            emission=(1.0, 0.93, 0.82, 1.0),
        ),
    }
    materials["metal"] = materials["aluminum"]
    materials["glass"] = make_glass_material(
        "Tepper_Glass",
        (0.28, 0.42, 0.44, 0.24),
    )
    add_noise_bump(materials["concrete"], 7.0, 0.13, 0.035)
    add_noise_bump(materials["maple"], 3.4, 0.10, 0.025)
    return materials


def add_prism(name, outline, height, material, collection, bottom_z=-0.08):
    top_z = bottom_z + height
    count = len(outline)
    vertices = [(x, y, bottom_z) for x, y in outline]
    vertices.extend((x, y, top_z) for x, y in outline)
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for index in range(count):
        following = (index + 1) % count
        faces.append((
            index,
            following,
            following + count,
            index + count,
        ))
    mesh = bpy.data.meshes.new(name + "_Data")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(material)
    return obj


def add_centerline_prism(
    name,
    centerline,
    height,
    thickness,
    material,
    collection,
    bottom_z=0.0,
    smooth_sides=True,
):
    points = [Vector(point) for point in centerline]
    directions = [
        (points[index + 1] - points[index]).normalized()
        for index in range(len(points) - 1)
    ]
    normals = [Vector((-direction.y, direction.x)) for direction in directions]
    half_thickness = thickness * 0.5
    left_side = []
    right_side = []
    for index, point in enumerate(points):
        if index == 0:
            offset = normals[0] * half_thickness
        elif index == len(points) - 1:
            offset = normals[-1] * half_thickness
        else:
            miter = normals[index - 1] + normals[index]
            if miter.length < 1.0e-6:
                offset = normals[index] * half_thickness
            else:
                miter.normalize()
                denominator = max(1.0e-6, miter.dot(normals[index]))
                offset = miter * (half_thickness / denominator)
        left_side.append(tuple(point + offset))
        right_side.append(tuple(point - offset))
    outline = tuple(left_side + list(reversed(right_side)))
    obj = add_prism(
        name,
        outline,
        height,
        material,
        collection,
        bottom_z=bottom_z,
    )
    if smooth_sides:
        for polygon in obj.data.polygons:
            if abs(polygon.normal.z) < 0.5:
                polygon.use_smooth = True
    return obj


def build_blended_centerline(
    start,
    joint,
    end,
    blend_distance,
    sample_count,
):
    start = Vector(start)
    joint = Vector(joint)
    end = Vector(end)
    incoming = (joint - start).normalized()
    outgoing = (end - joint).normalized()
    blend_start = joint - incoming * blend_distance
    blend_end = joint + outgoing * blend_distance
    angle = math.acos(max(-1.0, min(1.0, incoming.dot(outgoing))))
    if angle < 1.0e-6:
        handle_length = blend_distance * 2.0 / 3.0
    else:
        radius = blend_distance / math.tan(angle * 0.5)
        handle_length = (
            4.0
            / 3.0
            * radius
            * math.tan(angle * 0.25)
        )
    control_1 = blend_start + incoming * handle_length
    control_2 = blend_end - outgoing * handle_length
    curve_points = []
    for index in range(sample_count + 1):
        parameter = index / sample_count
        inverse = 1.0 - parameter
        point = (
            blend_start * inverse ** 3
            + control_1 * 3.0 * inverse ** 2 * parameter
            + control_2 * 3.0 * inverse * parameter ** 2
            + blend_end * parameter ** 3
        )
        curve_points.append(tuple(point))
    return (tuple(start), *curve_points, tuple(end))


def add_segment_box(
    name,
    start,
    end,
    height,
    thickness,
    material,
    collection,
    bottom_z=0.0,
    bevel=0.012,
    start_extension=0.0,
    end_extension=0.0,
):
    start_vector = Vector(start)
    end_vector = Vector(end)
    delta = end_vector - start_vector
    direction = delta.normalized()
    start_vector -= direction * start_extension
    end_vector += direction * end_extension
    delta = end_vector - start_vector
    length = delta.length
    midpoint = (start_vector + end_vector) * 0.5
    return common.add_box(
        name,
        (midpoint.x, midpoint.y, bottom_z + height * 0.5),
        (length, thickness, height),
        material,
        collection,
        bevel=bevel,
        rotation_z=math.atan2(delta.y, delta.x),
    )


def join_mesh_objects(objects, name):
    mesh_objects = [obj for obj in objects if obj and obj.type == "MESH"]
    if not mesh_objects:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for obj in mesh_objects:
        obj.select_set(True)
    joined = mesh_objects[0]
    bpy.context.view_layer.objects.active = joined
    bpy.ops.object.join()
    joined.name = name
    joined.data.name = name + "_Data"
    joined["opaque_lidar_surface"] = True
    return joined


def union_mesh_objects(objects, name):
    mesh_objects = [obj for obj in objects if obj and obj.type == "MESH"]
    if not mesh_objects:
        return None
    for obj in mesh_objects:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(
            location=True,
            rotation=True,
            scale=True,
        )
    united = mesh_objects[0]
    for index, obj in enumerate(mesh_objects[1:], start=1):
        bpy.ops.object.select_all(action="DESELECT")
        united.select_set(True)
        bpy.context.view_layer.objects.active = united
        modifier = united.modifiers.new(f"Union_{index:02d}", "BOOLEAN")
        modifier.operation = "UNION"
        modifier.solver = "EXACT"
        modifier.object = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(obj, do_unlink=True)
    united.name = name
    united.data.name = name + "_Data"
    return united


def add_baseboard(
    name,
    start,
    end,
    materials,
    collection,
    bevel=0.012,
    start_extension=0.0,
    end_extension=0.0,
):
    return add_segment_box(
        name,
        start,
        end,
        0.16,
        0.035,
        materials["baseboard"],
        collection,
        bottom_z=0.0,
        bevel=bevel,
        start_extension=start_extension,
        end_extension=end_extension,
    )


def build_concrete_wall(
    name,
    start,
    end,
    materials,
    collection,
    bevel=0.012,
    start_extension=0.0,
    end_extension=0.0,
):
    wall = add_segment_box(
        name,
        start,
        end,
        CEILING_HEIGHT,
        0.16,
        materials["wall"],
        collection,
        bevel=bevel,
        start_extension=start_extension,
        end_extension=end_extension,
    )
    wall["opaque_lidar_surface"] = True
    add_baseboard(
        name + "_Baseboard",
        start,
        end,
        materials,
        collection,
        bevel=bevel,
        start_extension=start_extension,
        end_extension=end_extension,
    )
    return wall


def build_glass_wall(name, start, end, materials, collection, panel_width=2.15):
    start_vector = Vector(start)
    end_vector = Vector(end)
    delta = end_vector - start_vector
    length = delta.length
    direction = delta.normalized()
    angle = math.atan2(delta.y, delta.x)
    panel_count = max(1, math.ceil(length / panel_width))
    actual_panel_width = length / panel_count

    add_segment_box(
        name + "_Glass",
        start,
        end,
        2.72,
        0.035,
        materials["glass"],
        collection,
        bottom_z=0.12,
    )
    add_segment_box(
        name + "_Bottom_Rail",
        start,
        end,
        0.10,
        0.08,
        materials["aluminum"],
        collection,
        bottom_z=0.03,
    )
    add_segment_box(
        name + "_Top_Rail",
        start,
        end,
        0.08,
        0.07,
        materials["aluminum"],
        collection,
        bottom_z=2.84,
    )
    for index in range(panel_count + 1):
        position = start_vector + direction * actual_panel_width * index
        common.add_box(
            name + f"_Mullion_{index:02d}",
            (position.x, position.y, 1.50),
            (0.055, 0.075, 2.92),
            materials["aluminum"],
            collection,
            bevel=0.006,
            rotation_z=angle,
        )
    upper_wall = add_segment_box(
        name + "_Upper_Wall",
        start,
        end,
        CEILING_HEIGHT - GLASS_WALL_FRAME_TOP,
        0.16,
        materials["wall"],
        collection,
        bottom_z=GLASS_WALL_FRAME_TOP,
        bevel=0.0,
    )
    upper_wall["opaque_lidar_surface"] = True
    return upper_wall


def build_glass_door(name, start, end, materials, collection):
    start_vector = Vector(start)
    end_vector = Vector(end)
    delta = end_vector - start_vector
    direction = delta.normalized()
    angle = math.atan2(delta.y, delta.x)

    add_segment_box(
        name + "_Glass",
        start,
        end,
        2.42,
        0.032,
        materials["glass"],
        collection,
        bottom_z=0.12,
    )
    add_segment_box(
        name + "_Bottom_Rail",
        start,
        end,
        0.10,
        0.08,
        materials["aluminum"],
        collection,
        bottom_z=0.03,
    )
    add_segment_box(
        name + "_Top_Rail",
        start,
        end,
        0.08,
        0.08,
        materials["aluminum"],
        collection,
        bottom_z=2.54,
    )
    for index, point in enumerate((start_vector, end_vector), start=1):
        common.add_box(
            name + f"_Jamb_{index}",
            (point.x, point.y, GLASS_DOOR_FRAME_TOP * 0.5),
            (0.065, 0.085, GLASS_DOOR_FRAME_TOP),
            materials["aluminum"],
            collection,
            bevel=0.006,
            rotation_z=angle,
        )

    handle_point = start_vector + direction * delta.length * 0.68
    common.add_box(
        name + "_Handle",
        (handle_point.x, handle_point.y, 1.10),
        (0.035, 0.13, 0.28),
        materials["aluminum"],
        collection,
        bevel=0.010,
        rotation_z=angle,
    )
    upper_wall = add_segment_box(
        name + "_Upper_Wall",
        start,
        end,
        CEILING_HEIGHT - GLASS_DOOR_FRAME_TOP,
        0.16,
        materials["wall"],
        collection,
        bottom_z=GLASS_DOOR_FRAME_TOP,
        bevel=0.0,
    )
    upper_wall["opaque_lidar_surface"] = True
    return upper_wall


def build_corridor_door(
    name,
    center,
    materials,
    collection,
    rotation_z=0.0,
    open_angle_degrees=0.0,
    hinge_side="LEFT",
):
    x, y = center
    cosine = math.cos(rotation_z)
    sine = math.sin(rotation_z)

    def local_to_world(local_x, local_y, z):
        return (
            x + local_x * cosine - local_y * sine,
            y + local_x * sine + local_y * cosine,
            z,
        )

    if hinge_side not in {"LEFT", "RIGHT"}:
        raise ValueError(f"Unsupported door hinge side: {hinge_side}")
    hinge_direction = 1.0 if hinge_side == "LEFT" else -1.0
    open_angle = math.radians(open_angle_degrees) * hinge_direction
    open_cosine = math.cos(open_angle)
    open_sine = math.sin(open_angle)
    hinge_x = -0.49 * hinge_direction
    panel_center_x = hinge_x + hinge_direction * 0.49 * open_cosine
    panel_center_y = hinge_direction * 0.49 * open_sine

    common.add_box(
        name,
        local_to_world(panel_center_x, panel_center_y, 1.22),
        (0.98, 0.07, 2.44),
        materials["maple"],
        collection,
        bevel=0.018,
        rotation_z=rotation_z + open_angle,
    )
    for side in (-0.53, 0.53):
        common.add_box(
            name + f"_Frame_{side:+.2f}",
            local_to_world(side, 0.0, 1.25),
            (0.08, 0.10, 2.50),
            materials["aluminum"],
            collection,
            bevel=0.008,
            rotation_z=rotation_z,
        )
    common.add_box(
        name + "_Frame_Top",
        local_to_world(0.0, 0.0, 2.48),
        (1.14, 0.10, 0.08),
        materials["aluminum"],
        collection,
        bevel=0.008,
        rotation_z=rotation_z,
    )
    handle_from_hinge_x = hinge_direction * 0.82
    handle_from_hinge_y = -0.055
    handle_x = (
        hinge_x + handle_from_hinge_x * open_cosine
        - handle_from_hinge_y * open_sine
    )
    handle_y = (
        handle_from_hinge_x * open_sine
        + handle_from_hinge_y * open_cosine
    )
    common.add_box(
        name + "_Handle",
        local_to_world(handle_x, handle_y, 1.05),
        (0.04, 0.12, 0.16),
        materials["aluminum"],
        collection,
        bevel=0.012,
        rotation_z=rotation_z + open_angle,
    )


def build_short_room_corridor(specification, materials, collection):
    name = specification["name"]
    root_left, back_left, back_right, root_right = specification["outline"]
    root_left_vector = Vector(root_left)
    back_left_vector = Vector(back_left)
    back_right_vector = Vector(back_right)
    root_right_vector = Vector(root_right)
    connected_root_left = root_left_vector - (
        back_left_vector - root_left_vector
    ).normalized() * CORRIDOR_JOIN_OVERLAP
    connected_root_right = root_right_vector - (
        back_right_vector - root_right_vector
    ).normalized() * CORRIDOR_JOIN_OVERLAP
    connected_outline = (
        tuple(connected_root_left),
        back_left,
        back_right,
        tuple(connected_root_right),
    )
    floor = add_prism(
        name + "_Floor",
        connected_outline,
        0.10,
        materials["concrete"],
        collection,
    )
    ceiling = add_prism(
        name + "_Ceiling",
        connected_outline,
        0.12,
        materials["ceiling"],
        collection,
        bottom_z=CEILING_HEIGHT,
    )
    left_wall = build_concrete_wall(
        name + "_Left_Wall",
        root_left,
        back_left,
        materials,
        collection,
        bevel=0.0,
        start_extension=CORRIDOR_JOIN_OVERLAP,
        end_extension=CORRIDOR_JOIN_OVERLAP,
    )
    right_wall = build_concrete_wall(
        name + "_Right_Wall",
        back_right,
        root_right,
        materials,
        collection,
        bevel=0.0,
        start_extension=CORRIDOR_JOIN_OVERLAP,
        end_extension=CORRIDOR_JOIN_OVERLAP,
    )

    back_delta = back_right_vector - back_left_vector
    back_direction = back_delta.normalized()
    back_center = (back_left_vector + back_right_vector) * 0.5
    door_half_width = min(0.57, back_delta.length * 0.38)
    door_left = back_center - back_direction * door_half_width
    door_right = back_center + back_direction * door_half_width
    back_wall_left = build_concrete_wall(
        name + "_Back_Wall_Left",
        back_left,
        tuple(door_left),
        materials,
        collection,
        bevel=0.0,
        start_extension=CORRIDOR_JOIN_OVERLAP,
    )
    back_wall_right = build_concrete_wall(
        name + "_Back_Wall_Right",
        tuple(door_right),
        back_right,
        materials,
        collection,
        bevel=0.0,
        end_extension=CORRIDOR_JOIN_OVERLAP,
    )
    door_upper_wall = add_segment_box(
        name + "_Back_Wall_Upper",
        tuple(door_left),
        tuple(door_right),
        CEILING_HEIGHT - ROOM_DOOR_FRAME_TOP,
        0.16,
        materials["wall"],
        collection,
        bottom_z=ROOM_DOOR_FRAME_TOP,
        bevel=0.0,
        start_extension=CORRIDOR_JOIN_OVERLAP,
        end_extension=CORRIDOR_JOIN_OVERLAP,
    )
    door_upper_wall["opaque_lidar_surface"] = True
    connected_back_wall = join_mesh_objects(
        (back_wall_left, door_upper_wall, back_wall_right),
        name + "_Connected_Back_Wall",
    )
    build_corridor_door(
        name + "_Room_Door",
        tuple(back_center),
        materials,
        collection,
        rotation_z=math.atan2(back_delta.y, back_delta.x),
    )
    return {
        "floor": floor,
        "ceiling": ceiling,
        "walls": (left_wall, connected_back_wall, right_wall),
    }


def build_elevator_entrance(specification, materials, collection):
    name = specification["name"]
    root_left, back_left, back_right, root_right = specification["outline"]
    root_left_vector = Vector(root_left)
    back_left_vector = Vector(back_left)
    back_right_vector = Vector(back_right)
    root_right_vector = Vector(root_right)
    connected_root_left = root_left_vector - (
        back_left_vector - root_left_vector
    ).normalized() * CORRIDOR_JOIN_OVERLAP
    connected_root_right = root_right_vector - (
        back_right_vector - root_right_vector
    ).normalized() * CORRIDOR_JOIN_OVERLAP
    connected_outline = (
        tuple(connected_root_left),
        back_left,
        back_right,
        tuple(connected_root_right),
    )
    floor = add_prism(
        name + "_Floor",
        connected_outline,
        0.10,
        materials["concrete"],
        collection,
    )
    ceiling = add_prism(
        name + "_Ceiling",
        connected_outline,
        0.12,
        materials["ceiling"],
        collection,
        bottom_z=CEILING_HEIGHT,
    )
    left_return_wall = build_concrete_wall(
        name + "_Left_Return_Wall",
        root_left,
        back_left,
        materials,
        collection,
        bevel=0.0,
        start_extension=CORRIDOR_JOIN_OVERLAP,
        end_extension=CORRIDOR_JOIN_OVERLAP,
    )
    right_return_wall = build_concrete_wall(
        name + "_Right_Return_Wall",
        back_right,
        root_right,
        materials,
        collection,
        bevel=0.0,
        start_extension=CORRIDOR_JOIN_OVERLAP,
        end_extension=CORRIDOR_JOIN_OVERLAP,
    )

    back_delta = back_right_vector - back_left_vector
    back_center = (back_left_vector + back_right_vector) * 0.5
    back_angle = math.atan2(back_delta.y, back_delta.x)
    upper_wall = add_segment_box(
        name + "_Upper_Wall",
        back_left,
        back_right,
        CEILING_HEIGHT - ELEVATOR_FRAME_TOP,
        0.16,
        materials["wall"],
        collection,
        bottom_z=ELEVATOR_FRAME_TOP,
        bevel=0.0,
        start_extension=CORRIDOR_JOIN_OVERLAP,
        end_extension=CORRIDOR_JOIN_OVERLAP,
    )
    upper_wall["opaque_lidar_surface"] = True
    connected_wall = join_mesh_objects(
        (left_return_wall, upper_wall, right_return_wall),
        name + "_Connected_Wall",
    )
    add_segment_box(
        name + "_Door",
        back_left,
        back_right,
        2.60,
        0.08,
        materials["elevator"],
        collection,
        bottom_z=0.04,
    )
    for index, point in enumerate((back_left_vector, back_right_vector)):
        common.add_box(
            name + f"_Frame_Jamb_{index + 1}",
            (point.x, point.y, 1.36),
            (0.11, 0.14, 2.72),
            materials["aluminum"],
            collection,
            bevel=0.008,
            rotation_z=back_angle,
        )
    common.add_box(
        name + "_Frame_Header",
        (back_center.x, back_center.y, 2.69),
        (back_delta.length + 0.11, 0.14, 0.10),
        materials["aluminum"],
        collection,
        bevel=0.008,
        rotation_z=back_angle,
    )
    common.add_box(
        name + "_Door_Seam",
        (back_center.x, back_center.y, 1.34),
        (0.016, 0.09, 2.60),
        materials["aluminum"],
        collection,
        bevel=0.003,
        rotation_z=back_angle,
    )
    return {
        "floor": floor,
        "ceiling": ceiling,
        "walls": (connected_wall,),
    }


def build_wall_protrusion(materials, collection):
    center_x, center_y = WALL_PROTRUSION_CENTER
    length, width = WALL_PROTRUSION_SIZE
    wall = common.add_box(
        "Tepper_Lobby_Wall_Protrusion",
        (center_x, center_y, CEILING_HEIGHT * 0.5),
        (length, width, CEILING_HEIGHT),
        materials["wall"],
        collection,
        bevel=0.012,
        rotation_z=WALL_PROTRUSION_ROTATION,
    )
    wall["opaque_lidar_surface"] = True

    cosine = math.cos(WALL_PROTRUSION_ROTATION)
    sine = math.sin(WALL_PROTRUSION_ROTATION)

    def local_to_world(local_x, local_y):
        return (
            center_x + local_x * cosine - local_y * sine,
            center_y + local_x * sine + local_y * cosine,
        )

    corners = (
        local_to_world(-length * 0.5, -width * 0.5),
        local_to_world(length * 0.5, -width * 0.5),
        local_to_world(length * 0.5, width * 0.5),
        local_to_world(-length * 0.5, width * 0.5),
    )
    for index in range(len(corners)):
        add_baseboard(
            f"Tepper_Lobby_Wall_Protrusion_Baseboard_{index + 1}",
            corners[index],
            corners[(index + 1) % len(corners)],
            materials,
            collection,
        )
    return wall


def build_changing_rooms(parent, materials):
    collection = common.create_collection("Tepper_Changing_Rooms", parent)
    for specification in CHANGING_ROOMS:
        name = specification["name"]
        room_center_x = specification["door_center_x"]
        left_x = room_center_x - CHANGING_ROOM_WIDTH * 0.5
        right_x = room_center_x + CHANGING_ROOM_WIDTH * 0.5
        back_y = CHANGING_ROOM_BACK_Y
        walls = (
            build_concrete_wall(
                name + "_Left_Wall",
                changing_room_frontage_point(left_x),
                (left_x, back_y),
                materials,
                collection,
                bevel=0.0,
                start_extension=CORRIDOR_JOIN_OVERLAP,
                end_extension=CORRIDOR_JOIN_OVERLAP,
            ),
            build_concrete_wall(
                name + "_Back_Wall",
                (left_x, back_y),
                (right_x, back_y),
                materials,
                collection,
                bevel=0.0,
                start_extension=CORRIDOR_JOIN_OVERLAP,
                end_extension=CORRIDOR_JOIN_OVERLAP,
            ),
            build_concrete_wall(
                name + "_Right_Wall",
                (right_x, back_y),
                changing_room_frontage_point(right_x),
                materials,
                collection,
                bevel=0.0,
                start_extension=CORRIDOR_JOIN_OVERLAP,
                end_extension=CORRIDOR_JOIN_OVERLAP,
            ),
        )
        join_mesh_objects(walls, name + "_Connected_Walls")

    for index, center in enumerate(CHANGING_ROOM_STOOL_CENTERS, start=1):
        stool = common.add_cylinder(
            f"Tepper_Changing_Room_Stool_{index:02d}",
            (
                center[0],
                center[1],
                CHANGING_ROOM_STOOL_HEIGHT * 0.5,
            ),
            CHANGING_ROOM_STOOL_RADIUS,
            CHANGING_ROOM_STOOL_HEIGHT,
            materials["kiosk"],
            collection,
            vertices=64,
        )
        stool["opaque_lidar_surface"] = True
        for polygon in stool.data.polygons:
            if abs(polygon.normal.z) < 0.5:
                polygon.use_smooth = True
        bevel = stool.modifiers.new("Rounded stool edges", "BEVEL")
        bevel.width = 0.035
        bevel.segments = 3

    return collection


def build_north_enclosure_walls(parent, materials):
    collection = common.create_collection(
        "Tepper_North_Enclosure_Walls",
        parent,
    )
    for specification in NORTH_ENCLOSURE_WALLS:
        name = specification["name"]
        centerline = specification["centerline"]
        wall = add_centerline_prism(
            name,
            centerline,
            CEILING_HEIGHT,
            0.16,
            materials["wall"],
            collection,
            smooth_sides=False,
        )
        wall["opaque_lidar_surface"] = True
        add_centerline_prism(
            name + "_Baseboard",
            centerline,
            0.16,
            0.035,
            materials["baseboard"],
            collection,
            smooth_sides=False,
        )
    return collection


def build_floor_and_architecture(collection, materials):
    corridor_north_west = ((-40.00, 0.415), (-17.65, 1.292))
    corridor_north_east = ((-17.15, 1.287), MAPPED_WHITE_WALL_CENTERLINE[0])
    corridor_north_tail = (MAPPED_WHITE_WALL_CENTERLINE[-1], (0.20, 2.892))
    corridor_south_west = ((-40.00, -1.636), (-17.60, -0.961))
    corridor_south_east = ((-17.50, -0.919), (-2.50, -0.051))
    corridor_south_tail = ((-2.50, -0.062), (-0.50, 0.011))

    corridor_outline = [
        corridor_south_west[0],
        corridor_south_west[1],
        corridor_south_east[0],
        corridor_south_east[1],
        corridor_south_tail[0],
        corridor_south_tail[1],
        corridor_north_tail[1],
        corridor_north_tail[0],
        MAPPED_WHITE_WALL_CENTERLINE[2],
        MAPPED_WHITE_WALL_CENTERLINE[1],
        MAPPED_WHITE_WALL_CENTERLINE[0],
        corridor_north_east[0],
        corridor_north_west[1],
        corridor_north_west[0],
    ]
    room_outline = [
        (-0.50, 0.011),
        (1.30, 0.345),
        (5.15, 2.948),
        (18.10, 9.250),
        (12.70, 9.700),
        (12.25, 17.500),
        (12.25, CHANGING_ROOM_BACK_Y),
        (-0.85, CHANGING_ROOM_BACK_Y),
        (-0.85, 16.550),
        (-0.04, 6.000),
        (-0.04, 2.700),
        (0.20, 2.892),
    ]
    side_corridor_outline = [
        (-0.50, 0.011),
        (-0.05, -7.400),
        (1.75, -7.150),
        (1.30, 0.345),
    ]
    robot_area_floor_outline = [
        ROBOT_GLASS_WALL_START,
        ROBOT_GLASS_WALL_END,
        (ROBOT_GLASS_WALL_END[0], ROBOT_AREA_FLOOR_BACK_Y),
        (ROBOT_GLASS_WALL_START[0], ROBOT_AREA_FLOOR_BACK_Y),
    ]
    corridor_floor = add_prism(
        "Tepper_Corridor_Floor",
        corridor_outline,
        0.10,
        materials["concrete"],
        collection,
    )
    add_prism(
        "Tepper_Locker_Room_Floor",
        room_outline,
        0.10,
        materials["concrete"],
        collection,
    )
    add_prism(
        "Tepper_Side_Corridor_Floor",
        side_corridor_outline,
        0.10,
        materials["concrete"],
        collection,
    )
    add_prism(
        "Tepper_Robot_Area_Floor",
        robot_area_floor_outline,
        0.10,
        materials["concrete"],
        collection,
    )
    corridor_ceiling = add_prism(
        "Tepper_Corridor_Ceiling",
        corridor_outline,
        0.12,
        materials["ceiling"],
        collection,
        bottom_z=CEILING_HEIGHT,
    )
    add_prism(
        "Tepper_Locker_Room_Ceiling",
        room_outline,
        0.12,
        materials["ceiling"],
        collection,
        bottom_z=CEILING_HEIGHT,
    )
    add_prism(
        "Tepper_Side_Corridor_Ceiling",
        side_corridor_outline,
        0.12,
        materials["ceiling"],
        collection,
        bottom_z=CEILING_HEIGHT,
    )
    short_corridor_parts = [
        build_short_room_corridor(specification, materials, collection)
        for specification in SHORT_ROOM_CORRIDORS
    ]
    elevator_parts = [
        build_elevator_entrance(specification, materials, collection)
        for specification in ELEVATOR_ENTRANCES
    ]
    union_mesh_objects(
        [corridor_floor]
        + [part["floor"] for part in short_corridor_parts]
        + [part["floor"] for part in elevator_parts],
        "Tepper_Corridor_Connected_Floor",
    )
    union_mesh_objects(
        [corridor_ceiling]
        + [part["ceiling"] for part in short_corridor_parts]
        + [part["ceiling"] for part in elevator_parts],
        "Tepper_Corridor_Connected_Ceiling",
    )
    short_room_wall_objects = [
        wall
        for part in short_corridor_parts
        for wall in part["walls"]
    ]
    elevator_wall_objects = [
        wall
        for part in elevator_parts
        for wall in part["walls"]
    ]

    west_wall_before_glass = build_concrete_wall(
        "Tepper_Corridor_North_Concrete_West_Before_Glass",
        corridor_north_west[0],
        WEST_GLASS_WALL_START,
        materials,
        collection,
        bevel=0.0,
    )
    west_glass_upper_wall = build_glass_wall(
        "Tepper_Corridor_West_Glass_Wall",
        WEST_GLASS_WALL_START,
        WEST_GLASS_WALL_END,
        materials,
        collection,
        panel_width=0.85,
    )
    west_wall_after_glass = build_concrete_wall(
        "Tepper_Corridor_North_Concrete_West_After_Glass",
        WEST_GLASS_WALL_END,
        (-30.00, 0.807),
        materials,
        collection,
        bevel=0.0,
        end_extension=CORRIDOR_JOIN_OVERLAP,
    )
    west_connected_wall = join_mesh_objects(
        (
            west_wall_before_glass,
            west_glass_upper_wall,
            west_wall_after_glass,
        ),
        "Tepper_Corridor_North_West_Connected_Wall",
    )
    north_wall_segments = (
        ((-30.00, 0.807), SHORT_ROOM_CORRIDORS[0]["outline"][0]),
        (
            SHORT_ROOM_CORRIDORS[0]["outline"][3],
            SHORT_ROOM_CORRIDORS[1]["outline"][0],
        ),
    )
    north_wall_segment_objects = []
    for index, (start, end) in enumerate(north_wall_segments):
        name = f"Tepper_Corridor_North_Wall_{index + 1}"
        wall = add_segment_box(
            name,
            start,
            end,
            CEILING_HEIGHT,
            0.16,
            materials["wall"],
            collection,
            bevel=0.0,
            start_extension=CORRIDOR_JOIN_OVERLAP,
            end_extension=CORRIDOR_JOIN_OVERLAP,
        )
        wall["opaque_lidar_surface"] = True
        north_wall_segment_objects.append(wall)
        add_baseboard(
            name + "_Baseboard",
            start,
            end,
            materials,
            collection,
            bevel=0.0,
            start_extension=CORRIDOR_JOIN_OVERLAP,
            end_extension=CORRIDOR_JOIN_OVERLAP,
        )
    door_left_wall = build_concrete_wall(
        "Tepper_Corridor_North_Wall_3",
        SHORT_ROOM_CORRIDORS[1]["outline"][3],
        CORRIDOR_GLASS_DOOR_START,
        materials,
        collection,
        bevel=0.0,
        start_extension=CORRIDOR_JOIN_OVERLAP,
    )
    glass_door_upper_wall = build_glass_door(
        "Tepper_Corridor_Glass_Door",
        CORRIDOR_GLASS_DOOR_START,
        CORRIDOR_GLASS_DOOR_END,
        materials,
        collection,
    )
    door_right_wall = build_concrete_wall(
        "Tepper_Corridor_North_Wall_4_West",
        CORRIDOR_GLASS_DOOR_END,
        MIDDLE_GLASS_WALL_START,
        materials,
        collection,
        bevel=0.0,
    )
    middle_glass_upper_wall = build_glass_wall(
        "Tepper_Corridor_Middle_Glass_Wall",
        MIDDLE_GLASS_WALL_START,
        MIDDLE_GLASS_WALL_END,
        materials,
        collection,
        panel_width=0.85,
    )
    mapped_white_wall = add_centerline_prism(
        "Tepper_Corridor_Mapped_White_Wall",
        MAPPED_WHITE_WALL_CENTERLINE,
        CEILING_HEIGHT,
        0.16,
        materials["wall"],
        collection,
        smooth_sides=False,
    )
    mapped_white_wall["opaque_lidar_surface"] = True
    add_centerline_prism(
        "Tepper_Corridor_Mapped_White_Wall_Baseboard",
        MAPPED_WHITE_WALL_CENTERLINE,
        0.16,
        0.035,
        materials["baseboard"],
        collection,
        smooth_sides=False,
    )
    central_connected_wall = join_mesh_objects(
        (
            door_left_wall,
            glass_door_upper_wall,
            door_right_wall,
            middle_glass_upper_wall,
            mapped_white_wall,
        ),
        "Tepper_Corridor_North_Central_Connected_Wall",
    )
    robot_glass_upper_wall = build_glass_wall(
        "Tepper_Robot_Area_Glass_Wall",
        ROBOT_GLASS_WALL_START,
        ROBOT_GLASS_WALL_END,
        materials,
        collection,
        panel_width=0.80,
    )
    robot_glass_upper_wall.name = "Tepper_Robot_Area_Connected_Wall"
    robot_glass_upper_wall.data.name = (
        "Tepper_Robot_Area_Connected_Wall_Data"
    )
    robot_connected_wall = robot_glass_upper_wall
    join_mesh_objects(
        (
            west_connected_wall,
            *north_wall_segment_objects,
            *short_room_wall_objects,
            central_connected_wall,
            robot_connected_wall,
        ),
        "Tepper_Corridor_North_Connected_Wall",
    )

    south_wall_west = add_segment_box(
        "Tepper_Corridor_South_Wall_West_Continuous",
        corridor_south_west[0],
        ELEVATOR_ENTRANCES[0]["outline"][0],
        CEILING_HEIGHT,
        0.16,
        materials["wall"],
        collection,
        bevel=0.0,
        end_extension=CORRIDOR_JOIN_OVERLAP,
    )
    south_wall_west["opaque_lidar_surface"] = True
    add_baseboard(
        "Tepper_Corridor_South_Wall_West_Continuous_Baseboard",
        corridor_south_west[0],
        ELEVATOR_ENTRANCES[0]["outline"][0],
        materials,
        collection,
        bevel=0.0,
        end_extension=CORRIDOR_JOIN_OVERLAP,
    )
    south_east_wall_segments = (
        (
            ELEVATOR_ENTRANCES[0]["outline"][3],
            ELEVATOR_ENTRANCES[1]["outline"][0],
        ),
        (
            ELEVATOR_ENTRANCES[1]["outline"][3],
            ELEVATOR_ENTRANCES[2]["outline"][0],
        ),
    )
    south_east_wall_objects = []
    for index, (start, end) in enumerate(south_east_wall_segments):
        south_east_wall_objects.append(
            build_concrete_wall(
                f"Tepper_Corridor_South_Wall_East_{index + 1}",
                start,
                end,
                materials,
                collection,
                bevel=0.0,
                start_extension=CORRIDOR_JOIN_OVERLAP,
                end_extension=CORRIDOR_JOIN_OVERLAP,
            )
        )
    post_elevator_wall = build_concrete_wall(
        "Tepper_Corridor_South_Post_Elevator_Continuous_Wall",
        ELEVATOR_ENTRANCES[2]["outline"][3],
        corridor_south_tail[1],
        materials,
        collection,
        bevel=0.0,
        start_extension=CORRIDOR_JOIN_OVERLAP,
        end_extension=CORRIDOR_JOIN_OVERLAP,
    )
    side_corridor_left_wall = build_concrete_wall(
        "Tepper_Side_Corridor_Left_Wall",
        corridor_south_tail[1],
        (-0.05, -7.400),
        materials,
        collection,
        bevel=0.0,
        start_extension=CORRIDOR_JOIN_OVERLAP,
    )
    post_elevator_baseboard = bpy.data.objects.get(
        post_elevator_wall.name + "_Baseboard"
    )
    side_corridor_left_baseboard = bpy.data.objects.get(
        side_corridor_left_wall.name + "_Baseboard"
    )
    union_mesh_objects(
        (post_elevator_baseboard, side_corridor_left_baseboard),
        "Tepper_Post_Elevator_Side_Corridor_Connected_Baseboard",
    )
    post_elevator_connected_wall = union_mesh_objects(
        (post_elevator_wall, side_corridor_left_wall),
        "Tepper_Post_Elevator_Side_Corridor_Connected_Wall",
    )
    side_corridor_right_wall = build_concrete_wall(
        "Tepper_Side_Corridor_Right_Wall",
        (1.30, 0.345),
        (1.75, -7.150),
        materials,
        collection,
        bevel=0.0,
        start_extension=CORRIDOR_JOIN_OVERLAP,
    )
    side_corridor_right_baseboard = bpy.data.objects.get(
        side_corridor_right_wall.name + "_Baseboard"
    )
    join_mesh_objects(
        (
            south_wall_west,
            *south_east_wall_objects,
            *elevator_wall_objects,
            post_elevator_connected_wall,
        ),
        "Tepper_Corridor_South_Connected_Wall",
    )

    locker_west_centerline = build_blended_centerline(
        (-0.85, CHANGING_ROOM_BACK_Y),
        (-0.04, 6.00),
        (-0.04, 2.70),
        LOCKER_WEST_BLEND_DISTANCE,
        LOCKER_WEST_BLEND_SAMPLES,
    )
    locker_west_wall = add_centerline_prism(
        "Tepper_Locker_West_Blended_Wall",
        locker_west_centerline,
        CEILING_HEIGHT,
        0.16,
        materials["wall"],
        collection,
        bottom_z=0.0,
    )
    locker_west_wall["opaque_lidar_surface"] = True
    locker_west_baseboard = add_centerline_prism(
        "Tepper_Locker_West_Blended_Baseboard",
        locker_west_centerline,
        0.16,
        0.035,
        materials["baseboard"],
        collection,
        bottom_z=0.0,
    )
    locker_west_wall.name = "Tepper_Locker_West_Connected_Wall"
    locker_west_wall.data.name = "Tepper_Locker_West_Connected_Wall_Data"
    locker_west_baseboard.name = "Tepper_Locker_West_Connected_Baseboard"
    locker_west_baseboard.data.name = (
        "Tepper_Locker_West_Connected_Baseboard_Data"
    )
    wall_spans = []
    span_start = CHANGING_ROOM_FRONTAGE_X_RANGE[0]
    for specification in CHANGING_ROOMS:
        door_center_x = specification["door_center_x"]
        door_left = door_center_x - CHANGING_ROOM_DOOR_HALF_OPENING
        door_right = door_center_x + CHANGING_ROOM_DOOR_HALF_OPENING
        wall_spans.append((span_start, door_left))
        span_start = door_right
    wall_spans.append((span_start, CHANGING_ROOM_FRONTAGE_X_RANGE[1]))

    north_wall_parts = []
    for index, (start_x, end_x) in enumerate(wall_spans, start=1):
        north_wall_parts.append(
            build_concrete_wall(
                f"Tepper_North_Wall_{index}",
                changing_room_frontage_point(start_x),
                changing_room_frontage_point(end_x),
                materials,
                collection,
                bevel=0.0,
            )
        )

    for index, specification in enumerate(CHANGING_ROOMS, start=1):
        center_x = specification["door_center_x"]
        door_left = center_x - CHANGING_ROOM_DOOR_HALF_OPENING
        door_right = center_x + CHANGING_ROOM_DOOR_HALF_OPENING
        header = add_segment_box(
            f"Tepper_North_Door_Header_{index}",
            changing_room_frontage_point(door_left),
            changing_room_frontage_point(door_right),
            CEILING_HEIGHT - ROOM_DOOR_FRAME_TOP,
            0.16,
            materials["wall"],
            collection,
            bottom_z=ROOM_DOOR_FRAME_TOP,
            bevel=0.0,
        )
        header["opaque_lidar_surface"] = True
        north_wall_parts.append(header)
        build_corridor_door(
            f"Tepper_Changing_Room_Door_{index}",
            changing_room_frontage_point(center_x, normal_offset=-0.055),
            materials,
            collection,
            rotation_z=CHANGING_ROOM_FRONTAGE_ANGLE,
            open_angle_degrees=specification[
                "door_open_angle_degrees"
            ],
            hinge_side=specification["door_hinge_side"],
        )

    join_mesh_objects(
        north_wall_parts,
        "Tepper_North_Changing_Room_Connected_Wall",
    )
    build_changing_rooms(collection, materials)
    build_north_enclosure_walls(collection, materials)

    add_segment_box(
        "Tepper_East_Upper_Wall",
        (12.70, 9.70),
        (12.25, 17.50),
        CEILING_HEIGHT,
        0.16,
        materials["wall"],
        collection,
    )
    add_baseboard(
        "Tepper_East_Upper_Baseboard",
        (12.70, 9.70),
        (12.25, 17.50),
        materials,
        collection,
    )
    diagonal_centerline = build_blended_centerline(
        (1.30, 0.345),
        (5.15, 2.948),
        (18.10, 9.250),
        DIAGONAL_BLEND_DISTANCE,
        DIAGONAL_BLEND_SAMPLES,
    )
    diagonal_connected_wall = add_centerline_prism(
        "Tepper_Diagonal_Blended_Wall",
        diagonal_centerline,
        CEILING_HEIGHT,
        0.16,
        materials["wall"],
        collection,
        bottom_z=0.0,
    )
    diagonal_connected_wall["opaque_lidar_surface"] = True
    diagonal_connected_baseboard = add_centerline_prism(
        "Tepper_Diagonal_Blended_Baseboard",
        diagonal_centerline,
        0.16,
        0.035,
        materials["baseboard"],
        collection,
        bottom_z=0.0,
    )
    union_mesh_objects(
        (side_corridor_right_wall, diagonal_connected_wall),
        "Tepper_Diagonal_Connected_Wall",
    )
    union_mesh_objects(
        (side_corridor_right_baseboard, diagonal_connected_baseboard),
        "Tepper_Diagonal_Connected_Baseboard",
    )
    build_wall_protrusion(materials, collection)


def build_lobby_column(collection, materials):
    column = common.add_cylinder(
        "Tepper_Lobby_Concrete_Column",
        (
            LOBBY_PILLAR_CENTER[0],
            LOBBY_PILLAR_CENTER[1],
            CEILING_HEIGHT * 0.5,
        ),
        LOBBY_PILLAR_RADIUS,
        CEILING_HEIGHT,
        materials["concrete"],
        collection,
        vertices=64,
    )
    for polygon in column.data.polygons:
        if abs(polygon.normal.z) < 0.5:
            polygon.use_smooth = True
    bevel = column.modifiers.new("Soft edges", "BEVEL")
    bevel.width = 0.012
    bevel.segments = 3
    return column


def build_robot_area_column(collection, materials):
    column = common.add_cylinder(
        "Tepper_Robot_Area_Concrete_Column",
        (
            ROBOT_AREA_PILLAR_CENTER[0],
            ROBOT_AREA_PILLAR_CENTER[1],
            CEILING_HEIGHT * 0.5,
        ),
        ROBOT_AREA_PILLAR_RADIUS,
        CEILING_HEIGHT,
        materials["concrete"],
        collection,
        vertices=64,
    )
    column["opaque_lidar_surface"] = True
    for polygon in column.data.polygons:
        if abs(polygon.normal.z) < 0.5:
            polygon.use_smooth = True
    bevel = column.modifiers.new("Soft edges", "BEVEL")
    bevel.width = 0.012
    bevel.segments = 3
    return column


def build_locker_bank(specification, parent, materials):
    collection = common.create_collection(specification["name"], parent)
    center_x, center_y = specification["center"]
    length = specification["length"]
    width = specification.get("width", LOCKER_BANK_WIDTH)
    count = specification["count"]
    module_width = length / count
    rotation = math.radians(specification.get("rotation_degrees", 0.0))
    cosine = math.cos(rotation)
    sine = math.sin(rotation)

    def local_to_world(local_x, local_y, z):
        return (
            center_x + local_x * cosine - local_y * sine,
            center_y + local_x * sine + local_y * cosine,
            z,
        )

    common.add_box(
        specification["name"] + "_Body",
        (center_x, center_y, LOCKER_HEIGHT * 0.5),
        (width, length - 0.12, LOCKER_HEIGHT),
        materials["maple_edge"],
        collection,
        bevel=0.025,
        rotation_z=rotation,
    )
    common.add_box(
        specification["name"] + "_Plinth",
        (center_x, center_y, 0.06),
        (width + 0.06, length + 0.04, 0.12),
        materials["maple_edge"],
        collection,
        bevel=0.015,
        rotation_z=rotation,
    )
    common.add_box(
        specification["name"] + "_Top_Cap",
        (center_x, center_y, LOCKER_HEIGHT + 0.025),
        (width + 0.05, length + 0.05, 0.05),
        materials["maple"],
        collection,
        bevel=0.012,
        rotation_z=rotation,
    )

    start_y = -length * 0.5
    for side in (-1.0, 1.0):
        side_label = "West" if side < 0.0 else "East"
        face_x = side * (width * 0.5 + 0.010)
        for index in range(count):
            door_y = start_y + module_width * (index + 0.5)
            common.add_box(
                specification["name"]
                + f"_{side_label}_Door_{index + 1:02d}",
                local_to_world(face_x, door_y, 1.20),
                (0.020, module_width - 0.012, 2.12),
                materials["maple"],
                collection,
                bevel=0.006,
                rotation_z=rotation,
            )
            hardware_x = side * (width * 0.5 + 0.048)
            common.add_box(
                specification["name"]
                + f"_{side_label}_Latch_{index + 1:02d}",
                local_to_world(
                    hardware_x,
                    door_y + module_width * 0.18,
                    0.98,
                ),
                (0.075, 0.115, 0.050),
                materials["aluminum"],
                collection,
                bevel=0.014,
                rotation_z=rotation,
            )
            common.add_box(
                specification["name"]
                + f"_{side_label}_Padlock_{index + 1:02d}",
                local_to_world(
                    hardware_x + side * 0.012,
                    door_y - 0.010,
                    0.90,
                ),
                (0.060, 0.052, 0.080),
                materials["lock_red"],
                collection,
                bevel=0.014,
                rotation_z=rotation,
            )

    for end_index, end_y in enumerate((-length * 0.5, length * 0.5)):
        common.add_box(
            specification["name"] + f"_End_Glass_{end_index + 1}",
            local_to_world(0.0, end_y, LOCKER_HEIGHT * 0.5),
            (width - 0.12, 0.035, LOCKER_HEIGHT - 0.18),
            materials["glass"],
            collection,
            bevel=0.010,
            rotation_z=rotation,
        )
        for side in (-1.0, 1.0):
            common.add_box(
                specification["name"]
                + f"_End_Frame_{end_index + 1}_{side:+.0f}",
                local_to_world(
                    side * (width * 0.5 - 0.035),
                    end_y,
                    LOCKER_HEIGHT * 0.5,
                ),
                (0.07, 0.065, LOCKER_HEIGHT),
                materials["maple_edge"],
                collection,
                bevel=0.008,
                rotation_z=rotation,
            )
        for z in (0.06, LOCKER_HEIGHT - 0.06):
            common.add_box(
                specification["name"]
                + f"_End_Frame_{end_index + 1}_{z:.2f}",
                local_to_world(0.0, end_y, z),
                (width, 0.065, 0.12),
                materials["maple_edge"],
                collection,
                bevel=0.008,
                rotation_z=rotation,
            )
    return collection


BIN_LAYOUT = [
    ('Tepper_Corridor_Trash', 'trash', -10.48, -0.30, math.atan(0.057916), 0.7),
    ('Tepper_Corridor_Recycling', 'recycling', -7.67, -0.15, math.atan(0.057916), 0.7),
    ('Tepper_Lobby_Trash', 'trash', 10.30, 5.60, math.atan(0.486619), 0.7),
    ('Tepper_Lobby_Recycling', 'recycling', 10.80, 5.85, math.atan(0.486619), 0.7),
]


def build_props(collection, materials):
    arm_center = ROBOT_ARM_CENTER
    arm_rotation = ROBOT_ARM_ROTATION
    arm_cosine = math.cos(arm_rotation)
    arm_sine = math.sin(arm_rotation)

    def arm_to_world(local_x, local_y, z):
        return (
            arm_center[0]
            + local_x * arm_cosine
            - local_y * arm_sine,
            arm_center[1]
            + local_x * arm_sine
            + local_y * arm_cosine,
            z,
        )

    arm_points = tuple(
        arm_to_world(local_x, local_y, z)
        for local_x, local_y, z in (
            (0.00, 0.00, 0.22),
            (-0.04, 0.00, 0.82),
            (0.24, -0.04, 1.25),
            (0.06, -0.20, 1.72),
            (-0.20, -0.40, 1.48),
        )
    )
    common.add_curve(
        "Tepper_Robot_Arm",
        arm_points,
        0.055,
        materials["baseboard"],
        collection,
    )
    for index, point in enumerate(arm_points):
        common.add_uv_sphere(
            f"Tepper_Robot_Arm_Joint_{index + 1}",
            point,
            0.105 if index in (1, 2, 3) else 0.075,
            materials["baseboard"],
            collection,
        )



def add_ceiling_fixture(name, location, dimensions, materials, collection):
    common.add_area_light(
        name + "_Area",
        (location[0], location[1], location[2] - 0.06),
        340.0,
        max(dimensions[0], dimensions[1]),
        collection,
        color=(1.0, 0.91, 0.80),
    )


def build_bezier_motion_path(
    name,
    points,
    collection,
    material=None,
    bevel_depth=0.0,
):
    curve_data = bpy.data.curves.new(name + "_Data", "CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 24
    curve_data.render_resolution_u = 32
    curve_data.use_path = True
    curve_data.path_duration = CAMERA_TRAJECTORY_END_FRAME - 1
    curve_data.bevel_depth = bevel_depth
    curve_data.bevel_resolution = 3
    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bezier_point, point in zip(spline.bezier_points, points):
        bezier_point.co = point
        bezier_point.handle_left_type = "AUTO"
        bezier_point.handle_right_type = "AUTO"
    path = bpy.data.objects.new(name, curve_data)
    collection.objects.link(path)
    path.show_in_front = True
    path.hide_render = True
    if material is not None:
        curve_data.materials.append(material)
    return path


def build_camera_trajectory(collection, materials):
    scene = bpy.context.scene
    camera_points = [
        position for _, _, position in CAMERA_TRAJECTORY_KEYFRAMES
    ]
    look_points = []
    for point, look_direction in zip(
        camera_points,
        CAMERA_TRAJECTORY_LOOK_DIRECTIONS,
    ):
        current = Vector(point)
        direction = Vector((*look_direction, 0.0))
        direction.normalize()
        look_point = current + direction * CAMERA_TRAJECTORY_LOOK_DISTANCE
        look_point.z = CAMERA_TRAJECTORY_LOOK_HEIGHT
        look_points.append(tuple(look_point))

    camera_path = build_bezier_motion_path(
        "Tepper_Walkthrough_Camera_Path",
        camera_points,
        collection,
        material=materials["feature_red"],
        bevel_depth=0.018,
    )
    look_path = build_bezier_motion_path(
        "Tepper_Walkthrough_Look_Path",
        look_points,
        collection,
    )
    look_path.display_type = "WIRE"

    target = bpy.data.objects.new("Tepper_Walkthrough_Look_Target", None)
    target.empty_display_type = "SPHERE"
    target.empty_display_size = 0.10
    collection.objects.link(target)

    camera_data = bpy.data.cameras.new("Tepper_Walkthrough_Camera_Data")
    camera_data.lens = 24.0
    camera_data.clip_start = 0.05
    camera_data.clip_end = 250.0
    camera = bpy.data.objects.new("Tepper_Walkthrough_Camera", camera_data)
    collection.objects.link(camera)

    camera_follow = camera.constraints.new("FOLLOW_PATH")
    camera_follow.name = "Follow walkthrough trajectory"
    camera_follow.target = camera_path
    camera_follow.use_fixed_location = True
    camera_follow.use_curve_follow = False

    target_follow = target.constraints.new("FOLLOW_PATH")
    target_follow.name = "Follow walkthrough look trajectory"
    target_follow.target = look_path
    target_follow.use_fixed_location = True
    target_follow.use_curve_follow = False

    camera_track = camera.constraints.new("TRACK_TO")
    camera_track.name = "Look along walkthrough trajectory"
    camera_track.target = target
    camera_track.track_axis = "TRACK_NEGATIVE_Z"
    camera_track.up_axis = "UP_Y"

    interpolation_setting = (
        bpy.context.preferences.edit.keyframe_new_interpolation_type
    )
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    try:
        camera_distances = [0.0]
        look_distances = [0.0]
        for index in range(1, len(camera_points)):
            camera_distances.append(
                camera_distances[-1]
                + (Vector(camera_points[index]) - Vector(camera_points[index - 1])).length
            )
            look_distances.append(
                look_distances[-1]
                + (Vector(look_points[index]) - Vector(look_points[index - 1])).length
            )
        camera_total_distance = camera_distances[-1]
        look_total_distance = look_distances[-1]
        for index, (frame, _, _) in enumerate(CAMERA_TRAJECTORY_KEYFRAMES):
            camera_follow.offset_factor = (
                camera_distances[index] / camera_total_distance
            )
            camera_follow.keyframe_insert(
                data_path="offset_factor",
                frame=frame,
            )
            target_follow.offset_factor = (
                look_distances[index] / look_total_distance
            )
            target_follow.keyframe_insert(
                data_path="offset_factor",
                frame=frame,
            )
    finally:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = (
            interpolation_setting
        )

    camera_path["reference_video"] = VIDEO_PATH
    camera_path["reference_frame_rate"] = REFERENCE_VIDEO_FPS
    camera_path["reference_frame_count"] = REFERENCE_VIDEO_FRAME_COUNT
    camera_path["animation_frame_rate"] = CAMERA_TRAJECTORY_FPS
    camera_path["animation_frame_count"] = CAMERA_TRAJECTORY_END_FRAME
    camera_path["corridor_travel_time_seconds"] = 12.0
    camera_path["route_stages"] = (
        "Corridor start; corridor traversal; left into lockers; right past "
        "changing rooms; right at last locker; right past pillar and "
        "recycling to the corner."
    )
    camera_path["timed_waypoints"] = str(CAMERA_TRAJECTORY_KEYFRAMES)

    scene.render.fps = CAMERA_TRAJECTORY_FPS
    scene.render.fps_base = 1.0
    scene.frame_start = 1
    scene.frame_end = CAMERA_TRAJECTORY_END_FRAME
    scene.frame_set(1)
    return camera


def build_lighting_and_cameras(collection, trajectory_collection, materials):
    scene = bpy.context.scene
    world = scene.world or bpy.data.worlds.new("Tepper_World")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.055, 0.060, 0.065, 1.0)
    background.inputs["Strength"].default_value = 0.38

    fixture_index = 0
    for x in (1.5, 5.0, 8.5, 11.5):
        for y in (5.5, 10.5, 15.0):
            fixture_index += 1
            if x == 11.5 and y == 5.5:
                continue
            add_ceiling_fixture(
                f"Tepper_Locker_LED_{fixture_index:02d}",
                (x, y, CEILING_HEIGHT - 0.08),
                (1.80, 0.22, 0.055),
                materials,
                collection,
            )

    hero_data = bpy.data.cameras.new("Tepper_Hero_Camera_Data")
    hero_data.lens = 27.0
    hero = bpy.data.objects.new("Tepper_Hero_Camera", hero_data)
    hero.location = (12.00, 8.20, 1.45)
    common.point_camera(hero, (3.80, 2.80, 1.05))
    collection.objects.link(hero)

    corridor_data = bpy.data.cameras.new("Tepper_Corridor_Camera_Data")
    corridor_data.lens = 26.0
    corridor = bpy.data.objects.new("Tepper_Corridor_Camera", corridor_data)
    corridor.location = (-18.0, 0.14, 1.45)
    common.point_camera(corridor, (-1.0, 1.35, 1.05))
    collection.objects.link(corridor)

    overhead_data = bpy.data.cameras.new("Tepper_Overhead_Camera_Data")
    overhead_data.type = "ORTHO"
    overhead_data.ortho_scale = 36.0
    overhead = bpy.data.objects.new("Tepper_Overhead_Camera", overhead_data)
    overhead.location = (-10.0, 7.0, 3.05)
    common.point_camera(overhead, (-10.0, 7.0, 0.0))
    collection.objects.link(overhead)
    scene.camera = build_camera_trajectory(
        trajectory_collection,
        materials,
    )


def build_overlay(collection):
    return common.build_image_overlay(
        "Tepper_Hallway_Map_Overlay",
        collection,
        MAP_OVERLAY_PATH,
        map_to_world,
        MAP_RESOLUTION,
        "YAML map recentered at pixel 850,350 without changing scale",
    )


def mark_unified_visual_collision(*collections):
    physical_objects = {}
    for collection in collections:
        for obj in collection.all_objects:
            if obj.type not in {"MESH", "CURVE"}:
                continue
            obj["unified_visual_and_collision"] = True
            obj["separate_collision_proxy"] = False
            physical_objects[obj.name] = obj
    return {
        "shared_visual_collision_objects": len(physical_objects),
        "wall_geometry": "smooth fitted solids",
        "separate_collision_proxy": False,
    }


def main():
    os.makedirs(RENDER_OUTPUT_DIR, exist_ok=True)
    clear_scene()
    scene = bpy.context.scene
    scene.name = "Tepper_Hallway"
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    if scene.render.image_settings.file_format != "FFMPEG":
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = PREVIEW_PATH
    scene.render.film_transparent = False

    root = common.create_collection("Tepper_Hallway_Recreation", scene.collection)
    architecture = common.create_collection("Tepper_Architecture", root)
    lockers = common.create_collection("Tepper_Lockers", root)
    props = common.create_collection("Tepper_Props", root)
    measurement = common.create_collection("Tepper_Measurement", root)
    lighting = common.create_collection("Tepper_Lighting", root)
    camera_trajectory = common.create_collection(
        "Tepper_Camera_Trajectory",
        root,
    )

    materials = build_materials()
    build_floor_and_architecture(architecture, materials)
    build_lobby_column(architecture, materials)
    build_robot_area_column(architecture, materials)
    for specification in LOCKER_BANKS:
        build_locker_bank(specification, lockers, materials)
    build_props(props, materials)

    visual_geometry_summary = mark_unified_visual_collision(
        architecture,
        lockers,
        props,
    )
    overlay = build_overlay(measurement)
    overlay.hide_viewport = False
    overlay.hide_render = True
    build_lighting_and_cameras(lighting, camera_trajectory, materials)

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.shading.type = "MATERIAL"

    return root
