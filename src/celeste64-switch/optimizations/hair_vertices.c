#include <stdint.h>
#include <string.h>
#if defined(__aarch64__)
#include <arm_neon.h>
#endif

#pragma GCC push_options
#pragma GCC optimize ("fp-contract=off")
static int nonfinite(float f) {
    uint32_t bits; memcpy(&bits, &f, 4);
    return (bits & 0x7f800000u) == 0x7f800000u;
}

// Vertex is the pinned game's packed 19-float record. Source and destination
// are separate spans owned by Hair. Return zero before writing on exceptional
// position/matrix input so the caller retains BCL NaN propagation.
int FosterFillHairVertices(const float* source, int count, const float* matrix, float* destination)
{
    for (int i = 0; i < 16; i++) if (nonfinite(matrix[i])) return 0;
    for (int i = 0; i < count; i++)
        for (int lane = 0; lane < 3; lane++) if (nonfinite(source[i*19+lane])) return 0;
#if defined(__aarch64__)
    const float32x4_t x = vld1q_f32(matrix), y = vld1q_f32(matrix+4);
    const float32x4_t z = vld1q_f32(matrix+8), translation = vld1q_f32(matrix+12);
#endif
    for (int i = 0; i < count; i++) {
        const float* s = source+i*19;
        float* d = destination+i*19;
#if defined(__aarch64__)
        float32x4_t p = vmulq_n_f32(x, s[0]);
        p = vaddq_f32(vmulq_n_f32(y, s[1]), p);
        p = vaddq_f32(vmulq_n_f32(z, s[2]), p);
        p = vaddq_f32(p, translation);
        vst1q_f32(d, p); // fourth lane is overwritten with Tex.X below
#else
        for (int lane = 0; lane < 3; lane++) {
            float p = matrix[lane] * s[0];
            p = matrix[4+lane] * s[1] + p;
            p = matrix[8+lane] * s[2] + p;
            d[lane] = p + matrix[12+lane];
        }
#endif
        d[3] = d[4] = 0;
        d[5] = d[6] = d[7] = 1;
        memcpy(d+8, s+8, 3*sizeof(float));
        d[11] = d[12] = d[13] = d[14] = 0;
        d[15] = d[16] = d[17] = d[18] = 1;
    }
    return 1;
}
#pragma GCC pop_options
