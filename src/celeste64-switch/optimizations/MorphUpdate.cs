using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using SharpGLTF.Transforms;

namespace SharpGLTF.Runtime;

internal static class MorphUpdate
{
    // Produce this with the pinned Core implementation rather than reproducing
    // its canonical index/weight layout, including unused slots.
    private static readonly SparseWeight8 neutral = SparseWeight8.Create((MorphTransform.COMPLEMENT_INDEX, 1f));

    public static void Apply(MorphTransform transform, in SparseWeight8 input)
    {
        if (input.IsWeightless && !transform.AbsoluteMorphTargets)
        {
            var current = transform.MorphWeights;
            if (MemoryMarshal.AsBytes(MemoryMarshal.CreateReadOnlySpan(ref current, 1)).SequenceEqual(
                MemoryMarshal.AsBytes(MemoryMarshal.CreateReadOnlySpan(ref Unsafe.AsRef(in neutral), 1))))
                return;
        }
        transform.Update(input, false);
    }
}
