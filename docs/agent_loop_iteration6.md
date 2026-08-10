# Autopoietic loop — iteration 6 (the process-meta-assessor WATCHES + GUIDES)

Turn the crank a sixth time, this time with the **process-meta-assessor watching and
guiding the loop in real time** — so the loop self-corrects at the *process* level
(stays on-frontier instead of wandering to outcome-detours). The brief's crux is the
guide-vs-observe honesty: does the assessor's signal actually **redirect** the loop's
pick to the frontier, or only observe? **It redirects** — the pick changes from a
downstream recognition gap to the closest-to-frontier gap *because of* the assessor,
verified live. The honest residual: the agent synthesizes no perception/units gap, so
the redirect lands at the closest available level (segmentation), not exactly at the
frontier.

All numbers below are LIVE (`scripts/agent_loop_iteration6.py`, real perception readout
on FSDD + native Term eval), not prose or constants.

Reproduce: `SG_PER=6 python scripts/agent_loop_iteration6.py`
Tests: `python -m pytest tests/test_gap_guidance.py tests/test_process_meta_assessor.py
tests/test_perception_self_assessment.py tests/test_stt_pipeline.py -q` → **23 passed**.

---

## 1. STEP 1 — the assessor's feeds AUTO-WIRED (the completed stub)

At commit a20a5044 the assessor's per-iteration feeds were STUBBED: `set_frontier`
hand-set the frontier rank, and `record_iteration` took `pick_rank` / `moved_source` as
adapter-set arguments. Iteration 6 completes the stub
(`domains/process_meta_assessor.py`, mechanical world↔graph reads — no decision):

- **`frontier_rank_from_perception`** — frontier_rank ← `perception_self_assessment`'s
  LIVE frontier flag. Its rule sets `PerceptionSelfRoot.frontier = 'perception'` when
  the units fail the `predict_over_freq` yardstick; this maps that to the
  perception/units pipeline rank (1.0), and to a far-downstream default (999) when the
  flag is `'none'`. **Proven LIVE, not a constant:**

  ```
  GOOD units  -> flag: none        -> auto frontier_rank: ('none', 999.0)
  BAD  units  -> flag: perception  -> auto frontier_rank: ('perception_units', 1.0)
  ```

  On real FSDD the units fail the yardstick, so the flag is `perception` and the feed
  yields rank 1.0:

  ```
  LIVE perception readout on FSDD (108 utterances):
    predict_over_freq = 1.000   (floor 1.25)
    compress_ratio    = 0.189   lexicon=31  tokens=61
  perception_self_assessment FRONTIER FLAG: 'perception'
  => frontier_rank AUTO-WIRED FROM THE FLAG: level='perception_units' rank=1.0
  ```

- **`pick_rank_from_axis`** — pick_rank ← the picked gap's pipeline level, computed by
  the ranker's OWN capability→level map (`gap_prioritiser.axis_pipeline_level`), so the
  assessor's notion of "where the pick sits" is exactly the ranker's.

- **`moved_source_from_feedback`** — moved_source ← `measurement_feedback`'s latest
  `MeasurementOutcome` for the iteration's attempted key (1 if it beat baseline, else 0).

`record_iteration_auto` composes the three so the assessor reads the loop's real state.

## 2. STEP 2 — THE SELF-CORRECTION: the signal CHANGES the pick (guide, not observe)

This is the new mechanism and the brief's crux. The assessor's BELOW_FRONTIER judgement
was previously **observe-only**: its rule sets `below_frontier=1` on a recorded
Iteration node, but nothing fed that back into the ranker, so it could not change the
NEXT pick. Iteration 6 wires it INTO the ranker (`domains/gap_prioritiser.py`), the same
graph-resident penalty pattern `measurement_feedback` already uses for the exhaust
signal:

- Each `CapabilityAxis` carries its **pipeline `level_rank`** (`axis_pipeline_level`
  maps the capability terms-of-art to the perception→recognition ordering).
