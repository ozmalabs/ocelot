# Universal closed loop — Phase C, PIPER voicebox (the forward-model swap)

**VERDICT: NO-LIFT — Piper (neural TTS) did NOT beat espeak, and the floor separation
stayed NEGATIVE. Neural QUALITY was not the limiting factor.**

Phase C (espeak, commit `3d724209`) plateaued at cross-speaker LOSO **0.420** < CMVN
**0.570** and a forward-model-floor diagnostic pinned the cause as **(a) the forward model
too coarse** (espeak): true-word best-adapted residual **0.442** was NOT below the best
wrong-word **0.441**, separation **−0.021** (negative). The pre-written lever was a richer
generator (Piper neural voices). This run swapped **only** the synth backend — the loop
logic reused **byte-for-byte** — and re-ran the make-or-break floor diagnostic + the LOSO
table to completion. **Result: the wall did not fall; Piper did not even lift above espeak.
The diagnosis (a) is refuted as stated — the bottleneck is NOT the mouth's timbre.**

Scripts: `scripts/universal_loop_phaseC_piper.py` (runner) + `scripts/universal_loop_phaseAB_piper.py`
(the Piper voicebox swap-in). Loop reused unchanged from `scripts/universal_loop_phaseC.py`.
Captured log: `/tmp/phaseC_piper.log` (marker `UNIVERSAL_LOOP_PHASEC_PIPER_COMPLETE`).
Run: `.venv/bin/python -m scripts.universal_loop_phaseC_piper 40 10 60 20240610`
(`PHASEC_MAX_SYNTHS=12 PHASEC_PASSES=3 PHASEC_K=5 PHASEC_DIAG_N=60`). pgrep-verified exited,
exit code 0, total 608 s. **Must run with the project `.venv` python (Piper lives there).**

## (1) The Piper voicebox, wired (donkey audit)

`synth(W,V)` swapped to the Piper neural vocoder, SAME signature + voice-dict shape
(`{"id","variant","pitch","rate"}`) the loop manipulates, so the loop's coarse-match /
adapt-V coordinate-descent / order-N iterate / argmin run **unchanged** (the only edit is
rebinding the module-level `synth`/`build_voice_space` symbols inside the phaseC namespace).

- **Models present (verified synthesising):** `en_US-lessac-medium`, `fr_FR-siwis-medium`,
  `de_DE-thorsten-medium`, `es_ES-davefx-medium` — 4 neural timbres, **single-speaker each**
  (`num_speakers=1`). Donkey-audit voicing: `synth('five', lessac@p40r160) -> 32 cmvn frames
  x 32 bands`. Verified BEFORE the full run (Piper imports + synthesises one clip).
- **V-axes mapped onto Piper's controllable knobs** (the loop's unchanged coordinates →
  the neural mouth): `variant` → model timbre (hill-climbed neighbourhood); `rate`
  (80–300 wpm) → `length_scale = 175/rate` (clamped 0.55–1.8); `pitch` (0–99) →
  `noise_w_scale` 0.2–1.4 (Piper's per-utterance prosodic-variability knob — the medium
  models expose no f0 control, so this is the honest available prosody axis).
- **Honest coverage caveat:** 4 single-speaker models vs espeak's 104 variants. The
  diagnosis was QUALITY not COUNT, so single-timbre-family is a valid first test; the floor
  diagnostic isolates quality from count.
- **Donkey boundary (clean):** Piper = the WORLD/voicebox the agent controls and hears,
  NEVER inverted by the agent, NEVER in a decision — only re-voiced and re-heard via the
  loop's residual-min search. Features = the agent's OWN front end (`learned_voice_shape.
  residual_track`, empty library = per-utt CMVN), the SAME feature the DtwTo recognizer
  reads on real clips. The only `evaluate` target is DtwTo; no net/fit/gradient in the
  agent. Held-out REAL speakers NEVER banked; LOSO ungameable.

## (2) The FLOOR DIAGNOSTIC (the make-or-break) — separation still NEGATIVE

FULL adapt at EVERY word (no top-k pruning, k = all 10 words, budget 12 synths/word — the
absolute ceiling perfect convergence could reach), on **60 held-out LOSO clips**, 1388 live
Piper synths.

```
                                  Piper            espeak (prior)
coarse argmin (no adapt) acc:     0.350            0.417
FULL-adapt-every-word ceiling:    0.383            0.367
TRUE-word adapted residual:       median 0.434     0.442
best WRONG-word adapted residual: median 0.426     0.441
SEPARATION (wrong-true):          −0.009           −0.021
frac true<wrong:                  0.383            0.367
```

