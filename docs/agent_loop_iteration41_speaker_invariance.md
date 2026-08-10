# iter-41 — feature-space SPEAKER-INVARIANCE via cross-speaker clustering

> The convergent bound (iter-40 verdict + the agent's LIVE order-N derivative,
> docs/agent_frontier_selfdiagnosis_postiter40.md, + the human reading): the cue-graph
> CARRIES the information (iter-37/38 error-overlaps above chance) but its raw
> feature-space nodes can't discriminate SPEAKER-INVARIANTLY. The agent's own #1
> frontier pick — **cross-speaker clustering** (unsupervised-clustering, payoff 82) —
> is the lever; this iteration enacts it as a composable, no-fit transform of the
> channel evidence and measures whether it lifts held-out-speaker recognition.

## (1) What was built — audited

The bound localises in the channel evidence: `many_settings_recognizer._channel_distances`
computes, per channel, `D_c(s,w) = min over TRAIN exemplars of word w` of the cosine
distance. The train exemplars are per-SPEAKER tokens, so a held-out-speaker query
matches its single nearest TOKEN — frequently a same-speaker / different-word token
rather than the right word's cross-speaker cluster. That is the speaker-invariance
failure, sitting *inside* the channel evidence.

**`domains/speaker_invariant_centroids.py`** — the agent's owned cross-speaker
clustering, no-fit:

- `word_speaker_prototypes` — per (word, speaker) prototype = L2-normalised mean of
  that speaker's tokens of that word (the within-speaker cluster's centroid).
- `speaker_invariant_centroids(k)` — for each word, cluster its per-speaker prototypes
  (each train speaker weighing equally) into **k cross-speaker centroids**. `k=1` =
  per-speaker-mean then pool (the single speaker-invariant centre); `k>1` = k-means
  modes over the per-speaker prototypes (textbook deterministic Lloyd, cosine
  geometry, seeded — no label beyond the word grouping, no model fit).
- `centroid_channel_likelihood` — `D_c(s,w) = min cosine distance to word w's
  cross-speaker centroids`, fed through the **identical** `likelihood_from_distances`
  softmax every channel already uses. Same `{word: likelihood}` output shape as
  `channel_likelihood`, so it is a strict drop-in.

**`scripts/iter41_speaker_invariance.py`** — `heldout_combined_centroid` is
`EH.heldout_combined` with one line changed: each cosine vector channel's per-candidate
likelihood now comes from the cross-speaker centroid distance instead of raw-token
1-NN. The recognition **decision Term is byte-identical** (same variadic
`Argmax`-of-`Times` product, same softmax, same AxS likelihood channel unchanged); only
the distance SOURCE changes. NO trained classifier, NO learned weight, NO gradient, NO
net — the prototypes are group means (and, for k>1, Lloyd iterations over those means).

NO-DONKEY / NO-FIT audit: the only computation added is group-mean + (optional) k-means
over those means — the same exemplar-average form the agent already owns
(`axs_channel._axs_word_model` = per-word mean trajectory). The selector is not a sweep:
k is a fixed argument, the venue is reported at the chosen k (k=1 is the principled
default — one cross-speaker cluster per word). No best-of selection over folds.

Speaker labels for clustering are reconstructed from `build_fold`'s exact train order
(`train_speaker_labels`), including the shuffle re-bucketing, so the shuffle control
clusters over a SCRAMBLED voice partition (cross-speaker clustering over scrambled
voices must not help — the structural control).

## (2) Smoke validation (alignment + wiring)

Synthetic 3-speaker / 2-word with speaker-shaped offsets: centroid 1-NN generalises to
a held-out (new-offset) speaker at 1.0 where raw token 1-NN cannot. One real FSDD fold
(n_per=2, held=george): single-flat centroid 0.450 vs raw 0.300 (Δ +0.150); many
transition channels lift +0.20–0.30 per-channel; `formant_relation` HURTS under
centroid (−0.35) — it is already a speaker-invariant relational cue, so averaging its
trajectory across speakers smears it. The full product is saturated at tiny n. Speaker
labels align to every channel's train vectors (asserted).

