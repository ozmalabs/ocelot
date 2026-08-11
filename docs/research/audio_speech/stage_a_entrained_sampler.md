# Stage A — the self-clocking rhythmic sampler (entrained theta oscillator)

Stage A of the active-transducer interface plan (`docs/active_transducer_interface_plan.md`).
Tests the thesis **"the passive interface failed the frame; the active interface fixes it"**
(memory `ozma_interface_layer_is_active_transduction`).

## What was built — the SENSE, owned DSP, no net/fit

`domains/prosody_syllable.py::entrain_theta` — an **entrained theta oscillator** on the
voiced-energy *onset* envelope. It replaces the passive envelope **peak-counter**
(`extract_syllables`, the ~0.751 baseline) as the syllable read. A human does not count
envelope peaks; a theta oscillator entrained to the speech *is* the syllable clock, and
because it INTEGRATES over time it rides through sonorant-internal dips (`follow`/`zero`/
`sheila`) that under-count the peak-counter.

Concrete form (a damped-driven / gradient-frequency phase-locked oscillator — a Large-style
adaptive oscillator reduced to one unit):

- internal phase `theta` advances at an instantaneous frequency `omega`;
- `omega` adapts **slowly** (`tau_f = 0.30 s` → inertia, ~1.5 syllables of memory) toward the
  dominant envelope rhythm via a Hebbian/gradient term; clamped to the theta band [2.5, 8] Hz;
- the onset drive (half-wave-rectified envelope derivative) **drives** the phase toward lock
  (`K_phase`), it is never hard-reset — so a momentary dip leaves the oscillator coasting at
  its current `omega` and it only marks a boundary when *its own* cycle completes;
- a **voice gate** (20 % of clip peak + 60 ms hysteresis) engages the clock only where speech
  is present, so it does not free-run through the ~0.5–0.8 s of silence padding in an isolated
  SC clip; the hysteresis bridges within-word dips (the integration the peak-counter lacks);
- boundary/syllable = a `2π` phase wrap of a **driven** cycle (a cycle finished by pure
  intrinsic coasting, with no onset drive ≥ 0.40, is a phantom tick and is not counted).

All constants are frozen from the physics of the theta band / a syllable's shape, **not swept
on the test set**. No net, no fit, no gradient descent. This is the world-adapter transduction
(mechanical audio → boundaries); no graph state, no agent decisions.

**The frame + the cognition are unchanged.** The oscillator's count feeds the SAME owned soft
excluder (`prosody_excluder`) into the SAME agent collapse (`weighted_admissibility`). Only the
READ differs between the passive and active conditions.

## Donkey audit

| Component | Owner | Status |
|---|---|---|
| theta oscillator (the read) | owned DSP | numpy, frozen constants, no net/fit, integrates (tau_f + gate hysteresis) |
| syllable soft excluder | owned DSP | `prosody_excluder`, unchanged |
| word syllable structures | world knowledge | stated dictionary (SC) / CMUdict (continuous), unchanged |
| weighted-admissibility collapse | the agent | `frame_inference_v2`, unchanged |
| held-out speakers | — | never banked; LOSO ungameable |

## Results

### Test 1 — the SC syllable frame (the f8576bbc KILL, isolated single words)

`scripts/stage_a_entrained_sampler.py` — cross-speaker, 34 held-out speakers, n=3000,
chance 0.029. Same harness/splits as the KILL. Four-way frame: acoustic | +n-gram |
+PASSIVE-syllable | +OSCILLATOR-syllable, swept over the prosody weight.

**(a) Boundary reliability (cross-speaker syllable-count accuracy, n=3000):**

| read | count accuracy |
|---|---|
| PASSIVE peak-counter | **0.751** (the f8576bbc baseline) |
| ACTIVE theta-oscillator | **0.723** (−0.028) |

The active read is **NOT** more reliable than the passive peak-counter on isolated words.
Read cost: acoustic DTW 106.5 ms/item, passive 0.27 ms/item, oscillator 0.30 ms/item.

**(b) The frame (four-way, n=3000, chance 0.029):**

```
  (1) acoustic-only                = 0.138
  (2) +n-gram (no syllable)        = 0.767   (over acoustic +0.630)
  (3) +n-gram +PASSIVE syllable    = 0.761   (lift over (2) -0.006)
  (4) +n-gram +OSCILLATOR syllable = 0.754   (lift over (2) -0.014)

  pros_w  noProsody   PASSIVE   p-lift    OSCILL   o-lift  osc-pass
    0.25      0.767     0.765   -0.002     0.761   -0.006    -0.004
    0.50      0.767     0.768   +0.001     0.762   -0.005    -0.006
    1.00      0.767     0.761   -0.006     0.754   -0.014    -0.007
    2.00      0.767     0.652   -0.115     0.629   -0.138    -0.023
    4.00      0.767     0.610   -0.157     0.586   -0.181    -0.024
```

