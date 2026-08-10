# Cursive reading — the grounded plan (from RESEARCH_CURSIVE.md)

*Executable distillation of the research spike. Grounds runs 68+.*

## The reframe (why runs 62-67 floored, and why that's expected)

The research externally validates our floor. The **Bayesian Action-Perception
(BAP) model** (Gilet, Diard, Bessière 2011, PLoS ONE) — a *training-free*
motor-simulation cursive recognizer (a hand-specified probabilistic program,
inferred not backprop-trained) — scores:

- **93.36% WITHIN-writer**
- **49.68% CROSS-writer** (26-way per-letter)

Runs 62-67 measured **cross-writer, feed-forward, invariant** — the exact
worst-case regime BAP puts at ~50%, and our ~18% sits below only because our
bottom-up channel is weaker (invariant frame discards pose) and the envelope
re-entangles. **The floor is the human/BAP cross-writer bottom-up limit, not
our failure.** Two things follow:

1. **The target splits.** Within-writer cursive reading is achievable (~93%,
   BAP). Cross-writer bottom-up is a ~50% ceiling *without adaptation*. Every
   future gate reports within- and cross-writer **separately**, calibrated
   against BAP's 93% / 50%.
2. **The lever is NOT "make the per-letter recognizer strong in isolation"**
   (humans don't; nobody does). It is the three things humans actually use:
   a strong **own-motor generator** (we already have it — we can WRITE), a
   strong **lexical prior**, and a **bidirectional top-down loop** — plus
   **writer-adaptation**, which BAP shows *is the 50%→93% difference*.

The machine literature warns (Liu/Wang 2020, IAM WER 22.2%→17.3% with an
explicit LM): context is a **multiplier on a decent posterior, not a
substitute for one**. A feed-forward "lexicon rescues 18% letters" pipeline is
insufficient — which is precisely what runs 61-67's one-directional collapse
was. The fix is the *loop* and the *writer-adapted generator*, not more LM.

## The architecture (what we're building, in one line)

**Interactive-activation reading realised as analysis-by-synthesis:** infer the
writer's low-dimensional generator from the ink, then predict-and-verify each
letter incrementally with our own writer as the forward model, with the lexical
prior feeding *back* into which letter to synthesise-and-check next. This is the
human handwriting-reading architecture (weak letters + own-motor prior +
top-down loop; reading handwriting recruits the writing motor system — Longcamp
2003/05) and the only configuration with a 93% existence proof (BAP).

## The staged plan (run specs)

**Step 1 (RUN 68) — Close the top-down loop.** Replace the one-directional
lexicon collapse with a **bidirectional word↔letter** interactive-activation
loop: partially-activated lexicon entries feed activation *back* to re-score
per-letter candidates; iterate to a fixed point (natural as a `run_rules`
fixpoint — the decode→re-decode we already run for codebook growth).
- **Tests:** does word→letter feedback lift char *and* word accuracy on
  hand-PRINT above the feed-forward 67%/78% (the cheap regime where the letter
  channel is already decent)?
- **Diagnostic value:** if it only helps where the posterior is already good,
  it *confirms* the multiplier warning — feedback amplifies a decent posterior,
  can't create one — and cursive needs Steps 2/3. Cheap, high-diagnostic, first.

**Step 2 (RUN 69) — Re-admit POSE in a WRITER-RELATIVE frame.** The separating
signal we discarded (pose/placement) is writer-dependent. Estimate a per-writer
frame from the line (baseline, slant, x-height, join grid — the sigma-lognormal
"virtual target" geometry, Plamondon), score each letter's pose *relative to
that frame*. This is BAP's "known writer" made operational, and donkey=0
metric-learning done in the *right coordinates* (closed-form/exemplar-grown, NOT
an SGD-trained net — that would cross the line).
- **Tests:** does within-writer char accuracy rise toward BAP's 93% when pose is
  scored in the writer's own frame? Report within- vs cross-writer separately.
- **Risk:** estimating the frame from little ink is unstable (the 50% regime
  lives here). Highest-leverage step, hardest.

**Step 3 (RUN 70) — INCREMENTAL AbS reading (predict-and-verify).** Use our
working writer (runs 63/65/66) as the forward model: given the writer frame
(Step 2) and lexical hypotheses (Step 1), *synthesise* the predicted next
letter's stroke incrementally and compare to the ink at that span (AbS inner
loop over the `vit` span lattice), advancing left-to-right, letting prediction
pick the segmentation. This is CTC-style recognition-by-alignment (Graves 2009)
with our generator as the emission model; Graves-2013 one-point-at-a-time
prediction. **Dissolves the whole-word pose/envelope re-entanglement** (run-16).
- **Tests:** does incremental AbS beat whole-word render-and-compare (run-16/66
  verdict) on cursive?
- **Risk:** synthesis-per-hypothesis is expensive; needs Step 1 to prune
  hypotheses hard and Step 2 to make synthesis match. Depends on 1+2.

**Step 4 (RUN 71) — Motor co-representation.** Make reading and writing share
the *same* stroke codebook / generator (BAP common-coding; the biological
result). The writer's learned joins (runs 63/65) become the recognition
emission model directly — no separate reading representation.
- **Tests:** does sharing the generator (vs a separate reading codebook) improve
  cursive reading, replicating the human co-representation benefit?
- **Risk:** our writer was taught on a synthetic curriculum; real writers are
  style *families* (run 9/15) — may need Step 2's adaptation to bridge to a real
  hand. Integration/ablation once 1-3 exist.

**Step 5 (RUN 72) — Powered cross-writer gate + honest boundary.** Report
within-writer and cross-writer word accuracy with CIs against BAP's 93%/50%
calibration (run-15 standing rule: power the gate). If cross-writer clears a
useful bar with a few adaptation lines → a training-free reader that adapts like
a human. If it floors at ~50% without adaptation → the honest boundary: cursive
reading is writer-adaptive-or-lifetime-learned, and we say so. Truth-telling
step; the only risk is self-deception, guarded by the powered gate.

## The honest target

- **Within-writer:** approach BAP's ~93% — the real, reachable goal, and a
  genuine training-free result if hit.
- **Cross-writer, unadapted:** ~50% is the bottom-up limit (BAP); we do NOT fake
  clearing it. Usable cross-writer reading *requires* a few adaptation lines
  (in-context writer-adaptation, human-shaped) — that becomes the claim.

## What this reuses (nothing new-from-scratch)

- The writer (generation): runs 63/65/66 — WORKS, 140/140.
- The lexical collapse: run 61 — WORKS on print; Step 1 makes it bidirectional.
- The span lattice (segmentation-by-recognition): `vit_step`/`vit_backtrace` —
  the graph form of CTC's recognition-by-alignment (research C1 confirms this is
  the correct architecture).
- The codebook growth loop: `run_rules` fixpoint — Step 1's feedback loop is the
  same machine.
- donkey=0 throughout (flag: Step 2 metric-learning stays closed-form/
  exemplar-grown; any SGD-trained feature net would cross the line).
