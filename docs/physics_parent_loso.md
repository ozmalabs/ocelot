# Physics-model varied-voice parent vs the cross-speaker (LOSO) gap

**Question.** The espeak parent is ONE synthetic voice. The agent has its OWN
source-filter / Klatt-LF voicebox (`audio_primitives.rs :: synthesize_from_trajectory`,
`synthesize_klatt_lf`) that can voice a word at arbitrary f0 / vocal-tract-length /
voice-quality. Hypothesis: a parent that teaches each digit across MANY synthetic
voices teaches the speaker-INVARIANT, so a held-out HUMAN speaker falls inside what was
taught and the cross-speaker LOSO gap (LOSO ~0.35 vs seen-speaker ~0.95) closes.

**Verdict: NO — honest STOP.** The voicebox exists and runs, and its synthesis is
internally self-consistent, but the agent **cannot recognise its own synthetic speech
against real human FSDD** in its current front-end feature space. Adding varied-voice
synthetic exemplars does **not** lift the human LOSO probe — it slightly hurts it. The
synthetic-vs-human domain shift dominates. The move is to fix the voicebox / front end,
**not** to wire the varied-voice parent and launch the long loop.

---

## (1) Voicebox VERIFIED to exist and run — but off-manifold vs real speech

Both physics-model synthesizers are present and exposed via PyO3 (after rebuilding the
stale `~/.local` `_native.abi3.so` from `runners/dsl/src` — the installed extension
predated these methods; rebuilt with `maturin build --release`):

- `synthesize_from_trajectory` — RBJ-bandpass source-filter voicebox (harmonic stack at
  f0, per-formant bandpasses). `py.rs:3345`, `audio_primitives.rs:434`.
- `synthesize_klatt_lf` — Klatt cascade resonators + Liljencrants-Fant glottal source +
  nasal antiresonance, the iter-40 upgraded forward model. `py.rs:3409`,
  `audio_primitives.rs:735`.

