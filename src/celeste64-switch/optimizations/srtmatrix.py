def optimize_srtmatrix(out, port, replace):
    (out / 'foster/switch_srt_matrix.c').write_text((port / 'optimizations/srtmatrix.c').read_text())
    p = out / 'managed/SharpGLTF/NativeAnimationMath.cs'
    s = p.read_text()
    a = '    public static Matrix4x4 ToMatrix('
    s = replace(s, a, '    [DllImport("FosterPlatform", CallingConvention=CallingConvention.Cdecl)]\n    private static extern int FosterRenderSrtMatrix(in Vector3 scale,in Quaternion rotation,in Vector3 translation,out Matrix4x4 result);\n\n' + a)
    a = '        if (!transform.IsSRT) return transform.Matrix;'
    s = replace(s, a, a + '\n        if (FosterRenderSrtMatrix(transform.Scale,transform.Rotation,transform.Translation,out var native) != 0) return native;')
    p.write_text(s)
