#include <string.h>
#include <stddef.h>
void FosterMaterialCopyMatrixPair(float* destinationA,const float* sourceA,int countA,float* destinationB,const float* sourceB,int countB);
void FosterMaterialCopyMatrixPair(float* destinationA,const float* sourceA,int countA,float* destinationB,const float* sourceB,int countB)
{
    if(countA>0)memmove(destinationA,sourceA,(size_t)countA*sizeof(float));
    if(countB>0)memmove(destinationB,sourceB,(size_t)countB*sizeof(float));
}
