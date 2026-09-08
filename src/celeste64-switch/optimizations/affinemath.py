def optimize_affinemath(out, replace):
    folder = out / 'managed/SharpGLTF'
    path = folder / 'NativeAnimationMath.cs'
    text = path.read_text()
    head, tail = text.rsplit('\n}', 1)
    path.write_text(head + '\n\n    public static Matrix4x4 ToMatrix(in SharpGLTF.Transforms.AffineTransform transform)\n    {\n        // Keep matrix-form and undefined-transform behavior in the pinned Core.\n        if (!transform.IsSRT) return transform.Matrix;\n        var matrix = Multiply(Matrix4x4.CreateScale(transform.Scale),\n            Matrix4x4.CreateFromQuaternion(transform.Rotation));\n        matrix.Translation = transform.Translation;\n        return matrix;\n    }\n}' + tail)
    path = folder / 'NodeTemplate.cs'
    text = path.read_text()
    assert text.count('_LocalTransform.Matrix') == 3
    text = text.replace('_LocalTransform.Matrix', 'NativeAnimationMath.ToMatrix(_LocalTransform)')
    text = replace(text, 'GetLocalTransform(trackLogicalIndex, time).Matrix', 'NativeAnimationMath.ToMatrix(GetLocalTransform(trackLogicalIndex, time))')
    text = replace(text, 'GetLocalTransform(track, time, weight).Matrix', 'NativeAnimationMath.ToMatrix(GetLocalTransform(track, time, weight))')
    path.write_text(text)
