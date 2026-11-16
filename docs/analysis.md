# How the Protocol Was Recovered (and How to Verify It)

This is the methods + evidence document. Everything claimed in
[protocol.md](protocol.md) traces to one of the numbers below.

## Corpus

The vendor's [zip-files page](https://www.keyringer.com/zip-files) states:
"All the original KeyRinger tones, including audio1.html that referenced the
tones." Four archives were downloaded (November 2026) and SHA-256 verified:

| Archive | SHA-256 | Content |
|---|---|---|
| `all_tones.zip` | `ef15795d847b1218967c0db1fcec2410586c0f2c1a11e957ff9b7e424e65ccfb` | 5,870 entries: 5,869 MP3s + `audio1.htm` |
| `universal_program_tones.zip` | `afd8510d373bbc413fd83947e72bf874d6c8b50cceeec9105ab7f201ce149308` | 101 MP3s (subset, byte-identical to `all_tones.zip`) |
| `receive_program_tones.zip` | `a825b4c6357140f33b14e40eeca31505bbe1243661335445a69a5677a97622d2` | 101 MP3s (subset, byte-identical) |
| `transmit_program_tones.zip` | `b123fe1ec9203b0f718284f9ef2d1a9220cbc05afad1ac070f1f7304b0e4b22e` | 101 MP3s (subset, byte-identical) |

(The three program archives were diffed against `all_tones.zip` entry by
entry: 303/303 MD5-identical. Analysis used the union: 5,869 unique tones.)

The live site's 17 buttons fetch lazily from `music.wixstatic.com/mp3/<id>.mp3`;
the URLs were captured by clicking every Play button and diffing the browser's
`performance.getEntriesByType('resource')` log (Wix JSON scraping was a dead
end; click-and-diff worked). **MD5 verification: 16 of 17 live tones are
byte-identical to vendor library files** (`universal_5_1`, `universal_5_5`,
`unique_5_1…14`); the 17th ("CALL ORIGINAL") is byte-identical to
`keyringer1.mp3`. So the live page and the archived library are the same
system.

The archives were security-scanned before extraction (magic bytes, path
traversal, encryption flags, symlink entries, zip-bomb ratio, executable
extensions): clean. `all_tones.zip` opens with a plain
Microsoft FrontPage-era `audio1.htm` — the vendor's own 2013-era control
panel. Its JavaScript (`finish_up(button_number)`, archived verbatim as
[legacy-audio1-page.js](legacy-audio1-page.js)) is primary evidence for the
command taxonomy and factory defaults: it *names* every tone file from user
input, e.g. `audio_file_name = "response_duration_" + response_duration.value`,
and its factory-reset branch writes the default table reproduced in
[product.md](product.md).

## Decoding pipeline

1. MP3 → WAV via ffmpeg (`-ar 44100 -ac 1 pcm_s16le`). 5,886 files
   (5,869 vendor + 17 live, deduplicated by MD5 to unique stems).
2. Locate the sync tone by **frequency-change** run detection on a 256-point
   STFT (Goertzel power at A/B/C per frame). Note: amplitude gating fails —
   payload tones are *contiguous*, back-to-back with no silence between them,
   so only frequency transitions delimit slots.
3. Fit the payload duration to a uniform slot grid (0.17705 s calling,
   0.2441 s command; 17 slots for command frames — the grid fit is exact
   across the whole corpus, e.g. a 12-slot frame measures 12.00 ± 0.05 slots).
4. Per slot, measure Goertzel power at 4032/4098/4167 Hz in the slot interior
   (guard margins ~0.22 of a slot each side); assign the unique dominant
   symbol. Command slots: A/B only; no C slot or multi-symbol slot occurs in
   any of the 1,375 command files.
5. Symbol strings vs ground truth: **the vendor's own file names are the
   labels.** A file called `unique_10_329.mp3` is, by the vendor's own
   generator, "unique frame, length 10, value 329."

## Verification results

