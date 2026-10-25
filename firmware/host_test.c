/*
 * Host test of the ESP32 FOA core against the Python reference, plus a timing microbenchmark.
 *
 *   python3 firmware/make_vectors.py
 *   cc -O2 -std=c99 -Wall -Wextra -o firmware/host_test firmware/host_test.c \
 *      firmware/esp32_foa/foa_core.c firmware/esp32_foa/foa_sha256.c -lm
 *   ./firmware/host_test firmware/vectors.bin
 *
 * Checks, per recorded cycle (no error compounding: each cycle starts from Python's state):
 *   1. foa_propose on the same batch gives Python's proposal (float32 vs float64 tolerance),
 *   2. foa_step on Python's proposal and peers gives Python's update and FOA state,
 *   3. frames packed in C are byte-identical to Python's, verify accepts them, and every
 *      single-bit flip, wrong key and stale cycle is rejected; HMAC matches RFC 4231 case 2.
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "esp32_foa/foa_core.h"
#include "esp32_foa/foa_sha256.h"

static const unsigned char *P;
static float rf(void) { float f; memcpy(&f, P, 4); P += 4; return f; }
static int ri(void) { int v; memcpy(&v, P, 4); P += 4; return v; }
static void rfv(float *x, int n) { for (int i = 0; i < n; i++) x[i] = rf(); }

static void read_state(foa_state_t *st) {
    foa_state_init(st);
    rfv(st->C, FOA_D); rfv(st->R, FOA_D); rfv(st->m_ema, FOA_D); rfv(st->p_ema, FOA_D);
    st->Cs = rf(); st->Rs = rf(); st->ms_ema = rf(); st->ps_ema = rf(); st->pa_ema = rf(); st->sig_ema = rf(); st->sigs_ema = rf();
}

static float maxrel(const float *a, const float *b, int n, float floor) {
    float m = 0;
    for (int i = 0; i < n; i++) {
        float e = fabsf(a[i] - b[i]) / (fabsf(b[i]) > floor ? fabsf(b[i]) : floor);
        if (e > m) m = e;
    }
    return m;
}

static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + 1e-9 * t.tv_nsec; }

int main(int argc, char **argv) {
    const char *path = argc > 1 ? argv[1] : "firmware/vectors.bin";
    FILE *f = fopen(path, "rb");
    if (!f) { perror(path); return 2; }
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    unsigned char *buf = malloc(sz);
    if (fread(buf, 1, sz, f) != (size_t)sz) { fprintf(stderr, "short read\n"); return 2; }
    fclose(f);
    if (memcmp(buf, "FOAV1", 5)) { fprintf(stderr, "bad magic\n"); return 2; }
    P = buf + 8;
    int n_cases = ri();
    foa_detector_t det;
    rfv(det.mu0, FOA_D); det.s0 = rf(); det.tau = rf(); det.c = rf(); det.kappa = rf(); det.beta = rf(); det.f0 = rf(); det.eta = rf();
    foa_params_t prm;
    prm.B0 = rf(); prm.B = rf(); prm.B0s = rf(); prm.Bs = rf(); prm.B0c = rf(); prm.Bc = rf(); prm.B0cs = rf(); prm.Bcs = rf();
    prm.alpha = rf(); prm.z0 = rf(); prm.z1 = rf();
    prm.k_min = (uint8_t)ri(); prm.lam_gate = (uint8_t)ri(); prm.signif = (uint8_t)ri(); prm.common_budget = (uint8_t)ri();
    prm.robust_lam = (uint8_t)ri();

    static float X[FOA_MAX_BATCH * FOA_D];
    float pdmu[FOA_MAX_PEERS * FOA_D], pdls[FOA_MAX_PEERS];
    int prop_bad = 0, step_bad = 0, ncore_bad = 0, below_kmin = 0;
    float worst_prop = 0, worst_step = 0, worst_state = 0;
    for (int c = 0; c < n_cases; c++) {
        int tj = ri(), n = ri(), K = ri();
        rfv(det.mu0, FOA_D); det.s0 = rf(); det.tau = rf(); det.c = rf(); det.kappa = rf(); det.beta = rf(); det.f0 = rf(); det.eta = rf();
        rfv(det.mu, FOA_D); det.s = rf();
        foa_state_t st, st_exp;
        read_state(&st);
        rfv(X, n * FOA_D);
        rfv(pdmu, K * FOA_D); rfv(pdls, K);
        foa_proposal_t exp_prop; rfv(exp_prop.dmu, FOA_D); exp_prop.dls = rf(); exp_prop.along = rf(); exp_prop.n_core = (uint16_t)ri();
        float exp_out[FOA_D + 1]; rfv(exp_out, FOA_D + 1);
        read_state(&st_exp);
        if (K < prm.k_min) below_kmin++;

        foa_proposal_t prop;
        float u[FOA_D];
        int has_u = foa_consensus_direction(&st, u);
        foa_propose(&det, X, n, has_u ? u : NULL, &prop);
        float e_along = fabsf(prop.along - exp_prop.along) / (1e-3f * det.s0);
        if (e_along > 10.0f) prop_bad++;
        float scale = 1e-3f * det.s0;
        float e1 = maxrel(prop.dmu, exp_prop.dmu, FOA_D, scale);
        float e1s = fabsf(prop.dls - exp_prop.dls) / 1e-3f;
        if (prop.n_core != exp_prop.n_core) ncore_bad++;
        if (e1 > 1e-2f || e1s > 1e-2f) prop_bad++;
        if (e1 > worst_prop) worst_prop = e1;

        float out[FOA_D], out_dls;
        foa_step(&st, &prm, det.tau * det.s0, (uint32_t)tj, &exp_prop, pdmu, pdls, K, out, &out_dls);
        float e2 = maxrel(out, exp_out, FOA_D, scale);
        float e2s = fabsf(out_dls - exp_out[FOA_D]) / 1e-3f;
        float e3 = fmaxf(maxrel(st.C, st_exp.C, FOA_D, scale), maxrel(st.R, st_exp.R, FOA_D, scale));
        if (e2 > 1e-2f || e2s > 1e-2f || e3 > 1e-2f) step_bad++;
        if (e2 > worst_step) worst_step = e2;
        if (e3 > worst_state) worst_state = e3;
    }
    printf("cycles checked            %d (%d with fewer than k_min peers)\n", n_cases, below_kmin);
    printf("proposal mismatches       %d   (n_core differs in %d; worst rel. error %.2e)\n", prop_bad, ncore_bad, worst_prop);
    printf("FOA step mismatches       %d   (worst rel. error update %.2e, state %.2e)\n", step_bad, worst_step, worst_state);

    /* frames */
    int n_frames = ri(), frame_bad = 0, reject_bad = 0, flips = 0;
    for (int k = 0; k < n_frames; k++) {
        uint8_t snd = *P++; uint32_t cyc; memcpy(&cyc, P, 4); P += 4;
        float dmu[FOA_D]; rfv(dmu, FOA_D); float dls = rf();
        uint16_t nc; memcpy(&nc, P, 2); P += 2;
        uint8_t key[32], pyframe[FOA_FRAME_BYTES], cframe[FOA_FRAME_BYTES];
        memcpy(key, P, 32); P += 32; memcpy(pyframe, P, FOA_FRAME_BYTES); P += FOA_FRAME_BYTES;
        foa_frame_pack(cframe, snd, cyc, dmu, dls, nc, key);
        if (memcmp(cframe, pyframe, FOA_FRAME_BYTES)) frame_bad++;
        float o[FOA_D], ol; uint16_t on;
        if (foa_frame_verify(pyframe, FOA_FRAME_BYTES, key, cyc, o, &ol, &on) != FOA_OK || on != nc || memcmp(o, dmu, sizeof o)) frame_bad++;
        if (foa_frame_verify(pyframe, FOA_FRAME_BYTES, key, cyc + 1, o, &ol, &on) != FOA_ERR_STALE) reject_bad++;
        uint8_t wrong[32]; memcpy(wrong, key, 32); wrong[0] ^= 1;
        if (foa_frame_verify(pyframe, FOA_FRAME_BYTES, wrong, cyc, o, &ol, &on) != FOA_ERR_TAG) reject_bad++;
        for (int b = 8 * 2; b < 8 * FOA_FRAME_BYTES; b++) {      /* every bit after version/sender */
            uint8_t t[FOA_FRAME_BYTES]; memcpy(t, pyframe, FOA_FRAME_BYTES); t[b / 8] ^= (uint8_t)(1 << (b % 8));
            if (foa_frame_verify(t, FOA_FRAME_BYTES, key, cyc, o, &ol, &on) == FOA_OK) reject_bad++;
            flips++;
        }
    }
    /* RFC 4231 test case 2 */
    uint8_t mac[32];
    const char *exp_hex = "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843";
    foa_hmac_sha256((const uint8_t *)"Jefe", 4, (const uint8_t *)"what do ya want for nothing?", 28, mac);
    char hex[65]; for (int i = 0; i < 32; i++) sprintf(hex + 2 * i, "%02x", mac[i]);
    int rfc_ok = strcmp(hex, exp_hex) == 0;
    printf("frames byte-identical     %d/%d\n", n_frames - frame_bad, n_frames);
    printf("bad frames accepted       %d   (of %d bit flips + %d wrong-key + %d stale)\n", reject_bad, flips, n_frames, n_frames);
    printf("HMAC-SHA256 RFC 4231 #2   %s\n", rfc_ok ? "pass" : "FAIL");

    /* timing on this host (not the ESP32; see the paper for the scaling estimate) */
    foa_detector_t d2 = det; for (int i = 0; i < FOA_D; i++) d2.mu[i] = d2.mu0[i]; d2.s = d2.s0;
    srand(1);
    for (int i = 0; i < 200 * FOA_D; i++) X[i] = d2.mu0[i % FOA_D] + d2.s0 * ((rand() / (float)RAND_MAX) - 0.5f) * 3.0f;
    for (int i = 0; i < 8 * FOA_D; i++) pdmu[i] = 0.01f * ((rand() / (float)RAND_MAX) - 0.5f);
    for (int i = 0; i < 8; i++) pdls[i] = 0.001f * i;
    foa_proposal_t pr; foa_state_t s2; foa_state_init(&s2);
    int reps = 20000; double t0 = now();
    volatile float sink = 0;
    float u2[FOA_D] = {1.0f};
    for (int r = 0; r < reps; r++) { foa_propose(&d2, X, 200, u2, &pr); sink += pr.dmu[0]; }
    double t_prop = (now() - t0) / reps;
    float o2[FOA_D], ol2; t0 = now();
    for (int r = 0; r < reps; r++) { foa_step(&s2, &prm, d2.tau * d2.s0, (uint32_t)r, &pr, pdmu, pdls, 8, o2, &ol2); sink += o2[0]; }
    double t_step = (now() - t0) / reps;
    uint8_t fr[FOA_FRAME_BYTES]; t0 = now();
    for (int r = 0; r < reps; r++) { foa_frame_pack(fr, 1, (uint32_t)r, pdmu, 0.0f, 100, (const uint8_t *)"0123456789abcdef0123456789abcdef"); sink += fr[60]; }
    double t_mac = (now() - t0) / reps;
    printf("host time per call        propose(200 pts) %.2f us, foa_step(8 peers) %.2f us, frame pack+HMAC %.2f us\n",
           1e6 * t_prop, 1e6 * t_step, 1e6 * t_mac);
    printf("state size                detector %zu B, FOA state %zu B, frame %d B\n", sizeof(foa_detector_t), sizeof(foa_state_t), FOA_FRAME_BYTES);
    int ok = prop_bad <= n_cases / 100 && step_bad == 0 && frame_bad == 0 && reject_bad == 0 && rfc_ok;
    printf("%s\n", ok ? "ALL CHECKS PASSED" : "CHECKS FAILED");
    free(buf);
    return ok ? 0 : 1;
}