## (3) The cross-speaker multi-metric — FSDD LOSO, 6 speakers, with shuffle

### k=1 (single cross-speaker centroid per word) — n_per=6, rounds=2, chance 0.100

Mean over 6 held-out speakers:

| metric | speaker-invariant | current raw-token | Δ |
|---|---|---|---|
| **full cue-graph** | **0.464** | **0.586** | **−0.122 (HURTS)** |
| single-flat (cleanest single-channel read) | 0.364 | 0.489 | −0.125 |
| frozen | 0.442 | — | — |

Every one of the 6 folds is negative (−0.067 to −0.200). Shuffle control CLEAN (SI real
0.464 vs shuffle 0.411, margin +0.053; raw margin also +0.053 — the cross-speaker
structure is real in both, the centroid just exploits it worse). Error-overlap: SI
fixes 32/149 of raw's errors but raw fixes 76/193 of SI's (net −44 for SI).

**The decisive diagnostic — per-channel centroid Δ (mean over folds):** the single
cross-speaker centroid HELPS exactly the WEAK / NOISY channels and HURTS the STRONG ones:

| helped (Δ>0) | Δ | | hurt (Δ<0) | Δ |
|---|---|---|---|---|
| f0_contour | +0.119 | | mid_freq:trans_w4 | −0.139 |
| modspec | +0.089 | | mid_time:flat | −0.136 |
| manner_voicing | +0.061 | | mid_freq:flat | −0.131 |
| landmark | +0.058 | | middle:flat | −0.125 |
| fft_ear | +0.050 | | sharp_freq:trans_w4 | −0.125 |
| formant_relation | +0.006 | | (all strong gammatone flat/trans) | −0.10..−0.14 |

The mechanism is now unambiguous: **averaging into one centroid DENOISES a weak cue
(f0/modspec/manner/landmark/fft are individually unreliable, so collapsing their token
cloud to the cross-speaker centre helps) but DESTROYS the discriminative within-word
variance the STRONG gammatone channels' 1-NN exploits** (those channels are already
near-saturated as raw token 1-NN; the single centroid under-fits them). The strong
channels dominate the product, so the full graph follows them DOWN. One centroid per
word is too coarse — the classic clustering under-fit.

### k=3 / k=6 (sub-word k-prototypes — keep the cross-speaker modes)

k>1 keeps k cross-speaker clusters per word (k-means over the per-speaker prototypes);
k=6 ≥ the 5 train speakers, so it recovers the per-speaker-prototype 1-NN — every
speaker stays its own denoised mode, the maximally mode-preserving variant. The full
k-sweep, full cue-graph, mean over 6 held-out speakers (raw-token graph 0.586 throughout):

| k | SI graph | Δ vs raw | single-flat Δ | shuffle margin (SI / raw) | error-overlap net |
|---|---|---|---|---|---|
| 1 | 0.464 | **−0.122** | −0.125 | +0.053 / +0.053 | −44 |
| 3 | 0.547 | **−0.039** | −0.061 | +0.078 / +0.053 | −14 |
| 6 | 0.550 | **−0.036** | −0.064 | +0.078 / +0.053 | −13 |

Keeping the modes RECOVERS most of the k=1 loss (−0.122 → −0.036) — confirming the k=1
collapse was under-fit — but the lever NEVER crosses into positive. At k=3/k=6 the
weak-channel denoising gain shrinks too (f0 +0.119 → +0.058) because the per-speaker
prototypes are noisier than the single centroid, so the two effects nearly cancel and
the graph lands a hair below the raw token 1-NN. The shuffle margin WIDENS at k>1
(+0.078 vs raw +0.053): the cross-speaker structure the clustering captures is GENUINE
(not an artifact) — it just doesn't net-improve the digit cue-graph because the strong
gammatone channels' raw token 1-NN is already a near-optimal use of that same structure.

