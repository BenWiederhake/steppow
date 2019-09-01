#!/usr/bin/env python3

from hashlib import sha256
from math import ceil, log2

TEST_CERTS = [
    bytes(4),
    bytes(1400),
]


def read_params(filename):
    with open(filename, 'r') as fp:
        lines = fp.read().split('\n')
    params = dict()
    for l in lines:
        if not l.startswith('#define'):
            continue
        if not l.startswith('#define SPOW_'):
            print('WARNING: problems with this line:\n\t' + l)
            continue
        name_value = l[len('#define SPOW_'):].split(' ')
        if len(name_value) != 2:
            print('WARNING: cannot split line:\n\t' + l)
            continue
        name, value = name_value
        name = name.lower()
        if name in params:
            print('Error: {} defined multiple times?!'.format(name))
            return None
        if value.startswith('"'):
            value = 'b' + value
        value = eval(value)  # TODO: Do this without eval, please?
        params[name] = value
    return params


def analyze_params(prefix, difficulty, safety, steps):
    print('Prefix: {}'.format(prefix))
    print('Difficulty: {}'.format(difficulty))
    print('Safety: {}'.format(safety))
    print('Steps: {}'.format(steps))
    print('--------------------')
    print('Bits per step: {}'.format(difficulty + steps))
    print('Probability of impossibility: < 2^({})'.format(log2(steps) - 2 ** safety))
    print('E[num hashes]: {}'.format(steps * (2 ** difficulty)))
    print('Certificate byte length: {}'.format(ceil(steps * (difficulty + safety) / 8)))


def try_verify(cert, prefix, difficulty, safety, steps):
    if len(cert) != ceil(steps * (difficulty + safety) / 8):
        print('Bad length.')
        return False
    print('Checking rest: NOTIMPLEMENTED')
    return True


def run_on(filename):
    params = read_params(filename)
    if params is None:
        exit(1)
    # del params['NOTNEEDED']
    analyze_params(**params)
    for cert_i, cert in enumerate(TEST_CERTS):
        print('--------------------')
        print('Checking cert #{} ({}...)'.format(cert_i, cert[:80]))
        print(try_verify(cert, **params))


if __name__ == '__main__':
    import os.path
    # "os.path" allows calling this script from anywhere.
    run_on(os.path.join(os.path.dirname(__file__), 'config.h'))
