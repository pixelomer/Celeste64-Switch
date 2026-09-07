using System.Numerics;
using System.Runtime.InteropServices;

namespace Celeste64;

internal static class SwitchHairVertices
{
    static unsafe SwitchHairVertices()
    {
        if (sizeof(Vertex) != 76) throw new InvalidOperationException("Hair vertex ABI changed");
    }

    [DllImport("FosterPlatform", CallingConvention = CallingConvention.Cdecl)]
    private static extern unsafe int FosterFillHairVertices(Vertex* source, int count, in Matrix4x4 matrix, Vertex* destination);

    public static unsafe void Fill(ReadOnlySpan<Vertex> source, Span<Vertex> destination, in Matrix4x4 matrix)
    {
        if (destination.Length < source.Length) throw new ArgumentException("Hair vertex destination too small");
        fixed (Vertex* src = source)
        fixed (Vertex* dst = destination)
        {
            if (FosterFillHairVertices(src, source.Length, matrix, dst) != 0) return;
        }
        for (int i = 0; i < source.Length; i++)
            destination[i] = new(Vector3.Transform(source[i].Pos, matrix), Vector2.Zero, Vector3.One, source[i].Normal);
    }
}
