#include "foa_core.h"
#include "foa_sha256.h"

#include <math.h>
#include <string.h>

#define D FOA_D

/* ------------------------------------------------------------------ small helpers */
static float dot(const float *a, const float *b) {
    float s = 0.0f;
    for (int i = 0; i < D; i++) s += a[i] * b[i];
    return s;
}

static float dist2(const float *a, const float *b) {
    float s = 0.0f;
    for (int i = 0; i < D; i++) { float d = a[i] - b[i]; s += d * d; }
    return s;
}

static float clampf(float x, float lo, float hi) { return x < lo ? lo : (x > hi ? hi : x); }

static void sortf(float *a, int n) {
    for (int i = 1; i < n; i++) {
        float v = a[i]; int j = i - 1;
        while (j >= 0 && a[j] > v) { a[j + 1] = a[j]; j--; }
        a[j + 1] = v;
    }
}

/* Median with numpy's convention (mean of the two middle values when n is even). Sorts a. */
static float median_inplace(float *a, int n) {
    sortf(a, n);
    return (n & 1) ? a[n / 2] : 0.5f * (a[n / 2 - 1] + a[n / 2]);
}

/* Closest point to v with norm <= radius, in place. */
static void project_ball(float *v, float radius) {
    float n = sqrtf(dot(v, v));
    if (n > radius) { float k = radius / n; for (int i = 0; i < D; i++) v[i] *= k; }
}

static float ramp_weight(float z, float z0, float z1) { return clampf((z - z0) / (z1 - z0), 0.0f, 1.0f); }

/* ------------------------------------------------------------------ detector */
void foa_default_params(foa_params_t *p) {
    p->B0 = 0.1f; p->B = 0.005f; p->B0s = 0.1f; p->Bs = 0.001f;
    p->B0c = 0.75f; p->Bc = 0.06f; p->B0cs = 0.7f; p->Bcs = 0.02f;
    p->alpha = 0.2f; p->z0 = 2.0f; p->z1 = 4.0f;
    p->k_min = 2; p->lam_gate = 1; p->signif = 1; p->common_budget = 1; p->robust_lam = 1;
}

void foa_state_init(foa_state_t *st) { memset(st, 0, sizeof *st); }

float foa_score(const foa_detector_t *d, const float *x) { return sqrtf(dist2(x, d->mu)) / d->s; }

/* numpy's default (linear) quantile of a sorted array */
static float quantile_sorted(const float *a, int n, float q) {
    float h = (n - 1) * q;
    int lo = (int)floorf(h), hi = lo + 1 < n ? lo + 1 : lo;
    return a[lo] + (h - lo) * (a[hi] - a[lo]);
}

static uint32_t rng_state = 7u;
static float urand(void) {                      /* xorshift32 in (0, 1) */
    rng_state ^= rng_state << 13; rng_state ^= rng_state >> 17; rng_state ^= rng_state << 5;
    return ((rng_state >> 8) + 0.5f) * (1.0f / 16777216.0f);
}
static float nrand(void) { return sqrtf(-2.0f * logf(urand())) * cosf(6.2831853f * urand()); }

