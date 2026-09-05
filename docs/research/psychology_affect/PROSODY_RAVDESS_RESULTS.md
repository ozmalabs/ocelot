# FELT-PROSODY × RAVDESS — results (block 295000)

Pre-registration: `PROSODY_RAVDESS_PREREG.md`, committed BEFORE any confirmatory
measurement. The external ground-truth regions (§2), the FIXED affect→knob map
(§3, Arm A), and the FIXED feature vector + prior weight λ=1.0 + blind twin +
classifier + split + metric (§4, Arm B) were all frozen there. Affect→prosody
generator: `domains/prosody_generation.py`. Confirmatory measures:
`scripts/prosody_generation_measure.py` → `results/prosody_ravdess/generation.json`
(Arm A); `scripts/prosody_parsing_lift_measure.py` →
`results/prosody_ravdess/parsing_lift.json` (Arm B). Judge = the substrate's OWN
prosody extractor (`runners/dsl/python/substrate_rs/communication.py`, READ-ONLY).

**HEADLINE (the honest two-arm verdict on "does system-1 felt-prosody earn its
place").**

- **ARM B (PARSING LIFT): STRONG POSITIVE, significant, speaker-independent.**
  On the REAL held-out RAVDESS actors (17–24), the felt-prosody vector
  `[energy, f0_mean, contour]` lifts binary AROUSAL classification from the blind
  twin's **67.0 %** to **84.0 %** — a **+17.0 % lift, bootstrap 95 % CI
  [+10.8 %, +23.3 %], excluding zero.** The felt signal converts into real,
  measured parsing lift over a byte-identical control. **The felt-prosody signal
  earns its place on the parsing side.**

- **ARM A (GENERATION): PARTIAL — affect-appropriate on the axis the synthesizer
  can move (f0/pitch), blocked on energy by a synthesizer limit.** The
  affect-driven digit renders re-analyze with **f0_mean monotone in the
  pre-registered arousal ordering (6/7 adjacent pairs correct, 0.857)**, HIGH-mean
  f0 **279.6 Hz** clearly above LOW-mean **177.7 Hz** (gap **+101.8 Hz**),
  CI-separated from the flat baseline for 4/8 emotions, and **angry lands squarely
  in its own HIGH region and is nearest its own region centre (3.4 Hz).** BUT the
  synthesizer **peak-normalizes every buffer**, so re-analyzed **energy is
  saturated (~0.30, spread 0.029) and carries no arousal signal** — the second
  reliable axis is unusable on synthetic output. So affect-driven pitch prosody
  is genuine and affect-appropriate; the energy axis and the absolute-f0 landing
  are limited by the synth.

**Overall:** system-1 felt-prosody **gives a real, significant parsing lift
(Arm B, +17 pts, held-out)** and **drives affect-appropriate PITCH prosody
(Arm A, monotone in arousal, HIGH≫LOW)** — but only on the arousal axis, only on
pitch for generation (energy saturated by the synth), and NOT on valence (the
pre-registered §0 limit). A genuine, honestly-scoped positive-on-B /
partial-on-A result. **This is a CAPABILITY / mechanism demonstration**, not an
empirical claim about human emotion encoding.

## The mechanism (named)

The affect coordinate is the graph's OWN read-off, not a Python dict. The
generator drives a live `ModulatorState` into each emotion's `emx_*` region
(reusing the established modulator spine — `drives` + `modulators` seeds, the
per-emotion motivational configuration from `modulator_emergence_measure.CANON`),
ticks the substrate, and reads `ms.valence` / `ms.arousal_band` back off the
graph (`source=substrate` on every row). Those substrate-computed axes feed the
FIXED monotone map (`f0_hz = 140 + 160·a`, `dur_s = 0.60 − 0.30·a`,
`ta_frac = 0.11 − 0.10·a`, contour by arousal band) and a per-frame f0 CONTOUR
track. The synthesizer is the substrate's OWN `build_speech_forward`; because its
Rust primitive takes a SCALAR f0, the contour is realised by WRAPPING `forward` —
rendering the digit segment-wise at the per-frame f0 and concatenating with
raised-cosine crossfades. **`projection.py` is not edited; no Python computes the
emotion label or the judge's verdict; no Rust; no shaping.**

Arm B reads the judge's own features over the vendored wavs and fits a frozen
logistic regression (C=1.0, both feature blocks standard-scaled — the λ=1.0 prior
weight) on TRAIN actors, evaluated on TEST actors. The classifier is implemented
in numpy so the measure runs with only stdlib `wave` + numpy (no
sklearn/soundfile/scipy, which are absent in this env).

## ARM A — produced vs pre-registered region (re-analyzed by the judge)

Per emotion: affect coordinate READ OFF the substrate → FIXED knobs → synthesized
digit → RE-ANALYZED f0_mean (bootstrap 95 % CI over the 10 digit carriers). Flat
baseline f0_mean = **205.3 Hz** [190.6, 218.7].

| emotion | emx (substrate) | knob f0 | produced f0 [CI] | arousal class | f0 region | landed own? | nearest region | CI-sep from flat? |
|---|---|---:|:--:|:--:|:--:|:--:|:--:|:--:|
| calm      | bliss   | 164 | 175.5 [166, 188] | LOW  | LOW  | **✓** | calm (✓)  | ✓ |
| neutral   | —       | 170 | 180.0 [172, 191] | LOW  | LOW  | **✓** | calm (✓)  | · |
| sad       | sadness | 173 | 184.1 [175, 196] | MID  | LOW  | —     | calm      | · |
| disgust   | disgust | 210 | 224.6 [216, 235] | MID  | LOW  | —     | calm      | · |
| surprised | surprise| 230 | 254.1 [236, 277] | MID  | LOW  | —     | calm      | ✓ |
| happy     | joy     | 236 | 269.0 [244, 303] | HIGH | LOW  | ✗     | calm      | ✓ |
| fearful   | fear    | 212 | 225.1 [216, 236] | HIGH | LOW  | ✗     | calm      | · |
| angry     | anger   | 279 | 344.6 [298, 399] | HIGH | **HIGH** | **✓** | **angry (✓)** | ✓ |

- **f0 tracks affect arousal (the headline generation result):** monotone
  fraction **0.857**; HIGH-mean f0 **279.6** ≫ LOW-mean **177.7** (gap +101.8 Hz);
  `verdict_arousal_monotone = verdict_high_above_low = True`. The mapping REACHES
  the arousal-direction structure of human prosody on the pitch axis.
- **In-region hit rate (HIGH/LOW, f0 axis): 3/5 = 0.60.** calm, neutral land LOW;
  angry lands HIGH. happy and fearful miss the strict ≥320 Hz HIGH threshold.
- **Nearest-own arousal rate: 0.375.** The synth's absolute f0 sits ~50–90 Hz
  BELOW the RAVDESS region centres (real actors are higher-pitched than the
  digit-carrier synth), so the nearest-region metric defaults toward the calm
  centre for the mid band — an absolute-scale offset, not a direction error (the
  DIRECTION is correct, per the monotone fraction).
- **fearful lands LOW, not HIGH** — because the substrate's OWN `emx_fear` region
  has *decayed threat precision* → a LOW `arousal_band`. This is the substrate's
  genuine affect computation faithfully propagated (the felt-arousal read), not a
  mapping bug. It is exactly the fear=low/anxiety=high dissociation the modulator
  seed encodes.

### The energy limit (HONEST, pinned)

`produced_energy` is **~0.30 for every emotion** (spread **0.029**), because the
Rust synthesizer peak-normalizes each buffer to [−0.9, 0.9]. The RAVDESS regions
require BOTH `energy ≥ 0.010` AND `f0_mean ≥ 320` for HIGH; synth energy always
clears 0.010 (it sits at 0.30) but carries **no between-emotion arousal signal**.
So the strict two-axis region is not testable on synthetic output — landing is
scored on f0_mean, the axis the synth CAN move. **This is a property of the
substrate's own renderer, reported straight, not a flaw in the affect→knob map.**

## ARM B — parsing lift on real held-out RAVDESS actors

Binary AROUSAL: HIGH {angry, fearful, happy} vs LOW {calm, neutral}. TRAIN actors
01–16 (n=960 total, 288 test-binary on 17–24). Logistic regression, C=1.0, both
blocks standard-scaled (λ=1.0). Bootstrap 95 % CI over the held-out test samples.

| model | features | held-out accuracy |
|---|---|---:|
| **FELT** (the test)   | `[energy_mean, f0_mean, contour]` | **0.840** |
| **BLIND** (the twin)  | `[duration_s, zcr]`               | **0.670** |
| majority-class baseline | —                               | 0.667 |

> **LIFT = felt − blind = +0.170 (17.0 pts), 95 % CI [+0.108, +0.233], excludes
> zero → SIGNIFICANT.** `verdict_positive_lift = verdict_lift_significant = True.`

- The blind twin (`duration + zcr`) barely beats the majority-class floor
  (0.670 vs 0.667) — duration/ZCR carry essentially no arousal signal, exactly as
  the §0 caveat pre-registered.
- **Reliable-axis sign check (point-biserial with the HIGH label, held-out):**
  energy **+0.481**, f0_mean **+0.376** — both POSITIVE, the literature-correct
  arousal direction. `verdict_reliable_axes_sign_correct = True.`
- **Secondary 8-way (expected LIMITED, per §0):** felt **0.333** vs blind
  **0.210** vs chance **0.125**. Felt beats blind and chance, but is far from the
  binary-arousal accuracy — valence is NOT separated, as pre-registered. Reported
  as the weak secondary, never the headline; no leakage audit triggered (it is
  low, as expected).

## THE JUDGE GATE (re-asserted on the TEST split)

On real held-out actors (17–24), the judge's own energy for **angry ≫ neutral**
(the reliable arousal axis carries real emotion signal — the premise of both
arms). Asserted in the test with a wide margin (angry > 2× neutral). This is the
task-1 gate, re-confirmed on the held-out speakers.

## THE TWO-ARM VERDICT

- **Arm A — PARTIAL PASS (affect-appropriate pitch prosody).** Affect-driven
  contour+scalar prosody, driven through the real substrate affect state, lands
  its re-analyzed f0_mean in the arousal-correct direction (monotone; HIGH≫LOW;
  angry in-region and nearest its own centre; 4/8 CI-separated from flat). It does
  NOT land the strict two-axis region because (i) synth energy is saturated by
  peak-normalization and (ii) the absolute f0 sits below the real-actor region
  centres. **Genuine affect-appropriate PITCH prosody on digit carriers; the
  energy axis and valence are honest limits.**
- **Arm B — PASS (significant held-out lift).** The felt-prosody signal gives a
  **+17-pt** binary-arousal parsing lift over the blind twin on speaker-
  independent held-out actors, CI excluding zero, with the reliable axes signed
  correctly. **The felt signal earns its place on parsing.**
- **Overall — system-1 felt-prosody DOES give lift (Arm B, strongly) and DOES
  enable affect-appropriate prosody generation (Arm A, on pitch/arousal).** The
  honest scope: AROUSAL only (not valence, §0), pitch-only for generation (energy
  saturated by the synth), digit carriers for Arm A (the synth is locked to
  `GESTURE_SCORES`). A partial-A / strong-B result — not forced to a full pass.

## Test result

`tests/test_prosody_ravdess_migrated.py` — **19 passed.** Surrounding
emotion/affect/qualia surface GREEN: `test_marshmallow_migrated +
test_bouba_kiki_sound_symbolism_migrated + test_trait_anxiety_interpretation_
migrated + test_mere_exposure_social_migrated + test_qualia_space_migrated +
test_qualia_schema` → **63 passed.** `tests/test_communication.py` **cannot be
collected** because it does `import av` and `av` is absent in this env — a
**pre-existing environment failure, NOT this rung's** (my code uses only stdlib
`wave` + numpy so it runs). Likewise `soundfile`/`sklearn`/`scipy` are absent and
deliberately not depended on.

