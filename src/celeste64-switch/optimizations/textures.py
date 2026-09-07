def optimize_textures(out, replace):
    path = out / 'foster/foster_renderer_opengl.c'
    text = path.read_text()
    text = replace(text, 'void* valueCache;', 'void* valueCache;\n    int nextTextureUniform;')
    text = replace(text, 'GLint samplerCount;', 'GLint samplerCount;\n    int firstTextureUniform;')
    text = replace(text, 'shader->samplerCount = 0;', 'shader->samplerCount = 0;\n    shader->firstTextureUniform = -1;\n    int lastTextureUniform = -1;')
    text = replace(text, 'uniform->valueCache = NULL;', 'uniform->valueCache = NULL;\n            uniform->nextTextureUniform = -1;')
    text = replace(text, 'shader->samplerCount += uniform->glSize;', 'shader->samplerCount += uniform->glSize;\n                if (lastTextureUniform < 0) shader->firstTextureUniform = i;\n                else shader->uniforms[lastTextureUniform].nextTextureUniform = i;\n                lastTextureUniform = i;')
    marker = 'void FosterDraw_OpenGL(FosterDrawCommand* command)'
    text = replace(text, marker, 'static int FosterTextureSlotsUnchanged(FosterUniform_OpenGL* uniform, const GLuint* slots)\n{\n    size_t bytes = sizeof(GLuint) * uniform->glSize;\n    if (uniform->valueCache != NULL)\n    {\n        if (SDL_memcmp(uniform->valueCache, slots, bytes) == 0) return 1;\n    }\n    else\n    {\n        uniform->valueCache = SDL_malloc(bytes);\n        if (uniform->valueCache == NULL) return 0;\n    }\n    SDL_memcpy(uniform->valueCache, slots, bytes);\n    return 0;\n}\n\n' + marker)
    start = text.index(marker)
    before, draw = (text[:start], text[start:])
    draw = replace(draw, 'i < FOSTER_MAX_UNIFORM_TEXTURES; i++', 'i < shader->samplerCount && i < FOSTER_MAX_UNIFORM_TEXTURES; i++')
    draw = replace(draw, 'for (int i = 0; i < shader->uniformCount; i++)\n\t\t{\n\t\t\tFosterUniform_OpenGL* uniform = shader->uniforms + i;\n\t\t\tif (uniform->glType != GL_SAMPLER_2D)\n\t\t\t\tcontinue;', 'for (int i = shader->firstTextureUniform; i >= 0; i = shader->uniforms[i].nextTextureUniform)\n        {\n            FosterUniform_OpenGL* uniform = shader->uniforms + i;')
    draw = replace(draw, 'fgl.glUniform1iv(uniform->glLocation, (GLint)uniform->glSize, textureSlots);', 'if (!FosterTextureSlotsUnchanged(uniform, textureSlots))\n                fgl.glUniform1iv(uniform->glLocation, (GLint)uniform->glSize, textureSlots);')
    path.write_text(before + draw)
