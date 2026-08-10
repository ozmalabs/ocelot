# PER-AREA ASYNC SETTLEMENT — a cortex tick is a SETTLEMENT EVENT that CARRIES a residual (results)

**Block 186000.** Prereg `SETTLEMENT_PER_AREA_PREREG.md`, committed ALONE
(`5d972c8cd36e98617875c34e958d086e95833cad`) BEFORE any number from the mechanism.
`source_match = "own"`. **This rung BUILDS Rust** — the canonical `.so`
(`…/gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so`, md5
`8f84f55a60046f0134a0591dd10edfa6`, mtime Jul 25 09:19) is **UNCHANGED**; the build
happened only in this worktree. **CANONICAL NEEDS REBUILD ON MERGE.**
Seed block **186000–186999**; `python3 scripts/seed_claim.py 186000 186999` → **CLEAN**
(603 unresolved sink sites tree-wide, counted not discarded).

## Headline

> *"You settle for this time, but there is always a residual; you never get to 0 unless
> you stop operating."*

The committed global `run_rules` fixpoint is **CLOSED-ACCOUNT** settlement: `residual == 0`
IS its termination condition, and its rule pass is a synchronous barrier. This rung builds
the **OPEN-ACCOUNT** form ALONGSIDE it, **DEFAULT OFF**, and proves the bridge:

**Per-area settlement with an unbounded budget reproduces the global fixpoint's final graph
state BYTE-IDENTICALLY on all four real workloads tested — including with no barrier
anywhere — and under a finite budget an area settles part of its work, CARRIES the rest,
and converges to the SAME endpoint. DROPPING the carried residual instead DIVERGES. An area
with no dirty input does EXACTLY ZERO work.**

And the honest other half: **on the shipped vision path the area grain buys nothing**, for a
reason this rung names precisely (below, C4d) — and one pre-registered threshold is
**BREACHED** (C4c: 1.92× vs the predicted ≤1.40 when every area is dirty).

## What already existed vs what this rung built

**Already existed (and needed only wiring, not inventing):**

- `RewriteRule.area: Sym`, `order`, `latency_class` (`rewrite.rs:321-325`), parsed from every
  seed manifest's `"area"` key with manifest-level inheritance (`py.rs::parse_rule_json`).
- `area_scheduler::derive` — grouping by area in first-rule-index order, writer→reader
  dependencies, Tarjan SCCs. Its own doc says plainly: *"It does not alter rule execution."*
- `seeds/cognitive_scheduler.json` — 10 rules of genuine async POLICY: per-area
  `logical_tick` / `input_epoch`, `ct_ready_when_dependencies_settle`, stale re-arm,
  supersession, effort∝salience, worker backpressure, graph-visible shedding, and
  `ct_broadcast_residual_once_per_destination_epoch` (epoch-deduped residual projection over
  `projects_to`).
- `cognitive_cycle.rs` `AreaSerial` / `AreaParallel` plans, and per-area `CognitiveTask`
  execution with a deterministic `(logical_time, area, node)` fold.
