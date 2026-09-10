#!/usr/bin/env python3
"""Check administrator-provided tools without installing packages or using sudo."""
import os, platform, re, shutil, subprocess
from pathlib import Path
from common import ROOT

def environment():
    env = os.environ.copy()
    devkit = Path(env.get('DEVKITPRO', '/opt/devkitpro')).resolve()
    env.update(DEVKITPRO=str(devkit), DEVKITA64=str(devkit / 'devkitA64'))
    env['PATH'] = str(devkit / 'devkitA64/bin') + ':' + str(devkit / 'tools') + ':' + env.get('PATH', '')
    javac = shutil.which('javac', path=env['PATH'])
    java = Path(env.get('JAVA_HOME') or (str(Path(javac).resolve().parents[1]) if javac else '/missing-jdk'))
    env['JAVA_HOME'] = str(java)
    if any((c.isspace() for c in str(ROOT) + str(devkit) + str(java))):
        raise RuntimeError('The upstream native Makefiles require repository/tool paths without whitespace.')
    missing = [n for n in ['git', 'python3', 'dotnet', 'cmake', 'ninja', 'meson', 'patch', 'make', 'aarch64-none-elf-gcc', 'aarch64-none-elf-g++', 'elf2nro', 'nacptool', 'javac'] if not shutil.which(n, path=env['PATH'])]
    missing += [str(p) for p in [java / 'include/jni.h', java / 'include/linux/jni_md.h', devkit / 'libnx/lib/libnx.a', devkit / 'meson-cross.sh', *[devkit / 'portlibs/switch/lib' / n for n in ['libSDL2.a', 'libEGL.a', 'libglapi.a', 'libdrm_nouveau.a']]] if not p.is_file()]
    if missing:
        raise RuntimeError('Missing administrator-provided dependencies:\n  ' + '\n  '.join(missing) + '\nSee docs/BUILDING.md.')
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise RuntimeError('The pinned Mono AOT SDK requires Linux x86-64.')
    sdks = subprocess.check_output(['dotnet', '--list-sdks'], env=env, text=True)
    if not any((x.startswith('10.') for x in sdks.splitlines())) or not any((x.startswith('9.') for x in sdks.splitlines())):
        raise RuntimeError('Install .NET SDK 9 and 10 (SDK 9 supplies the net9.0 targeting pack).')
    pacman = shutil.which('dkp-pacman', path=env['PATH']) or str(devkit / 'pacman/bin/pacman')
    if Path(pacman).is_file():
        query = subprocess.run([pacman, '-Q', 'libnx'], capture_output=True, text=True)
        version = re.search('libnx\\s+(\\d+)\\.(\\d+)\\.(\\d+)', query.stdout)
        if version and tuple(map(int, version.groups())) < (4, 10, 0):
            raise RuntimeError('libnx 4.10.0 or newer is required for the Horizon TLS ABI.')
    try:
        __import__('mako')
    except ImportError:
        raise RuntimeError('Install Python Mako for Mesa code generation.') from None
    return env
if __name__ == '__main__':
    try:
        env = environment()
        print('Prerequisites available; SDK/dependency fetching can proceed.')
    except RuntimeError as e:
        raise SystemExit(str(e))
