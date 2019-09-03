/*
 * portable-endian.h, a truly portable header-only library about endianness
 * Copyright (c) 2016 Ben Wiederhake
 * The MIT License (MIT)
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 * -----
 *
 * The old problem: "performance, portability, readability; choose two."
 * This header tries to achieve universal portability and readability.
 * The trick is to *ignore* the actual machine's endianness.
 * There is no configuration, no macro-flags, no magic going on.
 * It should "just work".
 *
 * Sufficiently advanced compilers should be able to optimize these functions
 * down to no-ops and byteswaps:
 * https://godbolt.org/z/Fs9-c4
 * Even if not: the code is branch-free and operates only on the stack,
 * without reading a global or something.
 *
 * As this library has no includes other than stdint.h, it is extremely
 * portable.  Managing which platform/compiler/environment defines which
 * macros in which files is a mess:
 * https://github.com/BenWiederhake/portable-endian.h/blob/0ff2b6574b56bb08efcf01311f22c177b744da1d/portable_endian.h
 * This library does without, and might even work on a potato.
 *
 * Finally, readability: Apart from a bit of macro-noise for customizability,
 * there is nothing fancy going on.  Each function writes chars and reads some
 * uintX_t, or writes a uintX_t and reads some chars.  That's it.
 * It doesn't get more readable than that.
 *
 * In case you have a weird system that doesn't support some of the
 * types uint16_t, uint32_t, or uint64_t, just define the appropriate guard.
 * For example if there's no uint64_t, or you want to skip those functions:
 *   #define PORTABLE_ENDIAN_NO_UINT_64_T
 *
 * In case you have a *really* weird system where the compiler doesn't know how
 * to inline a function that's nothing but a bitshifts and ORs (no branches!),
 * try putting "static inline" in front of a function with the macro
 * PORTABLE_ENDIAN_MODIFIERS (except on C89):
 *   #define PORTABLE_ENDIAN_MODIFIERS static inline
 *
 * In case you have a *seriously* weird system where the above trick doesn't
 * quite work or doesn't get properly inlined, write the following in
 * exactly *one* compilation unit:
 *   #define PORTABLE_ENDIAN_MODIFIERS / * nothing * /
 * and in all other compilation units:
 *   #define PORTABLE_ENDIAN_MODIFIERS extern
 *   #define PORTABLE_ENDIAN_DECLS_ONLY
 * This way, portable-endian behaves mostly as if it's a library against which
 * you statically link, without the hassle of having to deal with any
 * compilation flags.
 */

#ifndef PORTABLE_ENDIAN_PORTABLE_ENDIAN_H_
#define PORTABLE_ENDIAN_PORTABLE_ENDIAN_H_

#include <stdint.h>



/* To differentiate this from different forks, this is the specific flavor of
 * the project. Please *do* change this string when forking.
 * The original flavor "VIPERS_BEGAN_HOBBLE" is hosted here:
 * https://github.com/BenWiederhake/portable-endian/
 * The words were chosen by randomly picking from the dictionary.
 * I never actually observed that vipers began to hobble. */
#define PORTABLE_ENDIAN_FLAVOR "VIPERS_BEGAN_HOBBLE"

#ifndef PORTABLE_ENDIAN_MODIFIERS
#define PORTABLE_ENDIAN_MODIFIERS static
#endif /* PORTABLE_ENDIAN_MODIFIERS */



