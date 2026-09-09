using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

namespace Celeste64;

// Only immutable generated geometry is shared. Each actor retains a separate
// SimpleModel, material/part lists, transform, flags and attachment state.
internal static class SpikeMeshCache
{
    private sealed class Geometry(SimpleModel source)
    {
        internal readonly Mesh<Vertex> Mesh = source.Mesh;
        internal readonly SimpleModel.Part[] Parts = source.Parts.ToArray();
        internal readonly DefaultMaterial[] Materials = source.Materials.ToArray();
        internal SimpleModel Instantiate() => new(Mesh, Parts, Materials);
    }
    private static readonly ConditionalWeakTable<SkinnedTemplate, Dictionary<string, Geometry>> caches = new();
    private const int Capacity = 128;

    internal static SimpleModel Get(SkinnedTemplate template, float width, float height,
        in Matrix rotation, in Vec3 horizontal, in Vec3 vertical, in Vec3 forward,
        Func<SimpleModel> build)
    {
        Span<float> values = stackalloc float[27];
        values[0] = width; values[1] = height;
        MemoryMarshal.Write(MemoryMarshal.AsBytes(values[2..18]), in rotation);
        MemoryMarshal.Write(MemoryMarshal.AsBytes(values[18..21]), in horizontal);
        MemoryMarshal.Write(MemoryMarshal.AsBytes(values[21..24]), in vertical);
        MemoryMarshal.Write(MemoryMarshal.AsBytes(values[24..27]), in forward);
        foreach (float value in values) if (!float.IsFinite(value)) return build();
        // Exact float bits include signed zeros. Asset reload creates a new
        // template identity and therefore a separate, collectable cache.
        string key = Convert.ToHexString(MemoryMarshal.AsBytes(values));
        var cache = caches.GetOrCreateValue(template);
        if (cache.TryGetValue(key, out var geometry) && !geometry.Mesh.IsDisposed)
            return geometry.Instantiate();
        var result = build();
        if (cache.Count < Capacity || cache.ContainsKey(key)) cache[key] = new(result);
        return result;
    }
}
