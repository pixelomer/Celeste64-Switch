// Appended to Foster's platform implementation. Preserve the order and exact
// arguments of its individual setters, with one managed/native transition.
typedef struct SwitchUniformBinding
{
    int kind;
    int index;
    int offset;
} SwitchUniformBinding;

_Static_assert(sizeof(SwitchUniformBinding) == 12, "Uniform binding ABI");

void FosterShaderApplyUniforms(FosterShader* shader,
    const SwitchUniformBinding* bindings, int count, float* floats,
    FosterTextureSampler* samplers, FosterTexture** textures)
{
    for (int i = 0; i < count; i++)
    {
        const SwitchUniformBinding* binding = bindings + i;
        switch (binding->kind)
        {
            case 0: FosterShaderSetUniform(shader, binding->index, floats + binding->offset); break;
            case 1: FosterShaderSetSampler(shader, binding->index, samplers + binding->offset); break;
            case 2: FosterShaderSetTexture(shader, binding->index, textures + binding->offset); break;
        }
    }
}
