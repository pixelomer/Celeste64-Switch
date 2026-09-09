#include <string.h>
#include <stddef.h>
int FosterRenderMatrixPair(const float*,const float*,const float*,float*,float*);
int FosterMaterialComputeMatrices(const float* local,const float* world,const float* projection,float* first,float* second,
    float* destinationA,int countA,float* destinationB,int countB);
int FosterMaterialComputeMatrices(const float* local,const float* world,const float* projection,float* first,float* second,
    float* destinationA,int countA,float* destinationB,int countB)
{
    // The existing exact product validates both intermediates before any output.
    if(!FosterRenderMatrixPair(local,world,projection,first,second))return 0;
    if(countA>0)memmove(destinationA,first,(size_t)countA*sizeof(float));
    if(countB>0)memmove(destinationB,second,(size_t)countB*sizeof(float));
    return 1;
}
