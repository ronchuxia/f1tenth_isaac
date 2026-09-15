"""Build the self-contained ROS asset with Isaac Sim's Python."""
from pathlib import Path

from isaacsim import SimulationApp

app = SimulationApp({'headless': True, 'extra_args': ['--/app/settings/persistent=0']})

import omni.graph.core as og
import omni.usd
from pxr import Gf, Sdf, UsdGeom
from isaacsim.core.experimental.utils import app as app_utils
from isaacsim.core.experimental.prims import RigidPrim
from isaacsim.core.simulation_manager import SimulationManager

for extension in ('isaacsim.ros2.bridge', 'isaacsim.robot.wheeled_robots.nodes', 'omni.graph.scriptnode'):
    app_utils.enable_extension(extension)

project = Path(__file__).resolve().parents[2]
output = project / 'assets/robots/f1tenth/f1tenth_ros.usda'

context = omni.usd.get_context()
context.new_stage()
stage = context.get_stage()
UsdGeom.SetStageMetersPerUnit(stage, 1)
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

car = UsdGeom.Xform.Define(stage, '/F1Tenth').GetPrim()
car.GetReferences().AddReference(str(output.parent / 'f1tenth.usda'))
stage.SetDefaultPrim(car)

chassis = '/F1Tenth/Rigid_Bodies/Chassis'
base_link = chassis + '/base_link'

cache = UsdGeom.XformCache()
chassisToWorld = cache.GetLocalToWorldTransform(stage.GetPrimAtPath(chassis)).RemoveScaleShear()
baseToWorld = cache.GetLocalToWorldTransform(stage.GetPrimAtPath(base_link)).RemoveScaleShear()
baseToChassis = baseToWorld * chassisToWorld.GetInverse()

# compute chasis COM to convert COM linear velocity to base_link linear velocity
authored_layer = stage.GetRootLayer().ExportToString()
SimulationManager.setup_simulation(dt=1/120, device='cpu')
app_utils.play()
chasis_body = RigidPrim(chassis, reset_xform_op_properties=False)
chasis_com = Gf.Vec3d(*chasis_body.get_coms()[0].numpy()[0].tolist())
app_utils.stop()
stage.GetRootLayer().ImportFromString(authored_layer)
print('CHASSIS COM (m)', list(chasis_com), flush=True)

keys = og.Controller.Keys

# Drive graph
nodes = [('Tick', 'omni.graph.action.OnPlaybackTick'),
         ('Subscription', 'isaacsim.ros2.bridge.ROS2SubscribeAckermannDrive'),
         ('Ackermann', 'isaacsim.robot.wheeled_robots.AckermannController'),
         ('WheelHeadings', 'omni.graph.scriptnode.ScriptNode'),
         ('Steering', 'isaacsim.core.nodes.IsaacArticulationController'),
         ('Velocity', 'isaacsim.core.nodes.IsaacArticulationController')]

connections = [('Tick.outputs:tick', 'Subscription.inputs:execIn'),
               ('Subscription.outputs:execOut', 'Ackermann.inputs:execIn'),
               ('Subscription.outputs:speed', 'Ackermann.inputs:speed'),
               ('Subscription.outputs:steeringAngle', 'Ackermann.inputs:steeringAngle'),
               ('Tick.outputs:tick', 'WheelHeadings.inputs:execIn'),
               ('WheelHeadings.outputs:execOut', 'Steering.inputs:execIn'),
               ('Ackermann.outputs:execOut', 'Velocity.inputs:execIn'),
               ('Ackermann.outputs:wheelAngles', 'WheelHeadings.inputs:headings'),
               ('WheelHeadings.outputs:positions', 'Steering.inputs:positionCommand'),
               ('Ackermann.outputs:wheelRotationVelocity', 'Velocity.inputs:velocityCommand')]

wheel_headings_node_code = (project / 'src/f1tenth_steering.py').read_text() + '''
import omni.graph.core as og
from isaacsim.core.experimental.prims import Articulation

def setup(db):
    root = str(db.node.get_prim_path()).rsplit('/ROS/', 1)[0]
    db.per_instance_state.steering = F1TenthSteering(root, Articulation(root))

def compute(db):
    db.outputs.positions = db.per_instance_state.steering.joint_targets(db.inputs.headings)
    db.outputs.execOut = og.ExecutionAttributeState.ENABLED
    return True
'''

