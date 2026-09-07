def optimize_morphneutral(out, port, replace):
    folder = out / 'managed/SharpGLTF'
    (folder / 'MorphUpdate.cs').write_text((port / 'optimizations/MorphUpdate.cs').read_text())
    path = folder / 'DrawableTemplate.cs'
    text = path.read_text()
    text = replace(text, 'statxform.Update(node.MorphWeights, false);', 'MorphUpdate.Apply(statxform, node.MorphWeights);')
    text = replace(text, 'skinxform.Update(armature.LogicalNodes[_MorphNodeIndex].MorphWeights, false);', 'MorphUpdate.Apply(skinxform, armature.LogicalNodes[_MorphNodeIndex].MorphWeights);')
    path.write_text(text)
