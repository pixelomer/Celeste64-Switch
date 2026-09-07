def optimize_collisionmath(out, port, game, override):
    (out / 'managed/Game/SwitchCollisionMath.cs').write_text((port / 'optimizations/SwitchCollisionMath.cs').read_text())
    source = (game / 'Source/Helpers/Utils.cs').read_text(encoding='utf-8-sig')
    start = source.index('public static bool RayIntersectsTriangle(')
    end = source.index('[MethodImpl(MethodImplOptions.AggressiveInlining)]\n\tpublic static Vec2 XY(', start)
    before = source[start:end]
    after = before.replace('Vec3.Dot(', 'SwitchCollisionMath.Dot(').replace('Vec3.Cross(', 'SwitchCollisionMath.Cross(')
    assert after != before
    override('Helpers/Utils.cs', [(before, after)])
