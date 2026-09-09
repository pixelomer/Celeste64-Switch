"""Resolve current shader uniform-block bindings once per material layout."""
from pathlib import Path

def optimize_stage_bindings(out, here, replace, native_copy):
    path = out / 'managed/Foster/GraphicsCompat.cs'
    text = path.read_text()
    text = replace(text, 'private readonly byte[][] buffers=new byte[4][];', 'private readonly StageBindings stageBindings=new();\n        private readonly byte[][] buffers=new byte[4][];')
    start = text.index('        internal void Upload()')
    brace = text.index('{', start)
    end = brace + 1
    depth = 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    text = text[:start] + '        internal void Upload() => owner.UploadStage(vertex,buffers,Samplers,FlipTargetSamplers,stageBindings);' + text[end:]
    if native_copy:
        text = replace(text, 'source.CopyTo(buffers[slot]);', 'CopyStageBytes(source,buffers[slot]);')
        project = out / 'managed/Foster/Foster.Framework.csproj'
        project.write_text(project.read_text().replace('</PropertyGroup>', '<DefineConstants>$(DefineConstants);C64_NATIVE_UNIFORM_COPY</DefineConstants></PropertyGroup>', 1))
        (out / 'foster/switch_uniform_copy.c').write_text((here.parent / 'optimizations/uniform_copy.c').read_text())
    path.write_text(text)
    (out / 'managed/Foster/StageBindings.cs').write_text((here / 'optimizations/StageBindings.cs').read_text())
    path = out / 'managed/Foster/Material.cs'
    path.write_text(replace(path.read_text(), 'uniforms.Clear();', 'uniforms.Clear();\n        stageLayoutEpoch=new object();'))
