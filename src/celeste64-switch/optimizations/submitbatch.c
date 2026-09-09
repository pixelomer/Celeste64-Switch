#include "foster_platform.h"
struct SwitchUniformBinding;
void FosterShaderApplyUniforms(FosterShader*,const struct SwitchUniformBinding*,int,float*,FosterTextureSampler*,FosterTexture**);
void FosterShaderApplyAndDraw(FosterShader* shader,const struct SwitchUniformBinding* bindings,int count,
    float* floats,FosterTextureSampler* samplers,FosterTexture** textures,FosterDrawCommand* command);
void FosterShaderApplyAndDraw(FosterShader* shader,const struct SwitchUniformBinding* bindings,int count,
    float* floats,FosterTextureSampler* samplers,FosterTexture** textures,FosterDrawCommand* command)
{
    // Preserve every setter, then the exact draw command; only cross the managed
    // boundary once. Neither GL order nor batching/flush policy changes here.
    FosterShaderApplyUniforms(shader,bindings,count,floats,samplers,textures);
    FosterDraw(command);
}
