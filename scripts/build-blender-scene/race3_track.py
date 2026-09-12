import math
import os
import sys
from pathlib import Path
SCRIPT_DIR = os.path.dirname(__file__)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
import race_atrium_common as atrium_common
PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
OVERLAY_PATH = PROJECT_ROOT + '/maps/race3_clean.pgm'
MAP_RESOLUTION = 0.05
MAP_WIDTH = 140
MAP_HEIGHT = 374
TRACK_CENTER_X = 0.0
TRACK_CENTER_Y = 0.0
TRACK_PILLAR_OFFSET_Y = -0.5
RACE3_PERSON_LEFT_MID_LOCATION = (-4.5, -2.0, 0.0)
RACE3_F1TENTH_CAR_ORIGIN = (-4.5, -4.0, 0.0)
atrium_common.PERSON_LEFT_MID_LOCATION = RACE3_PERSON_LEFT_MID_LOCATION
atrium_common.F1TENTH_CAR_ORIGIN = RACE3_F1TENTH_CAR_ORIGIN

def race3_map_to_world(point, z):
    return ((point[0] - MAP_WIDTH * 0.5) * MAP_RESOLUTION + TRACK_CENTER_X, (MAP_HEIGHT * 0.5 - point[1]) * MAP_RESOLUTION + TRACK_CENTER_Y, z)

def offset_closed_polyline(points, distance):
    if len(points) < 3:
        return points
    signed_area = 0.0
    for (current, following) in zip(points, points[1:] + points[:1]):
        signed_area += current[0] * following[1] - following[0] * current[1]
    orientation = 1.0 if signed_area >= 0.0 else -1.0
    offset_points = []
    count = len(points)
    for (index, point) in enumerate(points):
        previous = points[(index - 1) % count]
        following = points[(index + 1) % count]
        tangent_x = following[0] - previous[0]
        tangent_y = following[1] - previous[1]
        tangent_length = math.hypot(tangent_x, tangent_y)
        if tangent_length < 1e-09:
            offset_points.append(point)
            continue
        outward_x = orientation * tangent_y / tangent_length
        outward_y = orientation * -tangent_x / tangent_length
        offset_points.append((point[0] + outward_x * distance, point[1] + outward_y * distance, point[2]))
    return offset_points

def offset_black_centerline(points):
    return offset_closed_polyline(points, atrium_common.BLACK_DUCT_RADIUS)

def offset_yellow_centerline(points):
    return offset_closed_polyline(points, -atrium_common.YELLOW_DUCT_RADIUS)
