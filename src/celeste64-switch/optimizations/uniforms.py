"""Move the existing uniform submission loop across the managed/native boundary."""

def optimize_uniforms(out, port, foster, replace):
    source = foster / 'Framework/Graphics/Material.cs'
    dest = out / 'managed/Foster/Material.cs'
    text = (dest if dest.exists() else source).read_text()
    text = replace(text, 'private readonly List<Uniform> uniforms = new();', 'private readonly List<Uniform> uniforms = new();\n    private SwitchUniformBinding[] nativeBindings = [];\n    private int nativeBindingCount;')
    text = replace(text, 'uniforms.Clear();', 'uniforms.Clear();\n        nativeBindingCount = 0;')
    text = replace(text, 'if (samplerLength > samplerBuffer.Length)', 'if (nativeBindings.Length < uniforms.Count)\n            Array.Resize(ref nativeBindings, uniforms.Count);\n        nativeBindingCount = 0;\n        foreach (var uniform in uniforms)\n        {\n            int kind = IsFloat(uniform.Type) ? 0 : uniform.Type == UniformType.Sampler2D ? 1 : uniform.Type == UniformType.Texture2D ? 2 : -1;\n            if (kind >= 0)\n                nativeBindings[nativeBindingCount++] = new SwitchUniformBinding\n                { Kind = kind, Index = uniform.Index, Offset = uniform.BufferStart };\n        }\n\n        if (samplerLength > samplerBuffer.Length)')
    begin = text.index('\t\t\t// apply each uniform value')
    end = text.index('\n\t\t}\n\t}', begin)
    text = text[:begin] + '            fixed (SwitchUniformBinding* bindings = nativeBindings)\n                SwitchUniforms.FosterShaderApplyUniforms(id, bindings, nativeBindingCount, floatPtr, samplerPtr, texturePtr);' + text[end:]
    dest.write_text(text)
    project = out / 'managed/Foster/Foster.Framework.csproj'
    xml = project.read_text()
    if str(source) + ';' not in xml:
        project.write_text(replace(xml, ' Exclude="', ' Exclude="' + str(source) + ';'))
    (out / 'managed/Foster/SwitchUniforms.cs').write_text((port / 'optimizations/SwitchUniforms.cs').read_text())
    native = out / 'foster/foster_platform.c'
    native.write_text(native.read_text() + '\n' + (port / 'optimizations/uniforms.c').read_text())
