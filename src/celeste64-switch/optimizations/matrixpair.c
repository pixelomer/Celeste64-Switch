#include <string.h>

extern int FosterRenderMatrixMultiply(const float* a, const float* b, float* output);

// Keep both intermediate products and their order. The managed caller handles
// any nonfinite input/intermediate using its existing per-product fallback.
int FosterRenderMatrixPair(const float* a, const float* b, const float* c,
                          float* first, float* second)
{
    float ab[16], abc[16];
    if (!FosterRenderMatrixMultiply(a, b, ab)) return 0;
    if (!FosterRenderMatrixMultiply(ab, c, abc)) return 0;
    memcpy(first, ab, sizeof(ab));
    memcpy(second, abc, sizeof(abc));
    return 1;
}