#ifndef PORTABLE_ENDIAN_NO_UINT_16_T
PORTABLE_ENDIAN_MODIFIERS uint16_t pe_be16toh(uint16_t v);
PORTABLE_ENDIAN_MODIFIERS uint16_t pe_htobe16(uint16_t v);
PORTABLE_ENDIAN_MODIFIERS uint16_t pe_le16toh(uint16_t v);
PORTABLE_ENDIAN_MODIFIERS uint16_t pe_htole16(uint16_t v);
typedef char portable_endian_u16_check[sizeof(uint16_t) == (16/8) ? 1 : -1];
#ifndef PORTABLE_ENDIAN_DECLS_ONLY
union portable_endian_u16_union {
    uint16_t as_uint;
    unsigned char as_chars[sizeof(uint16_t)];
};
PORTABLE_ENDIAN_MODIFIERS uint16_t pe_be16toh(uint16_t v) {
    union portable_endian_u16_union u;
    (void)pe_htole16; /* Avoid "unused function" warnings */
    u.as_uint = v;
    /* No matter *what* is being shifted, it is first promoted to int.
     * http://stackoverflow.com/a/11203159/3070326
     * This means that (((uint16_t)u.as_chars[0]) << 8) might be of type int,
     * so the overall value might be of type int, which might be longer than
     * uint16_t, resulting in loss of precision.
     * This is visible with "clang -Weverything". */
    return (uint16_t)(
              (((uint16_t)u.as_chars[0]) << 8)
            | (((uint16_t)u.as_chars[1]) << 0)
            );
}
PORTABLE_ENDIAN_MODIFIERS uint16_t pe_htobe16(uint16_t v) {
    /* Note that htons and ntohs are the same because, mathematically speaking,
     * it holds for every permutation p of two elements that (p \concat p) = id.
     * For readability we do not exploit this here, since it doesn't hold for
     * 32- and 64-bit values anyway. */
    union portable_endian_u16_union u;
    (void)pe_be16toh; /* Avoid "unused function" warnings */
    u.as_chars[0] = (unsigned char)(v >> 8);
    u.as_chars[1] = (unsigned char)(v >> 0);
    return u.as_uint;
}
PORTABLE_ENDIAN_MODIFIERS uint16_t pe_le16toh(uint16_t v) {
    union portable_endian_u16_union u;
    (void)pe_htobe16; /* Avoid "unused function" warnings */
    u.as_uint = v;
    return (uint16_t)(
              (((uint16_t)u.as_chars[1]) << 8)
            | (((uint16_t)u.as_chars[0]) << 0)
            );
}
PORTABLE_ENDIAN_MODIFIERS uint16_t pe_htole16(uint16_t v) {
    union portable_endian_u16_union u;
    (void)pe_le16toh; /* Avoid "unused function" warnings */
    u.as_chars[1] = (unsigned char)(v >> 8);
    u.as_chars[0] = (unsigned char)(v >> 0);
    return u.as_uint;
}
#endif /* PORTABLE_ENDIAN_DECLS_ONLY */
#endif /* PORTABLE_ENDIAN_NO_UINT_16_T */



#ifndef PORTABLE_ENDIAN_NO_UINT_32_T
PORTABLE_ENDIAN_MODIFIERS uint32_t pe_be32toh(uint32_t v);
PORTABLE_ENDIAN_MODIFIERS uint32_t pe_htobe32(uint32_t v);
PORTABLE_ENDIAN_MODIFIERS uint32_t pe_le32toh(uint32_t v);
PORTABLE_ENDIAN_MODIFIERS uint32_t pe_htole32(uint32_t v);
typedef char portable_endian_u32_check[sizeof(uint32_t) == (32/8) ? 1 : -1];
#ifndef PORTABLE_ENDIAN_DECLS_ONLY
union portable_endian_u32_union {
    uint32_t as_uint;
    unsigned char as_chars[sizeof(uint32_t)];
};
PORTABLE_ENDIAN_MODIFIERS uint32_t pe_be32toh(uint32_t v) {
    union portable_endian_u32_union u;
    (void)pe_htole32; /* Avoid "unused function" warnings */
    u.as_uint = v;
    return (uint32_t)(
              (((uint32_t)u.as_chars[0]) << 24)
            | (((uint32_t)u.as_chars[1]) << 16)
            | (((uint32_t)u.as_chars[2]) << 8)
            | (((uint32_t)u.as_chars[3]) << 0)
            );
}
PORTABLE_ENDIAN_MODIFIERS uint32_t pe_htobe32(uint32_t v) {
    union portable_endian_u32_union u;
    (void)pe_be32toh; /* Avoid "unused function" warnings */
    u.as_chars[0] = (unsigned char)(v >> 24);
    u.as_chars[1] = (unsigned char)(v >> 16);
    u.as_chars[2] = (unsigned char)(v >> 8);
    u.as_chars[3] = (unsigned char)(v >> 0);
    return u.as_uint;
}
PORTABLE_ENDIAN_MODIFIERS uint32_t pe_le32toh(uint32_t v) {
    union portable_endian_u32_union u;
    (void)pe_htobe32; /* Avoid "unused function" warnings */
    u.as_uint = v;
    return (uint32_t)(
              (((uint32_t)u.as_chars[3]) << 24)
            | (((uint32_t)u.as_chars[2]) << 16)
            | (((uint32_t)u.as_chars[1]) << 8)
            | (((uint32_t)u.as_chars[0]) << 0)
            );
}
PORTABLE_ENDIAN_MODIFIERS uint32_t pe_htole32(uint32_t v) {
    union portable_endian_u32_union u;
    (void)pe_le32toh; /* Avoid "unused function" warnings */
    u.as_chars[3] = (unsigned char)(v >> 24);
    u.as_chars[2] = (unsigned char)(v >> 16);
    u.as_chars[1] = (unsigned char)(v >> 8);
    u.as_chars[0] = (unsigned char)(v >> 0);
    return u.as_uint;
}
#endif /* PORTABLE_ENDIAN_DECLS_ONLY */
#endif /* PORTABLE_ENDIAN_NO_UINT_32_T */



