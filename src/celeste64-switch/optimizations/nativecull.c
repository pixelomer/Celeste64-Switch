#include <stdint.h>
#include <string.h>
#pragma GCC push_options
#pragma GCC optimize ("fp-contract=off")
_Static_assert(sizeof(float) == 4, "Frustum scalar ABI");

static int finite_scalar(float value)
{
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    return (bits & 0x7f800000u) != 0x7f800000u;
}

// Six packed box scalars (min/max) and six packed System.Numerics.Planes.
// Exceptional inputs use the original managed implementation. Preserve the
// original negative-vertex choice and separate product/sum rounding.
int FosterBoxInFrustum(const float* box, const float* planes)
{
    for (int i=0;i<6;i++) if (!finite_scalar(box[i])) return -1;
    for (int i=0;i<24;i++) if (!finite_scalar(planes[i])) return -1;
    for (int i=0;i<6;i++)
    {
        const float* p=planes+i*4;
        float x=p[0]>=0 ? box[0] : box[3];
        float y=p[1]>=0 ? box[1] : box[4];
        float z=p[2]>=0 ? box[2] : box[5];
        float xy=p[0]*x+p[1]*y;
        float xyz=xy+p[2]*z;
        if (xyz+p[3]>0) return 0;
    }
    return 1;
}
#pragma GCC pop_options
