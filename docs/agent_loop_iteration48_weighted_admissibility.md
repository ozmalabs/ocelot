# iter-48 — the WEIGHTED ADMISSIBILITY RULE GRAPH

> The user: "they need weight — almost like a weighted admissibility rule graph."
> iter-45 found the wall: the EQUAL symmetric Argmax-of-product over every (cue x order)
> node SURFACES which order each channel wants (the per-channel best-order diagnostic is
> unambiguous) but CANNOT ACT on it — a wrong-order node is informative-but-WRONG
> (peaked at the wrong word, NOT near-flat), so it DILUTES the product. The fix: weight
> each (cue x order) node by its MEASURED reliability so the product can down-weight the
> unreliable toward 1 (P^0 = flat, can't dilute). Working tree only — NOT committed.

---

## The form

    score(w) = PROD_i  P_i(w) ^ weight_i              (a graph Times of Pow terms)
    predict(s) = Argmax_w score(w)
    weight_i = max(0, (acc_i - chance) / (1 - chance))

A reliable node (weight -> 1) counts in full; a wrong-order/unreliable node (weight ->
0) is raised toward P^0 = 1 (flat regardless of how peaked-wrong it was) so it CANNOT
dilute the product. The structure stays binary-admissible (every node is in the
product); the RULES carry weights. The equal combine-all (iter-45) is the special case
weight_i == 1 for all i (verified: weighted(w=1) == equal, byte-identical).

## The in-thesis line — weights MEASURED, not searched (the hard constraint)

`weight_i` is the agent's MEASURED reliability:
- `acc_i` = node i's held-out accuracy MEASURED ON THE TRAIN FOLDS ONLY (inner
  leave-one-speaker-out over the train speakers — the same yardstick iter-42 used). The
  outer-held voice is absent from train entirely (LOSO-clean, NO test leakage).
- `chance` = 1/n_candidates — DERIVED, not a knob.
- the map `(acc - chance)/(1 - chance)` is the fixed above-chance reliability
  normalisation — NO free parameter, NO sweep, NO gradient, NO fit. The accuracy is a
  MEASUREMENT (the same per-node argmax-likelihood the harness scores with).

We do NOT try weight values and keep the best (the forbidden negative-space search).
iter-45's per-channel best-order diagnostic IS this reliability map — surfaced as a
measurement, now ACTED on.

## Files
- `domains/weighted_admissibility.py` — the weighted score Term (Times of Pow),
  `weight_attr`, `reliability_to_weight` (the fixed map). No-fit.
- `scripts/iter48_weighted_admissibility.py` — the FSDD LOSO acceptance harness
  (`measure_node_reliabilities` = inner-LOSO on train; `heldout_combined_weighted` =
  the weighted product).
- `scripts/iter48_weighted_continuous.py` — the continuous gold-span acceptance harness.
- `tests/test_weighted_admissibility.py` — the no-fit / Pow-through-graph / equal-weight
  locks.
- `docs/agent_loop_iteration48_weighted_admissibility.md` — this report.

---

## (1) What was built — audited

`domains/weighted_admissibility.py`:
- `weighted_score_term(n)` = `Times([Pow(Attr(w, p_ch{i}), Attr(w, w_ch{i})) for i])`
  — the reliability-weighted product as a graph Term, evaluated by `substrate.evaluate`
  via `Pow` (the Rust `TermNode::Pow` does `powf` for float exponents; the JSON term
  parser accepts `Pow{a,b}` — both verified). `predict_weighted_term` = the Argmax.
- `reliability_to_weight(acc, chance) = max(0, (acc - chance)/(1 - chance))` — the fixed
  (no-parameter) above-chance reliability map.

`scripts/iter48_weighted_admissibility.py`:
- `measure_node_reliabilities` = the inner leave-one-speaker-out on the TRAIN folds
  only: per (order x channel) node, hold out one train speaker, build the node's
  per-word cloud model from the remaining train speakers, predict the held-out train
  speaker's tokens with that single node, average over inner folds -> acc -> weight.
- `heldout_combined_weighted` = the weighted product over the SAME (order x channel)
  nodes as iter-45.

**Equal-weight special case recovers iter-45 EXACTLY** (smoke test):
`weighted(weights=1) == equal combine-all`, byte-identical (0.7500 == 0.7500). So the
ONLY change from iter-45 is each node's likelihood raised to its measured weight.

**The weight IS a measurement, not a searched param (audited):** weight =
`(acc - chance)/(1 - chance)`; `chance = 1/n_candidates` is DERIVED; `acc` is the node's
inner-LOSO accuracy on TRAIN speakers (the same argmax-likelihood the harness scores
with). NO weight value is tried-and-kept; NO fit/gradient/optimizer; the map has no free
parameter. LOSO-clean: the outer-held voice is absent from train entirely, so no
reliability measurement ever touches the test fold. The shuffle control scrambles the
voice partition for the reliability measurement TOO (the inner-LOSO groups by the
shuffled buckets).

