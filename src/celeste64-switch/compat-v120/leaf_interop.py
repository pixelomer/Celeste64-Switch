"""Suppress GC transitions only for bounded, nonblocking native leaf helpers."""
import re

def optimize_leaf_interop(out, replace):
    for relative in ['Game/SwitchRenderMath.cs', 'Game/NativeCull.cs', 'SharpGLTF/NativeAnimationMath.cs']:
        path = out / 'managed' / relative
        if not path.exists():
            continue
        source, count = re.subn('(\\s*\\[(?:System\\.Runtime\\.InteropServices\\.)?DllImport\\([^\\n]+\\)\\])', '\\n    [System.Runtime.InteropServices.SuppressGCTransition]\\1', path.read_text())
        assert count > 0, relative
        path.write_text(source)
    path = out / 'managed/Foster/StageBindings.cs'
    s = path.read_text()
    old = '[DllImport("FosterPlatform",CallingConvention=CallingConvention.Cdecl)]\n    private static extern unsafe void FosterMaterialCopyFloats(float* destination,float* source,int count);'
    s = replace(s, old, '[DllImport("FosterPlatform",EntryPoint="FosterMaterialCopyFloats",CallingConvention=CallingConvention.Cdecl)]\n    private static extern unsafe void CopyFloatsNormal(float* destination,float* source,int count);\n    [SuppressGCTransition]\n    [DllImport("FosterPlatform",EntryPoint="FosterMaterialCopyFloats",CallingConvention=CallingConvention.Cdecl)]\n    private static extern unsafe void CopyFloatsLeaf(float* destination,float* source,int count);\n    private static unsafe void FosterMaterialCopyFloats(float* destination,float* source,int count)\n    {\n        if((uint)count<=256) CopyFloatsLeaf(destination,source,count);\n        else CopyFloatsNormal(destination,source,count);\n    }')
    path.write_text(s)
    path = out / 'managed/Foster/StageCopyBatch.cs'
    s = path.read_text()
    old = '[DllImport("FosterPlatform",CallingConvention=CallingConvention.Cdecl)]\n    private static extern unsafe void FosterStageCopyBatch(float* target,byte* vertex,byte* joints,byte* fragment,CopyPlan* plan);'
    s = replace(s, old, '[DllImport("FosterPlatform",EntryPoint="FosterStageCopyBatch",CallingConvention=CallingConvention.Cdecl)]\n    private static extern unsafe void CopyStageNormal(float* target,byte* vertex,byte* joints,byte* fragment,CopyPlan* plan);\n    [SuppressGCTransition]\n    [DllImport("FosterPlatform",EntryPoint="FosterStageCopyBatch",CallingConvention=CallingConvention.Cdecl)]\n    private static extern unsafe void CopyStageLeaf(float* target,byte* vertex,byte* joints,byte* fragment,CopyPlan* plan);\n    private static unsafe void FosterStageCopyBatch(float* target,byte* vertex,byte* joints,byte* fragment,CopyPlan* plan)\n    {\n        long count=(long)plan->Vertex.Count+plan->Joints.Count+plan->Fragment.Count;\n        if(count>=0 && count<=256) CopyStageLeaf(target,vertex,joints,fragment,plan);\n        else CopyStageNormal(target,vertex,joints,fragment,plan);\n    }')
    path.write_text(s)
