#!/usr/bin/env python3
"""Build the selected full-AOT release and a local SD installation ZIP."""
import argparse, os, subprocess, sys
from pathlib import Path
from common import ROOT
from preflight import environment
from icon import prepare_icon
p = argparse.ArgumentParser()
p.add_argument('--icon', type=Path, help='Existing 256x256 baseline JPEG icon, cached under ignored local/icon.jpg')
p.add_argument('--fmod-dir', help='Directory with the original Linux/Android 2.02.18 SDK archives')
p.add_argument('--skip-fetch', action='store_true', help='Reuse already fetched, verified dependencies')
a = p.parse_args()
try:
    env = environment()
except RuntimeError as e:
    raise SystemExit(str(e))
try:
    prepare_icon(a.icon)
except (OSError, ValueError) as e:
    raise SystemExit(str(e))
env = {k: v for k, v in env.items() if not k.startswith('CELESTE64_')}
env.update(CELESTE64_MESA_LARGE_UPLOADS='1')

def run(args):
    subprocess.run(args, cwd=ROOT, env=env, check=True)
if not a.skip_fetch:
    run([sys.executable, 'scripts/fetch.py'])
run([sys.executable, 'scripts/download_fmod.py', *(['--archive-dir', a.fmod_dir] if a.fmod_dir else [])])
run([sys.executable, 'src/celeste64-switch/audio/sdk.py'])
run([sys.executable, 'src/celeste64-switch/renderer/build-mesa-thread.py', '--ensure'])
run(['bash', 'src/celeste64-switch/compat-v120/build-optimized.sh'])
run([sys.executable, 'scripts/package.py'])
