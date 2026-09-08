"""Cache point-shadow queries only while broadphase identity/geometry is stable."""

def optimize_shadowcache(out, port, game, override):
    override('Actors/Actor.cs', [('private bool dirty = true;', 'private bool dirty = true;\n    internal bool ShadowTransformDirty => dirty;\n    internal ShadowRayCache? PointShadowCache;'), ('this.world = world;', 'if (!ReferenceEquals(this.world, world)) PointShadowCache = null;\n        this.world = world;')])
    override('Actors/Solid.cs', [('public bool Collidable = true;', 'internal ulong ShadowGeometryRevision;\n\tpublic bool Collidable = true;'), ('if (initialized)\n\t\t{', 'if (initialized)\n\t\t{\n            unchecked { ShadowGeometryRevision++; }')])
    original = (game / 'Source/Graphics/Sprite.cs').read_text()
    start = original.index('\tpublic static Sprite CreateShadowSprite(')
    end = original.index('\n\tpublic static Sprite CreateFlat(', start)
    method = original[start:end].replace('CreateShadowSprite(World world, Vec3 position', 'CreateCachedShadowSprite(World world, Actor owner, Vec3 position')
    method = method.replace('world.SolidRayCast(position, -Vec3.UnitZ, 1000, out var hit)', '(owner.PointShadowCache ??= new ShadowRayCache()).RayCast(world, position, out var hit)')
    override('Graphics/Sprite.cs', [('\tpublic static Sprite CreateFlat(', method + '\n\tpublic static Sprite CreateFlat(')])
    override('Scenes/World.cs', [('Sprite.CreateShadowSprite(this, actor.Position + Vec3.UnitZ, alpha)', 'Sprite.CreateCachedShadowSprite(this, actor, actor.Position + Vec3.UnitZ, alpha)')])
    source = (port / 'optimizations/ShadowRayCache.cs').read_text()
    (out / 'managed/Game/ShadowRayCache.cs').write_text(source)
