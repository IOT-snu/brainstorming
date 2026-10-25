#include "foa_features.h"

#include <math.h>
#include <string.h>

static const float LAMBDA[FEAT_LAMBDAS] = {5.0f, 3.0f, 1.0f, 0.1f, 0.01f};

static float decay(float lambda, uint32_t from_us, uint32_t to_us) {
    float dt = (float)(uint32_t)(to_us - from_us) * 1e-6f;   /* wrap-safe */
    return exp2f(-lambda * dt);
}

static void inc(foa_incstat_t *s, float lambda, float x, uint32_t t_us) {
    float f = s->w > 0.0f ? decay(lambda, s->t_us, t_us) : 1.0f;
    s->w = s->w * f + 1.0f;
    s->ls = s->ls * f + x;
    s->ss = s->ss * f + x * x;
    s->t_us = t_us;
}

void feat_init(foa_feat_t *f) { memset(f, 0, sizeof *f); }

void feat_observe(foa_feat_t *f, int dir, float bytes, uint32_t t_us) {
    for (int l = 0; l < FEAT_LAMBDAS; l++) inc(&f->size[dir][l], LAMBDA[l], bytes, t_us);
    if (f->seen[dir]) {
        float gap = (float)(uint32_t)(t_us - f->last_pkt_us[dir]) * 1e-6f;
        for (int l = 0; l < FEAT_LAMBDAS; l++) inc(&f->gap[dir][l], LAMBDA[l], gap, t_us);
    }
    f->last_pkt_us[dir] = t_us;
    f->seen[dir] = 1;
}

static void emit(const foa_incstat_t *s, float lambda, uint32_t t_us, float *o) {
    if (s->w <= 0.0f) { o[0] = o[1] = o[2] = 0.0f; return; }
    float mean = s->ls / s->w;
    o[0] = s->w * decay(lambda, s->t_us, t_us);      /* weight decays to now; mean and variance do not */
    o[1] = mean;
    o[2] = fabsf(s->ss / s->w - mean * mean);
}

void feat_vector(const foa_feat_t *f, uint32_t t_us, float out[FEAT_N]) {
    int k = 0;
    for (int dir = 0; dir < 2; dir++)
        for (int l = 0; l < FEAT_LAMBDAS; l++) {
            emit(&f->size[dir][l], LAMBDA[l], t_us, out + k); k += 3;
            emit(&f->gap[dir][l], LAMBDA[l], t_us, out + k); k += 3;
        }
}

void feat_project(const float raw[FEAT_N], const float *mean, const float *std, const float *W, float z[FOA_D]) {
    for (int j = 0; j < FOA_D; j++) z[j] = 0.0f;
    for (int i = 0; i < FEAT_N; i++) {
        float x = raw[i];
        float v = (x < 0 ? -1.0f : 1.0f) * log1pf(fabsf(x));
        v = (v - mean[i]) / std[i];
        for (int j = 0; j < FOA_D; j++) z[j] += v * W[i * FOA_D + j];
    }
    for (int j = 0; j < FOA_D; j++) z[j] = z[j] > 1e3f ? 1e3f : (z[j] < -1e3f ? -1e3f : z[j]);
}
