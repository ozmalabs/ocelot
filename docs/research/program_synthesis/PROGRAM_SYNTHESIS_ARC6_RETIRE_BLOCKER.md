# ARC 6 — A17: RETIRING A `supply_blocker`-DESCENDED POOL MEMBER — the gap A15 named, closed at the grain A16 minted

**Date:** 2026-08-11
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` **amendment A17** (`AR17a`-`AR17c`),
registered **before** this build.
**Base commit:** `80f353e` (detached worktree `/home/matt/ocelot-arc6-retire-blocker`,
branch `arc6-retire-blocker`).
**Engine:** `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`,
copied into this worktree and **verified resolving from inside it** —
`substrate_rs._native.__file__` is
`/home/matt/ocelot-arc6-retire-blocker/runners/dsl/python/substrate_rs/_native.abi3.so`
— the **same** binary A16/MG4 measured on (the box's committed `.so` has not
moved since). Coherence probe passed before every measurement:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` **distinctly**.
**Seed:** `seeds/arc_decompose.json` **v1.1.0** (bumped from v1.0.0), sha256
`7a1f82db9d1b564ceb8746e58b9bd14e19ef40973f898487ba3b8e9ebd917609`, emitted by
`tools/build_arc_decompose_seed.py` and gated byte-identical against it.
**Gate:** `tests/test_arc_decompose_migrated.py` — **28/28 green** (19
pre-existing + 9 new A17 gates); the five other arc-6 suites reproduce their
own known baselines unchanged (§5).
**No new Rust, no new runner script, no change to `ax_dispatch`/`ROUTE`/
`_routable`** — confirmed by diff, not promised (`test_ar17_no_new_rust_
and_ax_dispatch_UNTOUCHED`).

**SCOPE: exactly AR17a-AR17c — investigate every `supply_blocker`/
`source_claim`/`decomposition_tier` goal kind for a real retirement
mechanism, and build the one found.** The re-arm deadlock, the silent
order-N fallback, `ag_ask`/`ax_dispatch` collapse-agreement in general,
`gr_condition_lapse`'s closed vocabulary, `results/arc6_import_impedance.json`,
fold-up, and a general re-verification mechanism for tiers 2-4 of the same
ladder are all **untouched**, per the task's explicit boundary.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **AR17a — the survey, every kind classified with evidence** | **DONE** | Six kinds surveyed (`supply_blocker`×3, `source_claim`×4-as-one-shape, and the previously-unnamed fifth kind `decomposition_tier` MG4 mints), each classified by reading the actual rule/seed code, not by re-quoting a prior rung's prose. §2 |
| **AR17b — the GO/NO-GO criterion, registered before building** | **GO — built** | A real, checkable, currently-unbuilt mechanism was found: `decomposition_tier` children (A16's own MG4 output) carry no `mint_source` edge, so `ax_dispatch`/`_routable` cannot ever route them — but their own retirement condition (full witness coverage of one measured tier's own task-id increment) is expressible with **zero new Rust, zero new runner script, zero `ax_dispatch` change** — one adapter fact-probe pair + one Rule, reusing the artifact the ALREADY-WIRED second `ExecClass` (A15) already re-measures. Built, and measured to correctly DECLINE on the real, currently-reachable state (§3) as well as FIRE on a documented construction (§4). §3-§4 |
| **AR17c — no regression, node-id lists not counts** | **PASS** | The six gate suites reproduce the **same** failing node ids before and after, paired and named. `arc_executor.py`, `build_arc_executor_seed.py`, `arc_goals.json`, `goal_residuals.json`, `arc_magnitude.json`, `program_synthesis.json` all byte-identical to `HEAD`; `seeds/arc_decompose.json` regenerates byte-identically from its own (edited, version-bumped) emitter. §5 |