## (2) FSDD LOSO — multi-metric, shuffle, per-fold  (COMPLETE — /tmp/iter48_fsdd_full.txt)

6 held-out FSDD speakers, 27 channels x orders {0,1,2} = 81 (cue x order) nodes,
n_max=2, ridge=0, chance 0.100, with the voice-partition SHUFFLE control.

| graph | acc |
|---|---|
| iter-44 single-interp (order-1, full rank) | **0.644** |
| EQUAL combine-all (iter-45, all orders x channels) | 0.597 |
| **WEIGHTED admissibility graph (this iter)** | **0.594** |
| 1-NN graph (order-0 point estimate) | 0.594 |
| frozen | 0.442 |

- **weighted vs EQUAL  Δ -0.003** — weighting by measured reliability does NOT lift over
  the equal combine-all; it marginally HURTS.
- **weighted vs iter-44  Δ -0.050** — below the single fixed order (does NOT beat 0.644).
- **weighted vs 1-NN  Δ +0.000** — tied with the current point-estimate graph.

**SHUFFLE / cross-voice margin**: weighted real 0.594 / shuffle 0.564 -> margin +0.031
(CLEAN); equal +0.033; iter-44 +0.031; 1-NN +0.075. **The weighting did NOT widen the
cross-voice margin** — essentially identical to the equal product's margin, both still
well below 1-NN's +0.075. The smoothing-vs-structure problem is NOT fixed.

**The weighting genuinely ACTS (the measurement is real and on-target):** the measured
weights are monotone by order — order-0 0.260 < order-1 0.310 < order-2 0.343 (mean over
folds x channels), with real spread (range 0.05-0.58). This MATCHES iter-45's
unambiguous diagnostic (curvature / order-2 is the most reliable order on FSDD); the
reliability measurement recovered it cleanly, LOSO-clean. So the weights are correct and
they act — they just do not lift recognition.

**Error-overlap**: weighted fixes 9/145 of equal's errors; equal fixes 10/146 of
weighted's (net -1) — a near-perfect wash.

## (3) WHY the weighting does not lift (the honest structural reading)

The weights act but GENTLY, and the gentleness is forced by the data, not by a knob:
- Every node's inner-LOSO accuracy sits in a NARROW band (0.33-0.46 mean by order; no
  channel/order is near chance, none is near perfect). So `(acc - chance)/(1 - chance)`
  maps them ALL into 0.05-0.58 — no node is driven to weight 0 (full abstain) and none
  to weight 1 (full say). The reliable/unreliable CONTRAST the weighting needs to
  suppress a wrong-order node is small, because on FSDD the nodes are all
  moderately-and-similarly reliable.
- iter-45's wall was a wrong-order node that is "informative-but-WRONG" (peaked at the
  wrong word). A per-NODE reliability weight can only down-weight that node by its
  AVERAGE reliability over all queries — but a node that is right on most words and wrong
  on a few has HIGH average reliability, so its weight stays high and it keeps diluting on
  the few words it gets wrong. Per-node reliability is the wrong GRANULARITY to fix a
  per-query/per-contrast wrong-order dilution.

So "they need weight" is the right INSTINCT but per-node measured reliability is too
COARSE a weight to act on iter-45's specific wall. The fixer is not the weight VALUE (it
is correctly measured) but the weight's GRANULARITY: the dilution is per-(query x
contrast), the reliability is per-node.

## (4) CONTINUOUS gold-span — multi-metric, shuffle, per-fold  (COMPLETE — /tmp/iter48_continuous_full.txt)

LibriSpeech gold-span words, faster-whisper forced alignment, 5 held-out speakers,
10-word shared cross-speaker vocab (chance 0.100), 27 channels x orders {0,1,2}, SHUFFLE.

| graph | acc |
|---|---|
| EQUAL combine-all (iter-45) | **0.292** |
| iter-44 single-interp (order-1) | 0.287 |
| **WEIGHTED admissibility graph (this iter)** | 0.275 |
| 1-NN graph (order-0) | 0.263 |
| frozen | 0.232 |

- **weighted vs EQUAL  Δ -0.017** — weighting HURTS over the equal combine-all here too.
- **weighted vs iter-44  Δ -0.012** — below the single fixed order.
- **weighted vs 1-NN  Δ +0.012** — a small lift over the current point-estimate graph.

**SHUFFLE / cross-voice margin**: weighted real 0.275 / shuffle 0.286 -> margin -0.011
(NOT CLEAN — collapses under shuffle); equal -0.002; iter-44 +0.067; 1-NN +0.018. As in
iter-45's continuous run, the order-N family's lift is smoothing not cross-voice
structure, and the weighting does not fix that (iter-44's single order keeps the only
clean cross-voice margin).

