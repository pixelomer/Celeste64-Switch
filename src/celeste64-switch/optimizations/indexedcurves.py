"""Binary-search finite, increasing vector/quaternion keys; preserve Core interpolation."""

def optimize_indexedcurves(out, port, replace):
    path = out / 'managed/SharpGLTF/CachedCurve.cs'
    text = path.read_text()
    for kind in ['Vector3', 'Quaternion']:
        start = text.index(f'internal static ICurveSampler<{kind}> Create(')
        end = text.index('\n        }', start)
        block = text[start:end]
        block = block.replace('sampler.GetLinearKeys().ToArray().CreateSampler(isLinear: false, optimize: false)', 'IndexedCurves.Create(sampler.GetLinearKeys().ToArray(), false)')
        block = block.replace('sampler.GetLinearKeys().ToArray().CreateSampler(isLinear: true, optimize: false)', 'IndexedCurves.Create(sampler.GetLinearKeys().ToArray(), true)')
        text = text[:start] + block + text[end:]
    path.write_text(text)
    (path.parent / 'IndexedCurves.cs').write_text((port / 'optimizations/IndexedCurves.cs').read_text())
