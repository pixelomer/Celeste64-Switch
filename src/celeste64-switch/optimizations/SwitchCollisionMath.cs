using System.Numerics;
using System.Runtime.CompilerServices;

namespace Celeste64;

internal static class SwitchCollisionMath
{
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static bool Finite(in Vector3 a)
        => float.IsFinite(a.X) && float.IsFinite(a.Y) && float.IsFinite(a.Z);

    // The linked Vector128.Dot fallback sums the lower pair and the upper
    // pair separately. Vector3.AsVector128 supplies +0 in its fourth lane.
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static float Dot(in Vector3 a, in Vector3 b)
    {
        if (!Finite(a) || !Finite(b)) return Vector3.Dot(a, b);
        return ((0.0f + a.X * b.X) + a.Y * b.Y) + ((0.0f + a.Z * b.Z) + 0.0f);
    }

    // Match Cross's shuffled product followed by MultiplyAddEstimate of the
    // negated other operand. In particular, retain its signed-zero behavior.
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Vector3 Cross(in Vector3 a, in Vector3 b)
    {
        if (!Finite(a) || !Finite(b)) return Vector3.Cross(a, b);
        return new(
            float.MultiplyAddEstimate(-a.Z, b.Y, a.Y * b.Z),
            float.MultiplyAddEstimate(-a.X, b.Z, a.Z * b.X),
            float.MultiplyAddEstimate(-a.Y, b.X, a.X * b.Y));
    }
}
