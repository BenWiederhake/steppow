CC=clang -Wall
#CC_WARN?=-Weverything
CFLAGS?=-O3 -march=native

all: runprover runverifier

# No auto-rules
.SUFFIX:

.PHONY: runprover
runprover: bin/prover
	$<

bin/prover: src/prove.c src/prove-config.h src/portable-endian.h
	${CC} ${CC_WARN} ${CFLAGS} $< -lgcrypt -o $@

.PHONY: runverifier
runverifier: src/verify.py
	$<
