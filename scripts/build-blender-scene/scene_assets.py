"""Shared mesh, material, lighting and imported asset helpers."""
import math
from tempfile import TemporaryDirectory

import bmesh
import bpy
from mathutils import Matrix, Vector

GENERATED_TEXTURES = TemporaryDirectory(prefix='f1tenth_textures_')

PROJECT_ROOT = "/Users/xiachu/Files/projects/f1tenth_isaac"
ASSET_ROOT = PROJECT_ROOT + "/blender/assets/polyhaven"
TEXTURE_ROOT = ASSET_ROOT + "/textures"
MODEL_ROOT = ASSET_ROOT + "/models"
TEXTURE_SIZE_M = {
    "yellow_brick": 2.0,
    "dirty_carpet": 0.6,
    "granite_tile": 2.3,
    "oak_veneer_01": 1.83,
    "denim_fabric": 0.1,
    "white_plaster_02": 1.0,
}


# ----------------------------------------------------------------------------
# Data helpers
# ----------------------------------------------------------------------------
def get_collection(name, parent):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    if collection.name not in parent.children:
        parent.children.link(collection)
    return collection


def remove_collection_tree(collection):
    for child in list(collection.children):
        remove_collection_tree(child)
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def load_image(path, colorspace):
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = colorspace
    return image


def finalize_mesh(mesh, smooth=False):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    if smooth:
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))


def mesh_object(name, mesh, material, collection, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)):
    if material is not None:
        mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    collection.objects.link(obj)
    return obj


def add_box(name, center, size, material, collection, rot_z=0.0, rot_y=0.0, uv=True):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    mesh = bpy.data.meshes.new(name + "_Data")
    bm.to_mesh(mesh)
    bm.free()
    obj = mesh_object(name, mesh, material, collection, center, (0.0, rot_y, rot_z))
    if uv:
        box_uv(obj)
    return obj


def add_cylinder(name, center, radius, depth, material, collection, segments=32, caps=True, rotation=(0.0, 0.0, 0.0), smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, segments=segments, radius1=radius, radius2=radius, depth=depth)
    mesh = bpy.data.meshes.new(name + "_Data")
    bm.to_mesh(mesh)
    bm.free()
    finalize_mesh(mesh, smooth=smooth)
    obj = mesh_object(name, mesh, material, collection, center, rotation)
    box_uv(obj)
    return obj


def add_polydata(name, vertices, faces, material, collection, smooth=False, uv=True):
    mesh = bpy.data.meshes.new(name + "_Data")
    mesh.from_pydata([tuple(v) for v in vertices], [], faces)
    finalize_mesh(mesh, smooth=smooth)
    obj = mesh_object(name, mesh, material, collection)
    if uv:
        box_uv(obj)
    return obj


def box_uv(obj, layer="BoxUV"):
    """World-space box projection, 1 UV unit = 1 metre."""
    mesh = obj.data
    uv = mesh.uv_layers.get(layer) or mesh.uv_layers.new(name=layer)
    mesh.uv_layers.active = uv
    uv.active_render = True
    matrix = obj.matrix_world if obj.parent else obj.matrix_basis
    normal_matrix = matrix.to_3x3().inverted().transposed()
    for poly in mesh.polygons:
        normal = normal_matrix @ poly.normal
        axis = max(range(3), key=lambda i: abs(normal[i]))
        for loop_index in poly.loop_indices:
            world = matrix @ mesh.vertices[mesh.loops[loop_index].vertex_index].co
            if axis == 0:
                uv.data[loop_index].uv = (world.y, world.z)
            elif axis == 1:
                uv.data[loop_index].uv = (world.x, world.z)
            else:
                uv.data[loop_index].uv = (world.x, world.y)


# ----------------------------------------------------------------------------
# Materials
# ----------------------------------------------------------------------------
def reset_material(name):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    output = tree.nodes.new("ShaderNodeOutputMaterial")
    output.location = (700, 0)
    bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (350, 0)
    tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return material, tree, bsdf


