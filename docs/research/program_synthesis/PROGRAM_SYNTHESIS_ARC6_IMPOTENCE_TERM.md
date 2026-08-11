# ARC 6 — A13: THE IMPOTENCE TERM

**Date:** 2026-08-11
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` **amendment A13** (`IM1`–`IM5`),
registered **before** this build.
**Base commit:** `7a6bf55` (detached worktree `/home/matt/arc6-impotence-term`).
**Engine:** `953b8e3fa6471a285f5e4d5fb731a721667ecf6e4fffba1f3feca52b96683a85`
— built fresh in this worktree from the same source `7a6bf55` ships, and it
reproduces **byte-identically** to `HEAD`'s own committed
`_native.abi3.so` (verified by `sha256sum` both before and after the build;
`git status` never lists the binary as modified in this worktree). Unlike
`PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md` §6, **no glibc/rustc mismatch was hit
here** — the committed binary in this snapshot of `main` already is
`953b8e3f…`, so this rung measures on the SAME engine the prior rung did, with
full continuity. Archived out of tree at
`~/ozma-engine-archive/_native.abi3.so.953b8e3f` (already present from the
prior rung; re-verified identical). Coherence probe passed before every
measurement: `add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back
`[1,2,3]` and `(1,2,3)` **distinctly**.
**Seed:** `seeds/arc_executor.json` **v1.2.0**, sha256
`49aa286f4d76999ebcadc47d6065f05b879257a3a2aa4bc7f7aabceb14ee83b5`, emitted by
`tools/build_arc_executor_seed.py` and gated byte-identical against it
(`test_ex6_the_seed_REGENERATES_byte_identically`).
**Artifact:** `results/arc6_impotence_term.json` (engine + seed stamped; every
scene below is a live boot, not a fixture replay).
**Gate:** `tests/test_arc_executor_migrated.py` — **50 collected, 49 green**,
the one red **pre-existing and environment-conditional**, same node id as
before this rung (§4).

