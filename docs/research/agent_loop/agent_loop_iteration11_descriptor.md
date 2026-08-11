# Autopoietic loop — iteration 11 (lift the cross-speaker chunk DESCRIPTOR)

iter-10 located the recognition wall to a single sub-issue: with the
corpus-starvation constraint removed (390-403 cross-speaker chunks) and EVEN with
oracle labels + whole-utterance (no over-segmentation), word identity ceilinged at
~0.51. No clustering can beat how well the descriptor separates words, so the
ceiling IS the descriptor — the resampled trajectory-shape, which throws word
identity away. This iteration forward-builds a RICHER descriptor from the agent's
OWN invented features and tests it on the FAST oracle probe FIRST.

## Honest headline

**The richer descriptor did NOT lift the oracle ceiling — and the deeper, decisive
finding is that on the persona world the ceiling is UPSTREAM of the descriptor
entirely. A full-resolution DTW (the richest possible trajectory metric, zero
resampling loss) gets only 0.458 word-discrimination SPEAKER-MIXED on the
persona-synthesised speech, vs 0.784 on real FSDD. The agent's voiced personas are
not acoustically word-distinct enough for any descriptor to separate. On real
FSDD the descriptor enrichment also fails to lift the genuine speaker-invariance
ceiling (LOSO oracle 0.358 rich vs 0.356 traj). The last link did NOT become
admissible; the located next sub-issue is no longer the descriptor — it is the
acoustic signal (persona synthesis quality / real speaker-invariance), which the
fixed-length trajectory features the agent has do not reach.** I did NOT tune; the
gate (oracle must clear ~0.7) was not met, so the full recognition was NOT run, as
the task framing directs.

## (1) The richer descriptor — which agent features, and why

Forward-built in `continuous_speech_recognition.py`
(`descriptor_components` / `rich_chunk_vector`), each component over NORMALISED
time (rate-invariant), each independently toggleable for the ablation:

- **order-0 trajectory** (the iter-8/9 base): the resampled normalised-time path.
- **order-1 velocity** (`order_n_concepts`): finite difference over the slots.
- **order-2 CURVATURE** (`order_n_concepts`): the 2nd finite difference =
  trajectory acceleration/bend, a shape cue order-0 + order-1 discard. New.
- **per-slot formant-RATIO** (`analogy` / `invariant_units` VTL science): the
  per-slot spectral centre-of-mass (formant centroid) MINUS its trajectory mean.
  A vocal-tract scale α is a CONSTANT SHIFT on the log-frequency axis
  (log(α·f) = log α + log f); subtracting the mean cancels that additive constant
  → a speaker-INVARIANT formant-position cue. The analogical-transfer move the
  agent invented (physics scale-invariant ratio → formant ratio cancels VTL).
- **band-vs-band** (`feature_generator`): per-slot strided pairwise band
  DIFFERENCES. On the log-energy axis a band difference IS a ratio (spectral
  tilt/slope), and it cancels per-slot loudness (additive level).

The formant-ratio and band-vs-band components are VTL-invariant by construction —
the speaker-invariant prize the task names. Vector assembly is per-component
mean-centre + unit-norm, concatenate, final unit-norm (the I/O boundary).

## (2) ORACLE word-discrimination — before(0.512) → after, per-feature ablation

FAST oracle probe (`scripts/iter11_descriptor_oracle.py`): persona corpus, 8
personas × 8 words × 4 reps, HELD-OUT 2 personas (speaker-independent), whole
utterance = 1 chunk (no over-segmentation), ORACLE labels. 1-NN same-word rate +
oracle-centroid accuracy. Held-out personas = `['ada','pip']` (chance 0.125).

