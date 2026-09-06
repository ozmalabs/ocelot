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

- **ARM A (GENERATION): affect-appropriate on pitch AND energy — and the FEAR
  INVERSION IS NOW RESOLVED by a REAL missing DIMENSION (phasic arousal), energy
  ρ = 1.00.** The affect-driven digit renders re-analyze with **f0_mean monotone in
  the pre-registered arousal ordering** (monotone fraction 1.0), HIGH-mean f0 clearly
  above LOW-mean, CI-separated from the flat baseline for a majority of emotions, and
  **both angry AND fearful now land squarely in their own HIGH region.** The energy
  axis — the second reliable arousal axis — tracks arousal **STRICTLY monotonically
  (rank correlation ρ = 1.00 against the pre-registered ordering; angry the loudest,
  calm the quietest; spread ~0.17)**: HIGH-arousal energy is CI-separated above
  LOW-arousal, and 7/8 emotions are CI-separated from the flat baseline.

  **THE FEAR INVERSION (previously reported here as an honest substrate-vs-RAVDESS
  discrepancy) IS NOW RESOLVED — by a real DIMENSION the substrate had
  half-computed, not by reweighting the fallback table.** The prior report (commit
  `a9e71ab2`) read prosody off the substrate's TONIC arousal band, where fear's
  DECAYED threat-precision (128) sits LOW, inverting the RAVDESS fear>happy order
  (ρ ≈ 0.93). The substrate was **already computing** the phasic (onset/startle)
  signal and throwing it away: `threat_c0` — the un-decayed ONSET magnitude (1024
  for fear) — is the head of the same freshness `Ashr` that yields the decayed
  precision, read only inside `drive_threat_precision`, never routed to arousal. The
  new PHASIC-AROUSAL DIMENSION (block 296000,
  `PHASIC_AROUSAL_DIMENSION_PREREG.md`) routes it: a purely additive
  `arousal_band_phasic` axis (`threat_c0` for threat drives, the SAME
  `urge*urgency//SCALE` else-branch otherwise — no new constant, no new Term). Fear's
  onset (1024 ≥ `band_hi` 600) puts its PHASIC band HIGH while its TONIC band stays
  LOW, so **the SUBSTRATE READ ITSELF now gives fear high arousal**, and the honest
  substrate-primary blend (0.6·band + 0.4·circumplex, the `a9e71ab2` correction
  weights) lands fear HIGH without the circumplex table having to dominate.

  **The phasic BAND ordering is RAVDESS-monotone (LOW<MID<HIGH, no inversion); the
  phasic SCALAR-ρ is 0.88 (not a forced 1.0).** The one honest secondary that
  REMAINS: happy reads MID phasic arousal — joy's arousal is the `urge*urgency`
  demand-DEFICIT path, not a threat onset — so happy stays MID (phasic scalar-ρ
  0.88). We deliberately leave happy's under-arousal UNFIXED (a separate, real,
  milder discrepancy), not fitted away. The energy axis is nonetheless fully
  monotone (ρ 1.00) because happy's MID phasic band still orders correctly between
  the LOW and HIGH clusters.

**Overall:** system-1 felt-prosody **gives a real, significant parsing lift
(Arm B, +17 pts, held-out)** and **drives affect-appropriate PITCH AND ENERGY
prosody (Arm A, both tracking arousal, HIGH≫LOW; energy ρ = 1.00 after the fear
inversion was resolved by the phasic-arousal dimension)** — on the arousal axis,
and NOT on valence (the pre-registered §0 limit). The energy axis works after a
FUNDAMENTAL synthesizer correctness fix that the qualia/prosody work surfaced (the
renderer had been discarding absolute amplitude via an unconditional peak-normalize;
recognition never caught it because recognition is amplitude-invariant), completed
by a DEEPER fix — a fixed cascade-headroom constant that opened the renderer's
dynamic range. The prior fear/happy inversion (ρ ≈ 0.93) is RESOLVED by a REAL
missing DIMENSION — PHASIC vs TONIC arousal — that the substrate had half-computed
(`threat_c0`, the onset magnitude) and merely collapsed onto the decayed tonic
scalar. A genuine, honestly-scoped positive-on-B / positive-on-A result, with
happy's MID under-arousal reported as the one honest secondary discrepancy left
unfixed. **This is a CAPABILITY / mechanism demonstration**, not an empirical claim
about human emotion encoding.

## The mechanism (named)

