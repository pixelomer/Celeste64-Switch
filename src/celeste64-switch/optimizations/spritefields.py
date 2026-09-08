"""Fill the packed vertex buffer by field, without constructing temporary vertices."""

def optimize_spritefields(override):
    old = '\n'.join((f'            vertices[i{suffix}] = new(board.{corner}, board.Subtexture.TexCoords{j}, board.Color);' for j, (suffix, corner) in enumerate([('', 'A'), (' + 1', 'B'), (' + 2', 'C'), (' + 3', 'D')])))
    new = '\n'.join((f'            ref var v{j} = ref writable[i + {j}];\n            v{j}.Pos = board.{corner};\n            v{j}.Tex = board.Subtexture.TexCoords{j};\n            v{j}.Color = board.Color;' for j, corner in enumerate('ABCD')))
    override('Graphics/SpriteRenderer.cs', [('private record struct SpriteBatch', '// Same explicit packed fields as pinned SpriteVertex. Both contain no references.\n    [StructLayout(LayoutKind.Sequential, Pack = 1)]\n    private struct WritableVertex { public Vec3 Pos; public Vec2 Tex; public Color Color; }\n    private record struct SpriteBatch'), ('var vertices = CollectionsMarshal.AsSpan(spriteVertices);', 'var vertices = CollectionsMarshal.AsSpan(spriteVertices);\n        var writable = MemoryMarshal.Cast<SpriteVertex, WritableVertex>(vertices);'), (old, new)])
