def optimize_nativeuniformcopy(out, port, replace):
    p = out / 'managed/Foster/Material.cs'
    s = p.read_text()
    a = '    protected struct MatrixUniformCache'
    s = replace(s, a, '    [System.Runtime.InteropServices.DllImport("FosterPlatform", CallingConvention=System.Runtime.InteropServices.CallingConvention.Cdecl)]\n    private static extern unsafe void FosterMaterialCopyFloats(float* destination,float* source,int count);\n    private static unsafe void CopyFloatBuffer(ReadOnlySpan<float> source,Span<float> destination)\n    {\n        if(destination.Length<source.Length) { source.CopyTo(destination); return; }\n        fixed(float* src=source)\n        fixed(float* dst=destination)\n            FosterMaterialCopyFloats(dst,src,source.Length);\n    }\n\n' + a)
    s = replace(s, 'new ReadOnlySpan<float>((float*)data, Math.Min(16, cache.Length))\n                .CopyTo(floatBuffer.AsSpan()[cache.Start..]);', 'CopyFloatBuffer(new ReadOnlySpan<float>((float*)data, Math.Min(16, cache.Length)),\n                floatBuffer.AsSpan()[cache.Start..]);')
    s = replace(s, 'subspan.CopyTo(floatBuffer.AsSpan()[it.BufferStart..]);', 'CopyFloatBuffer(subspan,floatBuffer.AsSpan()[it.BufferStart..]);')
    p.write_text(s)
    (out / 'foster/switch_uniform_copy.c').write_text((port / 'optimizations/uniform_copy.c').read_text())
