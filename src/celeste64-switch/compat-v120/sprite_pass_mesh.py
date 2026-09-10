"""Keep independent GPU storage for pre/post sprite passes in the same frame."""

def optimize_sprite_pass_mesh(out, replace):
    p = out / 'managed/Game/SpriteRenderer.cs'
    s = p.read_text()
    s = replace(s, 'private readonly Mesh<SpriteVertex> spriteMesh = new(Game.Instance.GraphicsDevice);', 'private readonly Mesh<SpriteVertex> preSpriteMesh = new(Game.Instance.GraphicsDevice);\n    private readonly Mesh<SpriteVertex> postSpriteMesh = new(Game.Instance.GraphicsDevice);')
    a = 'public void Render(ref RenderState state, List<Sprite> sprites, bool postEffects)\n\t{'
    s = replace(s, a, a + '\n        // A post-pass upload must not overwrite vertices used by pre-pass draws\n        // still queued on the GL worker/GPU. Each pass keeps its own mesh.\n        var spriteMesh = postEffects ? postSpriteMesh : preSpriteMesh;')
    s = replace(s, 'bool indicesGrew = false;', '')
    s = replace(s, 'indicesGrew = true;', '')
    s = replace(s, 'if (indicesGrew) spriteMesh.SetIndices<int>(CollectionsMarshal.AsSpan(spriteIndices));', 'if (spriteMesh.IndexCount < spriteIndices.Count) spriteMesh.SetIndices<int>(CollectionsMarshal.AsSpan(spriteIndices));')
    p.write_text(s)