values = [('Subscription.inputs:topicName', '/drive'), 
          ('Subscription.inputs:queueSize', 1),
          ('Ackermann.inputs:wheelBase', .32), 
          ('Ackermann.inputs:trackWidth', .24),
          ('Ackermann.inputs:frontWheelRadius', .052), 
          ('Ackermann.inputs:backWheelRadius', .052),
          ('Ackermann.inputs:maxWheelRotation', .523599),
          ('Ackermann.outputs:wheelAngles', [0.0, 0.0]),
          ('WheelHeadings.inputs:script', wheel_headings_node_code),
          ('Steering.inputs:targetPrim', [Sdf.Path('/F1Tenth')]),
          ('Velocity.inputs:targetPrim', [Sdf.Path('/F1Tenth')]),
          ('Steering.inputs:jointNames', ['Knuckle__Upright__Front_Left', 'Knuckle__Upright__Front_Right']),
          ('Velocity.inputs:jointNames', ['Wheel__Knuckle__Front_Left', 
                                          'Wheel__Knuckle__Front_Right',
                                          'Wheel__Upright__Rear_Left', 
                                          'Wheel__Upright__Rear_Right'])]

og.Controller.edit({'graph_path': '/F1Tenth/ROS/Drive', 'evaluator_name': 'execution'},
                   {keys.CREATE_NODES: nodes})

# custom ports
conversion = og.Controller.node('/F1Tenth/ROS/Drive/WheelHeadings')
og.Controller.create_attribute(conversion, 'inputs:headings', 'double[]', og.AttributePortType.INPUT)
og.Controller.create_attribute(conversion, 'outputs:positions', 'double[]', og.AttributePortType.OUTPUT)

og.Controller.edit('/F1Tenth/ROS/Drive', {
    keys.CONNECT: [('/F1Tenth/ROS/Drive/' + source, '/F1Tenth/ROS/Drive/' + target) for source, target in connections],
    keys.SET_VALUES: [('/F1Tenth/ROS/Drive/' + name, value) for name, value in values]})

# Sensors graph
nodes = [('Tick', 'omni.graph.action.OnPlaybackTick')]
connections, values = [], []
for name, path, width, height in [('Lidar', base_link + '/lidar', 1, 1),
                                  ('Left', chassis + '/Camera_Left', 640, 480),
                                  ('Right', chassis + '/Camera_Right', 640, 480)]:
    render = name + 'Render'
    nodes.append((render, 'isaacsim.core.nodes.IsaacCreateRenderProduct'))
    connections.append(('Tick.outputs:tick', render + '.inputs:execIn'))
    values.extend([(render + '.inputs:cameraPrim', [Sdf.Path(path)]),
                   (render + '.inputs:width', width), (render + '.inputs:height', height)])
    
    if name == 'Lidar':
        publishers = [('Scan', 'ROS2RtxLidarHelper', '/scan', 'laser')]
        values.append(('Scan.inputs:type', 'laser_scan'))
    else:
        camera = UsdGeom.Camera(stage.GetPrimAtPath(path))
        camera.GetVerticalApertureAttr().Set(camera.GetHorizontalApertureAttr().Get() * height / width)
        publishers = [(name + 'Image', 'ROS2CameraHelper', '/camera/' + name.lower() + '/image_raw', 'camera_' + name.lower() + '_optical'),
                      (name + 'Info', 'ROS2CameraInfoHelper', '/camera/' + name.lower() + '/camera_info', 'camera_' + name.lower() + '_optical')]

    for pub, kind, topic, frame in publishers:
        nodes.append((pub, 'isaacsim.ros2.bridge.' + kind))
        connections.extend([(render + '.outputs:execOut', pub + '.inputs:execIn'),
                            (render + '.outputs:renderProductPath', pub + '.inputs:renderProductPath')])
        values.extend([(pub + '.inputs:topicName', topic), 
                       (pub + '.inputs:frameId', frame),
                       (pub + '.inputs:resetSimulationTimeOnStop', False)])

