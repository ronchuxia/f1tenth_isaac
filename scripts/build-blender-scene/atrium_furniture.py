"""Apply the requested furniture, circulation and redundant object cleanup."""
import sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT = Path('/Users/xiachu/Files/projects/f1tenth_isaac')
sys.path.insert(0, str(ROOT / 'scripts/build-blender-scene'))
from atrium_interior import block, SERVICES

def main():
    col = bpy.data.collections['Race2_Video_Refinement_Marked']
    for (i, (x, y)) in enumerate([(-4.85, 9.7), (4.1, 9.7)]):
        root = bpy.data.objects[f'Indoor_Tree_{i:02}']
        root.location = (x, y, 0.45)
        for name in (f'Planter_{i:02}', f'Planter_Soil_{i:02}'):
            o = bpy.data.objects[name]
            o.location.x = x
            o.location.y = y
            bpy.context.view_layer.update()
            world = o.matrix_world.copy()
            o.parent = root
            o.matrix_world = world
    sources = [o for o in bpy.data.objects if o.name == 'Race_Table_0' or o.name.startswith('Race_Table_0_')]
    for (i, (x, y)) in enumerate(((x, y) for x in (-4.85, 4.85) for y in (-18.8, -15.6))):
        delta = Vector((x - 5.15, y + 4.8, 0))
        for source in sources:
            o = source.copy()
            o.name = f'NSH_Detail_Dining_{i}_{source.name}'
            col.objects.link(o)
            o.location += delta
            o['asset_source'] = source.name
        for (side, dy) in [('North', 1.16), ('South', -1.16)]:
            source = bpy.data.objects['Cafe_Chair_00_' + side]
            root = source.copy()
            root.name = f'NSH_Detail_Dining_{i}_Chair_{side}'
            col.objects.link(root)
            root.location = Vector((x, y + dy, source.location.z))
            for child in source.children:
                o = child.copy()
                o.name = root.name + '_Mesh'
                o.parent = root
                col.objects.link(o)
                o['asset_source'] = child.name
    cream = bpy.data.materials['NSH_Cream_Structure']
    block('Passage_Ceiling', (3.44, 13.15, 2.75), (1.64, 2.1, 0.2), cream, col, True)
    from atrium_architecture import tube
    for (y, w) in SERVICES:
        n = int((w - 0.12) / 0.6)
        for j in range(n):
            cy = y + (j - (n - 1) / 2) * 0.6
            o = block('Counter_Cabinet_Door', (-7.615, cy, 0.54), (0.045, 0.591, 0.78), bpy.data.materials['NSH_Counter_Laminate'], col, radius=0.004)
            tube('NSH_Detail_Cabinet_Handle', [(-7.57, cy + 0.17, 0.64), (-7.57, cy + 0.17, 0.83)], 0.009, bpy.data.materials['Race2_Table_Steel'], col)
