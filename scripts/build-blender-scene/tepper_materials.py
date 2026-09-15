"""Materials, mapped surface textures and recycling fixtures for Tepper."""
import json
import math
import os
import random
import re
import sys
from array import array

import bmesh
import bpy
from mathutils import Vector

PROJECT_ROOT = "/Users/xiachu/Files/projects/f1tenth_isaac"
if PROJECT_ROOT + "/scripts/build-blender-scene" not in sys.path:
    sys.path.insert(0, PROJECT_ROOT + "/scripts/build-blender-scene")
from scene_assets import *  # noqa: F401,F403

BUILDER_ROOT = "Tepper_Hallway_Recreation"
OVERLAY_NAME = "Tepper_Hallway_Map_Overlay"
DERIVED_ROOT = GENERATED_TEXTURES.name
LABEL_ROOT = PROJECT_ROOT + "/blender/assets/tepper"
UV_NAME = "st"
FLOOR_TOP_Z = 0.02
FLOOR_TEXTURE = "concrete_floor_worn_001"
FLOOR_TILE_M = 3.0
FLOOR_COLOR_GAIN = (1.15, 1.12, 1.05)
FLOOR_ROUGHNESS = (0.25, 0.05)  # scale, offset applied to the scanned roughness
WALL_TEXTURE = "white_plaster_02"
WALL_TILE_M = 2.0
WALL_COLOR_GAIN = (1.05, 1.05, 1.04)
WALL_FLATTEN = ((0.88, 0.87, 0.84), 0.55)  # blend the plaster stains toward off white
WALL_NORMAL_FLATTEN = ((0.5, 0.5, 1.0), 0.7)  # weaken the plaster relief
VENEER_GAIN = (0.92, 1.0, 0.8)  # okoume toward honey
COLUMN_TILE_M = 3.0
VENEER_TEXTURE = "okoume_veneer"
VENEER_TILE_M = 1.0
PADLOCK_RED_SHARE = 0.38
ORANGE_PANEL = (0.85, 0.22, 0.03)  # translucent acrylic end panels on the lobby side of the locker banks
ORANGE_PANEL_ALPHA = 0.7
FIXTURE_WATTS = 220.0
FIXTURE_COLOR = (1.0, 0.93, 0.84)
FIXTURE_SPREAD = math.radians(130.0)
OVERLAY_CAMERA_LOCATION = (-11.0, 4.25, 3.05)
OVERLAY_CAMERA_SCALE = 60.0


# ----------------------------------------------------------------------------
# Object classes and UVs
# ----------------------------------------------------------------------------
def builder_objects():
    return [obj for obj in bpy.data.collections[BUILDER_ROOT].all_objects if obj.type == "MESH" and obj.name != OVERLAY_NAME]


def surface_class(name):
    if name.endswith("_Floor"):
        return "floor"
    if name.endswith("_Ceiling"):
        return "ceiling"
    if name.endswith(("_Connected_Wall", "_Connected_Walls", "_Enclosure_Wall")) or name in ("Tepper_East_Upper_Wall", "Tepper_Lobby_Wall_Protrusion"):
        return "wall"
    if name.endswith("_Concrete_Column"):
        return "column"
    if name.startswith("Locker_Bank") and (name.endswith(("_Body", "_Top_Cap")) or "_Door_" in name or "_End_Frame_" in name):
        return "veneer"
    return None


def write_box_uv(obj, layer_name, tile_m, rotate=False, offset=(0.0, 0.0)):
    """World-space box projection in texture tiles; rotate turns a horizontal
    grain vertical on side faces."""
    mesh = obj.data
    layer = mesh.uv_layers.get(layer_name) or mesh.uv_layers.new(name=layer_name)
    matrix = obj.matrix_world if obj.parent else obj.matrix_basis
    normal_matrix = matrix.to_3x3().inverted().transposed()
    scale = 1.0 / tile_m
    for poly in mesh.polygons:
        normal = normal_matrix @ poly.normal
        axis = max(range(3), key=lambda i: abs(normal[i]))
        for loop_index in poly.loop_indices:
            world = matrix @ mesh.vertices[mesh.loops[loop_index].vertex_index].co
            if axis == 0:
                u, v = world.y, world.z
            elif axis == 1:
                u, v = world.x, world.z
            else:
                u, v = world.x, world.y
            if rotate:
                u, v = -v, u
            layer.data[loop_index].uv = (u * scale + offset[0], v * scale + offset[1])
    mesh.uv_layers.active = layer
    layer.active_render = True
    return layer


# ----------------------------------------------------------------------------
# Derived images and materials
# ----------------------------------------------------------------------------
def texture_path(texture_id, suffix):
    return f"{TEXTURE_ROOT}/{texture_id}/{texture_id}_{suffix}_2k.jpg"