**SCOPE: the impotence term only.** `ag_ask`'s tie logic is untouched (frozen,
byte-identical `seeds/arc_goals.json`), MG4/decomposition is untouched, and the
other named remaining uncertainties (silent fallback, `ag_ask`/`ax_dispatch`
reading different collapses, the re-arm deadlock) are named where relevant
but not built against.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **IM1 — fires on POOL-quantified impotence, both directions** | **PASS** | positive: retiring the sole routable goal from a healthy 8-goal pool mints exactly one `AgendaVerdict{kind:'impotent'}` naming the remaining 7. Negative: the shipped, untouched boot (routable goal present) mints nothing. A third, unregistered-but-checked case: an EMPTIED pool (0 goals) also mints nothing — "done" is not "impotent." §2 |
| **IM2 — the discriminator: does NOT fire on a winner-only misread** | **PASS** | the shipped boot itself is the discriminating scene — order-1's winner is the unroutable 42-task blocker, and the routable `re_measure` goal sits lower in the ranking. A winner-only reading would call this impotent; the pool-quantified term correctly does not. §3 |
| **IM3 — no regression** | **PASS** | five suites, identical failing-node-id lists before/after (one pre-existing red each, same ids); `seeds/arc_goals.json` / `goal_residuals.json` / `arc_magnitude.json` byte-identical to `HEAD`; seed regenerates byte-identically; adapter source audit green; 48 pass ids / 95 accepted ids byte-identical to `PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md`'s own list. §4 |
| **IM4 — composes with the order-N wiring A11/A12 landed** | **PASS** | with `arc_magnitude` + the tier ladder loaded, retiring the sole routable goal (order-N's own pick, per WH1) makes BOTH `arc_sel_agid` and `mg_sel_agid` converge on the SAME now-unroutable goal, and the fact fires there specifically — not one step earlier, while the routable goal was still in the pool. §5 |
| **IM5 — mint-once by pool signature, lapse via UNMODIFIED `gr_condition_lapse`** | **PASS** | repeated `run_rules()` over an unchanged impotent pool mints exactly one verdict, never a duplicate; a genuinely different impotent pool (even inside one epoch) mints its own; bumping `arc_measure_epoch` marks the held verdict stale through the **untouched** `gr_condition_lapse` rule (`seeds/goal_residuals.json` byte-identical to `HEAD`), and a fresh verdict mints for the new epoch because the pool is still impotent. §6 |

**The one thing worth reading if you read nothing else.** A12/WH4 designed
"terminate honestly" and registered two constraints for whoever built it:
quantify over the pool, not the winner; and reuse `gr_condition_lapse`, don't
rebuild it. Both landed with **zero new DSL Term and zero changes to any seed
this rung doesn't own** — `_routable` (the per-goal routability test
`ax_dispatch` itself uses) and `POOL()` (`ag_select`'s own filter) were
already exactly the vocabulary the design called cheap, and
`gr_condition_lapse`'s `match` already carries no type constraint on the node
it lapses, so a fifth rule (`ax_impotent`) rides the existing engine without
touching it.

---

## 1. WHAT CHANGED

Five files edited (one of them a regenerated artifact of another), two added.
**No new DSL Term, no engine source change, no edit to any seed file this rung
does not own** (`arc_goals.json` / `goal_residuals.json` / `arc_magnitude.json`
all byte-identical to `HEAD`, gated).

```
tools/build_arc_executor_seed.py     the emitter.  MAPLIST / _dispatchable /
                                      _pool_unroutable / _pool_nonempty /
                                      _pool_sig / _nearest_unroutable_goal /
                                      _r_impotent, two new productions,
                                      version 1.1.0 -> 1.2.0
seeds/arc_executor.json              REGENERATED from that emitter (never
                                      hand-edited)
domains/arc_executor.py              + agenda_verdicts() -- one pure read-off,
                                      same shape as orders()/pool()/statuses()
tests/test_arc_executor_migrated.py  + 10 new gates (IM1-IM5), + one line in
                                      the existing every-rule-fires gate
scripts/arc6_impotence_term_measure.py  NEW -- the measurement runner
results/arc6_impotence_term.json     NEW -- the artifact
PROGRAM_SYNTHESIS_ARC6_PREREG.md     amendment A13 appended
PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_TERM.md  NEW -- this file
```

### 1.1 The design investigation, in brief (full form: PREREG A13)

`ax_dispatch`'s own route (`_cue_matches` / `ROUTE` / `_routable`,
`tools/build_arc_executor_seed.py`) is already the per-goal "can the executor
act on this" predicate: a three-part key (kind + `evidence_artifact` +
`source_rid`) against the one shipped `ExecClass`. Lifting it to the whole
pool is one `Not(Exists(...))`:

```python
def _dispatchable(goal_var="g"):
    # _routable(goal_var) AND Count(mint_source) == 1 -- ax_dispatch's FULL
    # routability test, not an approximation of it.
    return AND(_routable(goal_var),
               EQ(COUNT(NEIGH(V(goal_var), "mint_source")), L(1)))

def _pool_unroutable():
    return NOT(EXISTS(POOL(), "gru", _dispatchable("gru")))
```

`POOL()` is imported unchanged from `tools/build_arc_goals_seed.py` — the
SAME filter `ag_select` ranks over — so "the pool" this rule quantifies over
is literally the pool, not a redefinition of it. A non-emptiness guard
(`Exists(POOL(), g, True)`) sits alongside it, because `Not(Exists(...))`
over an empty source is vacuously true and an agenda that finished everything
is not the same fact as one that is stuck.

### 1.2 Mint-once by pool signature, not by tick

The registered requirement was explicit: keyed on the pool's own signature,
not a rate limit. `MapList` (`runners/dsl/src/term.rs`, confirmed evaluated by
the SAME `evaluate()` the rule engine runs — read at the match-arm level, not
assumed from the synth-only sub-language that also happens to use the name)
turns the pool into an ordered `Value::List` of agids in one Term;
`ToJsonString` of that list gives a plain string, comparable by `Eq` with **no
sort**:

```python
def _pool_sig():
    return STR(MAPLIST(POOL(), "gsig", A(V("gsig"), "agid")))
```

The mint guard is `Not(Exists(<existing non-stale AgendaVerdict with this
exact pool_agids>))`. Two reads of the *same* graph state walk the same
underlying `Filter`, so this is a same-run signature — exactly what mint-once
needs, and it deliberately sidesteps the tree's own named residual ("no
string-ordering primitive; `sorted`-on-strings is unfixed",
`ArcGoalPolicy.tie_break`'s comment in `tools/build_arc_goals_seed.py`)
because *equality*, not *ordering*, is all a signature needs here.