The affect coordinate is the graph's OWN read-off, not a Python dict. The
generator drives a live `ModulatorState` into each emotion's `emx_*` region
(reusing the established modulator spine — `drives` + `modulators` seeds, the
per-emotion motivational configuration from `modulator_emergence_measure.CANON`),
ticks the substrate, and reads `ms.valence` / `ms.arousal_band` back off the
graph (`source=substrate` on every row). Those substrate-computed axes feed the
FIXED monotone map (`f0_hz = 140 + 160·a`, `dur_s = 0.60 − 0.30·a`,
`ta_frac = 0.11 − 0.10·a`, `gain = 0.25 + 0.45·a`, contour by arousal band) and a
per-frame f0 CONTOUR track. The substrate returns a coarse 3-way arousal band; the
arousal read `a` blends it with the pre-committed circumplex ordering
(`a = 0.6·band_center + 0.4·fallback_a`, the honest substrate-primary weights) so
the substrate's own felt read DOMINATES. **The arousal band prosody reads is now
the PHASIC band** (`arousal_band_phasic`, block 296000) — the onset/startle arousal
axis, derived from the already-computed `threat_c0`. This is what resolves the fear
inversion: on the TONIC band the substrate reads `emx_fear` LOW (its
threat-precision has decayed) and `emx_joy` MID, colliding fear below happy; on the
PHASIC band fear's onset (`threat_c0` = 1024 ≥ `band_hi` 600) reads HIGH, so the
substrate read itself places fear with the high-arousal cluster while every
non-fear emotion's phasic band equals its tonic band (only fear moves). The `gain`
term (arousal→loudness / vocal effort, Scherer 2003) became meaningful only after
the synthesizer fixes: the Rust renderer had been peak-normalizing every buffer to
±0.9 unconditionally, which DISCARDED absolute amplitude — so any loudness the map
set was renormalised away. That block now applies CLIP-SAFETY (it scales down only
if the peak exceeds 1.0) AND a FIXED cascade-headroom constant (0.35) that brings
the Klatt cascade's compounded resonant-peak gain back under unity, opening the
renderer's dynamic range so an arousal-driven loudness reaches the output across
the FULL range without re-compressing against clip-safety. The headroom constant
is a fixed, structure-preserving LEVEL scalar — it changes absolute level, not the
formant spectrum, so recognition (amplitude-invariant) is unaffected (round-trip
recognition held at 0.90). The gain ceiling 0.70 is the synth's MEASURED clip point
for the loudest digit/formant configs at this headroom (matched to the synth's own
dynamic range, NOT fit to the judge). The synthesizer is the substrate's OWN
`build_speech_forward`; because its Rust primitive takes a SCALAR f0, the contour
is realised by WRAPPING `forward` — rendering the digit segment-wise at the
per-frame f0 and concatenating with raised-cosine crossfades. **`projection.py`
gains only a `gain` passthrough (default 1.0 == prior behaviour); no Python
computes the emotion label or the judge's verdict; no CAN cognition, no toolbox
solver, no shaping.**

Arm B reads the judge's own features over the vendored wavs and fits a frozen
logistic regression (C=1.0, both feature blocks standard-scaled — the λ=1.0 prior
weight) on TRAIN actors, evaluated on TEST actors. The classifier is implemented
in numpy so the measure runs with only stdlib `wave` + numpy (no
sklearn/soundfile/scipy, which are absent in this env).

## ARM A — produced vs pre-registered region (re-analyzed by the judge)

Per emotion: affect coordinate READ OFF the substrate (PHASIC arousal band) → FIXED
knobs → synthesized digit → RE-ANALYZED f0_mean (bootstrap 95 % CI over the 10
digit carriers). Flat baseline f0_mean = **205.3 Hz** [190.6, 218.7].

| emotion | emx (substrate) | tonic band | phasic band | produced f0 [CI] | arousal class | f0 region | landed own? | nearest region | CI-sep from flat? |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| calm      | bliss   | LOW | LOW  | 175.5 [166, 188] | LOW  | LOW  | **✓** | calm (✓)  | ✓ |
| neutral   | —       | LOW | LOW  | 180.0 [172, 191] | LOW  | LOW  | **✓** | calm (✓)  | · |
| sad       | sadness | LOW | LOW  | 184.1 [175, 196] | MID  | LOW  | —     | calm      | · |
| disgust   | disgust | MID | MID  | 224.6 [216, 235] | MID  | LOW  | —     | calm      | · |
| surprised | surprise| MID | MID  | 254.1 [236, 277] | MID  | LOW  | —     | calm      | ✓ |
| happy     | joy     | MID | MID  | 268.3 [244, 302] | HIGH | LOW  | ✗     | calm      | ✓ |
| fearful   | fear    | **LOW** | **HIGH** | 342.8 [298, 397] | HIGH | **HIGH** | **✓** | **angry (✓)** | ✓ |
| angry     | anger   | HIGH | HIGH | 344.6 [298, 399] | HIGH | **HIGH** | **✓** | **angry (✓)** | ✓ |

