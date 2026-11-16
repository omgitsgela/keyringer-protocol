#!/usr/bin/env python3
"""manifest.py — decode a directory of KeyRinger tone WAVs into a CSV manifest.

Usage: python3 manifest.py <wav_dir> <out.csv> [shard_index] [shard_count]
"""
import os, sys, csv, glob
import decoder

FIELDS = ['file', 'kind', 'family', 'command', 'value', 'volume_level',
          'opcode', 'slot15_flag', 'parity_ok', 'symbols', 'duration_s', 'sync_s', 'unit']

def main():
    d, out = sys.argv[1], sys.argv[2]
    shard = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    nshard = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    files = sorted(glob.glob(os.path.join(d, '*.wav')))
    files = [f for i, f in enumerate(files) if i % nshard == shard]
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for k, f in enumerate(files):
            try:
                r = decoder.decode_file(f)
            except Exception as e:
                r = {'file': os.path.basename(f), 'kind': 'error:' + type(e).__name__}
            w.writerow({k2: r.get(k2, '') for k2 in FIELDS})
            if (k + 1) % 500 == 0:
                print(shard, k + 1, flush=True)
    print('shard', shard, 'done', len(files), flush=True)

if __name__ == '__main__':
    main()
