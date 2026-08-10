# ARC 6 — THE INCOHERENT TREE: what it was, how it was found, what it changed

**Date:** 2026-08-03
**Status:** RECONCILED. `tests/test_goal_residual_migrated.py` 31/31.
**Engine (coherent):**
`8311d4356082acf4f70fab61a6e943d3dcecbd404d6e90c4f72ccc9486936df0`,
archived out of tree at
`~/ozma-engine-archive/_native.abi3.so.FINAL_8311d4356082…` (prereg A1.1).
**Engine (incoherent, superseded):** `48da7257f35d…`.
**Documents corrected:** `PROGRAM_SYNTHESIS_ARC6_GOAL_RESIDUALS.md` §10.

---

## 1. What "incoherent" means here

A tree is **coherent** when its binary was built from its own committed source.
Between the value-layer rung landing (`9611ed9821`) and the goal-residual rung
running, this worktree stopped being coherent in two ways at once:

1. **The binary was the wrong one.** `runners/dsl/python/substrate_rs/_native.abi3.so`
   is a **single gitignored file that every build overwrites** — prereg **A1.1**,
   registered on 2026-08-02 as a hazard, one day before it fired. The file held
   `48da7257f35d…` (the value-layer rung's *arm A* baseline binary), not the
   `8311d4356082…` that arms B and C were measured on.
2. **The source was reverted to match it.** The value-layer adapter edits in
   `domains/prog_synthesis.py`, `domains/prog_moves.py` and
   `domains/prog_retrieval.py` were absent from the working tree while present
   in `HEAD`.

The combination is what made the state so hard to see. Each half **corroborated
the other**: `engine_provenance` compared the binary against the *working
tree's* Rust source, found them consistent, and reported `source_match: "own"`
and `stale_rust: []`. An instrument that asks *"does this binary match the
source next to it?"* returns a clean answer for a tree that has been rolled back
wholesale. It cannot ask *"is this the source that is committed?"*

The goal-residual rung therefore ran on a tree that looked internally
consistent, measured everything honestly, and produced a set of numbers
describing a world that no longer existed anywhere except on that disk.

## 2. How it was found

Not by the battery. **`tests/test_arc6_valuelayer_migrated.py` was 29 red**, and
the goal-residual write-up correctly declined to absorb those reds — §6 recorded
them as *"pre-existing … red before this rung; red identically after"* and §7
recorded the engine discrepancy in detail, including the decisive probe
(`add_node({"lst":[1,2,3],"tup":(1,2,3)})` reading **both back as `tuple`**).

**Everything needed to diagnose it was written down; the wrong conclusion was
drawn from it.** §7 read the discrepancy as a fact about the tree — *"the brief
… is false in this worktree"* — and re-pinned the bar downward to match
(48 → 36). The alternative reading, that the *tree* was damaged and the brief
was describing the tree that should exist, was not considered. Prereg **A1.1**
had registered exactly this failure the day before, and the write-up even cited
it (*"A1.1's registered hazard realised"*) — while treating the realised hazard
as a boundary condition rather than as something to repair.

The repair was possible only because **A1.1's archive requirement had been
honoured**: `8311d4356082…` still existed at
`~/ozma-engine-archive/`. Had it not, arm C would have been irreproducible and
the value-layer rung's entire result would have been unverifiable — which is the
scenario A1.1 was written to prevent, arriving on schedule.

**This is the sixth logged instance of the standing failure mode:** reasoning
correctly inside a wrong frame. The premise (*which tree am I standing in?*) was
never checked, because every instrument that could have checked it was
answering a narrower question.

## 3. What was restored (not by this reconciliation — it was already done)

- engine `8311d4356082…`, copied back from the out-of-tree archive;
- the value-layer adapter edits in `domains/prog_synthesis.py`,
  `prog_moves.py`, `prog_retrieval.py`, restored from `HEAD`.

Verified live, in-process, before anything was re-measured:

```
add_node("X", {"lst": [1,2,3], "tup": (1,2,3)})
  -> {'lst': list, 'tup': tuple}          # distinct.  Was both `tuple`.
provenance_line()
  -> engine 8311d4356082 @ <this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so
tests/test_arc6_valuelayer_migrated.py    -> 35/35
```

**A hazard found while verifying this, and worth recording as standing
practice:** the probe must be run **under `conftest.py`**. `site-packages/substrate_rs.pth`
is an absolute path into the *canonical* tree, so a bare
`python -c "import substrate_rs; …"` from inside this worktree resolves the
**canonical tree's** binary — currently `7dd9af13a038…`, which still collapses
list and tuple. The worktree's `conftest.py` puts this tree's build first on
`sys.path`; without it, the coherence check reports the opposite of the truth.
The first probe run during this reconciliation did exactly that and briefly
looked like grounds to stop and report. **An engine probe that does not go
through `conftest` is not a probe of the tree you are standing in.**

## 4. The six red gates: five wrong-world pins, one self-nullifying reference

**None was a defect in the goal-residual mechanism.** Each was verified
independently rather than accepted on the brief's reading.

### 4.1 The lapse cascade — four gates, one cause

`domains/goal_residual_ingest.probe_facts` **measures** the value layer live:
it writes a list attr and a tuple attr and reads them back. On the coherent
engine they no longer collapse, so `value_layer_list_eq_tuple` measures `"0"`.
The row-verdict residual's condition is `fact_equals value_layer_list_eq_tuple
== "1"`, so `gr_condition_lapse` fires and the residual is **stale as shipped**.

| gate | red because | verified |
|---|---|---|
| `…gr2_the_value_layer_fact_condition_lapses_the_row_verdict_residual` | the gate asserted the fact was `"1"` | its own message said what to do: *"the residual SHOULD then be stale; update this gate with the measurement"* |
| `…gr2_all_conditions_hold_in_the_shipped_world` | one residual now stale | the stale one is the row-verdict residual, and only it |
| `…gr2_HEADLINE_seam_c_lapses_when_the_math_codebook_is_populated` | the "every other residual is 0.0" clause | **seam C's own lapse still fires correctly** — only the baseline clause tripped |
| `…gr1_every_residual_discriminates_its_own_signature_from_every_other` | a stale residual charges 0.0 | a *consequence* of the above, not independent: the residual's `weight` is still 51.33 and it charges its full weight the moment its condition is re-satisfied |

**This is GR2 working, live and unprompted, and it is the most interesting thing
in this reconciliation.** Every GR2 demonstration in the original write-up was
*staged* — a fixture shape added, a payload written, a fact hand-flipped. This
lapse was not staged by anyone. A condition was falsified by a change made for
an unrelated reason, and the residual went stale by itself in the next
`run_rules` fixpoint. §4 of the results document said *"a residual that cannot
lapse is a lie with a long half-life"*; this one could, and did.

Per §4's own rule, **staleness is not falsity**: the row-verdict ceiling must be
re-measured before it may be used again. Nothing here re-measures it.

### 4.2 `test_gr4_the_live_mbpp_pass_ids_are_unchanged` — 36 → 48

The gate pinned 36 and measured 48, `lost: []`. Verified rather than assumed:

- the 12 gained ids are **exactly** `results/arc6_valuelayer.json` →
  `arms.C_minus_B.pass_gained`: `161, 249, 257, 272, 290, 393, 413, 418, 436,
  450, 457, 460` — the value layer's own gains;
- the measured list is **set-equal to arm C's 48**, and the accepted list to
  arm C's 95;
- **the bar is still "unchanged", not "48".** The 48 was *not* adopted from the
  patched run. The pre-patch seed (v1.11.0, sha `5302b959daf2`) was rerun on
  the coherent engine specifically for this reconciliation
  (`results/arc6_verdict_gr_baseline_8311d435.json`): **48 pass / 95 accepted**.
  The patched seed then reproduces it exactly — `lost: []`, `gained: []`, on
  both lists. The residual patch is inert, which is what GR4 was written to
  demonstrate.

The gate now asserts the decomposition arithmetically
(`superseded_36 ∪ value_layer_12 == new_48`, disjoint), so the re-pin stays
attributable and cannot be reused to absorb a future gain.

### 4.3 `test_gr4_the_synthesis_seed_diff_is_confined_to_two_rules` — NOT an engine issue

This one is different in kind and is called out so it is not folded into the
engine story. The gate diffs `seeds/program_synthesis.json` in the working tree
against **`HEAD`**. It was written while the rung was uncommitted, so `HEAD`
meant *"the tree before this change"*. **Committing the rung (`921b8967d3`) made
`HEAD` contain the change**, the diff went empty, and the gate reported
`changed == []` — it could no longer demonstrate its claim at all.

A gate whose reference point is `HEAD` self-nullifies the moment its own work is
committed. Re-pointed to a fixed pre-rung commit (`d4177b30ab`, the rung's
parent, seed v1.11.0), plus an assertion that the pin still names a v1.11.0
seed so the pin cannot rot silently. The confinement claim — only `ps_move_mark`
and `ps_move_select` change; `where` and `match` byte-identical; every other
section identical — is re-verified and unchanged.

## 5. What the reconciliation did and did not do

**Re-pinned, in the improvement direction, with dated notes:** all six gates.
Every one keeps its original mechanism claim.

**Made stronger — two gates:**

- the seam-C headline now asserts a **before/after delta** over the stale map
  instead of "every other residual is 0.0"; it therefore also catches a
  codebook change that *un*-stales something, which the old form could not;
- the LOO discrimination gate now runs its scene **twice** — once with all six
  residuals live (the original coverage, retained in full) and once as shipped
  (the stale one must charge exactly 0.0, and its weight must still be non-zero
  so the 0.0 is staleness speaking and not an empty residual).

**No assertion was widened. No coverage gap was created.** The one gate that
could have lost coverage — the LOO — kept it by re-satisfying the condition
rather than by dropping the residual from the loop.

**Not absorbed, per the brief:** `sorted`-on-strings, `Eq(0.0, False)`, the
`inputs_json` boundary. None were touched.

## 6. Reds: the full before/after, enumerated

**Goal-residual suite** (`tests/test_goal_residual_migrated.py`):

| | before | after |
|---|---|---|
| | 6 red / 25 green | **0 red / 31 green** |

The six: `test_gr1_every_residual_discriminates_its_own_signature_from_every_other`,
`test_gr2_all_conditions_hold_in_the_shipped_world`,
`test_gr2_HEADLINE_seam_c_lapses_when_the_math_codebook_is_populated`,
`test_gr2_the_value_layer_fact_condition_lapses_the_row_verdict_residual`,
`test_gr4_the_synthesis_seed_diff_is_confined_to_two_rules`,
`test_gr4_the_live_mbpp_pass_ids_are_unchanged`.

**Reds elsewhere on the coherent tree — NOT this reconciliation's, and NOT
absorbed.** Running the arc-6/arc-4/arc-5 pin files on the coherent engine
gives **9 red node ids**, and **all nine are already enumerated** in the
value-layer rung's own paired sweep
(`results/arc6_valuelayer.json` → `tree_wide_paired_sweep.armC.red_node_ids`,
which lists 14 arm-C-only ids). They are the value layer's outstanding
reconciliation debt, listed here so they are visible rather than characterised:

```
tests/test_arc6_tier0_migrated.py::test_no_python_decision_was_added
tests/test_arc6_tier0_migrated.py::test_string_as_sequence_reaches_the_search_through_a_shipped_template
tests/test_arc6_tier0_migrated.py::test_tmpl_item_in_listvar_fires
tests/test_arc6_tier0_migrated.py::test_tmpl_len_item_vs_var_fires
tests/test_arc6_tier0_migrated.py::test_tmpl_nested_reduction_fires
tests/test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift
tests/test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift
tests/test_reject_informs_repair_migrated.py::test_no_wrong_accept_regression_vs_v1_7_0_baseline
tests/test_retrieval_migrated.py::test_ceiling_task_reproduces_measured_outcome_live[106]
```

Notes on two of them, because they matter to anyone reading the 48:

- `test_reject_informs_repair…::test_no_wrong_accept_regression_vs_v1_7_0_baseline`
  is red **saying the right thing**: *"the set of arc6-tier0 ids reaching `pass`
  changed; every one of them needs a constructed-witness sweep before it may be
  claimed"*, naming `161, 249, 257, 290, 393, 450`. That is the correct
  discipline and this reconciliation does **not** silence it. The witnesses for
  those ids exist — `results/arc6_valuelayer.json` →
  `constructed_witness_sweeps` — but reconciling that gate is the value-layer
  rung's job, not this one's.
- `test_arc6_tier0_migrated.py::test_no_python_decision_was_added` asserts
  `git status --porcelain domains seeds` is empty and so reds for any
  working-tree dirt in those paths **by design**. It is currently red on
  pre-existing dirt (`M seeds/metonymy_patterns.json`, `?? seeds/acquired/`)
  that this reconciliation did not create. **Not narrowed; reported.**

The seven-file pin sweep the goal-residual document cites as "198 green" now
runs **220 green / 4 red** across nine files (more tests, and the four reds are
in the list above).

## 7. Artifacts

| file | what |
|---|---|
| `results/arc6_goal_residuals.json` | **re-measured** on `8311d4356082`, `engine_sha256` at top level. The `48da7257f35d` reading is kept verbatim under `superseded_measurement_48da7257` with its own sha and a `why_superseded` string — not deleted, not overwritten in place. New `GR4_no_regression` section carries the pre/post paired id lists. |
| `results/arc6_verdict_gr_baseline_8311d435.json` | **new.** The pre-patch seed (v1.11.0, `5302b959daf2`) rerun on the coherent engine: 48 pass / 95 accepted. This is what makes GR4's bar "unchanged" rather than "48". |
| `results/arc6_verdict_gr4_gate.json` | regenerated by the gate on the coherent engine: the same 48 / 95. |
| `results/arc6_verdict_gr_baseline.json` | **untouched.** A valid measurement under a condition that no longer holds. A historical record is never converted. |
| `PROGRAM_SYNTHESIS_ARC6_GOAL_RESIDUALS.md` | §10 correction; in-place markers on the header, §5's GR2 table, §5's GR4 block and §7. Nothing deleted. |
| `tests/test_goal_residual_migrated.py` | six gates re-pinned with dated notes; two strengthened. |
| `scripts/arc6_goal_residuals_report.py` | records both lapse directions from the measured fact (the old one-way flip would now be a no-op), plus the GR4 pre/post block and the superseded reading. |

## 8. Standing rules this earns

1. **A results document must ASSERT its engine, not merely record it.** §7
   named `48da7257f35d…` correctly and still reached a false conclusion.
   Naming a sha proves which binary ran — not that it was the *right* binary
   for the committed source.
2. **`source_match: "own"` is not a coherence check.** It compares the binary
   against the source *next to it*, which a wholesale rollback keeps
   consistent. The question it cannot ask is *"is this the source that is
   committed?"* A `git diff HEAD -- <the source the engine is built from>`
   answers that one and costs nothing.
3. **The cheapest coherence check is a behavioural probe of the semantics the
   rung depends on** — here, `probe_facts`' list/tuple read-back. This rung
   *already had* that probe and used it as a *condition* rather than as a
   *precondition*. A rung that depends on an engine semantic should assert it
   before measuring, not merely record what it found.
4. **Run the probe under `conftest`.** A bare `python -c` from a worktree
   resolves the canonical tree's engine via an absolute `.pth` and will report
   the opposite of the truth (§3).
5. **A gate must not pin its reference point to `HEAD`.** Committing the work
   the gate guards then empties the diff and the gate silently stops
   demonstrating anything — here it failed loudly, which was luck, not design
   (§4.3).
6. **When a hazard you registered yesterday fires today, repair it — do not
   re-pin the bar to it.** A1.1 was written on 2026-08-02 and realised on
   2026-08-03. It was cited by name in the write-up that then lowered the bar
   to accommodate it.