RACE3_DUCTS = [{'name': 'Race3_Black_Duct_Outer', 'material': 'black_duct', 'rib_material': 'black_rings', 'radius': atrium_common.BLACK_DUCT_RADIUS, 'rib_radius': atrium_common.BLACK_DUCT_RIB_RADIUS, 'spacing': 0.3, 'cyclic': True, 'subdivisions': 5, 'smooth_point_transform': offset_black_centerline, 'map_alignment': 'inner surface overlaps the outer occupied contour', 'source_points': [(0.0, 62.0), (2.153, 52.847), (4.0, 43.568), (6.458, 34.542), (10.0, 25.965), (13.837, 18.0), (18.038, 10.962), (26.441, 7.0), (35.243, 4.0), (44.873, 3.0), (54.089, 1.0), (64.133, 1.0), (74.177, 1.0), (83.393, 1.0), (93.024, 2.0), (100.654, 5.0), (102.201, 14.201), (104.0, 23.5), (105.0, 33.13), (106.0, 42.76), (107.276, 52.276), (108.015, 62.015), (110.0, 71.237), (111.0, 80.867), (113.059, 90.059), (115.0, 99.299), (115.95, 108.95), (117.0, 118.559), (118.0, 128.189), (120.0, 137.405), (120.0, 147.45), (121.0, 157.08), (122.0, 166.71), (123.0, 176.34), (123.272, 186.272), (125.0, 195.601), (126.0, 205.231), (127.0, 214.861), (128.0, 224.491), (127.0, 234.121), (127.824, 243.824), (129.618, 252.0), (129.0, 261.426), (129.0, 271.471), (129.0, 281.515), (128.103, 291.103), (128.0, 300.361), (130.0, 308.991), (132.0, 318.207), (133.0, 327.838), (132.0, 337.468), (130.0, 346.098), (127.0, 354.9), (120.676, 362.324), (113.0, 365.089), (104.695, 368.0), (95.065, 369.0), (85.435, 370.0), (76.448, 367.448), (68.588, 363.588), (62.728, 357.728), (57.0, 350.642), (53.0, 342.84), (50.0, 334.624), (47.0, 325.822), (45.0, 316.606), (43.276, 307.276), (41.83, 297.83), (39.0, 288.958), (38.0, 279.328), (34.665, 270.665), (32.0, 261.725), (28.946, 252.946), (27.0, 243.707), (27.239, 233.761), (29.391, 224.609), (31.544, 215.456), (34.0, 206.429), (36.0, 197.213), (36.0, 187.997), (34.0, 178.781), (31.0, 171.151), (28.0, 162.349), (25.0, 153.547), (23.0, 144.331), (22.0, 134.701), (23.0, 125.071), (25.0, 116.441), (26.0, 106.811), (24.42, 97.42), (19.975, 90.975), (13.287, 84.287), (6.598, 77.598), (2.0, 70.044)]}, {'name': 'Race3_Yellow_Duct_Inner', 'material': 'yellow_duct', 'rib_material': 'yellow_rings', 'radius': atrium_common.YELLOW_DUCT_RADIUS, 'rib_radius': atrium_common.YELLOW_DUCT_RADIUS + 0.018, 'spacing': 0.22, 'cyclic': True, 'subdivisions': 5, 'smooth_point_transform': offset_yellow_centerline, 'map_alignment': 'outer surface overlaps the inner occupied contour', 'source_points': [(29.0, 58.0), (33.709, 52.291), (40.519, 46.0), (47.693, 42.0), (55.867, 39.0), (63.322, 42.322), (68.152, 49.152), (72.0, 56.974), (75.0, 65.734), (77.0, 74.908), (77.0, 84.081), (78.0, 93.67), (79.0, 103.258), (81.305, 112.305), (83.0, 121.605), (83.0, 131.608), (84.0, 141.196), (85.554, 150.554), (86.263, 160.263), (88.0, 169.545), (89.0, 179.134), (89.0, 187.722), (91.0, 196.895), (92.342, 206.342), (94.0, 215.657), (94.0, 225.66), (96.0, 234.833), (96.0, 244.836), (97.0, 254.424), (99.0, 263.012), (100.0, 272.6), (101.0, 282.188), (100.0, 291.776), (98.636, 301.0), (93.876, 308.0), (84.288, 309.0), (79.115, 303.0), (74.544, 295.544), (69.593, 287.593), (65.762, 279.762), (63.0, 272.076), (59.0, 265.488), (55.0, 258.314), (51.0, 251.14), (49.317, 242.683), (51.44, 233.56), (53.0, 224.205), (54.0, 214.617), (55.0, 205.029), (56.0, 195.44), (58.0, 186.267), (58.0, 176.264), (57.0, 166.676), (55.355, 157.355), (50.914, 151.0), (46.326, 145.0), (44.0, 137.567), (46.0, 128.393), (50.0, 120.048), (51.0, 110.459), (51.0, 101.286), (50.0, 91.698), (47.663, 82.663), (43.35, 76.0), (37.539, 71.539), (31.416, 66.416)]}]
_unshifted_outer_points = [((point[0] - MAP_WIDTH * 0.5) * MAP_RESOLUTION, (MAP_HEIGHT * 0.5 - point[1]) * MAP_RESOLUTION, atrium_common.BLACK_DUCT_RADIUS) for point in RACE3_DUCTS[0]['source_points']]
_unshifted_outer_curve = atrium_common.catmull_rom(_unshifted_outer_points, cyclic=True, subdivisions=RACE3_DUCTS[0]['subdivisions'])
_unshifted_black_centerline = offset_black_centerline(_unshifted_outer_curve)
UNSHIFTED_BLACK_CENTER_MAX_Y = max((point[1] for point in _unshifted_black_centerline))
PILLAR_FRONT_EDGE_Y = atrium_common.LEFT_PILLAR_WORLD_LOCATION[1] - atrium_common.LONG_PILLAR_LENGTH * 0.5
TRACK_CENTER_Y = PILLAR_FRONT_EDGE_Y - atrium_common.BLACK_DUCT_RADIUS - UNSHIFTED_BLACK_CENTER_MAX_Y + TRACK_PILLAR_OFFSET_Y

def build_race3_track(collection, duct_materials):
    return atrium_common.build_track_components(collection, RACE3_DUCTS, race3_map_to_world, duct_materials)

def build_race3_overlay(collection):
    return atrium_common.build_image_overlay('Race3_Map_Ground_Overlay', collection, OVERLAY_PATH, race3_map_to_world, MAP_RESOLUTION, 'Map centered with its irregular contour on the pillar side')


def apply_barrier_materials(collection):
    """Use Race2's generated fabric textures on the existing Race3 geometry."""
    import numpy as np
    from atrium_surfaces import duct_fabric_images, material

    wire = material('Race3_Duct_Wire', base=(0.013, 0.012, 0.01),
                    roughness=0.36, metallic=0.18)
    for obj in collection.objects:
        if obj.name.endswith('_Ribs'):
            mat = wire
        elif obj.type == 'CURVE':
            spline = obj.data.splines[0]
            points = np.array([list(p.co)[:3] for p in spline.points])
            if spline.use_cyclic_u:
                points = np.vstack((points, points[0]))
            distances = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
            yellow = obj.name.startswith('Race3_Yellow')
            color, normal = duct_fabric_images(obj.name, distances, yellow)
            color.pack()
            normal.pack()
            mat = material(obj.name + '_Video_Fabric', color, normal=normal,
                           roughness=0.4 if yellow else 0.34, uv='UVMap')
        else:
            continue
        obj.data.materials.clear()
        obj.data.materials.append(mat)
