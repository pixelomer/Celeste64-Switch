def optimize_skinmemcpy(out, port, override):
    (out / 'managed/Game/SkinMatrixCopy.cs').write_text((port / 'optimizations/SkinMatrixCopy.cs').read_text())
    (out / 'foster/switch_skin_copy.c').write_text((port / 'optimizations/skin_copy.c').read_text())
    override('Graphics/SkinnedModel.cs', [('for (int j = 0, n = Math.Min(SkinMatrixCount, skinXform.SkinMatrices.Count); j < n; j ++)\n\t\t\t\t\t\t\ttransformSkin[j] = skinXform.SkinMatrices[j];', 'SkinMatrixCopy.Copy(skinXform.SkinMatrices, transformSkin);')])