## (4) VERDICT

**The convergent feature-space speaker-invariance lever (the agent's #1 frontier pick,
cross-speaker clustering), enacted faithfully and no-fit, does NOT lift held-out-speaker
FSDD digit recognition.** k=1 hurts the full LOSO cue-graph by −0.122; the
mode-preserving k=3/k=6 recover to −0.036, neutral-to-slightly-negative, never positive.
Honest and reproducible across all 6 folds and 3 settings of k, with a clean shuffle
control. This is a NULL on the headline question for the FSDD venue.

**The residual is sharply localised, and it is informative:**

1. *Structure IS there.* The shuffle control is clean and the SI margin over shuffle
   WIDENS at k>1 (+0.078) — cross-speaker clustering captures genuine cross-speaker
   structure. The null is not "nothing to recover."

2. *It helps the WEAK cues, hurts the STRONG ones.* Cross-speaker averaging denoises
   the individually-unreliable source/rate/transient cues (f0 +0.06..+0.12, modspec,
   manner, landmark, fft_ear) and under-fits the strong gammatone spectral channels
   (−0.06..−0.14 at k=1). The strong channels carry the digit recognition and dominate
   the product, so the graph follows them down. **For the strong channels the
   per-speaker token cloud IS the discriminative signal, not noise to be averaged
   away** — which is exactly why this venue's prior work
   (`ozma_speaker_normalization`: learn_over_cochlea 55%) found LEARNING over many raw
   tokens, not centroid normalization, was the lever that worked.

3. *This converges with the prior arc, sharpening it.* The first-pass speaker_norm was
   "built-but-insufficient" (+3% only). iter-41 now shows WHY centroid-style
   speaker-invariance is bounded: on a balanced digit task the raw exemplar 1-NN
   already uses the cross-speaker structure near-optimally; explicit centroid
   clustering cannot beat it, only re-package it (and loses on the strong channels).
   The agent's order-N derivative converged on the feature front-end; the bare ranker
   picked clustering; the MEASUREMENT here shows the ranker's pick, while structurally
   sound, is NOT the leverage point for this venue — the
   "already-built-but-insufficient reads as closed" seam the self-diagnosis flagged is
   confirmed empirically: clustering is real but not the bottleneck the digit cue-graph
   is bound by.

**Venue-dependence (stated, not yet measured here):** the weak-cue denoising gain is
real and could matter where the WEAK cues carry more of the load — continuous
gold-span words, where coarticulation degrades the strong spectral channels and the
source/rate/transient cues become relatively more informative (the iter-37/38
error-overlap finding). The drop-in transfers unchanged to
`scripts.iter36_continuous_graph` via `heldout_combined_centroid`; that run is the
honest next probe of whether the lever pays off in the venue where the strong channels
are themselves degraded. NOT claimed as a win until measured.

**No over-claim:** the lever was the agent's own pick, faithfully built (audited:
group-mean / k-means, no fit, no net, no donkey; decision Term byte-identical), and it
is a NULL on FSDD digits. The bound is confirmed to be feature-space discrimination,
but the specific repair (cross-speaker centroid clustering) is not sufficient on this
venue — the residual is that the strong cochlear channels' raw exemplar variance is
already discriminative, so the leverage is in LEARNING over those raw tokens (the prior
arc's finding), not in clustering them into invariant centroids.

## Files
- `domains/speaker_invariant_centroids.py` — the cross-speaker clustering (no-fit).
- `scripts/iter41_speaker_invariance.py` — the LOSO acceptance harness.
- `docs/agent_loop_iteration41_speaker_invariance.md` — this report.

## Reproduce
```
PYTHONUNBUFFERED=1 python -m scripts.iter41_speaker_invariance 6 2 1   # n_per rounds k
```
Required suites green (32): `python -m pytest tests/test_stt_pipeline.py
tests/test_perception_self_assessment.py tests/test_process_meta_assessor.py
tests/test_gap_guidance.py -q`.