def derived_image(source_path, out_name, gain=(1.0, 1.0, 1.0), scale=1.0, offset=0.0, colorspace="sRGB", flatten=None):
    """Copy of a scanned map with per-channel gain (base colour), a linear
    scale and offset (roughness), or a blend toward a constant (flatten =
    (colour, factor); used to weaken stains and normal maps), saved as PNG so
    the USD export can use it."""
    existing = bpy.data.images.get(out_name)
    if existing is not None:
        bpy.data.images.remove(existing)
    image = bpy.data.images.load(source_path, check_existing=False)
    count = image.size[0] * image.size[1] * 4
    buffer = array("f", [0.0]) * count
    image.pixels.foreach_get(buffer)
    for channel in range(3):
        factor = gain[channel] * scale
        values = buffer[channel::4]
        if flatten is not None:
            target, amount = flatten[0][channel], flatten[1]
            values = array("f", [value * (1.0 - amount) + target * amount for value in values])
        buffer[channel::4] = array("f", [min(1.0, max(0.0, value * factor + offset)) for value in values])
    image.pixels.foreach_set(buffer)
    image.filepath_raw = f"{DERIVED_ROOT}/{out_name}"
    image.file_format = "PNG"
    image.save()
    image.name = out_name
    image.colorspace_settings.name = colorspace
    return image


def image_material(name, diff=None, rough=None, normal=None, base_color=None, roughness=0.5, metallic=0.0):
    """Exportable material: image textures through the st UV map straight
    into the Principled BSDF; missing maps fall back to constants."""
    material, tree, bsdf = reset_material(name)
    uv = tree.nodes.new("ShaderNodeUVMap")
    uv.location = (-800, 0)
    uv.uv_map = UV_NAME
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if base_color is not None:
        bsdf.inputs["Base Color"].default_value = (base_color[0], base_color[1], base_color[2], 1.0)
    for image, socket, y in ((diff, "Base Color", 300), (rough, "Roughness", 0)):
        if image is None:
            continue
        node = tree.nodes.new("ShaderNodeTexImage")
        node.location = (-450, y)
        node.image = image
        tree.links.new(uv.outputs["UV"], node.inputs["Vector"])
        tree.links.new(node.outputs["Color"], bsdf.inputs[socket])
    if normal is not None:
        node = tree.nodes.new("ShaderNodeTexImage")
        node.location = (-450, -350)
        node.image = normal
        tree.links.new(uv.outputs["UV"], node.inputs["Vector"])
        normal_map = tree.nodes.new("ShaderNodeNormalMap")
        normal_map.location = (-150, -350)
        normal_map.uv_map = UV_NAME
        tree.links.new(node.outputs["Color"], normal_map.inputs["Color"])
        tree.links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
    return material


