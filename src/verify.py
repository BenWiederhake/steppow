#!/usr/bin/env python3

from hashlib import sha256
from math import ceil, log2

TEST_CERTS = [
    (b'', 7, 7, 800, bytes(10), -1, False),
    (b'', 7, 7, 800, bytes(1400), -1, False),
    (b'', 7, 7, 33, b'\x04\x64\x02\xA0\x13\x80\x47\x03\xF4\x04\x60\x1A\x01\x33\x0C\xAC\x04\x00\x12\x40\x4E\x01\x6C\x0B\x90\x52\x40\x85\x02\x1C\x0C\x20\x35\x01\x3A\x05\xF4\x0A\x90\x3A\x00\x9E\x00\xE0\x14\xA0\x24\x40\xEB\x01\xE4\x0B\xA0\x38\x80\x68\x06\x2C', 6596, True),
    (b'x', 7, 7, 33, b'\x04\x64\x02\xA0\x13\x80\x47\x03\xF4\x04\x60\x1A\x01\x33\x0C\xAC\x04\x00\x12\x40\x4E\x01\x6C\x0B\x90\x52\x40\x85\x02\x1C\x0C\x20\x35\x01\x3A\x05\xF4\x0A\x90\x3A\x00\x9E\x00\xE0\x14\xA0\x24\x40\xEB\x01\xE4\x0B\xA0\x38\x80\x68\x06\x2C', -1, False),
    (b'', 7, 7, 33, b'\x04\x64\x02\xA0\x13\x80\x47\x03\xF4\x04\x60\x1A\x01\x33\x0C\xAC\x04\x00\x12\x40\x4E\x01\x6C\x0B\x90\x52\x41\x85\x02\x1C\x0C\x20\x35\x01\x3A\x05\xF4\x0A\x90\x3A\x00\x9E\x00\xE0\x14\xA0\x24\x40\xEB\x01\xE4\x0B\xA0\x38\x80\x68\x06\x2C', -1, False),
]


def analyze_params(prefix, difficulty, safety, steps, hashes_actual):
    print('Prefix: {}'.format(prefix))
    print('Difficulty: {}'.format(difficulty))
    print('Safety: {}'.format(safety))
    print('Steps: {}'.format(steps))
    print('--------------------')
    print('Bits per step: {}'.format(difficulty + safety))
    print('Probability of impossibility: < 2^({})'.format(log2(steps) - 2 ** safety))
    print('E[num hashes]: {}'.format(steps * (2 ** difficulty)))
    print('Actual num hashes: {}'.format(hashes_actual))
    print('Suffix byte length: {}'.format(ceil(steps * (difficulty + safety) / 8)))
    print('--------------------')


def check_difficulty(buf, difficulty):
    digest = sha256(buf).digest()
    return all(digest[i // 8] & (1 << (7 - i % 8)) == 0 for i in range(difficulty))


def try_verify(prefix, difficulty, safety, steps, suffix):
    if len(suffix) != ceil(steps * (difficulty + safety) / 8):
        print('Bad length.')
        return False
    for i in range(1, steps + 1):
        suffix_bits = (difficulty + safety) * i
        buf = bytearray(prefix) + suffix[:(suffix_bits + 7) // 8]
        clear_bits = (8 - suffix_bits % 8) % 8
        buf[-1] &= ~((1 << clear_bits) - 1)
        if not check_difficulty(buf, difficulty):
            print('Failed at step {}, with buf {}'.format(i, buf))
            return False
    return True


def run_on(prefix, difficulty, safety, steps, suffix, hashes_actual, valid_expect):
    analyze_params(prefix, difficulty, safety, steps, hashes_actual)
    valid_actual = try_verify(prefix, difficulty, safety, steps, suffix)
    print('Valid: {}'.format(valid_actual))
    print('Matches expectation: {}'.format(valid_actual == valid_expect))
    if valid_actual != valid_expect:
        print('== ERROR: Wrong! ==')


def run_all(certificates):
    for cert_i, cert in enumerate(TEST_CERTS):
        print('========================================')
        print('Checking cert #{}'.format(cert_i))
        run_on(*cert)


if __name__ == '__main__':
    run_all(TEST_CERTS)
