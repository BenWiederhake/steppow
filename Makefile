CC=clang
CC_WARN?=-Wall -Wextra -pedantic
#CC_WARN?=-Weverything -Wno-padded
CFLAGS?=-O3 -march=native

all: runprover runverifier

# No auto-rules
.SUFFIX:

.PHONY: runprover
runprover: bin/prove
	$<

bin/prove: src/prove.c src/portable-endian.h
	${CC} ${CC_WARN} ${CFLAGS} $< -lgcrypt -o $@

.PHONY: runverifier
runverifier: src/verify.py
	$<
