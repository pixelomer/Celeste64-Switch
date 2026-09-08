using System.Runtime.CompilerServices;

namespace Celeste64;

// Only point-shadow queries use this cache. Physics/camera queries keep the
// original method. The pinned game changes collision geometry in Transformed;
// it never mutates the returned WorldVertices/WorldFaces arrays externally.
internal sealed class ShadowRayCache
{
    private struct Entry
    {
        internal Solid Solid;
        internal ulong Revision;
        internal bool Active;
    }

    private World? world;
    private Vec3 origin;
    private bool ready, found;
    private RayHit result;
    private readonly List<Solid> candidates = [];
    private readonly List<Entry> previous = [];

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static bool Same(float a, float b)
        => BitConverter.SingleToInt32Bits(a) == BitConverter.SingleToInt32Bits(b);

    internal bool RayCast(World current, in Vec3 point, out RayHit hit)
    {
        if (!float.IsFinite(point.X) || !float.IsFinite(point.Y) || !float.IsFinite(point.Z))
        {
            ready = false;
            return current.SolidRayCast(point, -Vec3.UnitZ, 1000, out hit);
        }

        // A read-only broadphase check. Do not validate dirty transformations:
        // on a miss the original raycast must perform those side effects itself.
        var end = point + -Vec3.UnitZ * 1000;
        var box = new BoundingBox(Vec3.Min(point, end), Vec3.Max(point, end)).Inflate(1);
        candidates.Clear();
        current.SolidGrid.Query(candidates, new Rect(box.Min.XY(), box.Max.XY()));
        bool same = ready && ReferenceEquals(world, current)
            && Same(origin.X, point.X) && Same(origin.Y, point.Y) && Same(origin.Z, point.Z)
            && previous.Count == candidates.Count;
        if (same)
        {
            for (int i = 0; i < candidates.Count; i++)
            {
                var solid = candidates[i];
                var old = previous[i];
                bool active = solid.Collidable && !solid.Destroying;
                if (!ReferenceEquals(old.Solid, solid) || old.Active != active
                    || (active && (solid.ShadowTransformDirty || old.Revision != solid.ShadowGeometryRevision)))
                {
                    same = false;
                    break;
                }
            }
        }
        if (same)
        {
            // VALIDATE_HIT
            
            hit = result;
            return found;
        }

        
        ready = false;
        found = current.SolidRayCast(point, -Vec3.UnitZ, 1000, out hit);
        result = hit;
        origin = point;
        world = current;
        previous.Clear();
        foreach (var solid in candidates)
            previous.Add(new Entry { Solid = solid, Revision = solid.ShadowGeometryRevision,
                Active = solid.Collidable && !solid.Destroying });
        ready = true;
        return found;
    }
}
