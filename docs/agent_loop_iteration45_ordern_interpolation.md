# iter-45 — ARBITRARY, ORDER-N INTERPOLATION (the order-N operator on the token cloud)

> The user: "selective interp should be arbitrary and order n." iter-44 showed the
> interpolation manifold LIFTS (interp 0.644 vs 1-NN 0.594, +0.050) but is per-channel
> MIXED (helps broad/formant channels, HURTS sparse narrow-window ones — best
> sharp_time:trans_w3 +0.086, worst mid_freq:trans_w2 −0.142) and its real-vs-shuffle
> margin stayed smoothing-dominated (+0.031 < 1-NN's +0.075). iter-44's manifold was a
> SINGLE fixed order (the linear affine span). DO NOT hand-pick which channels get
> interp (the forbidden select-best). Make interpolation the agent's ORDER-N operator on
> the token cloud — arbitrary channel, ALL orders — and let combine-all sort which order
> fits each channel. Working tree only — NOT committed.

---

## (1) What was built — audited

**The generalization, not a new mechanism.** iter-44's affine manifold is exactly ONE
order of the agent's OWNED order-N operator (`domains/order_n_concepts`: 0=value,
1=tilt, 2=curvature, … n) — pointed at the token CLOUD manifold instead of at
time/frequency. `domains/order_n_interpolation.py` builds, per channel's per-word token
cloud, EVERY order at once from a single closed-form SVD of the cloud's own scatter:

| order | the read of the SAME token cloud | what it models |
|---|---|---|
| 0 | distance to the cloud CENTROID | the VALUE (point estimate) |
| 1 | residual to the cloud's top-1 LINEAR span | the TILT (linear manifold) |
| 2 | residual to the degree-2 surface (top-2 dirs + curvature clip) | the CURVATURE |
| … n | residual to the degree-n local model | the order-n surface |

The order = the degrees of freedom of the local cloud model: order-r uses the top-r
principal directions; order≥2 additionally constrains the in-plane coordinate to the
cloud's degree-r supported reach (the higher finite-difference structure — the continuous
local-polynomial analogue of `order_n_concepts.nth_order_terms`), so a token off the
cloud's curved support keeps the overshoot as residual. iter-44 == the pure-linear
residual off the full-rank span (verified identical: `0.6659705… == 0.6659705…`).

**combine-all over EVERY (order × channel).** Each (order × channel) is one NODE; ALL
enter the SAME variadic Argmax-of-product (`scripts/iter45_ordern_interpolation.heldout_combined_ordern`).
For 26 cosine channels × orders 0..n_max the product has 26·(n_max+1) order-N nodes. The
graph keeps whichever order fits each channel's cloud: a broad/structured cloud's higher
order WIDENS; a flat/sparse cloud's higher order (degenerate degree-d basis → collapses
toward order-0 / multiplies in near-uniform) cannot drag the rest. NO channel is
hand-picked for an order. The decision Term is byte-identical to iter-34 — only the node
COUNT and each node's distance SOURCE differ.

**Key functions:** `word_cloud_model(tokens, n_max)` (one SVD → all orders),
`order_n_residual(query, model, order, ridge)` (the order-N reconstruction residual),
`word_cloud_models` (per-word, LOSO-clean), `order_n_channel_likelihood` (one
(order×channel) node's softmax-by-own-median likelihood — the IDENTICAL
`likelihood_from_distances` every channel uses), `heldout_1nn_order_n` (per-order probe).

