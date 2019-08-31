/* This file is included by C and parsed by python.
 * Hence, the #define's must stringtly follow the format:
 * '#define ' VARNAME ' ' NUMBER
 * with no leading or trailing whitespace. */

/* Any string you like, but keep it short.
 * Used as a prefix to the hash.  Use `\xff` notation. */
#define SPOW_DOMAIN ""

/* The difficulty of a single step.  Keep it low enough that
 * parallelizing a single step is not really advantagenous. */
#define SPOW_DIFFICULTY 7

/* Extra margin for the nonce.  Too low might make the PoW accidentally
 * impossible.  Too high makes the certificate too long. */
#define SPOW_SAFETY 7

/* How many steps are necessary for a successful Proof of Work. */
#define SPOW_STEPS 800

/* See the Python code for all the implications.  In fact, just run it! */
