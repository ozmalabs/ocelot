# Iteration 31 — recognition READS THROUGH the transition channel (closing iter-30's gap)

> Spec: `docs/agent_loop_iteration30_transition_contrast_selector.md` (commit
> ab2b8850) + `docs/research_speech_deficits.md`. Written INCREMENTALLY; runs
> captured to `/tmp` files; `PYTHONUNBUFFERED=1`.

## The gap being closed (iter-30)

iter-30's transition-contrast SELECTOR finally bites on its own objective — the
real cross-voice transition-channel margin (+0.336) beats its own shuffle (+0.294),
so the selector is no longer inert (iter-29 had shuffle ≡ real on every metric). But
the **recognition readout** (1-NN-DTW / cosine over per-utterance vectors) still read
the **RAW grown patch-response matrix** (`l2_flat(R)` / `l2_pool(R)`), NOT the
transition channel the selector selects on. Consequence: the selection improves the
transition margin while the recognizer never looks there — recognition stayed
warp-driven (1-NN flat 0.517 = shuffle 0.517, the gain over frozen was the cohort-warp
removal alone; pooled/persona down).

**The fix (criterion 1 — the readout wired, auditable no-fit).** Make the RECOGNITION
representation BE the transition-channel readout — `transition_channel(R, patches)`,
the agent's order-1-over-time operator (`order_n_concepts.nth_order_terms(.., 1)` over
TIME / `dynamics_features.compose_formant_transitions`, F_late − F_early per ordered
channel + the two-region ArgMax formant sweep) — the **SAME** channel the selector
scores on. Both the selector AND the readout now live on the transition channel: the
recognizer consumes the discrimination the selector built.

No-donkey: the readout is the agent's OWNED transition operator evaluated natively and
L2-normalised for cosine 1-NN. No optimiser, no fit, no weight tensor, no hand-tuned
score. `transition_channel(R)` is already a single per-utterance (P+2)-vector; the
recognition vector IS that vector. Everything else is unchanged (discrete accretion,
the cross-voice transition-contrast selector, gold spans, the frozen baseline, all
ablations + the shuffle control).

### Where the wiring lives

- `scripts/grown_representation_hvpt_accept.py`:
  - `trans_readout(R, patches)` = `l2(transition_channel(R, patches))` — the iter-31
    recognition vector (the same operator the selector uses).
  - `vecs(...)` now emits THREE readouts per utterance — flat (iter-30 raw), pool
    (iter-30 raw), **trans (iter-31, the transition channel)** — for every
    representation (frozen, grown, no-warp ablation, grown-all control).
  - `*_1nn_trans` recognition metrics added for frozen / grown / no-warp / grown-all,
    plus the iter-31 shuffle read on 1NN-trans and the head-to-head 1NN-trans.
  - The decisive BITE flag now requires REAL > SHUFFLE on BOTH the trans-margin
    (objective) AND the 1NN-trans recognition (readout), the clean-generalisation bar.

## The runs (criterion 2 — captured to /tmp, incremental)

- `/tmp/iter31_smoke_n1.txt` — n=1 smoke (harness validity).
- `/tmp/iter31_n4_run.txt` — n=4, the reported LOSO run (pending).

<!-- results filled in below as runs complete -->
