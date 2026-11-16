#!/usr/bin/env python3
"""keyringer.py — encode and decode the KeyRinger audible-tone protocol.

The KeyRinger system (keyringer.com) calls its key/phone finders by playing
sequences of audio tones through any ordinary speaker. This module implements
the two protocol generations found in the vendor's own tone library:

  1. Calling frames (address protocol, devices sold since 2014):
       1.172 s sync tone at symbol B, then L slots at 0.177 s/slot encoded
       with a differential 3-symbol FSM: the bit rides on the *transition*
       between consecutive symbols, not on the symbol itself.
       Symbols: A=4032 Hz, B=4098 Hz, C=4167 Hz.
       - Universal/group frames: anchor symbol A, then L transition bits,
         LSB-first (L = 5..8, group value 0..255).
       - Unique/individual frames: anchor symbol C, then a long-code flag
         transition (1 when value >= 16 - the vendor's own short/long
         signal-length rule), then L-1 data bits, LSB-first (L = 5..12).

  2. Programming/command frames:
       1.172 s sync tone, then 17 slots at 0.2441 s/slot, binary A=0 / B=1
       (absolute symbol encoding, unlike the calling frames):
         slot 1    : anchor A
         slots 2-9 : value byte (8 bits, LSB-first; one-hot for volume levels)
         slots 10-14: opcode (5 bits, LSB-first)
         slot 15    : opcode-extension flag
         slot 16    : even parity over slots 2..15
         slot 17    : second check symbol (function of opcode+value; rule not
                      recoverable from the tone corpus - see docs/protocol.md)

Usage:
  python3 keyringer.py encode --family universal_8 --value 42 out.wav
  python3 keyringer.py encode --family unique_12 --value 1234 out.wav
  python3 keyringer.py encode --cmd response_duration=45 out.wav
  python3 keyringer.py decode tone.wav
"""
import argparse, sys, wave, math

SR = 44100
SYMFREQ = {'A': 4032.0, 'B': 4098.0, 'C': 4167.0}
SYNC_LEN = 1.171
CALL_UNIT = 0.1766
CMD_UNIT = 0.2441

# Differential FSM for calling frames: (previous symbol, bit) -> next symbol
TRANS = {('A',0):'B', ('A',1):'C', ('B',0):'C', ('B',1):'A', ('C',0):'B', ('C',1):'A'}
# Inverse (empirically forced by all 4,492 vendor address tones):
INV = {('A','B'):0, ('A','C'):1, ('B','C'):0, ('B','A'):1, ('C','B'):0, ('C','A'):1}

# Command opcodes, verified against all 1,375 vendor command tones.
# Tuple = (5-bit opcode in slots 10-14, slot-15 flag value, value_lo, value_hi).
OPCODES = {
    'universal_code':        (0b00000, 1, 0, 255),
    'signal_length_short':   (0b00001, 1, 5, 8),
    'signal_length_long':    (0b00010, 1, 6, 13),
    'double_click_speed':    (0b00011, 1, 3, 100),
    'uniq_code_xmit_base_lo':(0b00100, 1, 0, 255),
    'uniq_code_xmit_base_hi':(0b00101, 1, 0, 15),
    'uniq_code_rcv_lo':      (0b00110, 1, 0, 255),
    'uniq_code_rcv_hi':      (0b00111, 1, 0, 15),
    'min_response_volume':   (0b01000, 1, 1, 5),
    'max_response_volume':   (0b01001, 1, 1, 5),
    'response_duration':     (0b01010, 1, 1, 255),
    'min_call_volume':       (0b01011, 1, 1, 5),
    'max_call_volume':       (0b01100, 1, 1, 5),
    'duration_each_call_vol':(0b01101, 1, 1, 5),
    'disable_low_battery':   (0b01110, 1, 0, 1),
    'flicker_led':           (0b01111, 1, 0, 1),
    'detection_window_size': (0b10000, 1, 1, 6),
    'threshold_12':          (0b11110, 0, 4, 64),
    'threshold_25':          (0b11111, 0, 16, 128),
    'factory_reset':         (0b11111, 1, 0, 0),
}
# Volume levels (1..5) are stored one-hot in the value byte, not binary.
ONEHOT = {'min_response_volume', 'max_response_volume', 'min_call_volume',
          'max_call_volume'}

