#!/usr/bin/env python3
"""Build a complete isolated Mesa archive from checksum-pinned package sources.

The stock installation is never modified. Rebuild every member together to keep private structures consistent with the
current compiler and newlib headers; do not mix objects from the installed archive.
"""
import hashlib, json, shutil, subprocess, sys, tarfile, urllib.request, os
from pathlib import Path
root = Path(__file__).resolve().parents[3]
out = root / 'artifacts/mesa-renderer-build'
out.mkdir(parents=True, exist_ok=True)
inputs = {'mesa-20.1.0-rc3.tar.xz': ('https://archive.mesa3d.org/older-versions/20.x/mesa-20.1.0-rc3.tar.xz', 'c90b75ea34302ebde9b81b87c5642fa864c40fe9c4ad34ce0793170c1413168d'), 'switch-mesa-20.1.0-5.patch': ('https://raw.githubusercontent.com/devkitPro/pacman-packages/master/switch/mesa/switch-mesa-20.1.0-5.patch', '950f93d3e5b6ae9c5a42c2918623fe9a80d7ee398d92d2e73abec86b62d75916'), 'gl_XML.py.patch': ('https://raw.githubusercontent.com/devkitPro/pacman-packages/master/switch/mesa/gl_XML.py.patch', 'a9bc326195b3fe29709e079466a8b2162a2ac9409f694eaad5494490155e2dd4'), 'glX_XML.py.patch': ('https://raw.githubusercontent.com/devkitPro/pacman-packages/master/switch/mesa/glX_XML.py.patch', '1475defcdf8600690eaddeee28d8f01310635c1273fb541f668e8789714d36ca')}
large = os.environ.get('CELESTE64_MESA_LARGE_UPLOADS') == '1'
lib = out / ('full-lib-large' if large else 'full-lib')
manifest_path = lib / 'manifest.json'
fingerprints = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__), Path(__file__).with_name('patch-mesa-thread.py'), Path(__file__).with_name('patch-mesa-large.py')]}
identity = {'inputs': inputs, 'scripts': fingerprints, 'large_uploads': large, 'compiler': subprocess.check_output(['/opt/devkitpro/devkitA64/bin/aarch64-none-elf-gcc', '--version'], text=True), 'devkitpro_packages': subprocess.check_output(['/opt/devkitpro/pacman/bin/pacman', '-Q'], text=True)}
identity = json.loads(json.dumps(identity))
if '--ensure' in sys.argv and manifest_path.is_file() and (lib / 'libEGL.a').is_file():
    cached = json.loads(manifest_path.read_text())
    if cached.get('identity') == identity and cached.get('archive_sha256') == hashlib.sha256((lib / 'libEGL.a').read_bytes()).hexdigest():
        print('Verified cached Switch Mesa archive:', lib / 'libEGL.a')
        sys.exit(0)
for name, (url, sha) in inputs.items():
    p = out / name
    if not p.exists():
        urllib.request.urlretrieve(url, p)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == sha, name
source = out / 'mesa-20.1.0-rc3'
if source.exists():
    shutil.rmtree(source)
with tarfile.open(out / 'mesa-20.1.0-rc3.tar.xz') as archive:
    archive.extractall(out, filter='data')
for name in list(inputs)[1:]:
    subprocess.run(['patch', '-p1', '-i', str(out / name)], cwd=source, check=True)
subprocess.run([sys.executable, str(Path(__file__).with_name('patch-mesa-thread.py')), str(source)], check=True)
if large:
    subprocess.run([sys.executable, str(Path(__file__).with_name('patch-mesa-large.py')), str(source)], check=True)
build = out / 'thread-build'
if not (build / 'build.ninja').exists():
    subprocess.run(['/opt/devkitpro/meson-cross.sh', 'switch', str(out / 'cross-thread.ini'), str(build), str(source), '-Db_ndebug=true'], check=True)
subprocess.run(['ninja', '-C', str(build), '-j8', 'src/egl/libEGL.a'], check=True)
lib = out / ('full-lib-large' if large else 'full-lib')
lib.mkdir(exist_ok=True)
shutil.copyfile(build / 'src/egl/libEGL.a', lib / 'libEGL.a')
manifest = {'identity': identity, 'archive_sha256': hashlib.sha256((lib / 'libEGL.a').read_bytes()).hexdigest(), 'meson_options': ['-Db_ndebug=true'], 'worker_core': 1}
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
print('Built Switch Mesa archive:', lib / 'libEGL.a', manifest['archive_sha256'])