int foa_calibrate(foa_detector_t *d, const float *X, int n, float *r, float eta) {
    if (n < 50) return -1;
    memset(d->mu0, 0, sizeof d->mu0);
    for (int k = 0; k < n; k++) for (int i = 0; i < D; i++) d->mu0[i] += X[k * D + i] / n;
    float acc = 0.0f;
    for (int k = 0; k < n; k++) acc += dist2(X + k * D, d->mu0);
    d->s0 = sqrtf(acc / n / D);
    for (int k = 0; k < n; k++) r[k] = sqrtf(dist2(X + k * D, d->mu0)) / d->s0;
    /* r is sorted for the quantiles, so per-point radii are recomputed below */
    sortf(r, n);
    d->tau = quantile_sorted(r, n, 0.99f);
    d->c = quantile_sorted(r, n, 0.8f);
    float kc = 0.0f; int nc = 0, nacc = 0, nshell = 0;
    for (int k = 0; k < n; k++) {
        float rk = sqrtf(dist2(X + k * D, d->mu0)) / d->s0;
        if (rk <= d->c) { kc += dist2(X + k * D, d->mu0); nc++; }
        if (rk <= d->tau) { nacc++; if (rk > d->c) nshell++; }
    }
    d->kappa = sqrtf(kc / nc / D) / d->s0;
    d->f0 = (float)nshell / (float)nacc;
    float ratios[40];
    for (int j = 0; j < 40; j++) {
        float dir[D], nd = 0.0f, mc[D] = {0}, msh[D] = {0}; int c1 = 0, c2 = 0;
        for (int i = 0; i < D; i++) { dir[i] = nrand(); nd += dir[i] * dir[i]; }
        nd = sqrtf(nd);
        for (int i = 0; i < D; i++) dir[i] /= nd;
        for (int k = 0; k < n; k++) {
            float y[D];
            for (int i = 0; i < D; i++) y[i] = X[k * D + i] + 0.3f * d->s0 * dir[i];
            float rk = sqrtf(dist2(y, d->mu0)) / d->s0;
            if (rk > d->tau) continue;
            if (rk <= d->c) { for (int i = 0; i < D; i++) mc[i] += y[i]; c1++; }
            else { for (int i = 0; i < D; i++) msh[i] += y[i]; c2++; }
        }
        float dc = 0.0f, ds = 0.0f;
        for (int i = 0; i < D; i++) {
            dc += (c1 ? mc[i] / c1 - d->mu0[i] : 0.0f) * dir[i];
            ds += (c2 ? msh[i] / c2 - d->mu0[i] : 0.0f) * dir[i];
        }
        ratios[j] = ds / (dc > 1e-9f ? dc : 1e-9f);
    }
    d->beta = median_inplace(ratios, 40);
    d->eta = eta;
    memcpy(d->mu, d->mu0, sizeof d->mu);
    d->s = d->s0;
    return 0;
}

void foa_apply(foa_detector_t *d, const float *dmu, float dls) {
    for (int i = 0; i < D; i++) d->mu[i] += dmu[i];
    d->s *= expf(dls);
}

/* Signature-free proposal (the "auto" rule of detector.py): learn from the dense core only,
   scale the centre move by outer-ring support, gate spread growth on outer-ring backing. */
int foa_consensus_direction(const foa_state_t *st, float *u) {
    float n = sqrtf(dot(st->m_ema, st->m_ema));
    if (n <= 0.0f) return 0;
    for (int i = 0; i < D; i++) u[i] = st->m_ema[i] / n;
    return 1;
}

void foa_propose(const foa_detector_t *d, const float *X, int n, const float *u, foa_proposal_t *out) {
    static uint8_t cls[FOA_MAX_BATCH];          /* 0 alarmed, 1 core, 2 outer ring */
    static float proj[FOA_MAX_BATCH];
    float sc[D] = {0}, ss[D] = {0}, step[D], mu_p[D];
    int n_acc = 0, n_core = 0, n_shell = 0;
    memset(out, 0, sizeof *out);
    if (n <= 0) return;
    if (n > FOA_MAX_BATCH) n = FOA_MAX_BATCH;
    for (int k = 0; k < n; k++) {
        const float *x = X + k * D;
        float r = foa_score(d, x);
        if (r <= d->tau) {
            n_acc++;
            if (r <= d->c) { cls[k] = 1; n_core++; for (int i = 0; i < D; i++) sc[i] += x[i]; }
            else { cls[k] = 2; n_shell++; for (int i = 0; i < D; i++) ss[i] += x[i]; }
        } else cls[k] = 0;
    }
    out->alarm = 1.0f - (float)n_acc / (float)n;
    out->n_acc = (uint16_t)n_acc;
    if (n_acc == 0 || n_core < 5) return;
    if (u) {                                     /* robust agreement: median projection of core points */
        int m = 0;
        for (int k = 0; k < n; k++) if (cls[k] == 1) {
            float pr = 0.0f;
            for (int i = 0; i < D; i++) pr += (X[k * D + i] - d->mu[i]) * u[i];
            proj[m++] = pr;
        }
        out->along = d->eta * median_inplace(proj, m);
    }
    float dcore[D];
    for (int i = 0; i < D; i++) { dcore[i] = sc[i] / n_core - d->mu[i]; step[i] = d->eta * dcore[i]; }
    float nd = sqrtf(dot(dcore, dcore));
    if (n_shell >= 5 && nd > 1e-9f) {
        float dshell = 0.0f;
        for (int i = 0; i < D; i++) dshell += (ss[i] / n_shell - d->mu[i]) * (dcore[i] / nd);
        float sup = clampf(dshell / (d->beta * nd), 0.0f, 1.0f);
        for (int i = 0; i < D; i++) step[i] *= sup;
    }
    for (int i = 0; i < D; i++) mu_p[i] = d->mu[i] + step[i];
    float acc2 = 0.0f;
    for (int k = 0; k < n; k++) if (cls[k] == 1) acc2 += dist2(X + k * D, mu_p);
    float s_core = sqrtf(acc2 / n_core / D) / d->kappa;
    float s_step = d->eta * (s_core - d->s);
    if (s_step > 0.0f) {
        float frac = (float)n_shell / (float)n_acc;
        s_step *= clampf((frac - d->f0) / (0.25f * d->f0) + 1.0f, 0.0f, 1.0f);
    }
    memcpy(out->dmu, step, sizeof step);
    out->dls = logf((d->s + s_step) / d->s);
    out->n_core = (uint16_t)n_core;
}