- **The make-or-break separation is STILL NEGATIVE: −0.009.** Piper narrowed the gap from
  espeak's −0.021 and dropped the true-word residual floor (0.442→0.434), but the true
  word, fully adapted, is **still not closer** than the best wrong word. The synthetic-vs-
  real gap remains larger than the between-word distance, even with a neural vocoder.
- The perfect-convergence **ceiling is 0.383** — below espeak's even-then 0.367 on the
  prior split, and nowhere near CMVN 0.570. Fixing convergence cannot reach the wall.

## (3) The LOSO table — Piper-loop BELOW espeak-loop

Robust SC 40-held-out-speaker LOSO; **80 seen + 100 cross-speaker LOSO** clips (10/word),
held-out REAL never banked. 111 live world calls in the loop, 0.2 synths/probe (the grid
was pre-synthesised offline — 600 Piper exemplars / 60 voices / 83 s — and adapt mostly
hit the cache).

| regime | seen | cross-speaker LOSO | gap |
|--------|------|--------------------|-----|
| CMVN (the wall) | 0.500 | **0.510** (canonical 0.570) | −0.010 |
| espeak-static (prior) | – | 0.400 | – |
| espeak-loop (prior) | – | 0.420 | – |
| PIPER-static (floor) | 0.375 | 0.350 | +0.025 |
| **PIPER-LOOP** | 0.388 | **0.360** | +0.028 |

- **PIPER-LOOP vs CMVN (this split): −0.150** (0.510 → 0.360). Far below the wall.
- **PIPER-LOOP vs espeak-loop (0.420): −0.060.** Piper-loop is WORSE than espeak-loop.
- **PIPER-LOOP vs PIPER-static floor: +0.010** — the loop's adaptation barely lifts above
  its own static library, and the convergence curves show **near-zero adapt drops**
  (`drop +0.000` on nearly every winning word): live re-synth rarely beat the cached grid
  voice, so adapt is doing almost nothing here.

## VERDICT: NO-LIFT — the mouth was not the wall

Piper neural quality moved the floor in the *predicted direction* (separation −0.021 →
−0.009, true-word residual 0.442 → 0.434) but **did not flip it positive and did not lift
LOSO above espeak** (0.360 < 0.420 < CMVN 0.510/0.570). Two readings, both pointing away
from "the mouth is the limit":

1. **Neural quality was not the limiting factor.** Doubling the generator's fidelity bought
   ~0.012 of separation and still left it negative. The hypothesis that espeak's *timbre*
   was the wall is **not supported** — a much better mouth lands in the same place.
2. The Piper *single-speaker* coverage (4 timbres + prosody knobs, no f0/speaker axis)
   likely sits *worse-positioned* than espeak's 104-variant pool for matching arbitrary
   real talkers — which is why the loop ends up below espeak even with cleaner audio. So
   the lifts-but-caps "→ multi-speaker Piper" reading is *possible*, but the **negative
   separation refutes the simple quality story**: the limiting factor is not rendering
   fidelity, it is that the **per-utterance CMVN feature + DtwTo residual cannot separate
   words across the synthetic-vs-real domain gap regardless of the mouth.**

**Where to look next (NOT the mouth):** the wall is the **feature front end / the DtwTo
residual / the V-axis itself**, not the generator's timbre. Candidate levers: a feature
that is invariant to the synthetic-vs-real domain shift (the residual is dominated by that
domain gap, swamping the between-word signal); a richer/learned residual than raw CMVN-DTW;
or a genuinely speaker-spanning V-axis (a multi-speaker model such as VCTK/LibriTTS) tested
against the same floor diagnostic to see if separation *finally* goes positive — but the
honest read of this run is that **swapping the mouth alone is exhausted as a lever.** Do not
rescue: the inversion machinery is sound and donkey-clean; the wall is upstream of the mouth.

## Notes

- Tests green where touched: `test_stt_pipeline`, `test_frontend_effect_gate` (11 passed) —
  same suites the espeak Phase C reported; only new script files added, no existing code
  modified.
- Compute managed as specified: the (W,V) grid pre-synthesised offline (600 Piper synths,
  83 s); the loop adapted over the grid with live re-synth reserved for the adapted
  neighbourhood (111 world calls total in the loop, 1388 in the full-budget diagnostic).
  Piper voice objects cached in-process (~0.6 s load once, ~0.14 s/synth thereafter).
- Not committed (coordinate).

[MARKER] UNIVERSAL_LOOP_PHASEC_PIPER_DOC_COMPLETE