## G-discipline — PASS

- Canonical `_native.abi3.so` md5 **a32ed336662eaa9eb6df27b7112541ac** —
  UNCHANGED. NO Rust (`runners/dsl/src/*.rs` untouched); the JUDGE
  (`communication.py`) and `GESTURE_SCORES` READ-ONLY; toolbox solvers / frozen
  seeds untouched.
- **No new auto-loaded seed** — this rung authors no seed file
  (`prosody_generation.py` has no `load_seed_manifest` / `add_production`), so
  `load_all_seeds` sees nothing new and the base tree is **byte-identical when the
  affect mapping is absent (default == today)**.
- **Glass-box source-audit clean:** no graph-rewrite driver / matcher /
  rule-builder; no reward/punishment shaping (`.fit(` only via `np.polyfit`, which
  is DSP, not a trained model). The affect→knob map is a fixed function of a fixed
  affect coordinate, never learned.
- **Data:** RAVDESS present (1440 wavs) + `data/ravdess/ATTRIBUTION.md`
  (CC-BY-NC-SA 4.0, Livingstone & Russo 2018). The wavs are gitignored (`data/`),
  exactly as `data/fsdd/` is; **only the attribution note is committed, not the
  ~200 MB of audio.**

## Honest residuals & claim separation

- **Capability vs empirical.** A MECHANISM demonstration: a small felt vector
  drives affect-appropriate pitch prosody (A) and lifts arousal parsing (B),
  glass-box, against real external RAVDESS data with the substrate's own extractor
  as judge. NOT a claim about how humans encode/decode emotion.
- **Arousal, not valence.** Both arms are scoped to arousal (energy + f0_mean).
  Valence (happy vs angry, both high-arousal) is NOT separated — the pre-registered
  §0 limit, visible in the 8-way secondary (0.333).
- **Arm A energy is saturated by the synth's peak-normalization**; generation is
  demonstrated on the pitch axis only. The absolute synth f0 sits below the
  real-actor region centres, so nearest-region (0.375) understates the
  direction-correct result (monotone 0.857). These are synthesizer/carrier limits,
  not affect-map errors.
- **Different carriers per arm (by design):** Arm A synthesizes DIGIT words (the
  only carriers `GESTURE_SCORES` supports); Arm B runs on REAL RAVDESS sentences.
  Neither pretends the other's carrier (prereg scope split).
- **Prior-art posture.** That arousal drives F0/energy/rate is Banse & Scherer /
  Scherer; that prosody helps SER is established. The delta is the SAME felt
  vector serving both a generation map (into the arousal-correct direction) and a
  significant held-out parsing lift, on this glass-box substrate, with the affect
  coordinate read off the real ModulatorState and every threshold/weight fixed
  before measuring.