/* ------------------------------------------------------------------ fleet rule */
void foa_geometric_median(const float *M, int K, int iters, float *y) {
    float tmp[FOA_MAX_PEERS];
    if (K == 1) { memcpy(y, M, sizeof(float) * D); return; }
    for (int i = 0; i < D; i++) {
        for (int k = 0; k < K; k++) tmp[k] = M[k * D + i];
        y[i] = median_inplace(tmp, K);
    }
    for (int it = 0; it < iters; it++) {
        float num[D] = {0}, den = 0.0f, yn[D];
        for (int k = 0; k < K; k++) {
            float dk = sqrtf(dist2(M + k * D, y));
            float w = 1.0f / (dk > 1e-9f ? dk : 1e-9f);
            for (int i = 0; i < D; i++) num[i] += w * M[k * D + i];
            den += w;
        }
        for (int i = 0; i < D; i++) yn[i] = num[i] / den;
        if (sqrtf(dist2(yn, y)) < 1e-12f) break;
        memcpy(y, yn, sizeof yn);
    }
}

void foa_step(foa_state_t *st, const foa_params_t *p, float rho, uint32_t tj, const foa_proposal_t *own,
              const float *peer_dmu, const float *peer_dls, int K, float *out_dmu, float *out_dls) {
    const float al = p->alpha;
    float a[D] = {0}, a_s = 0.0f, lam = 0.0f, w = 0.0f, ws = 0.0f;
    if (K > FOA_MAX_PEERS) K = FOA_MAX_PEERS;
    if (K >= p->k_min) {
        float m[D], tmp[FOA_MAX_PEERS];
        foa_geometric_median(peer_dmu, K, 10, m);
        for (int k = 0; k < K; k++) tmp[k] = peer_dls[k];
        float ms = median_inplace(tmp, K);
        for (int k = 0; k < K; k++) tmp[k] = sqrtf(dist2(peer_dmu + k * D, m));
        float sig = median_inplace(tmp, K) / sqrtf((float)K);
        for (int k = 0; k < K; k++) tmp[k] = fabsf(peer_dls[k] - ms);
        float sig_s = 1.25f * 1.4826f * median_inplace(tmp, K) / sqrtf((float)K);
        for (int i = 0; i < D; i++) st->m_ema[i] = (1 - al) * st->m_ema[i] + al * m[i];
        st->ms_ema = (1 - al) * st->ms_ema + al * ms;
        st->sig_ema = (1 - al) * st->sig_ema + al * sig;
        st->sigs_ema = (1 - al) * st->sigs_ema + al * sig_s;
        float shrink = sqrtf(al / (2 - al));
        if (p->signif) {
            float den = st->sig_ema * shrink, dens = st->sigs_ema * shrink;
            w = ramp_weight(sqrtf(dot(st->m_ema, st->m_ema)) / (den > 1e-12f ? den : 1e-12f), p->z0, p->z1);
            ws = ramp_weight(fabsf(st->ms_ema) / (dens > 1e-12f ? dens : 1e-12f), p->z0, p->z1);
        } else {
            w = ws = 1.0f;
        }
        for (int i = 0; i < D; i++) st->p_ema[i] = (1 - al) * st->p_ema[i] + al * own->dmu[i];
        st->ps_ema = (1 - al) * st->ps_ema + al * own->dls;
        st->pa_ema = (1 - al) * st->pa_ema + al * own->along;
        float nm2 = dot(st->m_ema, st->m_ema), lam_s = 0.0f;
        if (nm2 > 0.0f) {
            if (!p->lam_gate) lam = 1.0f;
            else if (p->robust_lam) lam = clampf(st->pa_ema / sqrtf(nm2), 0.0f, 1.0f);
            else lam = clampf(dot(st->p_ema, st->m_ema) / nm2, 0.0f, 1.0f);
        }
        if (st->ms_ema != 0.0f) lam_s = p->lam_gate ? clampf(st->ps_ema / st->ms_ema, 0.0f, 1.0f) : 1.0f;
        for (int i = 0; i < D; i++) a[i] = w * lam * st->m_ema[i];
        a_s = ws * lam_s * st->ms_ema;
        if (p->common_budget) {
            float v[D];
            for (int i = 0; i < D; i++) v[i] = st->C[i] + a[i];
            project_ball(v, (p->B0c + p->Bc * (float)tj) * rho);
            for (int i = 0; i < D; i++) a[i] = v[i] - st->C[i];
            float lim = p->B0cs + p->Bcs * (float)tj;
            a_s = clampf(st->Cs + a_s, -lim, lim) - st->Cs;
        }
    }
    float v[D], r_app[D];
    for (int i = 0; i < D; i++) v[i] = st->R[i] + (own->dmu[i] - a[i]);
    project_ball(v, (p->B0 + p->B * (float)tj) * rho);
    for (int i = 0; i < D; i++) r_app[i] = v[i] - st->R[i];
    float lim = p->B0s + p->Bs * (float)tj;
    float r_s_app = clampf(st->Rs + (own->dls - a_s), -lim, lim) - st->Rs;
    for (int i = 0; i < D; i++) {
        st->C[i] += a[i];
        st->R[i] += r_app[i];
        out_dmu[i] = a[i] + r_app[i];
    }
    st->Cs += a_s; st->Rs += r_s_app;
    *out_dls = a_s + r_s_app;
    st->lam = lam; st->w = w;
}

