# Note — LPC harvester investigation + fix (uncommitted)

Working tree only; not committed (per instruction).

## TL;DR — the task's diagnosis was itself the stale artifact

The brief said the all-pole shape "does NOT transfer onto source_filter_theory".
**That is false against the live code.** I verified with the live demo + traces:

- The harvested all-pole shape (from `IIR_filter`) **DOES** transfer onto
  `source_filter_theory`. It fired even before my change (via the `\bresonanc`
  trigger matching "imposes the resonances (formants)"). Derivation works.
- The reason ACCEPTANCE-1 printed `MISS LPC` was **NOT** a transfer failure. It
  was the SELECTOR correctly pruning LPC because the agent has since
  **IMPLEMENTED** it: `domains/sound_graph.py:_lpc_formant_peaks`
  (autocorrelation → Levinson-Durbin → all-pole, commit `c1b695d`
  "loop iter-2 — GENUINE self-correction to LPC"). `sound_graph.py` is in
  `_SPEECH_GLOBS`, so `_codebase_has` finds it and prunes it. **Correct behaviour.**

Proof (live): with the codebase-coverage check bypassed, the LPC gap synthesises
3/3 from `source_filter_theory` via the all-pole shape from `IIR_filter`. So the
transfer was never the problem.

The real defects were **conflation bugs** (the "trust a print line" trap, in two
directions):

1. The demo / tests / loop measured **post-selector OPEN gaps** but called it
   "self-sufficiency / recall", conflating "can DERIVE this implication"
   (harvester's job — works) with "is still an OPEN gap" (selector's job — LPC is
   closed). That made `MISS LPC` read as a harvester failure.
2. The demo prose hard-coded **"recall is 3/3"** while the live computed result
   was 2/3 — the exact over-claim the brief warned about, baked as a constant.

## The fix (GENERAL — no LPC/source_filter hardwire)

`grep` confirms **zero** `if postulate==source_filter_theory` / LPC special-cases.

1. **`domains/order_n_postulates.py` (~50 lines, 100% shape-agnostic):** add a
   `prune` flag to `is_gap` / `synthesize_gaps` / `synthesize_over_all`. It cleanly
   separates the two questions:
   - `prune=False` → DERIVATION: report every coherent transferred implication
     regardless of whether the agent has since implemented it (= harvester
     self-sufficiency).
   - `prune=True` (default, unchanged) → OPENNESS: gate on the science/impl +
     codebase coverage scan (LPC correctly pruned).
   This is general — it applies to every postulate and every shape.

2. **`domains/implication_harvester.py` (~12 added lines, kind-level, not
   LPC-specific):** broaden the `parametric_allpole` extractor's `triggers` to
   match the structural KIND "resonant linear filter" explicitly — grounded in the
   resonance↔pole bridge the agent's own concepts encode (`IIR_filter`,
   `source_filter_theory`, `vocal_tract_resonance_formants` all describe
   pole/resonance systems). Patterns: `\bresonanc`, `\bpoles?\b`, and filter↔
   (resonance|formant) co-occurrence. No postulate is named.
   - Verified it fires on `source_filter_theory` AND
     `vocal_tract_resonance_formants` (>1 ⇒ not a hardwire) and does NOT fire on
     `statistical_learning` / `lexical_access` (no spurious all-pole/LPC gap).

3. **`scripts/order_n_postulates_demo.py`:** ACCEPTANCE-1 now prints the LIVE
   computed `DERIVED=` and `still-open=` per known capability, the derivation
   chain + source concept, and explicitly flags LPC as already-implemented (not
   open). ACCEPTANCE-3's "recall" line is now COMPUTED from the run
   (`DERIVATION RECALL 3/3`, of which `2/3` still open) — the stale "3/3" constant
   is gone, with a note that it conflated derivation with openness.

4. **`scripts/agent_loop_iteration2.py`:** STEP-0 now records DERIVATIONS
   (`prune=False`) so the LPC axis comes from the agent's OWN synthesis. Result:
   `record_outcome` finds the existing axis — **`minted_blocker=False`**, no
   `_mint_blocker_axis` fallback. The re-rank still promotes LPC to the top via the
   unblock bonus and the self-correction test still passes. The stale loop comment
   ("the harvested all-pole shape does not fire on source_filter_theory") is
   corrected.

## Honest verdict

- DERIVATION self-sufficiency: **GENUINELY 3/3**, general (transfer by structural
  kind, multi-postulate, no hardwire). Confirmed live, not from a print line.
- OPEN gaps: **2/3** is the correct live number — LPC is no longer a gap because
  the agent built it. Reporting it as a gap would be the fake-3/3 failure mode.
- The all-pole shape is NOT effectively hardwired: it is a resonant-linear-filter
  kind match firing on multiple postulates and pruned-correctly elsewhere.

## Tests

- `test_stt_pipeline`, `test_perception_self_assessment`, `test_implication_harvester`:
  **20 passed** (was 18 passed / 2 failed — the 2 were already red on the pristine
  tree for the same conflation reason; now fixed + 3 new guard tests added).
- Full suite has 42 unrelated pre-existing failures (test_frames, test_reconsider,
  test_theorems_as_terms, test_substrate_awareness, test_meta_curiosity_and_t3,
  test_graph_rewrite, test_codec_graph_resident) — verified failing on the pristine
  tree with my changes stashed; none import any module I touched.
