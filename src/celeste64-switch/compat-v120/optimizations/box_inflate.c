#include <stdint.h>
#include <string.h>
#pragma GCC push_options
#pragma GCC optimize ("fp-contract=off")
static int box_finite(float value)
{
    uint32_t bits;memcpy(&bits,&value,4);
    return (bits&0x7f800000u)!=0x7f800000u;
}
int FosterInflateBox(const float* box,float amount,float* result);
int FosterInflateBox(const float* box,float amount,float* result)
{
    if(!box_finite(amount)) return 0;
    for(int i=0;i<6;i++) if(!box_finite(box[i])) return 0;
    float values[6];
    // Preserve Size + One*amount*2 and Center +/- size/2, including each
    // intermediate rounding. This deliberately does not simplify to min-pad.
    for(int i=0;i<3;i++)
    {
        float size=(box[i+3]-box[i])+((1.0f*amount)*2.0f);
        float center=(box[i]+box[i+3])/2.0f;
        values[i]=center-size/2.0f;
        values[i+3]=center+size/2.0f;
    }
    for(int i=0;i<6;i++) if(!box_finite(values[i])) return 0;
    memcpy(result,values,sizeof(values));
    return 1;
}
#pragma GCC pop_options
