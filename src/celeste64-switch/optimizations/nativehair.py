def optimize_nativehair(out, port, override):
    for source, destination in [('SwitchHairVertices.cs', 'managed/Game/SwitchHairVertices.cs'), ('hair_vertices.c', 'foster/switch_hair_vertices.c')]:
        (out / destination).write_text((port / 'optimizations' / source).read_text())
    override('Graphics/Hair.cs', [('var vertex = index;', ''), ('foreach (ref readonly var vert in CollectionsMarshal.AsSpan(sphereVertices))\n\t\t\t\tpreparedVertices[vertex++] = new(SwitchRenderMath.TransformPosition(vert.Pos, transform), Vec2.Zero, Vec3.One, vert.Normal);', 'SwitchHairVertices.Fill(CollectionsMarshal.AsSpan(sphereVertices),\n                preparedVertices.Slice(index, sphereVertices.Count), transform);')])
