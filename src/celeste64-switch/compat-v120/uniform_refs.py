"""Write current per-draw uniform fields in place instead of copying entire blocks."""

def optimize_uniform_refs(out, replace, override):
    p = out / 'managed/Foster/GraphicsCompat.cs'
    s = p.read_text()
    s = replace(s, '        public T GetUniformBuffer<T>(int slot=0) where T:unmanaged', "        // Only used by synchronous game setters that immediately write this block.\n        // Do not retain the reference across material copies or buffer replacement.\n        public ref T GetWritableUniformBuffer<T>(int slot=0) where T:unmanaged\n        {\n            int bytes=System.Runtime.CompilerServices.Unsafe.SizeOf<T>();\n            int size=(bytes+15)&~15;\n            var prior=buffers[slot];\n            if(prior!=null && prior.Length<bytes)\n                _=MemoryMarshal.Read<T>(prior); // Preserve the ordinary getter's failure.\n            if(prior==null || prior.Length!=size)\n            {\n                var next=new byte[size];\n                if(prior!=null) prior.AsSpan(0,bytes).CopyTo(next);\n                buffers[slot]=next;\n            }\n            return ref MemoryMarshal.AsRef<T>(buffers[slot].AsSpan());\n        }\n        public T GetUniformBuffer<T>(int slot=0) where T:unmanaged")
    p.write_text(s)
    override('Graphics/Materials.cs', [('public string Name = string.Empty;', 'public string Name = string.Empty;\n    internal ref UniformBuffers.DefaultVertex WritableVertex => ref Vertex.GetWritableUniformBuffer<UniformBuffers.DefaultVertex>();\n    internal ref UniformBuffers.DefaultFragment WritableFragment => ref Fragment.GetWritableUniformBuffer<UniformBuffers.DefaultFragment>();')])
    override('Graphics/RenderState.cs', [('var vertex = mat.VertexUniforms;', 'ref var vertex = ref mat.WritableVertex;'), ('mat.VertexUniforms = vertex;', ''), ('var fragment = mat.FragmentUniforms;', 'ref var fragment = ref mat.WritableFragment;'), ('mat.FragmentUniforms = fragment;', '')])
    for file in ['Graphics/SimpleModel.cs', 'Graphics/SkinnedModel.cs']:
        override(file, [('mat.VertexUniforms = mat.VertexUniforms with { JointsMult = 0 };', 'mat.WritableVertex.JointsMult = 0;')])
    override('Graphics/SkinnedModel.cs', [('var uniforms = mat.VertexUniforms with { JointsMult = 1.0f };\n\t\t\t\t\tmat.VertexUniforms = uniforms;', 'mat.WritableVertex.JointsMult = 1.0f;')])