def build_materials():
    os.makedirs(DERIVED_ROOT, exist_ok=True)
    floor_diff = derived_image(texture_path(FLOOR_TEXTURE, "diff"), "tepper_floor_diff.png", gain=FLOOR_COLOR_GAIN)
    floor_rough = derived_image(texture_path(FLOOR_TEXTURE, "rough"), "tepper_floor_rough.png", scale=FLOOR_ROUGHNESS[0], offset=FLOOR_ROUGHNESS[1], colorspace="Non-Color")
    floor_normal = load_image(texture_path(FLOOR_TEXTURE, "nor_gl"), "Non-Color")
    wall_diff = derived_image(texture_path(WALL_TEXTURE, "diff"), "tepper_wall_diff.png", gain=WALL_COLOR_GAIN, flatten=WALL_FLATTEN)
    wall_rough = load_image(texture_path(WALL_TEXTURE, "rough"), "Non-Color")
    wall_normal = derived_image(texture_path(WALL_TEXTURE, "nor_gl"), "tepper_wall_nor.png", colorspace="Non-Color", flatten=WALL_NORMAL_FLATTEN)
    column_diff = load_image(texture_path(FLOOR_TEXTURE, "diff"), "sRGB")
    column_rough = load_image(texture_path(FLOOR_TEXTURE, "rough"), "Non-Color")
    veneer_diff = derived_image(texture_path(VENEER_TEXTURE, "diff"), "tepper_veneer_diff.png", gain=VENEER_GAIN)
    veneer_rough = load_image(texture_path(VENEER_TEXTURE, "rough"), "Non-Color")
    veneer_normal = load_image(texture_path(VENEER_TEXTURE, "nor_gl"), "Non-Color")
    materials = {
        "floor": image_material("Tepper_Polished_Concrete", floor_diff, floor_rough, floor_normal),
        "wall": image_material("Tepper_Warm_White_Wall", wall_diff, wall_rough, wall_normal),
        "ceiling": image_material("Tepper_White_Ceiling", wall_diff, wall_rough, wall_normal),
        "column": image_material("Tepper_Concrete_Column", column_diff, column_rough, floor_normal),
        "veneer": image_material("Tepper_Maple_Lockers", veneer_diff, veneer_rough, veneer_normal),
        "plinth": simple_material("Tepper_Maple_Edges", (0.05, 0.04, 0.035), roughness=0.6),
        "mirror": simple_material("Tepper_Locker_Mirror", (0.92, 0.93, 0.94), roughness=0.02, metallic=1.0),
        "orange_panel": orange_panel_material("Tepper_Locker_Orange_Panel"),
        "baseboard": simple_material("Tepper_White_Baseboard", (0.50, 0.51, 0.52), roughness=0.35, metallic=1.0),
        "aluminum": simple_material("Tepper_Brushed_Aluminum", (0.64, 0.65, 0.66), roughness=0.30, metallic=1.0),
        "elevator": simple_material("Tepper_Elevator_Dark_Metal", (0.42, 0.43, 0.44), roughness=0.28, metallic=1.0),
        "door_paint": simple_material("Tepper_Painted_Door", (0.88, 0.88, 0.86), roughness=0.32),
        "padlock_red": simple_material("Tepper_Padlock_Red", (0.45, 0.02, 0.015), roughness=0.3),
        "padlock_silver": simple_material("Tepper_Padlock_Silver", (0.62, 0.63, 0.65), roughness=0.25, metallic=1.0),
        "kiosk": simple_material("Tepper_Kiosk_Charcoal", (0.50, 0.45, 0.37), roughness=0.45),
        "label_red": simple_material("Tepper_Feature_Red", (0.5, 0.02, 0.02), roughness=0.4),
        "arm": simple_material("Tepper_Robot_Arm_Paint", (0.72, 0.74, 0.76), roughness=0.35),
        "arm_joint": simple_material("Tepper_Robot_Arm_Joint", (0.10, 0.12, 0.16), roughness=0.4),
        "laminate": simple_material("Tepper_Station_Laminate", (0.12, 0.11, 0.10), roughness=0.5),
    }
    materials["cardboard"] = simple_material("Tepper_Cardboard", (0.30, 0.21, 0.12), roughness=0.9)
    materials["bin_grey"] = simple_material("Tepper_Trash_Gray", (0.36, 0.37, 0.38), roughness=0.55)
    materials["bin_blue"] = simple_material("Tepper_Recycling_Blue", (0.02, 0.09, 0.42), roughness=0.5)
    materials["bin_lid_black"] = simple_material("Tepper_Bin_Lid_Black", (0.015, 0.015, 0.016), roughness=0.5)
    materials["logo_red"] = simple_material("Tepper_Logo_Red", (0.6, 0.02, 0.02), roughness=0.4)
    liner, liner_tree, liner_bsdf = reset_material("Tepper_Bin_Liner")
    liner_bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.92, 1.0)
    liner_bsdf.inputs["Roughness"].default_value = 0.3
    liner_bsdf.inputs["Alpha"].default_value = 0.45
    materials["bin_liner"] = liner
    label_image = load_image(f"{LABEL_ROOT}/bin_label.png", "sRGB")
    label_image.reload()
    materials["bin_label_print"] = image_material("Tepper_Bin_Label_Print", diff=label_image, roughness=0.5)
    for key, file_name, roughness in (("station_panel", "recycling_station_panel.png", 0.45), ("station_side", "recycling_station_side.png", 0.45), ("cardboard_tartan", "cardboard_tartan.png", 0.85)):
        image = load_image(f"{LABEL_ROOT}/{file_name}", "sRGB")
        image.reload()
        materials[key] = image_material("Tepper_" + key.title(), diff=image, roughness=roughness)
    material, tree, bsdf = reset_material("Tepper_Glass")
    bsdf.inputs["Base Color"].default_value = (0.9, 0.95, 0.93, 1.0)
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.5
    materials["glass"] = material
    return materials


def orange_panel_material(name):
    material, tree, bsdf = reset_material(name)
    bsdf.inputs["Base Color"].default_value = (ORANGE_PANEL[0], ORANGE_PANEL[1], ORANGE_PANEL[2], 1.0)
    bsdf.inputs["Roughness"].default_value = 0.15
    bsdf.inputs["Alpha"].default_value = ORANGE_PANEL_ALPHA
    return material


def set_material(obj, material):
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)


