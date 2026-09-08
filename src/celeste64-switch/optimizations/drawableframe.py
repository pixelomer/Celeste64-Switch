"""Reuse drawable preparation within the synchronous World render passes."""

def optimize_drawableframe(out, port, override):
    import os
    override('Graphics/RenderState.cs', [('public Camera Camera;', 'public Camera Camera;\n    internal ulong DrawableFrame;')])
    override('Scenes/World.cs', [('public Camera Camera = new();', 'public Camera Camera = new();\n    private static ulong drawableFrameSerial;'), ('RenderState state = new();', '// Zero is reserved for standalone/unscoped render callers.\n        RenderState state = new();\n        state.DrawableFrame = drawableFrameSerial < ulong.MaxValue ? ++drawableFrameSerial : 0;')])
    override('Graphics/SkinnedModel.cs', [('private readonly Matrix[] transformSkin = new Matrix[SkinMatrixCount];', 'private readonly Matrix[] transformSkin = new Matrix[SkinMatrixCount];\n    private readonly DrawableFrameCache drawableFrameCache = new();'), ('var drawable = Instance[i];', 'var drawable = drawableFrameCache.Get(Instance, i, state.DrawableFrame);')])
    source = (port / 'optimizations/DrawableFrameCache.cs').read_text()
    (out / 'managed/Game/DrawableFrameCache.cs').write_text(source)