/* ------------------------------------------------------------------ gossip frames */
static void put_u16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static void put_u32(uint8_t *p, uint32_t v) { for (int i = 0; i < 4; i++) p[i] = (uint8_t)(v >> (8 * i)); }
static uint32_t get_u32(const uint8_t *p) { return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24); }
static void put_f32(uint8_t *p, float f) { uint32_t u; memcpy(&u, &f, 4); put_u32(p, u); }
static float get_f32(const uint8_t *p) { uint32_t u = get_u32(p); float f; memcpy(&f, &u, 4); return f; }

#define BODY (FOA_FRAME_BYTES - FOA_TAG_BYTES)

void foa_frame_pack(uint8_t frame[FOA_FRAME_BYTES], uint8_t sender, uint32_t cycle, const float *dmu, float dls,
                    uint16_t n_core, const uint8_t key[32]) {
    uint8_t mac[32];
    frame[0] = FOA_FRAME_VERSION;
    frame[1] = sender;
    put_u16(frame + 2, n_core);
    put_u32(frame + 4, cycle);
    for (int i = 0; i < D; i++) put_f32(frame + 8 + 4 * i, dmu[i]);
    put_f32(frame + 8 + 4 * D, dls);
    foa_hmac_sha256(key, 32, frame, BODY, mac);
    memcpy(frame + BODY, mac, FOA_TAG_BYTES);
}

uint8_t foa_frame_sender(const uint8_t *frame) { return frame[1]; }

int foa_frame_verify(const uint8_t *frame, size_t len, const uint8_t key[32], uint32_t cycle,
                     float *dmu, float *dls, uint16_t *n_core) {
    uint8_t mac[32], diff = 0;
    if (len != FOA_FRAME_BYTES) return FOA_ERR_LEN;
    if (frame[0] != FOA_FRAME_VERSION) return FOA_ERR_VERSION;
    foa_hmac_sha256(key, 32, frame, BODY, mac);
    for (int i = 0; i < FOA_TAG_BYTES; i++) diff |= (uint8_t)(mac[i] ^ frame[BODY + i]);   /* constant time */
    if (diff) return FOA_ERR_TAG;
    if (get_u32(frame + 4) != cycle) return FOA_ERR_STALE;
    for (int i = 0; i < D; i++) dmu[i] = get_f32(frame + 8 + 4 * i);
    *dls = get_f32(frame + 8 + 4 * D);
    *n_core = (uint16_t)(frame[2] | (frame[3] << 8));
    return FOA_OK;
}
