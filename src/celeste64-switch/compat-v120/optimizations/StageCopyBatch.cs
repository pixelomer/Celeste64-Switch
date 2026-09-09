using System.Runtime.InteropServices;
namespace Foster.Framework;

public partial class Material
{
    [StructLayout(LayoutKind.Sequential)]
    private struct CopyBlock { internal int Start, Count; }
    [StructLayout(LayoutKind.Sequential)]
    private struct CopyPlan { internal CopyBlock Vertex, Joints, Fragment; }
    private object? copyEpoch;
    private byte[]? copyVertex,copyJoints,copyFragment;
    private CopyPlan copyPlan;
    private bool copyPlanValid;

    private bool PlanBlock(ref StageBinding binding,string name,byte[]? bytes,out CopyBlock block)
    {
        block=default;
        if(bytes==null) return true;
        ref readonly var uniform=ref ResolveStageBinding(ref binding,name);
        if(!binding.Present) return true;
        if(!IsFloat(uniform.Type)) return false;
        int count=Math.Min(bytes.Length/4,uniform.BufferLength);
        if(uniform.BufferStart<0 || count<0 || uniform.BufferStart>floatBuffer.Length-count) return false;
        block=new CopyBlock {Start=uniform.BufferStart,Count=count};
        return true;
    }

    [DllImport("FosterPlatform",CallingConvention=CallingConvention.Cdecl)]
    private static extern unsafe void FosterStageCopyBatch(float* target,byte* vertex,byte* joints,byte* fragment,CopyPlan* plan);

    private unsafe bool TryCopyStageBuffers()
    {
        if(vertexStage==null || fragmentStage==null) return false;
        var v=vertexStage.buffers;var f=fragmentStage.buffers;
        // Unusual slot combinations retain ordered generic uploads and errors.
        if(v[2]!=null || v[3]!=null || f[1]!=null || f[2]!=null || f[3]!=null) return false;
        if(copyEpoch!=stageLayoutEpoch || copyVertex!=v[0] || copyJoints!=v[1] || copyFragment!=f[0])
        {
            copyPlanValid=PlanBlock(ref vertexStage.stageBindings.Floats[0],"type_VertexUniforms",v[0],out copyPlan.Vertex)
                && PlanBlock(ref vertexStage.stageBindings.Floats[1],"type_JointUniforms",v[1],out copyPlan.Joints)
                && PlanBlock(ref fragmentStage.stageBindings.Floats[0],"type_FragmentUniforms",f[0],out copyPlan.Fragment);
            copyEpoch=stageLayoutEpoch;copyVertex=v[0];copyJoints=v[1];copyFragment=f[0];
        }
        if(!copyPlanValid) return false;
        fixed(float* target=floatBuffer)
        fixed(byte* vertex=v[0])
        fixed(byte* joints=v[1])
        fixed(byte* fragment=f[0])
        fixed(CopyPlan* plan=&copyPlan) FosterStageCopyBatch(target,vertex,joints,fragment,plan);
        return true;
    }
}
