# Sizing the retrieved-exemplar-fallthrough opportunity — PREREG

**Date:** 2026-08-14. Worktree `progsyn-retrieval-fallthrough`, base
`main @ c80f24d` ("Correct unintentional-abuser scoping: intent, not
knowledge"), verified fresh via `git log --oneline -1 main` immediately
before creating the worktree and re-verified again before any docs were
committed. This is a **sizing investigation, not a build** — it directly
answers the question `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_2_PREREG.md`
§4 explicitly declined to answer: *"would `SynthEnumerate` actually solve a
meaningful fraction of the 60 [retrieved-exemplar-rejected tasks] — BEFORE
costing the control-flow change."*

**Investigation plan, registered before running the probe:**

1. Locate the exact gate that dead-ends a rejected `retrieved_exemplar`
   candidate instead of falling through to `SynthEnumerate`, and read the
   ORIGINAL reasoning in its own historical context (not re-derive it from
   behaviour).
2. Reproduce the 60-task population live against today's real baseline
   (main may have moved since the reassessment doc; verify the count is
   still 60, not assume it).
3. Run a bounded, honest, non-committal probe: for every one of the 60
   tasks, let the UNCHANGED pipeline reach its natural terminal state (zero
   seed/rule edits), then call `domains.prog_synthesis.run_enumerate`
   directly on the already-terminal goal node — a leaf Python helper that
   reads the message's example rows and whatever operator-shape hint the
   (unconditional, already-fired) `ps_select_synthesis_operator_shape` rule
   decided, and evaluates the `SynthEnumerate` Term exactly as a live rung-3
   firing would. This is not a patch to the gate — it never touches the
   graph rule engine at all — but it answers exactly the question a real
   fallthrough would face: *given today's op-table, what would enumerate
   produce for this spec, and would it be right?*
4. Score each result against the task's own held-out row (the same
   comparator the real battery uses, `prog_synthesis._row_cmp_ok` /
   `ProgEval`), so "found a candidate" and "found the CORRECT candidate"
   are never conflated.
5. Make an evidence-based GO/NO-GO/SIZE call; only build the real
   control-flow change if the probe's yield clearly justifies the
   blast-radius risk the reassessment doc flagged.

**Expected outcomes going in, stated honestly before running the probe:**
either (a) most of the 60 hit the same budget-exhaustion wall as the 102
`gapped:enumerate_failed` tasks (the reassessment doc's own soft guess,
§4.1) — a NO-GO on low absolute yield — or (b) enumerate finds real
answers for a meaningful fraction with an acceptable false-accept rate — a
GO for a scoped, gated fallthrough. **Both of these predictions turned out
to be wrong in an important way** — see the RESULTS doc,
`PROGRAM_SYNTHESIS_RETRIEVAL_FALLTHROUGH_RESULTS.md`, for what was actually
measured.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-retrieval-fallthrough
git log --oneline -1 main   # c80f24d, verify fresh
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 /tmp/claude-1000/-home-matt-ozmadev-ocelot/272b6058-8f21-4012-b852-d8348df69ff4/scratchpad/diag_sweep.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 /tmp/claude-1000/-home-matt-ozmadev-ocelot/272b6058-8f21-4012-b852-d8348df69ff4/scratchpad/fallthrough_probe.py
```

Both scripts are read-only measurement drivers (no seed/rule edits, no
graph-engine patch); `results/*.json` (gitignored, copied from the primary
tree so the boot's own reference data — `prog_construction_scan.json` etc.
— resolves) must be present for `ensure_program_synthesis` /
`install_mined_chunks` to boot correctly in an isolated worktree.
