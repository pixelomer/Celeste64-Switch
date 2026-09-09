#include <stddef.h>
#include <string.h>
void FosterMaterialCopyFloats(float *destination,const float *source,int count);
void FosterMaterialCopyFloats(float *destination,const float *source,int count)
{
    if(count>0)memmove(destination,source,(size_t)count*sizeof(float));
}
