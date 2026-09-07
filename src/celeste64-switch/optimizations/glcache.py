def optimize_glcache(out, replace):
    path = out / 'foster/foster_renderer_opengl.c'
    text = path.read_text()
    text = replace(text, 'int samplerIndex;\n} FosterUniform_OpenGL;', 'int samplerIndex;\n    void* valueCache;\n} FosterUniform_OpenGL;')
    text = replace(text, 'uniform->samplerIndex = 0;', 'uniform->samplerIndex = 0;\n            uniform->valueCache = NULL;')
    text = replace(text, 'SDL_free(it->uniforms[i].samplerName);', 'SDL_free(it->uniforms[i].samplerName);\n        SDL_free(it->uniforms[i].valueCache);')
    marker = 'void FosterShaderSetUniform_OpenGL(FosterShader* shader, int index, float* values)'
    text = replace(text, marker, '// Uniform storage is per GL program and is immutable in size after linking.\n// Every float uniform write in this backend passes through this function.\nstatic int FosterUniformValueUnchanged(FosterUniform_OpenGL* uniform, const float* values, int components)\n{\n    size_t bytes = sizeof(float) * components * uniform->glSize;\n    if (uniform->valueCache != NULL)\n    {\n        if (SDL_memcmp(uniform->valueCache, values, bytes) == 0) return 1;\n    }\n    else\n    {\n        uniform->valueCache = SDL_malloc(bytes);\n        if (uniform->valueCache == NULL) return 0; // Keep submitting on allocation failure.\n    }\n    SDL_memcpy(uniform->valueCache, values, bytes);\n    return 0;\n}\n\n' + marker)
    for gltype, components in [('GL_FLOAT', 1), ('GL_FLOAT_VEC2', 2), ('GL_FLOAT_VEC3', 3), ('GL_FLOAT_VEC4', 4), ('GL_FLOAT_MAT3x2', 6), ('GL_FLOAT_MAT4', 16)]:
        start = text.index(marker)
        before, setter = (text[:start], text[start:])
        setter = replace(setter, f'case {gltype}:\n\t\t\t', f'case {gltype}:\n            if (FosterUniformValueUnchanged(uniform, values, {components})) return;\n\t\t\t')
        text = before + setter
    path.write_text(text)
