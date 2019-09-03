# steppow

> Simple, Asymmetric Proof of Work

I needed a proof of work system with the following properties:
- Asymmetric
- Easy to implement
- Easy to understand
- No parallelism
- Bonus: Easy way to determine progress
- Bonus: Free Software

Steppow implements all of these aspects as a Proof of Concept.

## Table of Contents

- [Background](#background)
- [Theory](#theory)
- [Install](#install)
- [Usage](#usage)
- [Recommendations](#recommendations)
- [Security](#security)
- [Design Considerations](#design-considerations)
- [Performance](#performance)
- [Alternatives](#alternatives)
- [TODOs](#todos)
- [NOTDOs](#notdos)
- [Contribute](#contribute)

## Background

### The Basic Model

There are two players: The prover and the verifier.  The verifier is in a privileged position.
The prover wants to spend effort on some problem, and then prove this work to the verifier.
There are many systems for doing that, however none had quite the properties I was looking for.

In the following, I will elaborate on what exactly I want from this method.

### Asymmetric

In the above explanation, there was no mention of how much work the verifier has to do.
Some systems don't care about this aspect, and let the verifier just compute the same
thing, and check whether the results are the same.

I want a system in which the verifier has very little work to do;
this is the case for steppow.

### Easy to Implement

No-one likes importing a big blob of code without knowing what it does.
Also, PoW systems inherently occur in environments where different programs are
communicating, usually across hosts, and across languages.

Therefore, it should be sufficiently easy to rewrite the verifier and ideally prover
in the language of your choice.
This is one of the reasons why the heavy lifting is done by the
well-trodden building block SHA256 and nothing fancy.

For comparison: `src/prove.c` only contains roughly 60 lines that actually run the prover.
The rest is comments, setup, and output.
And even that could be reduced further by reducing the code's generality:
Turns out, handling arbitrary bitshifts has an impact on source code
length (and performance, too, I guess).

### Easy to Understand

I don't want to learn about Elliptic Curves or Weaken Fiat–Shamir signatures or how Merkle trees could be used for this.

Instead, steppow uses an old trick in a new flavor:
A hash has to be inverted partially *repeatedly*.

### No Parallelism

Partial hash inversions have been around for a long time.  There seems to
exist a tendency such that over time, the difficulty of such systems increases
to many, many bits.  A high difficulty (requiring many zeros) has disadvantages:
- A single attempt is basically worthless.
- Variance can be really awful.  Sometimes a single attempt solves the entire problem,
  sometimes it takes way more than expected attempts to solve it.
- Buying more hardware could speed up the solving-process.

In steppow, a single attempt still is not worth much (that's the entire point).
However, random variance has bounds:
By construction, the prover would need to guess correct nonces several times in a row.
Likewise, hitting the worst-case only means that *a single step* took more than
typically many hash computations.  As this happens rarely, the total amount of
hash computations is relatively stable.
Also see [Amount of Work](#amount-of-work).

Finally, buying more hardware is not useful for steppow: Computing a certificate
cannot be meaningfully parallelized, as each step depends on the previous.
Computing a step cannot be meaningfully parallelized, because the expected number
of hashes for a single step already is so low that the synchronization overhead
might make it slower.

### Bonus: Easy Way to Determine Progress

A partial hash inversion gives no feedback about progress.  Either the correct
nonce has been found, or it hasn't.

In steppow, the prover can give feedback to the caller that "x/y"
steps have already completed.  This can be used as a progress indicator.

### Bonus: Free Software

And last but not least: You can [run, study, improve and redistribute](https://en.wikipedia.org/wiki/Free_software#Definition_and_the_Four_Freedoms) to your heart's content.

### Name

The name comes from "Stepped Proof-of-Work".

The backronym is "Stepped Transparent Esymmetric Practical Proof of Work"
if you disregard orthography.

## Theory

In some other PoW systems, the prover has to find a partial hash inverse.
The core idea of steppow is to force the prover to sequentially do many
simple partial hash inverses in several steps.

There are four parameters:
- Initial Hash / Token: Arbitrary strings of a fixed short length.
  This binds the PoW certificate to its purpose.
  You could also call it "domain".
- Difficulty: A number indicating the difficulty to make a single "step".
- Safety: A number indicating the safety margin.  Note that this is about *Safety, not Security*.
- Steps: The number of sequential iterations of this PoW system.
  Note that this is not the total number of hashes, but rather
  the number of puzzles (i.e. partial hash inversions).

/* hashbuf = last_hash || nonce || token || step*/

In each step, the prover needs to find a nonce of bitlength Difficulty + Safety
such that `hash(last_hash || nonce || token || num_steps)` begins with Difficulty-many 0 bits.
The operator `||` is concatenation, and `last_hash` is the output hash of the previous round,
or Initial Hash in the first round.

The bits of `nonce` are *left*-padded to fill 8 bytes; as if it was a Big Endian 8-byte integer.
The number `num_steps` is encoded as a Big Endian 4-byte integer.

### Simple Properties

The certificate length is determined by the Difficulty, Safety, and Steps: `Steps * (Difficulty + Safety)`.

The [probability of impossibility](#safety-against-impossibility) is determined
by the Difficulty, Safety, and Steps: `< 2^(log2(Steps) - log2(e) * 2^Safety)`.
Note that for Safety = 7, this means that the probability of impossibility is
less than 2^-170 for any sane value of Steps.
This means that even after 2^80 independent executions of the prover,
the probability of seeing *any* failure is less than 2^-90.

The [expected amount of work](#amount-of-work) for the prover is determined by
the Difficulty and Steps: `Steps * 2^Difficulty`.

The exact amount of work for the verifier is also determined by
the Difficulty and Steps, but is not exponential: `Steps * Difficulty`.
(As usual for partial-hash-inversion-style PoWs.)

The certificate length is determined by the Difficulty, Safety, and Steps:
`steps * (difficulty + safety)` bits.

### Safety Against Impossibility

An ideal cryptographic hash function would be [indistinguishable
from a random function](https://en.wikipedia.org/wiki/Random_oracle),
i.e., a function picked randomly from the space of functions that map arbitrary
binary strings to fixed-length binary strings.

This section shows that under this (Random oracle) assumption, the probability
of the prover needing to backtrack is negligible.

Let's look at a single step executed by the prover:
The probability that a specific nonce leads to a satisficing hash is `2^-Difficulty`.
Hence the probability that there is no such nonce is `(1 - 2^-Difficulty)^(2^(Difficulty+Safety))`
[`=`](https://en.wikipedia.org/wiki/E_(mathematical_constant)#Inequalities)
`e^-(2^Safety)`.  Note that this is a double exponential, and goes rapidly to 0.

The probability of the prover needing to backtrack can therefore be
[upperbounded by](https://en.wikipedia.org/wiki/Boole%27s_inequality)
`e^-(2^Safety) * Steps`, i.e., practically never.

### Amount of Work

The amount of work for the prover is determined by the number of hashes that
need to be computed.  That's why steppow measures work
in terms of hash computations.

If the prover follows the algorithm (i.e., repeatedly guess nonces),
then the number of hashes follows the
[Erlang (k=Steps, lambda=2^-Difficulty) distribution](https://en.wikipedia.org/wiki/Erlang_distribution).

This means that the expected number of hash computations is `Steps * 2^Difficulty`.
The median number of hash computations is negligibly smaller than that.

TODO: Figure out bounds on the tail.  Specifically, what are the 0.1%, 1%, 10%,
90%, 99%, and 99.9% quantiles of the number of hash computations?

## Install

This is only a Proof of Concept thing.  First I want to get feedback on
whether this is actually a good idea, and maybe fix other issues,
before I implement it in a variety of languages.

This is why steppow cannot be installed yet, in any way.

The dependencies of steppow are simple:
- The python implementation of `verify` needs python3 (duh).
- The C implementation of `prove` needs a C compiler (at least clang and gcc work),
  and gcrypt (package name on Debian: `libgcrypt20-dev`).

## Usage

### Prover

The prover is not meant to be used in a dynamic fashion.
However, it should be straight-forward to replace the dependencies
on macros by variables in this particular implementation.

The way to run it is by changing values in `src/prove-config.h`, recompiling and running it.
The comment at the top of `src/prove.c` tells you how:
`clang -O3 -march=native src/prove.c -lgcrypt -o bin/prove`

The output looks something like this:

```
Certificate found after 521318 hashes:
\x02\xBA\xF0\x18\x27\x02\xC3\xA0\x0E\x7B\x00\x22\x00\x02\x7B\x00\x12\x80\x38\x16\x00\xB2\xC0\x0C\xD1\x00\xCD\x60\x03\x2B\x00\x8D\xC0\x0E\x37\x00\x4D\xF0\x15\xE2\x01\x6E\x50\x0F\x62\x02\xA8\x80\x2B\xE2\x00\x20\xD0\x14\x26\x00\x4B\x50\x2F\xD2\x00\x11\x80\x0D\xD1\x01\x61\x70\x0B\xC2\x01\x17\x20\x04\x24\x00\x26\x90\x0C\x91\x01\x5C\xF0\x07\xF8\x03\x1F\x60\x01\x0C\x00\x5D\xF0\x07\xE4\x00\x0A\x30\x00\x18\x00\x4B\x80\x16\x6E\x00\x72\x50\x06\xC0\x01\x14\xA0\x03\x19\x02\xC9\xE0\x07\x76\x01\x79\x90\x03\x29\x00\x59\x90\x0E\xD5\x03\x5F\x60\x12\xED\x03\x31\x00\x00\xE3\x00\xC9\xB0\x41\x78\x00\xFC\x40\x21\x05\x00\xA7\x70\x00\x17\x01\x43\x40\x09\x1D\x02\xF7\x20\x12\x8A\x00\x53\x50\x05\xB6\x01\xA3\x00\x22\x03\x00\xCF\xB0\x01\xB2\x00\xDC\xB0\x23\x11\x00\x69\xC0\x0E\x4C\x00\x51\xB0\x0B\x4B\x01\xC6\x40\x0C\x68\x02\x17\x60\x00\xA2\x00\x65\x70\x00\xF1\x00\x95\x90\x0F\x0B\x00\x63\x20\x03\x8C\x00\x2A\x00\x06\x31\x02\xA0\xB0\x28\x14\x00\xAC\xC0\x09\x0B\x00\x33\xA0\x14\xE9\x00\xBA\x60\x04\xB3\x00\x15\xB0\x04\x4E\x00\x53\x50\x18\x45\x00\x3A\xA0\x24\xC9\x00\x11\x40\x14\xFF\x01\x22\x40\x1C\x12\x00\x2B\xA0\x0B\x57\x00\x19\xA0\x08\xB1\x02\x2A\xF0\x0A\x02\x00\x46\xD0\x14\xD5\x01\x14\x80\x12\xA7\x01\x2C\x10\x11\x57\x00\xB2\x80\x04\x19\x01\x02\x00\x0C\x7B\x00\xD5\xA0\x22\x26\x00\xAE\x30\x07\x73
```

This tells you two things:
1. It took 521318 hash-computations to find the solution.  This is a very rough measure of raw computational power sunk into the PoW.
2. The weird blob of data is the certificate.  In the context of the parameters, this proves that my machine computed about [Steps * 2^Difficulty](#amount-of-work) many hashes only for this.

This output, together with the parameters, can be copied into `src/verify.py`
to verify the certificate.

### Verifier

The verifier could in theory be already used as-is for production work.
(However, it hasn't been battle-tested yet, and the tests in `TEST_CERTS` are
basically all the tests I ran so far.)
The function `try_verify(init_hash, token, difficulty, safety, steps, certificate)`
checks whether a given blob is a valid
certificate for a given set of parameters.

You can also run `verify.py` as a stand-alone executable.
Then it runs a few self-tests, with everything I deemed possibly relevant.

Here's how the typical output looks like:

```
========================================
Checking cert #4 (58 bytes)
Initial hash: b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
Token: b'\x00\x00\x00\x00\x00\x00\x00\x00'
Difficulty: 7
Safety: 7
Steps: 33
--------------------
Bits per step: 14
Probability of impossibility: < 2^(-122.95560588064154)
E[num hashes]: 4224
Actual num hashes: 3061
Certificate byte length: 58
--------------------
Valid: True
Matches expectation: True
```

The first section is just a copy of the parameters, and an indication which entry
the verifier is currently looking at.
The second part is mostly determined by the parameters alone, and shows the
actual hash amount ("effort") for comparison.
As you can see, the actual number of hashes is close enough to the expected
number of hashes.
The third part checks whether the blob (not printed) is a valid certificate,
which errors were encountered, and whether this matches our expectation.
This way we can easily check that good certificates are accepted,
and bad certificates are not.

For easier inspection, you can find the output of `src/verify.py` in `src/verify.py.out`.

## Recommendations

The Safety number only has an influence on provability, and a minor influence on the certificate size.
Hence I recommend a Safety number of 7, as it gives an extremely small probability of impossibility (around 2^-118),
but does not bloat the certificate size.

This leaves the two other parameters Difficulty and Stepcount:

    Profile   Difficulty   Stepcount   Expected Total Work (KH)   Certificate Size (Bytes)
    S               9          200                102,4                      400
    M               9         1000                512                       2000
    L              12(*)      1000               4096                       2375 (2500)
    XL             13         5000              40960                      12500

For comparison: A reasonable upper estimate on the performance of a single core is 3000 KH/s,
a reasonable lower bound seems to be 100 KH/s.
For orientation which certificate sizes are acceptable, I imagined it being sent as binary POST data.
There, everything below 4 KiB seems acceptable to me.

The reason I prefer a Difficulty of 9 is simple: The prover guesses nonces of length
Difficulty + Safety, which in this case is 16 bits.
This aligns nicely with byte boundaries, and makes implementations simpler and maybe faster.

Likewise for Difficulty 13: Then the nonces have the length 20 bits, or exactly 2.5 bytes.
This isn't as nice as 2.0, but is still simpler than a bitlength not divisible by 4.

(*): Difficulty 12 can still be easy to implement:
If one chooses Safety 8, each nonce is exactly 2.5 bytes again,
but the certificate size increases to 2500 bytes.

The Initial Hash and Token could be derived from the same (large)
piece of context struct held by the verifier.
Specifically, the following should work, as HMAC-SHA256 is
just two invocations of SHA256:

    Initial_Hash := HMAC-SHA256(context)
    Token := SHA256(context) [:8]

where `[:8]` is the truncation operation to 8 bytes.
Any other method should be fine, too.
If available, the non-standard `SHA-256/64` function should be considered.

## Security

The software is provided "as is", without warranty of any kind, yadda yadda.

There was no professional security audit on this yet.  I started development on this on 2019-09-01.

Well, at least I haven't broken it yet.  On the other hand, I haven't broken anything yet
(except of course assignments), so my assessment
is [worth squat](https://www.schneier.com/blog/archives/2011/04/schneiers_law.html).

## Design Considerations

For this project I assume that it is hard to find a nonce such that the leading output bits of SHA256 are 0.
This assumption seems to be a safe one, as many other PoW systems build on this.

Furthermore, I assume that changing the first 32 bytes of the hash input has
unpredictable influence over the rest: The nonce has to be computed anew,
and no precomputations or guessing are efficient, unless an exponential
amount of work is sunk into that.

Next, to prevent replay attacks, the Proof of Work certificate needs to be bound
to some kind of argument.  In the case of steppow, I used the initial hash and token for that.

To thwart any attack that tries to confuse step numbers, these are made part of the hash input.
Therefore when computing a step, the algorithm must know the token and step number,
and vice versa: When computing a step, the algorithm has no confusion about which
token and step number it is working on.

The order `last_hash || nonce || token || num_steps` was chosen to make partial precomputation
impossible (i.e., already the first round of SHA256 is likely to read different data in each step).
The number of steps is last, the prevent the same in the other direction as well as possible.

The number of steps is restricted to 2^32, because no-one wants to deal with GiB-sized certificates.

The number of bytes hashed is therefore 52.  This is very much intentional:
SHA256 has a block size of 64 bytes, and it's first action is to pad the input
by at least 9 bytes (technically: "at least 65 bits").
Therefore, I wanted to stay below 55 bytes, to keep it to a single block,
which dampens the advantage of hyper-specialized hardware for SHA rounds.

Including both `last_hash` and `token` *and* `num_steps` is probably overkill,
but made the previous points easier to argue.

A certificate contains redundant information, and can be compressed:
The bits in the Safety range are usually 0 or close to it.
Specifically, [Golomb coding](https://en.wikipedia.org/wiki/Golomb_coding) applies here perfectly,
as the Safety bits do indeed follow a geometric distribution, if the certificate was computed naively.
However, this makes the certificate of variable size and therefore more difficult to handle.
Furthermore, even removing the Safety bits completely would yield 50% compression
at best.  For most applications, this should not make an all-or-nothing difference.
Therefore I judged it more important to keep the PoW system as simple as possible.

Length extension attacks to not apply,
as the hash buffer lengths are a compile-time constant.

## Performance

This is mostly a Proof of Concept implementation, so don't look at the numbers too
closely.  However, as the C implementation is not too bad and the verifier by
design doesn't have much work, the numbers aren't too far off, either.

The prover has to compute roughly `r * 2^d` hashes, where `r` is the number of
steps, and `d` is the difficulty.  This split means that `r` and `d` can be
adapted to your PoW-needs, i.e. as easy or difficult as you need it to be.
It also means that most of the work is done by the SHA256 function.
As most languages already have ways to compute SHA256 efficiently,
I'm not going to analyze how well this can be done.
As a rough orientation, `prover.c` seems to compute about 500 KH/s
(kilo hashes per second) on my machine.

The prover has to submit a certificate of length `r * (d + s)` bits, where `s` is the
"Safety" number (see [Theory](#theory)).  This means that certificates can easily be
kept short enough for most applications.

The verifier has to compute exactly `r` hashes (or less in case of an invalid certificate).
This means that the verifier has basically nothing to do, which is also why I dared to implement it in Python.
For reference: All tests (which include at least 4 valid, nontrivial certificates)
run faster than I can meaningfully measure.

## Alternatives

- Single hash inversion: [Bitcoin](https://en.wikipedia.org/wiki/Bitcoin),
  [Hashcash](https://en.wikipedia.org/wiki/Hashcash), other cryptocurrencies,
- Symmetric hash inversion: [scrypt](https://en.wikipedia.org/wiki/Scrypt)-based systems
- More complex, possibly-single-shot system: [Equihash](https://en.wikipedia.org/wiki/Equihash)
- PoW that sees parallelism as a benefit: [Lyra2](https://en.wikipedia.org/wiki/Lyra2)
- See also: [List of PoW functions](https://en.wikipedia.org/wiki/Proof_of_work#List_of_Proof-of-Work_functions)
- See also: [Proof of Space](https://en.wikipedia.org/wiki/Proof_of_space)

## TODOs

Next up are these:
* Ask people for feedback on:
    * Making it more interesting for other people
    * Better comparison with other projects
* Consider reordering README sections
* Make the prover actually usable
* Implement the prover in other languages (i.e. go, Rust, wasm, etc.)
* Implement the verifier in other languages (i.e. go, Rust, wasm, etc.)
* Figure out Erlang distribution tails (see above)

## NOTDOs

Here are some things this project will definitely not support:
* Zero-knowledge anything.  This field of work is awesome, but not in scope for this little PoW project.
* Anything sophisticated with the Initial Hash or Token.
  The idea is that the parameters are already agreed-upon.
* Compression: See [Design Considerations](#design-considerations)
* Any other way to deal with endianness.  Trying to do it with
  [portable includes](https://github.com/BenWiederhake/portable-endian.h/blob/0ff2b6574b56bb08efcf01311f22c177b744da1d/portable_endian.h)
  is a mess.  Doing it with
  [shifts and bitmasks](https://github.com/BenWiederhake/portable-endian/blob/master/portable-endian.h)
  compiles down to
  [noop and byteswap](https://godbolt.org/z/Fs9-c4)
  in sufficiently advanced compilers.

I'm not sure how I feel about super-hyper-optimizations using assembler or SIMD-type things.
For now, I will not focus on it, but a PR adding for example a `prover-simd.c` would be welcome.

## Contribute

Feel free to dive in! [Open an issue](https://github.com/BenWiederhake/subint/issues/new) or submit PRs.
