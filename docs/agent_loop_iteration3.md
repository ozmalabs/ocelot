# Autopoietic loop — iteration 3

Turn the crank a third time: the agent picks + forward-builds the next open gap it
derived. This iteration produced **one real loop-mechanism result** (a diversification
fix the loop genuinely lacked) and **one honest negative on the recognition gap** (the
forward-built boundary fix is correct science but not the binding constraint). Numbers
below are from LIVE output, not prose.

## 1. PICK — what the agent's ranker chose, and why it landed there

### The diversification flag (a REAL loop gap, flagged plainly)

The agent's graph-resident ranker (`domains/gap_prioritiser.py`) scores each
`CapabilityAxis` by compression payoff = number of held postulates it unifies. Live
ranks (agent's own openness selector, `synthesize_over_all(prune=True)`, which drops
already-IMPLEMENTED capabilities — LPC, speaker-norm, coarticulation, cepstral, etc.):

```
OPEN-ONLY RANK (prune=True)
  payoff=6 score=5999  ['unsupervised-clustering', 'cross-speaker-clustering']
  payoff=4 score=3999  ['transitional probability', 'word-scale chunking']
```

Exactly the 2 open gaps. **Clustering (payoff 6) re-wins** — but it was ALREADY BUILT
(iter-1, `domains/cross_speaker_clustering.py`) and attempted TWICE (purity 0.441 then
0.460 with the LPC front-end), still below the raw-spectrum baseline 0.483. The loop
had **NO "attempted -> diminishing -> move on" signal**: verified live, the only
feedback edge was `blocked_by` (which *boosts* a blocker). Replaying iter-2's feedback,
the ranker even re-picked the already-CLOSED LPC axis at eff_score 7999, because
`blocked_by` lent it clustering's payoff and nothing recorded that LPC was built. So the
loop would re-pick already-built gaps forever.

**This is the same class of gap the missing prioritiser was** (a loop-mechanism hole,
not a domain hole). FLAGGED, and fixed (intervention, see below): a move-on signal so
the agent advances to the next UN-built gap.

### After the fix — the agent advances to word-scale chunking (live)

```
record clustering attempts (0.441 -> 0.460, baseline 0.483) + mark move-on
OPEN rank, AFTER move-on signal:
  eff_score=3999     ['transitional probability', 'word-scale chunking']
  eff_score=-994001  ['unsupervised-clustering', 'cross-speaker-clustering'] EXHAUSTED
  PICK NOW: ['transitional probability', 'word-scale chunking', 'statistical segmentation']
  ADVANCED to word-scale chunking? True
```

The pick is the native Argmax over the penalised score Term — the decision is in the
graph, not Python. **The agent picked WORD-SCALE CHUNKING** — the actual
continuous-speech recognition loss (`CONTINUOUS_SPEECH_FINDINGS.md`: TP-trough chunker
over-segments ~8x, chunks-per-word 7.71, lexicon purity 0.179).

## 2. BUILD — the forward-built fix (composed vs adapter-math)

The agent forward-builds from the SAME `statistical_learning` science it already
grounded (Saffran/Aslin/Newport), read more faithfully. The original chunker
(`domains/forward_segmentation.py`) cuts at every BELOW-RUNNING-MEDIAN transition — i.e.
~half of ALL transitions. A genuine word boundary is a **LOCAL MINIMUM** of TP (a true
trough: TP below BOTH neighbours) — exactly the agent's own order-1 sign-change concept
(`order_n_concepts`) applied to the TP curve.

- **Composed (graph-resident):** `local_min_boundary_term` —
  `Filter(transitions, t, And(Lt(t.tp, t.prev_tp), Lt(t.tp, t.next_tp)))`. The boundary
  DECISION is a Term the agent evaluates natively (`substrate.evaluate`), same pattern
  as `recognition_graph` / the existing `boundary_term`. Built from And/Lt/Attr/Filter,
  all already in `term.rs`. No new Rust primitive needed.
- **Adapter-math (mechanical I/O):** each `Transition` carries `prev_tp`/`next_tp` scalar
  attrs (the same kind of structure translation as `tp` itself; sequence-ends get a
  sentinel-high value). `boundary_mode="local_min"` threads through
  `find_boundaries_via_graph` / `segment_pass` / `forward_segment`. Default stays
  `"median"` so existing behaviour/tests are untouched.

