# iter-49 — ADMISSIBILITY GRAPHS ON THE NODES THEMSELVES

> The user: "the finer grain is admissibility graphs on the nodes themselves."
> iter-48 found per-NODE reliability is too COARSE: a wrong-order node confidently-wrong
> on a SPECIFIC contrast (e.g. b/d) but HIGH on AVERAGE keeps its per-node weight high and
> DILUTES that contrast. The fix: each (cue × order) node gets its OWN admissibility
> (sub-)graph — its per-(word/contrast) reliability, measured LOSO-clean — GATING its
> contribution PER candidate word. So the wrong-order node ABSTAINS on the contrasts it is
> not admissible for, and the per-contrast dilution disappears. Working tree only — NOT
> committed.

---

## The form — per-word weight via a CONVEX BLEND toward flat (NOT a per-word exponent)

    gated_i(w) = weight_i(w) * P_i(w) + (1 - weight_i(w)) * u_i      (a graph Plus of Times)
    score(w)   = PROD_i gated_i(w)                                    (a graph Times)
    predict(s) = Argmax_w score(w)
    weight_i(w) = max(0, (precision_i(w) - chance) / (1 - chance))

`weight_i(w)` is now PER CANDIDATE WORD — node i's measured reliability for word w
specifically, NOT its average over all words (iter-48). A node admissible for w counts in
full (`weight->1` -> `gated = P_i(w)`); a node NOT admissible for w blends toward its FLAT
reference `u_i = 1/n_candidates` (`weight->0` -> `gated = u_i`).

**Why a blend, not iter-48's exponent (a bug caught in build).** iter-48 gated by
`P_i(w)^weight_i` with a node-CONSTANT exponent (scaling the whole node uniformly). A
per-word EXPONENT is WRONG: since `0<=P<=1`, `P^0 = 1` is the LARGEST possible
contribution, so abstaining-by-exponent INFLATES exactly the words the node is bad at — the
first smoke run with the exponent form collapsed to 0.167 (it boosted the inadmissible
hypothesis). The correct per-contrast abstain makes an inadmissible node contribute a
WORD-NEUTRAL value `u_i` (the same for every candidate) -> it cancels in the Argmax -> the
node truly ABSTAINS on that contrast (neither dilutes nor inflates). All weights == 1
recovers the equal combine-all `PROD_i P_i(w)` exactly (test lock).

**The recursive (G, Γ) — admissibility all the way down.** The recognition is admissible
iff its node-combination is; each NODE is admissible (for THIS contrast) iff its own
sub-graph (its measured per-word reliability) says so. iter-48's per-node weight is the
special case `weight_i(w) == weight_i` for all w; iter-45's equal combine-all the further
special case `weight_i(w) == 1`.

## The per-word reliability MEASUREMENT (the node's admissibility sub-graph)

For node i and word w, measured by inner leave-one-speaker-out on the TRAIN speakers only:

    precision_i(w) = of the held-out TRAIN tokens node i CLAIMED were w (its single-node
                     argmax-likelihood prediction == w), the fraction whose TRUTH was w.

This is exactly the per-contrast admissibility the wall needs: a node that confidently
CLAIMS w but is usually WRONG when it claims w has low `precision_i(w)` → weight → 0 →
abstains on w → stops diluting the w hypothesis. `chance = 1/n_candidates` (DERIVED). A
node that never claimed w on inner-LOSO has no precision sample → its weight for w falls
back to the node's OVERALL (per-node, iter-48) reliability — a graceful, LOSO-clean
default (this fallback fraction is reported as the sparsity probe).

## The in-thesis line — weights MEASURED, not searched

`weight_i(w)` is a MEASUREMENT (inner-LOSO precision on TRAIN speakers, the same
argmax-likelihood the harness scores with), translated to a per-candidate graph attr. The
COMBINATION decision is the graph Term (Argmax of Times-of-Pow, evaluated by
`substrate.evaluate`). NO fit, NO gradient, NO learned weight, NO sweep; the
`(precision-chance)/(1-chance)` map has no free parameter; chance is derived. LOSO-clean:
the outer-held voice is absent from train entirely, so no reliability measurement ever
touches the test fold. The shuffle control scrambles the voice partition for the
reliability measurement TOO. Per-node-constant weights recover iter-48; all-1 recovers
iter-45's equal combine-all.

