def optimize_rendermath(out, port, override):
    (out / 'managed/Game/SwitchRenderMath.cs').write_text((port / 'optimizations/SwitchRenderMath.cs').read_text())
    path = out / 'managed/Game/RenderState.cs'
    text = path.read_text() if path.exists() else ''
    changes = [('localTransformation * ModelMatrix', 'SwitchRenderMath.Multiply(localTransformation, ModelMatrix)', 2 if 'MaterialMatrices' in text else 1), ('mat.Model * Camera.ViewProjection', 'SwitchRenderMath.Multiply(mat.Model, Camera.ViewProjection)')]
    if 'MaterialMatrices' in text:
        changes.append(('matrices.Model * Camera.ViewProjection', 'SwitchRenderMath.Multiply(matrices.Model, Camera.ViewProjection)'))
    override('Graphics/RenderState.cs', changes)
    override('Scenes/World.cs', [('it.Model.Transform * it.Actor.Matrix', 'SwitchRenderMath.Multiply(it.Model.Transform, it.Actor.Matrix)')])
    override('Graphics/Hair.cs', [('Matrix.CreateScale(new Vec3(xzScale, yScale, xzScale) * Squish) *\n\t\t\t\tangle *\n\t\t\t\tMatrix.CreateTranslation(nodes[i])', 'SwitchRenderMath.Multiply(\n                    SwitchRenderMath.Multiply(Matrix.CreateScale(new Vec3(xzScale, yScale, xzScale) * Squish), angle),\n                    Matrix.CreateTranslation(nodes[i]))'), ('Vec3.Transform(vert.Pos, transform)', 'SwitchRenderMath.TransformPosition(vert.Pos, transform)')])
    override('Graphics/SkinnedModel.cs', [('statXform.WorldMatrix * BaseTranslation', 'SwitchRenderMath.Multiply(statXform.WorldMatrix, BaseTranslation)')])
