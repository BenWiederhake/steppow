/* Compile:
 * clang -Wall -O3 -march=native src/prove.c -lgcrypt -o bin/prove
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
#include <string.h> /* memcpy / memmove */

#define PORTABLE_ENDIAN_NO_UINT_16_T

#include "prove-config.h"
#include "portable-endian.h"

/* I don't think this will ever change.  But just in case.
 * However, you may want to choose a hash which has block size at least
 * SPOW_HASHBYTES + 1 + 8, because then it probably fits in a block. */
#define SPOW_HASHALGO GCRY_MD_SHA256

/* Policy: Don't trust the macros defined in prove-config.h,
 * but *do* trust the macros defined here. */
#define SPOW_MD_SIZE (256 / 8)
#define SPOW_NONCELEN ((SPOW_DIFFICULTY) + (SPOW_SAFETY))
#define SPOW_CERTBYTES (((SPOW_STEPS) * SPOW_NONCELEN + 7) / 8)
/* "1UL << SPOW_NONCELEN" fails when the sum is 64. */
#define SPOW_MAXNONCE ((1UL << (SPOW_DIFFICULTY) << (SPOW_SAFETY)) - 1)
#define SPOW_DIFFICULTY_MASK (((1UL << (SPOW_DIFFICULTY)) - 1) << (32 - (SPOW_DIFFICULTY)))

/* hashbuf = last_hash || nonce || token || step */
#define SPOW_H_LAST_HASH_OFF 0
#define SPOW_H_LAST_HASH_LEN SPOW_MD_SIZE
#define SPOW_H_NONCE_OFF (SPOW_H_LAST_HASH_OFF + SPOW_H_LAST_HASH_LEN)
#define SPOW_H_NONCE_LEN 8
#define SPOW_H_TOKEN_OFF (SPOW_H_NONCE_OFF + SPOW_H_NONCE_LEN)
#define SPOW_H_TOKEN_LEN 8
#define SPOW_H_STEP_OFF (SPOW_H_TOKEN_OFF + SPOW_H_TOKEN_LEN)
#define SPOW_H_STEP_LEN 4
#define SPOW_HASHBYTES (SPOW_H_STEP_OFF + SPOW_H_STEP_LEN)
#define SPOW_H_NONCE_OFF_U64 (SPOW_H_NONCE_OFF / 8)

typedef char assert_SPOW_INITHASH_length[
    (sizeof(SPOW_INITHASH) == (SPOW_MD_SIZE + 1)) ? 1 : -1];
typedef char assert_nonce_fits[
    (SPOW_NONCELEN <= 64) ? 1 : -1];
typedef char assert_SPOW_HOFF_U64_consistency[
    (SPOW_H_NONCE_OFF_U64 * 8 == SPOW_H_NONCE_OFF) ? 1 : -1];
typedef char assert_SPOW_HBYTES_consistency[
    (SPOW_HASHBYTES == SPOW_H_LAST_HASH_LEN + SPOW_H_STEP_LEN + SPOW_H_TOKEN_LEN + SPOW_H_NONCE_LEN) ? 1 : -1];