- The per-rule dirty index `rule_dirty` + `dirty_by_writeset` (writer's over-approximated
  write-set ∩ reader's read-set) — **already an event-causal surprise-propagation mechanism.**

**What did NOT exist:** *nothing in either `run_rules` implementation reads `rule.area`.* The
area partition was inert scheduling metadata; the scheduler seed's policy governs
CognitiveTASKS, never the rule fixpoint. Settlement at the RULE grain, a budget, and a
carried residual did not exist.

**Built here (Rust, additive, default off):**

- `Substrate::attempt_one_rule` — the body of `run_rules_opts`'s inner loop **EXTRACTED
  VERBATIM** so settlement reuses committed semantics instead of duplicating and drifting.
  Verified mechanically: 162 lines, **zero** differences from the committed body once the
  caller's two accumulators (`steps += 1; any_progress = true;`) are removed.
- `Substrate::area_groups` — the O(rules) canonical partition (areas by first active rule
  index; rules within an area ascending), recomputed each round, never hash order.
- `Substrate::run_rules_settle(budget_per_area, max_rounds, drop_residual, snapshot_round)`
  + `SettleReport` / `SettleRound` / `AreaSettleRow` ledger.
- `Substrate::set_rule_area` — mechanical relabel (scheduling metadata only), so a
  measurement can split an existing seed's rules across areas without editing seed data.
- PyO3: `run_rules_settle`, `set_rule_area`, `rule_areas`.
- **NO new Term enum variant** — `term.rs` untouched (`git diff --stat` shows no change).

## The mechanism, exactly

A **ROUND** is one pass over the areas in canonical order. Each area settles up to `budget`
PROGRESSING steps of its own dirty set, then yields. `budget == 0` is unbounded (settle this
round's whole dirty set). Rounds repeat until no area progresses.

**The residual is CARRIED, never frozen.** Work the budget did not reach keeps its dirty bit;
**nothing about the graph that rule will later read is altered.** This is the direct lesson of
block 185000's Branch-B negative (a deferred retina cell departing from a FROZEN adapted floor
MANUFACTURED spurious onsets, carve precision 0.978→0.0): the deferral must live in the
SCHEDULE, never in the state.

**The one remaining choice about synchrony is explicit, and both arms are measured:**

| `snapshot_round` | what an area reads | barrier? |
|---|---|---|
| `false` (**default**) | its OWN dirty set at the moment ITS turn comes — surprise a neighbour wrote earlier this round is visible NOW | **none** |
| `true` | every area's dirty set snapshotted at round start, so a round attempts exactly the rule multiset one committed global pass would, permuted into area-major order | round-start |

## C1 — DEFAULT-OFF BYTE-IDENTITY (the primary gate) — **PASS**

| id | measured | pass |
|---|---|---|
| C1a | vision oracle `rung7_vision_bench.sh`: **BEFORE 214 passed / 10 skipped / 0 failed**, **AFTER 214 / 10 / 0** — BEFORE == AFTER | ✅ |
| C1b | cross-domain regression (`scripts/per_area_settlement_regression.sh`, 34 named files): **BEFORE 23 failed / 277 passed / 5 skipped**, **AFTER 23 / 277 / 5**, and the **SET of 23 failing node ids is IDENTICAL** (listed below) | ✅ |
| C1c | DEFAULT path, base engine `7572a616…` vs settlement engine `fc503e78…`, full float-exact `graph_to_dict` dump on 4 workloads: `vision_carve` `91129b4a9c699c1b`, `scheduler` `731d8a5eab6aa42c`, `quiet_areas` `731d8a5eab6aa42c`, `conversation` `54e4b9b9553e9951` — **all four identical** | ✅ |
| C1d | `runners/dsl/src/term.rs` unchanged | ✅ |

`rung7` runs in the documented **worktree-without-data** condition (no `data/` symlink); `main`
reports 224/0 with data present.

**The 23 pre-existing reds, identical on both sides** (they are the worktree's
missing-acquired-state condition, not this rung): `test_cortices_tick.py::`{`test_crow_report_byte_identical_via_tick`,
`test_ticked_reading_matches_run_reading_flow_report`, `test_nested_lion_mouse_reciprocity_via_tick`};
`test_composer_driver_migrated.py::test_question_driver_parity`; 5 in
`test_gap_awareness_migrated.py`; 5 in `test_elaboration_migrated.py`; 9 in
`test_topic_route_selfheal_migrated.py`.

**The non-determinism exclusion, named and proved.** Byte-identity dumps exclude EXACTLY two
attributes: `AreaLoad.service_wall_micros` and `TaskResult.wall_micros`. These are wall-clock
counters the runtime writes into the graph, so two runs of the SAME binary on the SAME input
differ in them. Measured, not assumed: two consecutive committed-loop runs of every workload
differ in those two keys **and in nothing else** — node ids, `next_id` and the entire edge set
reproduce exactly. Gated by
`test_the_only_nondeterminism_is_the_named_wall_clock`, which FAILS if any other key drifts.

## C2 — THE REDUCTION (the correctness bridge) — **PASS, with a named scope boundary**

`run_rules_settle(budget = UNBOUNDED)` vs `run_rules()`, full float-exact graph dump:

| workload | areas (from committed seeds) | settle steps | rounds/call | ASYNC identical | BARRIER identical |
|---|---|---|---|---|---|
| `vision_carve` (real 2-D retina on the GRAPH, 20×15, carve+motion+salience) | 2 — `scheduler`, `retina` | 45 | 2,2,…,1 | ✅ | ✅ |
| `scheduler` (3 CognitiveAreas, tasks/residual/projection/load) | 1 — `scheduler` | 4 | 2,2,1,1 | ✅ | ✅ |
| `quiet_areas` (same + `information_commitment` + `spatial_belief_core`) | 3 — `scheduler`, `executive`, `spatial` | 4 | 2,2,1,1 | ✅ | ✅ |
| `conversation` (booted `WorldAdapter`, 4 utterances — NON-vision) | 1 — `global` | 24 | 3,3,3,3 | ✅ | ✅ |

**C2b non-vacuity ✅** — >0 steps, ≥2 rounds, and ≥2 areas on two workloads.
**Crucially the FULLY ASYNC arm passes too**: on these workloads the reduction does not
depend on the barrier at all.

**C2c/C2d — THE SCOPE, stated exactly.** In every committed seed set an area's rules are
**CONTIGUOUS** in the rule list, because a seed is loaded as a unit; so area-major order is the
IDENTITY permutation of the committed pass order. A deliberate probe with **INTERLEAVED** areas
(`ilv_x`, `ilv_y` alternating, with node-minting effects) **BREAKS the reduction in both arms**
(global `76f9725501d2082d` vs settle `abc3613f146d0f84`, 8 steps either way).

**So the honest claim is:** *per-area settlement reproduces the global fixpoint exactly
whenever the area partition respects rule-list order — which is the case for every committed
seed set — and NOT in general.* The divergence is node-MINT ORDER (allocation-ordered NodeIDs),
i.e. the rule system is not confluent under re-ordering. That is a property of the committed
rule system, not of settlement, and it is now measured rather than assumed.

## C3 — RESIDUAL IS CARRIED, NOT LOST — **PASS**

Finite budget `b`, run to completion, compared against the global fixpoint's dump:

| workload | b=1 | b=2 | b=4 | b=8 | unbounded |
|---|---|---|---|---|---|
| `vision_carve` | ✅ 44 rounds, **318 carried** | ✅ 30, **118** | ✅ 29, 0 | ✅ 29, 0 | 29 rounds, 0 carried |
| `scheduler` | ✅ 8, **19** | ✅ 7, **4** | ✅ 6, 0 | ✅ 6, 0 | 6, 0 |
| `quiet_areas` | ✅ 8, **19** | ✅ 7, **4** | ✅ 6, 0 | ✅ 6, 0 | 6, 0 |
| `conversation` | ✅ 28, **184** | ✅ 17, **65** | ✅ 12, **11** | ✅ 12, 0 | 12, 0 |

(✅ = **byte-identical endpoint**; second number = total work CARRIED across all rounds.)

**C3a ✅** every budget lands on the identical endpoint. **C3b ✅** the budget genuinely
deferred: carried > 0 and rounds(b=1) > rounds(∞) on every workload (44>29, 8>6, 28>12).
**C3c ✅** terminal residual is exactly **0** in every run. At b≥4 (b≥8 for `conversation`)
nothing is carried — correct, the budget stops biting.

**C3d — "you never get to 0 unless you stop operating" — PASS.** ONE settlement round per world
tick, budget 2, fresh CognitiveTasks arriving every tick:

```
input FLOWING (30 rounds):  9 8 5 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4
input STOPPED:              0 0 0 0 ...
```

Residual **> 0 in 100% of the flowing rounds** (threshold ≥95% ✅), settling to a **steady-state
residual of 4** — the account never closes while the world keeps feeding it. It reaches exactly
**0 in 1 round** after the input stops (threshold ≤50 ✅).

## F — THE FALSIFIER: DROPPING the residual DIVERGES — **PASS**

`drop_residual = True` settles to budget then DISCARDS the remainder (clears the bits instead
of leaving them set). Compared against the CARRIED run at the same budget:

| workload | b=1 | b=2 | b=4 | b=8 |
|---|---|---|---|---|
| `vision_carve` | **DIVERGES** (44 vs 45 steps; dump 1 102 638 vs 1 117 328 chars) | **DIVERGES** | ≡ | ≡ |
| `scheduler` | **DIVERGES** (`44d7e249…` vs `731d8a5e…`) | **DIVERGES** | ≡ | ≡ |
| `quiet_areas` | **DIVERGES** | **DIVERGES** | ≡ | ≡ |
| `conversation` | **DIVERGES** (**8 vs 24 steps — two thirds of the work LOST**) | **DIVERGES** (12 vs 24) | **DIVERGES** (20 vs 24) | ≡ |

The carried arm equals the global fixpoint at EVERY budget; the drop arm does not, at every
budget where the budget actually bites. Where it does not bite, drop ≡ carry — correct, because
nothing was dropped. **The residual accounting is real.**

## C4 — COST ∝ SURPRISE AT THE AREA GRAIN — **PASS on C4a/C4b, BREACHED on C4c, honest NEGATIVE on C4d**

**C4a — a QUIET area does EXACTLY ZERO work. ✅** 32 areas, settled, then perturbed in `d` of
them (settling first is load-bearing: a freshly installed rule is dirty by construction, so
measuring straight after `add_rule` would time "try every area once" and say nothing about
surprise — the same adapt-then-perturb discipline as 185000):

| dirty areas `d` | 0 | 1 | 2 | 4 | 8 | 16 | 32 |
|---|---|---|---|---|---|---|---|
| µs / settle (median of 9) | **12.8** | 55.8 | 64.7 | 100.9 | 161.6 | 291.6 | 543.9 |
| **rule attempts** | **0** | 6 | 12 | 24 | 48 | 96 | 192 |
| areas that did any work | **0** | 1 | 2 | 4 | 8 | 16 | 32 |

Rule attempts are **exactly 6·d** — a quiet area is skipped by one `is_empty()` on its own
rule-index list and never touches the graph.

**C4b ✅** affine fit `t = 30.8 µs + 16.1 µs·d`, **R² = 0.9978** (≥0.90), and
**cost(d=1)/cost(d=32) = 0.1026** (≤0.30).

**C4c — ⚠️ PRE-REGISTERED THRESHOLD BREACHED, reported not excused.** All 32 areas dirty:
global `285.5 µs` vs settle `548.9 µs` → **ratio 1.92**, outside the pre-registered
**[0.80, 1.40]**. The direction was predicted (settlement should cost MORE when nothing can be
skipped — there is no free lunch) but the **magnitude was under-predicted by ~40%**. Cause,
named: settlement pays an O(rules) `area_groups()` rebuild plus one `Vec` allocation per dirty
area **per round**, where the committed loop builds one `to_try` vector per pass. On a
32-area × 6-round run that is 192 small vector allocations against 6 large ones. It is a
constant-factor artefact of this implementation, not of the idea — but it is what was measured
and the threshold stands breached.

**C4d — THE VISION PATH: an honest NEGATIVE, with the reason named.** The rung's premise was
that the carve/motion/salience settle ops, being per-AREA, are the next lever. Measured
(20×15 graph-path retina, both arms):

| arm | areas | areas doing work on a PLAIN photon tick | median photon tick |
|---|---|---|---|
| as shipped | `scheduler`, `retina` | **both** (dirty 10 / 6) | 2.87 ms |
| relabelled via `set_rule_area` into 6 | `scheduler`, `retina`, `v1_onset`, `mt_carve`, `mt_motion`, `lip_salience` | **all six** (dirty 10/2/1/1/1/1) | 2.87 ms |

**No win, either way.** Two independent reasons, both real:

1. **The committed vision seeds put every retinal rule in ONE `retina` area**, so out of the box
   there is no area partition inside vision to exploit.
2. **More fundamentally: even split, every settle-op area is woken on every photon tick.** The
   cross-area waking mechanism is `dirty_by_writeset`, which intersects the writer's
   **over-approximated** write-set with the reader's read-set. The onset rule writes the very
   `RetinalOnsetEvent` / column material the carve, motion and salience rules read, so all
   three are marked dirty every tick — even when their settle TASK does not exist and they
   cannot possibly fire. They cost one cheap failing match each, not zero.

So the per-area lever is real (C4a/C4b prove it at the mechanism grain) but **vision cannot
currently pull it**, and the blocker is **the precision of the dirty propagation, not the area
partition.** That is the measured next lever, and it is a different rung.

## Provenance & discipline

- **Oracle** `bash scripts/rung7_vision_bench.sh`: **BEFORE 214 passed / 10 skipped / 0 failed**
  and **AFTER 214 / 10 / 0** — BEFORE == AFTER. (worktree-without-data condition; `main` = 224/0.)
- **Gate** `tests/test_per_area_settlement_migrated.py`: **17 passed**.
- **Cross-domain regression** `scripts/per_area_settlement_regression.sh` (34 named files, never
  a `-k` substring selector): BEFORE == AFTER, **identical failing node-id LIST**.
- **Rust built in this worktree ONLY.** Canonical `.so` md5 `8f84f55a60046f0134a0591dd10edfa6`
  **UNCHANGED**, verified before and after. Worktree engine md5
  `fc503e787f38d20788a1bab6c9fd81a9` (reproducible: rebuilt twice to the same md5), engine short
  `c8118425299a`. **CANONICAL NEEDS REBUILD ON MERGE.**
- `source_match = "own"`, `stale_rust = []`.
- **NO new Term enum variant** — `term.rs` untouched.
- Seed block **186000–186999**, `check_claim` CLEAN.
- Raw + curves: `results/per_area_settlement/per_area_settlement.json`,
  `results/per_area_settlement/per_area_settlement.png`,
  `results/per_area_settlement/default_path_dump{,_BASE_ENGINE}.json`.

## Honest residuals — especially WHAT IS STILL SYNCHRONOUS

1. **The ROUND is still a host-driven loop.** Per-area settlement removes the global barrier
   *over rules* — an area reads its own dirty set on its own clock and can see a neighbour's
   write within the same round — but the rounds themselves are still iterated by one caller in
   one thread, and areas take turns rather than running concurrently. **This is one graph
   writer, deliberately** (the async-cognitive-core rung established that general non-confluent
   rule mutation is not parallelised). So: **the rule-level barrier is gone; the round boundary
   and the single-writer serialisation are not.**
2. **Cross-area surprise propagation IS real and event-causal** — it is the committed
   `dirty_by_writeset` (writer's write-set ∩ reader's read-set), computed at the moment the
   writer fires. It is NOT mediated by a barrier and NOT a whole-graph scan. But it is an
   **over-approximation**, and C4d shows that over-approximation is exactly what defeats the
   area grain on the vision path.
3. **Areas do not yet have their OWN clocks in the engine's sense.** `CognitiveArea.logical_tick`
   / `input_epoch` are seeded node attrs that `cognitive_scheduler.json`'s rules advance from
   TASK completion; `run_rules_settle` partitions by `RewriteRule.area` and does not read or
   write those attrs. Joining the two — a per-area budget that is a function of the area's own
   `effort`/`salience` graph state rather than a call parameter — is the obvious next step and
   is NOT done here. The budget is a call argument, which is host policy.
4. **`graph_rules::rule_from_node` drops `area` to the default Sym** (`graph_rules.rs:352-408`
   reads only id/match/where/effect/batch/match_type), so every graph-resident `Rule` NODE lands
   in one area. Inherited limitation, not fixed here.
5. **The reduction is scoped to order-respecting partitions** (C2d). Interleaved areas break it
   through node-mint order. Any future rung that loads seeds in a way that interleaves areas
   loses the byte-identity bridge and must re-establish it.
6. **C4c is breached at 1.92×.** Settlement is ~2× the committed loop when every area is dirty.
   The named cause (per-round `area_groups()` + per-area vector allocation) is a fixable
   constant factor, but nothing here fixes it.
7. **The 185000 lesson was applied, not re-learned**: the residual is carried IN the mechanism
   (dirty bits stay set, no reference is frozen), and the DROP falsifier confirms the accounting
   is real rather than decorative. But note the shapes differ: 185000's Branch B shed a
   RECEPTOR's residual by freezing its adapted floor, which fabricated surprise; here dropping
   loses work outright. Both diverge; only the former manufactures false structure.

## Proposed VISION_PROTOCOL ledger row

| **186000–186999 (`check_claim(186000,186999)` CLEAN; SEPARATE prereg commit `5d972c8cd3` BEFORE build)** | **PER-AREA ASYNC SETTLEMENT — a cortex tick is a SETTLEMENT EVENT that CARRIES a residual. Built ALONGSIDE the global fixpoint, DEFAULT OFF; the fixpoint stays the default AND the oracle.** The committed `run_rules` is CLOSED-ACCOUNT settlement (`residual==0` IS its termination condition) and a synchronous barrier; `Substrate::run_rules_settle(budget, rounds, drop, snapshot)` is the OPEN-ACCOUNT form — each area settles as much of its own dirty set as its BUDGET affords per round, then CARRIES the rest. `RewriteRule.area` existed since the async-core rung but **nothing in either `run_rules` ever read it**; this makes the partition EXECUTABLE. **C1 DEFAULT-OFF BYTE-IDENTITY (primary gate) — PASS:** oracle `rung7` BEFORE==AFTER **214/10/0** (worktree-without-data); 34-file cross-domain regression BEFORE==AFTER with an **IDENTICAL failing node-id LIST** (23/277/5 both sides); and the DEFAULT path dumps byte-identically (full float-exact `graph_to_dict`) on 4 workloads between base engine `7572a616…` and settlement engine `fc503e78…`. The inner loop is **EXTRACTED VERBATIM** into `attempt_one_rule` — 162 lines, mechanically verified zero-diff. **C2 THE REDUCTION — PASS:** settle(UNBOUNDED) ≡ global fixpoint byte-for-byte on `vision_carve` (2 areas scheduler+retina, real 2-D graph retina with carve/motion/salience), `scheduler`, `quiet_areas` (3 areas incl. `executive`/`spatial` from committed seeds), `conversation` (non-vision) — **and it passes in the FULLY ASYNC arm with no barrier anywhere**, not only the round-snapshot arm. **SCOPE, NAMED:** in every committed seed set an area's rules are CONTIGUOUS (a seed loads as a unit) so area-major order is the identity permutation; a deliberate INTERLEAVED-area probe **BREAKS the reduction in both arms** — the committed rule system is not confluent under re-ordering (node-MINT order), so the claim is scoped to order-respecting partitions and is not general. **C3 RESIDUAL CARRIED — PASS:** budgets 1/2/4/8 all reach the BYTE-IDENTICAL endpoint; b=1 carries 318/19/19/184 units of work and needs 44/8/8/28 rounds vs the unbounded 29/6/6/12; terminal residual exactly 0 everywhere. **"You never get to 0 unless you stop operating" — MEASURED:** one round per world tick under budget 2 with tasks still arriving → residual >0 in **100%** of 30 flowing rounds at a steady state of 4, and **0 in 1 round** once the input stops. **FALSIFIER — HELD:** the DROP-the-residual arm (shed instead of carry) **DIVERGES** from the carried arm at every budget that bites (conversation b=1: **8 steps vs 24 — two thirds of the work LOST**), while the carried arm equals the fixpoint at every budget. **C4 COST ∝ SURPRISE AT THE AREA GRAIN — PASS at the mechanism grain:** 32 areas, settled then perturbed in d of them → rule attempts exactly **6·d** and **0 at d=0** (a quiet area is skipped by one `is_empty()`, 12.8 µs); affine R²=0.9978, cost(d=1)/cost(d=32)=**0.103**. **⚠️ ONE PREREG THRESHOLD BREACHED:** all-dirty settle/global = **1.92×** vs the pre-registered ≤1.40 — direction right (no free lunch), magnitude under-predicted; cause named exactly (per-round `area_groups()` + per-area vector allocation vs one `to_try` per pass). **⚠️ HONEST NEGATIVE ON THE NAMED TARGET:** on the vision path the area grain buys **nothing** — as shipped every retinal rule is in ONE `retina` area, and even relabelled into 6 areas (`v1_onset`/`mt_carve`/`mt_motion`/`lip_salience` via the new `set_rule_area`) **all six are dirty on every photon tick**, because `dirty_by_writeset` is an OVER-APPROXIMATION and the onset rule writes exactly the material carve/motion/salience read. **The blocker is the PRECISION of the dirty propagation, not the area partition** — that is the measured next lever. **CANONICAL NEEDS REBUILD ON MERGE** (Rust changed; canonical md5 `8f84f55a60…` UNCHANGED during the rung, worktree engine `fc503e787f…`, reproducible). **NO new Term enum** (`term.rs` untouched — engine method + PyO3 only); gate `test_per_area_settlement_migrated` **17/17**; §10 `source_match=own`. **HONEST RESIDUALS:** (1) the rule-level barrier is GONE but the ROUND boundary and single-writer serialisation are not — areas take turns, they do not run concurrently; (2) cross-area surprise propagation is genuinely event-causal (`dirty_by_writeset` at fire time, no barrier, no whole-graph scan) but over-approximate, which is what defeats C4d; (3) the budget is still a CALL ARGUMENT — joining it to the area's own `effort`/`salience` graph state (which `cognitive_scheduler.json` already computes for TASKS) is the un-done step that would make the schedule fully graph-native; (4) `graph_rules::rule_from_node` drops `area`, so graph-resident Rule NODES all land in one area. Curves: `results/per_area_settlement/per_area_settlement.png`, raw `…/per_area_settlement.json`; `SETTLEMENT_PER_AREA_RESULTS.md`. `SEED CLAIM 186000-186999 CLEAN`. |
