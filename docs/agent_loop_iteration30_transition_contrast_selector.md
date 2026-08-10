# Iteration 30 — the TRANSITION-CONTRAST selector (fixing iter-29's structural dyslexia)

> Spec: `docs/research_speech_deficits.md` (the deficit/lesion study, commit
> d8fa80f5) + `docs/agent_loop_iteration29_representation_builder.md` (the harness
> + the failure). Written INCREMENTALLY; runs captured to `/tmp` files.

## The diagnosis being fixed

iter-29's representation-builder works (the cohort warp WAS the baked-in HVPT
failure) but its build signal — `grown_representation.masked_prediction_error`, a
1-step smoothness predictor `r̂_t = r_{t−1}` — is **voice-agnostic AND
contrast-agnostic**. It rewards temporally SMOOTH channels. Consequence: the
cross-voice survival selector did NOT bite (shuffle ≡ real: shuffling
utterance→voice labels gave the same grown bank).

The deficit study names the missing signal: **dyslexia's two sub-lesions
(phonological-core + rapid-transition) prove phoneme identity lives in the FAST
TEMPORAL TRANSITION and the CATEGORICAL CONTRAST** — exactly the cues a smoothness
signal discards. A smoothness-built representation is a *dyslexic* representation.

## The fix (criterion 1 — the selector wired, auditable no-fit)

Replace the smoothness build signal with a **CROSS-VOICE TRANSITION-CONTRAST
MARGIN**, using machinery the agent ALREADY OWNS but never wired to the selector:

- **The transition channel** (`grown_representation.transition_channel`) = the
  agent's order-1-over-time operator (`order_n_concepts.nth_order_terms(.., 1)`
  over TIME / `dynamics_features.compose_formant_transitions`, `F_late − F_early`),
  read on the patch-response matrix:
  - patch columns ordered by centre Hz (the ArgMax-of-region frame);
  - frames split EARLY/LATE (the `enrich_sign_windows` split);
  - per ordered channel: late mean − early mean = order-1-over-time (the
    per-channel transition profile), PLUS the agent's two-region formant-frequency
    sweep (`F = ArgMax(region)`, `F_late − F_early`) for F1 (low half) and F2
    (high half). Both terms are the same owned operator at two granularities.
- **The contrast margin** (`transition_contrast_margin` /
  `patch_survives_transition`) = `sim(same word, ACROSS different voices) −
  sim(different words)`, measured THROUGH the transition channel. The two terms
  are the two dyslexia sub-lesions: the same-word-across-voices term is the
  categorical / cross-voice contrast (the *what* invariant to the *who*); the
  minus-different-word term is the discrimination.
- **The shell is unchanged**: `patch_survives_transition` keeps iter-29's
  voice-counting structure — for each anchored voice, the margin (held voice's
  words vs the SAME word across OTHER voices, minus different words) must RISE
  when the candidate is added; survive iff it rises on ≥ `min_voices_frac` of the
  voices. It reads the SIGN of a margin change and counts voices. **No optimiser,
  no weight fit, no swept score.** Patches are still `(centre, sigma)` Gaussians
  rendered exactly from the formula; accretion stays discrete.

No-donkey line held: the selector is the agent's owned transition operator + a
discrimination margin; the inventory is grown by discrete accretion under it.

### Why the shuffle MUST now bite (by construction)

The same-word term is restricted to pairs from DIFFERENT voices. Shuffling the
utterance→voice labels (words stay attached; only the voice partition is
randomised) destroys the same-word-across-voice structure the margin depends on —
so the transition selector, unlike iter-29's smoothness selector, cannot survive
its own shuffle. That is the decisive test.

## The runs (criterion 2 — captured to /tmp, incremental)

Harness: `scripts/grown_representation_hvpt_accept.py`, now growing under the
TRANSITION selector (default) with the iter-29 SMOOTHNESS selector run alongside
for the head-to-head, plus the SHUFFLE control on the transition selector.
Real-FSDD-speaker LOSO over 6 speakers + agent-generated persona cross-check;
reports ALL metrics (1-NN flat AND pooled AND persona AND same-word flat margin
AND transition-channel margin). Inputs are the agent's gammatone band-trajectory
matrices (`band_trajectory_matrix`); word labels are the FSDD digit identities.

