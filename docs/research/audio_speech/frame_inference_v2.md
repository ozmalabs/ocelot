# FRAME-INFERENCE v2 — recognition as a collapse over weighted admissibility of many soft-excluder frames

## What this is

v1 (`scripts/frame_inference_v1.py`) showed a single SPEAKER-RELATIVE acoustic frame
beats absolute/removal cross-speaker but UNDER-determines — one frame is never enough.
v2 instantiates the theory faithfully: recognition is the **intersection of MANY
frames**, each a **soft excluder** (abstain where unsure, exclude where confident),
combined by **weighted admissibility** (vector-weighted intersection of
log-admissibilities), kept soft until a Viterbi/argmax collapse — explicitly **NOT** a
single frame and **NOT** a dot product.

Memory grounding: `ozma_collapse_multiple_frames`,
`ozma_context_is_everything_noise_is_unexplained`, `ozma_weighting_is_a_vector`,
`ozma_recognition_is_exclusion`.

## The build (donkey-clean)

- **World (imposed, stated honestly):** short digit SEQUENCES (len 5) per speaker,
  concatenating real Speech-Commands digit clips under an **imposed bigram** Markov
  transition (`scripts/frame_inference_v2.py:imposed_bigram`). Peakiness controls how
  much structure the world's statistics carry. Cross-speaker = HELD-OUT speakers'
  sequences, never banked.

- **Frames, each a SOFT EXCLUDER** over the 10 digit candidates — a per-candidate
  **log-admissibility** vector in `[FLOOR, 0]`: `0` = fully admissible / abstain,
  `< 0` = excluded. A cue can only **carve**, never boost above admissible. Built in
  `domains/frame_inference_v2.py`:
  - **Speaker-relative acoustic** — v1 talker-relative formant reading → 1-NN DTW
    distances to the frame-relative bank → `soft_exclude_from_distance` (closest
    admissible, others carved).
  - **Context** — predecessor's bigram row → `soft_exclude_from_score`, conditioned
    SOFTLY on the predecessor's acoustic posterior (`_expected_excluder`).
  - **Future sheaf** — successor's bigram column (1-step) and 2-step lookahead →
    soft excluders, down-weighted by the neighbour's posterior confidence
    (`_posterior_confidence` = abstain-where-unsure: a shaky neighbour carves less,
    so a cue can never hurt).
  - **Lexical/prior** — bigram stationary unigram → a weak soft excluder.

- **Collapse = WEIGHTED ADMISSIBILITY** (`weighted_admissibility`): per-position
  emission = acoustic ⊕ prior ⊕ future-sheaf, vector-weighted **sum of
  log-admissibilities** (= intersection of admissibility masses; each term ≤ 0, so
  every frame can only carve). The **context** frame is the Viterbi forward transition
  (`viterbi_soft`) — the DP folds the whole sequence so each position is constrained by
  both predecessor and successor. Kept soft until the path argmax.

- **Dot-product control** (`dot_product_combine`): the SAME frames, but as POSITIVE
  scores (`score_from_soft_exclude` = `exp(e)`, the same information) combined by a
  SCALAR weighted SUM, argmax per position. No veto, no intersection — a high score on
  one frame can RESCUE a candidate another excluded.

The only difference between (ii) and (iii) is **scalar-positive-sum vs
vector-weighted-log-intersection** — the soft-admissibility-vs-scalar claim, isolated.

## Donkey audit

Frames = owned models (acoustic = v1 relative reading + 1-NN DTW = owned DSP; context /
future / prior = owned bigram + unigram counts). The combine = owned numpy
(soft-exclude / vector-weight / intersect / Viterbi). **No net, no fit, no gradient, no
sweep-and-keep-best** — the peakiness × sheaf sweeps REPORT the surface; the combine
itself carries no tuned parameter (weights are measurements: per-frame exclusion depth
and neighbour posterior confidence). Recognition is the agent's; sequence structure is
the world's (imposed bigram, stated honestly); held-out speakers never banked; CortexLoop
untouched.

## Results (cross-speaker LOSO, SC held-out speakers)

<!-- RESULTS_TABLE -->

## Verdict

<!-- VERDICT -->
