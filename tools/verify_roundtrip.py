#!/usr/bin/env python3
"""verify_roundtrip.py — encoder -> WAV -> decoder self-test across the protocol.

Encodes a sample of every calling family/value range and every command
opcode/value range with tools/keyringer.py, writes a WAV, then decodes it
back with tools/decoder.py and checks the payload survived exactly.

Run from the tools/ directory (or add tools/ to PYTHONPATH).
"""
import os, sys, random, tempfile
import keyringer as K
import decoder as D

random.seed(1234)

def calling_cases():
    # (family, value): sample edges + randoms for every family the vendor ships
    ranges = {
        'universal_5': (0, 31), 'universal_6': (0, 63),
        'universal_7': (0, 127), 'universal_8': (0, 255),
        'unique_5': (1, 15), 'unique_6': (1, 31), 'unique_7': (1, 63),
        'unique_8': (1, 127), 'unique_9': (16, 255), 'unique_10': (16, 511),
        'unique_11': (16, 1023), 'unique_12': (16, 2047),
    }
    for fam, (lo, hi) in ranges.items():
        vs = {lo, hi, (lo + hi) // 2, 16, 15}
        vs |= set(random.sample(range(lo, hi + 1), min(6, hi - lo + 1)))
        for v in sorted(vs):
            if lo <= v <= hi:
                yield fam, v

def command_cases():
    for cmd, (op, flag, lo, hi) in K.OPCODES.items():
        vs = {lo, hi, (lo + hi) // 2}
        vs |= set(random.sample(range(lo, hi + 1), min(5, hi - lo + 1)))
        for v in sorted(vs):
            if lo <= v <= hi:
                yield cmd, v

def main():
    tmp = tempfile.mkstemp(suffix='.wav')[1]
    ok = fail = 0
    failures = []
    for fam, v in calling_cases():
        syms = K.calling_symbols(fam, v)
        K.symbols_to_wav(tmp, syms, K.CALL_UNIT)
        r = D.decode_file(tmp)
        if r.get('kind') == 'calling' and r.get('family') == fam and r.get('value') == v:
            ok += 1
        else:
            fail += 1
            failures.append(('calling', fam, v, r))
    for cmd, v in command_cases():
        syms = K.command_symbols(cmd, v)
        K.symbols_to_wav(tmp, syms, K.CMD_UNIT)
        r = D.decode_file(tmp)
        if cmd in K.ONEHOT:
            # volume levels travel one-hot in the value byte; the decoder
            # reports the raw byte in 'value' and the level in 'volume_level'
            good = (r.get('kind'), r.get('command'), r.get('volume_level')) == ('command', cmd, v)
        else:
            good = (r.get('kind'), r.get('command'), r.get('value')) == ('command', cmd, v)
        if good:
            ok += 1
        else:
            fail += 1
            failures.append(('command', cmd, v, r))
    os.unlink(tmp)
    print(f'round-trip: {ok} passed, {fail} failed')
    for f in failures[:20]:
        print('  FAIL', f[0], f[1], f[2], '->', {k: f[3].get(k) for k in
              ('kind', 'family', 'command', 'value', 'symbols')})
    sys.exit(1 if fail else 0)

if __name__ == '__main__':
    main()