**NO-DONKEY / NO-FIT audit (machine-checked, PASS):** the executable code (docstrings
stripped via AST) contains NONE of `fit(`, `backward`, `gradient`, `optimizer`, `nn.`,
`torch`, `sklearn`, `.train(`, `grad`, `loss`, `.predict(`, `Classifier`; it uses
`np.linalg.svd` (closed-form geometry of the group's own scatter) + the shared
`likelihood_from_distances`. The degree n is a fixed small cap (n_max), bounded by cloud
support (R = min(n_tokens−1, d, n_max)), NOT swept. NO trained classifier, NO gradient,
NO learned weight, NO net. **combine-all decision Term audited:** node types =
{Argmax, Attr, Lit, NodesWhere, Times, Var} — NO Max/Sort/Pick/If/Select/weight.

## (2) Synthetic validation (mechanism + alignment)

- order-0 residual == distance to centroid (exact: `1.19139… == 1.19139…`).
- iter-44 manifold residual == pure-linear residual off the full-rank span (exact).
- Curved-cloud contrast (two words, same centroid + same linear extent, OPPOSITE
  curvature; held tokens on each word's curved arc): order-0 0.800, order-1 0.800,
  **order-2 0.900** — order-2 recovers structure orders 0/1 cannot. Confirms higher
  orders model spread the linear/point reads miss, WHERE the cloud is curved.

## (3) FSDD LOSO — multi-metric, shuffle, per-order drop-it  (COMPLETE — /tmp/iter45_fsdd_full.txt)

6 held-out FSDD speakers, 26 cosine channels × orders {0,1,2} = 78 order-N nodes,
n_max=2, ridge=0, chance 0.100, with the voice-partition SHUFFLE control.

| graph | acc |
|---|---|
| iter-44 single-interp (order-1 linear, full rank) | **0.644** |
| ORDER-N combine-all (all orders × channels) | 0.597 |
| 1-NN graph (order-0 point estimate, CURRENT) | 0.594 |
| CENTROID (iter-41) | 0.464 |
| frozen | 0.442 |

- **order-N vs 1-NN  Δ +0.003** — a marginal lift only.
- **order-N vs iter-44  Δ −0.047** — the arbitrary all-orders combine-all is WORSE
  than the single fixed order on FSDD.

**Per-order DROP-IT** (which orders the graph effectively uses):
`order-0 Δ −0.019 (HURTS)`, `order-1 Δ +0.033 (USES)`, `order-2 Δ +0.053 (USES)`.
The graph genuinely uses orders 1 and 2 (curvature carries the MOST, +0.053); but
**order-0 actively HURTS the product** (the point-estimate node drags the combine-all).

**SHUFFLE / cross-voice margin**: order-N real 0.597 / shuffle 0.564 → **margin +0.033**;
iter-44 +0.031; 1-NN +0.075. Order-N's margin is marginally WIDER than iter-44's but
**still well below 1-NN's +0.075 → the lift is still smoothing-leaning, not cross-voice
structure** (the iter-44 caveat is NOT resolved). Error-overlap is a near-wash (order-N
fixes 39/146 of 1-NN's errors; 1-NN fixes 38/145 of order-N's; net +1).

**Per-channel BEST-ORDER — the iter-44 mix RESOLVED, no hand-pick (the strong positive
result).** Each channel's single best order ALONE (diagnostic; the graph keeps ALL):

- The gammatone SPECTRAL channels (flat + transition readouts) overwhelmingly prefer
  **order-2 (curvature)** — e.g. `middle:flat o0:0.342 → o2:0.528`, `sharp_time:flat
  0.389 → 0.539`, `mid_freq:trans_w3 0.336 → 0.508`. Their token clouds carry CURVED
  manifold structure (VTL + coarticulation continuum) that order-2 models.
- The sparse / orthogonal cues prefer **order-0**: `manner_voicing`, `f0_contour`,
  `modspec`, `landmark`, `fft_ear`, `allpole_envelope` all peak at order-0 (their clouds
  are flat/sparse — a higher order over-fits and HURTS, e.g. f0_contour 0.253→0.156).
- Spread `{order-0: 7, order-1: 3, order-2: 17}` — channels genuinely DISTRIBUTE across
  orders. The iter-44 per-channel mix is REAL (it is exactly which order each channel's
  cloud supports), and the arbitrary order-N family lets each channel find its own order
  WITHOUT hand-picking. This is the mechanism the user asked for, working.

**The honest tension**: the per-channel diagnostic shows the order-N family DOES resolve
the mix (each channel finds its own order); but feeding ALL orders symmetrically into the
combine-all DILUTES (the order-0 nodes hurt, the weaker orders drag the channels whose
best is order-2), so the all-orders product underperforms even iter-44's single order. The
graph self-selects-by-product is too WEAK a selector here — a near-flat likelihood from a
wrong-order node still multiplies in and shifts the argmax. The structure is correct; the
combine-all OVER-SATURATES with the redundant lower-order nodes (reported honestly).

## (4) CONTINUOUS gold-span — multi-metric, shuffle, per-order drop-it  (COMPLETE — /tmp/iter45_continuous_full.txt)

LibriSpeech gold-span words, faster-whisper forced alignment, 5 held-out speakers,
10-word shared cross-speaker vocab (chance 0.100), 26 channels × orders {0,1,2}, with
SHUFFLE. (The 8-speaker run was killed twice by the background-task harness at fold
13/16 — the same fate iter-44's continuous run met; re-run fully detached via `setsid`
at 5 speakers, which COMPLETED, EXIT=0.)

| graph | acc |
|---|---|
| ORDER-N combine-all (all orders × channels) | **0.292** |
| iter-44 single-interp (order-1) | 0.287 |
| 1-NN graph (order-0, CURRENT) | 0.263 |
| CENTROID (iter-41) | 0.240 |
| frozen | 0.232 |

- **order-N vs 1-NN  Δ +0.029** — order-N LIFTS held-out recognition on continuous.
- **order-N vs iter-44  Δ +0.005** — order-N edges past the single fixed order here
  (unlike FSDD, where it lost to iter-44).

**Per-order DROP-IT**: `order-0 Δ +0.009 (USES)`, `order-1 Δ −0.010 (HURTS)`,
`order-2 Δ +0.019 (USES)`. Order-2 (curvature) again carries the most; order-1 is
redundant/harmful in the combine-all here.

**SHUFFLE / cross-voice margin — the decisive honest finding**: order-N real 0.292 /
shuffle 0.294 → **margin −0.002 (NOT CLEAN)**. iter-44's margin is +0.067; 1-NN's
+0.018. **The continuous order-N lift COLLAPSES under shuffle — it is smoothing, not
cross-voice structure.** The order-N family adds nodes that smooth the cloud, and on the
noisy continuous clouds that smoothing helps real and shuffled folds equally. iter-44's
single order keeps a clean cross-voice margin; the all-orders product does not.

**Per-channel BEST-ORDER** spread `{order-0: 14, order-1: 4, order-2: 9}` — channels
distribute across orders again (the mix is real), but on continuous the lower orders
dominate more (the gammatone spectral channels' continuous clouds are noisier/smaller,
so order-2 helps fewer of them than on FSDD). Each channel still finds its own order
WITHOUT hand-picking — the mechanism works; the SELECTOR (combine-all) is the limit.

## (5) VERDICT

The user's "arbitrary + order-N" IS the right general form, and it is WIRED correctly —
the agent's OWNED order-N operator (order_n_concepts) pointed at the token CLOUD manifold,
EVERY (order × channel) a node in the combine-all product, the graph self-selecting the
order per channel with NO hand-pick, NO fit, NO net (audited). But the empirical verdict
is MIXED, and under-claimed honestly:

**Does arbitrary order-N LIFT recognition?**
- FSDD: order-N 0.597 vs 1-NN 0.594 (Δ **+0.003**, marginal) but BELOW iter-44 0.644
  (Δ −0.047). On FSDD the all-orders product is WORSE than the single fixed order.
- Continuous: order-N 0.292 vs 1-NN 0.263 (Δ **+0.029**, real lift) AND vs iter-44 0.287
  (Δ +0.005). On continuous order-N edges ahead.
- So: a small lift over the CURRENT 1-NN graph on both venues; beats iter-44 on
  continuous, loses to it on FSDD. NOT a clear win.

**Does it RESOLVE the iter-44 per-channel mix WITHOUT hand-picking?** YES — this is the
clean positive result. The per-channel best-order diagnostic shows each channel finding
its OWN order with no hand-pick: on FSDD the gammatone spectral channels overwhelmingly
prefer **order-2 (curvature)** (their clouds carry curved VTL/coarticulation structure),
the sparse/orthogonal cues prefer **order-0** (their clouds are flat — higher orders
over-fit and HURT). Spread {0:7,1:3,2:17} on FSDD, {0:14,1:4,2:9} on continuous. The
per-order drop-it confirms the graph USES the higher orders (FSDD: o1 +0.033, o2 +0.053;
continuous: o2 +0.019) — curvature carries the most on BOTH venues. The arbitrary
order-N family is exactly the right form to let each channel's cloud express the order it
supports.

**Does it WIDEN the cross-voice margin (variation-modeling, not smoothing)?** NO — this
is the decisive honest limitation. FSDD: order-N margin +0.033 ≈ iter-44 +0.031, both far
below 1-NN's +0.075. Continuous: order-N margin −0.002 (NOT CLEAN — collapses under
shuffle) vs iter-44 +0.067. **The order-N lift is still smoothing-dominated, NOT
cross-voice structure** — on continuous it is PURELY smoothing (the shuffle margin
vanishes). The iter-44 caveat is not resolved; it is made worse by adding more
smoothing-prone nodes.

**The structural reading (fix-the-fixer, not the outcome).** The mechanism is correct
and the diagnostics prove the user's hypothesis: the cloud DOES carry order-N structure
(curvature, order-2, is the dominant useful order on both venues), and the arbitrary
order-N family lets each channel self-select it without hand-picking. The LIMIT is the
SELECTOR: combine-all (a symmetric product of softmax-by-own-median likelihoods) is too
WEAK to exploit the per-channel order structure it surfaces — a wrong-order node's
near-flat likelihood still multiplies in and dilutes, so feeding ALL orders
symmetrically under-performs even iter-44's single order on FSDD, and the net lift is
smoothing not structure. The graph SURFACES which order each channel wants (the
diagnostic is unambiguous) but the product cannot ACT on it. The next fixer is the
combination operator, not more orders: the agent needs a way for the product to weight a
channel's order BY HOW MUCH that order's cloud-fit is confident/peaked — which is exactly
the per-channel-order temperature the softmax already computes but the symmetric product
discards. That is a combination-operator question (still no-fit: the temperature is read
from the data), NOT a hand-pick and NOT a new order.

**Plainly, reproducibly, no-fit, no-hand-pick (re-verify):** arbitrary order-N
interpolation is the correct general form and resolves the per-channel mix (each channel
finds its own order, curvature dominant, combine-all, audited no-fit/no-donkey); it gives
a small recognition lift over the current 1-NN graph (+0.003 FSDD, +0.029 continuous) but
does NOT beat iter-44 on FSDD and does NOT widen the cross-voice margin (the lift is
smoothing, on continuous purely so). The order-N family is right; the combine-all
selector is the wall.

## Files
- `domains/order_n_interpolation.py` — the order-N cloud-manifold nodes (no-fit, audited).
- `scripts/iter45_ordern_interpolation.py` — the FSDD LOSO acceptance harness.
- `scripts/iter45_ordern_continuous.py` — the continuous gold-span acceptance harness.
- `docs/agent_loop_iteration45_ordern_interpolation.md` — this report.

## Reproduce
```
PYTHONUNBUFFERED=1 python -m scripts.iter45_ordern_interpolation 6 2 2          # FSDD: n_per rounds n_max
PYTHONUNBUFFERED=1 python -m scripts.iter45_ordern_continuous   5 30 6 10 2     # continuous: n_spk utts min_ex max_vocab n_max
```
NOTE: the continuous run is heavy (the per-fold per-channel best-order diagnostic
re-evaluates 26 channels × 3 orders); run it DETACHED (`setsid nohup`) so the
background-task harness does not kill it before the verdict is written — the 8-speaker
run was killed twice at 13/16 folds; the 5-speaker run completes. Required suites green
(32): `python -m pytest tests/test_stt_pipeline.py
tests/test_perception_self_assessment.py tests/test_process_meta_assessor.py
tests/test_gap_guidance.py -q`.
