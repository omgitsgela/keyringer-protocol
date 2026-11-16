# The Legacy (pre-2013) KeyRinger Tone

Units sold until the January 2013 algorithm change listen for a different,
simpler call signal. The vendor library preserves its only published sample:
`keyringer1.mp3` (also served today as the site's "CALL ORIGINAL" button,
byte-identical by MD5).

## Structure

Five frequency blips, keyed on/off with silence between them:

```
blip   on(s)    dur(s)   freq(Hz)
 1     0.030    0.179    4450   (preamble: ~1.4x longer)
 2     0.435    0.129    4100
 3     0.790    0.129    4400
 4     1.145    0.129    4100
 5     1.500    0.120    4400
```

- Steady silence gap between blips: **0.2256 s** (±0.0002 s across all four gaps).
- Blips 2–5 share a constant duration ≈ **0.129 s**; the preamble blip is
  ≈ 0.179 s (ratio ≈ 1.38).
- The frequencies are the old alphabet: 4100 and 4400 Hz alternate (4450 Hz
  measured for the longer preamble blip; FFT resolution on a 0.179 s tone
  makes 4450 vs 4400 within ~28 Hz of each other, so the preamble may just be
  4400 Hz).

## What it encodes

Two dimensions are available: symbol frequency (2 symbols: ~4100/4400 Hz) and
on-duration (the vendor library shows durations quantized around 0.129 / 0.179
s in this family's files, i.e. a short/long "dot-dash" style code, though only
the all-short `keyringer1` pattern ships in the library).

With 4 data blips and 2 frequency symbols that is 2⁴ = 16 addressable codes at
minimum, or 4×2 = 8 bits if durations are also used. The old control page
labels this button group "CALL KEYRINGERS 1–10" and always plays
`keyringer1.mp3` for it — consistent with a *group wake* signal rather than
an individual address: in the original product every pair responded to its own
pair and nothing else, and this tone exists to wake old units.

Given only one legacy tone exists in the corpus, the full legacy address
grammar cannot be recovered statistically — that would require the pre-2013
tone set, which the vendor did not publish. The 5-blip wake pattern above is
fully measured and reproducible (it is `keyringer1.mp3` itself).

## Cross-generation compatibility

Vendor FAQ: "In January 2013, a new and much improved algorithm was
introduced to detect the tones used by the KeyRinger. The new algorithm and
the original algorithm are not compatible" — confirmed acoustically: across
the full 5,886-file decoded corpus, **5,883 files begin with the modern
≥0.9 s sync tone, exactly 2 show the legacy 5-blip structure** (`keyringer1`
and its byte-identical live copy), and 1 (`short.mp3`) has no in-band tone
content at all. No post-2013 file shares the legacy on/off-keyed structure,
and the legacy blips (4100/4400 Hz with silence gaps) match none of the A/B/C
differential frame timing.
