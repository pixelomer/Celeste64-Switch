"""Do not upload an empty sprite pass or prepare a material that will not draw."""

def optimize_empty_sprites(out, replace):
    p = out / 'managed/Game/SpriteRenderer.cs'
    s = replace(p.read_text(), 'CollectionsMarshal.SetCount(spriteVertices, vertexCount);', "CollectionsMarshal.SetCount(spriteVertices, vertexCount);\n        // No batch can reference the mesh when no vertices were emitted.\n        // An empty Span pins to null; Mesa's null BufferSubData path flushes\n        // its worker even for zero bytes. Keep the next real upload unchanged.\n        if (vertexCount == 0) return;")
    p.write_text(s)
