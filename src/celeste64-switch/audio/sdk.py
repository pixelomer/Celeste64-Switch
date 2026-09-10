#!/usr/bin/env python3
"""Extract verified public-platform FMOD headers and libraries into ignored build inputs."""
import hashlib, io, json, tarfile
from pathlib import Path
root = Path(__file__).resolve().parents[3]
out = root / 'fmod/sdk'
out.mkdir(parents=True, exist_ok=True)
lock = json.loads((root / 'dependencies.json').read_text())['fmod']['platforms']
inputs = {}
for platform, item in lock.items():
    archive = root / 'fmod' / item['filename']
    data = archive.read_bytes()
    if hashlib.sha256(data).hexdigest() != item['sha256']:
        raise RuntimeError('FMOD SDK checksum mismatch: ' + item['filename'])
    inputs[platform] = item['sha256']
    for depth in range(2):
        with tarfile.open(fileobj=io.BytesIO(data)) as t:
            members = t.getmembers()
            nested = [m for m in members if m.isfile() and m.name.endswith('.tar.gz')]
            if platform == 'linux' and (not any(('/api/core/inc/' in m.name for m in members))) and (len(nested) == 1):
                data = t.extractfile(nested[0]).read()
                continue
            for m in members:
                if not m.isfile():
                    continue
                p = m.name
                header = platform == 'linux' and ('/api/core/inc/' in p or '/api/studio/inc/' in p)
                lib = ('/lib/x86_64/' if platform == 'linux' else '/lib/arm64-v8a/') in p
                license = p.endswith('/doc/LICENSE.TXT')
                if header or lib or license:
                    dest = out / ('inc' if header else platform) / Path(p).name
                    dest.parent.mkdir(exist_ok=True)
                    dest.write_bytes(t.extractfile(m).read())
            break
    else:
        raise RuntimeError('Unrecognized nested FMOD SDK layout')
for name in ['inc/fmod.h', 'inc/fmod_studio.h', 'android/libfmod.so', 'android/libfmodstudio.so', 'android/LICENSE.TXT']:
    if not (out / name).is_file():
        raise RuntimeError('Missing FMOD SDK input: ' + name)
manifest = root / 'artifacts/fmod-sdk-inputs.json'
manifest.parent.mkdir(exist_ok=True)
manifest.write_text(json.dumps(inputs, indent=2) + '\n')
