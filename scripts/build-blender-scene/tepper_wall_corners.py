"""Replace the short overlapping wall end caps with their shared plane intersection."""
import bmesh,math
from mathutils import Vector

def miter_corners(o):
 bm=bmesh.new();bm.from_mesh(o.data);adj={}
 for f in bm.faces:
  vs=[o.matrix_world@v.co for v in f.verts];pts=[]
  for a,b in zip(vs,vs[1:]+vs[:1]):
   if min(a.z,b.z)<1.5<max(a.z,b.z):
    p=a+(b-a)*((1.5-a.z)/(b.z-a.z));pts.append((round(p.x,5),round(p.y,5)))
  if len(pts)==2 and pts[0]!=pts[1]:
   a,b=pts;adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
 assert all(len(v)==2 for v in adj.values())
 seen=set();loops=[]
 for a in adj:
  if a in seen:continue
  loop=[];prev=None;p=a
  while p not in seen:
   seen.add(p);loop.append(p);n=[q for q in adj[p] if q!=prev];prev,p=p,n[0]
  loops.append(loop)
 changes=[]
 for loop in loops:
  N=len(loop)
  for i in range(N):
   a,b=loop[i],loop[(i+1)%N]
   if math.dist(a,b)<.4:continue
   mids=[b];j=(i+1)%N;length=0
   while j!=i:
    c,d=loop[j],loop[(j+1)%N];L=math.dist(c,d)
    if L>.4:break
    length+=L;mids.append(d);j=(j+1)%N
   if len(mids)<2 or length>.4:continue
   u=Vector(b)-Vector(a);v=Vector(d)-Vector(c);cross=u.x*v.y-u.y*v.x
   if abs(cross)/(u.length*v.length)<.3:continue
   ac=Vector(c)-Vector(a);t=(ac.x*v.y-ac.y*v.x)/cross;p=Vector(a)+t*u
   if max((p-Vector(q)).length for q in mids)>.22:continue
   changes.append({'points':mids,'corner':list(p)})
 inv=o.matrix_world.inverted()
 # The third changing room header shares an internal end cap with its jamb.
 # Keep only the jamb face below the existing 2.52 metre door opening.
 for f in list(bm.faces):
  points=[o.matrix_world@v.co for v in f.verts]
  if all(9.35<p.x<9.39 and 15.53<p.y<15.71 for p in points):
   clipped=[]
   for p in points:
    p.z=min(p.z,2.52);key=tuple(round(x,5) for x in p)
    if key not in [k for k,q in clipped]:clipped.append((key,p))
   bm.faces.remove(f)
   if len(clipped)>=3:bm.faces.new([bm.verts.new(inv@p) for key,p in clipped])
 for v in bm.verts:
  w=o.matrix_world@v.co;xy=w.xy
  for change in changes:
   pts=[Vector(q) for q in change['points']];hit=False
   for a,b in zip(pts,pts[1:]):
    d=b-a;t=max(0,min(1,(xy-a).dot(d)/d.length_squared))
    if (xy-a-t*d).length<.00008:hit=True;break
   if hit:
    w.x,w.y=change['corner'];v.co=inv@w;break
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001)
 bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0001)
 bmesh.ops.dissolve_limit(bm,angle_limit=.0001,verts=list(bm.verts),edges=list(bm.edges))
 bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.calc_area()<1e-8],context='FACES_ONLY')
 bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
 # Boolean cuts can leave collinear vertices on only one side of a shared edge.
 # Split the opposite edge at those same stations before welding the corner.
 while True:
  split=False
  for e in list(bm.edges):
   if e.is_manifold:continue
   a,b=e.verts;d=b.co-a.co
   for v in list(bm.verts):
    if v in e.verts:continue
    t=(v.co-a.co).dot(d)/d.length_squared
    if .00015<t*d.length<d.length-.00015 and (v.co-a.co-t*d).length<.00008:
     bmesh.utils.edge_split(e,a,t);split=True;break
   if split:break
  if not split:break
  bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001)
 bm.verts.index_update();keys=set();duplicates=[]
 for f in bm.faces:
  key=tuple(sorted(v.index for v in f.verts))
  if key in keys:duplicates.append(f)
  keys.add(key)
 bmesh.ops.delete(bm,geom=duplicates,context='FACES_ONLY')
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 return changes
