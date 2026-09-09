"""Fuse exact matrix calculation and valid uniform writes at the measured boundary."""

def optimize_matrixupload(out, port, override, replace):
    p = out / 'managed/Foster/Material.cs'
    s = p.read_text()
    start = s.index('        // A failed or stale binding')
    end = s.index('        fixed(float* destination=floatBuffer)', start)
    guards = s[start:end]
    a = '    protected struct MatrixUniformCache'
    s = replace(s, a, '    [System.Runtime.InteropServices.DllImport("FosterPlatform", CallingConvention=System.Runtime.InteropServices.CallingConvention.Cdecl)]\n    private static extern unsafe int FosterMaterialComputeMatrices(in Matrix4x4 local,in Matrix4x4 world,in Matrix4x4 projection,\n        out Matrix4x4 first,out Matrix4x4 second,float* destinationA,int countA,float* destinationB,int countB);\n    protected unsafe bool TryComputeCachedMatrixPair(in Matrix4x4 local,in Matrix4x4 world,in Matrix4x4 projection,\n        string nameA,ref MatrixUniformCache cacheA,string nameB,ref MatrixUniformCache cacheB,ref Matrix4x4 first,ref Matrix4x4 second)\n    {\n' + guards + '        fixed(float* destination=floatBuffer)\n            return FosterMaterialComputeMatrices(local,world,projection,out first,out second,\n                destination+cacheA.Start,cacheA.Present?Math.Min(16,cacheA.Length):0,\n                destination+cacheB.Start,cacheB.Present?Math.Min(16,cacheB.Length):0)!=0;\n    }\n\n' + a)
    p.write_text(s)
    override('Graphics/Materials.cs', [('public string Name = string.Empty;', 'public string Name = string.Empty;\n    public bool TryComputeModelAndMVP(in Matrix local,in Matrix world,in Matrix projection,ref Matrix modelValue,ref Matrix mvpValue)\n    {\n        if(!TryComputeCachedMatrixPair(local,world,projection,"u_model",ref modelBinding,"u_mvp",ref mvpBinding,ref modelValue,ref mvpValue))return false;\n        model=modelValue;matrix=mvpValue;return true;\n    }')])
    override('Graphics/RenderState.cs', [('if (!matrices.Ready)', 'bool uploaded = false;\n        if (!matrices.Ready)'), ('            SwitchRenderMath.MultiplyPair(localTransformation, ModelMatrix, projection,\n                out matrices.Model, out matrices.MVP);', '            uploaded = mat.TryComputeModelAndMVP(localTransformation, ModelMatrix, projection,\n                ref matrices.Model, ref matrices.MVP);\n            if (!uploaded) SwitchRenderMath.MultiplyPair(localTransformation, ModelMatrix, projection,\n                out matrices.Model, out matrices.MVP);'), ('mat.SetModelAndMVP(matrices.Model, matrices.MVP);', 'if (!uploaded) mat.SetModelAndMVP(matrices.Model, matrices.MVP);')])
    (out / 'foster/switch_matrixupload.c').write_text((port / 'optimizations/matrixupload.c').read_text())
