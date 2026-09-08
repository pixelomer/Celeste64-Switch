#!/usr/bin/env python3
"""Assemble a local install zip using the user-supplied Android FMOD libraries."""
from pathlib import Path
import hashlib, json, shutil, sys, zipfile
root = Path(__file__).resolve().parents[3]
out = Path(sys.argv[1]).resolve()
if out.parent != root / 'artifacts' or not out.name.startswith('celeste64-switch'):
    raise ValueError('Expected a port build folder in artifacts/')
stage = out / 'sdcard'
nro_name = 'celeste64-switch-fmod.nro'
files = {f'switch/{nro_name}': out / 'celeste64-switch.nro'}
for name in ('libfmod.so', 'libfmodstudio.so'):
    files['switch/celeste64/fmod/' + name] = root / 'fmod/sdk/android' / name
files['LICENSE-loader.txt'] = root / 'third_party/upstream/hl2-nx/LICENSE'
hashes = {}
for relative, source in files.items():
    target = stage / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    hashes[relative] = hashlib.sha256(target.read_bytes()).hexdigest()
(stage / 'INSTALL.txt').write_text('Copy the switch folder to the root of the SD card. Launch the FMOD NRO in full application mode. Existing saves stay in switch/celeste64. This local package includes the supplied FMOD Android 2.02.18 libraries; they are external to the NRO.\n')
(out / 'install-manifest.json').write_text(json.dumps(hashes, indent=2) + '\n')
with zipfile.ZipFile(out / 'sd-install.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for relative in [*files, 'INSTALL.txt']:
        z.write(stage / relative, relative)
print(out / 'sd-install.zip')
