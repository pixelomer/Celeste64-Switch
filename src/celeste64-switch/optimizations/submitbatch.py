"""Cross the native boundary once for existing uniform application plus drawing."""

def optimize_submitbatch(out, port, foster, replace):
    p = out / 'managed/Foster/Material.cs'
    s = p.read_text()
    a = s.index('\tinternal unsafe void Apply()')
    b = s.index('\n\t/// <summary>', a)
    method = s[a:b]
    method = replace(method, 'internal unsafe void Apply()', 'internal unsafe void ApplyAndDraw(ref Platform.FosterDrawCommand command)')
    method = replace(method, 'if (Shader == null || Shader.IsDisposed)\n\t\t\treturn;', 'if (Shader == null || Shader.IsDisposed)\n            { Platform.FosterDraw(ref command); return; }')
    method = replace(method, 'SwitchUniforms.FosterShaderApplyUniforms(id, bindings, nativeBindingCount, floatPtr, samplerPtr, texturePtr);', 'SwitchUniforms.FosterShaderApplyAndDraw(id, bindings, nativeBindingCount, floatPtr, samplerPtr, texturePtr, ref command);')
    p.write_text(s[:b] + method + '\n' + s[b:])
    p = out / 'managed/Foster/SwitchUniforms.cs'
    s = p.read_text()
    a = 'internal static unsafe class SwitchUniforms\n{'
    p.write_text(replace(s, a, a + '\n    [DllImport("FosterPlatform", CallingConvention = CallingConvention.Cdecl)]\n    internal static extern void FosterShaderApplyAndDraw(IntPtr shader,\n        SwitchUniformBinding* bindings,int count,float* floats,TextureSampler* samplers,IntPtr* textures,\n        ref Platform.FosterDrawCommand command);\n'))
    upstream = foster / 'Framework/Graphics/Graphics.cs'
    p = out / 'managed/Foster/Graphics.cs'
    s = (p if p.exists() else upstream).read_text()
    start = s.index('\t\t\t// apply material values before drawing')
    end = s.index('Platform.FosterDraw(ref fc);', start) + len('Platform.FosterDraw(ref fc);')
    call = '// Uniforms and draw retain their original native order in one call.\n            if(command.Material is {} material)material.ApplyAndDraw(ref fc);\n            else Platform.FosterDraw(ref fc);'
    p.write_text(s[:start] + call + s[end:])
    project = out / 'managed/Foster/Foster.Framework.csproj'
    s = project.read_text()
    if str(upstream) + ';' not in s:
        project.write_text(replace(s, ' Exclude="', ' Exclude="' + str(upstream) + ';'))
    p = out / 'foster/foster_platform.c'
    p.write_text(p.read_text() + '\n' + (port / 'optimizations/submitbatch.c').read_text())
