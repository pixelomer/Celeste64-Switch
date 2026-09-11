"""Replace Mono-era native matrix helpers in a generated NativeAOT tree.

Leave animation caches, pose reuse, material preparation and native hair batching
intact. The original System.Numerics operations now receive NativeAOT codegen.
"""
from pathlib import Path
import re

REMOVED = {"nativemath", "mathunroll", "matrixpair", "srtmatrix"}


def apply(managed: Path):
    for relative in ("Game/SwitchRenderMath.cs", "SharpGLTF/NativeAnimationMath.cs"):
        path = managed / relative
        text = path.read_text()
        # Attribute blocks belong to these three private native declarations.
        text, declarations = re.subn(
            r"\s*\[System\.Runtime\.InteropServices\.SuppressGCTransition\]\s*"
            r"\[(?:System\.Runtime\.InteropServices\.)?DllImport\([^\n]+\)\]\s*"
            r"private static extern int FosterRender(?:MatrixMultiply|MatrixPair|SrtMatrix)\([^;]+;",
            "\n", text)
        assert declarations == 2, (relative, declarations)
        text, multiply = re.subn(
            r"\s*if \(FosterRenderMatrixMultiply\(a, b, out var result\) != 0\) return result;",
            "", text)
        assert multiply == 1, relative
        if relative.startswith("Game/"):
            old = "        if (FosterRenderMatrixPair(a, b, c, out first, out second) != 0) return;\n"
            assert text.count(old) == 1
            text = text.replace(old, "")
        else:
            old = "        if (FosterRenderSrtMatrix(transform.Scale,transform.Rotation,transform.Translation,out var native) != 0) return native;\n"
            assert text.count(old) == 1
            text = text.replace(old, "")
        assert not re.search(r"FosterRender(?:MatrixMultiply|MatrixPair|SrtMatrix)", text)
        path.write_text(text)
