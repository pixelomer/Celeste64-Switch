"""Move the existing six-plane box test across one native boundary."""

def optimize_nativecull(out, port, override):
    import os
    (out / 'managed/Game/NativeCull.cs').write_text((port / 'optimizations/NativeCull.cs').read_text())
    (out / 'foster/switch_native_cull.c').write_text((port / 'optimizations/nativecull.c').read_text())
    extra = ''
    override('Spatial/BoundingFrustum.cs', [('public readonly bool Contains(in BoundingBox box)\n\t{', 'public readonly bool Contains(in BoundingBox box)\n    {\n        int native = NativeCull.Test(box, planes);\n        bool result = native < 0 ? ContainsReference(box) : native != 0;' + extra + '\n        return result;\n    }\n\n    private readonly bool ContainsReference(in BoundingBox box)\n    {')])
