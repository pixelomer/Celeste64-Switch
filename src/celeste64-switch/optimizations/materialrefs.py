def optimize_materialrefs(out, replace):
    path = out / 'managed/Foster/Material.cs'
    text = path.read_text()
    text = replace(text, 'var it = Get(uniform);', 'ref readonly var it = ref Get(uniform);', 3)
    text = replace(text, 'private Uniform Get(string uniform)', 'private ref readonly Uniform Get(string uniform)')
    text = replace(text, 'return uniforms[index];', 'return ref System.Runtime.InteropServices.CollectionsMarshal.AsSpan(uniforms)[index];')
    text = replace(text, 'var it = uniforms[i];\n\t\t\tif (it.Name == uniform)\n\t\t\t\treturn it;', 'ref readonly var it = ref System.Runtime.InteropServices.CollectionsMarshal.AsSpan(uniforms)[i];\n            if (it.Name == uniform)\n                return ref it;')
    path.write_text(text)
