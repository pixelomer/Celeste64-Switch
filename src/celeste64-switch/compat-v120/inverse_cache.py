"""Reuse a SimpleModel inverse only when every source matrix bit is unchanged."""

def optimize_inverse_cache(out, replace, override):
    (out / 'foster/switch_matrix_equal.c').write_text('#include <string.h>\nint FosterMatrixBitsEqual(const void* a,const void* b);\nint FosterMatrixBitsEqual(const void* a,const void* b) { return memcmp(a,b,64)==0; }\n')
    p = out / 'managed/Game/SwitchRenderMath.cs'
    s = p.read_text()
    s = replace(s, 'internal static class SwitchRenderMath\n{', 'internal static class SwitchRenderMath\n{\n    [System.Runtime.InteropServices.DllImport("FosterPlatform",CallingConvention=System.Runtime.InteropServices.CallingConvention.Cdecl)]\n    private static extern int FosterMatrixBitsEqual(in Matrix4x4 a,in Matrix4x4 b);\n    internal static bool EqualBits(in Matrix4x4 a,in Matrix4x4 b) => FosterMatrixBitsEqual(a,b)!=0;\n')
    p.write_text(s)
    override('Graphics/RenderState.cs', [('internal bool Ready;', 'internal bool Ready, CacheInverse, InverseReady;\n        internal Matrix InverseSource;'), ('Matrix.Invert(matrices.Model, out matrices.Inverse);', 'if (!matrices.CacheInverse || !matrices.InverseReady || !SwitchRenderMath.EqualBits(matrices.Model,matrices.InverseSource))\n            {\n                Matrix.Invert(matrices.Model, out matrices.Inverse);\n                if(matrices.CacheInverse) { matrices.InverseSource=matrices.Model;matrices.InverseReady=true; }\n            }')])
    override('Graphics/SimpleModel.cs', [('public class SimpleModel : Model\n{', 'public class SimpleModel : Model\n{\n    private RenderState.MaterialMatrices retainedMatrices = new() { CacheInverse=true };'), ('RenderState.MaterialMatrices matrices = default;', 'ref var matrices = ref retainedMatrices;\n        matrices.Ready=false;')])