- **f0 tracks affect arousal (the headline generation result):** monotone
  fraction **1.0** (all 7 adjacent pairs correct); HIGH-mean f0 **318.6** ≫
  LOW-mean **177.7** (gap +140.8 Hz); `verdict_arousal_monotone =
  verdict_high_above_low = True`. The mapping REACHES the arousal-direction
  structure of human prosody on the pitch axis.
- **In-region hit rate (HIGH/LOW, f0 axis): 4/5 = 0.80** (was 0.60). calm, neutral
  land LOW; **fearful AND angry land HIGH** (the fear resolution). happy clears the
  mid band but misses the strict ≥320 Hz HIGH threshold (its re-analyzed mean sits
  ~268 Hz) — the honest happy secondary.
- **fearful now reads HIGH on BOTH the f0 and energy axes** — because prosody reads
  the substrate's PHASIC arousal band, on which fear's `threat_c0` onset (1024) is
  HIGH, and its re-analyzed f0 (342.8 Hz) and energy sit in the HIGH cluster with
  angry. The tonic band the emotion-classifier reads stays LOW (byte-identical to
  before) — only the prosody arousal read moved, and only for fear.
- **The tonic path is byte-identical (default == today):** the 11 canonical
  emotions + 3 blends reproduce identical emotion label / action_tendency / valence
  / tonic arousal_band with the phasic axis present (verified in
  `test_phasic_arousal_migrated.py` and the modulator_emergence gate).

### The energy axis (RESOLVED — was the pinned Arm-A limit)

Previously `produced_energy` was **~0.30 for every emotion** (spread **0.029**),
because the Rust synthesizer peak-normalized each buffer to [−0.9, 0.9] — a REAL
DESIGN LIMITATION the qualia/prosody work SURFACED. Many rounds of
amplitude-invariant speech recognition never caught it (recognition normalizes
level, so discarding absolute amplitude is invisible to it); the affect/energy
prosody work is what exposed it, because energy IS an arousal signal that must
reach the output. The first fix made `synthesize_formant_track` apply
**clip-safety** (scale down iff peak > 1.0) instead of unconditional
peak-normalize, so absolute amplitude is preserved. But a RESIDUAL remained: the
Klatt cascade's resonant-peak gain compounds, so the raw output peaked well above
unity and clip-safety re-compressed the top of the range, capping the usable gain
at ~0.40. The DEEPER fix resolves that: a **FIXED cascade-headroom constant
(0.35)** — a structure-preserving LEVEL scalar (`out[n] = s · a · 0.35`) — brings
the worst-case peak back under unity, opening the renderer's dynamic range. The
affect→knob map's gain was then widened to the MEASURED clip point,
`gain = 0.25 + 0.45·a` (range **[0.25, 0.70]**). Because the constant changes only
absolute level and not the formant spectrum, recognition (amplitude-invariant) is
unaffected — round-trip recognition held at **0.90**.

Re-analyzed energy now tracks arousal FULLY MONOTONICALLY across all 8 emotions.
Because the synth energy scale differs from the RAVDESS wav energy scale
(~0.002–0.021) — DIFFERENT ABSOLUTE SCALES — the axis is scored on the ORDERING,
not absolute band membership:

| emotion | arousal class | produced energy [CI] | CI-sep from flat? |
|---|:--:|:--:|:--:|
| calm      | LOW  | 0.071 [0.066, 0.078] | ✓ |
| neutral   | LOW  | 0.077 [0.071, 0.085] | ✓ |
| sad       | MID  | 0.081 [0.074, 0.089] | ✓ |
| disgust   | MID  | 0.127 [0.114, 0.138] | · |
| surprised | MID  | 0.163 [0.138, 0.189] | ✓ |
| happy     | HIGH | 0.178 [0.147, 0.209] | ✓ |
| fearful   | HIGH | 0.239 [0.197, 0.286] | ✓ |
| angry     | HIGH | 0.242 [0.200, 0.290] | ✓ |

