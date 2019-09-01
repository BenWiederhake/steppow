/* Any short string you like.  Used as a prefix to the hash. */
#define SPOW_PREFIX "Frobnicate\0"

/* The difficulty of a single step.  Keep it low enough that
 * parallelizing a single step is not really advantagenous. */
#define SPOW_DIFFICULTY 12

/* Extra margin for the nonce.  Too low might make the PoW accidentally
 * impossible.  Too high makes the certificate too long. */
#define SPOW_SAFETY 7

/* How many steps are necessary for a successful Proof of Work. */
#define SPOW_STEPS 128

/* See the Python code for all the implications.  In fact, just run it!
 * Or see the README.md for recommended values. */
