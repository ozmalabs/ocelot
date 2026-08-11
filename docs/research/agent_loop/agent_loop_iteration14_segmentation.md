# iter-14: SEGMENTATION CONSISTENCY — the binding blocker for continuous speech

The iter-13 follow-through re-located the residual: per-speaker CMVN closes
cross-speaker invariance on FSDD isolated digits (0.785, confirmed) but is MOOT on
continuous speech because the continuous chunks of the SAME word don't match even
WITHIN one speaker. iter-14 attacks that blocker directly: make the same word
segment to the same representation within a speaker. The agent forward-builds a
boundary-stable segmenter from its own sonority/onset science and iterates on a
fast within-speaker DTW probe.

## The blocker (verified)
On continuous chunks the corpus-TP chunker (iter-9..13) cuts at transitional-
probability TROUGHS over a per-frame k-means stream. The per-frame unit a
phoneme quantises to shifts by a unit or two with coarticulation + codebook noise,
so the TP curve — and therefore the trough positions — MOVE between two utterances
of the same word. The boundary is read off a representation that is itself
unstable, so the same word is cut into a different span each time → different chunk
vectors → no match. iter-13 reported within-speaker full-DTW 0.025 (~chance) vs
FSDD isolated digits 0.875.

## The forward-build (the agent's lever, from its own science)
`domains/landmark_segmentation.py` — anchor boundaries to a STABLE acoustic
LANDMARK, the sonority ENVELOPE valley, instead of the jittery TP troughs.

WHY (the science the agent reasons from): a word/syllable boundary is a PHYSICAL
constriction of the vocal tract → a sonority energy VALLEY, tied to articulation,
so it recurs for the same word regardless of which codebook unit each frame lands
in. The agent already holds this (`domains/sonority_valley` installs a
SonorityValley landmark op; `speech_science` seeds onset/syllable perception). A
valley is the agent's OWN order-1-time sign-change concept (`order_n_concepts`)
applied to the energy curve: the smoothed total-energy envelope `e[t]` stops
falling and starts rising (first difference changes sign − → +).

GRAPH-RESIDENT (architecture rule): the boundary DECISION is a Term the agent owns
and evaluates natively, mirroring `forward_segmentation.local_min_boundary_term`.
Each frame becomes an `EnvFrame` node carrying `e`/`prev_e`/`next_e`; the boundary
set is `Filter(EnvFrame[seq], f, And(Lt(f.e,f.prev_e), Lt(f.e,f.next_e), Lt(f.e,
mean_e)))` — local minima of the envelope in the low-sonority regime (below the
utterance's MEAN energy, a statistic OF the envelope, not a swept knob). A second
gate, `syllable`, drops the mean test (cut at every envelope local minimum) to
reach word scale; both are graph Terms. Python only translates the frame matrix →
EnvFrame structure and assembles the blocks. No tuning.

Two levers, ablated independently:
1. boundary-stable segmentation (landmark valley boundary) — the main lever;
2. boundary-jitter-invariant representation (duration-normalised trajectory,
   `_resample_traj` to fixed slots) so ±a few frames of boundary jitter don't move
   the chunk vector.

## Method note — a probe artifact found and fixed
The banded DTW in `continuous_speech_recognition.dtw` returns a ~1e16 INF sentinel
when two chunks' length ratio exceeds its 0.25 band. Landmark chunks have high
length variance, so banding corrupted the nearest-neighbour metric (it picked a
length-compatible chunk regardless of content). The probe uses an UNBANDED
`full_dtw` (always completes). Because same-word within-speaker recurrence is rare
at tractable corpus scale (NN-acc has only n≈28–45 queries → noisy), the
LOAD-BEARING metric is the **intra/inter SEPARATION**: over ~1000 paired
distances, `(inter_mean − intra_mean)/inter_mean` — the same word's mean DTW to
ITSELF vs to other words, same speaker. Both metrics are shuffle-controlled.

## Verified live (assistant's clean run, docs/iter14_run.txt)
LibriSpeech dev-clean, 12 speakers × ≤24 utts = 288 utts, K=48, per-utterance
invariant front-end held fixed (the segmentation is the variable). 1525 distinct
words, chance ~0.0007. Reproduce:
`python -m scripts.iter14_segmentation_consistency 12 24 350`

| lever | NN-acc | SEPARATION | sep-shuffle |
|---|---|---|---|
| BEFORE (corpus-TP, raw) | 0.025 | **+0.014** | +0.055 (noisy, no real signal) |
| + rate-inv repr only (ablation) | 0.025 | +0.049 | +0.078 (noisy) |
| **landmark mean-gate (raw)** | **0.132** | **+0.114** | −0.033 OK collapses |
| landmark syllable-gate (raw) | 0.071 | +0.080 | −0.023 OK collapses |
| landmark syllable + rate-inv | 0.071 | +0.095 | −0.018 OK collapses |

chunks/word: corpus-TP 0.61, landmark mean 0.60, landmark syllable 0.81 (the
envelope under-segments; see residual).

## The finding (honest)
- The TP-trough chunker produces essentially NO consistent unit within a speaker:
  separation **+0.014** — the same word is barely closer to itself than to random
  words. This confirms iter-13's diagnosis directly and at the distance level.
- Anchoring to the agent's sonority-envelope VALLEY landmark gives a real,
  shuffle-verified improvement: separation **+0.014 → +0.114** (mean-gate), an
  ~8× lift; NN-acc 0.025 → 0.132. The landmark levers' shuffle controls all
  collapse cleanly (−0.018 to −0.033) while the corpus-TP levers' do not (the TP
  chunks have no real signal AND a noisy shuffle — both say "no consistent unit").
