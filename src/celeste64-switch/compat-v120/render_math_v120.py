"""Adapt the accepted render matrix helpers to current uniform-buffer materials."""

def optimize_render(out, port, replace, override, names):
    if 'renderprep' in names:
        override('Graphics/RenderState.cs', [('public void ApplyToMaterial(DefaultMaterial mat, in Matrix localTransformation)', 'public struct MaterialMatrices\n    {\n        internal bool Ready;\n        internal Matrix Model, MVP, Inverse;\n    }\n\n    public void ApplyToMaterial(DefaultMaterial mat, in Matrix localTransformation)\n    {\n        MaterialMatrices matrices = default;\n        ApplyToMaterial(mat, localTransformation, ref matrices);\n    }\n\n    public void ApplyToMaterial(DefaultMaterial mat, in Matrix localTransformation, ref MaterialMatrices matrices)'), ('vertex.Model = localTransformation * ModelMatrix;\n\t\tvertex.MVP = vertex.Model * Camera.ViewProjection;\n\t\tMatrix.Invert(vertex.Model, out vertex.ModelInverse);', 'if (!matrices.Ready)\n        {\n            matrices.Model = localTransformation * ModelMatrix;\n            matrices.MVP = matrices.Model * Camera.ViewProjection;\n            Matrix.Invert(matrices.Model, out matrices.Inverse);\n            matrices.Ready = true;\n        }\n        vertex.Model = matrices.Model;\n        vertex.MVP = matrices.MVP;\n        vertex.ModelInverse = matrices.Inverse;')])
        override('Graphics/SimpleModel.cs', [('public override void Render(ref RenderState state)\n\t{', 'public override void Render(ref RenderState state)\n\t{\n        RenderState.MaterialMatrices matrices = default;'), ('state.ApplyToMaterial(mat, Matrix.Identity);', 'state.ApplyToMaterial(mat, Matrix.Identity, ref matrices);')])
        override('Graphics/SkinnedModel.cs', [('var meshPart = Template.Parts[drawable.Template.LogicalMeshIndex];', 'var meshPart = Template.Parts[drawable.Template.LogicalMeshIndex];\n            RenderState.MaterialMatrices matrices = default;'), ('state.ApplyToMaterial(mat, statXform.WorldMatrix * BaseTranslation);', 'state.ApplyToMaterial(mat, statXform.WorldMatrix * BaseTranslation, ref matrices);'), ('state.ApplyToMaterial(mat, BaseTranslation);', 'state.ApplyToMaterial(mat, BaseTranslation, ref matrices);')])
    if 'rendermath' in names:
        assert 'renderprep' in names
        (out / 'managed/Game/SwitchRenderMath.cs').write_text((port / 'optimizations/SwitchRenderMath.cs').read_text())
        override('Graphics/RenderState.cs', [('localTransformation * ModelMatrix', 'SwitchRenderMath.Multiply(localTransformation, ModelMatrix)'), ('matrices.Model * Camera.ViewProjection', 'SwitchRenderMath.Multiply(matrices.Model, Camera.ViewProjection)')])
        override('Scenes/World.cs', [('it.Model.Transform * it.Actor.Matrix', 'SwitchRenderMath.Multiply(it.Model.Transform, it.Actor.Matrix)')])
        override('Graphics/SkinnedModel.cs', [('statXform.WorldMatrix * BaseTranslation', 'SwitchRenderMath.Multiply(statXform.WorldMatrix, BaseTranslation)')])
        override('Graphics/Hair.cs', [('Matrix.CreateScale(new Vec3(xzScale, yScale, xzScale) * Squish) *\n\t\t\t\tangle *\n\t\t\t\tMatrix.CreateTranslation(nodes[i])', 'SwitchRenderMath.Multiply(\n                    SwitchRenderMath.Multiply(Matrix.CreateScale(new Vec3(xzScale, yScale, xzScale) * Squish), angle),\n                    Matrix.CreateTranslation(nodes[i]))'), ('Vec3.Transform(vert.Pos, transform)', 'SwitchRenderMath.TransformPosition(vert.Pos, transform)')])
    if 'nativemath' in names:
        assert 'rendermath' in names
        from optimizations.nativemath import optimize_nativemath
        optimize_nativemath(out, port)
    if 'mathunroll' in names:
        assert 'nativemath' in names
        from optimizations.mathunroll import optimize_mathunroll
        optimize_mathunroll(out)
    if 'matrixpair' in names:
        assert {'nativemath', 'renderprep'} <= set(names)
        from optimizations.matrixpair import optimize_matrixpair
        optimize_matrixpair(out, port, override)
