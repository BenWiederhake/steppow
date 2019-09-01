# simple-pow

> Simple, Asymmetric Proof of Work

I needed a proof of work system with the following properties:
- Asymmetric
- Easy to implement
- Easy to understand
- No parallelism
- Bonus: Easy way to determine progress
- Bonus: Free Software

Simple-pow implements all of these aspects as a Proof of Concept.

## Table of Contents

- [Background](#background)
- [Theory](#theory)
- [Install](#install)
- [Usage](#usage)
- [Recommendations](#recommendations)
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
this is the case for simple-pow.

### Easy to Implement

No-one likes importing a big blob of code without knowing what it does.
Also, PoW systems inherently occur in environments where different programs are
communicating, usually across hosts, and usually written in different languages.

Therefore, it should be sufficiently easy to rewrite the prover in the language of your
choice.  This is one of the reasons why the heavy lifting is done by the
well-trodden building block SHA256.

For comparison: `src/prove.c` only contains roughly 60 lines that actually run the prover.
The rest is comments, setup, and output.
And even that could be reduced further by reducing generality:
Turns out, handling arbitrary bitshifts has an impact on source code
length (and performance, too, I guess).

### Easy to Understand

I don't want to learn about Elliptic Curves or Weaken Fiat–Shamir signatures or how Merkle trees could be used for this.

Instead, simple-pow uses an old trick in a new flavor: A hash has to be inverted partially.

### No Parallelism

Partial hash inversions have been around for a long time.  There seems to
exist a tendency such that over time, the difficulty of such systems increases
to many, many bits.  This means that a single attempt is basically worthless;
random variance can be really awful; and by buying more hardware, the process
can be sped up significantly.

In simple-pow, a single attempt still is not worth much, but random variance has bounds:
By construction, the prover would need to guess the correct suffix bytes several times in a row.
Likewise, hitting the worst-case only means that many hashes have to be computed for a single step.

Finally, buying more hardware is not useful for simple-pow: Computing a certificate
cannot be meaningfully parallelized, as each step depends on the previous.
Computing a step cannot be meaningfully parallelized, because the expected number
of hashes for a single step already is so low that the synchronization overhead
might make it slower.

### Bonus: Easy Way to Determine Progress

A partial hash inversion gives no feedback about progress.  Either the correct
nonce has been found, or it hasn't.

In simple-pow, the prover could theoretically give feedback to the caller that "x/y"
steps have already completed.  This should serve well as a progress indicator.

### Bonus: Free Software

And last but not least: You can [run, study, improve and redistribute](https://en.wikipedia.org/wiki/Free_software#Definition_and_the_Four_Freedoms) to your heart's content.

## Theory

FIXME

## Install

FIXME.  pip?

## Usage

### Prover

The prover is not meant to be used in a dynamic fashion.
However, it should be straight-forward to replace the dependencies
on macros by variables in this particular implementation.

The way to run it is by changing values in `src/config.h`, recompiling and running it.
The comment at the top of `src/prove.c` tells you how:
`clang -O3 -march=native src/prove.c -lgcrypt -o bin/prove`

The output looks something like this:

```
Certificate found after 576047 hashes.  Suffix is:
\x04\x3F\xC0\x14\x4C\x10\x65\x80\x2D\x40\x26\x72\x08\x36\x00\x6E\xD0\x23\x20\x02\x70\x20\x13\xE8\x0A\xEE\x80\x7D\x20\x13\x9E\x06\xAC\x81\x3A\x90\x20\x98\x00\x11\x60\x3A\x4C\x05\x34\x00\x2D\xC0\x18\x3C\x0F\x1A\x80\x1E\xD0\x0A\x6B\x00\x25\xC0\x1F\x84\x00\x6B\x80\x52\x20\x18\xDA\x0F\xB7\xC0\x4C\x18\x1B\x84\x00\x8D\x80\x10\xD0\x08\x3A\x00\xAD\xA0\x22\x24\x00\x28\x40\x63\x80\x09\x99\x03\x74\x60\x1D\x30\x05\x8E\x01\xDE\x40\x49\xE8\x01\x7A\x40\xC3\x28\x00\xE6\x00\x75\x61\x42\x80\x02\x34\x80\x92\xB0\x03\x38\x03\x2F\x80\x60\x38\x07\xDC\x01\xB9\xA0\x34\x48\x00\x29\x00\xE5\xE0\x06\xB0\x07\xC6\xC0\x74\xA8\x45\x8A\x01\x7F\xE0\x56\xEC\x1E\x95\x80\x5D\x90\x02\xE8\x02\x10\x00\x1B\xE0\x11\x67\x03\xB2\x00\x32\x40\x08\xB0\x00\x52\x00\x02\x78\x02\x19\x40\x77\x40\x1A\x80\x00\xCA\x00\x98\x44\x0E\x26\x80\xCB\xA0\x1E\x66\x0B\xD8\x00\x0B\x88\x15\x39\x00\xE7\xA0\x1C\x88\x05\x3F\x00\x94\xE0\x61\xCE\x0C\xBB\x80\x1F\x28\x01\x51\x00\x9E\x00\x35\xE8\x17\xE6\x01\x53\xB0\x02\x98\x01\x1F\x80\x0D\xB0\x01\xA2\x01\xD4\x21\x04\x18\x04\xB6\x80\xCF\x20\x0A\xBA\x03\xF5\x80\xB8\xE8\x0D\xBA\x00\x7A\x40\x98\x4C\x0D\x17\x00\x1C\x90\x02\x7A\x00\x7D\x00\xBA\x68\x1F\x4A\x03\x3D\xE0\x2D\x7C\x03\xC4\x00\x5F\xE0\x2B\xD0\x12\x9F\x01\xEE\x38\x06\xB8
```

This tells you two things:
1. It took 576047 hash-computations to find the solution.  This is a very rough measure of raw computational power suck into the PoW.
2. The weird blob of data is the "suffix" of the certificate.  This is all the data needed for the PoW.

This output, together with the parameters, can be copied into `src/verify.py` to test certificate verification.

### Verifier

The verifier could in theory be alreadyused as-is for production work.
(However, it hasn't been battle-tested yet, and the tests in `TEST_CERTS` are
all the tests I ran so far.)  The function `verify.try_verify(prefix,
difficulty, safety, steps, suffix)` checks whether a given suffix is a valid
certificate for a given set of parameters.

You can also run `verify.py` as a stand-alone executable.
Then it runs a few self-tests, with everything I deemed possibly relevant.

Here's how the typical output looks like:

```
========================================
Checking cert #6
Prefix: b'World!'
Difficulty: 12
Safety: 7
Steps: 122
--------------------
Bits per step: 19
Probability of impossibility: < 2^(-121.06926266243711)
E[num hashes]: 499712
Actual num hashes: 500635
Suffix byte length: 290
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
The third part checks whether the suffic is a valid certificate,
which errors were encountered, and whether this matches our expectation.
This wway we can easily check that good suffixes are accepted, and bad suffixes are not.

## Recommendations

The Safety number only has an influence on provability, and a minor influence on the certificate size.
Hence I recommect a Safety number of 7, as it gives an extremely small probability of impossibilty (around 2^-118),
but does not bloat the certificate size.

This leaves only two other parameters: Difficulty and Stepcount:

```
Profile	Difficulty	Stepcount	Expected Total Work (KH)	Suffix Size (Bytes)
S	9	200	102,4	400
M	10	500	512	1063
L	12	1000	4096	2375
XL	13	5000	40960	12500
```

For comparison: A reasonable upper estimate on the performance of a single core is 3000 KH/s.

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

The prover has to submit a suffix of length `r * (d + s)` bits, where `s` is the
"Safety" number (see [Theory](#theory)).  This means that certificates can easily be
kept short enough for most applications.

The verifier has to compute exactly `r` hashes (or less in case of an invalid certificate).
This means that the verifier has basically nothing to do, which is also why I dared to implement it in Python.
For reference: All tests (which include at least 4 valid, nontrivial certificates)
run faster than I can meaningfully measure.

## Alternatives

FIXME

## TODOs

Next up are these:
* Finish README
* Explore other cryptograhics building blocks (could use crypt-likes?)
* Make the prover actually usable
- Collect Alternatives and why I didn't use them
* Implement the prover in other languages (i.e. go, Rust, wasm, etc.)
* Ask people for feedback on:
    * Making it more interesting for other people
    * Better comparison with other projects

## NOTDOs

Here are some things this project will definitely not support:
* Zero-knowledge anything.  This field of work is awesome, but not in scope for this little *simple* PoW project.
* Anything sophisticated with the prefix.  The idea is that the prefix is already agreed-upon.

I'm not sure how I feel about super-hyper-optimizations using assembler or SIMD-type things.
For now, I will not focus on it, but a PR adding for example a `prover-simd.c` would be welcome.

## Contribute

Feel free to dive in! [Open an issue](https://github.com/BenWiederhake/subint/issues/new) or submit PRs.
