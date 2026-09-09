#include <string.h>
#pragma GCC push_options
#pragma GCC optimize ("fp-contract=off")
int FosterRenderMatrixMultiply(const float *a,const float *b,float *output);
int FosterRenderSrtMatrix(const float *scale,const float *q,const float *translation,float *output);
int FosterRenderSrtMatrix(const float *scale,const float *q,const float *translation,float *output)
{
    // Operation order from the actual pinned CoreLib CreateFromQuaternion IL.
    float xx=q[0]*q[0],yy=q[1]*q[1],zz=q[2]*q[2];
    float xy=q[0]*q[1],zw=q[2]*q[3],zx=q[2]*q[0],yw=q[1]*q[3];
    float yz=q[1]*q[2],xw=q[0]*q[3];
    float rotation[16]={1.f-2.f*(yy+zz),2.f*(xy+zw),2.f*(zx-yw),0.f,
                       2.f*(xy-zw),1.f-2.f*(zz+xx),2.f*(yz+xw),0.f,
                       2.f*(zx+yw),2.f*(yz-xw),1.f-2.f*(yy+xx),0.f,
                       0.f,0.f,0.f,1.f};
    float scaling[16]={scale[0],0.f,0.f,0.f,0.f,scale[1],0.f,0.f,
                       0.f,0.f,scale[2],0.f,0.f,0.f,0.f,1.f};
    float savedTranslation[3];memcpy(savedTranslation,translation,sizeof(savedTranslation));
    // Keep the full product, including zero terms and all intermediate rounding.
    // Nonfinite/overflowing matrices use the existing managed fallback.
    if(!FosterRenderMatrixMultiply(scaling,rotation,output))return 0;
    memcpy(output+12,savedTranslation,sizeof(savedTranslation));
    return 1;
}
#pragma GCC pop_options
