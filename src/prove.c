/* Compile:
 * clang -Weverything -O3 -march=native src/prove.c -lgcrypt -o bin/prove
 * Run:
 * ./bin/prove
 * Yay. */

/* Marginally speed up compilation */
#define GCRYPT_NO_MPI_MACROS
/* Fail-fast when something becomes deprecated. */
#define GCRYPT_NO_DEPRECATED

#include <assert.h>
#include <gcrypt.h>
#include <stddef.h> /* size_t */
#include <stdint.h>
#include <stdio.h>

#define PORTABLE_ENDIAN_NO_UINT_16_T

#include "config.h"
#include "portable-endian.h"

#define SPOW_CERTBYTES ((SPOW_STEPS * (SPOW_DIFFICULTY + SPOW_SAFETY) + 7) / 8)
#define SPOW_MSGBYTES (SPOW_CERTBYTES + sizeof(SPOW_PREFIX) - 1)
#define SPOW_MAXNONCE ((1UL << (SPOW_DIFFICULTY + SPOW_SAFETY)) - 1)
#define SPOW_DIFFICULTY_MASK (((1UL << SPOW_DIFFICULTY) - 1) << (32 - SPOW_DIFFICULTY))

#define SPOW_HASH GCRY_MD_SHA256
#define SPOW_MD_SIZE (256 / 8)

static void dump_bytes(unsigned char *buf, size_t num_bytes) {
    for (size_t i = 0; i < num_bytes; ++i) {
        printf("\\x%02X", buf[i]);
    }
}

static size_t extend_buffer(unsigned char *buf, size_t fixed_bits) {
    /* Check alignment: */
    assert((((intptr_t)buf) & 0x7) == 0);
    /* Check whether the nonce is always fully captured by a window of two u32s: */
    assert(SPOW_DIFFICULTY + SPOW_SAFETY <= 33);

    const uint32_t difficulty_mask = pe_htobe32(SPOW_DIFFICULTY_MASK);

    unsigned char digest[SPOW_MD_SIZE];
    const size_t new_fixed_bits = fixed_bits + SPOW_DIFFICULTY + SPOW_SAFETY;
    const size_t new_fixed_bytes = (new_fixed_bits + 7) / 8;

    /* Yes, it is aligned, the caller had to make sure, and we also checked it. */
    uint32_t *u32_buf = (uint32_t *)buf;
    uint32_t *u32_digest = (uint32_t *)digest;

    const int nonce_mask_shift = 64 - (SPOW_DIFFICULTY + SPOW_SAFETY) - (fixed_bits % 32);
    const uint32_t nonce_mask_l = pe_htobe32((SPOW_MAXNONCE << nonce_mask_shift) >> 32);
    const uint32_t nonce_mask_r = pe_htobe32((SPOW_MAXNONCE << nonce_mask_shift) & 0xFFFFFFFF);
    const size_t nonce_index_start = fixed_bits / 32;
    /* printf("%4lu fixed, start at #%3lu, nonce shift %2d, orig nonce mask is 0x%016lX, partials are now 0x%08X and 0x%08X\n",
        fixed_bits, nonce_index_start, nonce_mask_shift, SPOW_MAXNONCE << nonce_mask_shift, nonce_mask_l, nonce_mask_r); */
    for (uint64_t nonce = 42; nonce <= SPOW_MAXNONCE; ++nonce) {
        /* Clear old nonce */
        u32_buf[nonce_index_start] &= ~nonce_mask_l;
        u32_buf[nonce_index_start + 1] &= ~nonce_mask_r;
        /* Write nonce */
        const uint32_t write_l = pe_htobe32((nonce << nonce_mask_shift) >> 32);
        const uint32_t write_r = pe_htobe32((nonce << nonce_mask_shift) & 0xFFFFFFFF);
        u32_buf[nonce_index_start] |= write_l;
        u32_buf[nonce_index_start + 1] |= write_r;
        /* Compute digest */
        gcry_md_hash_buffer(SPOW_HASH, digest, buf, new_fixed_bytes);
        /* Are we done yet? */
        uint32_t relevant_digest = u32_digest[0] & difficulty_mask;
        if (relevant_digest == 0) {
            /* All required-zero bits are zero: */
            return nonce + 1;
        }
    }
    return 0;
}

int main() {
    /* Additional 4-1 bytes for overshoot accesses. */
    unsigned char message[SPOW_MSGBYTES + 3] = SPOW_PREFIX;
    size_t hashes = 0;
    for (size_t i = 0; i < SPOW_STEPS; ++i) {
        size_t fixed_bits = (sizeof(SPOW_PREFIX) - 1) * 8 + (SPOW_DIFFICULTY + SPOW_SAFETY) * i;
        size_t i_hashes = extend_buffer(message, fixed_bits);
        if (i_hashes == 0) {
            printf("Failed in step %lu, would need to backtrack!\n", i);
            // However, this is sufficiently unlikely.
            return 1;
        }
        hashes += i_hashes;
    }
    printf("Certificate found after %lu hashes.  Suffix is:\n", hashes);
    dump_bytes(message + sizeof(SPOW_PREFIX) - 1, SPOW_MSGBYTES - sizeof(SPOW_PREFIX) + 1);
    printf("\n");
    return 0;
}
