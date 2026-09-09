"""Reuse spike geometry while retaining original orientation and attachment tests."""
import shutil

def optimize_spike_mesh(out, here, replace):
    shutil.copy2(here / 'optimizations/SpikeMeshCache.cs', out / 'managed/Game/SpikeMeshCache.cs')
    p = out / 'managed/Game/SimpleModel.cs'
    s = p.read_text()
    s = replace(s, 'public readonly Mesh<Vertex> Mesh = new(Game.Instance.GraphicsDevice);', 'public readonly Mesh<Vertex> Mesh;')
    s = replace(s, 'public SimpleModel() {}', 'public SimpleModel() { Mesh = new(Game.Instance.GraphicsDevice); }\n    internal SimpleModel(Mesh<Vertex> mesh, Part[] parts, DefaultMaterial[] materials)\n    {\n        Mesh=mesh; Parts.AddRange(parts); Materials.AddRange(materials);\n        Transform=Matrix.Identity; Flags=ModelFlags.Terrain;\n    }')
    s = replace(s, 'public SimpleModel(List<SimpleModel> combine)', 'public SimpleModel(List<SimpleModel> combine) : this()')
    s = replace(s, 'public SimpleModel(List<SkinnedModel> combine)', 'public SimpleModel(List<SkinnedModel> combine) : this()')
    p.write_text(s)
    p = out / 'managed/Game/SpikeBlock.cs'
    s = p.read_text()
    s = replace(s, 'var models = new List<SkinnedModel>();', 'Model = SpikeMeshCache.Get(Assets.Models["spike"], width, height, rotation,\n            horizontal, vertical, forward, () =>\n        {\n        var models = new List<SkinnedModel>();')
    s = replace(s, 'Model = new SimpleModel(models);', 'return new SimpleModel(models);\n        });')
    p.write_text(s)