**Why the weighting is even weaker on continuous**: the per-node inner-LOSO accuracies
are all near chance (order-0 0.198, order-1 0.189, order-2 0.192) — and crucially NOT
monotone by order (unlike FSDD where order-2 clearly led). So the reliability map gives
near-flat weights (0.099-0.109) AND cannot even pick out a good order — the continuous
clouds are too noisy/small for the per-node reliability to carry order structure.

## (5) VERDICT

**The user's "they need weight" is wired correctly, derived not searched, but does NOT
lift recognition — a clean negative result on BOTH venues.**

- **Is the weighted combine wired with MEASURED weights (no leakage/sweep/fit/gradient)?**
  YES — `score(w) = PROD_i Pow(P_i(w), weight_i)` as a graph Term (Argmax of Times-of-Pow,
  evaluated by `substrate.evaluate`); `weight_i = (acc_i - chance)/(1-chance)` where acc_i
  is the node's inner-LOSO accuracy on TRAIN speakers only (the held voice absent), chance
  derived, the map fixed. Equal-weight recovers iter-45 byte-identical. No fit, no sweep,
  no gradient, no donkey (5 locks in `tests/test_weighted_admissibility.py`). The shuffle
  control scrambles the partition for the reliability measurement too. The weight IS a
  measurement, NOT a searched param — audited.

- **Does weighting by measured reliability ACT on the per-channel/order selection?**
  YES on FSDD — the measured weights are monotone by order (o0 0.260 < o1 0.310 < o2
  0.343), exactly recovering iter-45's curvature-dominant diagnostic, LOSO-clean. The
  measurement is correct and it acts. On continuous the weights are near-flat (all ~0.10)
  because the continuous node accuracies are all near chance and non-monotone — the
  measurement is honest (it reports the nodes are barely reliable) but has no order
  structure to act on.

- **Does it LIFT recognition over the equal combine-all? NO.**
  FSDD: weighted 0.594 vs equal 0.597 (Δ -0.003). Continuous: weighted 0.275 vs equal
  0.292 (Δ -0.017). Marginally HURTS on both. It does NOT beat iter-44 (0.644 FSDD /
  0.287 continuous). It does NOT widen the cross-voice margin (FSDD +0.031 ≈ equal +0.033,
  both below 1-NN +0.075; continuous -0.011, NOT clean). It ties/marginally beats the
  current 1-NN graph (Δ +0.000 FSDD, +0.012 continuous).

**The honest structural reading (fix-the-fixer).** Per-node measured reliability is the
WRONG GRANULARITY to act on iter-45's wall. iter-45's wall is a wrong-order node that is
"informative-but-WRONG" — peaked at the wrong word on a SPECIFIC contrast. A per-node
reliability weight can only down-weight that node by its AVERAGE reliability over ALL
queries; a node that is right on most words but confidently wrong on a few has HIGH
average reliability, so its weight stays high and it KEEPS diluting on exactly the
contrasts that matter. The dilution iter-45 surfaced is per-(query × contrast); the
reliability weight is per-node — too coarse to suppress it. The weights are correctly
measured and they act, but the action is at the wrong resolution to fix the wall.

So: "they need weight" is the right instinct, and the weighted admissibility rule graph
is the right STRUCTURE (binary-admissible nodes, rules carrying measured weights, the
combination a graph Term), built and validated no-fit/no-leakage/no-sweep. But per-node
measured reliability is too coarse a weight to convert iter-45's per-contrast wrong-order
dilution into a recognition lift. The fixer is the weight's GRANULARITY (per-query or
per-contrast reliability — still a measurement, not a sweep), NOT the weight value (which
is correct) and NOT more orders. Reported plainly, both venues, with shuffle, weights
proven to be measurements.

## Tests (all green)
- `tests/test_weighted_admissibility.py` (5, new) — Pow evaluates through the substrate;
  the reliability→weight map is the fixed formula; weight-0 makes a node flat (abstain);
  equal weights pick the same word as the equal product; no-fit/no-donkey source audit.
- Required suites: `test_stt_pipeline` (7), `test_perception_self_assessment` (8),
  `test_process_meta_assessor` (10), `test_gap_guidance` (3) — 28 passed.

## Reproduce
```
PYTHONUNBUFFERED=1 python -m scripts.iter48_weighted_admissibility 6 2 2          # FSDD
PYTHONUNBUFFERED=1 python -m scripts.iter48_weighted_continuous   5 30 6 10 2     # continuous
python -m pytest tests/test_weighted_admissibility.py tests/test_stt_pipeline.py \
  tests/test_perception_self_assessment.py tests/test_process_meta_assessor.py \
  tests/test_gap_guidance.py -q
```
NOTE: each fold runs the inner-LOSO reliability measurement (27 channels × n_inner
speakers × 3 orders) and is HEAVY; run DETACHED (`setsid`) so the background-task harness
does not kill it before the verdict is written. Verify completion via the `VERDICT`
marker in the output file (pgrep can match the waiter's own command line).