def assign_materials(materials):
    rng = random.Random(11)
    tiles = {"floor": FLOOR_TILE_M, "ceiling": WALL_TILE_M, "wall": WALL_TILE_M, "column": COLUMN_TILE_M, "veneer": VENEER_TILE_M}
    for obj in builder_objects():
        name = obj.name
        kind = surface_class(name)
        if kind is not None:
            offset = (rng.random(), rng.random()) if "_Door_" in name else (0.0, 0.0)
            write_box_uv(obj, UV_NAME, tiles[kind], rotate=(kind == "veneer"), offset=offset)
            set_material(obj, materials[kind])
        elif name.startswith("Locker_Bank") and "_Padlock_" in name:
            set_material(obj, materials["padlock_red"] if rng.random() < PADLOCK_RED_SHARE else materials["padlock_silver"])
        elif name.endswith("_End_Glass_1"):
            set_material(obj, materials["orange_panel"])
        elif name.endswith("_End_Glass_2"):
            set_material(obj, materials["mirror"])
        elif name.endswith("_Plinth"):
            set_material(obj, materials["plinth"])
        elif re.fullmatch(r"Tepper_Changing_Room_Door_\d", name) or name.endswith("_Room_Door"):
            set_material(obj, materials["door_paint"])
        elif name.startswith("Tepper_Robot_Arm_Joint"):
            set_material(obj, materials["arm_joint"])
    arm = bpy.data.objects.get("Tepper_Robot_Arm")
    if arm is not None and arm.type == "CURVE":
        if arm.data.materials:
            arm.data.materials[0] = materials["arm"]
        else:
            arm.data.materials.append(materials["arm"])


# ----------------------------------------------------------------------------
# Recycling station (replaces the builder's box on the same footprint)
# ----------------------------------------------------------------------------
STATION_PREFIX = "Recycling_Station_"
STATION_COLLECTION = "Tepper_Photoreal_Props"
# Extents in the builder station frame, read off the map overlay cells (u along the wall, v toward the lobby)
STATION_CABINET_U = (-0.55, 0.10)
STATION_CABINET_V = (-0.15, 0.45)  # back is raised to clear the wall face, measured by ray cast
STATION_CABINET_HEIGHT = 1.26
STATION_BAND = 0.03  # veneer edge banding width
STATION_BOX_U = (0.13, 0.60)
STATION_BOX_V = (-0.12, 0.33)
STATION_WALL_CLEARANCE = 0.01
STATION_BOX_HEIGHT = 0.75


def plate_uv(obj, axis="x"):
    """UVs from local box coordinates so an image fills the large face once,
    viewer's left at u = 0 when looking at the face from outside."""
    mesh = obj.data
    layer = mesh.uv_layers.get(UV_NAME) or mesh.uv_layers.new(name=UV_NAME)
    coords = [v.co for v in mesh.vertices]
    size = Vector((max(c.x for c in coords) - min(c.x for c in coords), max(c.y for c in coords) - min(c.y for c in coords), max(c.z for c in coords) - min(c.z for c in coords)))
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            u = 0.5 - co.x / size.x if axis == "x" else 0.5 - co.y / size.y
            layer.data[loop_index].uv = (u, co.z / size.z + 0.5)
    mesh.uv_layers.active = layer
    layer.active_render = True


def add_frame(name, world, x, z, width, height, bar, thickness, y, material, collection, yaw):
    """Four thin bars around a rectangular opening on the front face."""
    parts = []
    for tag, cx, cz, w, h in (("Top", x, z + height * 0.5 + bar * 0.5, width + 2.0 * bar, bar), ("Bottom", x, z - height * 0.5 - bar * 0.5, width + 2.0 * bar, bar), ("Left", x - width * 0.5 - bar * 0.5, z, bar, height), ("Right", x + width * 0.5 + bar * 0.5, z, bar, height)):
        parts.append(add_box(f"{name}_{tag}", world(cx, y, cz), (w, thickness, h), material, collection, rot_z=yaw))
    return parts


def add_torus(name, center, major, minor, material, collection, rotation=(0.0, 0.0, 0.0), major_segments=48, minor_segments=10):
    bm = bmesh.new()
    grid = []
    for i in range(major_segments):
        u = 2.0 * math.pi * i / major_segments
        row = []
        for j in range(minor_segments):
            v = 2.0 * math.pi * j / minor_segments
            radial = major + minor * math.cos(v)
            row.append(bm.verts.new((radial * math.cos(u), radial * math.sin(u), minor * math.sin(v))))
        grid.append(row)
    for i in range(major_segments):
        for j in range(minor_segments):
            face = bm.faces.new((grid[i][j], grid[(i + 1) % major_segments][j], grid[(i + 1) % major_segments][(j + 1) % minor_segments], grid[i][(j + 1) % minor_segments]))
            face.smooth = True
    mesh = bpy.data.meshes.new(name + "_Data")
    bm.to_mesh(mesh)
    bm.free()
    finalize_mesh(mesh, smooth=True)
    return mesh_object(name, mesh, material, collection, center, rotation)