def add_pbr_textures(tree, bsdf, texture_id, projection="UV", size_m=None, saturation=1.0, value=1.0, tint=None, roughness_scale=1.0, roughness_offset=0.0, normal_strength=1.0, ao_strength=1.0, rotation_z=0.0, flatten=None):
    prefix = f"{TEXTURE_ROOT}/{texture_id}/{texture_id}_"
    size = size_m or TEXTURE_SIZE_M[texture_id]
    nodes, links = tree.nodes, tree.links
    coord = nodes.new("ShaderNodeTexCoord")
    coord.location = (-1200, 0)
    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-1000, 0)
    mapping.inputs["Scale"].default_value = (1.0 / size, 1.0 / size, 1.0 / size)
    mapping.inputs["Rotation"].default_value = (0.0, 0.0, rotation_z)
    links.new(coord.outputs["UV" if projection == "UV" else "Object"], mapping.inputs["Vector"])

    def image_node(suffix, colorspace, y):
        node = nodes.new("ShaderNodeTexImage")
        node.location = (-700, y)
        node.image = load_image(f"{prefix}{suffix}_2k.jpg", colorspace)
        node.projection = "FLAT" if projection == "UV" else "BOX"
        node.projection_blend = 0.3
        links.new(mapping.outputs["Vector"], node.inputs["Vector"])
        return node

    diffuse = image_node("diff", "sRGB", 400)
    rough = image_node("rough", "Non-Color", 50)
    normal = image_node("nor_gl", "Non-Color", -300)
    ao = image_node("ao", "Non-Color", -650)

    mix_ao = nodes.new("ShaderNodeMix")
    mix_ao.data_type = "RGBA"
    mix_ao.blend_type = "MULTIPLY"
    mix_ao.location = (-400, 400)
    mix_ao.inputs["Factor"].default_value = ao_strength
    links.new(diffuse.outputs["Color"], mix_ao.inputs[6])
    links.new(ao.outputs["Color"], mix_ao.inputs[7])
    hsv = nodes.new("ShaderNodeHueSaturation")
    hsv.location = (-200, 400)
    hsv.inputs["Saturation"].default_value = saturation
    hsv.inputs["Value"].default_value = value
    links.new(mix_ao.outputs[2], hsv.inputs["Color"])
    color_output = hsv.outputs["Color"]
    if flatten is not None:
        flat_color, flat_factor = flatten
        mix_flat = tree.nodes.new("ShaderNodeMix")
        mix_flat.data_type = "RGBA"
        mix_flat.blend_type = "MIX"
        mix_flat.location = (-50, 600)
        mix_flat.inputs["Factor"].default_value = flat_factor
        mix_flat.inputs[7].default_value = (flat_color[0], flat_color[1], flat_color[2], 1.0)
        links.new(color_output, mix_flat.inputs[6])
        color_output = mix_flat.outputs[2]
    if tint is not None:
        mix_tint = nodes.new("ShaderNodeMix")
        mix_tint.data_type = "RGBA"
        mix_tint.blend_type = "MULTIPLY"
        mix_tint.location = (0, 400)
        mix_tint.inputs["Factor"].default_value = 1.0
        mix_tint.inputs[7].default_value = (tint[0], tint[1], tint[2], 1.0)
        links.new(color_output, mix_tint.inputs[6])
        color_output = mix_tint.outputs[2]
    links.new(color_output, bsdf.inputs["Base Color"])

    rough_math = nodes.new("ShaderNodeMath")
    rough_math.operation = "MULTIPLY_ADD"
    rough_math.location = (-200, 50)
    rough_math.inputs[1].default_value = roughness_scale
    rough_math.inputs[2].default_value = roughness_offset
    links.new(rough.outputs["Color"], rough_math.inputs[0])
    links.new(rough_math.outputs[0], bsdf.inputs["Roughness"])

    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.location = (-200, -300)
    normal_map.inputs["Strength"].default_value = normal_strength
    links.new(normal.outputs["Color"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
    return {"color": color_output, "hsv": hsv, "normal_map": normal_map}


def painted_metal(name, color, roughness=0.32, metallic=0.0, coat=0.25):
    material, tree, bsdf = reset_material(name)
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Coat Weight"].default_value = coat
    noise = tree.nodes.new("ShaderNodeTexNoise")
    noise.location = (-600, 0)
    noise.inputs["Scale"].default_value = 40.0
    noise.inputs["Detail"].default_value = 4.0
    ramp = tree.nodes.new("ShaderNodeMapRange")
    ramp.location = (-300, 0)
    ramp.inputs["To Min"].default_value = roughness - 0.08
    ramp.inputs["To Max"].default_value = roughness + 0.08
    tree.links.new(noise.outputs["Fac"], ramp.inputs["Value"])
    tree.links.new(ramp.outputs["Result"], bsdf.inputs["Roughness"])
    return material


def simple_material(name, color, roughness=0.5, metallic=0.0, emission=None, emission_strength=0.0, coat=0.0):
    material, tree, bsdf = reset_material(name)
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Coat Weight"].default_value = coat
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (emission[0], emission[1], emission[2], 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return material


def glass_material(name, tint=(0.90, 0.95, 0.93), roughness=0.0):
    material, tree, bsdf = reset_material(name)
    bsdf.inputs["Base Color"].default_value = (tint[0], tint[1], tint[2], 1.0)
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["IOR"].default_value = 1.5
    bsdf.inputs["Thin Wall"].default_value = True
    output = tree.nodes["Material Output"]
    light_path = tree.nodes.new("ShaderNodeLightPath")
    light_path.location = (200, 400)
    transparent = tree.nodes.new("ShaderNodeBsdfTransparent")
    transparent.location = (350, 250)
    mix = tree.nodes.new("ShaderNodeMixShader")
    mix.location = (550, 0)
    tree.links.new(light_path.outputs["Is Shadow Ray"], mix.inputs["Fac"])
    tree.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    tree.links.new(transparent.outputs["BSDF"], mix.inputs[2])
    tree.links.new(mix.outputs["Shader"], output.inputs["Surface"])
    return material



# ----------------------------------------------------------------------------
# Imported assets
# ----------------------------------------------------------------------------
def append_model(asset_id):
    path = f"{MODEL_ROOT}/{asset_id}/{asset_id}_2k.blend"
    with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
        names = [
            name for name in data_from.objects
            if ("LOD" not in name or "LOD0" in name)
            and not name.endswith(("_ground", "_geometry_nodes"))
        ]
        data_to.objects = names
    objects = [obj for obj in data_to.objects if obj is not None]
    for obj in objects:
        for material in obj.data.materials if obj.type == "MESH" else []:
            material.name = f"{asset_id}_{material.name}" if not material.name.startswith(asset_id) else material.name
    return objects


def bounds(objects):
    minimum = Vector((1e9, 1e9, 1e9))
    maximum = Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            minimum = Vector(min(a, b) for a, b in zip(minimum, world))
            maximum = Vector(max(a, b) for a, b in zip(maximum, world))
    return minimum, maximum


def facing_yaw(direction):
    """Z rotation that turns the Poly Haven chair (front along -Y at rest) toward direction."""
    return math.atan2(direction[1], direction[0]) - math.atan2(-1.0, 0.0)


class ModelInstancer:
    def __init__(self, asset_id, collection):
        self.asset_id = asset_id
        self.collection = collection
        self.templates = append_model(asset_id)
        self.minimum, self.maximum = bounds(self.templates)
        self.size = self.maximum - self.minimum
        self.uses = 0

    def place(self, name, location, rotation_z=0.0, scale=1.0):
        root = bpy.data.objects.new(name, None)
        root.empty_display_size = 0.2
        root.location = location
        root.rotation_euler = (0.0, 0.0, rotation_z)
        root.scale = (scale, scale, scale)
        self.collection.objects.link(root)
        for template in self.templates:
            obj = template if self.uses == 0 else template.copy()
            obj.name = f"{name}_{template.name.split('.')[0]}"
            obj.parent = root
            obj.matrix_parent_inverse = Matrix.Identity(4)
            self.collection.objects.link(obj)
        self.uses += 1
        return root



# ----------------------------------------------------------------------------
# Render
# ----------------------------------------------------------------------------
def setup_render(output_path, samples=512):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    preferences = bpy.context.preferences.addons["cycles"].preferences
    preferences.compute_device_type = "METAL"
    preferences.get_devices()
    for device in preferences.devices:
        device.use = device.type != "CPU"
    cycles = scene.cycles
    cycles.device = "GPU"
    cycles.samples = samples
    cycles.use_adaptive_sampling = True
    cycles.adaptive_threshold = 0.01
    cycles.use_denoising = True
    cycles.denoiser = "OPENIMAGEDENOISE"
    cycles.denoising_use_gpu = True
    cycles.use_light_tree = True
    cycles.caustics_reflective = False
    cycles.caustics_refractive = False
    cycles.sample_clamp_indirect = 8.0
    cycles.max_bounces = 10
    cycles.glossy_bounces = 4
    cycles.transmission_bounces = 8
    cycles.transparent_max_bounces = 12
    cycles.blur_glossy = 0.5
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    image_settings = scene.render.image_settings
    if hasattr(image_settings, "media_type"):
        image_settings.media_type = "IMAGE"
    image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.filepath = output_path
    scene.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium Contrast", "Medium Contrast", "None"):
        try:
            scene.view_settings.look = look
            break
        except TypeError:
            continue
    scene.view_settings.exposure = 0.4
    scene.view_settings.gamma = 1.0