- **`below_frontier_penalty_term`** — a graph Term-tree
  (`Gt / IfThenElse / Times / Minus / Attr`):
  `penalty = PENALTY * (level_rank − frontier_rank)` when `level_rank > frontier_rank`,
  else 0. The **distance scaling** is what makes the redirect land meaningfully when no
  axis sits exactly at the frontier: the Argmax picks the axis CLOSEST to the frontier.
- **`guided_score_term` / `guided_pick_term`** — base compression score MINUS the
  below-frontier penalty; `pick_with_guidance` installs a Rule that evaluates the guided
  Argmax NATIVELY (binding the frontier var to the live FrontierRoot) and reads back the
  winner.

LIVE on the real synthesized speech gap-set (frontier rank 1.0 from the perception flag):

```
(a) UNGUIDED pick — ranker WITHOUT the assessor's signal:
      payoff= 82 score=  81999  level=recognition          ['unsupervised-clustering', ...]
      payoff= 27 score=  26999  level=segmentation         ['transitional probability', ...]
      payoff= 12 score=  11999  level=feature_extraction   ['all-pole', 'levinson']
    UNGUIDED PICK: ['unsupervised-clustering', 'cross-speaker-clustering']  level='recognition'

(b) GUIDED pick — assessor's BELOW_FRONTIER signal IN the ranker:
      base= 26999 guided=   -973001  BELOW-FRONTIER  level=segmentation   ['transitional probability', ...]
      base= 11999 guided= -2988001  BELOW-FRONTIER  level=feature_extraction ['all-pole', ...]
      base= 81999 guided= -918001*  BELOW-FRONTIER  level=recognition    ['unsupervised-clustering', ...]
    GUIDED PICK: ['transitional probability', 'word-scale chunking']  level='segmentation'
    THE SELF-CORRECTION — pick CHANGED because of the assessor?  True
      unguided was: cross-speaker-clustering (recognition, rank 5, downstream of the frontier)
      guided re-picks the closest-to-frontier gap: segmentation (rank 2)
```

(*the recognition axis's distance is 4 → penalty 4M; segmentation's distance is 1 →
penalty 1M, so segmentation survives highest. The base payoff 82 is swamped by the
distance penalty — exactly the redirect.)

**The pick changes from recognition (payoff 82, the unguided winner) to segmentation —
purely because the assessor flagged recognition as below-frontier and the ranker read
that signal.** This is a GUIDE, not an observe. Verified by `test_gap_guidance.py`:
the same flip in isolation, plus a no-op control (frontier rank 999 → pick unchanged →
proves the signal only fires when the units actually fail the yardstick).

## 3. STEP 3 — pursue + the assessor's post-run verdict

The guided loop is now pointed frontier-ward (segmentation), and the assessor, fed its
auto-wired signals, confirms the redirect honestly:

```
ASSESSOR POST-RUN VERDICT (auto-wired feeds, native Rules):
  frontier_level=perception_units  frontier_rank=1.0
  loop_issue=none  fixer_progressing=1
  below_frontier flagged: ['iter6-unguided(recognition)', 'iter6-guided(segmentation)']
  the redirect pulled the pick UPSTREAM: rank 5.0 (recognition) -> rank 2.0 (segmentation)
  => the guided pick is CLOSER to the frontier but still below it — assessor flags it honestly: True
```

`loop_issue=none` (the probe channel did not spin this iteration) and
`fixer_progressing=1` (the guidance capability is a real loop-autonomy gain — a
separate channel from the probe, the two-channel design).

## 4. The honest residual (the real remaining gap, named)

**The redirect is genuinely wired (not observe-only), but it cannot land EXACTLY on the
perception/units frontier — because the agent synthesizes NO perception/units-level
gap.** Verified live: the 29-axis synthesized gap-set contains

```
axis count by pipeline level:
  recognition: 22   speaker_normalization: 4   feature_extraction: 2   segmentation: 1
  perception_units: 0
```

So the guided Argmax pulls the pick as far upstream as a gap EXISTS (segmentation,
rank 2), but the frontier is rank 1 and there is nothing there to pick. The assessor
correctly STILL flags the guided pick below-frontier — it is closer, not on. This is the
faithful state of the loop, reported rather than papered over.

