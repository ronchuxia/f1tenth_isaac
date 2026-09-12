import bpy
import math
import os
import sys
from pathlib import Path
from mathutils import Vector
SCRIPT_DIR = os.path.dirname(__file__)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from race_atrium_common import add_curve, add_ribs_mesh, catmull_rom, samples_along_polyline
PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
MAP_PATH = PROJECT_ROOT + '/maps/race2.png'
MAP_RESOLUTION = 0.05
ASSEMBLY_CENTERING_SHIFT_X = -0.2
BACK_WALL_EXTENSION_Y = 3.0
BLACK_DUCT_RADIUS = 0.2
BLACK_DUCT_RIB_RADIUS = BLACK_DUCT_RADIUS + 0.018
YELLOW_DUCT_RADIUS = 0.15
MIDDLE_TABLE_Y = 0.2
PILLAR_BEHIND_MIDDLE_TABLE_Y = 1.0
PILLAR_TARGET_Y = MIDDLE_TABLE_Y + PILLAR_BEHIND_MIDDLE_TABLE_Y
BACK_ASSEMBLY_FORWARD_SHIFT_Y = PILLAR_TARGET_Y - 8.25
LONG_PILLAR_WIDTH = 0.41
LONG_PILLAR_LENGTH = 1.82
PILLAR_CONTOUR_AXIS_X = 0.8120195968411388
PILLAR_CONTOUR_AXIS_Y = 0.5836301691533387
MAP_TO_WORLD_ROTATION = math.pi * 0.5 - math.atan2(PILLAR_CONTOUR_AXIS_Y, PILLAR_CONTOUR_AXIS_X)
LEFT_PILLAR_WORLD_LOCATION = (-1.1, 2.2)

def annotated_map_to_world(point, z):
    source_left_pillar = Vector((214.0, -65.0))
    source_right_pillar = Vector((245.0, -109.0))
    target_left_pillar = Vector((-1.45 + ASSEMBLY_CENTERING_SHIFT_X, 8.25 + BACK_ASSEMBLY_FORWARD_SHIFT_Y))
    target_right_pillar = Vector((1.45 + ASSEMBLY_CENTERING_SHIFT_X, 8.25 + BACK_ASSEMBLY_FORWARD_SHIFT_Y))
    source_midpoint = (source_left_pillar + source_right_pillar) * 0.5
    target_midpoint = (target_left_pillar + target_right_pillar) * 0.5
    scale = MAP_RESOLUTION
    rotation = MAP_TO_WORLD_ROTATION
    local = Vector((point[0], -point[1])) - source_midpoint
    cosine = math.cos(rotation)
    sine = math.sin(rotation)
    rotated = Vector((local.x * cosine - local.y * sine, local.x * sine + local.y * cosine))
    world = target_midpoint + rotated * scale
    return (world.x, world.y, z)

def retarget_black_duct_endpoints(world_points):
    straight_half_length = (LONG_PILLAR_LENGTH - LONG_PILLAR_WIDTH) * 0.5
    contact_distance = LONG_PILLAR_WIDTH * 0.5 + BLACK_DUCT_RIB_RADIUS
    endpoint_specs = ((0, 1, -straight_half_length), (-1, -2, straight_half_length))
    for (endpoint_index, neighbor_index, head_offset_y) in endpoint_specs:
        head_center = Vector((LEFT_PILLAR_WORLD_LOCATION[0], LEFT_PILLAR_WORLD_LOCATION[1] + head_offset_y, BLACK_DUCT_RADIUS))
        approach = Vector(world_points[neighbor_index]) - head_center
        approach.z = 0.0
        approach.normalize()
        endpoint = head_center + approach * contact_distance
        endpoint.z = BLACK_DUCT_RADIUS
        world_points[endpoint_index] = tuple(endpoint)
    return world_points