### 1.3 The lapse rides `gr_condition_lapse` — literally, not by analogy

```json
{"type": "ResidualCondition",
 "ckind": "fact_equals", "filter_value": "arc_measure_epoch",
 "expected_str": "<epoch at mint>"}
```

`gr_condition_lapse`'s `match` is `[["r", "holds_under", "c"]]` — **no type
constraint on `r`** (`seeds/goal_residuals.json`, unmodified). Any node with a
`stale` attr and a `holds_under` edge to a `ResidualCondition` is lapsed by
that rule, so `AgendaVerdict` rides it for free, the same way the testimony
reply (`ag_reply_mints_testimony_*`, `seeds/arc_goals.json`) already does.
Zero new lapse mechanism; the byte-identity of `goal_residuals.json` to `HEAD`
is itself part of the evidence (§6, gated by
`test_im5_goal_residuals_seed_is_UNMODIFIED_the_lapse_is_RIDDEN_not_rebuilt`).

---

## 2. IM1 — POOL-QUANTIFIED IMPOTENCE, BOTH DIRECTIONS

`results/arc6_impotence_term.json → IM1_positive_and_negative`.

**Positive.** Shipped boot (no `arc_magnitude`), the sole routable goal
(`AGID = arc.remeasure.arc6.verdict.row_verdict_seed_only`) is removed from
`POOL()` by setting `headroom_n` to 0 (a pool-exit path `ax_rearm` never
inspects — see §7.1 for why this matters). Read off the graph after
`run_rules()`:

```
kind                    impotent
epoch                   0
pool_n                  7
pool_agids              ["arc.supply...budget","arc6.claim.seam_b...",
                          "arc6.claim.seam_d...","arc6.claim.tier0...",
                          "arc6.claim.valuelayer...",
                          "arc.supply...missing_dimension",
                          "arc.supply...missing_structural_primitive"]
nearest_unroutable_agid arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive
nearest_unroutable_kind supply_blocker
stale                   0.0
```

`AGID` is absent from `pool_agids`; the list matches `axe.pool(s)` read back
independently. Before the retirement, zero verdicts.

**Negative.** The shipped, **untouched** boot: `AGID` is in the pool, zero
`AgendaVerdict` nodes exist.

**A third case, checked though not separately registered.** Retiring every
goal (`status: 'retired'` on all eight) empties the pool; zero verdicts —
`Not(Exists(...))` over an empty pool is not read as impotence, because the
non-emptiness guard refuses first. An agenda that finished is not an agenda
that is stuck.

**Live, not just synthetic.** `live_run`'s own post-execution state — a REAL
138-second re-measurement retired `AGID` for real, pool 8 → 7 — independently
registers as impotent with no scene construction at all
(`test_im1_the_REAL_live_run_scene_reaches_impotence_too`).

---

## 3. IM2 — THE DISCRIMINATOR

`results/arc6_impotence_term.json → IM2_discriminator`.

A12/WH4 §5.1 named the defect precisely: the CURRENT stop string
(`no_executable_goal_was_selected`, computed in a measurement script) reads
the **winner alone**, so a pool holding one routable goal ranked second would
misread as impotent. The **shipped, unmodified boot already is that scene**:

```
winner (arc_sel_agid)   arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive
AGID in pool            True
verdicts                []
```

Order-1's own winner is the unroutable 42-task blocker; `AGID` is present and
routable, merely outranked. A winner-only implementation would fire here.
`ax_impotent` does not, because it quantifies `Not(Exists(POOL(), g,
dispatchable(g)))` — false the instant *any* pool member is dispatchable,
independent of rank.

---

## 4. IM3 — NO REGRESSION. A LIST OF NODE IDS, NEVER A COUNT.

Both arms below ran on the **same binary** (`953b8e3fa647`), in this
worktree; the **before** arm is the unmodified tree at `7a6bf55`.

