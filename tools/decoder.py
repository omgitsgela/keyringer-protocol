#!/usr/bin/env python3
"""decoder.py — decode KeyRinger tone audio (WAV; MP3 via ffmpeg) into protocol records.

Works without scipy; numpy only. The algorithms in here are the same ones used to
verify the protocol against all 5,886 vendor tone files.
"""
import wave, subprocess, os, tempfile
import numpy as np

from keyringer import SR, SYMFREQ, TRANS, INV, CALL_UNIT, CMD_UNIT, OPCODES

_A, _B, _C = SYMFREQ['A'], SYMFREQ['B'], SYMFREQ['C']
FRQ = {'A': _A, 'B': _B, 'C': _C}


def load_audio(path):
    """Return float mono samples at 44100 Hz. MP3/other formats go through ffmpeg."""
    if not path.lower().endswith('.wav'):
        fd, tmp = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', path,
                        '-ar', str(SR), '-ac', '1', '-c:a', 'pcm_s16le', tmp], check=True)
        path = tmp
    with wave.open(path, 'rb') as w:
        assert w.getframerate() == SR, f'expected {SR} Hz, got {w.getframerate()}'
        n = w.getnframes()
        raw = w.readframes(n)
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0


def _goertzel_power(seg, f):
    n = np.arange(len(seg))
    k = 2 * np.pi * f / SR
    pr = float((seg * np.cos(k * n)).sum())
    pi = float((seg * np.sin(k * n)).sum())
    return pr * pr + pi * pi


def _frame_track(x, frame=256, hop=64):
    """Symbol runs by dominant in-band frequency (for locating the sync tone)."""
    win = np.hanning(frame)
    nf = 1 + (len(x) - frame) // hop
    idx = np.arange(frame)[None, :] + hop * np.arange(nf)[:, None]
    sg = x[idx] * win
    n = np.arange(frame)
    P = np.zeros((nf, 3))
    for j, f in enumerate((_A, _B, _C)):
        k = 2 * np.pi * f / SR
        pr = sg @ np.cos(k * n)
        pi = sg @ np.sin(k * n)
        P[:, j] = pr * pr + pi * pi
    tot = P.sum(axis=1)
    active = tot > tot.max() * 0.05
    dom = np.argmax(P, axis=1)
    runs = []
    i = 0
    while i < nf:
        if not active[i]:
            i += 1
            continue
        j = i + 1
        while j < nf and active[j] and dom[j] == dom[i]:
            j += 1
        runs.append((i * hop / SR, j * hop / SR, 'ABC'[dom[i]]))
        i = j
    return runs


def decode_file(path):
    """Decode a KeyRinger tone file. Returns a dict with kind, symbols and payload."""
    x = load_audio(path)
    total = len(x) / SR
    runs = _frame_track(x)
    if not runs:
        return {'file': os.path.basename(path), 'kind': 'silence', 'duration_s': round(total, 3)}
    t0 = runs[0][0]
    t_end = runs[-1][1]
    sync_end = runs[0][1] if (runs[0][1] - runs[0][0]) >= 0.8 else t0

    def grid(unit):
        n = int(round((t_end - sync_end) / unit))
        out = []
        for k in range(n):
            a = int((sync_end + k * unit + 0.22 * unit) * SR)
            b = int((sync_end + (k + 1) * unit - 0.22 * unit) * SR)
            b = min(b, len(x))
            if b - a < 64:
                out.append('?')
                continue
            seg = x[a:b] * np.hanning(b - a)
            pk = {c: _goertzel_power(seg, f) for c, f in FRQ.items()}
            mx = max(pk.values())
            on = sorted(c for c in 'ABC' if pk[c] > 0.35 * mx)
            out.append(on[0] if len(on) == 1 else (''.join(on) if on else '.'))
        return out

    # Calling frame: 0.1766 s slots, pure A/B/C, FSM-decodable
    for kind, unit, skip in (('universal', CALL_UNIT, 0), ('unique', CALL_UNIT, 1)):
        s = grid(unit)
        if not s or any(c not in 'ABC' for c in s):
            continue
        if s[0] != ('A' if kind == 'universal' else 'C'):
            continue
        bits = []
        ok = True
        for k in range(1, len(s)):
            tr = (s[k - 1], s[k])
            if tr not in INV:
                ok = False
                break
            bits.append(INV[tr])
        if ok and bits:
            # universal frame: anchor A, then L data bits (0..L-1) LSB-first.
            # unique frame: anchor C, then a redundant long-code flag transition
            # (set when value >= 16, which is exactly the vendor's short/long
            # signal-length rule), then data bits 0..L-2 LSB-first.
            if kind == 'unique':
                flag, data = bits[0], bits[1:]
                value = 0
                for i, b in enumerate(data):
                    value |= b << i
                if flag != (1 if value >= 16 else 0):
                    continue     # flag must agree with the value
            else:
                value = 0
                for i, b in enumerate(bits):
                    value |= b << i
            L = len(bits)
            return {'file': os.path.basename(path), 'kind': 'calling',
                    'family': f'{kind}_{L}', 'value': value,
                    'symbols': ''.join(s), 'duration_s': round(total, 3),
                    'sync_s': round(sync_end - t0, 3), 'unit': unit}

    # Command frame: 17 slots at 0.2441 s, binary A/B
    s = grid(CMD_UNIT)
    if len(s) == 17 and all(c in 'AB' for c in s):
        val = sum((1 if s[i] == 'B' else 0) << (i - 1) for i in range(1, 9))
        op5 = sum((1 if s[i] == 'B' else 0) << (i - 9) for i in range(9, 14))
        flag = 1 if s[14] == 'B' else 0
        p16 = 1 if s[15] == 'B' else 0
        c17 = 1 if s[16] == 'B' else 0
        par = sum(1 for i in range(1, 15) if s[i] == 'B') & 1
        onehot = {'min_response_volume', 'max_response_volume', 'min_call_volume',
                  'max_call_volume'}
        # command is identified by (opcode, slot15 flag) alone; the value byte is
        # a plain binary number except for volume levels, which are one-hot.
        name = None
        for cmd, (op, fl, lo, hi) in OPCODES.items():
            if op == op5 and fl == flag:
                name = cmd
                break
        level = None
        if name in onehot:
            if val and (val & (val - 1)) == 0 and val <= 16:
                level = val.bit_length()        # one-hot position = level 1..5
            else:
                name = name + '?bad-onehot'
        return {'file': os.path.basename(path), 'kind': 'command',
                'command': name, 'value': val, 'volume_level': level,
                'opcode': format(op5, '05b'), 'slot15_flag': flag,
                'parity_slot16': p16, 'parity_ok': p16 == par,
                'check_slot17': c17, 'symbols': ''.join(s),
                'duration_s': round(total, 3), 'sync_s': round(sync_end - t0, 3), 'unit': CMD_UNIT}

    return {'file': os.path.basename(path), 'kind': 'unknown',
            'symbols': ''.join(grid(CALL_UNIT))[:24], 'duration_s': round(total, 3)}


if __name__ == '__main__':
    import sys, json
    print(json.dumps(decode_file(sys.argv[1]), indent=1))
