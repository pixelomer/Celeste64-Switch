"""Link the isolated Switch Mesa worker."""
from pathlib import Path
import hashlib, os

def prepare_renderer(out, root, mode):
    assert mode in ('off', 'on')
    lib = root / 'artifacts/mesa-renderer-build/full-lib/libEGL.a'
    assert lib.is_file(), 'Build the isolated Mesa archive first'
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
    s = p.read_text()
    return hashlib.sha256(lib.read_bytes()).hexdigest()
