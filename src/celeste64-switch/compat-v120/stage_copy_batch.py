"""Copy the ordinary three stage buffers through one native boundary."""

def optimize_stage_copy_batch(out, here, replace):
    (out / 'managed/Foster/StageCopyBatch.cs').write_text((here / 'optimizations/StageCopyBatch.cs').read_text())
    (out / 'foster/switch_stage_copy_batch.c').write_text((here / 'optimizations/stage_copy_batch.c').read_text())
    path = out / 'managed/Foster/GraphicsCompat.cs'
    s = path.read_text()
    s = replace(s, 'private readonly StageBindings stageBindings=new();', 'internal readonly StageBindings stageBindings=new();')
    s = replace(s, 'private readonly byte[][] buffers=new byte[4][];', 'internal readonly byte[][] buffers=new byte[4][];')
    s = replace(s, 'vertexStage?.Upload(); fragmentStage?.Upload();', 'if(TryCopyStageBuffers()) fragmentStage!.UploadSamplers();\n        else { vertexStage?.Upload(); fragmentStage?.Upload(); }')
    s = replace(s, '        internal void Upload() =>', '        internal void UploadSamplers() => owner.UploadStage(vertex,buffers,Samplers,FlipTargetSamplers,stageBindings,true);\n        internal void Upload() =>')
    path.write_text(s)
    path = out / 'managed/Foster/StageBindings.cs'
    s = path.read_text()
    s = replace(s, 'private struct StageBinding', 'internal struct StageBinding')
    s = replace(s, 'private sealed class StageBindings', 'internal sealed class StageBindings')
    s = replace(s, 'StageBindings bindings)\n    {\n        for', 'StageBindings bindings,bool skipBuffers=false)\n    {\n        if(!skipBuffers) for')
    path.write_text(s)
    path = out / 'managed/Foster/Material.cs'
    path.write_text(replace(path.read_text(), 'private readonly record struct Uniform(', 'internal readonly record struct Uniform('))