Captured runs: `/tmp/iter30_smoke_n2.txt` (n=2 smoke), `/tmp/iter30_n4_run.txt`
(n=4, the reported run).

## Results — n=4, LOSO mean over 6 FSDD speakers (criterion 2 + 3)

### (2) THE DECISIVE SHUFFLE TEST (transition selector) — does REAL beat its own SHUFFLE?

| metric (LOSO mean) | REAL | SHUFFLE | REAL beats SHUFFLE? |
|---|---|---|---|
| **TRANSITION-channel margin** (the selector's own objective) | **+0.3360** | **+0.2941** | **YES (+0.042)** |
| same-word flat margin | +0.1631 | +0.1620 | yes (marginal) |
| 1-NN flat | 0.517 | 0.517 | TIE |
| 1-NN pooled | 0.158 | 0.142 | yes (marginal) |

**This is the qualitative change from iter-29.** iter-29's smoothness selector gave
shuffle ≡ real on *every* metric (the selector was inert). The transition selector
now produces **REAL > SHUFFLE on the transition-channel margin it actually selects on
(+0.336 vs +0.294)** — shuffling the voice partition destroys the same-word-across-
voice structure the margin depends on, so the cross-voice part of the selector is
finally doing discriminating work. The selector reads the cue the dyslexia deficit
named, and that cue is voice-structure-dependent (it collapses under shuffle).

It does NOT, however, separate real from shuffle on the **recognition** metric
(1-NN flat 0.517 = 0.517). The harness's combined BITES flag (which requires BOTH
trans-margin AND 1-NN-flat to beat shuffle) therefore reports "DOES NOT BITE." The
honest split: **the selector bites on its OWN objective (the transition contrast),
but that bite does NOT yet propagate to the flat-pooled 1-NN recognition number.**

Per-fold, the trans-margin REAL-vs-SHUFFLE is genuinely mixed (george, lucas,
yweweler: real > shuffle, clearly; jackson, nicolas: shuffle ≥ real; theo: both
reject all candidates so identical). The +0.042 mean is carried by the folds where
the real voice partition admits discriminating patches; the LOSO mean is positive
but not large and not uniform.

### (3) THE HVPT MULTI-METRIC: transition-grown vs smoothness-grown (iter-29) vs frozen

| metric (LOSO mean) | FROZEN | GROWN-TRANSITION (iter-30) | GROWN-SMOOTHNESS (iter-29) | no-warp ablation |
|---|---|---|---|---|
| same-word flat margin | +0.1294 | +0.1631 | +0.1646 | +0.1618 |
| **transition-channel margin** | +0.3616 | **+0.3360** | **+0.2839** | — |
| 1-NN flat | 0.379 | **0.517** | 0.513 | 0.504 |
| 1-NN pooled | 0.188 | **0.158** | 0.133 | 0.142 |
| patches added (mean) | — | **1.3** | 9.0 | — |

Mechanistic confirmation of the deficit prediction (the single sharpest finding):
**the SMOOTHNESS selector DEGRADES the transition channel** — on every fold the
iter-29 smoothness-grown bank LOWERS the held-out transition-channel margin
(george −0.077, lucas −0.234, theo −0.280, …; mean +0.2839 vs frozen +0.3616), i.e.
it is literally *building a dyslexic representation* that discards the fast-transition
cue. The transition selector preserves that cue far better (mean +0.3360, and it
RAISES it on the folds where it accretes, e.g. george +0.214). This is the deficit's
core claim, measured: smoothness throws away exactly the phonetically load-bearing
transition; the transition selector keeps it.

The transition selector is also far more PARSIMONIOUS (1.3 patches added vs 9.0) —
it rejects most candidates because raising a *cross-voice contrast* margin is a much
stricter bar than raising a per-voice smoothness, which is the intended behaviour.

