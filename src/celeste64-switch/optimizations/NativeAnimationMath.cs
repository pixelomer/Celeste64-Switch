using System.Numerics;
using System.Runtime.InteropServices;

namespace SharpGLTF.Runtime;

internal static class NativeAnimationMath
{
    [DllImport("FosterPlatform", CallingConvention = CallingConvention.Cdecl)]
    private static extern int FosterRenderMatrixMultiply(in Matrix4x4 a, in Matrix4x4 b, out Matrix4x4 result);

    public static Matrix4x4 Multiply(in Matrix4x4 a, in Matrix4x4 b)
    {
        if (FosterRenderMatrixMultiply(a, b, out var result) != 0) return result;
        return a * b;
    }
}
