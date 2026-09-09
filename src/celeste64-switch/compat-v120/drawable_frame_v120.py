"""Reuse drawable preparation within the synchronous World render passes."""

def optimize_drawableframe(out, port, override):
    import os
    override('Graphics/RenderState.cs', [('public Camera Camera = new();', 'public Camera Camera = new();\n    internal ulong DrawableFrame;')])
    override('Scenes/World.cs', [('public Camera Camera = new();', 'public Camera Camera = new();\n    private static ulong drawableFrameSerial;'), ('RenderState state = new(GraphicsDevice, Time);', '// Zero is reserved for standalone/unscoped render callers.\n        RenderState state = new(GraphicsDevice, Time);\n        state.DrawableFrame = drawableFrameSerial < ulong.MaxValue ? ++drawableFrameSerial : 0;')])
    override('Graphics/SkinnedModel.cs', [('public const int SkinMatrixCount = 32;', 'public const int SkinMatrixCount = 32;\n    private readonly DrawableFrameCache drawableFrameCache = new();'), ('var drawable = Instance[i];', 'var drawable = drawableFrameCache.Get(Instance, i, state.DrawableFrame);')])
    source = (port / 'optimizations/DrawableFrameCache.cs').read_text()
    (out / 'managed/Game/DrawableFrameCache.cs').write_text(source)
