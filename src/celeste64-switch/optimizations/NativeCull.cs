using System.Runtime.InteropServices;

namespace Celeste64;

internal static unsafe class NativeCull
{
    [DllImport("FosterPlatform", CallingConvention=CallingConvention.Cdecl)]
    private static extern int FosterBoxInFrustum(in BoundingBox box, Plane* planes);

    internal static int Test(in BoundingBox box, ReadOnlySpan<Plane> planes)
    {
        if (planes.Length != 6) throw new ArgumentException("Frustum requires six planes");
        fixed (Plane* data=planes) return FosterBoxInFrustum(box,data);
    }
}