Synthetic validation (clean bimodal TP): 40 true words -> **40 chunks (1.0/word)**, and
the chunks ARE the words (ABC, DE, FGH). The Term works and isolates word boundaries
when the TP curve is clean.

## 3. MEASURE — honest, live, on real LibriSpeech

`scripts/word_scale_chunking_probe.py`, 60 train utts / 13 speakers, K=48, held-out
speakers, both modes on the SAME pipeline (gammatone -> invariant transform -> k-means
codebook -> graph forward chunker -> DTW chunk->word lexicon):

```
metric                          MEDIAN (old)   LOCAL-MIN (new)
chunks-per-word (->1.0)                 7.21              7.07
cluster purity (->1.0)                 0.283             0.290
  MULTI-member purity                  0.235             0.234
BASELINE (findings): chunks-per-word 7.71, purity 0.179
```

**The forward-built fix barely moved chunks-per-word (7.21 -> 7.07).** Honest negative.

### Why — the precise diagnosis (live)

```
frames/word grain ratio: 7.56   (the fundamental over-segmentation floor)
local-minima fraction:   0.233  (local-min cuts ~23% of transitions)
below-median fraction:   0.475  (median cuts ~48%)
```

The boundary RULE was never the binding constraint — the **grain** is. The per-frame
unit stream has ~7.5 units per word, so ANY chunker that ever cuts within a word lands
near ~7 chunks/word. The local-min rule IS genuinely sharper — it halves the cut rate
(0.233 vs 0.475 of transitions) and nudges purity up (0.283 -> 0.290) — but real
per-frame TP is jagged noise, so local minima are still everywhere. Word-scale chunks
are unreachable until the unit stream is first coarsened from per-frame to per-segment
grain (run-length collapse of repeated units / a coarser unit grid) BEFORE the TP
chunker runs. That is the next capability, located precisely by this measurement.

(The purity numbers here, 0.283/0.290, are higher than the findings doc's 0.179 because
this probe runs a smaller/different subset; the apples-to-apples signal is median-vs-
local-min on the SAME data: a small real improvement, not a fix.)

## 4. Interventions (named plainly)

- **Loop-mechanism fix (the diversification gap).** Added an "attempted -> diminishing
  -> move on" signal the loop genuinely lacked: `mark_attempted_marginal` writes
  `attempted_marginal=1` on a built-and-exhausted axis; the ranking Term gains an
  `exhaust_penalty_term` (`attempted_marginal * PENALTY`, dominating payoff*K) so the
  Argmax advances. Seeded `attempted_marginal=0.0` on every axis in
  `build_axis_env`/`_mint_blocker_axis` so the Attr read is always numeric. The DECISION
  stays in the Term; this is the same world<->graph role `record_outcome` plays. WITHOUT
  this the ranker re-picks already-built gaps forever (shown live). This is the
  defensible move the task brief anticipated.
- **Did I advance the pick by hand?** No — I recorded clustering's real iter-1/iter-2
  outcome (built, 0.441 -> 0.460, still < 0.483, blocker already closed) as the move-on
  signal; the Argmax over the penalised Term advanced ITSELF to word-scale chunking.
- **Hand-code the boundary logic?** No — the boundary is a graph Term
  (`local_min_boundary_term`) evaluated natively; Python only stores prev/next-tp attrs
  (mechanical structure translation) and routes the mode.
- **A peer?** No.
- **New probe scripts (world adapters, no agent reasoning):**
  `scripts/word_scale_chunking_probe.py`.

## 5. Status / acceptance

- Agent PICKED word-scale chunking via its own ranker, once the loop-gap was fixed
  (live scores above).
- Forward-built the local-min boundary Term (composed) + prev/next-tp attrs (adapter).
- Honest measurement: chunks-per-word 7.21 -> 7.07 (barely), purity 0.283 -> 0.290
  (small real gain). The fix is correct science but NOT the binding constraint — the
  grain (frames/word 7.56) is. Recognition is NOT solved; this LOCATES the next gap
  (coarsen the unit grain before chunking).
- `test_stt_pipeline` + `test_perception_self_assessment`: **12 passed**. Gap/feedback +
  forward-segmentation tests: green.
- Not committed; left in the working tree.