| suite | before | after | failing node ids — **identical before and after** |
|---|---|---|---|
| `test_arc_executor_migrated` | 39 passed, **1 failed** (40 collected) | **49 passed, 1 failed** (50 collected) | `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` |
| `test_arc_goals_migrated` | **37 / 37** | **37 / 37** | — |
| `test_goal_residual_migrated` | 29 passed, **1 failed**, 1 skipped | 29 passed, **1 failed**, 1 skipped | `test_gr4_the_live_mbpp_pass_ids_are_unchanged` |
| `test_arc6_valuelayer_migrated` | **35 / 35** | **35 / 35** | — |
| `test_arc_magnitude_migrated` | **43 / 43** | **43 / 43** | — |

The executor suite's collected count rises **40 → 50**: ten new IM1–IM5
gates, zero removed, zero renamed.

### 4.1 The two reds, unchanged, neither caused here

Both are the SAME two `PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md` §4.1 already
named and neither is this rung's to fix (out of scope per the task
constraints):

- `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` — `results/` is
  gitignored and untracked in this checkout, so its `git show HEAD:…` witness
  returns empty. The property the gate is *about*
  (`protected_files_restored_byte_identical`) passes on every run here; the
  chosen witness is what fails.
- `test_gr4_the_live_mbpp_pass_ids_are_unchanged` — asserts the engine's short
  sha is in a three-entry allowlist that predates `953b8e3fa647`. **Not
  widened** — this rung did not touch that gate or its allowlist.

### 4.2 The 48/95 ids reproduce byte-identically to the prior rung

`results/arc6_verdict_gr4_gate.json`, written live by the suite:

```
pass_ids     n=48   [16, 20, 58, 59, 69, 82, 84, 85, 89, 90, 120, 127, 132,
                     135, 138, 139, 142, 145, 161, 227, 233, 234, 249, 257,
                     266, 272, 276, 278, 281, 290, 309, 312, 393, 394, 404,
                     406, 410, 413, 418, 433, 436, 443, 450, 457, 458, 460,
                     472, 477]
accepted_ids n=95
```

Identical, element for element, to `PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md`
§4's own list. This rung touches no measurement logic and no seed the MBPP
battery reads, so this is expected, not merely hoped for — it is reported
because the arc's standing rule is that a baseline is a list, and this is
that list, re-read.

### 4.3 The seeds below this rung are untouched, gated

`test_ex6_the_seeds_below_this_rung_are_UNTOUCHED` (unchanged, still green)
diffs `seeds/arc_goals.json`, `seeds/arc_magnitude.json`,
`seeds/goal_residuals.json`, `seeds/program_synthesis.json`,
`domains/arc_goal_ingest.py`, `domains/goal_residual_ingest.py` against
`HEAD` — all six byte-identical. `ag_ask`'s tie logic
(`seeds/arc_goals.json`) is untouched in every particular.

### 4.4 The source audit still passes

`test_ex6_the_adapter_CANNOT_contain_a_hidden_decision` — green, unchanged.
The one new adapter function (`agenda_verdicts`) is a pure read-off using only
already-allowed substrate calls (`nodes`, `node`); the audit's allow-list
needed no change and was not touched.

---

## 5. IM4 — COMPOSES WITH THE ORDER-N WIRING

`results/arc6_impotence_term.json → IM4_composes_with_order_N`.

With `arc_magnitude` loaded and the tier ladder installed (`_boot_with_magnitude(ladder=True)`,
the exact WH1 fixture):

| | `arc_sel_agid` (order-1) | `mg_sel_agid` (order-N) | verdicts |
|---|---|---|---|
| **before** retiring `AGID` | `…missing_structural_primitive` | **`AGID`** (order-N's own pick, per WH1) | **0** |
| **after** retiring `AGID` | `…missing_structural_primitive` | **`…missing_structural_primitive`** | **1** |

Before retirement, order-N is still picking the routable goal — exactly WH1's
finding, reproduced live — and the term is correctly silent. After removing
`AGID` from the pool (the same `headroom_n → 0` technique, not a status
retirement — see §7.1), **both** collapses converge on the same now-unroutable
goal, reproducing WH2 §3.1 iteration 1's real finding (there measured at
margins 35.0 / 6.64, "not a tie under either collapse") as a **structural**
fact rather than a value coincidence: the impotence term does not read either
collapse's margin, only routability, and it fires exactly where both hands
would have nothing to do.

The minted verdict's `nearest_unroutable_agid` equals `mg_sel_agid` (order-N),
confirming the purely-descriptive field correctly follows `SEL_AGID` — order-N
when live, per A11/WH1 — never re-deriving its own ranking.