| Check | Result |
|---|---|
| Decoder vs vendor filenames, all families | **5,855 / 5,867 direct agreements** |
| Remaining 12 | exactly the 12 volume tones `level 3,4,5` (decoded value byte is one-hot `4,8,16` — explained, see below) |
| 3 unclassified files | `keyringer1` (legacy), `mystery31e0` (MD5-identical to it), `short` (72 ms DC bump) |
| Address encoder re-encode, all 4,492 vendor address tones | **4,492 / 4,492 symbol-string exact** |
| Command encoder re-encode, slots 1–16 | **1,375 / 1,375 symbol-string exact** |
| Slot 16 parity rule | `XOR(slots 2..16) == 0` on **1,375 / 1,375** |
| Family/value coverage vs filename taxonomy | 12 calling families, 20 command families, identical ranges |
| Unique-code collisions | 0 — 4,010 unique frames, 4,010 distinct symbol strings (the long-code flag transition is what keeps L=10 value 106 distinct from L=12 value 106… they share a string *by design*: same code, different configured length) |
| End-to-end: repo encoder → WAV → repo decoder | all families/values sampled: exact; see `tools/verify_roundtrip.py` |

The one-hot volume finding came from exactly those 12 "mismatches": the
decoded value byte of every `*_volume_N` tone is a power of two (level N →
`1 << (N-1)`), and the 20 volume tones are the only files whose decoded value
disagrees with their filename number. One-hot also explains `duration_each_call_vol`
staying plain binary (it's a count, not a level).

## The differential FSM: how it was found

Pair statistics first: for `universal_5_V` the symbol at slot k correlates with
nothing at a fixed position — but the *transition* at slot k is a pure function
of bit k of V (verified per position for L = 5, 6, 7, 8; no exceptions across
482 files). Same for unique frames from a C anchor. The unique frames' first
transition initially looked like a constant header (`C→B`), but across L = 9…12
it flips at V = 16 — a boundary the filename data confirms is exactly the
vendor page's `< 16 ? short : long` branch, so the frame carries that decision
as a bit. With that rule the encoder matches the entire 4,010-file unique
corpus exactly.

The directed transition table (`B→A` = 1 while `A→B` = 0) means adjacent equal
symbols never occur in calling frames — consistent with the corpus (no `AA`,
`BB`, or `CC` runs in any of the 4,492 address frames after sync).

## Slot 17: what is known, what is not

Known: it is a deterministic function of opcode+value (no two identical
slot 1–16 payloads ever differ at slot 17 — checked exhaustively), its symbol
distribution is near-balanced (A:684, B:691), and for one-hot volume commands
it equals slot 16. Tried and rejected on all 1,375 frames: every contiguous
XOR parity window; GF(2)-linear functions of all 16 payload bits + constant
(rank-deficient by design — 676 inconsistent rows); mod-3/GF(3)/GF(4) symbol
sums; CRC-8 with 36×2×3 parameter sweep; Hamming(7,4)/(12,8)-style syndrome
bits; Luhn; decimal digit sums; popcount variants; V-bit arithmetic carries;
adjacency-change parity. The encoder therefore reads the exact vendor value
from [`slot17_table.json`](../data/slot17_table.json) (1,375 entries covering
the whole command space). A receiver only needs to *verify* slot 17, so a
compatible receiver can hard-code the same check; a transmitter for an
*uncatalogued* opcode+value pair cannot yet compute it.

## Legacy generation

`keyringer1.mp3` is not A/B/C at all: five on/off-keyed blips, first 0.179 s
then four at 0.129 s with 0.226 s gaps, at 4450 / 4100 / 4400 / 4100 / 4400 Hz
(measured to 0.1 Hz). The old page's "CALL KEYRINGERS 1–10" section plays it
as a group wake-up for pre-2013 devices. See [legacy.md](legacy.md).

## Honest limits

- No hardware was tested; this is RF-free acoustic analysis of vendor audio +
  vendor documentation.
- Slot 17's closed form is unknown (truth table published).
- The 16-bit receiver/transmitter-base architecture from `audio1.htm` matches
  the lo/hi command pairs, but how current firmware composes those 16-bit
  codes with the `unique_L_V` space is not observable from audio alone.
- Battery-life, range, and detection-window internals (the `detection_window_size`
  and `threshold_*` units) are vendor-internal; only their tone encodings are
  documented.
