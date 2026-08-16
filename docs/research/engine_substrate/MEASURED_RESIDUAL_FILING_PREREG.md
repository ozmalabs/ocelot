# Measured-residual filing — PREREG (Proposal 3 of DESIGN_REVIEW_CAPABILITY_EXPANSION_PREREG.md §4)

**Date:** 2026-08-16. **Status: implementation prereg**, worktree
`measured-residual-filing` off `main @ f4394fd` (re-verified fresh
immediately before branching — see §0). This document is written before any
seed/code change lands in the worktree, per house discipline.

---

## 0. Headline

**Proposal 3's mechanism (d) — a `prog_read` `SelfConcern` reaching
`promote_self_concern` and closing through `_process_prog_read_standing`,
"the `code_write` precedent's exact shape" — is ALREADY LANDED in the
baseline this worktree branches from.** `git log --oneline --all | grep A25`
finds `0e62166`/`4563c3a` ("ARC6 A25: prog_read self-improvement wiring —
measured, not predicted"), already merged into `main` history reachable from
`f4394fd`. Reading `scripts/jabberwock_daemon.py:2103-2121` (`_concern_tick`'s
`kind == "prog_read"` branch), `:2539` (`_process_prog_read_standing`), and
`tests/test_prog_read_selfimprove_migrated.py` (`promote_self_concern`
exercised end-to-end at lines 140/147, `_run_self_gaps` surfacing checked at
line 251) confirms the wiring investigation's own smallest recommendation was
closed by a **different, earlier arc** than the design review that names it —
the design review's §1.5 citation of
`PROGRAM_SYNTHESIS_SELF_IMPROVEMENT_WIRING_INVESTIGATION.md` predates A25's
fix and was not re-checked against current `main` at review time (a
concurrent-session ordering artifact, not an error in the review's own
citations, which are accurate as of what they read). **This rung does not
re-implement (d); it verifies the gate still passes (§5) and cites it as
prior art, not new work.**

**What this rung actually builds is (a)+(b)+(c): the diagnostic
scripts' already-computed taxonomy dicts become typed `EngineeringResidual`
fact nodes at write time; a new sibling seed
(`seeds/engineering_residual_gap.json`, `depends_on: ["gap_awareness"]`)
decides which populations are standing gaps and retires them on
re-measurement, in `gap_awareness.json`'s own dedup/retire shape verbatim;
`_run_self_gaps` (`domains/reflective_faculty.py:358`) surfaces them with
**zero code changes**, confirmed by reading its implementation (§3 below) —
it walks every live `SelfConcern` node generically, filtered only by
`status != 'retired'`, with no `kind`-specific branch to extend.**

---

## 1. Where the populations already live, read directly

`scripts/mbpp_endgame_battery.py:394-405`, `taxonomy()`:

```python
def taxonomy(runnable_rows, excluded_rows):
    by = {}
    for r in runnable_rows:
        e = by.setdefault(r["outcome"], {"n": 0, "task_ids": []})
        e["n"] += 1
        e["task_ids"].append(r["task_id"])
    for r in excluded_rows:
        e = by.setdefault(r["outcome"], {"n": 0, "task_ids": []})
        e["n"] += 1
        e["task_ids"].append(r["task_id"])
    return dict(sorted(by.items(), key=lambda kv: -kv[1]["n"]))
```

called at `:427` (`tax = taxonomy(runnable_rows, excluded_rows)`) and stored
on the arm's own artifact at `:448` (`"outcome_taxonomy": tax`). This is
**exactly** "a populated dict of N tasks in bucket X" the design doc names —
already a `{outcome: {"n": count, "task_ids": [...]}}` shape, already
computed, before any change of mine. Read from a real, already-on-disk
measurement (`results/mbpp_endgame.json`, copied into this worktree from the
real repo checkout — untracked, `results/*` is gitignored per
`.gitignore:25`, so this is real prior output, not fabricated for this rung):

```
pass 88
gapped:enumerate_failed 67
accepted_holdout_fail 60
gapped:property_verdict_reject 17
gapped:structural_verdict_reject 14
gapped:exhausted 5
gapped:no_shape 3
not_recognized 1
runner_exception:ValueError 1
runner_exception:TypeError 1
```

**10 buckets, one of them (`pass`) not a residual at all.** This is the
"~8 population-grain concerns" the design doc predicted, off real data, not
an estimate re-derived here.

`scripts/ceiling3_diag_sweep.py` (102 lines, read in full) does **not**
already call `taxonomy()` — it writes a flat per-task `out` list
(`:96-97`, `results/ceiling3_diag_sweep.json`). It already
`import mbpp_endgame_battery as battery` (`:21`), so `battery.taxonomy(out,
[])` is directly reusable with **zero new grouping logic** (its rows already
carry `task_id`/`outcome` keys — the sole two fields `taxonomy()` reads). No
`results/ceiling3_diag_sweep.json` exists on disk in this environment (the
script has apparently not been run recently) — the wiring for this script is
therefore proven with a synthetic-but-schema-accurate smoke fixture (§5.2),
clearly labelled as such, never as a real measurement.

---

## 2. Mechanism, precisely

**(a) Ingest — mechanical I/O only, one new module.**
`domains/engineering_residual_ingest.py` (new, world-adapter-shaped: no
`if`/`else` over graph state, only find-or-update + `add_node`/`set_attr`):

- `ingest_taxonomy(substrate, agent, *, source_script, taxonomy, measured_at=None)`
  — for each `(outcome, {"n": count, "task_ids": [...]})` in the caller's
  already-computed dict, upserts one `EngineeringResidual` node keyed by
  `(source_script, outcome)` (scan existing nodes of that type for a
  `source_script`+`outcome` match — a mechanical find, the same shape
  `domains/teach.py`'s own idempotent node search and CLAUDE.md's
  `_reconcile_seed_typed_nodes` precedent already use for "does this fact
  already exist under this identity"). Attrs: `source_script`, `outcome`,
  `population_key` (`f"{source_script}:{outcome}"`, the SelfConcern
  `content` value), `count` (Python `int`, CLAUDE.md's in-frame-integer
  invariant), `task_ids` (Python `list[int]`), `measured_at`. A population
  present in an OLDER ingest but **absent** from the current taxonomy is
  treated as `count=0` (absence is zero, the `space_quantize`/unknown-first-
  class precedent CLAUDE.md already names) — never silently left stale.
  Calls `substrate.tick()` once at the end so the new rule fires
  immediately, matching every other mechanical-record-then-tick adapter call
  in `world_adapter.py`.
- `load_or_boot_residual_substrate(checkpoint_path=...)` /
  `save_residual_substrate(substrate, checkpoint_path=...)` — a SEPARATE,
  SMALL, dedicated persisted graph
  (`results/engineering_gaps_substrate.json`, `graph_to_dict`/
  `graph_from_dict`, the exact pair CLAUDE.md's architecture diagram lists
  as a first-class Rust runtime capability, already used this way by
  `scripts/corpus_self_learn.py` and the `abusive_*` scripts). First call
  boots a full `WorldAdapter(seeds=()) + load_all_seeds(...)` (the
  `tests/test_gap_awareness_migrated.py` fixture's own pattern); later calls
  `graph_from_dict` the saved checkpoint. **Named, not solved here:** a
  resumed checkpoint does not re-run `_reconcile_seed_rules`-style rule-body
  refresh if this seed's rule bodies are edited later — the same residual
  CLAUDE.md already documents for the daemon's real checkpoint, scoped down
  to this dedicated file. Not exercised because this is a brand-new seed in
  this rung; flagged honestly rather than silently assumed away.
  **This checkpoint is NOT the real jabberwock daemon's `~/.jabberwock/
  checkpoints` state** — wiring the daemon itself to read it is out of
  scope, named as a residual (§6).

**(b) Decide — one new seed, `gap_awareness.json`'s own rule shape,
verbatim.** `seeds/engineering_residual_gap.json`, `depends_on:
["gap_awareness"]` (sibling naming to `code_write_gap.json`/
`prog_read_gap.json`, both `depends_on: ["gap_awareness"]` too):

- `note_engineering_residual_gap` — match `[["agent",
  "has_engineering_residual", "er"]]` (the SAME single-anchor-from-agent
  shape `note_upload_vision_gap` uses for its second anchor, `gap_awareness.
  json`'s own precedent for a non-`Goal`/non-`Message` fact source). `where`:
  `Not(Eq(er.count, 0))` AND `Not(Eq(er.outcome, "pass"))` (the ONE
  hardcoded literal in this rung — `"pass"` is the sole success sentinel
  both scripts' own `row["outcome"] = "pass"` lines already define, read
  directly at `mbpp_endgame_battery.py:337` and (via reuse) in
  `ceiling3_diag_sweep.py`; excluding it is the rule DECIDING what counts as
  a residual, never Python) AND the `Not Exists SelfConcern content==X`
  dedup guard, copied verbatim from `note_unresolved_topic_gap`/
  `note_solve_exhausted_gap`, AND a mint-once flag on `er`
  (`engineering_gap_noted`), the `gap_noted` precedent. Effects: mint
  `SelfConcern{status:'noted', source:'implicit', kind:'engineering_residual',
  content:<population_key>, count:<count>, task_ids:<task_ids>}` +
  `agent -has_self_concern-> sc`. **One `SelfConcern` per POPULATION**
  (content = `population_key`, e.g. `"mbpp_endgame_battery.full:
  accepted_holdout_fail"`), never per task-id — the design doc's one stated
  granularity risk, closed by construction (the rule matches `er` nodes,
  one per outcome bucket, never iterates `task_ids`).
- `retire_resolved_engineering_residual_gap` — `retire_duplicate_gap`'s
  exact guard shape, pointed at re-measurement instead of duplication: match
  `[["agent", "has_self_concern", "sc"]]`, `where`: `Eq(sc.kind,
  "engineering_residual")` AND `Not(Eq(sc.status, "retired"))` AND `Exists`
  an `EngineeringResidual` `er` with `Eq(er.population_key, sc.content)` AND
  `Eq(er.count, 0)`. Effects: `set_attr sc status retired` +
  `del_edge agent has_self_concern sc` — byte-identical effect shape to
  `retire_duplicate_gap`.
- **Known, named limitation carried forward from the precedent, not
  invented here:** the mint guard's `Not Exists SelfConcern content==X`
  (no `status` filter) means a population that goes `60 -> 0 (retired) -> 5`
  again (a regression) does not re-mint — `note_solve_exhausted_gap` has
  this exact same property today. Not fixed in this rung (staying inside
  the sanctioned shape means inheriting its edges too); named honestly.

**(c) Surface — verified, not assumed, by reading `_run_self_gaps`
(`domains/reflective_faculty.py:358-436`) in full.** It:
1. Walks every `Agent` node's `has_self_concern` neighbours (`:389-393`).
2. UNIONS in a scan of every `SelfConcern` node in the graph regardless of
   the edge (`:396-400`) — so even an edge-shape mistake would still surface.
3. Skips `status == 'retired'` (`:379-380`).
4. Groups by `source` (`:409-413`) using `_GAP_SOURCE_ORDER = ("implicit",
   "explicit_report", "conversation")` (`:350`) with an alphabetical
   fallback for any other `source` — our `source:'implicit'` value is
   already in that tuple, so no source-list edit is needed either.
5. Renders `"content" (kind)` per concern (`:415-418`) — `kind:
   'engineering_residual'` renders exactly like every other kind, no
   `kind`-specific branch anywhere in the function.

**Zero lines of `reflective_faculty.py` change are needed.** This is the
claim CLAUDE.md's own "confirm this is genuinely true... before assuming it
'just works'" instruction demanded be checked, not asserted — checked above,
line-cited.

**(d) `promote_self_concern` / `_process_prog_read_standing` — already
landed, see §0.** No change; §5 re-runs its gate.

---

## 3. What is NOT proposed

- No change to `synth_enumerate.rs`, the Occam metric, or any search
  machinery (Proposal 1/2 territory — out of scope, and this rung's own
  house discipline explicitly forbids drifting there).
- No MBPP battery run (none of this touches synthesis search behavior; the
  live-verify uses the real `results/mbpp_endgame.json` artifact already on
  disk, not a fresh run).
- No wiring of the real jabberwock daemon's own `~/.jabberwock/checkpoints`
  state to this new checkpoint file — named as a residual, not built.
- No new `promote_self_concern` routing branch for `kind:
  'engineering_residual'` — it falls through to the existing generic
  `comprehend_first` default (`jabberwock_daemon.py:2155-2158`), which is
  the same default every kind not explicitly special-cased already gets.
  The design doc's "Risk/size: LOW... one daemon branch" names ONLY (d),
  which is already satisfied; a human reading a filed engineering-residual
  concern and deciding what to build next (the design doc's own framing,
  §4 "capability gap it closes") does not require automated promotion
  routing to do anything special.

---

## 4. Falsifiable predictions, checked in §5

1. Ingesting the real `results/mbpp_endgame.json` `full`-arm taxonomy (10
   buckets, 1 being `pass`) mints **exactly 9** `SelfConcern{kind:
   'engineering_residual'}` nodes, none for `pass`.
2. Re-ingesting the identical taxonomy a second time mints **zero**
   additional concerns (dedup) and the count stays 9.
3. Ingesting a taxonomy where one previously-nonzero population's count
   drops to 0 retires exactly that population's concern and leaves the
   other 8 live.
4. `_run_self_gaps` on the resulting substrate lists all live
   `engineering_residual` concerns with their real content strings, with
   no code change to `reflective_faculty.py`.
5. `tests/test_gap_awareness_migrated.py`,
   `tests/test_self_gaps_surfacing_migrated.py`, and
   `tests/test_prog_read_selfimprove_migrated.py` (the already-landed A25
   gate) all still pass unmodified.

## 5. What this document does NOT establish (filled in by the RESULTS doc)

Whether the predictions above hold, the literal test/script output, and the
literal `_run_self_gaps`/`converse()` transcript are NOT claimed here — this
document is written before the code lands, per house discipline. See
`MEASURED_RESIDUAL_FILING_RESULTS.md`.