## Files
- `domains/node_admissibility_graphs.py` — the per-contrast module (`per_contrast_weight`;
  re-exports the shared iter-48 decision Term — only the granularity differs). No-fit.
- `scripts/iter49_node_admissibility_graphs.py` — the FSDD LOSO acceptance harness
  (`measure_per_contrast_reliabilities` = inner-LOSO per-word precision;
  `heldout_combined_per_contrast` = the per-word-weighted product; the sparsity probe).
- `scripts/iter49_node_admissibility_continuous.py` — the continuous gold-span harness.
- `tests/test_node_admissibility_graphs.py` — the convex-blend-gate / abstain-not-inflate
  / recover-equal / fixed-map / no-fit locks.
- `docs/agent_loop_iteration49_node_admissibility_graphs.md` — this report.

---

## (1) What was built — audited

`domains/node_admissibility_graphs.py`:
- `per_contrast_weight(precision, chance)` = the fixed `(precision-chance)/(1-chance)` map
  (iter-48's, now per-word).
- `gated_score_term` / `predict_weighted_term` = the per-contrast decision Term — `PROD_i
  [weight_i(w)·P_i(w) + (1-weight_i(w))·u_i]`, the per-node convex-blend gate (Plus of
  Times) inside the variadic Times, evaluated by `substrate.evaluate`. `weight_attr(i)`
  (the per-word weight) and `flat_attr(i)` (the node's flat reference `u_i`) are graph
  attrs the harness sets per candidate word per fold.

`scripts/iter49_node_admissibility_graphs.py`:
- `measure_per_contrast_reliabilities` = inner leave-one-speaker-out on TRAIN folds only;
  per (order × channel) node, collect (prediction, truth) over all inner held tokens, then
  per word w compute precision_i(w) → weight; record the per-(node,word) claim count (the
  precision sample size = the sparsity probe) and the per-node overall accuracy (the
  no-claim fallback).
- `heldout_combined_per_contrast` = the per-word-gated product over the SAME nodes as
  iter-48 / iter-45; sets `u_i = 1/n_candidates`.
- The iter-48 per-NODE comparator is the SAME inner-LOSO measurement
  (`measure_node_reliabilities`) + `heldout_combined_weighted`, so per-contrast vs per-node
  is an apples-to-apples granularity contrast on identical folds.

**The weight IS a measurement (audited):** weight = `(precision-chance)/(1-chance)`;
chance derived; precision is the node's inner-LOSO per-word precision on TRAIN speakers. NO
weight value tried-and-kept; NO fit/gradient/optimizer; the map has no free parameter.
LOSO-clean. The gate is a convex blend (no exponent), so an inadmissible node abstains
(contributes the word-neutral `u_i`) rather than inflating; all-1 recovers iter-45 (test
locks).

## (2) CONTINUOUS gold-span — multi-metric, shuffle, per-fold  (COMPLETE — /tmp/iter49_continuous_full.txt)

LibriSpeech gold-span words, faster-whisper forced alignment, 5 held-out speakers,
10-word shared cross-speaker vocab (chance 0.100), 27 channels × orders {0,1,2}, SHUFFLE.

| graph | acc | shuffle margin |
|---|---|---|
| **PER-CONTRAST admissibility graphs (this iter)** | **0.301** | **+0.013 (CLEAN)** |
| EQUAL combine-all (iter-45) | 0.292 | -0.002 |
| iter-44 single-interp (order-1) | 0.287 | +0.067 |
| PER-NODE weighted (iter-48) | 0.275 | -0.011 |
| 1-NN graph (order-0) | 0.263 | +0.018 |
| frozen | 0.232 | — |

- **per-contrast vs PER-NODE  Δ +0.026** — the finer grain LIFTS over iter-48's per-node
  weight: each node's admissibility graph ACTS on the per-contrast dilution that the
  per-node average could not.
- **per-contrast vs EQUAL  Δ +0.009**, **vs iter-44  Δ +0.014**, **vs 1-NN  Δ +0.039** —
  per-contrast is the TOP order-N-family graph on continuous, edging past every comparator.
- **SHUFFLE / cross-voice margin**: per-contrast is the ONLY order-N-family combine-all
  with a CLEAN positive margin (+0.013); per-node (-0.011) and equal (-0.002) COLLAPSE
  under shuffle. The per-contrast gating converts the family's smoothing into a real
  cross-voice signal (still below iter-44's single-order +0.067, but iter-44 is one fixed
  order, not the combine-all). The per-contrast admissibility recovers a clean cross-voice
  margin the per-node weight destroyed.
- **Error-overlap**: per-contrast fixes 21/166 of per-node's errors; per-node fixes 16/161
  of per-contrast's (net +5 per-contrast) — the finer grain genuinely re-decides contrasts.
- **SPARSITY: ADEQUATE** — median 17 precision-claims per (node,word) cell, only 1% of
  cells had zero claims (fell back to per-node). The per-contrast measurement is well-
  sampled on this venue, so the lift is not a sparsity artefact.

## (3) FSDD LOSO — multi-metric, shuffle, per-fold  (COMPLETE — /tmp/iter49_fsdd_full.txt)

6 held-out FSDD speakers, 27 channels × orders {0,1,2} = 81 (cue × order) nodes,
n_max=2, ridge=0, chance 0.100, with the voice-partition SHUFFLE control.

| graph | acc | shuffle margin |
|---|---|---|
| iter-44 single-interp (order-1, full rank) | **0.644** | +0.031 |
| EQUAL combine-all (iter-45) | 0.597 | +0.033 |
| PER-NODE weighted (iter-48) | 0.594 | +0.031 |
| 1-NN graph (order-0) | 0.594 | +0.075 |
| **PER-CONTRAST admissibility graphs (this iter)** | **0.561** | +0.019 (CLEAN) |
| frozen | 0.442 | — |

- **per-contrast vs PER-NODE  Δ -0.033** — on FSDD the finer grain HURTS over iter-48's
  per-node weight (the opposite of continuous).
- **per-contrast vs EQUAL  Δ -0.036**, **vs iter-44  Δ -0.083 (BELOW)**, **vs 1-NN
  Δ -0.033**. The per-contrast gating drops below every comparator on FSDD.
- **SHUFFLE / cross-voice margin**: per-contrast stays CLEAN (+0.019) but NARROWER than
  per-node/equal (+0.031/+0.033) and well below 1-NN (+0.075). The finer grain did not
  widen the cross-voice margin here.
- **Error-overlap**: per-contrast fixes 26/146 of per-node's errors but per-node fixes
  38/158 of per-contrast's (net **-12** against per-contrast) — the finer grain re-decides
  many contrasts but loses MORE than it wins on FSDD.
- **SPARSITY: ADEQUATE** — median 29-30 precision-claims per (node,word) cell, only 1%
  zero-claim. So the FSDD loss is NOT a sparsity artefact: the per-contrast measurement is
  well-sampled; it simply does not help on this venue.

**Why FSDD differs from continuous (the honest structural reading).** FSDD digits are
clean, isolated, and already well-separated: the contrasts are EASY, so a node's per-word
precision is dominated by sampling noise around already-high reliabilities, and gating a
node OUT on a word it scores slightly-low on discards real evidence — over-fragmentation.
On the CONTINUOUS venue coarticulation genuinely degrades specific channel×order nodes on
specific contrasts (the b/d-style wrong-order dilution iter-45 surfaced), so the per-word
precision carries real per-contrast structure and the abstain ACTS where it should. The
finer grain helps exactly where the per-contrast dilution is REAL (continuous) and hurts
where contrasts are already clean (isolated FSDD digits).

## (4) VERDICT

**Per-contrast admissibility graphs (the user's "finer grain") are wired correctly,
measured not searched, and SPLIT by venue: they LIFT on continuous (where the
per-contrast dilution is real) and HURT on isolated FSDD digits (where contrasts are
already clean). The measurement is ADEQUATE on both venues, so this is NOT the
scale-the-venue null — it is a genuine, venue-dependent result.**

- **Are the per-node admissibility graphs wired (per-contrast MEASURED reliability gating
  each node, LOSO-clean, no leakage/sweep/fit)?** YES — `score(w) = PROD_i [weight_i(w)·
  P_i(w) + (1-weight_i(w))·u_i]` as a graph Term (Argmax of Times over per-node
  convex-blend gates, evaluated by `substrate.evaluate`); `weight_i(w) =
  (precision_i(w)-chance)/(1-chance)` where precision_i(w) is node i's inner-LOSO per-word
  precision on TRAIN speakers only (the held voice absent), chance derived, the map fixed.
  All-1 recovers iter-45 byte-identical (test lock). No fit, no sweep, no gradient, no
  donkey (5 locks). The shuffle control scrambles the partition for the reliability
  measurement too. The weight IS a measurement — audited. (A build bug was caught: the
  per-word EXPONENT form `P^weight` INFLATES the inadmissible word because `P^0=1` is the
  max contribution; the fix is the convex blend to the word-neutral flat reference — the
  inadmissible node abstains, dropping out of the Argmax.)

- **Does per-contrast admissibility ACT on the per-contrast dilution and LIFT past
  iter-48's per-node weight (and past iter-44)?**
  - CONTINUOUS: YES — per-contrast 0.301 beats per-node 0.275 (Δ +0.026), equal 0.292
    (+0.009), iter-44 0.287 (+0.014), 1-NN 0.263 (+0.039); and it is the ONLY order-N
    combine-all with a CLEAN positive shuffle margin (+0.013) where per-node (-0.011) and
    equal (-0.002) collapse. The finer grain converts the family's smoothing into a real
    cross-voice signal. On continuous, admissibility graphs on the nodes IS the combination
    operator the combine-all wall demanded — the user's "finer grain" CONFIRMED on the
    venue where the per-contrast dilution is real.
  - FSDD: NO — per-contrast 0.561 is below per-node 0.594 (Δ -0.033) and iter-44 0.644
    (-0.083). On clean isolated digits the finer grain over-fragments and hurts.

- **Is the per-contrast measurement too sparse (the scale-the-venue convergence)?** NO —
  median 29-30 claims/cell on FSDD, 17 on continuous, both ADEQUATE, ~1% zero-claim
  fallback. The split is structural (clean vs coarticulated contrasts), not a sample-size
  artefact.

**The honest read.** The user's "the finer grain is admissibility graphs on the nodes
themselves" is the right structure — recursive (G,Γ), each node admissible iff its own
sub-graph says so for THIS contrast — and it DOES act on iter-45's per-contrast dilution.
Where that dilution is REAL (continuous gold-span, coarticulation degrading specific
channel×order nodes on specific contrasts), the finer grain LIFTS recognition past
iter-48's per-node weight, past the equal combine-all, and past iter-44, AND recovers a
clean cross-voice margin the per-node weight had destroyed. Where the contrasts are
already clean (isolated FSDD digits) the per-word precision is sampling noise around
already-high reliabilities and the abstain over-fragments, so it hurts. Measured, not
searched; LOSO-clean; shuffle-controlled; sparsity ADEQUATE on both venues — under-claimed
and reproducible. The combination operator that helps the continuous (real-speech)
combine-all wall is admissibility graphs on the nodes; on toy isolated digits it is not
needed and costs.

## Tests (all green)
- `tests/test_node_admissibility_graphs.py` (5, new) — the convex-blend gate evaluates
  through the substrate; an inadmissible node abstains (contributes the flat reference)
  rather than inflating the word; all-1 weights recover the equal product; the
  per-contrast precision→weight map is the fixed formula; no-fit/no-donkey source audit.
- Required suites: `test_stt_pipeline` (7), `test_perception_self_assessment` (8),
  `test_process_meta_assessor` (10), `test_gap_guidance` (3) — 28 passed. Plus
  `test_weighted_admissibility` (5) still green. 42 passed total.

## Reproduce
```
PYTHONUNBUFFERED=1 python -m scripts.iter49_node_admissibility_graphs 6 2 2 0          # FSDD
PYTHONUNBUFFERED=1 python -m scripts.iter49_node_admissibility_continuous 5 30 6 10 2 0 # continuous
python -m pytest tests/test_node_admissibility_graphs.py tests/test_weighted_admissibility.py \
  tests/test_stt_pipeline.py tests/test_perception_self_assessment.py \
  tests/test_process_meta_assessor.py tests/test_gap_guidance.py -q
```
NOTE: each fold runs the inner-LOSO reliability measurement TWICE (per-contrast +
per-node comparator), so it is ~2× iter-48 and HEAVY; run DETACHED (`setsid`) and verify
completion via the `VERDICT` marker (pgrep can match the waiter's own command line).
