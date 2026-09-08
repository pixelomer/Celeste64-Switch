"""Cache scalar uniform bindings at hot call sites, retaining layout invalidation."""

def optimize_scalarbindings(out, override, replace):
    path = out / 'managed/Foster/Material.cs'
    text = path.read_text()
    anchor = 'protected unsafe void SetCachedMatrix('
    method = 'protected void SetCachedScalarIfPresent(string name, float value, ref MatrixUniformCache cache)\n    {\n        if (cache.Epoch != uniformEpoch || cache.Name != name)\n        {\n            bool present = Shader?.Has(name) ?? false;\n            int start = 0, length = 0;\n            if (present)\n            {\n                ref readonly var binding = ref Get(name);\n                if (!IsFloat(binding.Type))\n                    throw new Exception($"Uniform \'{name}\' is not a Float value type");\n                start = binding.BufferStart;\n                length = binding.BufferLength;\n            }\n            cache = new MatrixUniformCache { Epoch = uniformEpoch, Name = name,\n                Present = present, Start = start, Length = length };\n        }\n        if (cache.Present && cache.Length > 0) floatBuffer[cache.Start] = value;\n    }\n\n    '
    path.write_text(replace(text, anchor, method + anchor))
    override('Graphics/Materials.cs', [('private MatrixUniformCache mvpBinding, modelBinding;', 'private MatrixUniformCache mvpBinding, modelBinding, timeBinding, jointMultiplierBinding;\n    public void SetJointMultiplierIfPresent(float value)\n        => SetCachedScalarIfPresent("u_jointMult", value, ref jointMultiplierBinding);'), ('if (Shader?.Has("u_time") ?? false)\n                    Set("u_time", value);', 'SetCachedScalarIfPresent("u_time", value, ref timeBinding);')])
    for name, tabs in [('SimpleModel', 3), ('SkinnedModel', 5)]:
        old = 'if (mat.Shader != null &&' + (' ' if name == 'SkinnedModel' else '') + '\n' + '\t' * (tabs + 1) + 'mat.Shader.Has("u_jointMult"))\n' + '\t' * (tabs + 1) + 'mat.Set("u_jointMult", 0.0f);'
        override('Graphics/' + name + '.cs', [(old, 'mat.SetJointMultiplierIfPresent(0.0f);')])
