/*
 * Kitsune-style damped traffic statistics computed on the node itself (Mirsky et al., NDSS 2018,
 * "AfterImage" incremental statistics), for the node's own outgoing and incoming packets.
 *
 * For each direction (out, in), quantity (packet size, inter-packet gap) and decay rate
 * lambda in {5, 3, 1, 0.1, 0.01} per second we keep (w, LS, SS) and report weight, mean and
 * variance: 2 x 2 x 5 x 3 = 60 raw features. Like the N-BaIoT pipeline in experiments/foa/data.py,
 * they are sign-log transformed, standardised with fleet-wide constants and projected onto the
 * fleet's 10-D basis (foa_config.h, produced by firmware/fit_calibration.py).
 */
#ifndef FOA_FEATURES_H
#define FOA_FEATURES_H

#include <stdint.h>
#include "foa_core.h"

#ifdef __cplusplus
extern "C" {
#endif

#define FEAT_LAMBDAS 5
#define FEAT_N 60

typedef struct { float w, ls, ss; uint32_t t_us; } foa_incstat_t;

typedef struct {
    foa_incstat_t size[2][FEAT_LAMBDAS], gap[2][FEAT_LAMBDAS];
    uint32_t last_pkt_us[2];
    uint8_t seen[2];
} foa_feat_t;

enum { FEAT_OUT = 0, FEAT_IN = 1 };

void feat_init(foa_feat_t *f);
void feat_observe(foa_feat_t *f, int dir, float bytes, uint32_t t_us);
void feat_vector(const foa_feat_t *f, uint32_t t_us, float out[FEAT_N]);
void feat_project(const float raw[FEAT_N], const float *mean, const float *std, const float *W, float z[FOA_D]);

#ifdef __cplusplus
}
#endif
#endif