**NEXT FIXER (the loop's real next gap):** a perception/unit gap in the *synthesis* —
the units' own quality (the `predict_over_freq` shortfall that `perception_self_assessment`
already measures) surfaced as a synthesizable `CapabilityAxis`, so the redirect has a
frontier-level gap to land on. The guidance plumbing is in place; what is missing is a
gap at the level the guidance points to.

## 5. Interventions (named plainly)

- **Auto-wire (world-adapter, no decision):** `domains/process_meta_assessor.py` —
  `frontier_rank_from_perception`, `pick_rank_from_axis`, `moved_source_from_feedback`,
  `record_iteration_auto`. Each is a mechanical read of a number the loop's own
  components already computed.
- **Guidance (graph-resident, in the agent's ranker):** `domains/gap_prioritiser.py` —
  `level_rank` on each axis (mechanical level map), `below_frontier_penalty_term` /
  `guided_score_term` / `guided_pick_term` (Term-trees), `set_frontier_rank` /
  `rank_with_guidance` / `pick_with_guidance`. The DECISION is the guided Argmax Term;
  Python only builds the env, writes the live frontier rank, fires the Rule, reads back.
- **New probe (world adapter):** `scripts/agent_loop_iteration6.py` — runs the real
  FSDD perception readout, auto-wires the frontier, prints the unguided vs guided pick
  side by side, records the iteration with auto-wired feeds, and prints the assessor's
  post-run verdict. All numbers live.
- **Did I tune to a number?** No. The distance-scaled penalty is `PENALTY*(distance)`;
  no threshold was tuned to make a pick look good. The residual (no perception/units
  gap) is reported, not hidden.
- **A peer / an LLM authoring code?** No.
- **Default-off / back-compat:** the guidance is opt-in via the new `*_with_guidance`
  entry points; the base `rank_gaps` / `pick_frontier` are unchanged, so existing
  callers and tests are untouched.

## 6. Acceptance (verified LIVE)

- **(1) Feeds auto-wired — VERIFIED.** frontier_rank comes from the perception flag
  (none→999, perception→1.0); not a constant.
- **(2) The self-correction — VERIFIED.** The assessor's BELOW_FRONTIER signal is wired
  into the ranker and CHANGES the pick: recognition (rank 5, payoff 82) → segmentation
  (rank 2). `pick_changed=True`, with a no-op control proving it only fires when the
  units fail. This is GUIDE, not observe.
- **(3) Pursued frontier-ward gap + measurement.** The loop pursues the
  closest-to-frontier gap (segmentation); the unit yardstick (`predict_over_freq=1.0`)
  is what flagged the frontier in the first place and is the measure the pursued gap
  must move.
- **(4) Assessor post-run verdict — VERIFIED.** `loop_issue=none`,
  `fixer_progressing=1`; the unguided recognition pick is flagged below_frontier, the
  guided pick is flagged honestly as still-below (closer, not on).
- **HONEST residual NAMED:** no perception/units gap in the synthesis → the redirect
  lands at the closest available level, not on-frontier. Next fixer named.
- **Tests:** `test_gap_guidance` (new) + `test_process_meta_assessor` (3 new auto-wire
  tests) + `test_perception_self_assessment` + `test_stt_pipeline` — **23 passed**.
- **Not committed; left in the working tree** (`scripts/agent_loop_iteration6.py`,
  `domains/gap_prioritiser.py`, `domains/process_meta_assessor.py`,
  `tests/test_gap_guidance.py`, `tests/test_process_meta_assessor.py`, this doc).

### The one-line finding

The process-meta-assessor now **watches the loop live** (frontier fed from the real
perception flag) and **guides it** — its BELOW_FRONTIER signal is wired into the ranker
and genuinely REDIRECTS the pick from a high-payoff downstream recognition gap to the
closest-to-frontier gap. The remaining gap is not in the guidance (it works) but in the
synthesis: the agent produces no perception/units gap for the redirect to land on.