---

## 6. IM5 — MINT-ONCE BY POOL SIGNATURE, LAPSE VIA UNMODIFIED `gr_condition_lapse`

`results/arc6_impotence_term.json → IM5_mint_once_and_lapse`.

| step | verdict count | detail |
|---|---|---|
| first impotent pool (7 goals) | **1** | epoch 0, stale 0.0 |
| 2× more `run_rules()`, pool unchanged | **1** | same `_id` — no double-mint |
| a SECOND, different impotent pool (6 goals), same epoch | **2** | pool_n ∈ {7, 6}, both stale 0.0 — two genuinely distinct impotent states, both true, both held |
| `arc_measure_epoch` bumped (pool still impotent) | **3 total, 1 live** | both epoch-0 verdicts → stale 1.0; ONE new epoch-1 verdict mints (matching the CURRENT pool signature), stale 0.0 |

The lapse is asserted to be `gr_condition_lapse` firing, not a parallel rule:
`seeds/goal_residuals.json` is diffed against `HEAD` in the same test that
makes the behavioural claim
(`test_im5_goal_residuals_seed_is_UNMODIFIED_the_lapse_is_RIDDEN_not_rebuilt`)
— byte-identical.

**Twin-run determinism.** The IM1-positive scene run twice in one process,
independently booted, produces byte-identical `AgendaVerdict` content
(`results/arc6_impotence_term.json → twin_run_determinism.byte_identical:
true`).

---

## 7. EVERYTHING THAT BROKE

Recorded because the process is the result.

### 7.1 A synthetic retirement walked straight into `ax_rearm` — the FIRST design draft's test scene

The first attempt at an IM1/IM5 scene retired `AGID` the way
`sole_survivor`/`test_wh3_the_ORDER_N_stamp_OUTLIVES_…` already do —
`set_attr(status, 'retired')`. Bumping the epoch afterward brought the goal
**straight back into the pool**: `ax_retired_epoch` stamped `retired_epoch`,
and `ax_rearm`'s guard (`status=='retired'` AND the underlying
`GoalResidual.stale==1.0` AND `retired_epoch != current epoch`) fired,
because on THIS engine the residual is **genuinely, permanently stale**
(the value-layer list/tuple collapse is real, not a fixture) — nothing in the
synthetic scene ever ran the actual re-measurement that would un-stale it.
**This is the anti-oscillation latch working exactly as designed**, not a bug
in `ax_impotent` — but it silently invalidated the intended "pool stays
impotent across an epoch bump" test. Fixed by leaving the pool via
`headroom_n → 0` instead of `status → 'retired'`, a path `ax_rearm` never
inspects (its match requires `status=='retired'`). Recorded because it is
exactly the kind of interaction the "quantify over the pool" directive was
trying to get right, one level down: a hand-built test scene has to respect
the SAME structural rules the rule itself does, or it measures the wrong
thing.

### 7.2 The first `live_run`-based IM1 gate assumed a fixed verdict count

`live_run` is a **module-scoped** fixture shared with `test_ex4_*`'s
`latch_cells`, which walks the anti-oscillation latch through a real epoch
bump on the SAME graph. Because `test_ex4_*` runs earlier in file order, by
the time the new `test_im1_the_REAL_live_run_scene_reaches_impotence_too`
executed, the shared graph already held **two** `AgendaVerdict` nodes (one
stale, one live) rather than the one the first draft assumed — the test
failed with `2 == 1`. Not a defect in the rule (this is exactly IM5's
lapse-and-remint behaviour, correctly exercised by a fixture this rung did
not write); fixed by asserting on the **live (non-stale) subset**, which is
robust to how much of that shared history has already run.

### 7.3 Nothing else broke

No engine rebuild was needed (§ header), no seed this rung does not own
needed touching, and the emitter's `--check` passed on the first
regeneration after the rule was written correctly the first time (the
`MapList`/`ToJsonString` round-trip was verified with a standalone probe
before it was wired into the rule — see §1.2 — which is why it did not need a
second pass).

---

## 8. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do. Named, not built against —
out of this rung's scope per the task's own constraints.