def cut(target, cutter):
    modifier = target.modifiers.new("Cut_" + cutter.name, "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter


def station_frame():
    import tepper_geometry as geometry
    center = Vector((*geometry.MULTISTREAM_RECYCLING_CENTER, 0))
    dimensions = Vector((geometry.MULTISTREAM_RECYCLING_LENGTH,
                         geometry.MULTISTREAM_RECYCLING_WIDTH, 0))
    yaw = Vector((0, 0, geometry.MULTISTREAM_RECYCLING_ROTATION)).z
    return [center.x, center.y, yaw, dimensions.x, dimensions.y]


def add_open_box(name, center, size, thickness, outer, inner, collection, rot_z=0.0):
    """Hollow open-top box: four walls and a bottom in one mesh; faces that
    look into the box get the inner material."""
    w, d, h = size
    t = thickness
    bm = bmesh.new()
    for c, s in (((0.0, 0.0, -h * 0.5 + t * 0.5), (w, d, t)), ((0.0, d * 0.5 - t * 0.5, 0.0), (w, t, h)), ((0.0, -d * 0.5 + t * 0.5, 0.0), (w, t, h)), ((w * 0.5 - t * 0.5, 0.0, 0.0), (t, d - 2.0 * t, h)), ((-w * 0.5 + t * 0.5, 0.0, 0.0), (t, d - 2.0 * t, h))):
        verts = bmesh.ops.create_cube(bm, size=1.0)["verts"]
        bmesh.ops.scale(bm, vec=Vector(s), verts=verts)
        bmesh.ops.translate(bm, vec=Vector(c), verts=verts)
    bm.faces.ensure_lookup_table()
    for face in bm.faces:
        face.material_index = 1 if face.normal.dot(-face.calc_center_median()) > 0.0 else 0
    mesh = bpy.data.meshes.new(name + "_Data")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = mesh_object(name, mesh, outer, collection, center, (0.0, 0.0, rot_z))
    mesh.materials.append(inner)
    return obj


def wall_face_v(world, normal, u_range, z=0.6, samples=7):
    """Highest v (toward the lobby) of the wall face behind the station across
    a u range, from horizontal ray casts in the station frame."""
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    base = Vector(world(0.0, 0.0, z))
    values = []
    for index in range(samples):
        u = u_range[0] + (u_range[1] - u_range[0]) * index / (samples - 1)
        hit, location, _, _, obj, _ = scene.ray_cast(depsgraph, Vector(world(u, 0.9, z)), -normal)
        if hit and obj is not None and "Wall" in obj.name:
            values.append((location - base).dot(normal))
    return max(values) if values else None


def build_recycling_station(materials):
    """Carnegie Mellon multi-stream recycling cabinet plus the tartan
    cardboard bin beside it, placed to the map overlay's occupied cells in the
    builder station's local frame (u along the wall, v toward the lobby). The
    cabinet is a dark laminate carcass with veneer edge banding, a recessed
    textured front panel whose three centred openings are cut through with
    hidden boolean cutters and framed by metal bezels, labels below each
    opening, and the university wordmark printed on the corridor-facing side.
    The cardboard bin is a hollow open-top box."""
    scene = bpy.context.scene
    x0, y0, yaw, length, footprint_depth = station_frame()
    props = bpy.data.collections["Tepper_Props"]
    collection = get_collection(STATION_COLLECTION, scene.collection)
    origin = Vector((x0, y0, 0.0))
    along = Vector((math.cos(yaw), math.sin(yaw), 0.0))
    normal = Vector((-math.sin(yaw), math.cos(yaw), 0.0))

    def world(x, y, z):
        point = origin + along * x + normal * y
        return (point.x, point.y, z)

    (u_min, u_max), (v_min, v_max) = STATION_CABINET_U, STATION_CABINET_V
    wall_v = wall_face_v(world, normal, (u_min, u_max))
    if wall_v is not None:
        v_min = max(v_min, wall_v + STATION_WALL_CLEARANCE)
    width, depth, height = u_max - u_min, v_max - v_min, STATION_CABINET_HEIGHT
    cx, cy = (u_min + u_max) * 0.5, (v_min + v_max) * 0.5
    front = v_max
    band = STATION_BAND
    z0 = FLOOR_TOP_Z
    laminate = materials["laminate"]
    veneer = materials["veneer"]
    metal = materials["aluminum"]
    parts = []
    colliders = []

    carcass = add_box(STATION_PREFIX + "Carcass", world(cx, cy - 0.008, z0 + height * 0.5), (width - 0.004, depth - 0.02, height - 0.004), laminate, collection, rot_z=yaw)
    panel = add_box(STATION_PREFIX + "Panel", world(cx, front - 0.008, z0 + height * 0.5), (width - 2.0 * band, 0.012, height - 2.0 * band), materials["station_panel"], collection, rot_z=yaw)
    plate_uv(panel, "x")
    side = add_box(STATION_PREFIX + "Side_Panel", world(u_min - 0.004, cy - 0.006, z0 + height * 0.5), (0.012, depth - 0.036, height - 2.0 * band), materials["station_side"], collection, rot_z=yaw)
    plate_uv(side, "y")
    parts += [carcass, panel, side]
    colliders.append(carcass)
    parts += add_frame(STATION_PREFIX + "Band", world, cx, z0 + height * 0.5, width - 2.0 * band, height - 2.0 * band, band, 0.02, front - 0.01, veneer, collection, yaw)
    top = add_box(STATION_PREFIX + "Top", world(cx, cy, z0 + height + 0.006), (width, depth, 0.012), laminate, collection, rot_z=yaw)
    parts.append(top)
    colliders.append(top)
    for tag, x, y, w, d in (("Front", cx, front - 0.006, width, 0.012), ("Back", cx, v_min + 0.006, width, 0.012), ("Side1", u_min + 0.006, cy, 0.012, depth), ("Side2", u_max - 0.006, cy, 0.012, depth)):
        parts.append(add_box(f"{STATION_PREFIX}Top_Band_{tag}", world(x, y, z0 + height + 0.006), (w, d, 0.016), veneer, collection, rot_z=yaw))
    for tag, x in (("Left", u_min + 0.006), ("Right", u_max - 0.006)):
        parts.append(add_box(f"{STATION_PREFIX}Edge_{tag}", world(x, front - 0.006, z0 + height * 0.5), (0.012, 0.012, height), veneer, collection, rot_z=yaw))

    openings = (("Slot", "box", (0.24, 0.035), 1.10), ("Square", "box", (0.16, 0.16), 0.78), ("Round", "cylinder", (0.065, 0.065), 0.40))
    for tag, kind, size, z in openings:
        if kind == "box":
            cutter = add_box(f"{STATION_PREFIX}Cutter_{tag}", world(cx, front - 0.10, z0 + z), (size[0], 0.30, size[1]), None, collection, rot_z=yaw, uv=False)
            parts += add_frame(f"{STATION_PREFIX}Bezel_{tag}", world, cx, z0 + z, size[0], size[1], 0.008, 0.006, front + 0.001, metal, collection, yaw)
        else:
            cutter = add_cylinder(f"{STATION_PREFIX}Cutter_{tag}", world(cx, front - 0.10, z0 + z), size[0], 0.30, None, collection, segments=48, rotation=(math.pi * 0.5, 0.0, yaw))
            parts.append(add_torus(f"{STATION_PREFIX}Bezel_{tag}", world(cx, front + 0.001, z0 + z), size[0] + 0.004, 0.005, metal, collection, rotation=(math.pi * 0.5, 0.0, yaw)))
        cutter.hide_render = True
        cutter.display_type = "WIRE"
        cut(carcass, cutter)
        cut(panel, cutter)
        parts.append(cutter)

    (bu_min, bu_max), (bv_min, bv_max) = STATION_BOX_U, STATION_BOX_V
    box_wall_v = wall_face_v(world, normal, (bu_min, bu_max))
    if box_wall_v is not None:
        bv_min = max(bv_min, box_wall_v + STATION_WALL_CLEARANCE)
    bw, bd, bh = bu_max - bu_min, bv_max - bv_min, STATION_BOX_HEIGHT
    box = add_open_box(STATION_PREFIX + "Cardboard_Bin", world((bu_min + bu_max) * 0.5, (bv_min + bv_max) * 0.5, z0 + bh * 0.5), (bw, bd, bh), 0.008, materials["cardboard_tartan"], materials["cardboard"], collection, rot_z=yaw)
    write_box_uv(box, UV_NAME, 0.24)
    parts.append(box)
    colliders.append(box)

    for part in parts:
        if part.data.materials and part.data.materials[0] is veneer:
            write_box_uv(part, UV_NAME, 0.5)
    for part in colliders:
        props.objects.link(part)
    scene["tepper_station_extents"] = [u_min, u_max, v_min, v_max, bu_min, bu_max, bv_min, bv_max]
    return len(parts)


# ----------------------------------------------------------------------------
# Slim bins (replace the builder's four box bins on the map contour)
# ----------------------------------------------------------------------------
BIN_PREFIX = "Slim_Bin_"
BIN_DEPTH = 0.28
BIN_BODY_HEIGHT = 0.76
BIN_LID_HEIGHT = 0.028
BIN_CORNER = 0.03
BIN_WIDTH = 0.56  # Slim Jim, centred on the builder centre; only the front comes from the overlay
BIN_PAIR_GAP = 0.04  # extra separation along the wall between the two bins of a pair
BIN_MAX_WALL_OVERLAP = 0.13  # the builder wall prisms reach up to 17 cm past the mapped wall cells
BIN_BUILDERS = (("Tepper_Corridor_Trash", "trash"), ("Tepper_Corridor_Recycling", "recycling"), ("Tepper_Lobby_Trash", "trash"), ("Tepper_Lobby_Recycling", "recycling"))


def overlay_sampler():
    """Returns occupied(x, y) for the packed map overlay (0.05 m cells,
    anchored like the builder's map_to_world)."""
    image = bpy.data.images["hallway.pgm"]
    width, height = image.size
    pixels = image.pixels[:]

    def occupied(x, y):
        col = int(round(x / 0.05 + 850.0))
        row = int(round(350.0 - y / 0.05))
        if not (0 <= col < width and 0 <= row < height):
            return False
        index = ((height - 1 - row) * width + col) * 4
        return (pixels[index] + pixels[index + 1] + pixels[index + 2]) / 3.0 < 0.35

    return occupied


def bin_frames():
    from tepper_geometry import BIN_LAYOUT
    frames = []
    for base, kind, x, y, yaw, width_scale in BIN_LAYOUT:
        position = Vector((x, y, yaw))
        depth = Vector((0, 0.42 * width_scale, 0)).y
        frames.append([base, kind, *position, -depth * 0.5])
    return frames


def bin_contour(occupied, origin, along, normal):
    """Front v and u extent of a bin from the overlay cells around its frame:
    the front is the highest v row with at least four occupied cells within
    25 cm of the centre (adjacent bins share rows further out)."""
    rows = {}
    for j in range(6, -7, -1):
        v = j * 0.05
        cells = [i * 0.05 for i in range(-8, 9) if occupied(*(origin + along * (i * 0.05) + normal * v))]
        rows[round(v, 2)] = cells
    front = None
    for v in sorted(rows, reverse=True):
        if len([u for u in rows[v] if abs(u) <= 0.25]) >= 4:
            front = v
            break
    if front is None:
        return None, None, None
    cells = [u for v in (front, round(front - 0.05, 2)) for u in rows.get(v, []) if abs(u) <= 0.40]
    return front + 0.025, min(cells) - 0.025, max(cells) + 0.025


def bin_body_mesh(name, width, depth, height, corner):
    bm = bmesh.new()
    verts = bmesh.ops.create_cube(bm, size=1.0)["verts"]
    bmesh.ops.scale(bm, vec=Vector((width, depth, height)), verts=verts)
    bmesh.ops.translate(bm, vec=Vector((0.0, 0.0, height * 0.5)), verts=verts)
    vertical = [e for e in bm.edges if abs((e.verts[0].co - e.verts[1].co).normalized().z) > 0.9]
    bmesh.ops.bevel(bm, geom=vertical, offset=corner, segments=4, affect="EDGES")
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return mesh


def build_trash_bins(materials):
    """Rubbermaid Slim Jim style bins on the builder bins' frames: a slim
    body with rounded vertical corners, embossed panel strips, hinge
    knuckles, a clear liner band under the lid, and a hinged lid; the same
    shape for both kinds. Trash bins are grey with a black lid and a red
    logo; recycling bins are blue with a blue round-hole lid and a front
    label. Fronts come from the map
    overlay, averaged per pair so both bins stand on one line; the back may
    sit up to BIN_MAX_WALL_OVERLAP inside the builder wall prism, which
    extends past the mapped wall cells."""
    scene = bpy.context.scene
    frames = bin_frames()
    props = bpy.data.collections["Tepper_Props"]
    collection = get_collection(STATION_COLLECTION, scene.collection)
    occupied = overlay_sampler()
    extents = {}
    fronts = {}
    frames_by_base = {}
    for base, kind, x0, y0, yaw, builder_back in frames:
        origin = Vector((x0, y0))
        along = Vector((math.cos(yaw), math.sin(yaw)))
        normal = Vector((-math.sin(yaw), math.cos(yaw)))
        frames_by_base[base] = (origin, along, normal)
        front, _, _ = bin_contour(occupied, origin, along, normal)
        fronts[base] = front if front is not None else builder_back + BIN_DEPTH
    # each pair shares one frame (its first bin's) so both fronts lie on one line
    pairs = {}
    for base in sorted(fronts):
        pairs.setdefault(base.rsplit("_", 1)[0], []).append(base)
    pair_data = {}
    for pair, members in pairs.items():
        origin_ref, along_ref, normal_ref = frames_by_base[members[0]]
        offsets = {b: ((frames_by_base[b][0] - origin_ref).dot(along_ref), (frames_by_base[b][0] - origin_ref).dot(normal_ref)) for b in members}
        front_ref = sum(fronts[b] + offsets[b][1] for b in members) / len(members)
        mean_u = sum(offsets[b][0] for b in members) / len(members)
        pair_data[pair] = (front_ref, offsets, mean_u)
    for base, kind, x0, y0, yaw, builder_back in frames:
        origin = Vector((x0, y0))
        along = Vector((math.cos(yaw), math.sin(yaw)))
        normal = Vector((-math.sin(yaw), math.cos(yaw)))
        along3 = Vector((along.x, along.y, 0.0))
        normal3 = Vector((normal.x, normal.y, 0.0))

        def world(u, v, z, origin=origin, along=along, normal=normal):
            point = origin + along * u + normal * v
            return (point.x, point.y, z)

        front_ref, offsets, mean_u = pair_data[base.rsplit("_", 1)[0]]
        u_off, v_off = offsets[base]
        front = front_ref - v_off
        width = BIN_WIDTH
        cu = -BIN_PAIR_GAP * 0.5 if u_off < mean_u else BIN_PAIR_GAP * 0.5
        back = front - BIN_DEPTH
        wall_v = wall_face_v(world, normal3, (cu - width * 0.5, cu + width * 0.5), z=0.4)
        if wall_v is not None and back < wall_v - BIN_MAX_WALL_OVERLAP:
            back = wall_v - BIN_MAX_WALL_OVERLAP
            front = back + BIN_DEPTH
        cv = (front + back) * 0.5
        extents[base] = [round(v, 3) for v in (cu, width, back, front)]
        name = BIN_PREFIX + base.replace("Tepper_", "")
        shell = materials["bin_grey"] if kind == "trash" else materials["bin_blue"]
        lid_material = materials["bin_lid_black"] if kind == "trash" else materials["bin_blue"]
        z0 = FLOOR_TOP_Z
        parts = []
        body = mesh_object(name + "_Body", bin_body_mesh(name + "_Body_Data", width, BIN_DEPTH, BIN_BODY_HEIGHT, BIN_CORNER), shell, collection, world(cu, cv, z0), (0.0, 0.0, yaw))
        parts.append(body)
        lid_z = z0 + BIN_BODY_HEIGHT + 0.01  # lid rests on the liner band
        lid = add_box(name + "_Lid", world(cu, cv, lid_z + BIN_LID_HEIGHT * 0.5), (width + 0.01, BIN_DEPTH + 0.01, BIN_LID_HEIGHT), lid_material, collection, rot_z=yaw)
        bevel = lid.modifiers.new("Edge", "BEVEL")
        bevel.width = 0.01
        bevel.segments = 3
        parts.append(lid)
        if kind == "recycling":
            cutter = add_cylinder(name + "_Cutter", world(cu, cv, lid_z + BIN_LID_HEIGHT * 0.5), 0.055, 0.2, None, collection, segments=48)
            cutter.hide_render = True
            cutter.display_type = "WIRE"
            cut(lid, cutter)
            parts.append(cutter)
            label = add_box(name + "_Label", world(cu, front + 0.002, z0 + 0.50), (0.10, 0.004, 0.14), materials["bin_label_print"], collection, rot_z=yaw)
            plate_uv(label, "x")
            parts.append(label)
        for part in (body, lid):
            props.objects.link(part)
    scene["tepper_bin_extents"] = json.dumps(extents)
    return extents


# ----------------------------------------------------------------------------
# Lights, world, render, camera
# ----------------------------------------------------------------------------
def retune_fixtures():
    for obj in bpy.data.collections["Tepper_Lighting"].objects:
        if obj.type == "LIGHT":
            obj.data.energy = FIXTURE_WATTS
            obj.data.color = FIXTURE_COLOR
            obj.data.spread = FIXTURE_SPREAD


def setup_interior_world():
    world = bpy.context.scene.world
    world.use_nodes = True
    tree = world.node_tree
    tree.nodes.clear()
    output = tree.nodes.new("ShaderNodeOutputWorld")
    background = tree.nodes.new("ShaderNodeBackground")
    background.inputs["Color"].default_value = (0.5, 0.55, 0.6, 1.0)
    background.inputs["Strength"].default_value = 0.01
    tree.links.new(background.outputs["Background"], output.inputs["Surface"])


def setup_camera():
    camera = bpy.data.objects["Tepper_Hero_Camera"]
    camera.data.dof.use_dof = False
    bpy.context.scene.camera = camera


def setup_overlay_camera():
    """The builder's orthographic overhead camera, reframed to cover the whole
    map for the overlay check render."""
    camera = bpy.data.objects["Tepper_Overhead_Camera"]
    camera.location = OVERLAY_CAMERA_LOCATION
    camera.data.ortho_scale = OVERLAY_CAMERA_SCALE
    camera.data.clip_start = 0.01
    camera.data.clip_end = 100.0


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------
def main():
    scene = bpy.context.scene
    active = bpy.context.view_layer.objects.active
    if active is not None and active.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    materials = build_materials()
    assign_materials(materials)
    build_recycling_station(materials)
    build_trash_bins(materials)
    bpy.data.orphans_purge(do_recursive=True)
    retune_fixtures()
    setup_interior_world()
    setup_render(PROJECT_ROOT + "/blender/renders/tepper_photoreal_hero.png")
    scene.view_settings.exposure = 0.0
    setup_camera()
    setup_overlay_camera()
    bpy.ops.file.make_paths_relative()
    return {"materials": len(bpy.data.materials), "images": len(bpy.data.images)}


