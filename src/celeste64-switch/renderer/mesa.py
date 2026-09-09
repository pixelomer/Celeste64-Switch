"""Link the isolated Switch Mesa worker."""
from pathlib import Path
import hashlib, os, shutil

def prepare_renderer(out, root, mode):
    assert mode in ('off', 'on')
    large = os.environ.get('CELESTE64_MESA_LARGE_UPLOADS') == '1'
    lib = root / 'artifacts/mesa-renderer-build' / ('full-lib-large' if large else 'full-lib') / 'libEGL.a'
    assert lib.is_file(), 'Build the isolated Mesa archive first'
    if lib.with_name('manifest.json').exists():
        shutil.copyfile(lib.with_name('manifest.json'), out / 'mesa-build-manifest.json')
    p = out / 'Makefile'
    s = p.read_text()
    assert s.count('-lEGL ') == 1
    p.write_text(s.replace('-lEGL ', str(lib) + ' '))
    p = out / 'foster/foster_renderer_opengl.c'
    s = p.read_text()
    anchor = 'fgl.context = SDL_GL_CreateContext(state->window);'
    assert s.count(anchor) == 1
    debug = 'if (fgl.glDebugMessageCallback != NULL && state->logLevel != FOSTER_LOGGING_NONE)'
    assert s.count(debug) == 1
    s = s.replace(debug, 'if (0 && fgl.glDebugMessageCallback != NULL && state->logLevel != FOSTER_LOGGING_NONE)')
    p.write_text(s.replace(anchor, 'setenv("CELESTE64_MESA_THREAD", "' + ('true' if mode == 'on' else 'false') + '", 1);\n    ' + anchor))
    return hashlib.sha256(lib.read_bytes()).hexdigest()
