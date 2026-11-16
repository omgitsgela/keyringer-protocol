# The KeyRinger Tone Protocol — Full Specification

Everything in this document was derived from the vendor's own tone corpus
(5,869 files) and live site audio (17 files), and verified by re-encoding.
Measurements are from 44.1 kHz resampling of the vendor MP3s with
parabolic-interpolated FFT peak refinement.

## Symbol alphabet

Three steady tones, all within roughly one ERB of each other (human-audio
band, deliberately in the range small speakers reproduce well):

| Symbol | Frequency (measured) |
|---|---|
| `A` | 4032.0 Hz |
| `B` | 4098.0 Hz |
| `C` | 4167.0 Hz |

Vendor MP3s are natively 32 kHz mono; playback rate only needs to be consistent,
but everything below assumes absolute Hz at 44.1/48 kHz as shipped.

## Frame preamble (both generations, post-2013)

A **sync tone: `B` (4098 Hz) for 1.171 s**, starting ~0.029 s into the file
(the 29 ms lead-in is padding, not part of the protocol). Payload slots follow
*immediately and contiguously* — there are no silent gaps between payload
slots. Slot boundaries were confirmed by frequency-change detection:
mean measured sync length across samples 1.1709 s (calling) / 1.1697 s (command).

## 1. Calling frames

Slot length: **0.17705 s** (median of 38 measured slot pitches across
`universal_5…8`, `unique_5…12`; mean 0.17774, σ 0.0017 — the tiny positive
skew is run-detector edge quantization at 2.9 ms hop, not protocol).

Payload is encoded as a **differential 3-symbol finite state machine**: the bit
value is carried by the *transition* from one symbol to the next.

```
bit 0:  A→B   B→C   C→B
bit 1:  A→C   B→A   C→A
```

Equivalently: from symbol `A`, the two children are `{B, C}`; from `B` they are
`{C, A}`; from `C` they are `{B, A}` — each state has exactly one 0-child and
one 1-child, and no two states share both children. Note the alphabet is
*directed*: `B→A` is bit 1 while `A→B` is bit 0. This is the part of the
design worth admiring: the receiver needs no absolute symbol reference; it
decodes transitions, which is robust to a detection chain that can hear *which
tone stopped and which started* more reliably than a fixed label.

### 1.1 Universal (group) call frame — `universal_L_V`

- Anchor symbol: `A` (immediately after sync)
- Then `L` transition bits, LSB-first, where `L` ∈ {5, 6, 7, 8}
- Value range: 0 … 2^L − 1. Vendor corpus contains all values 0–31 (L=5),
  0–63 (L=6), 0–127 (L=7), 0–255 (L=8): 482 files.

`L` is the unit's *short/long signal length* setting — the device's receiver
only listens for frames of its configured length, and the site chooses the
length from the value (`V < 2^(L−1)` rule for the short default L=5).

