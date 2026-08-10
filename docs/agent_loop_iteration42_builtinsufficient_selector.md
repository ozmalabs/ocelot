# iter-42 — the gap-selector's built-but-insufficient meta-gap, fixed

> The agent could not flag an ALREADY-BUILT-BUT-INSUFFICIENT capability as a
> frontier: order-N synthesis only mints ABSENT (open) gaps, so a built first-pass
> (LPC / speaker-norm / coarticulation) that the agent MEASURED below its target was
> read as CLOSED and scored on compression payoff (irrelevant), and the selector
> picked cross-speaker clustering / segmentation instead of the front-end the agent's
> OWN order-N derivative names. The fix is the agent's OTHER frontier mechanism — the
> MEASUREMENT-YARDSTICK — generalised: a built capability measured below its target is
> RE-OPENED as a gap, ranked by the shortfall, feeding the existing Argmax.
>
> Graph-resident, no-donkey. Working tree only — NOT committed.

---

## (1) The fix, wired graph-resident (audited)

All in `domains/gap_prioritiser.py` (the existing graph-resident ranker), no new
Python decision and no hardcoded capability list:

- **`MeasuredCapability` node** (`MEASURED_TYPE`) — graph state carrying a BUILT
  capability's `measured` yardstick value, its `target`, and its `capability_keys`
  (the same terms-of-art the order-N synthesis / axis map use). Written by the
  world-adapter `record_measured_capability` — pure I/O translation of the agent's
  yardstick / do-contrast RESULT into a node (the probe computed the numbers; the
  function makes NO decision; whether `measured < target` is the Rule's call).

- **The synthesis Rule** `synthesise_builtinsufficient_gap`
  (`install_builtinsufficient_gap_rule`) — a graph Rule whose `where` gate is
  `Gt(target, measured) AND Eq(synth_pending, 1)` and whose effect mints a
  `CapabilityAxis` (flagged `is_axis`, `built_insufficient`) carrying
  `shortfall = Minus(target, measured)` computed **natively in the effect**, plus a
  `re_opens` provenance edge from the measurement to the axis, and clears its pending
  flag (idempotent — one axis per fresh reading). A capability measured at/above
  target yields no firing (read as closed). The DECISION is the Rule, not Python.

- **The score Term, extended** — `score_term` is now
  `payoff*K - min_order + shortfall*BOOST` (a `Plus` of the existing compression
  score and `shortfall_boost_term = Times([Attr(x, "shortfall"), BOOST])`). For a
  synthesised (never-measured) axis `shortfall` defaults to 0, so the bare
  compression ranking is unchanged; for a re-opened built-but-insufficient axis the
  shortfall (>0) is boosted above every compression payoff, and a larger shortfall
  outranks a smaller one. This flows through `rank_gaps`, `pick_frontier`,
  `rank_with_guidance`, `pick_with_guidance` — the SAME Argmax the agent already uses.

`build_axis_env` was extended to (a) backfill `level_rank` / `shortfall` /
`min_order` defaults on every `is_axis` node (so Rule-minted axes the grouping never
lists still read as numbers in the Term), and (b) return ALL `is_axis` nodes, not
only the SynthesizedGap-grouped ones — so a pick over Rule-minted-only axes is not
empty. No decision added; mechanical structuring.

**No-donkey audit:** the only Python is the I/O adapter (`record_measured_capability`
writes a node from the probe's numbers) and the fire-Rule-and-read-back driver
(`synthesise_builtinsufficient_gaps`). The re-open DECISION is the Rule's `where`
gate; the prioritisation DECISION is the score Term's `shortfall*BOOST`, evaluated by
`substrate.evaluate`. No hardcoded capability list, no `_specify_*` dict — the Rule
consumes whatever `MeasuredCapability` measurements are in the graph.

## (2) BEFORE vs AFTER — the selector's frontier pick

Driver: `scripts/agent_frontier_selfdiagnosis_postiter40.py` (full breadth: phonology
+ speech_science + math/eng/ml + concept expansions; harvested shapes, NOT the frozen
stencil). Section [4] feeds the agent's OWN iter-2/39/40 measurements of its BUILT
front-end (the same facts the registered postulate's `why` text describes) as
`MeasuredCapability` state, then re-runs the SAME ranker.

```
BEFORE (bare compression ranker) picked : unsupervised/cross-speaker-clustering   [level recognition]
AFTER  (built-but-insufficient source)  : all-pole / levinson / lpc-formant       [level feature_extraction]
```

The fed measurements (measured vs target → shortfall):
| capability (built) | measured | target | shortfall |
|---|---|---|---|
| all-pole / levinson / lpc-formant (LOSO filter front-end) | 0.335 | 0.649 | 0.314 |
| speaker normalization / formant ratio / VTL-norm | 0.38 | 0.65 | 0.270 |
| coarticulation predict-remove / context norm | 0.45 | 0.55 | 0.100 |

The Rule re-opened all three; the ranking AFTER (native Term scores):
```
score=313999999  feature_extraction     all-pole / levinson / lpc-formant     <-- PICK
score=269999999  speaker_normalization  speaker normalization / formant ratio
score= 99999999  speaker_normalization  coarticulation predict-remove
score=    81999  recognition            cross-speaker-clustering  (the old pick, now below)
score=    26999  segmentation           transitional probability
```

The top three are now all the FEATURE FRONT-END, ordered by measured shortfall;
cross-speaker clustering (the old pick, 82 postulates) drops below them.

## (3) VERDICT

**The meta-gap is FIXED.** The agent's order-N DERIVATIVE (script section 3a',
unchanged) converges on the feature front-end — all-pole/LPC, speaker(VTL)-norm,
coarticulation context-removal — from differentiating the registered state's own
text. BEFORE the fix the bare RANKER diverged (picked cross-speaker clustering by
compression payoff); AFTER the fix the selector **picks the feature front-end
(`feature_extraction` / all-pole-LPC)**, CONVERGING with its own order-N derivative,
driven by the measured insufficiency (the shortfall), not by a human pointing at it.

This is a GENERAL meta-ability, not a one-off: any built capability the agent's
yardstick measures below its target re-enters the gap set ranked by the shortfall —
the selector can now self-prioritise "already-built-but-insufficient" capabilities,
the frontier class order-N synthesis alone could never flag.

Honest scope: the measured numbers are fed by the world adapter
(`record_measured_capability`) — they are the agent's OWN recorded iter-2/39/40
probe results (the same facts in the postulate's `why`), translated to graph state,
exactly the permitted I/O role `measurement_feedback.record_outcome` /
`perception_self_assessment.record_perception_quality` already play. The re-open and
the prioritisation are the graph Rule + the score Term. The re-opened axis carries
its OWN compression payoff of 0 (no `unifies` edges) — correct: it wins by the
measured shortfall, not by postulate unification (provenance: a `re_opens` edge from
the measurement, flagged `built_insufficient`).

## Tests (all green)

- `tests/test_builtinsufficient_gap.py` (6, new) — the built-but-insufficient axis
  outranks the compression pick; larger shortfall outranks smaller; at/above-target
  mints nothing; idempotent per reading; provenance edge present; the decision is in
  the Term (`substrate.evaluate`, not Python).
- Required suites: `test_stt_pipeline` (7), `test_perception_self_assessment` (8),
  `test_process_meta_assessor` (10), `test_gap_guidance` (3) — 28 passed.
- `test_models` (18) — also touches `gap_prioritiser`, still green.

## Reproduce

```
python scripts/agent_frontier_selfdiagnosis_postiter40.py    # BEFORE/AFTER + verdict
python -m pytest tests/test_builtinsufficient_gap.py tests/test_stt_pipeline.py \
  tests/test_perception_self_assessment.py tests/test_process_meta_assessor.py \
  tests/test_gap_guidance.py -q
```

## Files
- `domains/gap_prioritiser.py` — the fix (MeasuredCapability node, the synthesis Rule,
  the shortfall-boosted score Term, build_axis_env backfill + full-axis return).
- `tests/test_builtinsufficient_gap.py` — the lock.
- `scripts/agent_frontier_selfdiagnosis_postiter40.py` — section [4]/[5] (BEFORE/AFTER).
- `docs/agent_loop_iteration42_builtinsufficient_selector.md` — this report.