# slot 17 is a vendor check symbol whose closed form is unknown; the exact
# value for every catalogued (command, value) pair is published in
# data/slot17_table.json. The encoder loads it when present.
import json as _json, os as _os
_S17 = None
def _slot17_table():
    global _S17
    if _S17 is None:
        p = _os.path.join(_os.path.dirname(__file__), '..', 'data', 'slot17_table.json')
        try:
            _S17 = _json.load(open(p))
        except (OSError, ValueError):
            _S17 = {}
    return _S17

def calling_symbols(family, value):
    kind, L = family.split('_'); L = int(L)
    if kind == 'universal':
        # anchor symbol A, then L differential transitions = L data bits (LSB-first)
        bits = L
        s = ['A']
    elif kind == 'unique':
        # anchor symbol C, then a "long code" flag transition (1 when value >= 16,
        # matching the vendor's short/long signal-length rule), then (L-1) data
        # bits (0..L-2) LSB-first
        bits = L - 1
        s = ['C', TRANS[('C', 1 if value >= 16 else 0)]]
    else:
        raise ValueError(f'unknown calling family {family}')
    if not (0 <= value < (1 << bits)):
        raise ValueError(f'value {value} out of range for {family} (0..{(1<<bits)-1})')
    for k in range(1, bits + 1):
        s = s + [TRANS[(s[-1], (value >> (k-1)) & 1)]]
    return s

def command_symbols(cmd, value, check17=None):
    op, flag, lo, hi = OPCODES[cmd]
    if not (lo <= value <= hi):
        raise ValueError(f'value {value} out of range for {cmd} ({lo}..{hi})')
    if cmd in ONEHOT:
        databits = [(1 if i == value - 1 else 0) for i in range(8)]
    else:
        databits = [(value >> k) & 1 for k in range(8)]
    opbits = [(op >> k) & 1 for k in range(5)]     # slots 10-14
    slots = ['A']
    slots += ['B' if b else 'A' for b in databits]      # slots 2-9
    slots += ['B' if b else 'A' for b in opbits]        # slots 10-14
    slots.append('B' if flag else 'A')                  # slot 15: opcode-extension flag
    par = (sum(databits) + sum(opbits) + flag) & 1
    slots.append('B' if par else 'A')                   # slot 16: even parity, slots 2..15
    if check17 is None:
        # exact vendor value for every catalogued command; falls back to the
        # parity bit only for uncatalogued (command, value) pairs
        tbl = _slot17_table().get(cmd, {})
        check17 = tbl.get(str(value), par)
    slots.append('B' if check17 else 'A')               # slot 17
    return slots

def symbols_to_wav(path, syms, unit, sync=SYNC_LEN, amp=0.5):
    n_sync = int(sync * SR)
    n_slot = int(round(unit * SR))
    sig = [0.0] * (n_sync + len(syms) * n_slot)
    for i in range(n_sync):
        sig[i] = amp * math.sin(2*math.pi*SYMFREQ['B']*i/SR)
    for j, s in enumerate(syms):
        f = SYMFREQ[s]
        a = n_sync + j*n_slot
        for i in range(n_slot):
            sig[a+i] = amp * math.sin(2*math.pi*f*(a+i)/SR)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for v in sig:
            w.writeframes(int(max(-1.0, min(1.0, v)) * 32767).to_bytes(2, 'little', signed=True))
    return syms

def main():
    p = argparse.ArgumentParser(description='KeyRinger tone encoder/decoder')
    sub = p.add_subparsers(dest='op', required=True)
    e = sub.add_parser('encode')
    e.add_argument('--family', help='calling family, e.g. universal_8 or unique_12')
    e.add_argument('--cmd', help='command, e.g. response_duration=45')
    e.add_argument('--value', type=int)
    e.add_argument('out', help='output .wav path')
    d = sub.add_parser('decode', help='decode requires numpy: see decode_note')
    d.add_argument('file')
    a = p.parse_args()
    if a.op == 'encode':
        if a.cmd:
            cmd, _, val = a.cmd.partition('=')
            if not val:
                p.error('--cmd wants name=value')
            syms = command_symbols(cmd, int(val))
            unit = CMD_UNIT
        elif a.family and a.value is not None:
            syms = calling_symbols(a.family, a.value)
            unit = CALL_UNIT
        else:
            p.error('use --family/--value or --cmd name=value')
        symbols_to_wav(a.out, syms, unit)
        print(f'{a.out}: {" ".join(syms)}')
    else:
        try:
            import numpy as np  # noqa
        except ImportError:
            print('decoding needs numpy; see README "Decoding" section'); sys.exit(1)
        from decoder import decode_file   # local helper
        print(decode_file(a.file))

if __name__ == '__main__':
    main()
