using System.Runtime.InteropServices;

namespace Foster.Framework;

// Matches SwitchUniformBinding in uniforms.c: three 32-bit integers, no pointers.
[StructLayout(LayoutKind.Sequential)]
internal struct SwitchUniformBinding
{
    internal int Kind;
    internal int Index;
    internal int Offset;
}

internal static unsafe class SwitchUniforms
{
    [DllImport("FosterPlatform", CallingConvention = CallingConvention.Cdecl)]
    internal static extern void FosterShaderApplyUniforms(IntPtr shader,
        SwitchUniformBinding* bindings, int count, float* floats,
        TextureSampler* samplers, IntPtr* textures);
}