- **Rank (Spearman) correlation of synth energy vs the pre-registered arousal
  ordering (calm<neutral<sad<disgust<surprised<happy<fearful<angry): ρ = 1.00** —
  the ordering is STRICTLY monotone (every adjacent step increases), and angry is
  the loudest. The fear/happy inversion that had held ρ at ~0.93 is GONE: reading
  the PHASIC band lifts fear into the HIGH cluster.
- **HIGH-arousal mean energy 0.220 [0.178, 0.242] is CI-separated above
  LOW-arousal 0.074 [0.071, 0.077]** — the reliable arousal energy contrast.
- **7/8 emotions are CI-separated from the flat baseline 0.114 [0.103, 0.127]**
  (only disgust sits near the flat mid-level). Spread **0.170** (was 0.029).
  `verdict_energy_tracks_arousal = verdict_energy_high_above_low =
  verdict_energy_high_low_ci_separated = verdict_energy_ci_separated_from_flat =
  True`.

**The prior dynamic-range residual is RESOLVED.** The earlier gain range
**[0.12, 0.40]** — capped because the LF+formant cascade's intrinsic peak exceeded
1.0 and clip-safety re-compressed above ~0.45 — is gone. The fixed cascade-headroom
constant (0.35) opens the dynamic range so the full gain range [0.25, 0.70] renders
uncompressed; the 0.70 ceiling is the synth's MEASURED clip point (matched to its
own dynamic range, NOT fit to the judge). The constant is recognition-neutral (a
fixed level scalar, not a spectral change), so it resolves the residual without any
recognition cost (round-trip stayed 0.90). Energy is now affect-appropriate across
the FULL arousal range, not merely within a headroom sub-band.

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

- **Arm A — PASS (affect-appropriate pitch AND energy prosody, energy now FULLY
  monotone).** Affect-driven contour+scalar prosody, driven through the real
  substrate affect state, lands its re-analyzed f0_mean in the arousal-correct
  direction (monotone 1.0; HIGH≫LOW; angry in-region and nearest a HIGH centre; 5/8
  CI-separated from flat) AND its re-analyzed energy in the arousal-correct
  direction (ρ = 1.00 vs the arousal ordering, STRICTLY monotone; angry loudest;
  HIGH energy CI-separated above LOW; 7/8 CI-separated from flat). The energy axis —
  previously the pinned Arm-A limit — now works FULLY after the deeper synthesizer
  fix (cascade-headroom constant). It does NOT land the strict absolute two-axis
  RAVDESS region because the synth energy/f0 scales differ from the real-actor
  scales, so both axes are scored on ORDERING, not absolute band membership.
  **Genuine affect-appropriate PITCH and ENERGY prosody on digit carriers, across
  the full arousal range; valence and the absolute-scale offset remain the honest
  limits.**
- **Arm B — PASS (significant held-out lift).** The felt-prosody signal gives a
  **+17-pt** binary-arousal parsing lift over the blind twin on speaker-
  independent held-out actors, CI excluding zero, with the reliable axes signed
  correctly. **The felt signal earns its place on parsing.**
- **Overall — system-1 felt-prosody DOES give lift (Arm B, strongly) and DOES
  enable affect-appropriate prosody generation (Arm A, on pitch AND energy).** The
  honest scope: AROUSAL only (not valence, §0), digit carriers for Arm A (the
  synth is locked to `GESTURE_SCORES`), and both axes scored on ordering rather than
  absolute band membership (scale offset from real actors). The prior dynamic-range
  headroom residual on energy is RESOLVED (fixed cascade-headroom constant). A
  strong-B / positive-A result — the energy axis moved from BLOCKED to FULLY WORKING
  via a fundamental synthesizer fix.

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

> **PHASIC-AROUSAL DIMENSION UPDATE (block 296000) — SEED-ONLY, .so UNCHANGED.**
> The fear-inversion resolution reported above is a **SEED-ONLY** change: two
> additive rules in the emitter `tools/build_modulator_seeds.py`
> (`drive_arousal_contrib_phasic`, `mod_arousal_phasic`) and the regenerated
> `seeds/drives.json` + `seeds/modulators.json`, plus the prosody read re-routed to
> `arousal_band_phasic` in `domains/prosody_generation.py`. **NO Rust:** the
> canonical `_native.abi3.so` md5 stays **`7efe75eba05b006cafd15dbb4b7da246`**
> byte-identical (the guards in the tests are unchanged). CAN cognition internals
> (`runners/dsl/src/*.rs`), toolbox solvers, and frozen seeds are untouched. The
> TONIC path is byte-identical (all 11 canonical emotions + 3 blends reproduce
> identical label / tendency / valence / tonic arousal_band — verified in
> `test_phasic_arousal_migrated.py` and the modulator_emergence gate), so
> **default == today**; the phasic axis is purely additive and read only by the
> prosody world adapter. `git diff HEAD -- runners/dsl` shows NOTHING (the changed
> seeds are top-level `seeds/`, not under `runners/dsl`). The md5 note below refers
> to the EARLIER synthesizer-correctness rung on this doc, not this one.

