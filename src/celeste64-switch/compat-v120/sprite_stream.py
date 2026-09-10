"""Give complete sprite vertex uploads fresh storage; preserve subrange writes."""

def optimize_sprite_stream(out, replace):
    source = out.parents[1] / 'third_party/upstream/foster-0.1.18/Framework/Graphics/Mesh.cs'
    p = out / 'managed/Foster/Mesh.cs'
    s = (p if p.exists() else source).read_text()
    anchor = 'internal IntPtr resource;'
    s = replace(s, anchor, '// Opt in only when the caller replaces every vertex used by the next draw.\n    // SetSubVertices retains its original preservation semantics.\n    public bool StreamVertexWrites { get; set; }\n    public static bool ForceOriginalStreamWrites;\n    [System.Runtime.InteropServices.DllImport("FosterPlatform", CallingConvention=System.Runtime.InteropServices.CallingConvention.Cdecl)]\n    private static extern void FosterMeshReplaceVertexData(IntPtr mesh, IntPtr data, int dataSize);\n    ' + anchor)
    anchor = '\t\tPlatform.FosterMeshSetVertexData('
    assert s.count(anchor) == 2
    s = s.replace(anchor, '        if (StreamVertexWrites && data != IntPtr.Zero && count > 0)\n        {\n            FosterMeshReplaceVertexData(resource, data, format.Stride * count);\n            return;\n        }\n' + anchor, 1)
    p.write_text(s)
    p = out / 'managed/Foster/Foster.Framework.csproj'
    s = p.read_text()
    if str(source) + ';' not in s:
        s = s.replace(' Exclude="', ' Exclude="' + str(source) + ';', 1)
    p.write_text(s)
    p = out / 'managed/Game/SpriteRenderer.cs'
    s = p.read_text()
    s = replace(s, 'private readonly Mesh<SpriteVertex> spriteMesh = new(Game.Instance.GraphicsDevice);', 'private readonly Mesh<SpriteVertex> spriteMesh = new(Game.Instance.GraphicsDevice) { StreamVertexWrites = true };')
    p.write_text(s)
    p = out / 'foster/foster_renderer_opengl.c'
    p.write_text(p.read_text() + '\n// Called only for a nonempty complete vertex replacement. Earlier draws keep\n// their old store; the subsequent SetVertexData allocates a fresh store and\n// fills exactly the prefix described by the managed Mesh.VertexCount.\nvoid FosterMeshReplaceVertexData(FosterMesh* mesh, void* data, int dataSize)\n{\n    FosterMesh_OpenGL* it = (FosterMesh_OpenGL*)mesh;\n    if (data != NULL && dataSize > 0) it->vertexBufferSize = 0;\n    FosterMeshSetVertexData_OpenGL(mesh, data, dataSize, 0);\n}\n')