Example — `universal_5_1` (the site's "CALL ALL" button):
symbols `A C B C B C` → transitions A→C(1), C→B(0), B→C(0), C→B(0), B→C(0)
→ bits LSB-first = `10000` = **1** = group ID 1 (factory default).

Example — `universal_5_5` (the site's "CALL DOMINO" button): bits `10100` = 5.

### 1.2 Unique (individual) call frame — `unique_L_V`

- Anchor symbol: `C`
- **First transition is the long-code flag**: 1 iff `V ≥ 16`. This is not an
  arbitrary header — it is literally the vendor's own routing rule
  (`if value < 16 use short_signal_length else use long_signal_length`)
  *encoded into the audio itself*, so the device always knows which length to
  expect without a separate negotiation.
- Then `L−1` data bits LSB-first (bits 0 … L−2).
- `L` ∈ {5…12}; vendor corpus: L=5 values 1–15, L=6 values 1–31, L=7 1–63,
  L=8 1–127, L=9 16–255, L=10 16–511, L=11 16–1023, L=12 16–2047 (4,010 files;
  value 0 is reserved/no tone, values 1–15 appear only in short lengths).

Example — `unique_5_7` (site button "unit 7"): symbols `C B A C A B`.
Transitions: C→B (flag 0, correct since 7 < 16), B→A (1), A→C (1), C→A (1),
A→B (0) → data bits LSB-first `1110` = **7**. ✔

Example — `unique_12_1000` (from vendor library, measured run list):
`B(sync) C A B C B A B A C A C A B` → flag C→A = 1 (1000 ≥ 16 ✔), data
bits `00011000111` = 1000. ✔

## 2. Programming (command) frames

Slot length: **0.2441 s**. Binary absolute encoding: `A` = 0, `B` = 1.
Total **17 payload slots**, all tones continuous. Measured example
(`universal_code_42`) run-lengths alternate exactly 1 or 2 slot units,
consistent with the fixed 0.2441 s grid.

| Slot | Field | Notes |
|---|---|---|
| 1 | `A` | anchor (0) |
| 2–9 | value byte | LSB-first. For the four volume commands the byte is **one-hot**: level k → bit k−1 (values 1,2,4,8,16), verified on all 20 volume tones |
| 10–14 | opcode | 5 bits, LSB-first |
| 15 | flag | opcode extension; constant per family (1 for 18 of 20 families, 0 for `threshold_12`/`threshold_25`) |
| 16 | parity | even parity over slots 2–15: verified `XOR(slots 2..16) == 0` on **all 1,375** command files |
| 17 | check symbol | deterministic function of (opcode, value). Rule unresolved (see docs/analysis.md); complete truth table: `data/slot17_table.json` |

A receiver plausibly uses slot 16 as a fast bit parity and slot 17 as a
frame-validity bit; the encoder here writes slot 17 from the vendor table, so
generated programming tones are bit-identical to the vendor's across all
1,375 catalogued commands.

### 2.1 Command table (all 20 opcodes)

| Command | Opcode | Flag | Value range (all contiguous in corpus) | Meaning |
|---|---|---|---|---|
| `universal_code` | 00000 | 1 | 0–255 | set group ID |
| `signal_length_short` | 00001 | 1 | 5–8 | set short call length |
| `signal_length_long` | 00010 | 1 | 6–13 | set long call length |
| `double_click_speed` | 00011 | 1 | 3–100 | double-click window (≈10 ms units; site shows 0.1 s–1.0 s) |
| `uniq_code_xmit_base_lo` | 00100 | 1 | 0–255 | unique transmit base, low byte |
| `uniq_code_xmit_base_hi` | 00101 | 1 | 0–15 | unique transmit base, high nibble |
| `uniq_code_rcv_lo` | 00110 | 1 | 0–255 | unique receiver ID, low byte |
| `uniq_code_rcv_hi` | 00111 | 1 | 0–15 | unique receiver ID, high nibble |
| `min_response_volume` | 01000 | 1 | 1–5 one-hot | response volume floor |
| `max_response_volume` | 01001 | 1 | 1–5 one-hot | response volume ceiling |
| `response_duration` | 01010 | 1 | 1–255 | beep duration; site presets 5 s/15 s/30 s/1/2/4 min |
| `min_call_volume` | 01011 | 1 | 1–5 one-hot | call volume floor |
| `max_call_volume` | 01100 | 1 | 1–5 one-hot | call volume ceiling |
| `duration_each_call_vol` | 01101 | 1 | 1–5 | time per volume step while ramping |
| `disable_low_battery` | 01110 | 1 | 0–1 | smoke-alarm-style low battery alert on/off |
| `flicker_led` | 01111 | 1 | 0–1 | constant LED flicker on/off |
| `detection_window_size` | 10000 | 1 | 1–6 | receiver detection window |
| `threshold_12` | 11110 | 0 | 4–64 | short-signal detection threshold (default 12) |
| `threshold_25` | 11111 | 0 | 16–128 | long-signal detection threshold (default 32) |
| `factory_reset` | 11111 | 1 | 0 | reset all settings |

`threshold_12` and `threshold_25` are named after the vendor's default values
(12 and 32) and are the only flag-0 opcodes; opcode 11111 + flag 1 is
`factory_reset`, so opcode+flag together form the 6-bit command space that
slot 15 extends.

The four volume commands take a level 1–5 and store it one-hot, which is why
the manifest's decoded value byte for `max_call_volume_3` reads 4 (binary
`100`): the third level. `min_*`/`max_*` pairs bound the ramp: a called unit
starts at the *min* level and steps to the *max* level, `duration_each_call_vol`
seconds per step. This matches the vendor's "responds first at a low level so
as not to startle anyone and gradually ramps up."

### 2.2 Factory defaults (from the vendor's own archived control page)

```
receiver number 1 · transmitter base 0 · group ID 1
double-click speed 40 · response duration 15
response volume 1→4 · call volume 3→4 · duration each call volume 1
flicker LED off · low battery alert on
short signal length 5 · long signal length 8
detection window 4 · short threshold 12 · long threshold 32
```

## 3. The 16-bit unique code system

The old control page shows the intended architecture: receiver numbers and
transmitter base numbers are 16-bit, played as **two consecutive command
tones** (`…_lo` always, plus `…_hi` only when the high nibble ≠ 0, with the
player waiting for the first tone to finish — `waitForAudio()`). That is why
16-value and 256-value families exist per role. The live "unit 1…14" buttons
are *not* this system; they are the simple `unique_5_V` codes used by current
retail units (verified by MD5: live button tones are byte-identical to
`unique_5_1 … unique_5_14` in the vendor library).

## 4. Timing budget summary

| Parameter | Value |
|---|---|
| Lead-in padding | 0.029 s |
| Sync tone | `B` = 4098 Hz, 1.171 s |
| Calling slot | 0.17705 s (frame totals 2.06–3.30 s) |
| Command slot | 0.2441 s (frame total ≈ 5.34 s, "approximately six seconds" per vendor docs) |
| Programming-mode timeout | 4 minutes (vendor docs) |
