"""Prepare native FMOD loader inputs from pinned, locally supplied SDKs."""
from pathlib import Path
import hashlib, json, subprocess, os

def prepare_audio(root, out):
    preferred_core = os.environ.get('CELESTE64_AUDIO_PREFERRED_CORE', '1')
    if preferred_core not in ('1', '2'):
        raise ValueError('Audio preferred core must be 1 or 2')
    port = root / 'src/celeste64-switch/audio'
    sdk = root / 'fmod/sdk'
    if not (sdk / 'inc/fmod.h').exists():
        subprocess.run(['python3', str(port / 'sdk.py')], check=True)
    up = root / 'third_party/upstream/hl2-nx'
    assert subprocess.check_output(['git', '-C', str(up), 'rev-parse', 'HEAD'], text=True).strip() == '41e045ea275fcfae906009f165a6635725e9a08f'
    from .fmod_imports import generate_imports
    generate_imports(sdk, out / 'foster', release=True)
    source = (up / 'source/so_util.c').read_text()
    source = source.replace('#include "config.h"', '').replace('#include "util.h"', 'int c64_loader_log(const char*,...);').replace('#include "error.h"', 'void c64_audio_fatal(const char*,...) __attribute__((noreturn));')
    source = source.replace('debugPrintf', 'c64_loader_log').replace('fatal_error', 'c64_audio_fatal')
    source = source.replace('envGetOwnProcessHandle()', 'c64ProcessHandle()').replace('#include <switch.h>', '#include <switch.h>\nHandle c64ProcessHandle(void);')
    source = source.replace('  return 0;\n}\n\nvoid so_execute_init_array', '  return missing;\n}\n\nvoid so_execute_init_array')
    (out / 'foster/switch_audio_loader.c').write_text(source)
    (out / 'foster/so_util.h').write_bytes((up / 'source/so_util.h').read_bytes())
    for name in ['compat', 'jni', 'engine']:
        (out / f'foster/switch_audio_{name}.c').write_bytes((port / f'{name}.c').read_bytes())
    import shutil
    shutil.copytree(root / 'third_party/upstream/celeste64-v1.1.1/Content/Audio', out / 'romfs/Content/Audio', dirs_exist_ok=True)
    inputs = [sdk / 'android/libfmod.so', sdk / 'android/libfmodstudio.so', *sorted((sdk / 'inc').glob('*.h'))]
    (out / 'audio-inputs.json').write_text(json.dumps({str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}, indent=2) + '\n')
    java = Path(os.environ['JAVA_HOME'])
    return f' -DC64_AUDIO_RELEASE -DC64_AUDIO_PREFERRED_CORE={preferred_core} -D_GNU_SOURCE -I{sdk}/inc -I{out}/foster -I{java}/include -I{java}/include/linux'
