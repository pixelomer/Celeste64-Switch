#include <stddef.h>
#include <string.h>
void FosterCopySkinMatrices(void *destination,const void *source,int count);
void FosterCopySkinMatrices(void *destination,const void *source,int count)
{
    if(count>0)memmove(destination,source,(size_t)count*16*sizeof(float));
}
