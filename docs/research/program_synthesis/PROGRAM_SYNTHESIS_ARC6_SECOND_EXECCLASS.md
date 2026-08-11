# ARC 6 — A15: THE SECOND `ExecClass` — a ceiling probe on the executor's reach

**Date:** 2026-08-11
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` **amendment A15** (`EC1`–`EC3`),
registered **before** this build.
**Base commit:** `baa24bd` (detached worktree `/home/matt/arc6-second-execclass`).
**Engine:** `953b8e3fa6471a285f5e4d5fb731a721667ecf6e4fffba1f3feca52b96683a85`
— the **committed** binary in this snapshot, unmodified (only its mtime
needed a `touch` to clear a false git-worktree-checkout staleness refusal,
sha unchanged before/after — the exact A14 §7.1 hazard, reproduced
identically). `_native.__file__` resolves from inside this worktree.
Coherence probe passed before every measurement:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` **distinctly**.
**Seed:** `seeds/arc_executor.json` **v1.3.0**, sha256
`4f9d563c89f2c6a20f0c1f4f990f83791221b5aee96b8558013d4ed7e34f22ad`, emitted
by `tools/build_arc_executor_seed.py` and gated byte-identical against it.
**Artifacts:** `results/arc6_second_execclass_probe.json` (the bonus
extension measurement, engine-stamped); no other new bulk artifact.
**Gate:** `tests/test_arc_executor_migrated.py` — **61 collected, 60
green**, the one red **pre-existing and environment-conditional**, same
node id every prior rung has recorded.

**SCOPE: exactly EC1–EC3 (the second-`ExecClass` ceiling probe).** The
re-arm deadlock (AG-5 §5), the silent order-N fallback (WIRE_HANDS §8.1),
and `gr_condition_lapse`'s closed vocabulary (A13/A14's own named-not-fixed
residual) are **untouched**, per the task's explicit boundary.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **EC1 — a genuinely re-measurable second candidate exists, MEASURED not assumed** | **PASS** | `goal_residual_ingest.SPEC` enumerated in full: **five** unwired `GoalResidual` nodes carry the identical structural shape row-verdict's own wired one does. One (`arc6.structural.enum_op_table`) was **live re-run** (stash-protected, sha-verified restore) and produced **genuinely different content** from its committed evidence: `witness_ids` grew **7 → 9** (gained tasks 424, 450) against evidence measured on an older engine (`5c1b472fe674…`). §2 |
| **EC2 — a concrete cost estimate, produced by reading the actual generality of the route Terms** | **PASS, and it beat its own threshold** | reading `ax_dispatch`/`ROUTE`/`_routable`/`_dispatchable` confirmed they already filter over **every** `ExecClass` node via the three-part key (kind + evidence_artifact + source_rid) — so the cost is **0 new rules**, **1 new runner script**, **1 new `ExecClass` seed-data row + edge**, **1 new adapter table line**. Verified in the diff, not estimated: `git diff` on `tools/build_arc_executor_seed.py` touches only `_nodes()`/`_edges()`/`build()`'s metadata — zero bytes changed in any `_r_*` rule function or in `ROUTE`/`_cue_matches`/`_routable`/`_armed`. §3 |
| **EC3 — GO/NO-GO against the pre-registered threshold** | **GO — built** | threshold was "≤2 new seed rules, ≤1 new runner script, no change to `ax_dispatch`'s own route-matching Term structure." Actual cost (0 rules, 1 runner, 0 route-Term changes) **clears it with margin**. Built: a second `ExecClass` (the structural-ceiling residual) + `scripts/arc6_remeasure_structural.py` + a `RUNNERS` table entry, gated with 11 new live scenes mirroring EX1/WH1/IM1's shape. §4 |

**The one thing worth reading if you read nothing else.** Four consecutive
rungs (A10–A14) each independently measured the executor's reach as **one**
`ExecClass`. It is now **two**, added for the cost of **seed data**, not a
rule — confirmed by a byte-level diff, not a design claim. The second class
was not merely wired and left untested: a **real** subprocess-backed
re-measurement of it ran on this engine and found genuinely new information
its own committed evidence did not have. And — reported honestly rather
than oversold, §6 — driving BOTH classes to completion in one boot produces
a real, never-before-reachable **9-goal, non-impotent, dual-order-in-
contention** intermediate state, but the **final** impotent composition it
settles into is identical to A14's own already-measured state 1. The
ceiling this rung raises is real; it did not, by itself, add a third
distinct *impotent* composition to A14's own concentration statistic.

