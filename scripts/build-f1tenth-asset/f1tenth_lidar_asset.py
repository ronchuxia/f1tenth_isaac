"""Author the project's planar RTX LiDAR in the vehicle override layer."""
from pxr import Gf, Sdf, UsdGeom


def add_lidar(stage, chassis):
    legacy = stage.GetPrimAtPath(chassis.GetPath().AppendChild('Lidar'))
    base = stage.GetPrimAtPath(chassis.GetPath().AppendChild('base_link'))

    # lidar pose relative to base_link
    cache = UsdGeom.XformCache()
    pose = cache.GetLocalToWorldTransform(legacy) * cache.GetLocalToWorldTransform(base).GetInverse()

    # deactivate legacy lidar
    legacy.SetActive(False)

    # add OmniLidar
    prim = stage.DefinePrim(base.GetPath().AppendChild('lidar'), 'OmniLidar')
    prim.AddAppliedSchema('OmniSensorGenericLidarCoreAPI')
    transform = Gf.Matrix4d(pose.ExtractRotation(), pose.ExtractTranslation())
    UsdGeom.Xformable(prim).AddTransformOp().Set(transform)

    def attr(name, type_name, value):
        prim.CreateAttribute('omni:sensor:' + name, type_name, custom=False).Set(value)

    attr('modelName', Sdf.ValueTypeNames.String, 'Hokuyo UST-10LX')
    attr('tickRate', Sdf.ValueTypeNames.Float, 40)
    # 270 degrees of a 40 Hz revolution, 0.25 degree steps.
    for name, value in [('scanType', 'ROTARY'), 
                        ('rayType', 'IDEALIZED'), ('rotationDirection', 'CCW'),
                        ('outputFrameOfReference', 'SENSOR'),
                        ('outputMotionCompensationState', 'NONCOMPENSATED')]:
        attr('Core:' + name, Sdf.ValueTypeNames.Token, value)
    for name, value in [('scanRateBaseHz', 40), 
                        ('patternFiringRateHz', 57600),
                        ('numberOfEmitters', 1), 
                        ('numberOfChannels', 1), 
                        ('maxReturns', 1)]:
        attr('Core:' + name, Sdf.ValueTypeNames.UInt, value)
    for name, value in [('nearRangeM', 0.05), 
                        ('minDistBetweenEchosM', 0.05),
                        ('farRangeM', 10),
                        ('azimuthErrorStd', 0), 
                        ('elevationErrorStd', 0),
                        ('rangeAccuracyM', 0),
                        ('startAzimuthOffsetDeg', -135),
                        ('validStartAzimuthDeg', 0), 
                        ('validEndAzimuthDeg', 270.25)]:    # End angle is exclusive
        attr('Core:' + name, Sdf.ValueTypeNames.Float, value)
    for name in ('accumulateOutputs', 'skipDroppingInvalidPoints'):
        attr('Core:' + name, Sdf.ValueTypeNames.Bool, True)
    prefix = 'Core:emitterState:s001:'
    attr(prefix + 'azimuthDeg', Sdf.ValueTypeNames.FloatArray, [0])
    attr(prefix + 'elevationDeg', Sdf.ValueTypeNames.FloatArray, [0])
    attr(prefix + 'channelId', Sdf.ValueTypeNames.UIntArray, [1])
    attr(prefix + 'fireTimeNs', Sdf.ValueTypeNames.UIntArray, [0])
    for name in ('distanceCorrectionM', 'emitterPeakPowerW', 'focalDistM', 'focalSlope', 'horOffsetM', 'vertOffsetM'):
        attr(prefix + name, Sdf.ValueTypeNames.FloatArray, [0])
