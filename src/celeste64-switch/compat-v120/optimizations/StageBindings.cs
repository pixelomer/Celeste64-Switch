using System.Runtime.InteropServices;
namespace Foster.Framework;

public partial class Material
{
    private object stageLayoutEpoch = new();
    private struct StageBinding
    {
        internal object? Epoch;
        internal string? Name;
        internal bool Present;
        internal Uniform Value;
    }
    private sealed class StageBindings
    {
        internal readonly StageBinding[] Floats = new StageBinding[4];
        internal readonly StageBinding[] Textures = new StageBinding[4];
        internal readonly StageBinding[] Samplers = new StageBinding[4];
        internal readonly StageBinding[] Flips = new StageBinding[4];
    }
    private static readonly string[] stageFlipNames = ["c64_flip0","c64_flip1","c64_flip2","c64_flip3"];
    private ref readonly Uniform ResolveStageBinding(ref StageBinding cache,string name,bool required=false)
    {
        if(cache.Epoch!=stageLayoutEpoch || cache.Name!=name)
        {
            bool present=required || Shader?.Has(name)==true;
            var value=present ? Get(name) : default;
            cache=new StageBinding { Epoch=stageLayoutEpoch,Name=name,Present=present,Value=value };
        }
        return ref cache.Value;
    }
    private void SetStageFloats(ref StageBinding cache,string name,ReadOnlySpan<float> data)
    {
        ref readonly var it=ref ResolveStageBinding(ref cache,name);
        if(!cache.Present) return;
        if(!IsFloat(it.Type)) throw new Exception($"Uniform '{name}' is not a Float value type");
        int count=Math.Min(data.Length,it.BufferLength);
        CopyStageFloats(data[..count],floatBuffer.AsSpan(it.BufferStart,count));
    }
#if C64_NATIVE_UNIFORM_COPY
    [DllImport("FosterPlatform",CallingConvention=CallingConvention.Cdecl)]
    private static extern unsafe void FosterMaterialCopyFloats(float* destination,float* source,int count);
#endif
    private static unsafe void CopyStageFloats(ReadOnlySpan<float> source,Span<float> destination)
    {
#if C64_NATIVE_UNIFORM_COPY
        if(destination.Length<source.Length) { source.CopyTo(destination);return; }
        fixed(float* src=source)
        fixed(float* dst=destination) FosterMaterialCopyFloats(dst,src,source.Length);
#else
        source.CopyTo(destination);
#endif
    }
    private static void CopyStageBytes(ReadOnlySpan<byte> source,Span<byte> destination)
    {
        if(source.Length%4!=0 || destination.Length<source.Length) { source.CopyTo(destination);return; }
        CopyStageFloats(MemoryMarshal.Cast<byte,float>(source),MemoryMarshal.Cast<byte,float>(destination));
    }
    private void UploadStage(bool vertex,byte[][] buffers,StageSampler[] samplers,bool flipTargets,StageBindings bindings)
    {
        for(int i=0;i<4;i++)
        {
            if(buffers[i]==null) continue;
            string name=vertex ? (i==0?"type_VertexUniforms":"type_JointUniforms") : "type_FragmentUniforms";
            SetStageFloats(ref bindings.Floats[i],name,MemoryMarshal.Cast<byte,float>(buffers[i]));
        }
        if(vertex) return;
        Span<float> flip=stackalloc float[1];
        for(int i=0;i<samplers.Length;i++)
        {
            if(!samplers[i].Assigned) continue;
            string name=i==0 ? (Shader?.Name=="Edge" ? "SPIRV_Cross_CombinedTextureTextureSampler" : "SPIRV_Cross_CombinedTextureSampler") : "SPIRV_Cross_CombinedDepthDepthSampler";
            ref readonly var texture=ref ResolveStageBinding(ref bindings.Textures[i],name);
            if(!bindings.Textures[i].Present) continue;
            if(texture.Type!=UniformType.Texture2D) throw new Exception($"Uniform '{name}' is not a Texture2D value type");
            if(texture.BufferLength<=0) throw new Exception($"Uniform '{name}' with index 0 is out of bounds");
            textureBuffer[texture.BufferStart]=samplers[i].Texture;
            string samplerName=i==0 ? (Shader?.Name=="Edge" ? "SPIRV_Cross_CombinedTextureTextureSampler_sampler" : "SPIRV_Cross_CombinedTextureSampler_sampler") : "SPIRV_Cross_CombinedDepthDepthSampler_sampler";
            ref readonly var sampler=ref ResolveStageBinding(ref bindings.Samplers[i],samplerName,true);
            if(sampler.Type!=UniformType.Sampler2D) throw new Exception($"Uniform '{samplerName}' is not a Sampler2D value type");
            if(sampler.BufferLength<=0) throw new Exception($"Uniform '{samplerName}' with index 0 is out of bounds");
            samplerBuffer[sampler.BufferStart]=samplers[i].Sampler;
            flip[0]=flipTargets && (samplers[i].Texture?.IsTargetAttachment ?? false)?1f:0f;
            SetStageFloats(ref bindings.Flips[i],stageFlipNames[i],flip);
        }
    }
}
