def optimize_animationmath(out, port, replace):
    destination = out / 'managed/SharpGLTF'
    (destination / 'NativeAnimationMath.cs').write_text((port / 'optimizations/NativeAnimationMath.cs').read_text())
    path = destination / 'NodeInstance.cs'
    text = path.read_text()
    text = replace(text, 'XFORM.Multiply(_LocalMatrix, _Parent.ModelMatrix)', 'NativeAnimationMath.Multiply(_LocalMatrix, _Parent.ModelMatrix)')
    text = replace(text, 'XFORM.Multiply(xform, ipwm)', 'NativeAnimationMath.Multiply(xform, ipwm)')
    path.write_text(text)