og.Controller.edit({'graph_path': '/F1Tenth/ROS/Sensors', 'evaluator_name': 'execution'},
                   {keys.CREATE_NODES: nodes, keys.CONNECT: connections, keys.SET_VALUES: values})

# State graph
nodes, connections, values = [], [], []

# 1. Clock
nodes.extend([('Tick', 'omni.graph.action.OnPlaybackTick'),
              ('Time', 'isaacsim.core.nodes.IsaacReadSimulationTime'),
              ('ClockPublish', 'isaacsim.ros2.bridge.ROS2PublishClock')])

connections.extend([('Tick.outputs:tick', 'ClockPublish.inputs:execIn'),
                    ('Time.outputs:simulationTime', 'ClockPublish.inputs:timeStamp')])

values.extend([('Time.inputs:resetOnStop', False),
               ('ClockPublish.inputs:topicName', '/clock')])

# 2. Static TF
cache = UsdGeom.XformCache()
frames = [('BaseToLaserTFStaticPublish', 'laser', 'base_link', base_link + '/lidar', base_link, False),
          ('BaseToCameraLeftOpticalTFStaticPublish', 'camera_left_optical', 'base_link', chassis + '/Camera_Left', base_link, True),
          ('BaseToCameraRightOpticalTFStaticPublish', 'camera_right_optical', 'base_link', chassis + '/Camera_Right', base_link, True)]

for name, child, parent, child_path, parent_path, optical in frames:
    childToWorld = cache.GetLocalToWorldTransform(stage.GetPrimAtPath(child_path)).RemoveScaleShear()
    parentToWorld = cache.GetLocalToWorldTransform(stage.GetPrimAtPath(parent_path)).RemoveScaleShear()
    childToParent = childToWorld * parentToWorld.GetInverse()

    position = childToParent.ExtractTranslation()

    if optical:
        childToParent = Gf.Matrix4d().SetScale(Gf.Vec3d(1, -1, -1)) * childToParent
    rotation = childToParent.RemoveScaleShear().ExtractRotationQuat()

    nodes.append((name, 'isaacsim.ros2.bridge.ROS2PublishRawTransformTree'))

    connections.extend([('Tick.outputs:tick', name + '.inputs:execIn'),
                        ('Time.outputs:simulationTime', name + '.inputs:timeStamp')])
    
    values.extend([(name + '.inputs:parentFrameId', parent),
                   (name + '.inputs:childFrameId', child),
                   (name + '.inputs:topicName', '/tf_static'),
                   (name + '.inputs:staticPublisher', True),
                   (name + '.inputs:translation', list(position)),
                   (name + '.inputs:rotation', [*rotation.GetImaginary(), rotation.GetReal()])])

# 3. Map to base_link TF
nodes.extend([('Identity', 'omni.graph.nodes.ConstantMatrix4d'),
              ('WorldToMap', 'omni.graph.nodes.ConstantMatrix4d'),
              ('BaseInWorld', 'isaacsim.core.nodes.IsaacReadWorldPose'),
              ('BaseToWorldRotation', 'omni.graph.nodes.SetMatrix4Rotation'),
              ('BaseToWorld', 'omni.graph.nodes.SetMatrix4Translation'),
              ('BaseToMap', 'omni.graph.nodes.MatrixMultiply'),
              ('BaseToMapPosition', 'omni.graph.nodes.GetMatrix4Translation'),
              ('BaseToMapOrientation', 'omni.graph.nodes.GetMatrix4Quaternion'),
              ('MapToBaseTFPublish', 'isaacsim.ros2.bridge.ROS2PublishRawTransformTree')])

connections.extend([
    ('Identity.inputs:value', 'BaseToWorldRotation.inputs:matrix'),
    ('BaseInWorld.outputs:orientation', 'BaseToWorldRotation.inputs:rotationAngle'),
    ('BaseToWorldRotation.outputs:matrix', 'BaseToWorld.inputs:matrix'),
    ('BaseInWorld.outputs:translation', 'BaseToWorld.inputs:translation'),
    ('BaseToWorld.outputs:matrix', 'BaseToMap.inputs:a'),
    ('WorldToMap.inputs:value', 'BaseToMap.inputs:b'),
    ('BaseToMap.outputs:output', 'BaseToMapPosition.inputs:matrix'),
    ('BaseToMap.outputs:output', 'BaseToMapOrientation.inputs:matrix'),
    ('BaseToMapPosition.outputs:translation', 'MapToBaseTFPublish.inputs:translation'),
    ('BaseToMapOrientation.outputs:quaternion', 'MapToBaseTFPublish.inputs:rotation'),
    ('OdomCompute.outputs:execOut', 'MapToBaseTFPublish.inputs:execIn'),
    ('Time.outputs:simulationTime', 'MapToBaseTFPublish.inputs:timeStamp')])

