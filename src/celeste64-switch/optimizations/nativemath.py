def optimize_nativemath(out, port):
    import re
    path = out / 'managed/Game/SwitchRenderMath.cs'
    text = path.read_text()
    text, count = re.subn('public static Matrix4x4 Multiply\\(in Matrix4x4 a, in Matrix4x4 b\\)\\s*=> new\\(.*?\\);', '[System.Runtime.InteropServices.DllImport("FosterPlatform", CallingConvention = System.Runtime.InteropServices.CallingConvention.Cdecl)]\n    private static extern int FosterRenderMatrixMultiply(in Matrix4x4 a, in Matrix4x4 b, out Matrix4x4 result);\n\n    public static Matrix4x4 Multiply(in Matrix4x4 a, in Matrix4x4 b)\n    {\n        if (FosterRenderMatrixMultiply(a, b, out var result) != 0) return result;\n        return a * b;\n    }', text, flags=re.S)
    assert count == 1, count
    path.write_text(text)
    (out / 'foster/switch_render_math.c').write_text((port / 'optimizations/render_math.c').read_text())
