/* Any 32 bytes you like, including the NUL byte.
 * You could use a hash here. */
#define SPOW_INITHASH "\x2c\xa7\xc6\x0f\x3a\x11\xd6\x8b\x10\xe2\xaa\x4d\x49\x8b\x7c\x78\x5f\xf2\xb3\xeb\xe2\xd4\x1a\x94\x32\x1f\x85\x52\x27\x21\x70\x3e"

/* Any 8 bytes you like, including the NUL byte.
 * You could use the first 8 bytes of SPOW_INITHASH here. */
#define SPOW_TOKEN "\x3d\x91\x5a\x13\xfd\xc4\x04\xe4"

/* The difficulty of a single step.  Keep it low enough that
 * parallelizing a single step is not really advantagenous. */
#define SPOW_DIFFICULTY 12

/* Extra margin for the nonce.  Too low might make the PoW accidentally
 * impossible.  Too high makes the certificate too long. */
#define SPOW_SAFETY 8

/* How many steps are necessary for a successful Proof of Work. */
#define SPOW_STEPS 128

/* See the Python code for all the implications.  In fact, just run it!
 * Or see the README.md for recommended values. */