On recognition: transition-grown 1-NN flat 0.517 ≈ smoothness-grown 0.513 ≈ no-warp
0.504 — the recognition gain over frozen (0.379 → 0.517) is still **almost entirely
the cohort-warp removal** (the iter-29 finding stands; the no-warp ablation alone
gets 0.504). 1-NN pooled is the one recognition metric where transition is best
(0.158 vs smoothness 0.133 vs frozen 0.188 — still below frozen).

### Persona cross-check (held-out 5th persona)

Persona REAL == SHUFFLE exactly (both grow the same +2 bank, trans-margin +0.4794,
1-NN flat 1.000, pooled 0.050). As iter-29 found, the persona generator is a pure
global resample that VTLN inverts, so it carries no genuine across-speaker structure
for the cross-voice selector to find — the real-speaker test is the honest one. The
frozen path still wins persona pooled (0.750) for the same reason.

## VERDICT

**Does the transition-contrast selector make cross-voice selection BITE? PARTIALLY —
it bites on its own objective, not yet on recognition.**

1. **The shuffle now bites on the selector's objective (the central iter-29 fix).**
   REAL transition-channel margin +0.3360 > SHUFFLE +0.2941. iter-29's shuffle ≡ real
   on every metric; iter-30's selector reads a voice-structure-dependent cue and the
   shuffle destroys it. The cross-voice part of the selector is no longer inert. This
   is real and reproducible (`/tmp/iter30_n4_run.txt`).

2. **It does NOT generalise cleanly to recognition.** 1-NN flat REAL = SHUFFLE
   (0.517), and the flat-recognition gain over frozen is still the warp-removal, not
   the selector. So by the strict multi-metric bar (the iter-29 lesson against
   cherry-picking 1-NN flat), this is "bites but does not yet generalise cleanly."

3. **The deficit's mechanistic prediction is confirmed.** The smoothness selector
   measurably DEGRADES the transition channel (it builds the dyslexic representation);
   the transition selector preserves/raises it. That is the lesion study's core claim,
   measured on held-out voices.

How far it gets: the selector engages on the discriminating cue (the developmental
polyglot selection is no longer inert), but the engaged contrast does not yet move
the recognition readout. Residual: the transition descriptor is coarse (a per-channel
late−early plus a 2-region ArgMax sweep), the per-fold signal is noisy and non-uniform
(3 of 6 folds clearly real>shuffle), and recognition is read by a flat/pooled 1-NN
that the transition contrast doesn't directly optimise. The honest one-line: **the
dyslexia fix turns the inert selector into one that bites on the right cue, but
closing the gap to recognition is the next lever** — likely a richer transition read
and/or making the recognition decision itself consume the transition channel.

## No-donkey audit (re-verifiable)

- The selector is the agent's OWNED transition operator (`transition_channel` =
  order-1-over-time per ordered channel + the 2-region ArgMax formant sweep,
  mirroring `dynamics_features.compose_formant_transitions` /
  `order_n_concepts.nth_order_terms(.., 1)` over time) + a same-vs-different
  CONTRAST margin (`patch_survives_transition`). It reads the SIGN of a margin
  change and counts voices. **No optimiser, no backprop, no least-squares, no weight
  tensor is fit anywhere.** Patches remain `(centre, sigma)` Gaussians rendered
  exactly from the formula; accretion is discrete.
- The shuffle keeps words attached and randomises only the voice partition, so it
  isolates the cross-voice same-word structure the margin depends on.

## Target tests

`test_stt_pipeline` + `test_perception_self_assessment` +
`test_process_meta_assessor` + `test_gap_guidance`: **32 passed** (after the
selector + harness edits).

## Files

- `domains/grown_representation.py` — added `transition_channel`,
  `transition_contrast_margin`, `_heldvoice_margin`, `patch_survives_transition`;
  `grow_representation` gains `selector="transition"` + `voice_word_matrices`.
- `scripts/grown_representation_hvpt_accept.py` — grows under the transition
  selector (default), runs the iter-29 smoothness selector head-to-head, carries
  word labels into growth, adds the transition-channel margin metric + the decisive
  shuffle read.
- `/tmp/iter30_n4_run.txt` — full captured n=4 run.
