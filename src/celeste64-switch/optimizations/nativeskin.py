"""Use the tested native matrix product for the pinned runtime's skin matrices."""

def optimize_nativeskin(out, replace):
    p = out / 'managed/SharpGLTF/DrawableTemplate.cs'
    s = p.read_text()
    old = 'try { Update(count, inverseBind, world); }'
    new = 'try\n                {\n                    // Core allocates and owns the array. Retain its first-update\n                    // initialization, fallback, callbacks and public transform type.\n                    if (SkinMatrices is Matrix4x4[] matrices && matrices.Length == count)\n                    {\n                        for (int i=0;i<count;i++)\n                            matrices[i] = NativeAnimationMath.Multiply(Bindings[i], ReadWorld(i));\n                    }\n                    else Update(count, inverseBind, world);\n                }'
    p.write_text(replace(s, old, new))