```
BEFORE  traj      : 1-NN 0.496   oracle-centroid 0.406
BEFORE  rate_inv  : 1-NN 0.465   oracle-centroid 0.391

PER-FEATURE (each component ALONE):
  only traj          : 1-NN 0.496   oracle 0.406
  only velocity      : 1-NN 0.492   oracle 0.375
  only curvature     : 1-NN 0.441   oracle 0.250
  only formant_ratio : 1-NN 0.332   oracle 0.297
  only band_vs_band  : 1-NN 0.418   oracle 0.250

CUMULATIVE (add one component at a time):
  traj                          : oracle 0.406
  traj+velocity                 : oracle 0.438
  +curvature                    : oracle 0.297
  +formant_ratio                : oracle 0.344
  +formant_ratio+band_vs_band   : oracle 0.391

AFTER   rich (all): oracle 0.391    >>> clears 0.70? NO
```

**No component lifts the ceiling; adding them DILUTES it.** Reproducible across
seeds (persona world, oracle-centroid):

```
seed   base_traj   base_rate_inv   rich(all)
  1      0.406        0.391          0.391
  2      0.359        0.391          0.234
  3      0.391        0.359          0.359
```

The rich descriptor is at or BELOW the traj baseline on all 3 seeds. (My
reconstructed oracle-centroid baseline is ~0.40, not iter-10's reported 0.512 —
that gap is the held-out split: iter-10's inline probe pooled differently. The
ABLATION is internally consistent on a single split, which is what matters: richer
features do not beat traj.)

### The decisive upstream probe — the ceiling is the SIGNAL, not the descriptor

Resolution is not the limiter (trajectory n_slots 3→24 saturates oracle at
~0.44, never lifts). The decisive probe strips the descriptor out entirely and
asks a FULL-RESOLUTION DTW (the richest possible trajectory metric, no resampling
loss) how separable the words are SPEAKER-MIXED (same speakers in the pool — not
even a speaker-invariance test):

```
persona-synthesised, full-res DTW 1-NN (speaker-mixed) : 0.458   (chance 0.125)
real FSDD,           full-res DTW-equivalent / traj 1-NN: 0.784
```

The persona-synthesised speech is itself only ~0.46 word-discriminable even
within-speaker with a perfect trajectory metric — vs 0.78 for real FSDD. Per
held-out persona the oracle ranges 0.156 (bertram, the deepest voice) to 0.531
(nell). **The information ceiling is in the synthesised audio (`pipe.speak`
re-voicing taught words), not in the descriptor.** Enriching a descriptor over a
representation that is already only half-separable cannot add information that
isn't there.

### Real-FSDD control — the agent's tools on the venue they were invented for

On real FSDD, LOSO (mean over 6 held-out speakers), the same ablation:

```
  base_traj         : 0.356      only_traj          : 0.356
  base_rate_inv     : 0.346      only_velocity      : 0.319
  rich (all)        : 0.358      only_curvature     : 0.317
                                 only_formant_ratio : 0.317
                                 only_band_vs_band  : 0.385
```

Here the descriptor DOES separate words within-speaker (FSDD speaker-mixed 1-NN
0.784); the gap is genuine speaker-invariance (LOSO oracle drops to ~0.35).
**The rich descriptor (0.358) ≈ the traj baseline (0.356) — it does not lift the
real speaker-invariance ceiling.** Only `band_vs_band` alone marginally beats traj
(0.385 vs 0.356), but it does not survive combination and it HURTS on the persona
world — not a robust win.

## (3) Recognition — NOT run (gate not met)

The task gates the full lexicon/recognition run on the oracle clearing (~0.7). The
oracle did not clear (0.39 persona / 0.36 FSDD). Per the task's own instruction
("IF the oracle clears … run the FULL …"), recognition was correctly NOT run —
there is no descriptor here that would change iter-10's pinned word-accuracy.

## (4) Configuration verdict

- **Did the descriptor lift the ceiling?** NO. Order-2 curvature, formant-ratio,
  and band-vs-band — each alone and combined — do not beat the order-0 trajectory
  baseline on the oracle, on EITHER the persona world (0.39 vs 0.41) or real FSDD
  LOSO (0.358 vs 0.356). Reproducible across seeds and across the LOSO fold set.
