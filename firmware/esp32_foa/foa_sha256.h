/* Minimal SHA-256 and HMAC-SHA256 (FIPS 180-4, RFC 2104). Portable C99, no heap. */
#ifndef FOA_SHA256_H
#define FOA_SHA256_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint32_t h[8];
    uint64_t len;
    uint8_t buf[64];
    size_t n;
} foa_sha256_t;

void foa_sha256_init(foa_sha256_t *c);
void foa_sha256_update(foa_sha256_t *c, const uint8_t *data, size_t len);
void foa_sha256_final(foa_sha256_t *c, uint8_t out[32]);
void foa_hmac_sha256(const uint8_t *key, size_t key_len, const uint8_t *msg, size_t msg_len, uint8_t out[32]);

#ifdef __cplusplus
}
#endif
#endif
