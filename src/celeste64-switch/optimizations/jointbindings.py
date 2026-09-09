"""Cache required skin uniform locations, retaining original errors and write order."""

def optimize_jointbindings(out, override, replace):
    p = out / 'managed/Foster/Material.cs'
    s = p.read_text()
    anchor = '    protected struct MatrixUniformCache'
    methods = '    private void RequireFloatBinding(string name,ref MatrixUniformCache cache)\n    {\n        if(cache.Epoch==uniformEpoch && cache.Name==name)return;\n        ref readonly var binding=ref Get(name);\n        if(!IsFloat(binding.Type))throw new Exception($"Uniform \'{name}\' is not a Float value type");\n        cache=new MatrixUniformCache { Epoch=uniformEpoch,Name=name,Present=true,Start=binding.BufferStart,Length=binding.BufferLength };\n    }\n    protected void SetCachedRequiredScalar(string name,float value,ref MatrixUniformCache cache)\n    {\n        RequireFloatBinding(name,ref cache);\n        if(cache.Length>0)floatBuffer[cache.Start]=value;\n    }\n    protected unsafe void SetCachedRequiredMatrices(string name,ReadOnlySpan<Matrix4x4> values,ref MatrixUniformCache cache)\n    {\n        RequireFloatBinding(name,ref cache);\n        fixed(Matrix4x4* data=values)\n        {\n            var source=new ReadOnlySpan<float>((float*)data,values.Length*16);\n            var prefix=source[..Math.Min(source.Length,cache.Length)];\n            prefix.CopyTo(floatBuffer.AsSpan()[cache.Start..]);\n        }\n    }\n\n'
    if 'FosterMaterialCopyFloats' in s:
        methods = methods.replace('prefix.CopyTo(floatBuffer.AsSpan()[cache.Start..]);', 'CopyFloatBuffer(prefix,floatBuffer.AsSpan()[cache.Start..]);')
    p.write_text(replace(s, anchor, methods + anchor))
    override('Graphics/Materials.cs', [('public string Name = string.Empty;', 'public string Name = string.Empty;\n    private MatrixUniformCache requiredJointMultiplier, requiredJointMatrices;\n    public void SetRequiredJointMultiplier(float value) => SetCachedRequiredScalar("u_jointMult",value,ref requiredJointMultiplier);\n    public void SetRequiredJointMatrices(ReadOnlySpan<Matrix> values) => SetCachedRequiredMatrices("u_jointMat",values,ref requiredJointMatrices);')])
    override('Graphics/SkinnedModel.cs', [('mat.Set("u_jointMult", 1.0f);', 'mat.SetRequiredJointMultiplier(1.0f);'), ('mat.Set("u_jointMat", transformSkin.AsSpan());', 'mat.SetRequiredJointMatrices(transformSkin.AsSpan());')])