Both voice an A1-patch **trajectory** at any f0 / Q (+ vocal-tract-length via waveform
resampling, the persona world's VTL knob). Per-digit trajectories were extracted from
FSDD train clips (each in a fresh substrate, mean-pooled — the analysis-by-synthesis
forward-model trajectory).

`scripts/verify_voicebox.py` (sweep of 4 f0 × 3 vtl × 2 q = 24 voices/digit, 240 total):

```
self-recognition of varied-voice synthesis: 28/240 = 0.117   (unigram floor 0.100)
collapses to "four"; per-f0 / per-vtl all ~0.10–0.13
```

At the unigram floor. The agent does not recognise its own varied-voice synthesis
against a real-FSDD bank.

## (2) Diagnosis — self-consistent synthesis, total synth-vs-real domain shift

`scripts/diag_voicebox.py` isolates the cause:

```
B. self-consistent synth space (bank synth, recognise HELD-OUT synth): 20/20 = 1.000
A. REAL FSDD bank, recognise NEUTRAL synth (f0=120, vtl=1, q=4):        1/10  = 0.100
D. synth(w) nearest real centroid is the CORRECT digit:                 1/10
   — 9/10 synthetic digits land nearest the real "zero" centroid
```

- **B = 1.000**: the voicebox is **not** producing mush. Synthesised digits are perfectly
  separable *from each other* — the per-digit acoustics are distinct and consistent.
- **A = 0.100 / D = 1/10**: but every synthesised digit lands in the **same degenerate
  corner** of the agent's feature space, far from real speech and collapsed onto one
  cluster. There is a **total synthetic-vs-human domain shift** at the recogniser level.
- Klatt-LF (the better forward model) shows the **same** collapse (everything → "six",
  0.100) — the upgraded source does not narrow the gap. It is not a source-richness
  problem; the synthesis is simply off the manifold of real FSDD in the current
  (seed cochleagram + L2-norm) front end.

## (3) The A/B at the bank level — the actual experiment, run in minutes

`scripts/synth_parent_loso_probe.py` runs the parent's *banking* (what ultimately drives
recognition) four ways against the SAME human-FSDD LOSO probe (held-out speaker
`yweweler`, full lexicon, the agent's own `blind_guess`). Real bank = 18 train
exemplars/digit (5 train speakers):

```
                        human seen-speaker     human LOSO (cross-speaker)
(1) REAL-ONLY               0.950                  0.350
(2) REAL + ESPEAK           0.933                  0.350   (espeak parent)
(3) REAL + SYNTH            0.933                  0.317   (+240 varied-voice synth)
(4) SYNTH-ONLY              0.250                  0.133   (pure varied-voice parent)

varied-voice SYNTH parent lifts LOSO over real-only by  -0.033
espeak parent lifts LOSO over real-only by              +0.000
```

- The varied-voice synthetic parent does **not** close the cross-speaker gap. It moves
  LOSO **down** 0.033 — the off-manifold synthetic exemplars pollute the 1-NN bank
  (the same train/test-mismatch mechanism that made IDS hurt).
- **SYNTH-ONLY collapses** (seen 0.250, LOSO 0.133) — confirming synthetic digits are
  barely separable against real human speech, even seen-speaker.
- The espeak parent is LOSO-neutral (+0.000), consistent with the premise that neither
  synthetic parent crosses the speaker wall.

This reproduces the known frontier numbers (real-only seen 0.950, LOSO 0.350) and shows
**0 of the 0.60 gap is closed** by varied-voice synthetic teaching — slightly negative.

## (4) Verdict and recommendation

A **better-sounding, varied-voice parent does NOT lift cross-speaker speaker-invariance**,
because the bottleneck is not voice *variety* — it is the **synthetic-vs-human source
floor**, and that floor is **total** in the agent's current front end: synthetic digits
(both source-filter and Klatt-LF) are self-consistent but land in a degenerate region
disjoint from real FSDD, so they cannot teach an invariant that transfers to human
held-out speakers. Banking them is net-negative.

The donkey boundary held (parent would speak/vary-voice via the agent's own voicebox;
recognition stayed the agent's `blind_guess`; the LOSO probe is human FSDD, full-lexicon,
held-out speaker, never banked) — but the experiment **stopped before wiring the parent
or launching the long run**, exactly as instructed when the voicebox isn't good enough.

**Recommended next move (fix the voicebox / front end, not the loop):**

1. **Close the synth-vs-real gap at the front end, not the source.** The collapse is in
   the recogniser's feature space (seed cochleagram + L2 norm), where synth lands
   off-manifold. A speaker-/source-normalised representation (VTL-invariant formant
   ratios — `ozma_speaker_normalization` — or CMVN over the cochleagram) is the lever
   that would make synth and real co-locate; voice variety only helps *after* synth and
   real share a manifold.
2. **Measure the synth-vs-real distance directly** (experiment D here) as the objective
   to drive down — that is the ungameable signal for "is the voicebox good enough yet."
3. Only once `REAL + SYNTH` LOSO ≥ `REAL-ONLY` in the bank-level probe is it worth wiring
   the varied-voice parent into `parent_teacher.parent_say` and running the long
   persistent loop. Until then the long run would just bank off-manifold mush.

## Reproduce

```
cd runners/dsl && maturin build --release          # rebuild the voicebox into the .so
python -m scripts.verify_voicebox                  # intelligibility sweep
python -m scripts.diag_voicebox                    # self-consistent vs synth-vs-real
python -m scripts.synth_parent_loso_probe          # the A/B LOSO experiment
```

Full captured output: `/tmp/physics_parent_run.txt`. Required suites green:
`test_stt_pipeline test_perception_self_assessment test_process_meta_assessor
test_gap_guidance test_frontend_effect_gate` (36 passed). Nothing committed; scripts left
in the working tree.
