"""Optional fresh storage/chunks for complete sprite writes; preserve subranges."""

def optimize_sprite_stream(out, replace, fresh=True, chunks=False):
    source = out.parents[1] / 'third_party/upstream/foster-0.1.18/Framework/Graphics/Mesh.cs'
    p = out / 'managed/Foster/Mesh.cs'
    s = (p if p.exists() else source).read_text()
    anchor = 'internal IntPtr resource;'
    s = replace(s, anchor, '// Opt in only when the caller replaces every vertex used by the next draw.\n    // SetSubVertices retains its original preservation semantics.\n    public bool StreamVertexWrites { get; set; }\n    public bool ChunkVertexWrites { get; set; }\n    [System.Runtime.InteropServices.DllImport("FosterPlatform", CallingConvention=System.Runtime.InteropServices.CallingConvention.Cdecl)]\n    private static extern void FosterMeshReplaceVertexData(IntPtr mesh, IntPtr data, int dataSize, int fresh, int chunks);\n    ' + anchor)
    anchor = '\t\tPlatform.FosterMeshSetVertexData('
    assert s.count(anchor) == 2
    s = s.replace(anchor, '        if ((StreamVertexWrites || ChunkVertexWrites) && data != IntPtr.Zero && count > 0)\n        {\n            FosterMeshReplaceVertexData(resource, data, format.Stride * count, StreamVertexWrites ? 1 : 0, ChunkVertexWrites ? 1 : 0);\n            return;\n        }\n' + anchor, 1)
    p.write_text(s)
    p = out / 'managed/Foster/Foster.Framework.csproj'
    s = p.read_text()
    if str(source) + ';' not in s:
        s = s.replace(' Exclude="', ' Exclude="' + str(source) + ';', 1)
    p.write_text(s)
    p = out / 'managed/Game/SpriteRenderer.cs'
    s = p.read_text()
    s = replace(s, 'private readonly Mesh<SpriteVertex> spriteMesh = new(Game.Instance.GraphicsDevice);', 'private readonly Mesh<SpriteVertex> spriteMesh = new(Game.Instance.GraphicsDevice) { StreamVertexWrites = ' + str(fresh).lower() + ', ChunkVertexWrites = ' + str(chunks).lower() + ' };')
    p.write_text(s)
    p = out / 'foster/foster_renderer_opengl.c'
    s = p.read_text()
    start = s.index('void FosterMeshSetVertexData_OpenGL(')
    end = s.index('\nvoid FosterMeshSetIndexFormat_OpenGL', start)
    region = s[start:end]
    region = replace(region, 'void FosterMeshSetVertexData_OpenGL(FosterMesh* mesh, void* data, int dataSize, int dataDestOffset)', 'static void FosterMeshSetVertexDataImpl(FosterMesh* mesh, void* data, int dataSize, int dataDestOffset, int chunks)')
    region = replace(region, 'fgl.glBufferSubData(GL_ARRAY_BUFFER, dataDestOffset, dataSize, data);', '// The linked Mesa worker accepts 32 KiB commands including their header.\n    // Keep 64 bytes for the header/alignment. All pieces precede the next draw;\n    // no subrange is omitted, reordered or retained from a previous upload.\n    if (chunks && data != NULL && dataSize > 32704)\n    {\n        for (int written = 0; written < dataSize;)\n        {\n            int length = dataSize - written;\n            if (length > 32704) length = 32704;\n            fgl.glBufferSubData(GL_ARRAY_BUFFER, dataDestOffset + written, length, (char*)data + written);\n            written += length;\n        }\n    }\n    else fgl.glBufferSubData(GL_ARRAY_BUFFER, dataDestOffset, dataSize, data);')
    region += '\nvoid FosterMeshSetVertexData_OpenGL(FosterMesh* mesh, void* data, int dataSize, int dataDestOffset)\n{\n    FosterMeshSetVertexDataImpl(mesh, data, dataSize, dataDestOffset, 0);\n}\n'
    s = s[:start] + region + s[end:]
    p.write_text(s + '\n// Called only for a nonempty complete vertex replacement. Earlier draws keep\n// their old store; the subsequent SetVertexData allocates a fresh store and\n// fills exactly the prefix described by the managed Mesh.VertexCount.\nvoid FosterMeshReplaceVertexData(FosterMesh* mesh, void* data, int dataSize, int fresh, int chunks)\n{\n    FosterMesh_OpenGL* it = (FosterMesh_OpenGL*)mesh;\n    if (fresh && data != NULL && dataSize > 0) it->vertexBufferSize = 0;\n    FosterMeshSetVertexDataImpl(mesh, data, dataSize, 0, chunks);\n}\n')
