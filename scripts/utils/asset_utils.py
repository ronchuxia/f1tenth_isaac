from pxr import Sdf, UsdPhysics


def set_contact_material(prim, static_friction, dynamic_friction, restitution):
    material = UsdPhysics.MaterialAPI.Apply(prim)
    material.CreateStaticFrictionAttr(static_friction)
    material.CreateDynamicFrictionAttr(dynamic_friction)
    material.CreateRestitutionAttr(restitution)

    prim.AddAppliedSchema('PhysxMaterialAPI')
    prim.CreateAttribute('physxMaterial:frictionCombineMode', Sdf.ValueTypeNames.Token, custom=False).Set('average')
    prim.CreateAttribute('physxMaterial:restitutionCombineMode', Sdf.ValueTypeNames.Token, custom=False).Set('average')