---

## 1. THE DESIGN INVESTIGATION (mirrors A13/A14's own practice: read first, draft bars second)

Registered verbatim in `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A15
before any seed/adapter/runner file was touched. Summarised here so this
document is self-contained:

1. **The full residual set is six, not one.** `domains/goal_residual_ingest.py`'s
   `SPEC` carries six `GoalResidual` entries — `arc6.seam_a.import_oracle`,
   `arc6.seam_b.ir_retarget`, `arc6.seam_c.shape_codebook`,
   `arc6.seam_d.property_atom`, `arc6.structural.enum_op_table`, and the one
   wired one, `arc6.verdict.row_verdict_seed_only` — every one a
   `GoalResidual` with `rid` + `stale` + `holds_under → ResidualCondition`,
   every one eligible for `ag_mint_remeasure` (`seeds/arc_goals.json`,
   byte-frozen) the moment its condition lapses.
2. **The four `arc6.claim.*` pool members are a DIFFERENT, weaker shape and
   are NOT candidates.** `tools/build_arc_goals_seed.py`'s `claims` tuple
   mints `ArcSourceClaim` nodes with **no** `ResidualCondition`, **no**
   `stale` attr, **no** lapse mechanism — `ag_mint_source_claim` mints their
   goal unconditionally, once, from a static node. Answering the task's own
   §1 question directly: **no**, they are not re-measurable in the
   row-verdict sense; treating them as candidates would mean inventing an
   entirely new condition-and-lapse apparatus, a materially bigger and
   different build than this rung's scope.
3. **Every unwired residual already has a standalone measurement script**
   that writes its evidence to a fixed, hard-coded path (the same shape
   `arc6_verdict_report.py` has): `scripts/arc6_a_ceiling.py` (seam A),
   `scripts/arc6_bc_ceiling.py` (seam B **and** C — one script, one shared
   artifact, two `rid`s), `scripts/arc6_d_loo.py` (seam D),
   `scripts/arc6_structural_ceiling.py` (structural).
4. **`reingest_evidence` (`domains/arc_executor.py`) is already generic over
   `rid`** — it looks up the matching `gri.SPEC` entry by `rid` and reads the
   same dotted paths the original ingest used. Wiring a second residual
   needed **zero** changes to `goal_residual_ingest.py` or the re-ingest half
   of the adapter.
5. **`ax_dispatch`/`ROUTE`/`_routable`/`_dispatchable` are already generic
   over the `ExecClass` table**, confirmed by reading the Term builders:
   `ROUTE()` is `Argmin(Filter(NOT_("ExecClass"), ec, _cue_matches(ec, goal)),
   priority)` — a filter over **every** `ExecClass` node. This is the single
   most load-bearing fact in the investigation: a second class is a **seed
   data** addition, not a rule change.
6. **Live-probed: the five unwired residuals' conditions are weaker than
   row-verdict's.** `expected_shas` — the `probe_facts` parameter that would
   make an `<artifact>_present` fact track CONTENT (sha), not just
   existence — is **never populated by any call site in the tree** (grepped
   across `domains/`, `scripts/`, `tests/`). So today the only way any of the
   five can lapse is outright file **deletion**, never content drift, unlike
   row-verdict's genuinely behavioural `value_layer_list_eq_tuple` probe.
7. **And yet a live re-run shows real drift the mechanism in #6 cannot see.**
   With `results/arc6_structural_ceiling.json` stashed and restored
   (sha-verified both before and after), `scripts/arc6_structural_ceiling.py`
   was re-run on this engine: **0.13 s**, exit 0, and a genuinely different
   result — `witness_ids` grew **7 → 9**, gaining tasks 424 and 450, against
   evidence measured on `engine_provenance.sha256 == 5c1b472fe674…` (an
   older engine). Real drift, invisible to the current file-presence-only
   condition.
8. **One candidate carries a real environmental cost the others do not.**
   `scripts/arc6_a_ceiling.py` requires `sympy`; on this machine `sympy` is
   importable under `/usr/bin/python3` (3.12) but **not** under the `python3`
   resolved first on `PATH` (Homebrew 3.13, the interpreter every other
   measurement in this rung ran under). `arc6_bc_ceiling.py`,
   `arc6_d_loo.py` and `arc6_structural_ceiling.py` have **no** third-party
   dependency beyond `substrate_rs` and in-repo `domains/*` modules.
9. **Runtime is cheap across the board** — far below row-verdict's ~140 s:
   `arc6_bc_ceiling.json` self-reports `elapsed_seconds: 1.6`;
   `arc6_d_loo.json` self-reports `8.37`; `arc6_structural_ceiling.py`
   measured live at **0.13 s**.

---

## 2. THE CANDIDATE SURVEY — a table, never a bare claim

| candidate | `rid` | runner script | shared artifact? | 3rd-party dep | measured/self-reported runtime | live content drift shown? | rank |
|---|---|---|---|---|---|---|---|
| row-verdict (already wired) | `arc6.verdict.row_verdict_seed_only` | `arc6_remeasure_row_verdict.py` | no | none | ~140 s (measured, twice, this rung) | yes (organic — engine value-layer fix) | (baseline) |
| **structural** | `arc6.structural.enum_op_table` | `arc6_structural_ceiling.py` | **no** | **none** | **0.13 s (measured live)** | **yes — witness_ids 7→9 (measured live)** | **1st — CHOSEN** |
| seam D | `arc6.seam_d.property_atom` | `arc6_d_loo.py` | no | none | 8.37 s (self-reported) | not attempted this rung | 2nd |
| seam B | `arc6.seam_b.ir_retarget` | `arc6_bc_ceiling.py` | **yes — shares w/ seam C** | none | 1.6 s (self-reported) | not attempted this rung | 3rd |
| seam C | `arc6.seam_c.shape_codebook` | `arc6_bc_ceiling.py` | **yes — shares w/ seam B** | none | 1.6 s (self-reported) | not attempted this rung | 3rd (tied) |
| seam A | `arc6.seam_a.import_oracle` | `arc6_a_ceiling.py` | no | **`sympy` — NOT importable under this tree's default `python3`** | not measured (blocked) | not attempted (blocked) | 4th — deprioritised |
| `arc6.claim.*` (×4) | n/a | n/a | n/a | n/a | n/a | **structurally impossible** — no `ResidualCondition` at all | **not a candidate** |

**Why structural over seam D/B/C** (all three are otherwise viable): seam D
and seam B/C were not independently ruled out — they remain good follow-up
candidates — but structural was the only one this rung **actually re-ran
live** and confirmed produces real drift, and it is the only one with **no**
shared artifact **and** no third-party dependency **and** the fastest
measured runtime. A tie-break made with evidence in hand beats one made on
self-reported numbers alone.

**The seam-A incident, recorded because the process is the result.** The
first attempt to cost seam A ran `scripts/arc6_a_ceiling.py` directly (no
stash) under the default `python3`. `sympy` import failed; the script's own
`except Exception` branch wrote a **partial** artifact to its hard-coded
`OUT` path before returning 1 — silently corrupting the canonical, symlinked
`results/arc6_a_ceiling.json` (sha `c65bfc0e…` → `e95078cd…`). A stash had
been taken immediately before per this rung's own registered discipline, so
recovery was immediate and sha-verified (`c65bfc0e…` restored, confirmed);
`git status --porcelain` in the canonical tree was re-checked clean (it
would not otherwise have shown the corruption, since `results/` is
gitignored). **The rule this adds to A12.2's own registered practice:**
stash the protected file(s) before running **any** measurement script
directly, even a fast one with no known tree-mutation history — the hazard
here was not a timeout, it was a script's own error-handling path writing a
partial result to its hard-coded output on first touch, with no `finally`
to catch it.

---

## 3. THE COST ESTIMATE (measured against the diff, not estimated)

| file | change | measured |
|---|---|---|
| `tools/build_arc_executor_seed.py` | +84/−7 lines | **only** `_nodes()`, `_edges()`, `build()`'s version/description touched — zero bytes changed in `ROUTE`/`_cue_matches`/`_routable`/`_dispatchable`/`_armed`/`_in_pool`/any `_r_*` rule builder (`git diff` read in full, §"what broke" item 1) |
| `seeds/arc_executor.json` | regenerated, +33/−2 lines | one new `ExecClass` node (local_id 4011) + one new `has_exec_class` edge; **rule count unchanged: 5 → 5**, gated (`test_a15_the_seed_added_ZERO_new_rules`) |
| `domains/arc_executor.py` | +2/−1 lines | one new `RUNNERS` table entry |
| `scripts/arc6_remeasure_structural.py` | **new, 128 lines** | mirrors `arc6_remeasure_row_verdict.py`'s stash/run/restore shape, sized down (one script, no seed-patch apply/revert dance); stdlib-only (gated `test_a15_no_third_party_dependency_in_the_new_runner`); never touches the substrate (gated `test_a15_the_new_runner_makes_no_decision_either`) |
| `tests/test_arc_executor_migrated.py` | +320/−6 lines | 2 pre-existing pins **inverted** (`len(cls)==1` → `==2`; `exec_classes_held==["re_measure"]` → `==["re_measure","re_measure"]`, both with docstrings explaining why, the WH1 precedent), 11 new gates |

**Against the pre-registered EC3 threshold** ("≤2 new seed rules, ≤1 new
runner script, no change to `ax_dispatch`'s own route-matching Term
structure"): **0 new rules** (better than ≤2), **1 new runner script**
(exactly at the limit), **0 changes** to any route-matching Term (better
than the "no change" requirement — confirmed by diff, not promised).
**Clears the bar with margin.**

---

## 4. WHAT WAS BUILT

```
tools/build_arc_executor_seed.py        +ExecClass local_id 4011, +edge,
                                        version 1.2.0 -> 1.3.0.  ZERO rule
                                        changes.
seeds/arc_executor.json                 REGENERATED (never hand-edited),
                                        sha256 4f9d563c89f2…
domains/arc_executor.py                 +1 RUNNERS table entry
scripts/arc6_remeasure_structural.py    NEW — the second runner
tests/test_arc_executor_migrated.py     2 pins inverted, 11 new gates
scripts/arc6_second_execclass_probe.py  NEW — the bonus extension probe
                                        (informational, not gated)
results/arc6_second_execclass_probe.json  NEW — its artifact
PROGRAM_SYNTHESIS_ARC6_PREREG.md        amendment A15 appended
PROGRAM_SYNTHESIS_ARC6_SECOND_EXECCLASS.md  this file
```

### 4.1 The 11 new gates, what each demonstrates

| test | demonstrates |
|---|---|
| `test_a15_the_structural_residual_is_UNWIRED_by_default` | the shipped boot's default pool composition is byte-for-byte unchanged by adding the second class — a wider capability table does not by itself create new work |
| `test_a15_forcing_staleness_MINTS_the_second_remeasure_goal_and_it_ROUTES` | the bar: a genuinely second `re_measure` goal, routed to its own runner via the three-part key |
| `test_a15_the_two_classes_NEVER_cross_route` | both directions (A7's own standing discipline): row-verdict never routes to the structural runner and vice versa |
| `test_a15_TWO_simultaneously_routable_goals_still_SERIALIZE_to_ONE_order` | **new scenario, never exercised by any prior rung** (there was only ever one executable goal): `ax_dispatch`'s "at most one outstanding order globally" guard, tested under real multi-candidate contention, not just read off the rule |
| `test_a15_it_actually_RUNS_the_structural_remeasurement_LIVE` | a real subprocess invocation of the unmodified measurement script, on this engine, mirroring EX1 |
| `test_a15_the_frozen_structural_artifact_is_STILL_byte_identical` | the runner's stash/restore discipline holds |
| `test_a15_the_fresh_measurement_genuinely_DIFFERS_from_committed_evidence` | the load-bearing finding this candidate was picked for: the re-run is not a no-op |
| `test_a15_the_CONDITION_REANCHORS_and_the_residual_UNSTALES` | mirrors EX1's own bar for the first class, on the second |
| `test_a15_the_seed_added_ZERO_new_rules` | EC2/EC3's own headline cost claim, gated rather than left as prose |
| `test_a15_no_third_party_dependency_in_the_new_runner` | the cost-comparison finding that ruled out seam A |
| `test_a15_the_new_runner_makes_no_decision_either` | mirrors `test_ex6_the_runner_makes_no_decision_either` for the second runner |

### 4.2 Why the structural residual is a genuine second capability, not a fixture

The staleness *trigger* used in every gated scene is **synthetic** — a
`_put_fact` poke (the same "narrow attribute poke" methodology A13 §7.1
validated for `headroom_n → 0`), because per finding #6 the condition
mechanism cannot organically detect content drift. **The measurement
itself, once ordered, is not synthetic**: `test_a15_it_actually_RUNS_the_
structural_remeasurement_LIVE` and `test_a15_the_fresh_measurement_
genuinely_DIFFERS_from_committed_evidence` both exercise a real subprocess
invocation of the unmodified `scripts/arc6_structural_ceiling.py`, and the
result genuinely differs from the committed evidence (§1 item 7). This
separation — synthetic trigger, real measurement — is stated explicitly in
every affected test's docstring, mirroring AG-5 §2.2's own "the reanchor is
the rung's one modelling choice, stated in the open" precedent.

---

## 5. REGRESSION — A LIST OF NODE IDS, NEVER A COUNT

Both arms below ran on the **same binary** (`953b8e3fa647`), in this
worktree; the **before** arm was measured **first**, before any code file
was touched (only the A15 prereg-amendment doc edit preceded it).

| suite | before | after | failing node ids — **identical before and after** |
|---|---|---|---|
| `test_arc_executor_migrated` | 49 passed, 1 failed (50 collected) | **60 passed, 1 failed (61 collected)** | `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` |
| `test_arc_goals_migrated` | 37 / 37 | 37 / 37 | — |
| `test_goal_residual_migrated` | 29 passed, 1 failed, 1 skipped | 29 passed, 1 failed, 1 skipped | `test_gr4_the_live_mbpp_pass_ids_are_unchanged` |
| `test_arc6_valuelayer_migrated` | 35 / 35 | 35 / 35 | — |
| `test_arc_magnitude_migrated` | 43 / 43 | 43 / 43 | — |

The executor suite's collected count rises **50 → 61**: 11 new A15 gates,
**zero removed, zero renamed** (the two inverted pins keep their original
names with updated bodies, exactly the WH1 precedent). Both reds are the
**same two** every prior rung since A12 has recorded, same conditions
(`results/` untracked in this checkout; the engine's short sha not in
`test_gr4`'s three-entry allowlist — neither is this rung's to fix, and
neither was touched).

`seeds/arc_goals.json`, `seeds/goal_residuals.json`,
`seeds/arc_magnitude.json`, `seeds/program_synthesis.json`,
`domains/arc_goal_ingest.py`, `domains/goal_residual_ingest.py` — all
byte-identical to `HEAD` (`test_ex6_the_seeds_below_this_rung_are_UNTOUCHED`,
green, unchanged). `ag_ask`'s tie logic untouched in every particular.

**Source audit.** `test_ex6_the_adapter_CANNOT_contain_a_hidden_decision`
green, unchanged — the one adapter edit (a `RUNNERS` dict entry, a plain
string) needed no change to the audit's allow-list. The new runner passes
the module-specific audit `test_a15_the_new_runner_makes_no_decision_either`
mirrors from `test_ex6_the_runner_makes_no_decision_either`.

---

## 6. THE BONUS EXTENSION PROBE — honestly reported, not oversold

EC3's optional clause: *"if time and the registered null-reading discipline
allow, re-run a scoped version of A14's own sweep to see whether the new
capability actually produces a genuinely distinct real pool state."*
`scripts/arc6_second_execclass_probe.py` (informational — **not** part of
the gated suite) drove **both** `re_measure` residuals to real completion in
one boot: row-verdict is already organically stale on this engine; the
structural residual was forced stale via the same synthetic poke §4.2
describes.

```
pool at boot                                     8 goals
after forcing structural stale (poke, no file touched)  9 goals — BOTH
                                                  re_measure goals present
                                                  and routable at once —
                                                  NEVER REACHABLE BEFORE A15
structural remeasurement runs, real, 0.13s   ->  retires, pool back to 8
row-verdict remeasurement runs, real, 137.8s ->  retires, pool -> 7
final impotent verdict: pool_n=7, nearest_unroutable_kind=supply_blocker,
                         nearest_unroutable_agid=…missing_structural_primitive
```

**What this shows, honestly.** (a) The **9-goal intermediate pool** — two
simultaneously stale, simultaneously routable `re_measure` goals in the
same pool — is a genuinely **new, real, never-before-reachable state**, and
`ax_dispatch`'s serialization guard was measured resolving it correctly
(also formally gated, `test_a15_TWO_simultaneously_routable_goals_still_
SERIALIZE_to_ONE_order`). (b) **The FINAL steady-state composition, once
both retire, is composition-identical to A14's own already-measured "state
1"** — `pool_n=7`, the same seven `supply_blocker`/`source_claim` goals,
the same `nearest_unroutable_kind: supply_blocker`. Once a `re_measure`
goal retires it leaves **no** permanent trace on `POOL()` — true of the
first class and now confirmed true of the second — so exercising a second
capability that *also* only ever retires does not, by itself, grow A14's
real-only impotent-state count from 2 toward the `n≥5` its own IC2 bar
needed.

**A self-correction, named because the process is the result.** The probe
script's own `is_a_THIRD_distinct_real_composition` field reads `true` in
the artifact — that field is **poorly named and overclaims**: it only
checks "differs from the boot pool," which is trivially true of any
retirement, not "differs from any state A14 already measured," which is
what would actually matter for A14's own concentration question. The raw
pool lists in the artifact are accurate; the summary field's name is not.
Recorded here rather than silently re-run to relabel a JSON key after a
140-second live measurement had already completed cleanly.

**What WOULD grow A14's real-only n**, per this rung's own honest reading:
a capability whose retirement changes *which* `nearest_unroutable_kind`
the final pool settles on — not merely a capability that removes one more
`re_measure` goal from an otherwise-unchanged remainder. Wiring a THIRD
class (e.g. seam D or seam B/C) would not change this either, by the same
argument, unless the newly-reachable pool member is itself a
`supply_blocker`/`source_claim` (which no currently-known mechanism can
retire). This is consistent with — and sharpens — A14 §9.2's own finding
that growing the real-only subset requires either new capability *of a
different shape* or further hypothetical depletion, not simply "one more
`re_measure` route."

**A second incident during this probe, caught before any tree-mutating
runner ran.** The probe's first draft clamped every other goal's
`headroom_n` to 0 to isolate each target in turn but never restored the
clamp between calls — so the *second* call's own target goal was still
clamped to 0 by the first call's loop, `pending_orders` came back empty, and
the script's own `assert len(pending) == 1` caught it **before**
`axe.run_order` (and therefore before any tree-mutating subprocess) was
ever invoked. Verified: `git status --porcelain` and every protected-file
sha were unaffected by the failed run. Fixed by snapshotting and restoring
real headroom values around each `run_one` call; the corrected script
produced the numbers above.

---

## 7. EVERYTHING THAT BROKE

Recorded because the process is the result (A11–A14's own standing
practice).

1. **The seam-A incident** (§2) — a partial-write-on-error hazard in
   `arc6_a_ceiling.py`, not this rung's own code, tripped by running it
   directly without a stash. Recovered, sha-verified, zero lasting damage.
2. **`exec_classes_held` is a RAW, non-deduplicated `MapList` over `ExecClass`
   names, and a second class sharing the same semantic name (`"re_measure"`)
   legitimately produces a duplicate entry.** `_r_impotent` (A13, untouched
   by this rung — editing it would be a rule edit this rung's own registered
   threshold specifically avoided) was written when exactly one `ExecClass`
   existed, so nobody needed to ask whether the list should be a set. Not a
   bug in the firing guard (which never reads this field — it is "purely
   descriptive," per `_r_impotent`'s own comment) and not a bug in A15's own
   new class — but a genuine, previously-invisible property of an existing
   rule, surfaced by widening the table it reads. **Reported, not patched**:
   fixing it is a `_r_impotent` edit, out of this rung's own registered
   scope. The pre-existing pin (`test_im1_fires_when_the_WHOLE_POOL_is_
   unroutable`) was **inverted, not removed**, with a docstring naming
   exactly this.
3. **The `sole_survivor`/`ax_rearm` interaction, found while building
   `live_run_structural`.** Combining `sole_survivor` (raw `status:
   'retired'`) with a REAL run that bumps the measurement epoch, in the same
   scene as a DIFFERENT goal that is genuinely stale on this engine
   (row-verdict), lets `ax_rearm`'s latch legitimately re-admit the retired
   goal — because from `ax_rearm`'s point of view a hand-retired goal with a
   still-stale residual is indistinguishable from a genuinely retired one.
   This is the anti-oscillation latch working **correctly**, not a defect —
   `_leave_pool_without_retiring`'s own docstring (A13) already named the
   general shape of this hazard, but no prior rung had combined
   `sole_survivor` with a live, epoch-bumping run of a DIFFERENT goal in one
   scene, because no prior rung had a second executable goal to make that
   scene possible. Fixed by adding `_sole_survivor_no_retire` (the
   `headroom_n → 0` pool-exit technique, applied to "every other goal," which
   `ax_rearm` never inspects) and using it in `live_run_structural`.
4. **The extension probe's own headroom-clamp bug** (§6) — caught cleanly by
   its own assertion before any tree mutation, fixed, re-run.
5. **The A12.2 mtime-staleness hazard reproduced identically to A14 §7.1.**
   `git worktree add` left several `.rs` mtimes racing the committed `.so`'s;
   `sha256sum` before and after a plain `touch` confirmed no content change.
   Not the glibc/rustc mismatch WIRE_HANDS §6 hit — this binary already ran;
   only the provenance check's own mtime heuristic needed correcting.
6. **The default Bash-tool timeout (2 minutes) killed a `pytest` invocation
   mid-way through the `live_run` fixture's ~140 s remeasurement**, despite
   an explicit inner `timeout 480` in the same command — the OUTER wrapper's
   own default fired first. This is A12.2's exact hazard, on a THIRD
   surface (a tool-call timeout rather than a shell `timeout` or a suite
   default): `seeds/program_synthesis.json` was left patched and
   `results/arc6_verdict_before.json` was left overwritten by the killed
   run's own `before` arm, both in the **canonical** tree via this
   worktree's symlinked `results/`. **Recovery, verified by sha, no
   guessing:** the tracked seed restored via `git checkout --`; the
   untracked artifact restored from the runner's own crash stash at
   `/tmp/arc6_remeasure_z5t12y8l/` — cross-checked against **two** older,
   independent stashes (`v2ug4sp3`, `1oiko27u`) that agreed on the exact
   same sha, strong corroboration this was the true pristine value rather
   than a guess. Both trees verified clean before any further measurement.
   **Added to A12.2's own registered rule:** a harness's own default
   per-call timeout is exactly as dangerous as an explicit short one — an
   inner `timeout N` does not protect against an outer wrapper timeout
   shorter than `N`. Every subsequent invocation in this rung passed an
   explicit, generous **tool-level** timeout (not only a shell-level one).

---

## 8. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do.

1. **The reach is now TWO nodes, still not general.** This rung raised the
   ceiling from one `ExecClass` to two; it did not build a mechanism that
   makes wiring a *third* progressively cheaper than the second was (the
   cost is the same seed-data shape each time, but each new candidate still
   needs its own hand-written runner script). Seam D and seam B/C remain
   good, unattempted next candidates (§2).
2. **The synthetic-staleness-trigger gap (§1 item 6 / §4.2) is a real,
   load-bearing limitation of the underlying mechanism, named not fixed.**
   Every gated A15 scene forces eligibility with a poke because
   `probe_facts`'s `expected_shas` is unwired. Wiring it (so
   `<artifact>_present` tracks content, not just existence) would make
   BOTH the structural residual's own condition AND — by the same
   mechanism — every other artifact-backed residual's condition genuinely
   behavioural, closing the asymmetry with row-verdict noted in §1 item 6.
   Not built here: it is a `goal_residual_ingest.py` change, and this
   rung's own registered scope was the `ExecClass` table, not the
   condition-probing mechanism underneath it.
3. **§6's honest correction is itself the sharpest finding in this
   document, and it bounds what a THIRD `ExecClass` would buy.** A new
   `re_measure` route does not, on the evidence gathered here, grow A14's
   real-only concentration statistic — only a capability whose retirement
   changes which pool composition the loop settles into would. No such
   capability was identified or built this rung.
4. **`exec_classes_held`'s non-deduplication (§7 item 2) will get worse with
   every further `ExecClass` added**, growing the list by one duplicate
   name per class that shares the "re_measure" label. Harmless today
   (purely descriptive, never read by a firing guard, and A14 already
   established the field carries no concentration information regardless
   of count) but worth fixing before a THIRD class is added, if the fix is
   ever prioritised.
5. **This rung never exercised the second `ExecClass` under `arc_magnitude`
   (order-N) loaded.** Every A15 scene uses plain `boot()` (order-1 only,
   matching AG-5's own EX1–EX6 convention). Whether `mg_select`'s order-N
   collapse prices the structural remeasurement goal differently from
   order-1 — and whether that changes which of the two simultaneously
   routable goals `ax_dispatch` picks first under order-N — is unmeasured,
   mirroring AG-5's own uncertainty #4 for the FIRST class, one level up
   for the second.
6. **The re-arm deadlock and the silent order-N fallback are untouched**,
   per the task's explicit scope boundary, and neither was exercised by any
   scene in this rung in a way that would have required touching them.

---

## 9. FILES

| file | what |
|---|---|
| `tools/build_arc_executor_seed.py` | the emitter — `RUNNER_2`/`ARTIFACT_2`/`SOURCE_RID_2`, `_nodes()` gains local_id 4011, `_edges()` gains its edge, version 1.2.0 → 1.3.0. **Zero rule changes** |
| `seeds/arc_executor.json` | **regenerated**, sha256 `4f9d563c89f2c6a20f0c1f4f990f83791221b5aee96b8558013d4ed7e34f22ad`, gated byte-identical against its emitter |
| `domains/arc_executor.py` | +1 `RUNNERS` table entry |
| `scripts/arc6_remeasure_structural.py` | the second runner — stash/run/restore, stdlib-only |
| `scripts/arc6_second_execclass_probe.py` | the bonus extension probe (informational, not gated) |
| `results/arc6_second_execclass_probe.json` | its artifact, engine-stamped |
| `tests/test_arc_executor_migrated.py` | 2 pins inverted, 11 new gates (§4.1) |
| `PROGRAM_SYNTHESIS_ARC6_PREREG.md` | amendment A15 appended, registered before the build |
| `PROGRAM_SYNTHESIS_ARC6_SECOND_EXECCLASS.md` | this file |

**In this worktree's `git status`, not part of the change:**

- `data` and `results` appear as untracked **symlinks** into the canonical
  tree (39 G / 21 G, gitignored). Must not be staged.
- `runners/dsl/python/substrate_rs/_native.abi3.so` does **not** appear as
  modified — its content is byte-identical to `HEAD`'s; only its mtime was
  touched (§7 item 5).

**Nothing in the canonical tree changed.** `/home/matt/ozmadev/ocelot`'s own
`git status --porcelain` was re-verified clean after every live measurement
in this rung, including after the two incidents in §7 that were caught and
recovered.

---

## 10. REPRODUCE

```bash
# --- the worktree ---------------------------------------------------------
git worktree add --detach /home/matt/arc6-second-execclass baa24bd
cd /home/matt/arc6-second-execclass
ln -s /home/matt/ozmadev/ocelot/data    data        # 39G, gitignored
ln -s /home/matt/ozmadev/ocelot/results results     # 21G, gitignored

# --- the engine.  Reproduces byte-identically to HEAD's committed binary on
#     this box.  If a git-worktree checkout leaves .rs mtimes racing the
#     .so's (a false "STALE" refusal, content unaffected), touch it: -------
touch runners/dsl/python/substrate_rs/_native.abi3.so
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

# --- the gate (includes the ~140s live row-verdict remeasurement AND the
#     <1s live structural remeasurement — ALWAYS an explicit, GENEROUS
#     tool-level timeout, not only a shell-level one; SS7 item 6). ---------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 -m pytest tests/test_arc_executor_migrated.py \
    --confcutdir=$PWD -q -p no:randomly -rf   # 60 passed, 1 failed (SS5)

# --- the regression arms, run identically before and after ----------------
for s in test_arc_goals_migrated test_goal_residual_migrated \
         test_arc6_valuelayer_migrated test_arc_magnitude_migrated; do
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
    PYTHONPATH=runners/dsl/python:. \
    python3 -m pytest tests/$s.py --confcutdir=$PWD -q -p no:randomly -rf
done

# --- the bonus extension probe (~140s; informational, not gated) ----------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 scripts/arc6_second_execclass_probe.py
#   -> results/arc6_second_execclass_probe.json
```

**`--confcutdir=$PWD` on every pytest invocation** — same reason as every
prior arc-6 rung: this worktree is not nested inside the canonical repo.

**Engine provenance.** Every number in this document was produced by
`953b8e3fa6471a285f5e4d5fb731a721667ecf6e4fffba1f3feca52b96683a85`, resolving
from inside `/home/matt/arc6-second-execclass`.

**Contamination.** No MBPP test-split `code` was read except by the
existing verdict battery/report scripts and `arc6_structural_ceiling.py`'s
own probes, both unmodified and both pre-existing — their reads are the
measurement itself. Nothing entered a codebook, a cue table or a route
table beyond the one new `ExecClass` row, which is graph DATA (an
artifact path and a `rid` string), never a task-derived value.