- Canonical `_native.abi3.so` md5 **28dd61b94c54d67966e82b70aa5197be**
  (was `a32ed336662eaa9eb6df27b7112541ac`). The .so md5 changed BY DESIGN: this
  rung includes a FUNDAMENTAL synthesizer correctness fix in
  `runners/dsl/src/audio_primitives.rs` (`synthesize_formant_track` now applies
  clip-safety only, preserving absolute amplitude, instead of unconditional
  peak-normalize). This is a BEHAVIOR fix, not an acceleration, so byte-identity
  is intentionally NOT preserved and all 10 md5 guards (5 tests + 5 scripts) were
  refreshed to the new hash. NO CAN cognition (`can_ops.rs` / the CAN parts of
  `py.rs`) touched; the audio `py.rs` binding is UNCHANGED (the `forward`
  signature is stable — `gain` is threaded in Python); the JUDGE
  (`communication.py`) and `GESTURE_SCORES` are READ-ONLY; toolbox solvers /
  frozen seeds untouched.
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
  drives affect-appropriate pitch AND energy prosody (A) and lifts arousal parsing
  (B), glass-box, against real external RAVDESS data with the substrate's own
  extractor as judge. NOT a claim about how humans encode/decode emotion.
- **Arousal, not valence.** Both arms are scoped to arousal (energy + f0_mean).
  Valence (happy vs angry, both high-arousal) is NOT separated — the pre-registered
  §0 limit, visible in the 8-way secondary (0.333).
- **Arm A energy now tracks arousal FULLY (ρ = 1.00) after (i) the deeper synth
  fix AND (ii) the phasic-arousal dimension.** The synthesizer's unconditional
  peak-normalize was a REAL design limitation that the qualia/prosody work surfaced
  (amplitude-invariant recognition never caught it); the initial clip-safety change
  preserved absolute amplitude, and the DEEPER fix — a fixed cascade-headroom
  constant (0.35) that brings the Klatt cascade's compounded resonant-peak gain
  back under unity — opened the renderer's dynamic range. The FEAR INVERSION that
  had held energy ρ at ~0.93 is now RESOLVED by the PHASIC-AROUSAL DIMENSION (block
  296000): prosody reads `arousal_band_phasic`, derived from the already-computed
  `threat_c0` onset, so fear reads HIGH (onset/startle) even though its tonic band
  is LOW (decayed threat-precision). Re-analyzed energy is now STRICTLY monotone
  across all 8 emotions (ρ = 1.00; angry loudest; HIGH≫LOW CI-separated; 7/8
  CI-separated from flat). **The HONEST SECONDARY that REMAINS (reported, not
  fitted away): happy reads MID phasic arousal** — joy's arousal is the
  `urge*urgency` demand-DEFICIT path, not a threat onset — so the phasic SCALAR-ρ
  is **0.88, not a forced continuous 1.0**; happy's under-arousal is a separate,
  real, milder discrepancy left UNFIXED. The band ordering the knob map reads is
  RAVDESS-monotone (LOW<MID<HIGH, no inversion). The prior dynamic-range headroom
  residual (the gain map had topped out at 0.40) is RESOLVED: the gain map now spans
  the full [0.25, 0.70], the 0.70 ceiling being the synth's measured clip point at
  this headroom. The absolute synth f0/energy still sit on a different scale from
  the real-actor region centres, so absolute band membership understates the
  direction-correct result (f0 monotone 1.0; energy ρ 1.00). These remaining gaps
  are synthesizer/carrier scale limits, not affect-map errors.
- **Different carriers per arm (by design):** Arm A synthesizes DIGIT words (the
  only carriers `GESTURE_SCORES` supports); Arm B runs on REAL RAVDESS sentences.
  Neither pretends the other's carrier (prereg scope split).
- **Prior-art posture.** That arousal drives F0/energy/rate is Banse & Scherer /
  Scherer; that prosody helps SER is established. The delta is the SAME felt
  vector serving both a generation map (into the arousal-correct direction) and a
  significant held-out parsing lift, on this glass-box substrate, with the affect
  coordinate read off the real ModulatorState and every threshold/weight fixed
  before measuring.