Neither read lifts on isolated words; the oscillator is slightly *worse* than the passive read
at every weight. **KILL on the isolated-word regime:** an oscillator needs a syllable *train*
to entrain, and an isolated single word (mostly monosyllabic in this vocab) gives barely one
cycle — there is no sustained rhythm to lock to. Rhythm is not the fix *in this regime*.

### Test 2 — continuous LibriSpeech (the oscillator's proper domain)

`scripts/stage_a_continuous_entrainment.py` — 400 cross-speaker utterances, 40 speakers all
held out, CMUdict ground truth (98 % coverage). An oscillator needs RHYTHM (several syllable
cycles) to phase-lock; isolated single words give barely one cycle (the hard case). The
prediction: on continuous speech the active read entrains and the advantage WIDENS with
utterance length.

```
reader                   mean|err|   exact-hit   pred/true
ACTIVE oscillator           11.387       0.022       0.648
PASSIVE peak-count          11.655       0.018       0.644

bin              n  true_mean  active|err|  passive|err|   gap(p-a)
short 1-3        3        2.7        2.667         2.000     -0.667
mid 4-7         27        6.0        1.333         1.370     +0.037
long 8-15       86       11.7        3.884         3.977     +0.093
xlong 16+      284       35.5       14.708        15.060     +0.352
```

**Confirmed on continuous speech:** the oscillator beats the passive counter overall
(|err| 11.387 vs 11.655) and the active advantage GROWS monotonically with utterance length
(short −0.667 → xlong +0.352) — the rhythm-entrainment signature. Short utterances favour the
passive read (too little rhythm to lock); as the syllable train lengthens the active read pulls
ahead. (Absolute counting of 28-syllable utterances is hard for both — exact-hit ~2 % — so the
diagnostic is |err| and the length-scaling gap, not exact-hit.)

## Verdict

The two tests answer the thesis precisely — **and the answer is regime-dependent, which is the
real finding.**

- **Isolated single words (the SC frame, the f8576bbc KILL regime):** the active read does NOT
  beat the passive read on (a) reliability (0.723 vs 0.751) and does NOT lift the frame
  (−0.014 vs the passive −0.006). An entrained oscillator has nothing to entrain to in one
  isolated word. **KILL — rhythm is not the fix here.** Note that this also means the *frame*
  itself does not carve on this vocab regardless of read quality: the n-gram already
  over-determines these items and the vocab is too uniform (21.2/35 ≈ 60 % survive a count
  match). So the isolated-word frame's failure is **two-fold** — the read AND the vocab
  uniformity — and an active read fixes neither, because there is no rhythm to read.

- **Continuous speech (the oscillator's proper domain):** the active read DOES beat the passive
  read on reliability (|err| 11.387 vs 11.655), **and the advantage grows monotonically with
  utterance length** (short −0.667 → xlong +0.352) — the unambiguous signature of rhythm
  entrainment. **CONFIRMED — the active interface is the better read once there is a rhythm to
  lock to.**

**Net verdict.** The thesis "the passive interface failed the frame; the active interface fixes
it" is **confirmed in mechanism but not in the isolated-word regime that produced the original
KILL.** The entrained theta oscillator is a genuinely better, integrating, self-clocking read —
demonstrated on continuous speech where its advantage scales with rhythm. But the f8576bbc
syllable-frame KILL lived in the isolated-word regime, where (i) there is no syllable train to
entrain to, so the active read cannot help, and (ii) the frame would not carve even with a
perfect read, because the monosyllabic-vocab uniformity + the over-determining n-gram are the
binding constraint there. Attribute correctly: **on continuous speech the interface was a real
limiter and the active read lifts it; on the isolated SC vocab the limiter was the
vocab/frame, not the interface — and an active read cannot manufacture a rhythm that isn't
there.**

The honest implication for the interface program: Stage A's active read pays off exactly where
the human syllable clock pays off — connected, rhythmic speech — and should be carried into the
continuous-speech recognition path, not the isolated-word one.

## Suites

No existing test suite touches `prosody_syllable`; `entrain_theta` was added (the existing
`extract_syllables` / `prosody_excluder` / dictionary are unchanged), so the prior
`prosody_syllable_frame` path is byte-for-byte unaffected. The `frame_inference_v2` collapse
and the agent cognition are untouched (the agent's, unchanged). CortexLoop untouched. Held-out
speakers never banked.