1. **A VERDICT'S CONDITION LAPSES ON EPOCH ADVANCE ONLY, NOT ON POOL
   COMPOSITION DRIFT.** §6's "different pool, same epoch" step shows TWO
   non-stale verdicts held simultaneously once the pool composition changes
   without an intervening measurement — the first (`pool_n=7`) describes a
   pool state that no longer exists once a further goal leaves, but it is not
   marked stale until the NEXT epoch bump, because the only condition wired
   is `fact_equals(arc_measure_epoch)`, per the registered requirement to
   reuse `gr_condition_lapse` with **no new mechanism**. Both verdicts are
   TRUE statements about the pool AS OF their own epoch, so this is not
   incorrect, but a reader must compare `pool_agids` against the CURRENT pool
   to know which one is current — a second, pool-signature-keyed condition
   kind would need a change to `gr_condition_lapse`'s closed `MISMATCH`
   vocabulary (`seeds/goal_residuals.json`), which this rung's scope
   explicitly excludes touching.
2. **`_dispatchable`/`POOL()` inherit the exposures they were built from,
   unmodified.** `POOL()` is `ag_select`'s own filter, imported verbatim,
   including its known headroom-null exposure (`_in_pool`'s own coalesced
   variant is NOT used here — deliberately, so "the pool" this rule quantifies
   over is literally the pool, not a hardened redefinition of it). If that
   exposure is ever fixed upstream in `ag_select`, `ax_impotent` inherits the
   fix automatically; if it is not, `ax_impotent` does not make it worse, but
   does not fix it either.
3. **THE OTHER TWO CANDIDATES ((a) ask-a-different-question, (b)
   mint-a-capability-goal) ARE NOW MEASURABLE, AND STILL NOT BUILT.** A12/WH4
   §5.3's own argument for building (c) first was that it produces the count
   that would decide between (a) and (b) — how often the loop ends impotent,
   and whether the impotence concentrates on one missing `ExecClass` or
   spreads. `AgendaVerdict.nearest_unroutable_kind` / `.exec_classes_held` are
   exactly that count's raw material, but no sweep across scenes has been run
   to actually decide (a) vs (b) — this rung built the measuring instrument,
   not the measurement campaign.
4. **THE RE-ARM DEADLOCK (AG-5 §5) AND THE SILENT ORDER-N FALLBACK
   (WIRE_HANDS §8.1) ARE BOTH STILL LIVE**, unmodified and out of this rung's
   scope, exactly as named in A13. §7.1 above measured the re-arm latch
   firing correctly, which is orthogonal to whether the deadlock scenario AG-5
   §5 named is itself resolved — it is not, and nothing here touches it.
