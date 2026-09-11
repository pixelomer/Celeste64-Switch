#!/usr/bin/env python3
"""Build the selected runtime and a local SD installation ZIP."""
import argparse, os, subprocess, sys
from pathlib import Path
from common import ROOT
from preflight import environment
from icon import prepare_icon
p = argparse.ArgumentParser()
p.add_argument('--runtime', choices=['nativeaot', 'mono'], default='nativeaot')
p.add_argument('--nativeaot-runtime', type=Path, help='Source-built Horizon .NET 9 runtime checkout (or NATIVEAOT_RUNTIME_ROOT)')
p.add_argument('--icon', type=Path, help='Existing 256x256 baseline JPEG icon, cached under ignored local/icon.jpg')
p.add_argument('--fmod-dir', help='Directory with the original Linux/Android 2.02.18 SDK archives')
p.add_argument('--skip-fetch', action='store_true', help='Reuse already fetched, verified dependencies')
a = p.parse_args()
if a.runtime == 'nativeaot':
    runtime_input = a.nativeaot_runtime or os.environ.get('NATIVEAOT_RUNTIME_ROOT')
    if not runtime_input:
        p.error('NativeAOT requires --nativeaot-runtime or NATIVEAOT_RUNTIME_ROOT; see docs/NATIVEAOT.md')
    runtime_root = Path(runtime_input).resolve()
    if any(c.isspace() for c in str(runtime_root)):
        p.error('The native Makefiles require a runtime path without whitespace')
    for relative in ['artifacts/bin/coreclr/libnx.arm64.Release/aotsdk/System.Private.CoreLib.dll',
                     'artifacts/bin/coreclr/libnx.arm64.Release/aotsdk/libRuntime.WorkstationGC.a',
                     'artifacts/bin/native/net9.0-libnx-Release-arm64/libSystem.Native.a']:
        if not (runtime_root / relative).is_file():
            p.error('Missing Horizon runtime build input: ' + relative)
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
if a.runtime == 'nativeaot':
    env['NATIVEAOT_RUNTIME_ROOT'] = str(runtime_root)

def run(args):
    subprocess.run(args, cwd=ROOT, env=env, check=True)
if not a.skip_fetch:
    run([sys.executable, 'scripts/fetch.py'])
run([sys.executable, 'scripts/download_fmod.py', *(['--archive-dir', a.fmod_dir] if a.fmod_dir else [])])
run([sys.executable, 'src/celeste64-switch/audio/sdk.py'])
run(['bash', 'src/celeste64-switch/compat-v120/bootstrap-shaders.sh'])
run([sys.executable, 'src/celeste64-switch/renderer/build-mesa-thread.py', '--ensure'])
if a.runtime == 'nativeaot':
    run(['bash', 'src/celeste64-switch/nativeaot/build-managed.sh'])
    run([sys.executable, 'src/celeste64-switch/nativeaot/build-native.py'])
else:
    run(['bash', 'src/celeste64-switch/compat-v120/build-optimized.sh'])
run([sys.executable, 'scripts/package.py', '--runtime', a.runtime])