**The one thing worth reading if you read nothing else.** A15 named the
exact gap this rung closes: growing A14's real-only impotent-state count
needs a capability whose retirement changes *which* `nearest_unroutable_kind`
the pool settles on — and named that no currently-known mechanism can retire
a `supply_blocker` or `source_claim` goal. A16 landed since, and *minted a
fifth kind* (`decomposition_tier`) without naming it as one, and asserted —
without a dedicated investigation — that no runner could ever execute
"supply a structural primitive." **That assertion does not survive contact
with the shipped Rust source**: tier 1 of the measured ladder (`B0`, 8
named units, 0 new `TermNode` variants) is not hypothetical outside work —
it is *already built*, verified by grep against `runners/dsl/src/
synth_enumerate.rs`/`term.rs`, not by trusting a docstring. This rung builds
the mechanism that lets the graph notice — and measures, honestly, that on
the real state it currently reaches (even after a live re-measurement on
this engine) that mechanism correctly **declines**: two of tier 1's ten task
ids (`18`, `310`) remain outside the witness-verified set. The gap A15 named
is real and closable at this grain; it is not yet closed by anything this
system can do *unaided* — the honest, load-bearing finding this rung
returns is the mechanism plus the measured shortfall, not a claim of full
resolution.

---

## 1. THE PROBLEM, RESTATED PRECISELY

`supply_blocker` goals (`missing_structural_primitive`, `missing_dimension`,
`budget`) and `source_claim` goals (the four `arc6.claim.*` nodes) have never
had any way to leave `POOL()` except the synthetic `headroom_n → 0` poke
A13 §7.1 validated for constructing test scenes. `ax_dispatch`'s route table
(`ExecClass`, `_routable`, `_dispatchable`) only ever targeted the ONE
`re_measure` goal (A10), then a SECOND `re_measure` residual (A15) — never a
`supply_blocker` or `source_claim` goal, and A15's own investigation
concluded correctly that the four `source_claim` goals cannot be (they carry
no `ResidualCondition`/`stale` apparatus at all). A16 landed MG4
(decomposition) in between, splitting the 42-task `missing_structural_
primitive` parent into four `decomposition_tier` children — but its own
module docstring asserted, without investigating, that none of THOSE could
be retired either.

This rung investigates that specific, narrower, more recent claim, and finds
it false at one tier.

---

## 2. THE SURVEY — every `supply_blocker`/`source_claim`/`decomposition_tier` kind, a table not a bare claim