typedef char assert_SPOW_DIFFICULTY_limit[
    (((SPOW_DIFFICULTY) <= 32) ? 1 : -1];

static void dump_bytes(unsigned char *buf, size_t num_bytes) {
    for (size_t i = 0; i < num_bytes; ++i) {
        printf("\\x%02X", buf[i]);
    }
}

static size_t extend_cert(unsigned char *cert, uint32_t step, unsigned char *last_hash, const unsigned char *token) {
    /* Check alignment: */
    assert((((intptr_t)last_hash) & 0x3) == 0);
    /* Check whether it fits in one block.  This is not a requirement,
     * but why would you need such a high Difficulty/Safety? */
    assert(SPOW_HASHBYTES <= 55);
    /* TODO: This implementation can't handle too large nonces: */
    assert(SPOW_NONCELEN <= 57);

    /* hashbuf = last_hash || nonce || token || step*/
    unsigned char hashbuf[SPOW_HASHBYTES] = "";
    memmove(hashbuf + SPOW_H_LAST_HASH_OFF, last_hash, SPOW_H_LAST_HASH_LEN);
    /* Skip nonce for now. */
    memmove(hashbuf + SPOW_H_TOKEN_OFF, token, SPOW_H_TOKEN_LEN);
    const uint32_t step_be = pe_htobe32(step);
    memmove(hashbuf + SPOW_H_STEP_OFF, &step_be, SPOW_H_STEP_LEN);

    uint64_t *u64_hashbuf = (uint64_t *)hashbuf;
    uint64_t nonce = 0;
    const uint32_t difficulty_mask = pe_htobe32(SPOW_DIFFICULTY_MASK);
    for (; ; ++nonce) {
        /* Write nonce. */
        u64_hashbuf[SPOW_H_NONCE_OFF_U64] = pe_htobe64(nonce);
        /* Compute digest */
        /* We use u64_hashbuf so that the compiler definitely sees the
         * read *and* writes on it, even when it assumes
         * strict non-aliasing (which we violate). */
        gcry_md_hash_buffer(SPOW_HASHALGO, last_hash,
            (unsigned char *)u64_hashbuf, SPOW_HASHBYTES);
        /* Are we done yet? */
        uint32_t relevant_digest = ((uint32_t *)last_hash)[0] & difficulty_mask;
        if (relevant_digest == 0) {
            /* All required-zero bits are zero: */
            break;
        }
        if (nonce == SPOW_MAXNONCE) {
            /* The impossible happened: Backtracking needed, but not implemented.
             * See README.md, topics "Safety" and "Recommendations". */
            return 0;
        }
    }

    const uint32_t fixed_bits = SPOW_NONCELEN * step;
    const uint64_t aligned_nonce = nonce << (64 - (SPOW_NONCELEN + fixed_bits % 8));
    /* bit machine-i goes into byte machine-(i//8) */
    const uint32_t first_touched_byte = (fixed_bits) / 8;
    const uint32_t last_touched_byte = (fixed_bits + SPOW_NONCELEN - 1) / 8;
    const uint32_t touch_bytes = last_touched_byte - first_touched_byte + 1;
    assert(touch_bytes * 8 <= SPOW_NONCELEN + 14);
    assert(touch_bytes >= (SPOW_NONCELEN + 7) / 8);
    assert(touch_bytes == (SPOW_NONCELEN + fixed_bits % 8 + 7) / 8);
    assert(touch_bytes <= 8);
    for (uint32_t i = 0; i < touch_bytes; ++i) {
        cert[first_touched_byte + i] |= (aligned_nonce >> (64 - (i + 1) * 8)) & 0xFF;
    }

    return nonce + 1;
}

int main() {
    /* Provide space for safe overwriting. */
    unsigned char certificate[SPOW_CERTBYTES + 7] = "";
    const unsigned char token[8] = SPOW_TOKEN;
    unsigned char last_hash[SPOW_MD_SIZE] = SPOW_INITHASH;
    size_t hashes = 0;
    for (uint32_t step = 0; step < (SPOW_STEPS); ++step) {
        size_t step_hashes = extend_cert(certificate, step, last_hash, token);

        if (step_hashes == 0) {
            printf("Failed in step %u, would need to backtrack!\n", step);
            /* However, this is sufficiently unlikely.
             * See README.md, topics "Safety" and "Recommendations". */
            return 1;
        }
        /* Theoretically you can overflow here.
         * Practically, this costs 2^64 hash computations. See you in 2080. */
        hashes += step_hashes;
    }
    printf("Certificate found after %lu hashes:\n", hashes);
    dump_bytes(certificate, SPOW_CERTBYTES);
    printf("\n");
    return 0;
}
