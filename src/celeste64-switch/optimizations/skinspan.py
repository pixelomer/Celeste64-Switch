"""Bulk-copy the pinned runtime's contiguous skin matrices, preserving the tail."""

def optimize_skinspan(override):
    old = 'for (int j = 0, n = Math.Min(SkinMatrixCount, skinXform.SkinMatrices.Count); j < n; j ++)\n\t\t\t\t\t\t\ttransformSkin[j] = skinXform.SkinMatrices[j];'
    override('Graphics/SkinnedModel.cs', [(old, 'if (skinXform.SkinMatrices is Matrix[] skinMatrices)\n                            skinMatrices.AsSpan(0, Math.Min(SkinMatrixCount, skinMatrices.Length)).CopyTo(transformSkin);\n                        else\n                        {\n                            ' + old + '\n                        }')])