5. **`ag_ask` AND `ax_impotent` NOW READ DIFFERENT THINGS FROM THE SAME
   AGENDA WITHOUT EITHER KNOWING ABOUT THE OTHER.** On a scene where the pool
   is impotent AND (hypothetically, not observed live in this rung's scenes)
   still carries a margin under `ArcAskPolicy.margin_threshold` for some
   reason, both `ag_ask` and `ax_impotent` could in principle fire in the same
   fixpoint — a tie-under-ignorance question minted alongside an honest
   impotence verdict. Not contradictory (a tie between two unroutable goals is
   still impotent), not observed in any scene this rung constructed, and not
   guarded against either way; named because A13 did not register a bar for
   it and this rung did not go looking for a scene that would exercise it.

---

## 9. FILES

| file | what |
|---|---|
| `tools/build_arc_executor_seed.py` | the emitter — `MAPLIST`, `_dispatchable`, `_pool_unroutable`, `_pool_nonempty`, `_pool_sig`, `_nearest_unroutable_goal`, `_r_impotent`; two new productions (`has_agenda_verdict`, `holds_under` AgendaVerdict→ResidualCondition); version 1.1.0 → 1.2.0 |
| `seeds/arc_executor.json` | **regenerated** from that emitter, never hand-edited; gated byte-identical by `test_ex6_the_seed_REGENERATES_byte_identically` |
| `domains/arc_executor.py` | `agenda_verdicts()` — one pure read-off |
| `tests/test_arc_executor_migrated.py` | ten new gates: `test_im1_fires_when_the_WHOLE_POOL_is_unroutable`, `test_im1_does_NOT_fire_while_the_pool_is_healthy`, `test_im1_an_EMPTY_pool_is_not_impotent_it_is_DONE`, `test_im1_the_REAL_live_run_scene_reaches_impotence_too`, `test_im2_the_discriminator_a_winner_only_reading_would_be_WRONG_here`, `test_im4_composes_with_the_order_N_wiring`, `test_im5_mint_once_by_pool_signature_not_by_tick`, `test_im5_a_DIFFERENT_impotent_pool_mints_its_OWN_verdict`, `test_im5_lapses_through_the_UNMODIFIED_gr_condition_lapse`, `test_im5_goal_residuals_seed_is_UNMODIFIED_the_lapse_is_RIDDEN_not_rebuilt`; plus one added assertion in `test_every_rule_in_this_seed_is_shown_to_FIRE_live` |
| `scripts/arc6_impotence_term_measure.py` | the measurement runner — IM1/IM2/IM4/IM5 scenes + twin-run check |
| `results/arc6_impotence_term.json` | the artifact, engine + seed stamped |
| `PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_TERM.md` | this file |
| `PROGRAM_SYNTHESIS_ARC6_PREREG.md` | **amendment A13** appended |

**In this worktree's `git status`, not part of the change:**

- **`data` and `results` appear as untracked.** They are **symlinks** into the
  canonical tree (39 G / 21 G, gitignored — the `.gitignore` patterns match
  directories, not symlinks). They must not be staged.
- `runners/dsl/python/substrate_rs/_native.abi3.so` does **not** appear as
  modified — unlike the prior rung, this rung's freshly built engine matches
  the committed one byte-for-byte.

**Nothing in the canonical tree changed.** This worktree's changes are
isolated to itself; the canonical `/home/matt/ozmadev/ocelot` tree's
`git status --porcelain` is unaffected by anything in this document.

---

## 10. REPRODUCE

```bash
# --- the worktree ---------------------------------------------------------
git worktree add --detach /home/matt/arc6-impotence-term 7a6bf55
cd /home/matt/arc6-impotence-term
ln -s /home/matt/ozmadev/ocelot/data    data        # 39G, gitignored
ln -s /home/matt/ozmadev/ocelot/results results     # 21G, gitignored

# --- the engine.  Reproduced byte-identically to HEAD's committed binary on
#     this box; rebuild anyway for a from-source guarantee. --------------
export PATH="$HOME/.cargo/bin:$PATH"     # rustup's rustc 1.97.1, if installed
bash scripts/engine_build.sh
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
#   953b8e3fa6471a285f5e4d5fb731a721667ecf6e4fffba1f3feca52b96683a85

# --- the coherence probe.  STOP if these read back the same. --------------
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs; s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst']!=a['tup'])"

# --- the seed is EMITTED, never hand-edited --------------------------------
python3 tools/build_arc_executor_seed.py            # writes seeds/arc_executor.json
python3 tools/build_arc_executor_seed.py --check    # "up to date"

# --- the measurement artifact ----------------------------------------------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 scripts/arc6_impotence_term_measure.py    # -> results/arc6_impotence_term.json

# --- the gate (includes the live 138s re-measurement fixture) --------------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 -m pytest tests/test_arc_executor_migrated.py \
    --confcutdir=$PWD -q -p no:randomly -rf   # 49 passed, 1 failed (SS4.1)

# --- the regression arms, run identically before and after the change -----
for s in test_arc_executor_migrated test_arc_goals_migrated \
         test_goal_residual_migrated test_arc6_valuelayer_migrated \
         test_arc_magnitude_migrated; do
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
    PYTHONPATH=runners/dsl/python:. \
    python3 -m pytest tests/$s.py --confcutdir=$PWD -q -p no:randomly -rf
done
```

**`--confcutdir=$PWD` on every pytest invocation** — same reason as
`PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md` §10: the invocation every arc-6 rung's
numbers were taken under.

**Engine provenance.** Every number in this document was produced by
`953b8e3fa6471a285f5e4d5fb731a721667ecf6e4fffba1f3feca52b96683a85`, resolving
from inside `/home/matt/arc6-impotence-term`.

**Contamination.** No MBPP test-split `code` was read by anything in this
rung; the only battery invocation is inside the pre-existing `live_run`
fixture this rung did not write, and the pass/accepted id lists it produces
are quoted, not re-derived.
