#include <string.h>
#include <stddef.h>
typedef struct { int start,count; } CopyBlock;
typedef struct { CopyBlock vertex,joints,fragment; } CopyPlan;
_Static_assert(sizeof(CopyPlan)==24,"Stage copy plan ABI");
void FosterStageCopyBatch(float* target,const void* vertex,const void* joints,const void* fragment,const CopyPlan* plan);
void FosterStageCopyBatch(float* target,const void* vertex,const void* joints,const void* fragment,const CopyPlan* plan)
{
    if(plan->vertex.count>0)memmove(target+plan->vertex.start,vertex,(size_t)plan->vertex.count*4);
    if(plan->joints.count>0)memmove(target+plan->joints.start,joints,(size_t)plan->joints.count*4);
    if(plan->fragment.count>0)memmove(target+plan->fragment.start,fragment,(size_t)plan->fragment.count*4);
}