#ifndef PORTABLE_ENDIAN_NO_UINT_64_T
PORTABLE_ENDIAN_MODIFIERS uint64_t pe_be64toh(uint64_t v);
PORTABLE_ENDIAN_MODIFIERS uint64_t pe_htobe64(uint64_t v);
PORTABLE_ENDIAN_MODIFIERS uint64_t pe_le64toh(uint64_t v);
PORTABLE_ENDIAN_MODIFIERS uint64_t pe_htole64(uint64_t v);
typedef char portable_endian_u64_check[sizeof(uint64_t) == (64/8) ? 1 : -1];
#ifndef PORTABLE_ENDIAN_DECLS_ONLY
union portable_endian_u64_union {
    uint64_t as_uint;
    unsigned char as_chars[sizeof(uint64_t)];
};
PORTABLE_ENDIAN_MODIFIERS uint64_t pe_be64toh(uint64_t v) {
    union portable_endian_u64_union u;
    (void)pe_htole64; /* Avoid "unused function" warnings */
    u.as_uint = v;
    return (uint64_t)(
              (((uint64_t)u.as_chars[0]) << 56)
            | (((uint64_t)u.as_chars[1]) << 48)
            | (((uint64_t)u.as_chars[2]) << 40)
            | (((uint64_t)u.as_chars[3]) << 32)
            | (((uint64_t)u.as_chars[4]) << 24)
            | (((uint64_t)u.as_chars[5]) << 16)
            | (((uint64_t)u.as_chars[6]) << 8)
            | (((uint64_t)u.as_chars[7]) << 0)
            );
}
PORTABLE_ENDIAN_MODIFIERS uint64_t pe_htobe64(uint64_t v) {
    /* Note that htons and ntohs are the same because, mathematically speaking,
     * it holds for every permutation p of two elements that p \concat p is the
     * identity.
     * For readability we do not exploit this here, since it doesn't hold for
     * 64-bit values anyway. */
    union portable_endian_u64_union u;
    (void)pe_be64toh; /* Avoid "unused function" warnings */
    u.as_chars[0] = (unsigned char)(v >> 56);
    u.as_chars[1] = (unsigned char)(v >> 48);
    u.as_chars[2] = (unsigned char)(v >> 40);
    u.as_chars[3] = (unsigned char)(v >> 32);
    u.as_chars[4] = (unsigned char)(v >> 24);
    u.as_chars[5] = (unsigned char)(v >> 16);
    u.as_chars[6] = (unsigned char)(v >> 8);
    u.as_chars[7] = (unsigned char)(v >> 0);
    return u.as_uint;
}
PORTABLE_ENDIAN_MODIFIERS uint64_t pe_le64toh(uint64_t v) {
    union portable_endian_u64_union u;
    (void)pe_htobe64; /* Avoid "unused function" warnings */
    u.as_uint = v;
    return (uint64_t)(
              (((uint64_t)u.as_chars[7]) << 56)
            | (((uint64_t)u.as_chars[6]) << 48)
            | (((uint64_t)u.as_chars[5]) << 40)
            | (((uint64_t)u.as_chars[4]) << 32)
            | (((uint64_t)u.as_chars[3]) << 24)
            | (((uint64_t)u.as_chars[2]) << 16)
            | (((uint64_t)u.as_chars[1]) << 8)
            | (((uint64_t)u.as_chars[0]) << 0)
            );
}
PORTABLE_ENDIAN_MODIFIERS uint64_t pe_htole64(uint64_t v) {
    union portable_endian_u64_union u;
    (void)pe_le64toh; /* Avoid "unused function" warnings */
    u.as_chars[7] = (unsigned char)(v >> 56);
    u.as_chars[6] = (unsigned char)(v >> 48);
    u.as_chars[5] = (unsigned char)(v >> 40);
    u.as_chars[4] = (unsigned char)(v >> 32);
    u.as_chars[3] = (unsigned char)(v >> 24);
    u.as_chars[2] = (unsigned char)(v >> 16);
    u.as_chars[1] = (unsigned char)(v >> 8);
    u.as_chars[0] = (unsigned char)(v >> 0);
    return u.as_uint;
}
#endif /* PORTABLE_ENDIAN_DECLS_ONLY */
#endif /* PORTABLE_ENDIAN_NO_UINT_64_T */



#endif /* PORTABLE_ENDIAN_PORTABLE_ENDIAN_H_ */
