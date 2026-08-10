# Loop reasoning → graph + the frontier-gap fixer

Two steps, both verified LIVE (real output, not prose). Working tree only — not committed.

1. **Step 1** — move the autopoietic-loop's reasoning OUT of Python into graph
   Rules/Terms (architecture rule [[ozma_concepts_in_gamma]] / CLAUDE.md: Python does
   only (a) run the graph and (b) translate world↔graph; all decisions are Rules/Terms).
2. **Step 2** — the next fixer, graph-resident: connect the yardstick
   (`perception_self_assessment`) → gap-synthesis so the units' shortfall becomes a
   synthesizable perception/units `CapabilityAxis` the guided loop LANDS on.

---

## Step 1 — audit + migration of the loop-mechanism files

Files audited: `domains/gap_prioritiser.py`, `domains/process_meta_assessor.py`,
`domains/measurement_feedback.py`, `domains/order_n_postulates.py`,
`domains/implication_harvester.py`.

### Disposition table (function → moved-to-graph | stays-as-IO + why)

| Function | Disposition | Why |
|---|---|---|
| **gap_prioritiser** | | |
| `payoff_term` / `score_term` / `pick_term` | already graph | Term constructors — the ranking DECISION is the Argmax Term, evaluated natively. |
| `below_frontier_penalty_term` / `guided_score_term` / `guided_pick_term` | already graph | the BELOW_FRONTIER redirect is a Term (Gt/IfThenElse/Times/Minus/Attr), eval'd natively. |
| `unblock_bonus_term`/`effective_*` (measurement_feedback) | already graph | the feedback re-rank is a Term. |
| `axis_pipeline_level` / `_KEY_TO_LEVEL` | **stays I/O** | opaque external capability STRINGS → the smallest graph token (a rank float). The DSL has **no string-contains primitive** (verified `runners/dsl/src/term.rs` — no `StrContains`/`Substring`/`Matches`), so per CLAUDE.md ("a thin I/O-boundary classifier is permitted when converting an opaque external form into the smallest graph token AND no Rust primitive can do the job") this is permitted translation. Crucially, its RESULT (`level_rank`) is stored as a graph attr on each axis, and the ranking decision reads that attr natively. No conditional over graph state decides the pick here. |
| `build_axis_env` / `shape_firing_breadth` | stays I/O | mechanical grouping/dedup of SynthesizedGap nodes into CapabilityAxis nodes + the specificity-gate (a corpus-frequency measurement). World↔graph structuring; no pick decision. |
| `rank_gaps`/`pick_frontier`/`rank_with_guidance`/`pick_with_guidance` | stays I/O | install the Rule, fire to fixed point (pending-flag loop), read back the axis the **Rule's Term** chose. The "fire a Rule and read its result" role. |
| **process_meta_assessor** | | |
| `install_*_rule` (DOMAIN_SPINNING / FIXER_PROGRESS / BELOW_FRONTIER / FIX_THE_OUTCOME) | already graph | the four judgements are general predicate Term-trees (And/Or/Gt/Lt/Eq/IfThenElse), native eval, zero session constants. |
| `frontier_rank_from_perception` | **MOVED → graph Rule** | was a Python conditional over graph state (`if flag == 'perception': rank 1.0 else 999`). That `if` is a decision. Migrated to `perception_self_assessment.set_frontier_rank_from_flag` (IfThenElse over string `Eq` reading the root's own `frontier` flag + two rank dials). This function is now a mechanical read-back: install+fire the Rule, read the rank the Rule wrote. |
| `pick_rank_from_axis` | stays I/O | delegates to `axis_pipeline_level` (the opaque-string→token I/O above). |
| `moved_source_from_feedback` | stays I/O | reads the latest MeasurementOutcome's `beats_baseline` flag — the comparison was the probe's; this returns the recorded number. |
| `record_iteration*` / `set_frontier` / `get_issues` | stays I/O | append iteration nodes, wire the `follows`/`has_iter` chain, query flags back. No decision. |
| `agent_assess` | stays I/O | drives the four Rules to fixed point + reads verdicts. |
| **measurement_feedback** | | |
| `record_outcome` / `mark_attempted_marginal` / `_mint_blocker_axis` / `_find_axis` | stays I/O | translate an external measurement RESULT (numbers + the probe's own verdict branch) into a node + a `blocked_by` edge. The cap-attribution `if gain ≤ 0` reads the probe's verdict, not a graph-state decision the agent makes. |
| **order_n_postulates** | | |
| `differentiate` | stays I/O (selector mechanism) | structural transfer (regex match of implication-shapes over text) — the shape LIBRARY is the agent's harvested concepts; this is the order-N derivative step, not a hand-coded decision. |
| `is_gap` selector | stays I/O | coverage check scans the agent's science/impl surface + speech codebase FILES for a capability's distinctive tokens — file/string matching no DSL primitive can do (genuine I/O boundary). The compression/cohesion judgement is structural (a shape fired + names a new axis). |
| `harvest_postulates` / `synthesize_gaps` / `_record_gap` | stays I/O | gather held concepts as order-0 nodes; mint SynthesizedGap nodes with their derivation chain. Translation. |
| **implication_harvester** | | |
| `harvest_shapes*` / `_extractors` / `harvest_report` | stays I/O | read the agent's Concept/Rule text, abstract implication-shapes (the analogy.abstract_patterns move applied to text). Harvesting graph data into a shape catalogue; no pick decision. |

**Honest:** the one genuine Python decision-over-graph-state in the loop machinery
(`frontier_rank_from_perception`'s flag→rank `if`) is now a graph Rule. The remaining
Python in these files is justified I/O: Term constructors (the decisions ARE the Terms),
the fire-Rule-and-read-back drivers, world↔graph structuring (axis env, iteration chain),
opaque-string→token classification the DSL cannot express (`axis_pipeline_level` — no
string primitive in `term.rs`), and external-measurement / codebase-scan translation.
No new primitive was needed; nothing was relabelled.

---

## Step 2 — the next fixer, graph-resident: yardstick → synthesis → ranker

### The seam (the iter-6 residual)

`perception_self_assessment` fires `frontier='perception'` when the units fail the
yardstick (`predict_over_freq < floor`). The guided ranker (`gap_prioritiser`) penalises
every axis below that frontier. But `order_n_postulates` synthesises **zero**
perception/units gaps (iter-6: 0 of 29 axes), so the closest the guided redirect could
land was **segmentation (rank 2)** — still below the rank-1 frontier. The loop could not
land on its own frontier.

### The fix (a Rule, not Python glue)

`perception_self_assessment.install_perception_gap_rule` —
`synthesise_perception_units_gap`:

```
WHEN  root.frontier == "perception"  AND  root.perception_gap_pending == 1
THEN  add_node CapabilityAxis {
        is_axis=1, level_rank = root.perception_units_rank (= 1.0, AT the frontier),
        pipeline_level="perception_units",
        capability_keys=[improve-unit-predictiveness, perception-units, unit-invariance],
        gap_text="improve the perceived units' predictiveness / invariance …" }
      add_edge root --synthesised_gap--> axis      (provenance to the yardstick shortfall)
      set root.perception_gap_pending = 0          (idempotent: one gap per shortfall)
```

The flag rule (`flag_perception_frontier`) re-arms `perception_gap_pending` whenever it
sets the frontier, so the synthesis tracks the live shortfall. Implementation gotcha
fixed: the rule binds via a **distinct `psr_self` marker edge** (not the generic `self`
that `gap_prioritiser`/`measurement_feedback` use on their FrontierRoot) — sharing `self`
made the guided-pick rule bind to the PerceptionSelfRoot and silently return None.

### Verified LIVE (`scripts/agent_loop_iteration6.py`, real FSDD perception readout)

```
[STEP 1] LIVE perception readout (108 utterances):
    predict_over_freq = 1.000  (floor 1.25)   -> FRONTIER FLAG: 'perception'
    frontier_rank AUTO-WIRED from the flag = 1.0  (via the graph Rule, not a constant)

[STEP 1b] NEW FIXER (graph Rule):
    flag='perception' -> MINTED a 'perception_units' axis at rank 1.0
    CapabilityAxes (is_axis=1): 29 -> 30 (+1 perception/units gap that did NOT exist)

[STEP 2] guided ranking at frontier rank 1.0:
    base=-1     guided=-1        at/above-frontier  perception_units   <-- TOP
    base=26999  guided=-973001   BELOW-FRONTIER     segmentation
    GUIDED PICK: perception_units   pick_changed = True
      (unguided was recognition rank 5.0)

[STEP 3] assessor verdict:
    pick_rank == frontier_rank?  True
    guided iteration NO LONGER below-frontier?  True
    below_frontier flagged: ['iter6-unguided(recognition)']   (guided iter is gone)
```

Side-by-side with iter-6's prior segmentation-pick: before, the guided pick landed on
segmentation (rank 2, still below the rank-1 frontier, assessor still flagged it). Now it
lands on **perception/units (rank 1 == frontier rank 1)** and the assessor no longer flags
the guided iteration.

---

## Honest assessment

- **Did reasoning genuinely move out of Python?** Yes for the one real
  decision-over-graph-state in the loop machinery (the flag→rank `if`), now a native Rule
  with the ranks as dials. The rest of the Python in these files is justified I/O
  (Term constructors are the decisions; the remainder is translation / fire-and-read-back
  / opaque-string classification the DSL cannot express). Not a relabel — the migrated
  `frontier_rank_from_perception` now reads an attr a Rule wrote, and a test
  (`test_frontier_rank_is_set_by_a_graph_rule_not_python`) locks that the rank comes from
  the Rule's IfThenElse, not Python.
- **Did the connection genuinely yield a frontier gap the loop lands on?** Yes, verified
  live: the guided pick LANDS on perception/units (pick_rank == frontier_rank == 1.0),
  `below_frontier` no longer flagged on the guided iteration. **This is the convergence the
  session pointed at: the guided loop now lands on its OWN frontier, the units the
  yardstick flagged, all graph-resident (Rules + native Term eval).** Reproducible:
  `python scripts/agent_loop_iteration6.py` and
  `tests/test_perception_self_assessment.py::test_units_failing_synthesises_a_perception_gap_the_guided_ranker_lands_on`.
- **Any stubbed/Python-still link?** The synthesised axis carries no `unifies` edges, so
  its base payoff is 0 (score −1) — it wins ONLY because every downstream axis is
  penalised below the frontier. That is correct (the frontier gap should win by being
  on-frontier, not by a fabricated payoff count), but means the perception axis is grounded
  in the measured shortfall (provenance edge), not in a postulate-unification count like
  the order-N gaps. Honest: it is a measurement-derived frontier gap, not an
  order-N-synthesised one — the same honesty `measurement_feedback._mint_blocker_axis`
  already flags for the LPC blocker.

## Tests (all green)

`test_stt_pipeline` (7), `test_perception_self_assessment` (8, +3 new),
`test_process_meta_assessor` (10), `test_gap_guidance` (3) — 26 passed.
(`test_implication_harvester::test_harvest_excludes_the_speech_science_postulates` fails on
a pre-existing 'determinant' exclude-Mt issue UNRELATED to this work — confirmed failing
with these two files reverted.)
