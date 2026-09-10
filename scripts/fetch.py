#!/usr/bin/env python3
"""Fetch exact source revisions and the pinned Linux x64 Mono/ICU SDK."""
import json, platform, subprocess
from pathlib import Path
from common import ROOT, download, extract_sdk_zip, sha256
lock = json.loads((ROOT / 'dependencies.json').read_text())
if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'AMD64'):
    raise SystemExit('The pinned AOT SDK requires Linux x86-64.')
for source in lock['sources']:
    dest = ROOT / 'third_party/upstream' / source['name']
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'init', '--quiet', str(dest)], check=True)
        subprocess.run(['git', '-C', str(dest), 'remote', 'add', 'origin', source['url']], check=True)
        subprocess.run(['git', '-C', str(dest), 'fetch', '--depth=1', 'origin', source['commit']], check=True)
        subprocess.run(['git', '-C', str(dest), 'checkout', '--detach', '--quiet', source['commit']], check=True)
    actual = subprocess.check_output(['git', '-C', str(dest), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != source['commit']:
        raise SystemExit(f"{source['name']}: wrong revision; refusing to reset your checkout")
    subprocess.run(['git', '-C', str(dest), 'diff', '--exit-code', 'HEAD', '--'], check=True)
    print('Pinned source:', source['name'], actual, flush=True)
sdk = lock['mono_sdk']
archive = ROOT / 'downloads/mono-nx-sdk-linux-x64.zip'
download(sdk['url'], archive, sdk['sha256'])
destination = ROOT / 'third_party/upstream/mono-nx'
stamp = destination / '.port-sdk-sha256'
required = [destination / 'dotnet_runtime/artifacts/bin/mono/linux.x64.Debug/cross/linux-x64/libnx-arm64/mono-aot-cross', destination / 'icu/libnx/share/icu/77.1/icudt77l.dat']
if not stamp.exists() or stamp.read_text().strip() != sdk['sha256'] or (not all((p.is_file() for p in required))):
    extract_sdk_zip(archive, destination)
    stamp.write_text(sdk['sha256'] + '\n')
print('Pinned Mono AOT + full ICU SDK ready.', flush=True)
