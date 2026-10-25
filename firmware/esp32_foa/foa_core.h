/*
 * Fleet-Orthogonal Adaptation (FOA): on-device detector and update rule, portable C99.
 *
 * Mirrors experiments/foa/detector.py (propose, auto rule) and experiments/foa/foa_rule.py
 * (foa_step) and is tested against them by firmware/host_test.c. No heap, no libc beyond math.h
 * and string.h, single-precision floats only (the ESP32 FPU is single precision).
 *
 * Memory: one detector + one FOA state = 4 * (2*10 + 8) + 4 * (4*10 + 8) = 304 bytes.
 */
#ifndef FOA_CORE_H
#define FOA_CORE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define FOA_D 16
#define FOA_MAX_PEERS 16
#define FOA_MAX_BATCH 512
#define FOA_FRAME_BYTES 92
#define FOA_TAG_BYTES 16
#define FOA_FRAME_VERSION 1

typedef struct {
    float mu0[FOA_D], mu[FOA_D];
    float s0, s, tau, c, kappa, beta, f0, eta;
} foa_detector_t;

typedef struct {
    float dmu[FOA_D];
    float dls;
    uint16_t n_acc, n_core;
    float alarm;
    float along;                 /* eta * median projection of core points on the consensus direction */
} foa_proposal_t;

typedef struct {
    float B0, B, B0s, Bs;        /* residual budget: displacement (alarm radii) and log spread */
    float B0c, Bc, B0cs, Bcs;    /* common-channel budget (alarm radii, log spread)            */
    float alpha, z0, z1;         /* EMA weight and significance ramp                           */
    uint8_t k_min, lam_gate, signif, common_budget, robust_lam;
} foa_params_t;

typedef struct {
    float C[FOA_D], R[FOA_D], m_ema[FOA_D], p_ema[FOA_D];
    float Cs, Rs, ms_ema, ps_ema, pa_ema, sig_ema, sigs_ema;
    float lam, w;                /* last agreement and significance, for logging              */
} foa_state_t;

enum { FOA_OK = 0, FOA_ERR_LEN = -1, FOA_ERR_VERSION = -2, FOA_ERR_TAG = -3, FOA_ERR_STALE = -4 };

void foa_default_params(foa_params_t *p);
void foa_state_init(foa_state_t *st);

/* On-device calibration from clean traffic (mirrors detector.py's constructor; beta uses a
   different random stream, so it agrees with Python only statistically). Uses scratch of n floats. */
int foa_calibrate(foa_detector_t *d, const float *X, int n, float *scratch, float eta);

float foa_score(const foa_detector_t *d, const float *x);
/* u: unit consensus direction from foa_consensus_direction(), or NULL before any consensus. */
void foa_propose(const foa_detector_t *d, const float *X, int n, const float *u, foa_proposal_t *out);
int foa_consensus_direction(const foa_state_t *st, float *u);
void foa_geometric_median(const float *M, int K, int iters, float *out);
void foa_step(foa_state_t *st, const foa_params_t *p, float rho, uint32_t tj, const foa_proposal_t *own,
              const float *peer_dmu, const float *peer_dls, int K, float *out_dmu, float *out_dls);
/* rho is the calibrated alarm radius tau * s0: budgets are fractions of it. */
void foa_apply(foa_detector_t *d, const float *dmu, float dls);

/* Authenticated gossip frame, byte-identical to experiments/foa/gossip.py. */
void foa_frame_pack(uint8_t frame[FOA_FRAME_BYTES], uint8_t sender, uint32_t cycle, const float *dmu, float dls,
                    uint16_t n_core, const uint8_t key[32]);
uint8_t foa_frame_sender(const uint8_t *frame);
int foa_frame_verify(const uint8_t *frame, size_t len, const uint8_t key[32], uint32_t cycle,
                     float *dmu, float *dls, uint16_t *n_core);

#ifdef __cplusplus
}
#endif
#endif