values.extend([('BaseInWorld.inputs:prim', [Sdf.Path(base_link)]),
               ('Identity.inputs:value', Gf.Matrix4d(1)),
               ('WorldToMap.inputs:value', Gf.Matrix4d(1)),
               ('MapToBaseTFPublish.inputs:parentFrameId', 'map'),
               ('MapToBaseTFPublish.inputs:childFrameId', 'base_link')])

# 4. Ego odom
nodes.append(('EgoOdomPublish', 'isaacsim.ros2.bridge.ROS2PublishOdometry'))

connections.extend([
    ('OdomCompute.outputs:execOut', 'EgoOdomPublish.inputs:execIn'),
    ('Time.outputs:simulationTime', 'EgoOdomPublish.inputs:timeStamp'),
    ('BaseToMapPosition.outputs:translation', 'EgoOdomPublish.inputs:position'),
    ('BaseToMapOrientation.outputs:quaternion', 'EgoOdomPublish.inputs:orientation'),
    ('BaseLinearVelocityInBase.outputs:result', 'EgoOdomPublish.inputs:linearVelocity'),
    ('BaseAngularVelocityInBase.outputs:result', 'EgoOdomPublish.inputs:angularVelocity')])

values.extend([('EgoOdomPublish.inputs:topicName', '/ego_racecar/odom'),
               ('EgoOdomPublish.inputs:odomFrameId', 'map'),
               ('EgoOdomPublish.inputs:chassisFrameId', 'base_link'),
               ('EgoOdomPublish.inputs:publishRawVelocities', True)])

# 5. Odom
nodes.extend([('OdomCompute', 'isaacsim.core.nodes.IsaacComputeOdometry'),
              ('OdomPublish', 'isaacsim.ros2.bridge.ROS2PublishOdometry'),
              ('BaseToChassis', 'omni.graph.nodes.ConstantMatrix4d'),
              ('ChassisToBase', 'omni.graph.nodes.ConstantMatrix4d'),
              ('ChassisToChasisInitRotation', 'omni.graph.nodes.SetMatrix4Rotation'),
              ('ChassisToChasisInit', 'omni.graph.nodes.SetMatrix4Translation'),
              ('BaseToChasisInit', 'omni.graph.nodes.MatrixMultiply'),
              ('BaseToBaseInit', 'omni.graph.nodes.MatrixMultiply'),
              ('BaseToBaseInitPosition', 'omni.graph.nodes.GetMatrix4Translation'),
              ('BaseToBaseInitOrientation', 'omni.graph.nodes.GetMatrix4Quaternion'),
              ('ChassisToWorld', 'omni.graph.nodes.MatrixMultiply'),
              ('WorldToChassis', 'omni.graph.nodes.OgnInvertMatrix'),
              ('BaseAngularVelocityInChasis', 'omni.graph.nodes.RotateVector'),
              ('ChasisCOMToBase', 'omni.graph.nodes.ConstantVector3d'),
              ('OffsetLinearVelocity', 'omni.graph.nodes.CrossProduct'),
              ('BaseLinearVelocityInChasis', 'omni.graph.nodes.Add'),
              ('BaseLinearVelocityInBase', 'omni.graph.nodes.RotateVector'),
              ('BaseAngularVelocityInBase', 'omni.graph.nodes.RotateVector')])

