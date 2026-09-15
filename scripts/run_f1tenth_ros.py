import argparse
import json
import sys
from pathlib import Path

from isaacsim import SimulationApp

parser = argparse.ArgumentParser()
parser.add_argument('--headless', action='store_true')
parser.add_argument('--config', required=True, type=Path)
args = parser.parse_args()

project = Path(__file__).resolve().parents[1]
config = json.loads(args.config.read_text())

app = SimulationApp({'headless': args.headless, 'enable_motion_bvh': True})

import omni.usd
import omni.timeline
from isaacsim.core.experimental.utils import app as app_utils
from isaacsim.core.rendering_manager import RenderingManager
from isaacsim.core.simulation_manager import SimulationManager

sys.path.insert(0, str(project / 'src'))
from f1tenth_scene import load_scene

for extension in ('isaacsim.ros2.bridge', 'isaacsim.robot.wheeled_robots.nodes'):
    app_utils.enable_extension(extension)

stage = omni.usd.get_context().get_stage()
car = load_scene(
    stage, 
    project / config['scene'], 
    config['spawn'],
    config['world_to_map']
)

SimulationManager.setup_simulation(dt=1/120, device='cpu')
RenderingManager.set_dt(1/120)
app_utils.play()

if not args.headless:
    from omni.kit.viewport.utility import get_active_viewport

    chase_camera = str(car.GetPath()) + '/Rigid_Bodies/Chassis/Camera_Chase'
    get_active_viewport().set_active_camera(chase_camera)

print('config:', args.config, flush=True)
print('map:', config['map'], flush=True)

while app.is_running():
    app.update()

app.close()