def build_map_overlay(collection):
    image = bpy.data.images.load(MAP_PATH, check_existing=True)
    image.filepath = MAP_PATH
    image.reload()
    image.pack()
    (width, height) = image.size
    corners = [annotated_map_to_world((0, 0), 0.012), annotated_map_to_world((0, height), 0.012), annotated_map_to_world((width, height), 0.012), annotated_map_to_world((width, 0), 0.012)]
    mesh = bpy.data.meshes.new('Race2_Map_Ground_Overlay_Data')
    mesh.from_pydata(corners, [], [(0, 1, 2, 3)])
    mesh.update()
    uv_layer = mesh.uv_layers.new(name='Race2_Map_UV')
    uvs = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    for loop in mesh.loops:
        uv_layer.data[loop.index].uv = uvs[loop.vertex_index]
    material = bpy.data.materials.new('Race2_Map_Overlay_Material')
    material.use_nodes = True
    material.diffuse_color = (1.0, 1.0, 1.0, 0.55)
    if hasattr(material, 'surface_render_method'):
        material.surface_render_method = 'DITHERED'
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    mix = nodes.new('ShaderNodeMixShader')
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    emission = nodes.new('ShaderNodeEmission')
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = image
    texture.interpolation = 'Closest'
    mix.inputs[0].default_value = 0.55
    material.node_tree.links.new(transparent.outputs[0], mix.inputs[1])
    material.node_tree.links.new(texture.outputs[0], emission.inputs[0])
    material.node_tree.links.new(emission.outputs[0], mix.inputs[2])
    material.node_tree.links.new(mix.outputs[0], output.inputs[0])
    overlay = bpy.data.objects.new('Race2_Map_Ground_Overlay', mesh)
    collection.objects.link(overlay)
    mesh.materials.append(material)
    overlay.hide_render = True
    overlay['source_path'] = MAP_PATH
    overlay['resolution_m_per_pixel'] = MAP_RESOLUTION
    overlay['alignment'] = 'Pillar midpoint with pillar contours parallel to side walls'
    return overlay

