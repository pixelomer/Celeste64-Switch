"""Compute the existing box inflation arithmetic in one native call."""

def optimize_box_inflate(out, here, replace, override):
    (out / 'foster/switch_box_inflate.c').write_text((here / 'optimizations/box_inflate.c').read_text())
    override('Spatial/BoundingBox.cs', [('public readonly BoundingBox Inflate(float amount)\n\t{', '[System.Runtime.InteropServices.DllImport("FosterPlatform",CallingConvention=System.Runtime.InteropServices.CallingConvention.Cdecl)]\n    private static extern int FosterInflateBox(in BoundingBox box,float amount,out BoundingBox result);\n\n    public readonly BoundingBox Inflate(float amount)\n    {\n        if(FosterInflateBox(this,amount,out var result)!=0) return result;\n        return InflateReference(amount);\n    }\n\n    private readonly BoundingBox InflateReference(float amount)\n    {')])

def optimize_inflated_cull(out, here, replace, override):
    (out / 'foster/switch_box_inflate.c').write_text((here / 'optimizations/box_inflate.c').read_text() + '\nint FosterBoxInFrustum(const float*,const float*);\nint FosterInflatedBoxInFrustum(const float* box,const float* planes,float amount);\nint FosterInflatedBoxInFrustum(const float* box,const float* planes,float amount)\n{\n    float expanded[6];\n    if(!FosterInflateBox(box,amount,expanded)) return -1;\n    return FosterBoxInFrustum(expanded,planes);\n}\n')
    path = out / 'managed/Game/NativeCull.cs'
    s = path.read_text()
    s = replace(s, '    internal static int Test(', '    [DllImport("FosterPlatform",CallingConvention=CallingConvention.Cdecl)]\n    private static extern int FosterInflatedBoxInFrustum(in BoundingBox box,Plane* planes,float amount);\n    internal static int TestInflated(in BoundingBox box,ReadOnlySpan<Plane> planes,float amount)\n    {\n        if(planes.Length!=6) throw new ArgumentException("Frustum requires six planes");\n        fixed(Plane* data=planes) return FosterInflatedBoxInFrustum(box,data,amount);\n    }\n    internal static int Test(')
    path.write_text(s)
    override('Spatial/BoundingFrustum.cs', [('public readonly bool Contains(in BoundingBox box)', 'public readonly bool ContainsInflated(in BoundingBox box,float amount)\n    {\n        int native=NativeCull.TestInflated(box,planes,amount);\n        return native<0 ? Contains(box.Inflate(amount)) : native!=0;\n    }\n    public readonly bool Contains(in BoundingBox box)')])
    override('Scenes/World.cs', [('Camera.Frustum.Contains(actor.WorldBounds.Inflate(1))', 'Camera.Frustum.ContainsInflated(actor.WorldBounds,1)')])
