using System.Numerics;
using System.Runtime.CompilerServices;

namespace Celeste64;

// Match the pinned BCL's Vector4.Transform lane operations, in the same order.
// Avoid its Vector128/Vector64 fallback construction and per-lane generic loops.
internal static class SwitchRenderMath
{
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static float Lane(float b0, float a0, float b1, float a1, float b2, float a2, float b3, float a3)
    {
        float value = b0 * a0;
        value = float.MultiplyAddEstimate(b1, a1, value);
        value = float.MultiplyAddEstimate(b2, a2, value);
        return float.MultiplyAddEstimate(b3, a3, value);
    }

    public static Matrix4x4 Multiply(in Matrix4x4 a, in Matrix4x4 b)
        => new(
            Lane(b.M11, a.M11, b.M21, a.M12, b.M31, a.M13, b.M41, a.M14),
            Lane(b.M12, a.M11, b.M22, a.M12, b.M32, a.M13, b.M42, a.M14),
            Lane(b.M13, a.M11, b.M23, a.M12, b.M33, a.M13, b.M43, a.M14),
            Lane(b.M14, a.M11, b.M24, a.M12, b.M34, a.M13, b.M44, a.M14),
            Lane(b.M11, a.M21, b.M21, a.M22, b.M31, a.M23, b.M41, a.M24),
            Lane(b.M12, a.M21, b.M22, a.M22, b.M32, a.M23, b.M42, a.M24),
            Lane(b.M13, a.M21, b.M23, a.M22, b.M33, a.M23, b.M43, a.M24),
            Lane(b.M14, a.M21, b.M24, a.M22, b.M34, a.M23, b.M44, a.M24),
            Lane(b.M11, a.M31, b.M21, a.M32, b.M31, a.M33, b.M41, a.M34),
            Lane(b.M12, a.M31, b.M22, a.M32, b.M32, a.M33, b.M42, a.M34),
            Lane(b.M13, a.M31, b.M23, a.M32, b.M33, a.M33, b.M43, a.M34),
            Lane(b.M14, a.M31, b.M24, a.M32, b.M34, a.M33, b.M44, a.M34),
            Lane(b.M11, a.M41, b.M21, a.M42, b.M31, a.M43, b.M41, a.M44),
            Lane(b.M12, a.M41, b.M22, a.M42, b.M32, a.M43, b.M42, a.M44),
            Lane(b.M13, a.M41, b.M23, a.M42, b.M33, a.M43, b.M43, a.M44),
            Lane(b.M14, a.M41, b.M24, a.M42, b.M34, a.M43, b.M44, a.M44));

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static float PositionLane(float b0, float x, float b1, float y, float b2, float z, float translation)
    {
        float value = b0 * x;
        value = float.MultiplyAddEstimate(b1, y, value);
        value = float.MultiplyAddEstimate(b2, z, value);
        return value + translation;
    }

    public static Vector3 TransformPosition(in Vector3 p, in Matrix4x4 m)
        => new(PositionLane(m.M11, p.X, m.M21, p.Y, m.M31, p.Z, m.M41),
               PositionLane(m.M12, p.X, m.M22, p.Y, m.M32, p.Z, m.M42),
               PositionLane(m.M13, p.X, m.M23, p.Y, m.M33, p.Z, m.M43));
}
