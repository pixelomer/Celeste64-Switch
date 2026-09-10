#!/usr/bin/env python3
"""Produce a deterministic local SD ZIP, without saves or development configuration."""
import json, zipfile
from pathlib import Path
from common import ROOT, sha256

def package():
    b = ROOT / 'artifacts/celeste64-switch-v120-bootstrap'
    meta = json.loads((b / 'build-options.json').read_text())
    assert all((meta[x] for x in ['aot_dedup', 'sprite_empty', 'sprite_stream', 'sprite_chunk']))
    nro_name = 'celeste64.nro'
    files = {f'switch/celeste64/{nro_name}': b / 'celeste64-switch.nro'}
    for n in ['libfmod.so', 'libfmodstudio.so']:
        files['switch/celeste64/fmod/' + n] = ROOT / 'fmod/sdk/android' / n
    for p in (ROOT / 'licenses').iterdir():
        if p.is_file():
            files['switch/celeste64/licenses/' + p.name] = p
    files['switch/celeste64/licenses/FMOD-SDK-LICENSE.txt'] = ROOT / 'fmod/sdk/android/LICENSE.TXT'
    for name in ['mono-nx', 'foster-0.1.18', 'foster', 'sharpgltf-1.0.5', 'hl2-nx', 'spirv-cross']:
        source = ROOT / 'third_party/upstream' / name
        for p in source.iterdir():
            if p.is_file() and p.name.lower() in ['license', 'license.txt', 'license.md', 'copying', 'copying.txt']:
                files[f'switch/celeste64/licenses/{name}-{p.name}'] = p
    files['switch/celeste64/licenses/Mesa-Licenses.html'] = ROOT / 'artifacts/mesa-renderer-build/mesa-20.1.0-rc3/docs/license.html'
    files['switch/celeste64/licenses/ATTRIBUTION.md'] = ROOT / 'THIRD_PARTY.md'
    files['switch/celeste64/licenses/Celeste64-Source-License.txt'] = ROOT / 'third_party/upstream/celeste64-v1.2-research/Source/License.txt'
    blobs = {n: p.read_bytes() for n, p in files.items()}
    blobs['INSTALL.txt'] = ('Extract this ZIP into the root of your Switch SD card, merging the switch folder.\nLaunch switch/celeste64/' + nro_name + ' with the Homebrew Menu in full application mode (hold R while launching a game).\nAlbum/applet mode does not provide enough memory. Requires a compatible homebrew setup.\nSaves and logs use switch/celeste64/userdata; existing saves are not included or overwritten.\nFMOD libraries use switch/celeste64/fmod. Keep both .so files.\nThis is an unofficial fan port, not made or endorsed by the Celeste team.\nThe generated package contains game assets and FMOD libraries under their own licenses;\nconsult their respective terms before redistribution.\n').encode()
    manifest = {'game_commit': meta['game_commit'], 'game_version': meta['game_version'], 'port_source_commit': meta['port_source_commit'], 'dependencies': json.loads((ROOT / 'dependencies.json').read_text()), 'mesa_archive_sha256': meta['mesa_archive_sha256'], 'files': {n: {'bytes': len(v), 'sha256': __import__('hashlib').sha256(v).hexdigest()} for n, v in blobs.items()}}
    blobs['BUILD-MANIFEST.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    target = dist / ('celeste64-switch-1.2.0' + '.zip')
    temporary = target.with_suffix('.zip.part')
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, data in sorted(blobs.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 33188 << 16
            z.writestr(info, data)
    with zipfile.ZipFile(temporary) as z:
        assert z.testzip() is None
        assert all((z.read(n) == v for n, v in blobs.items()))
    temporary.replace(target)
    target.with_suffix('.zip.sha256').write_text(sha256(target) + '  ' + target.name + '\n')
    print('SD installation ZIP:', target)
    return target
if __name__ == '__main__':
    package()