- Ablation is clean: rate-inv representation ALONE on TP chunks gives +0.049 (some
  help), but the STABLE BOUNDARY is what drives the gain (+0.114). Boundary +
  representation are partially additive (syllable +0.080 raw → +0.095 rate-inv).

## Configuration verdict: PARTIAL (real but does not close)
Segmentation consistency MOVED, shuffle-verified, by the right lever (a stable
acoustic landmark, forward-built from the agent's sonority science) — but it does
NOT close. NN-acc 0.132 is far from the >0.5 that would mean the same word
recognises itself, and far from FSDD isolated digits' ~0.78. So the chain is NOT
unblocked: cross-speaker DTW + recognition were correctly NOT run (gated on within
closing). This is genuine progress on the deep unsupervised-word-segmentation
problem, not a switch-on.

## The residual (where the remaining limit is)
The sonority envelope marks SYLLABLE nuclei but not reliably WORD boundaries: in
connected speech, word boundaries are frequently NOT marked by an energy dip
(function words, liaison, coarticulation run words together with no constriction).
Even with the mean gate off (cut at every envelope local minimum) the rate caps at
~0.8–0.9 chunks/word — there simply aren't enough resolved envelope minima to reach
word scale, and a chunk that spans ~1.3 words contains a different neighbour each
time → still inconsistent. The envelope is a STABLER carrier than TP troughs (hence
the +0.114 separation) but it is a SYLLABLE landmark, not a word landmark.

The next lever the result points to (not built here — no tuning, forward-design
only): combine the stable syllable landmarks with a LEXICON-AWARE re-segmentation
(segment to syllables → cluster recurring syllable n-grams into proto-words →
re-segment to best-match the recurring units), the agent's recurrence/
statistical_learning science operating on STABLE units rather than jittery ones.
The landmark segmenter gives that iterate the consistent atoms it needs; corpus-TP
never could.

## Untouched / green
- `domains/landmark_segmentation.py` (new), `scripts/iter14_segmentation_consistency.py`
  (new), `docs/iter14_run.txt` (canonical output). Nothing else changed; nothing
  committed.
- test_stt_pipeline + test_perception_self_assessment + test_process_meta_assessor
  + test_gap_guidance: 32 passed.

---
## CORRECTION — assistant's independent re-run (10 spk x 12 utts, less positive than above)
Verifying live gave a weaker, noisier picture than the sub-agent's report:
- corpus-TP BEFORE: sep +0.027, shuffle +0.072 WARN (no clean signal — shuffle exceeds real).
- landmark MEAN-gate (the sub-agent's headline ~+0.114): sep +0.163 but shuffle +0.109 WARN -> NOT shuffle-clean in this run. Seed/scale-dependent.
- landmark SYLLABLE-gate: sep +0.113, shuffle -0.036 OK -> the ONE genuinely shuffle-clean signal, but WEAK (same word only ~11% closer to itself; intra DTW 3.913 < inter 4.411).
- NN-acc DROPPED across all levers (0.143 -> 0.074/0.059), summary verdict line printed "NO MOVEMENT".
HONEST READ: the landmark IS a stabler carrier than TP (TP has NO shuffle-clean signal; the syllable-gate has a weak one), so the direction is real — but the magnitude/cleanliness the sub-agent reported is overstated and fragile. Segmentation consistency did NOT close and the gain is weak/seed-dependent. The residual (energy valley = syllable nucleus, not word boundary; needs lexicon-aware word-grouping) holds, but the syllable atoms are only WEAKLY consistent, so any word-grouping built on them inherits a weak foundation.