| goal kind | agid(s) | source shape | condition/lapse mechanism? | classification | evidence |
|---|---|---|---|---|---|
| `supply_blocker` / `budget` | `arc.supply.arc6.seam_a.import_oracle.budget` | `_r_mint_blocker`, minted from `GoalResidual{rid:'arc6.seam_a.import_oracle'}.reach_class_counts` | **none** — no retire rule anywhere in the tree targets `supply_blocker` | **GENUINELY OPEN** | "raise the search budget" has no natural bounded termination by its own definition (`PROGRAM_SYNTHESIS_ARC6_A_CEILING.md` §2: composition deeper than `max_size`); no existing runner treats it as a checkable, bounded action |
| `supply_blocker` / `missing_dimension` | `…missing_dimension` | same source | none | **GENUINELY OPEN** | supplying a real dimension (à la arc 5's π) is a genuine capability build for THESE 4 ids (`163,246,252,293`); no existing runner/script targets it; a different, bigger build than this rung's scope |
| `supply_blocker` / `missing_structural_primitive` (PARENT, whole 42-task claim) | `…missing_structural_primitive` | same source | none (before decomposition); after a horizon reply, MG4's `mg_decompose_retire` moves it to `status='decomposed'` — a REFRAMING via decomposition, not a resolution | **DECOMPOSABLE** (already decomposed by A16) | tiers 2-4 need 10+ new `Term` variants, a cross-cutting string-order fix with an unpriced fixture-migration cost, a `Lit`-boundary fix, and a `Recurse` capability decision — none built; only tier 1 is bounded and (partially) already-done, see below |
| `source_claim` ×4 (`seam_b_signature_39_of_257`, `seam_d_verbatim_35_of_36`, `tier0_hs1_0_of_10`, `valuelayer_supersedes_row_verdict`) | `arc6.claim.*` | `_r_mint_source_claim`, minted unconditionally from a static `ArcSourceClaim` node | **none, structurally** — `ArcSourceClaim` carries no `holds_under` edge and no `stale` attr, and appears in no rule's `match` clause anywhere in the tree except the one-shot mint (confirmed by reading every rule in `seeds/arc_goals.json`, not assumed) | **GENUINELY UNRESOLVABLE at this rung's cost** | making any of the four re-measurable means inventing an entire condition-and-lapse apparatus for a node type that has none — A15's own finding, independently reconfirmed here. Ironic and worth naming: one of the four (`tier0_hs1_0_of_10`) is now itself STALE (§2.1) — the mechanism gap is real on both sides |
| `decomposition_tier` (NEW, MG4/A16's own output — not surveyed as a distinct kind by any prior rung) | `…missing_structural_primitive.tier{1,2,3,4}.0` | `mg_decompose`, minted once a horizon reply triggers `decompose_required` | **built this rung** — `mg_tier_retire` reads a `TierWitnessFact` | **RESOLVABLE AT TIER 1, DEMONSTRATED; NOT YET NATURALLY REACHED** | §3-§4 |

### 2.1 The `tier0_hs1_0_of_10` irony, named because it sharpens the `source_claim` finding

`arc6.claim.tier0_hs1_0_of_10`'s own claim, quoted verbatim from the seed:
*"HS1 failed 0 of 10 converted (tier 0)"*. Amendment A2 (2026-08-02)
recorded this outcome, but the SAME amendment also found the *cause* was a
row-verdict boundary bug (non-scalar answers could never compare equal), not
the op-table itself — and by this rung's own §3 finding, the tier-0 op-table
bundle is fully built and (partially) witness-verified. The claim this
`source_claim` node asserts is therefore **itself now stale** — and nothing
in the tree can ever notice, because `ArcSourceClaim` has no lapse mechanism
at all. This is not claimed as a target for this rung (closing it needs the
same "invent a condition-and-lapse apparatus" build named above), but it is
recorded as independent confirmation that the `source_claim` gap is real on
both sides: neither the mechanism nor (in at least one case) the content
that mechanism would need to check has stayed in sync.

---

## 3. THE MECHANISM'S DESIGN, AND WHY IT IS NOT "A THIRD `ExecClass`"

**Read before drafting bars, per this arc's own standing practice.**
`_routable`'s three-part key (`tools/build_arc_executor_seed.py`) requires a
goal to carry a `mint_source` edge to a node with an `rid` matching the
`ExecClass`'s own `source_rid`. `mg_decompose`'s own effects (`seeds/
arc_decompose.json`, unchanged by this rung) add only `has_subgoal` (from
the parent) and `has_arc_goal` (from the agenda) — **no `mint_source` edge
at all**. A `decomposition_tier` goal is therefore structurally unroutable
by the existing `ax_dispatch` machinery, full stop — not merely
unrouted-by-omission. Making it routable would require EITHER growing
`mg_decompose` to mint a `mint_source` edge to some new residual-shaped node
(a bigger, riskier change to a mint rule this same arc just finished
correcting once, A16 §7 item 1) OR relaxing `_dispatchable`'s `Eq(Count(
mint_source), 1)` guard (a change to `ax_dispatch`'s own core routing
invariant, explicitly out of scope per A13-A16's shared boundary).

**This rung does neither.** It builds a THIRD, independent retirement
mechanism, in the SAME "self-contained seed, mechanical adapter, pure Rule"
shape A16 already used for decomposition itself — never touching
`arc_executor` at all:

```
domains/arc_decompose_ingest.py
  probe_tier_witness_coverage()      PURE MEASUREMENT.  Reads TWO dotted
                                      paths off results/arc6_structural_
                                      ceiling.json (the SAME artifact
                                      arc_magnitude_ingest.LADDER_ARTIFACT
                                      already names): each bundle's
                                      CUMULATIVE unlocked_ids (a set
                                      difference gives a tier's own
                                      increment, the IDENTICAL arithmetic
                                      arc_magnitude_ingest.probe_tier_ladder
                                      already performs for increment_n) and
                                      strict_reach.witness_and_in_budget_ids
                                      (freshly re-measurable by the
                                      ALREADY-WIRED second ExecClass, A15's
                                      scripts/arc6_remeasure_structural.py).
                                      One set-containment check per tier.
  install_tier_witness_facts()       Mechanical: one add_node("TierWitness
                                      Fact", ...) per record.  Mirrors
                                      goal_residual_ingest.probe_facts/
                                      install_facts's OWN "measure, then
                                      write the answer down" shape exactly.

seeds/arc_decompose.json v1.1.0
  mg_tier_retire   ONE new rule.  Retires a decomposition_tier child when a
                   TierWitnessFact names its own (parent_ladder_key,
                   tier_order) pair with all_ids_covered==1.0 -- via the
                   SAME headroom_n -> 0 pool-exit A13 SS7.1 / A15 SS4.2 /
                   A16 decision 1 already validated three times over.  ZERO
                   edits to seeds/arc_goals.json.  status='resolved' is a
                   DISTINCT, descriptive terminal token from the parent's
                   'decomposed' -- never itself the exclusion mechanism.
```

**Cost, measured against the diff, not estimated** (mirroring A15 EC2's own
discipline):

| file | change | measured |
|---|---|---|
| `domains/arc_decompose_ingest.py` | +92/−0 lines | two new functions, both pure Python (dotted-path reads + set arithmetic), zero `substrate_rs` import, zero `.evaluate(`, zero `run_rules` (`test_mg4d_no_python_decision_was_added`, unchanged, still passes over the whole file) |
| `seeds/arc_decompose.json` | regenerated, +146/−2 lines | one new rule (`mg_tier_retire`); rule count 3 → 4, gated (`test_arc_decompose_seed_loads_and_carries_FOUR_rules`) |
| `tools/build_arc_decompose_seed.py` | +91/−3 lines | the new rule builder + docstring/description updates; version 1.0.0 → 1.1.0 |
| `tests/test_arc_decompose_migrated.py` | +232/−9 lines | 1 pre-existing pin inverted (rule-count set, WH1 precedent), 9 new gates |
| `domains/arc_executor.py`, `tools/build_arc_executor_seed.py`, `seeds/arc_goals.json`, `seeds/goal_residuals.json`, `seeds/arc_magnitude.json`, `seeds/program_synthesis.json`, `runners/dsl/src/*.rs` | **UNCHANGED** | byte-identical to `HEAD`, asserted (`test_ar17_no_new_rust_and_ax_dispatch_UNTOUCHED`) |

Against AR17b(iii)'s registered threshold ("no new Rust, no `ax_dispatch`
change, ≤1 new adapter function pair, ≤1 new rule"): **0 new Rust** (meets
it), **0 `ax_dispatch` changes** (meets it), **1 new adapter function pair**
(exactly at the limit), **1 new rule** (exactly at the limit). **Clears the
bar.**

---

## 4. THE MEASUREMENT — a real DECLINE on the natural state, a documented FIRE on a construction

### 4.1 AR17b(ii)'s DECLINE half — the honest natural-state finding

On the artifact this rung's own base commit ships
(`results/arc6_structural_ceiling.json`, `strict_reach.
witness_and_in_budget_ids == [75, 98, 106, 161, 257, 290]`, 6 ids), every
tier reads `all_ids_covered == 0.0` — including tier 1, whose own 10-id
increment (`18, 75, 98, 106, 161, 257, 290, 310, 424, 450`) is missing
**four** ids from the witness set (`18, 310, 424, 450`).
(`test_ar17_probe_reads_the_REAL_committed_artifact_HONESTLY`.)

**A real, stash-protected, sha-verified live re-run on this rung's own
engine narrows but does not close the gap.**
`scripts/arc6_structural_ceiling.py` (unmodified — the SAME script A15's
second `ExecClass` already wires) was re-run live
(`test_ar17_a_LIVE_stash_protected_remeasurement_shows_REAL_partial_progress`):

| | before (committed) | after (live, this engine) |
|---|---|---|
| `strict_reach.witness_and_in_budget_ids` | `[75, 98, 106, 161, 257, 290]` (6) | `[75, 98, 106, 161, 257, 290, 424, 450]` (8) |
| tier 1's missing ids | `18, 310, 424, 450` (4) | `18, 310` (2) |
| tier 1 `all_ids_covered` | `0.0` | **still `0.0`** |

The delta (`+424, +450`) is the **identical** finding A15 §1 item 7 made on
a different engine, reproduced independently here — real drift, not a
fixture. The artifact was restored and sha-verified byte-identical
(`5af750cd4dcc…`) both before and after, per A12.2/A15/A16's own protected-
file discipline. **On the currently-reachable state — even after a real
re-measurement — the mechanism correctly declines to retire tier 1.** This
is the honest result AR17b(ii) asked to be measured, not assumed.

### 4.2 The FIRE half — a documented construction, per A13 §7.1 / A15 §4.2's own precedent

Because the natural trigger is not cheaply reachable live (closing the
remaining 2-id gap would mean building capability this tree does not have —
the exact structural work `missing_structural_primitive` itself names), the
rule's positive path is demonstrated the same way every prior rung in this
arc demonstrated a rare natural trigger: a documented, narrow construction —
here, installing the `TierWitnessFact` a completed re-measurement WOULD
produce, exactly A15 §4.2's own "synthetic trigger, real rule" separation.

`test_ar17_a_CONSTRUCTED_witness_fact_retires_ONLY_the_matching_tier`:
starting from a live-decomposed 4-child pool (horizon=5.0, the same scene
MG4b/c already established), installing a `TierWitnessFact{ladder_key:
'missing_structural_primitive', tier_order:1.0, all_ids_covered:1.0}` and
running `run_rules()` once:

| child | before | after |
|---|---|---|
| tier 1 | `status='minted'`, `headroom_n=10.0` | `status='resolved'`, `headroom_n=0.0`, `orderN_headroom_n=0.0`, `resolved_because='tier_units_witness_verified_live'` |
| tier 2 | `status='minted'`, `headroom_n=16.0` | **unchanged** |
| tier 3 | `status='minted'`, `headroom_n=6.0` | **unchanged** |
| tier 4 | `status='minted'`, `headroom_n=10.0` | **unchanged** |

**Negative control, both halves**
(`test_ar17_a_witness_fact_naming_a_DIFFERENT_tier_leaves_tier1_UNRESOLVED`):
a fact naming tier 2 with `all_ids_covered=1.0` resolves tier 2 and only
tier 2; a fact naming tier 1 itself with `all_ids_covered=0.0` does NOT
resolve it — the rule reads the fact's value, not merely its presence for
that key.

**Structural pool exclusion, both collapses**
(`test_ar17_the_resolved_tier_is_STRUCTURALLY_excluded_from_BOTH_pools`):
once resolved, tier 1's agid is absent from `POOL()` under both `ag_select`
(order-1) and `mg_select` (order-N, the same shared `Filter`), read via
`adi.pool_agids` (the adapter's own mirror of `POOL()`'s predicate); the
other three children remain present.

**Fixpoint terminates**
(`test_ar17_the_fixpoint_TERMINATES_a_second_pass_moves_nothing`): a second
and third `run_rules()` pass over the resolved state moves nothing.

---

## 5. REGRESSION — A LIST OF NODE IDS, NEVER A COUNT

Both arms below ran on the **same binary** (`c5e50801d48a`), in this
worktree; the **before** arm was measured first, before any code file was
touched (only this file's own eventual existence and the A17 prereg
amendment preceded it).

| suite | before | after | failing node ids — **identical before and after** |
|---|---|---|---|
| `test_arc_executor_migrated` | 60 passed, 1 failed (61 collected) | 60 passed, 1 failed (61 collected) | `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` |
| `test_arc_goals_migrated` | 37 / 37 | 37 / 37 | — |
| `test_goal_residual_migrated` | 29 passed, 1 failed, 1 skipped | 29 passed, 1 failed, 1 skipped | `test_gr4_the_live_mbpp_pass_ids_are_unchanged` |
| `test_arc6_valuelayer_migrated` | 35 / 35 | 35 / 35 | — |
| `test_arc_magnitude_migrated` | 43 / 43 | 43 / 43 | — |
| `test_arc_decompose_migrated` | 19 / 19 | **28 / 28** | — |

Both pre-existing reds are the **same two node ids every prior rung since
A12 has recorded**: `results/` is untracked in this checkout (`git show
HEAD:results/…` returns empty) and this engine's short sha is not in
`test_gr4`'s three-entry allowlist. Neither is this rung's to fix, and
neither was touched.

**Confinement, asserted not promised.** `seeds/arc_goals.json`,
`seeds/goal_residuals.json`, `seeds/arc_magnitude.json`,
`seeds/program_synthesis.json`, `domains/arc_executor.py`,
`tools/build_arc_executor_seed.py`, and `runners/dsl/src/*` are all
byte-identical to `HEAD` (`test_ar17_no_new_rust_and_ax_dispatch_UNTOUCHED`,
green). `seeds/arc_decompose.json` regenerates byte-identically from its
own, current emitter (`test_ar17_the_seed_regenerates_byte_identically` /
`test_mg4d_the_seed_regenerates_byte_identically`, both green). The one
adapter edit (`domains/arc_decompose_ingest.py`) passes the unmodified,
whole-file source audit `test_mg4d_no_python_decision_was_added`.

**Both trees verified clean.** This worktree's `git status --porcelain`
shows only the intended edits and the two symlinks; the canonical tree's
`git status --porcelain` was re-checked clean throughout, including
immediately after the two live subprocess re-measurements (§4.1's own gate,
and the one-off `arc6_structural_ceiling.py` probe run during this rung's
design investigation, §"Everything that broke" item 1). All three verdict
artifacts (`arc6_verdict_before/after/pricing.json`) and
`arc6_structural_ceiling.json` verified at their documented/measured
pristine shas after every touch.

---

## 6. EVERYTHING THAT BROKE

Recorded because the process is the result (A11-A16's own standing
practice).

1. **The A12.2/A15/A16 timeout hazard, reproduced a fourth time, on a
   FRESH node — the FIRST baseline attempt at `test_arc_executor_migrated`
   in this worktree, under the harness's own default 2-minute tool
   timeout.** The ~200s live row-verdict remeasurement was `SIGKILL`ed
   mid-flight, leaving `seeds/program_synthesis.json` patched in this
   worktree and, via the symlinked `results/`, the CANONICAL tree's
   `results/arc6_verdict_before.json` overwritten. Recovered exactly per
   A12.2/A15/A16's own playbook: the tracked seed via `git checkout --`;
   the untracked artifact from the killed run's own surviving
   `/tmp/arc6_remeasure_*` crash stash, **cross-checked against FIVE**
   independent stashes on disk (three from prior rungs, two from this
   one), **all five agreeing on the same pristine sha**
   (`ed90bf281bd8dc812a10a75cf85b8935843296c98d75290acc038a115f6aa7b0`) —
   the strongest corroboration any rung in this arc has recorded. Both
   trees verified clean before any further measurement. Every subsequent
   invocation of that suite passed an explicit, generous tool-level
   timeout (400000 ms), never only a shell-level one.
2. **The design-investigation probe run of `arc6_structural_ceiling.py`
   (§4.1) wrote through the symlinked `results/` into the canonical
   tree**, exactly as A15's own incident named — stashed first (per
   A12.2/A15's registered rule, "stash before running ANY measurement
   script directly"), restored and sha-verified after
   (`5af750cd4dcc7572a2164f5f360ff75b22e2bff411f8f094fd944b023ebfa322`,
   confirmed byte-identical before and after). No lasting damage; recorded
   because the near-miss is exactly the hazard this rung's own §4.1 gate
   later exercised under a formal test (with its own `try/finally`
   restore, additionally verified in the test body itself).
3. **`test_ar17_a_witness_fact_naming_a_DIFFERENT_tier_retires_NOTHING`
   (first draft) was WRONG, not the rule.** The first draft asserted that
   a `TierWitnessFact{tier_order:2.0, all_ids_covered:1.0}` should retire
   NOTHING — but a fact correctly NAMING tier 2 with `covered=1.0` SHOULD
   (and does) retire tier 2; the intended negative control was "does not
   retire tier 1," not "retires nothing at all." Caught immediately by the
   test's own failure message (`2.0` resolved when the assertion expected
   it not to), corrected before any other file was touched — the rule was
   never wrong; the first draft of its test was.

---

## 7. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do.

1. **The mechanism has never fired on a REAL (non-constructed) natural
   trigger.** §4.1 measured, honestly, that even a live re-measurement on
   this engine leaves tier 1 two ids short of full coverage. Whether a
   FUTURE re-measurement (on a later engine, or after the specific gap
   `18`/`310` closes for some other reason) would let `mg_tier_retire`
   fire naturally is unmeasured — the positive path is demonstrated only
   by construction, exactly A13/A15's own precedent for a rare trigger,
   named rather than hidden.
2. **Tiers 2-4 are further from resolvable, not closer, and this rung does
   not attempt them.** Tier 2 needs 10 new `Term` variants that do not
   exist; tier 3 additionally needs the cross-cutting string-order fix
   (unpriced fixture-migration cost, `PROGRAM_SYNTHESIS_ARC6_PREREG.md`
   §4) and the `Lit`-boundary fix; tier 4 needs a `Recurse` capability
   decision this project has repeatedly declined to make (`PROGRAM_
   SYNTHESIS_ARC6_STRUCTURAL_CEILING.md` §9). The mechanism this rung
   built is GENERIC over tier order — a future rung that builds any of
   that capability gets the retirement machinery for free — but building
   that capability is explicitly out of this rung's scope.
3. **Whether this actually grows A14's real-only impotent-state count is
   NOT measured here**, per the task's own instruction that a full
   impotence-campaign re-sweep need not be repeated unless cheap — and it
   is not cheap (A14's own sweep took ~6 minutes and included two REAL
   ~140s remeasurements). A17's own reasoning for why it COULD, if tier 1
   ever naturally resolves: `decomposition_tier` is a genuinely NEW kind
   value, distinct from `supply_blocker`/`source_claim`, so its retirement
   is exactly the shape A15 §6 named as necessary ("the newly-reachable
   pool member is [NOT] itself a `supply_blocker`/`source_claim`") — but
   this is a reasoned argument, not a measurement, and is named as such.
4. **The `source_claim` gap (§2, §2.1) is reported, not repaired.** Closing
   it would mean inventing a condition-and-lapse apparatus for
   `ArcSourceClaim` from nothing — a materially bigger, different build,
   exactly as A15 named for a second `ExecClass` and this rung
   independently reconfirms for a THIRD retirement mechanism.
5. **`budget` and `missing_dimension` remain genuinely open**, confirmed
   not merely inherited: neither has a bounded sub-claim analogous to
   tier 1's "these 8 named units, already built" — `budget` has no natural
   termination by definition, and `missing_dimension`'s 4 ids need a
   capability (a new Value dimension) this tree has never built for THIS
   population.
6. **The re-arm deadlock, the silent order-N fallback, `ag_ask`/
   `ax_dispatch` collapse-agreement, `gr_condition_lapse`'s closed
   vocabulary, and fold-up are untouched**, per the task's explicit scope
   boundary, and none was exercised by any scene in this rung in a way
   that would have required touching them.

---

## 8. FILES

| file | what |
|---|---|
| `domains/arc_decompose_ingest.py` | +92 lines: `probe_tier_witness_coverage`/`install_tier_witness_facts`, the `goal_residual_ingest.probe_facts`/`install_facts` shape applied to a decomposition child |
| `tools/build_arc_decompose_seed.py` | +91 lines: `_r_tier_retire`, docstring/description updates, version 1.0.0 → 1.1.0 |
| `seeds/arc_decompose.json` | **regenerated**, sha256 `7a1f82db9d1b564ceb8746e58b9bd14e19ef40973f898487ba3b8e9ebd917609`, gated byte-identical against its emitter |
| `tests/test_arc_decompose_migrated.py` | 1 pin inverted (rule-count set), 9 new gates |
| `PROGRAM_SYNTHESIS_ARC6_PREREG.md` | amendment A17 appended, registered before the build |
| `PROGRAM_SYNTHESIS_ARC6_RETIRE_BLOCKER.md` | this file |

**In this worktree's `git status`, not part of the change:**

- `data` and `results` appear as untracked **symlinks** into the canonical
  tree (gitignored). Must not be staged.
- `runners/dsl/python/substrate_rs/_native.abi3.so` does not appear as
  modified — copied verbatim from the canonical tree, sha unchanged.

**Nothing in the canonical tree changed.** `/home/matt/ozmadev/ocelot`'s own
`git status --porcelain` was re-verified clean after every live measurement
in this rung, including after the two incidents in §6 that were caught and
recovered.

---

## 9. REPRODUCE

```bash
# --- the worktree ---------------------------------------------------------
git worktree add --detach /home/matt/ocelot-arc6-retire-blocker 80f353e
cd /home/matt/ocelot-arc6-retire-blocker
git checkout -b arc6-retire-blocker
ln -s /home/matt/ozmadev/ocelot/data    data
ln -s /home/matt/ozmadev/ocelot/results results

# --- the engine -------------------------------------------------------------
cp /home/matt/ozmadev/ocelot/runners/dsl/python/substrate_rs/_native.abi3.so \
   runners/dsl/python/substrate_rs/_native.abi3.so
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
#   c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567

# --- the coherence probe ---------------------------------------------------
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs; s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst']!=a['tup'])"

# --- the seed is EMITTED, never hand-edited --------------------------------
python3 tools/build_arc_decompose_seed.py          # writes seeds/arc_decompose.json (v1.1.0)
python3 tools/build_arc_decompose_seed.py --check  # "up to date"

# --- the gate (includes ONE real, stash-protected, ~1s live re-measurement
#     of scripts/arc6_structural_ceiling.py -- always an explicit, generous
#     tool-level timeout, not only a shell-level one) ----------------------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 -m pytest tests/test_arc_decompose_migrated.py \
    --confcutdir=$PWD -q -p no:randomly -rf   # 28 passed

# --- the regression arms (test_arc_executor_migrated.py includes a REAL
#     ~200s live re-measurement -- ALWAYS an explicit, GENEROUS tool-level
#     timeout, never only a shell-level one) -------------------------------
for s in test_arc_goals_migrated test_goal_residual_migrated \
         test_arc6_valuelayer_migrated test_arc_magnitude_migrated; do
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
    PYTHONPATH=runners/dsl/python:. \
    python3 -m pytest tests/$s.py --confcutdir=$PWD -q -p no:randomly -rf
done
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 -m pytest tests/test_arc_executor_migrated.py \
    --confcutdir=$PWD -q -p no:randomly -rf   # 60 passed, 1 failed (pre-existing)
```

**`--confcutdir=$PWD` on every pytest invocation** — same reason as every
prior arc-6 rung: this worktree is not nested inside the canonical repo.

**Engine provenance.** Every number in this document was produced by
`c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`, resolving
from inside `/home/matt/ocelot-arc6-retire-blocker`.

**Contamination.** No MBPP test-split content was read by anything new this
rung added — `mg_tier_retire`/`probe_tier_witness_coverage`/
`install_tier_witness_facts` are pure graph/JSON arithmetic over artifacts
`arc6_structural_ceiling.py` (unmodified, pre-existing, already the
executor's own second `ExecClass` runner) already produces. Nothing new
entered a codebook, a route table, or a cue table.
