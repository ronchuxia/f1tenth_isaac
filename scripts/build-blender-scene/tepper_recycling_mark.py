"""Convert the outlined recycling glyph to portable geometry."""
import bpy
from mathutils import Vector

def add_mark(name, transform, collection, material):
    font=bpy.data.fonts.load('/System/Library/Fonts/Apple Symbols.ttf',check_existing=True)
    data=bpy.data.curves.new(name,'FONT');data.body='♲';data.font=font
    obj=bpy.data.objects.new(name,data);collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.object.convert(target='MESH');obj=bpy.context.object
    xs=[v.co.x for v in obj.data.vertices];ys=[v.co.y for v in obj.data.vertices]
    cx=(min(xs)+max(xs))/2;cy=(min(ys)+max(ys))/2;scale=.12/(max(ys)-min(ys))
    for v in obj.data.vertices:v.co=transform@Vector((-(v.co.x-cx)*scale,.1418,(v.co.y-cy)*scale+.39))
    obj.data.materials.append(material)
    return obj
