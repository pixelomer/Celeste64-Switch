"""Semantics-preserving source adaptations for the Switch AOT backend."""

def optimize(out, port, game, foster, names):
    unknown = set(names) - {'spatial', 'late', 'frustum', 'material', 'collision', 'sprites', 'animation', 'uniforms', 'snow', 'renderprep', 'glcache', 'hair', 'textures', 'materialrefs', 'modelsort', 'hairmesh', 'rendermath', 'nativemath', 'imagebytes', 'nativehair', 'snowphase', 'gridwalk', 'imagelifetime', 'matrixbindings', 'skinbindings', 'animationmath', 'morphneutral', 'collisionmath', 'affinemath', 'triangleedges', 'spritefill', 'mathunroll', 'matrixpair', 'matrixcache', 'snowsprite', 'snowfill', 'shadowcache', 'skinspan'}
    if unknown:
        raise ValueError(f'Unknown source optimizations: {unknown}')
    if 'late' in names and 'spatial' not in names:
        raise ValueError('late requires spatial')
    if 'frustum' in names and 'spatial' not in names:
        raise ValueError('frustum requires spatial')
    if 'textures' in names and 'glcache' not in names:
        raise ValueError('textures requires glcache')
    if 'materialrefs' in names and 'material' not in names:
        raise ValueError('materialrefs requires material')
    if 'nativemath' in names and 'rendermath' not in names:
        raise ValueError('nativemath requires rendermath')
    if 'nativehair' in names and (not {'hair', 'hairmesh', 'rendermath'} <= set(names)):
        raise ValueError('nativehair requires hair, hairmesh and rendermath')
    if 'snowphase' in names and 'snow' not in names:
        raise ValueError('snowphase requires snow')
    if 'gridwalk' in names and 'collision' not in names:
        raise ValueError('gridwalk requires collision')
    if 'matrixbindings' in names and 'materialrefs' not in names:
        raise ValueError('matrixbindings requires materialrefs')
    if 'skinbindings' in names and 'animation' not in names:
        raise ValueError('skinbindings requires animation')
    if 'animationmath' in names and (not {'animation', 'nativemath'} <= set(names)):
        raise ValueError('animationmath requires animation and nativemath')
    if 'morphneutral' in names and 'animation' not in names:
        raise ValueError('morphneutral requires animation')
    if 'affinemath' in names and 'animationmath' not in names:
        raise ValueError('affinemath requires animationmath')

    def replace(text, old, new, count=1):
        assert text.count(old) == count, (old, text.count(old), count)
        return text.replace(old, new)

    def override(relative, changes):
        dest = out / 'managed/Game' / relative.split('/')[-1]
        text = (dest if dest.exists() else game / 'Source' / relative).read_text(encoding='utf-8-sig')
        for change in changes:
            text = replace(text, *change)
        dest.write_text(text)
        project = out / 'managed/Game/Celeste64.Switch.csproj'
        xml = project.read_text()
        exclusion = str(game / 'Source' / relative) + ';'
        if exclusion not in xml:
            xml = replace(xml, ' Exclude="', ' Exclude="' + exclusion)
        project.write_text(xml)
    if 'imagebytes' in names:
        from optimizations.imagebytes import optimize_imagebytes
        optimize_imagebytes(out, replace, override)
    if 'skinspan' in names:
        from optimizations.skinspan import optimize_skinspan
        optimize_skinspan(override)
    if 'imagelifetime' in names:
        from optimizations.imagelifetime import optimize_imagelifetime
        optimize_imagelifetime(override)
    if 'animation' in names:
        from optimizations.animation import optimize_animation
        optimize_animation(out, port, replace)
    if 'skinbindings' in names:
        from optimizations.skinbindings import optimize_skinbindings
        optimize_skinbindings(out, replace)
    if 'animationmath' in names:
        from optimizations.animationmath import optimize_animationmath
        optimize_animationmath(out, port, replace)
    if 'affinemath' in names:
        from optimizations.affinemath import optimize_affinemath
        optimize_affinemath(out, replace)
    if 'morphneutral' in names:
        from optimizations.morphneutral import optimize_morphneutral
        optimize_morphneutral(out, port, replace)
    if 'snow' in names:
        from optimizations.snow import optimize_snow
        optimize_snow(override)
    if 'snowphase' in names:
        from optimizations.snowphase import optimize_snowphase
        optimize_snowphase(override)
    if 'hair' in names:
        from optimizations.hair import optimize_hair
        optimize_hair(override)
    if 'modelsort' in names:
        from optimizations.modelsort import optimize_modelsort
        optimize_modelsort(override)
    if 'hairmesh' in names:
        from optimizations.hairmesh import optimize_hairmesh
        optimize_hairmesh(override)
    if 'renderprep' in names:
        from optimizations.renderprep import optimize_renderprep
        optimize_renderprep(override, game)
    if 'rendermath' in names:
        from optimizations.rendermath import optimize_rendermath
        optimize_rendermath(out, port, override)
    if 'nativemath' in names:
        from optimizations.nativemath import optimize_nativemath
        optimize_nativemath(out, port)
    if 'nativehair' in names:
        from optimizations.nativehair import optimize_nativehair
        optimize_nativehair(out, port, override)
    if 'frustum' in names:
        override('Spatial/BoundingBox.cs', [('public readonly bool Contains(in Vec3 point)', 'public readonly bool IsInFrontOf(in Plane plane)\n    {\n        Vec3 negativeVertex;\n        negativeVertex.X = plane.Normal.X >= 0 ? Min.X : Max.X;\n        negativeVertex.Y = plane.Normal.Y >= 0 ? Min.Y : Max.Y;\n        negativeVertex.Z = plane.Normal.Z >= 0 ? Min.Z : Max.Z;\n        return Vec3.Dot(plane.Normal, negativeVertex) + plane.D > 0;\n    }\n\n    public readonly bool Contains(in Vec3 point)')])
        override('Spatial/BoundingFrustum.cs', [('box.Intersects(planes[i]) == PlaneIntersectionType.Front', 'box.IsInFrontOf(planes[i])')])
    if 'collision' in names:
        override('Scenes/World.cs', [('foreach (var face in faces)', 'foreach (ref readonly var face in faces.AsSpan())', 2)])
        override('Actors/Solid.cs', [('public class Solid : Actor, IHaveModels\n{', 'public class Solid : Actor, IHaveModels\n{\n    internal object? GridQueryOwner;\n    internal ulong GridQueryStamp;')])
        override('Scenes/World.cs', [('GridPartition<Solid> SolidGrid', 'SolidGridPartition SolidGrid')])
        for source in (game / 'Source/Actors').rglob('*.cs'):
            text = source.read_text(encoding='utf-8-sig')
            assert 'override bool Equals' not in text and 'override int GetHashCode' not in text, source
        grid = out / 'managed/Game/GridPartition.cs'
        text = (grid if grid.exists() else game / 'Source/Helpers/GridPartition.cs').read_text()
        text = replace(text, 'class GridPartition<T>', 'class SolidGridPartition')
        text = replace(text, 'public GridPartition(', 'public SolidGridPartition(')
        import re
        text = re.sub('\\bT\\b', 'Solid', text)
        text = replace(text, 'private readonly int gridsize;', 'private readonly int gridsize;\n    private object queryOwner = new();\n    private ulong queryStamp;')
        text = replace(text, 'var already = Pool.Get<HashSet<Solid>>();\n\t\talready.Clear();', 'if (++queryStamp == 0)\n        {\n            queryOwner = new object();\n            queryStamp = 1;\n        }')
        text = replace(text, 'if (!already.Contains(it))', 'if (it.GridQueryOwner != queryOwner || it.GridQueryStamp != queryStamp)')
        text = replace(text, 'already.Add(it);', 'it.GridQueryOwner = queryOwner;\n                    it.GridQueryStamp = queryStamp;')
        text = replace(text, 'Pool.Return(already);', '')
        (out / 'managed/Game/SolidGridPartition.cs').write_text(text)
    if 'gridwalk' in names:
        from optimizations.gridwalk import optimize_gridwalk
        optimize_gridwalk(out, replace)
    if 'triangleedges' in names:
        from optimizations.triangleedges import optimize_triangleedges
        optimize_triangleedges(override)
    if 'collisionmath' in names:
        from optimizations.collisionmath import optimize_collisionmath
        optimize_collisionmath(out, port, game, override)
    if 'sprites' in names:
        override('Graphics/SpriteRenderer.cs', [('spriteIndices.Clear();', 'bool indicesGrew = false;'), ('foreach (var board in sprites)', 'foreach (ref readonly var board in CollectionsMarshal.AsSpan(sprites))'), ('spriteIndices.Add(i + 0);\n\t\t\tspriteIndices.Add(i + 1);\n\t\t\tspriteIndices.Add(i + 2);\n\t\t\tspriteIndices.Add(i + 0);\n\t\t\tspriteIndices.Add(i + 2);\n\t\t\tspriteIndices.Add(i + 3);', 'if (spriteIndices.Count < (i / 4 + 1) * 6)\n            {\n                spriteIndices.Add(i + 0);\n                spriteIndices.Add(i + 1);\n                spriteIndices.Add(i + 2);\n                spriteIndices.Add(i + 0);\n                spriteIndices.Add(i + 2);\n                spriteIndices.Add(i + 3);\n                indicesGrew = true;\n            }'), ('spriteMesh.SetIndices<int>(CollectionsMarshal.AsSpan(spriteIndices));', 'if (indicesGrew) spriteMesh.SetIndices<int>(CollectionsMarshal.AsSpan(spriteIndices));')])
    if 'material' in names:
        source = foster / 'Framework/Graphics/Material.cs'
        dest = out / 'managed/Foster/Material.cs'
        text = (dest if dest.exists() else source).read_text()
        text = replace(text, 'private readonly List<Uniform> uniforms = new();', 'private readonly List<Uniform> uniforms = new();\n    private readonly Dictionary<string, int> uniformIndices = new(StringComparer.Ordinal);')
        text = replace(text, 'uniforms.Clear();', 'uniforms.Clear();\n        uniformIndices.Clear();')
        text = replace(text, 'uniforms.Add(it);', 'if (it.Name != null) uniformIndices.TryAdd(it.Name, uniforms.Count);\n            uniforms.Add(it);')
        text = replace(text, 'private Uniform Get(string uniform)\n\t{', 'private Uniform Get(string uniform)\n    {\n        if (uniform != null)\n        {\n            if (uniformIndices.TryGetValue(uniform, out int index)) return uniforms[index];\n            throw new Exception($"Uniform \'{uniform}\' does not exist");\n        }')
        import re
        text, count = re.subn('public void Set\\(string uniform, Matrix4x4 value\\).*?\\}\\);', 'public unsafe void Set(string uniform, Matrix4x4 value)\n        => Set(uniform, new ReadOnlySpan<float>(&value.M11, 16));', text, flags=re.S)
        assert count == 1, count
        text, count = re.subn('public void Set\\(string uniform, ReadOnlySpan<Matrix4x4> value\\).*?\\n\\t\\}', 'public unsafe void Set(string uniform, ReadOnlySpan<Matrix4x4> value)\n    {\n        fixed (Matrix4x4* ptr = value)\n            Set(uniform, new ReadOnlySpan<float>((float*)ptr, value.Length * 16));\n    }', text, flags=re.S)
        assert count == 1, count
        dest.write_text(text)
        project = out / 'managed/Foster/Foster.Framework.csproj'
        project.write_text(replace(project.read_text(), ' Exclude="', ' Exclude="' + str(source) + ';'))
    if 'materialrefs' in names:
        from optimizations.materialrefs import optimize_materialrefs
        optimize_materialrefs(out, replace)
    if 'matrixbindings' in names:
        from optimizations.matrixbindings import optimize_matrixbindings
        optimize_matrixbindings(out, override, replace)
    if 'uniforms' in names:
        from optimizations.uniforms import optimize_uniforms
        optimize_uniforms(out, port, foster, replace)
    if 'glcache' in names:
        from optimizations.glcache import optimize_glcache
        optimize_glcache(out, replace)
    if 'textures' in names:
        from optimizations.textures import optimize_textures
        optimize_textures(out, replace)
    if 'spritefill' in names:
        if 'sprites' not in names:
            raise ValueError('spritefill requires sprites')
        from optimizations.spritefill import optimize_spritefill
        optimize_spritefill(override)
    if 'mathunroll' in names:
        if 'nativemath' not in names:
            raise ValueError('mathunroll requires nativemath')
        from optimizations.mathunroll import optimize_mathunroll
        optimize_mathunroll(out)
    if 'matrixpair' in names:
        if not {'nativemath', 'renderprep'} <= set(names):
            raise ValueError('matrixpair requires nativemath and renderprep')
        from optimizations.matrixpair import optimize_matrixpair
        optimize_matrixpair(out, port, override)
    if 'matrixcache' in names:
        if 'nativemath' not in names:
            raise ValueError('matrixcache requires nativemath')
        from optimizations.matrixcache import optimize_matrixcache
        optimize_matrixcache(out, override)
    if 'snowsprite' in names:
        if 'snowphase' not in names:
            raise ValueError('snowsprite requires snowphase')
        from optimizations.snowsprite import optimize_snowsprite
        optimize_snowsprite(override)
    if 'snowfill' in names:
        if 'snowsprite' not in names:
            raise ValueError('snowfill requires snowsprite')
        from optimizations.snowfill import optimize_snowfill
        optimize_snowfill(override)
    if 'shadowcache' in names:
        if not {'spatial', 'collision'} <= set(names):
            raise ValueError('shadowcache requires spatial and collision')
        from optimizations.shadowcache import optimize_shadowcache
        optimize_shadowcache(out, port, game, override)
