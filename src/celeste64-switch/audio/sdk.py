#!/usr/bin/env python3
"""Extract only local public-platform FMOD SDK inputs into ignored fmod/."""
import pathlib, tarfile, hashlib, json
root = pathlib.Path(__file__).resolve().parents[3]
out = root / 'fmod/sdk'
out.mkdir(parents=True, exist_ok=True)
linux = root / 'fmod/inspection/linux/sdk.tar.gz'
if not linux.exists():
    with tarfile.open(root / 'fmod/fmodstudioapi20218linux.tar.gz') as archive:
        nested = [m for m in archive if m.isfile() and m.name.endswith('.tar.gz')]
        if len(nested) != 1:
            raise RuntimeError('Expected one nested Linux SDK archive')
        linux.parent.mkdir(parents=True, exist_ok=True)
        linux.write_bytes(archive.extractfile(nested[0]).read())
inputs = {}
for platform, archive in [('linux', linux), ('android', root / 'fmod/fmodstudioapi20218android.tar.gz')]:
    inputs[platform] = hashlib.sha256(archive.read_bytes()).hexdigest()
    with tarfile.open(archive) as t:
        for m in t:
            if not m.isfile():
                continue
            p = m.name
            is_header = platform == 'linux' and ('/api/core/inc/' in p or '/api/studio/inc/' in p)
            is_lib = ('/lib/x86_64/' if platform == 'linux' else '/lib/arm64-v8a/') in p
            if is_header or is_lib:
                dst = out / ('inc' if is_header else platform) / pathlib.Path(p).name
                dst.parent.mkdir(exist_ok=True)
                dst.write_bytes(t.extractfile(m).read())
manifest = root / 'artifacts/port-research/fmod/sdk-inputs.json'
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps(inputs, indent=2))
