#include <stdint.h>
#include <string.h>
#if defined(__aarch64__)
#include <arm_neon.h>
#endif

// The pinned Mono AOT reference implementation uses separate FMUL/FADD, not fused FMLA.
// Keep that rounding at each step. Do not enable fast-math for this file.
#pragma GCC push_options
#pragma GCC optimize ("fp-contract=off")
_Static_assert(sizeof(float) == 4, "Matrix scalar ABI");

// Return zero for non-finite inputs so the managed caller uses the original
// BCL path, including its exceptional-value propagation. Output may alias input.
int FosterRenderMatrixMultiply(const float* a, const float* b, float* output)
{
#if defined(__aarch64__)
    float32x4_t rowsA[4], rowsB[4], result[4];
    uint32x4_t invalid = vdupq_n_u32(0);
    const uint32x4_t exponent = vdupq_n_u32(0x7f800000u);
    for (int i = 0; i < 4; i++)
    {
        rowsA[i] = vld1q_f32(a + i * 4);
        rowsB[i] = vld1q_f32(b + i * 4);
        invalid = vorrq_u32(invalid, vceqq_u32(vandq_u32(vreinterpretq_u32_f32(rowsA[i]), exponent), exponent));
        invalid = vorrq_u32(invalid, vceqq_u32(vandq_u32(vreinterpretq_u32_f32(rowsB[i]), exponent), exponent));
    }
    if (vmaxvq_u32(invalid) != 0) return 0;
    for (int i = 0; i < 4; i++)
    {
        float32x4_t v = vmulq_laneq_f32(rowsB[0], rowsA[i], 0);
        v = vaddq_f32(vmulq_laneq_f32(rowsB[1], rowsA[i], 1), v);
        v = vaddq_f32(vmulq_laneq_f32(rowsB[2], rowsA[i], 2), v);
        result[i] = vaddq_f32(vmulq_laneq_f32(rowsB[3], rowsA[i], 3), v);
    }
    for (int i = 0; i < 4; i++) vst1q_f32(output + i * 4, result[i]);
#else
    for (int i = 0; i < 16; i++)
    {
        uint32_t av, bv;
        memcpy(&av, a + i, 4); memcpy(&bv, b + i, 4);
        if ((av & 0x7f800000u) == 0x7f800000u || (bv & 0x7f800000u) == 0x7f800000u) return 0;
    }
    float result[16];
    for (int row = 0; row < 4; row++)
        for (int col = 0; col < 4; col++)
        {
            float v = b[col] * a[row * 4];
            v = b[4 + col] * a[row * 4 + 1] + v;
            v = b[8 + col] * a[row * 4 + 2] + v;
            result[row * 4 + col] = b[12 + col] * a[row * 4 + 3] + v;
        }
    memcpy(output, result, sizeof(result));
#endif
    return 1;
}
#pragma GCC pop_options