def build_track_from_map(collection, yellow_material, black_material, ring_material, black_ring_material):
    duct_centerlines = [{'name': 'Black_Duct_Outer', 'material': black_material, 'rib_material': black_material, 'radius': BLACK_DUCT_RADIUS, 'spacing': 0.3, 'pillar_endpoints': False, 'subdivisions': 1, 'map_alignment': 'inner surface follows the occupancy return', 'source_points': [(220.775344, 69.151272), (215.848653, 69.886464), (211.394961, 71.338089), (207.557881, 72.652632), (204.314077, 74.10496), (200.972844, 75.698891), (197.774875, 77.584992), (195.665114, 78.491605), (193.862153, 79.686005), (191.940633, 80.767602), (189.960075, 81.840801), (187.979997, 83.010003), (185.980556, 84.281125), (183.922078, 85.584563), (181.834324, 86.911442), (179.747042, 88.25288), (177.690002, 89.600002), (175.67984, 90.950401), (173.696723, 92.309999), (171.715682, 93.682398), (169.711764, 95.0712), (167.660003, 96.480001), (165.557842, 97.930885), (163.421923, 99.421445), (161.25608, 100.918567), (159.064158, 102.389125), (156.850004, 103.800005), (154.602239, 105.134565), (152.318319, 106.414885), (150.015284, 107.665919), (147.710157, 108.912643), (145.419996, 110.180006), (143.147836, 111.471042), (140.882311, 112.769126), (138.618874, 114.069684), (136.352957, 115.368164), (134.079995, 116.660006), (131.777916, 117.941847), (129.449758, 119.216725), (127.128633, 120.489689), (124.847669, 121.76577), (122.639998, 123.050005), (120.495995, 124.384168), (118.393593, 125.764892), (116.471877, 127.149928), (114.672693, 128.528788), (112.651959, 129.878048), (110.775107, 131.159761), (108.83373, 132.407466), (106.886172, 133.620675), (105.273764, 134.360678), (103.515362, 135.250275), (101.53994, 136.263062), (99.410651, 137.327872), (97.234101, 138.484264), (95.116816, 139.771873), (93.165372, 141.230271), (91.296087, 142.846196), (90.180921, 144.392774), (88.996475, 146.408312), (87.924785, 148.668237), (87.262696, 151.176001), (86.926529, 153.918321), (86.883395, 156.809772), (87.100428, 159.764893), (87.544765, 162.698242), (88.277328, 165.642478), (89.320056, 168.654557), (90.581488, 171.685529), (91.970211, 174.686409), (93.39478, 177.608242), (94.864295, 180.435847), (96.439719, 183.201859), (98.107412, 185.929051), (99.853644, 188.640258), (101.664785, 191.358243), (103.526381, 194.187527), (105.447581, 197.11289), (107.449975, 199.977618), (109.555173, 202.624979), (111.784781, 204.898253), (114.138938, 206.721291), (116.603265, 208.198565), (119.177501, 209.444326), (121.861421, 210.572803), (124.654777, 211.698243), (126.496131, 212.343948), (128.531004, 212.942472), (130.94109, 213.552933), (132.867965, 214.036127), (135.802771, 214.43596), (139.675898, 213.825832), (141.977196, 212.92523), (144.37288, 212.069227), (146.629914, 211.088426), (148.752624, 210.138832), (150.723012, 209.194756), (152.538233, 208.15218), (154.225215, 207.049669), (155.811016, 205.925706), (157.322616, 204.818824), (158.723139, 203.725586), (160.032207, 202.854226), (161.330851, 202.051659), (162.92391, 201.151632), (164.843976, 200.296813), (166.782749, 199.335364), (168.700563, 198.252542), (170.246929, 197.096446), (171.957916, 196.043805), (173.420723, 195.054806), (175.230817, 193.793469), (176.588052, 192.840127), (178.293599, 191.398415), (180.216093, 189.867842), (182.437925, 188.234173), (185.008411, 186.501211), (187.872573, 184.678493), (190.956489, 182.760257), (194.186248, 180.740741), (196.478114, 179.350715), (198.72816, 177.924724), (202.332086, 175.484564), (206.02992, 172.967044), (209.739844, 170.449675), (213.380008, 168.009998), (216.949767, 165.625443), (220.503683, 163.244322), (224.042726, 160.900485), (227.567844, 158.627765), (231.080003, 156.460007), (234.614722, 154.422646), (238.17136, 152.493126), (241.696642, 150.633285), (245.137282, 148.804965), (248.440005, 146.970006), (251.58208, 145.13448), (254.599038, 143.323839), (257.524961, 141.528964), (260.393915, 139.740722), (263.239991, 137.949996), (266.06351, 136.137919), (268.841753, 134.31056), (271.574235, 132.496238), (274.26047, 130.723274), (276.899995, 129.020004), (279.482713, 127.43057), (282.008949, 125.936087), (284.493838, 124.470325), (286.95248, 122.967045), (289.399997, 121.360006), (291.86808, 119.605203), (294.346635, 117.746806), (296.788157, 115.850806), (299.145118, 113.983211), (301.369997, 112.209999), (303.443593, 110.578399), (305.397589, 109.044393), (307.260791, 107.537197), (309.061993, 105.985991), (310.82999, 104.32), (312.610068, 102.555997), (314.383037, 100.741201), (316.080963, 98.850395), (317.635915, 96.8584), (318.980011, 94.739996), (320.123934, 92.439834), (321.112972, 89.974715), (321.931029, 87.427683), (322.562076, 84.881762), (322.989992, 82.420003), (323.216388, 80.041444), (323.251985, 77.690725), (323.094403, 75.36928), (322.741204, 73.078567), (322.190013, 70.819999), (321.373449, 68.620486), (320.293133, 66.479041), (319.050093, 64.355359), (317.745376, 62.209122), (316.480019, 59.999995), (315.252415, 57.699039), (313.995217, 55.333115), (312.710812, 52.945679), (311.401602, 50.580164), (310.070018, 48.279992), (308.75777, 45.934316), (307.463284, 43.51416), (306.123931, 41.185833), (304.677042, 39.115678), (303.060008, 37.469994), (301.212006, 36.231674), (299.174799, 35.289839), (297.03961, 34.670151), (294.897594, 34.398322), (292.840006, 34.499994), (290.940237, 35.127357), (289.137523, 36.263272), (287.321672, 37.679519), (285.382566, 39.147828), (283.209989, 40.44), (280.748314, 41.614397), (278.070952, 42.823196), (275.261431, 43.978797), (272.40327, 44.993598), (269.579986, 45.779999), (266.582872, 46.270754), (263.356248, 46.524254), (260.213175, 46.641384), (257.466737, 46.723005), (255.429992, 46.869997), (254.277344, 47.098288), (253.349551, 47.413117), (252.259025, 47.964939), (250.985824, 48.891235), (249.616194, 50.127544)]}, {'name': 'Yellow_Duct_Left_Hook', 'material': yellow_material, 'rib_material': ring_material, 'radius': YELLOW_DUCT_RADIUS, 'spacing': 0.22, 'subdivisions': 1, 'source_points': [(114.000008, 131.999997), (114.986514, 134.929526), (116.108972, 137.041339), (117.414955, 138.701754), (119.064891, 140.45195), (120.936, 141.687999), (122.471995, 142.376003), (124.000006, 142.999995), (125.55201, 143.591994), (127.176007, 144.135996), (128.824002, 144.583999), (130.447989, 144.888008), (132.0, 145.0), (133.480002, 144.903999), (134.919997, 144.632003), (136.320008, 144.207996), (137.679999, 143.656004), (139.00001, 142.999994), (140.34401, 142.239995), (141.712001, 141.36), (143.008003, 140.359999), (144.136004, 139.239998), (144.999991, 138.000007), (145.535995, 136.464004), (145.807998, 134.632), (146.044916, 132.515134), (145.837034, 130.111549), (145.176576, 127.759832)]}, {'name': 'Yellow_Duct_Upper_Hook', 'material': yellow_material, 'rib_material': ring_material, 'radius': YELLOW_DUCT_RADIUS, 'spacing': 0.22, 'subdivisions': 1, 'source_points': [(177.713453, 145.55639), (176.181514, 143.721797), (175.000236, 141.612175), (174.199507, 139.730702), (174.043073, 137.72076), (173.937575, 135.399595), (173.886156, 133.119318), (173.8619, 131.236753), (173.930898, 129.403358), (174.108339, 127.022336), (174.364358, 124.641357), (174.925232, 122.511178), (175.579868, 120.729944), (178.24599, 117.698501), (181.206486, 115.342374), (183.94662, 113.545739), (186.12876, 112.378418), (188.451971, 111.566156), (191.186433, 110.60348), (194.375999, 109.856001), (197.840937, 109.352263)]}, {'name': 'Yellow_Duct_Pillar_Connected', 'material': yellow_material, 'rib_material': ring_material, 'radius': YELLOW_DUCT_RADIUS, 'spacing': 0.22, 'subdivisions': 1, 'map_alignment': 'both surfaces follow the paired occupancy returns', 'source_points': [(132.379122, 170.175611), (134.412597, 170.38146), (136.614959, 170.639495), (138.581046, 170.907132), (140.058348, 171.119083), (142.170043, 171.362543), (143.925445, 171.661713), (145.926022, 171.861556), (147.471315, 171.880644), (149.523349, 171.41824), (151.550648, 170.723911), (153.310564, 169.766837), (154.964722, 168.467869), (156.597078, 167.300363), (158.240091, 166.03619), (159.872709, 164.655382), (161.740379, 162.816994), (163.522798, 161.126067), (164.845591, 159.875739), (166.873836, 158.126955), (168.22154, 156.79702), (170.368106, 154.845959), (172.087477, 153.360354), (173.830272, 151.984676), (175.372831, 150.669553), (177.211166, 149.283999), (178.628924, 148.326888), (180.469607, 147.054096), (182.726388, 145.970676), (184.786272, 144.994184), (186.126408, 144.28489), (188.357301, 143.116954), (189.879188, 142.237867), (192.064829, 141.103196), (194.300435, 139.586368), (196.328447, 137.654038), (198.457244, 135.617808), (199.982238, 133.929104), (201.435133, 132.124426), (202.928021, 130.359757), (203.851262, 129.206046), (205.55527, 127.271928), (206.656478, 125.995023), (208.381087, 123.739544), (209.456767, 121.532061), (210.734846, 119.391155), (211.919998, 117.704001), (213.876808, 115.34787), (215.09969, 113.906398), (217.242027, 112.680845), (219.645025, 111.858304), (221.624339, 111.467531), (223.941095, 111.255879), (226.711986, 110.670119), (228.809663, 109.58555), (230.325219, 108.708974), (232.08057, 107.739843), (233.39137, 106.706917), (235.031505, 105.937892), (236.633167, 106.115447), (238.234708, 106.543905), (240.056799, 106.980155), (241.559005, 107.171627), (242.819655, 107.188758), (244.384003, 106.456), (245.0, 106.0)]}, {'name': 'Yellow_Duct_Lower_Hook', 'material': yellow_material, 'rib_material': ring_material, 'radius': YELLOW_DUCT_RADIUS, 'spacing': 0.22, 'subdivisions': 1, 'source_points': [(131.295573, 192.074457), (132.639572, 192.074456), (134.527575, 192.074454), (136.743566, 192.074462), (139.071578, 192.074455), (141.295583, 192.07445), (143.412054, 192.014296), (145.565012, 191.893976), (147.759719, 191.803743), (150.001476, 191.833823), (152.176018, 191.689937), (154.469266, 191.670137), (156.906807, 191.536536), (159.847864, 191.402709), (162.808318, 191.517917), (165.368068, 192.449933), (167.397855, 194.390104)]}]
    component_summaries = []
    for duct in duct_centerlines:
        radius = duct['radius']
        world_points = [annotated_map_to_world(point, radius) for point in duct['source_points']]
        if duct.get('pillar_endpoints'):
            world_points = retarget_black_duct_endpoints(world_points)
        smooth_points = catmull_rom(world_points, cyclic=False, subdivisions=duct.get('subdivisions', 5))
        add_curve(duct['name'], smooth_points, radius, duct['material'], collection)
        rib_samples = samples_along_polyline(smooth_points, spacing=duct['spacing'])
        add_ribs_mesh(duct['name'] + '_Ribs', rib_samples, BLACK_DUCT_RIB_RADIUS if radius == BLACK_DUCT_RADIUS else radius + 0.018, 0.028, duct['rib_material'], collection)
        source_points = duct['source_points']
        component_summaries.append({'name': duct['name'], 'source_points': len(source_points), 'source_start': list(source_points[0]), 'source_end': list(source_points[-1]), 'material': 'yellow' if duct['material'] == yellow_material else 'black', 'source': 'race2.png and race2-annotated.png', 'map_alignment': duct.get('map_alignment', 'centerline follows map trace')})
    reference = bpy.data.objects.new('Race2_Map_Reference', None)
    reference.empty_display_type = 'IMAGE'
    reference.empty_display_size = 4.0
    reference.hide_render = True
    reference.hide_viewport = True
    reference['source_path'] = MAP_PATH
    collection.objects.link(reference)
    return component_summaries

def build_shared_race2_track(collection, duct_materials):
    return build_track_from_map(collection, duct_materials['yellow_duct'], duct_materials['black_duct'], duct_materials['yellow_rings'], duct_materials['black_rings'])

def build_shared_race2_overlay(collection):
    return build_map_overlay(collection)
