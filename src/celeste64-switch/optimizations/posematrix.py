def optimize_posematrix(out, replace):
    p = out / 'managed/SharpGLTF/NodeTemplate.cs'
    s = p.read_text()
    s = replace(s, '_LocalTransform = srcNode.LocalTransform;', '_LocalTransform = srcNode.LocalTransform;\n            _PoseMatrix = new Lazy<Matrix4x4>(() => NativeAnimationMath.ToMatrix(_LocalTransform),\n                System.Threading.LazyThreadSafetyMode.PublicationOnly);')
    s = replace(s, 'private readonly TRANSFORM _LocalTransform;', 'private readonly TRANSFORM _LocalTransform;\n        private readonly Lazy<Matrix4x4> _PoseMatrix;')
    start = s.index('#region properties')
    head = s[:start]
    tail = s[start:]
    assert tail.count('NativeAnimationMath.ToMatrix(_LocalTransform)') == 3
    p.write_text(head + tail.replace('NativeAnimationMath.ToMatrix(_LocalTransform)', '_PoseMatrix.Value'))