connections.extend([
    ('Tick.outputs:tick', 'OdomCompute.inputs:execIn'),
    ('OdomCompute.outputs:execOut', 'OdomPublish.inputs:execIn'),
    ('Time.outputs:simulationTime', 'OdomPublish.inputs:timeStamp'),
    ('Identity.inputs:value', 'ChassisToChasisInitRotation.inputs:matrix'),
    ('OdomCompute.outputs:orientation', 'ChassisToChasisInitRotation.inputs:rotationAngle'),
    ('ChassisToChasisInitRotation.outputs:matrix', 'ChassisToChasisInit.inputs:matrix'),
    ('OdomCompute.outputs:position', 'ChassisToChasisInit.inputs:translation'),
    ('BaseToChassis.inputs:value', 'BaseToChasisInit.inputs:a'),
    ('ChassisToChasisInit.outputs:matrix', 'BaseToChasisInit.inputs:b'),
    ('BaseToChasisInit.outputs:output', 'BaseToBaseInit.inputs:a'),
    ('ChassisToBase.inputs:value', 'BaseToBaseInit.inputs:b'),
    ('BaseToBaseInit.outputs:output', 'BaseToBaseInitPosition.inputs:matrix'),
    ('BaseToBaseInit.outputs:output', 'BaseToBaseInitOrientation.inputs:matrix'),
    ('BaseToBaseInitPosition.outputs:translation', 'OdomPublish.inputs:position'),
    ('BaseToBaseInitOrientation.outputs:quaternion', 'OdomPublish.inputs:orientation'),
    ('ChassisToBase.inputs:value', 'ChassisToWorld.inputs:a'),
    ('BaseToWorld.outputs:matrix', 'ChassisToWorld.inputs:b'),
    ('ChassisToWorld.outputs:output', 'WorldToChassis.inputs:matrix'),
    ('WorldToChassis.outputs:invertedMatrix', 'BaseAngularVelocityInChasis.inputs:rotation'),
    ('OdomCompute.outputs:angularVelocity', 'BaseAngularVelocityInChasis.inputs:vector'),
    ('BaseAngularVelocityInChasis.outputs:result', 'OffsetLinearVelocity.inputs:a'),
    ('ChasisCOMToBase.inputs:value', 'OffsetLinearVelocity.inputs:b'),
    ('OdomCompute.outputs:linearVelocity', 'BaseLinearVelocityInChasis.inputs:a'),
    ('OffsetLinearVelocity.outputs:product', 'BaseLinearVelocityInChasis.inputs:b'),
    ('BaseLinearVelocityInChasis.outputs:sum', 'BaseLinearVelocityInBase.inputs:vector'),
    ('ChassisToBase.inputs:value', 'BaseLinearVelocityInBase.inputs:rotation'),
    ('BaseAngularVelocityInChasis.outputs:result', 'BaseAngularVelocityInBase.inputs:vector'),
    ('ChassisToBase.inputs:value', 'BaseAngularVelocityInBase.inputs:rotation'),
    ('BaseLinearVelocityInBase.outputs:result', 'OdomPublish.inputs:linearVelocity'),
    ('BaseAngularVelocityInBase.outputs:result', 'OdomPublish.inputs:angularVelocity')])

values.extend([('OdomCompute.inputs:chassisPrim', [Sdf.Path(chassis)]),
               ('OdomPublish.inputs:topicName', '/odom'),
               ('OdomPublish.inputs:odomFrameId', 'odom'),
               ('OdomPublish.inputs:chassisFrameId', 'base_link'),
               ('OdomPublish.inputs:publishRawVelocities', True),
               ('BaseToChassis.inputs:value', baseToChassis),
               ('ChassisToBase.inputs:value', baseToChassis.GetInverse()),
               ('ChasisCOMToBase.inputs:value', baseToChassis.ExtractTranslation() - chasis_com)])

og.Controller.edit({'graph_path': '/F1Tenth/ROS/State', 'evaluator_name': 'execution'},
                   {keys.CREATE_NODES: nodes, keys.CONNECT: connections, keys.SET_VALUES: values})

layer = Sdf.Layer.CreateNew(str(output))
Sdf.CopySpec(stage.GetRootLayer(), '/F1Tenth', layer, '/F1Tenth')
layer.defaultPrim = 'F1Tenth'
layer.pseudoRoot.SetInfo('metersPerUnit', 1.0)
layer.pseudoRoot.SetInfo('upAxis', 'Z')
layer.GetPrimAtPath('/F1Tenth').referenceList.explicitItems = [Sdf.Reference('f1tenth.usda')]
layer.Save()

context.close_stage()
app.update()
print('BUILT', output, flush=True)
app.close()