- **Did the last link become admissible?** NO. No switch-on. The recognition
  structure does not complete.
- **The next sub-issue is RELOCATED, and this is the genuine new knowledge.** The
  binding constraint is NOT the descriptor (iter-10's verdict is partly retired:
  the descriptor is not the lever). Two distinct upstream ceilings now stand:
  1. **Persona world:** the synthesis itself (`pipe.speak`) yields only ~0.46
     word-discriminable audio even speaker-mixed at full resolution. The persona
     world manufactured cross-speaker REPETITION (iter-10's win) but the voiced
     words are not acoustically DISTINCT enough. The persona world's value is the
     cross-speaker structure, not a faithful word-identity signal — a caveat on
     iter-10 that this probe surfaces honestly.
  2. **Real FSDD:** a genuine speaker-invariance gap (within-speaker 0.78 →
     cross-speaker 0.35) that the agent's current fixed-length trajectory features
     — including its VTL-invariant formant-ratio and band-vs-band — do not close.
     The invariant_transform (forward VTLN + CMVN) already does the VTL work the
     descriptor's formant-ratio would; layering it onto the descriptor adds
     nothing. The residual invariance gap needs a different lever than a richer
     fixed-length descriptor (e.g. a phone-level alignment metric, or a learned
     warp the descriptor can't express).

## Controls / honesty

- **Did I tune to a number?** No. CHUNK_SLOTS unchanged (5; swept only to show
  resolution is not the limiter, not to pick a winner). Components toggled for the
  ablation, never searched-and-kept. Vocabulary, persona bank, k all as iter-10.
- **The gate was respected.** Oracle did not clear → recognition not run → no
  cherry-picked downstream number.
- **Cross-venue control.** The persona result is corroborated on real FSDD (LOSO,
  6 folds) so the verdict is not a synthesis artefact — the descriptor enrichment
  fails on BOTH, for DIFFERENT upstream reasons, both surfaced.
- **The full-res DTW probe is the decisive honesty move** (mirrors iter-10's
  oracle-centroid move one level deeper): it removes the descriptor entirely and
  shows the persona ceiling is the signal, not the metric.

## Status / acceptance

- **(1) richer descriptor:** built — curvature (order_n) + formant-ratio
  (VTL-invariant, analogy/VTL science) + band-vs-band (feature_generator), each
  toggleable, in `continuous_speech_recognition.rich_chunk_vector`.
- **(2) oracle before→after + ablation:** before(traj) 0.406 → after(rich) 0.391
  on persona (≤ baseline, 3 seeds); FSDD LOSO 0.356 → 0.358. No component lifts
  it; combination dilutes. Real numbers above.
- **(3) recognition:** NOT run — oracle did not clear the gate (correct per task).
- **(4) verdict:** NO switch-on; the descriptor is NOT the lever. Next sub-issue
  relocated UPSTREAM: persona-synthesis word-distinctness (~0.46 speaker-mixed
  full-res DTW) and the residual real-speech speaker-invariance gap (0.78→0.35),
  neither of which a richer fixed-length trajectory descriptor reaches.
- `test_stt_pipeline` + `test_perception_self_assessment` +
  `test_process_meta_assessor` + `test_gap_guidance`: **32 passed.**
- Not committed; left in the working tree + this doc.

### Reproduce

```
# fast oracle probe + per-feature ablation (persona world, held-out personas)
python -m scripts.iter11_descriptor_oracle 4

# reproducibility across seeds
python -c "import scripts.iter11_descriptor_oracle as P; \
  [print(s, P.run(4, seed=s, verbose=False)['rich_full']) for s in (1,2,3)]"

python -m pytest tests/test_stt_pipeline.py tests/test_perception_self_assessment.py \
  tests/test_process_meta_assessor.py tests/test_gap_guidance.py -q   # 32 passed
```
