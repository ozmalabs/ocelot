# PER-AREA ASYNC SETTLEMENT — PRE-REGISTRATION (block 186000–186999)

**Committed ALONE, BEFORE any number is produced by the mechanism.**
Seed block **186000–186999**; `python3 scripts/seed_claim.py 186000 186999` → **CLEAN**
(no collision detected; 603 unresolved sink sites tree-wide, counted not discarded).

## 0. The thesis being tested

The architecture's root axiom, in the project creator's words:

> *"The rules need to be a library of nodes drawn from and executed within cortex.
> Fundamentally it is exactly the same as a settlement event in a bank account — you
> settle for this time, but there is always a residual; you never get to 0 unless you
> stop operating."*

The committed global fixpoint (`Substrate::run_rules_opts`, `runners/dsl/src/substrate.rs`;
`rewrite::run_rules_opts`, `runners/dsl/src/rewrite.rs:1861`) is **CLOSED-ACCOUNT
settlement**: it runs every dirty rule, everywhere, until the whole graph stops changing.
`residual == 0` is its termination condition, i.e. it assumes the world stopped feeding it.
It is also a **synchronous barrier** — a hidden global clock.

The proper form is **per-AREA settlement**: each area spends a BUDGET of settlement work
per tick on its own accumulated surprise and **CARRIES the remainder forward**; an area
with no dirty input does no work; surprise propagates between areas as events, not through
a barrier.

## 1. WHAT IS AND IS NOT BEING CLAIMED (scope, fixed in advance)

- **NOT** claimed: that the global fixpoint is replaced, deprecated, or made non-default.
  `run_rules` has ~821 Python call sites, 144 Rust references and 137 test files. It
  **remains the default AND the correctness oracle.**
- **Claimed**: per-area settlement is built **ALONGSIDE**, **DEFAULT OFF**, reachable only
  by an explicit new entrypoint that nothing in the committed tree calls.
- Any measured result is reported **with its exact workload scope**. If the reduction (C2)
  holds only on a subset of workloads, the claim is scoped to that subset **by name**.
- A failure to reproduce the fixpoint at all is a **legitimate rung outcome** and will be
  reported as a diagnosed NEGATIVE, not papered over.

## 2. THE MECHANISM (design fixed in advance)

Per-area settlement is a NEW engine entrypoint that reuses the committed inner machinery:

- **Area partition.** `RewriteRule.area: Sym` already exists (`rewrite.rs:321`) and is
  already parsed from every seed manifest's `"area"` key (`py.rs::parse_rule_json`).
  `area_scheduler::derive` already groups active rules by area in **first-rule-index
  order**. Nothing in either committed `run_rules` reads `rule.area` — the partition is
  currently inert scheduling metadata. This rung makes it EXECUTABLE, opt-in.
- **Per-area dirty set.** The engine's committed `rule_dirty: Vec<bool>` + the
  writer→reader propagation `dirty_by_writeset` already carry surprise from a rule that
  WROTE to every rule that READS what it wrote. **An area is DIRTY iff it holds ≥1 dirty
  active rule.** This is event-causal and per-area: it never reads a global barrier state.
- **A ROUND** = one pass over areas in canonical (first-rule-index) order. Each area spends
  at most `budget` progressing rewrite steps on its own dirty rules, then yields.
- **RESIDUAL** = the area's dirty rules that its budget did not reach this round. They are
  **CARRIED** — their dirty bits stay set, their inputs are NOT frozen, nothing about what
  the area will later see is altered. (Block 185000's Branch-B negative established that
  shedding a residual by FREEZING its reference FABRICATES surprise; carrying it inside the
  mechanism is the whole point.)
- **Termination**: rounds repeat until no area progressed in a whole round, or `max_rounds`.
- **NO new Term enum variant.** `runners/dsl/src/term.rs` will be untouched. The build is a
  new engine method + PyO3 entrypoint + (if needed) a mechanical rule-relabel op.
- **NO agent decisions in Python.** Budget/rounds are call parameters and graph data; the
  Python side is mechanical I/O and measurement only.

## 3. PRE-REGISTERED CRITERIA AND THRESHOLDS

Every threshold below is fixed now. A breached threshold is reported as breached, decomposed,
and never re-negotiated after the fact.

### C1 — DEFAULT-OFF BYTE-IDENTITY (the PRIMARY gate; a failure here rejects the rung)

| id | criterion | threshold |
|---|---|---|
| C1a | vision oracle `bash scripts/rung7_vision_bench.sh` | **0 failed**, and **BEFORE == AFTER** on (passed, skipped, failed). Both counts reported. |
| C1b | broad cross-domain regression, run as much of `tests/` as is tractable; at minimum the vision suite + the pipeline/seizure/psychosis/cognitive-task regression | **the SET of failing node ids is IDENTICAL before and after** (a LIST, never a count — per the CLAUDE.md baseline retraction). Exactly which files were run is reported. |
| C1c | engine byte-identity of the DEFAULT path: with settlement never invoked, `run_rules()`/`tick()` produce an **identical full graph dump** (every node id/type/attr and every edge, floats at `repr()` precision) vs the BASE engine built from unmodified sources | **byte-identical on ≥ 3 distinct workloads** (vision carve, cognitive-task scheduler, one non-vision domain) |
| C1d | `runners/dsl/src/term.rs` unchanged | `git diff --stat` shows no change to `term.rs` |

### C2 — THE REDUCTION (the correctness bridge)

| id | criterion | threshold |
|---|---|---|
| C2a | `run_rules_settle(budget = UNBOUNDED)` final graph state vs `run_rules()` final graph state | **byte-identical full graph dump** on the vision carve workload at **≥ 2 grid sizes**, and on the cognitive-task scheduler workload |
| C2b | NON-VACUITY: the settlement path must genuinely differ from "call the same loop" | settlement takes **> 0 steps** and **≥ 2 rounds** on ≥1 workload, AND the measured area partition has **≥ 2 areas** on ≥1 workload |
| C2c | SCOPE | the exact list of workloads on which the reduction was tested is reported, **with the pass/fail of each**. A partial hold is scoped by name, not generalised. |

If C2a fails everywhere: the mechanism is reported as WRONG, with the diagnosed reason.

### C3 — RESIDUAL IS CARRIED, NOT LOST

| id | criterion | threshold |
|---|---|---|
| C3a | endpoint invariance under a FINITE budget: for budget `b ∈ {1, 2, 4, 8}`, running rounds to completion reaches the SAME final graph state as `b = ∞` and as global `run_rules` | **byte-identical endpoint for every `b` tested**, on the C2-scope workloads |
| C3b | the budget genuinely DEFERRED work (non-vacuity of C3a) | for at least one finite `b`, **rounds(b) > rounds(∞)** and the measured carried-residual is **> 0 in ≥ 1 round** |
| C3c | convergence curve | total carried residual vs round is reported for every `b`; it reaches **exactly 0** at the terminal round |
| C3d | **"you never get to 0 unless you stop operating"** — with input CONTINUING to flow (fresh sensory material submitted every round) | residual **> 0 in ≥ 95% of the flowing rounds** (≥ 20 rounds measured); after input STOPS, residual reaches **exactly 0 within 50 rounds** |

### C4 — THE WIN: compute ∝ surprise at the AREA grain

| id | criterion | threshold |
|---|---|---|
| C4a | a CLEAN area does ZERO work | measured rule-attempt count inside a clean area is **exactly 0** |
| C4b | per-round cost tracks DIRTY AREAS, not total areas: at fixed total areas `A ≥ 16`, sweep dirty-area count `d` | affine fit `t = c₀ + c₁·d` with **R² ≥ 0.90**, and **cost(d=1) / cost(d=A) ≤ 0.30** |
| C4c | **HONEST ALL-DIRTY CASE (the no-free-lunch falsifier)**: when every area is dirty, per-round settle cost vs the global fixpoint's per-pass cost | ratio reported whatever it is; **pre-registered expectation ∈ [0.80, 1.40]** (settlement should cost slightly MORE when nothing can be skipped). A ratio outside this band is reported as a breach. |
| C4d | the VISION path specifically (carve / motion / salience settle ops — the named bottleneck) | the per-area cost split is measured and reported. If the committed vision seeds carry too FEW distinct areas to show an area-grain win, **that is reported as the honest finding**, not worked around by changing committed seed data. |

### F — THE FALSIFIER: DROPPING the residual must DIVERGE

Mirrors the 185000 Branch-B negative. A `drop_residual` variant settles to budget and then
**DISCARDS** the remainder (clears the carried dirty bits instead of leaving them set).

| id | criterion | threshold |
|---|---|---|
| F1 | at a finite budget on a workload where the budget actually bites, the DROP run **diverges** from the CARRIED run | final graph state **differs** (different full dump / fingerprint) on **≥ 1 workload**, with the divergence magnitude reported |
| F2 | if DROP ≡ CARRY on every workload tested | then the residual accounting is declared **NOT REAL** and the rung reports that as its headline NEGATIVE |

## 4. GATE, ORACLE, PROVENANCE, BUILD SAFETY (fixed in advance)

- **Gate**: `tests/test_per_area_settlement_migrated.py`, self-contained, pinning:
  default-OFF byte-identity; the REDUCTION (unbounded ≡ global fixpoint); residual-carried
  convergence to an identical endpoint; the DROP-variant falsifier; cost-tracks-dirty-areas.
  Gates assert invariants that hold in BOTH the worktree AND `main` — never a
  worktree-specific value, never a stricter exact form re-derived in Python over a
  mechanism that is tolerant by design, never a global-barrier snapshot (async ordering
  breaks that gate shape).
- **Oracle**: `bash scripts/rung7_vision_bench.sh`, BEFORE and AFTER, both reported.
  (`main` reports 224 passed / 0 failed with `data/` present; this worktree has no `data/`
  symlink so the documented worktree-without-data condition is 214 passed / 10 skipped /
  0 failed. Whichever applies is named explicitly.)
- **Provenance §10**: `domains.engine_provenance.provenance_stamp` →
  `source_match ∈ ("own", "shared")`, reported.
- **Build safety**: `.so` built in **this worktree only**. Canonical
  `/home/matt/ozma/internal/research/experiments/gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so`
  md5 recorded BEFORE (**`8f84f55a60046f0134a0591dd10edfa6`**, mtime Jul 25 09:19) and
  re-verified AFTER. If Rust changes, the report says **LOUDLY**: *"CANONICAL NEEDS REBUILD
  ON MERGE."*
- **Curves** saved under `results/per_area_settlement/`.

## 5. WHAT WOULD MAKE THIS RUNG A FAILURE

Stated in advance so it cannot be redefined later:

1. Any change to DEFAULT behaviour (C1 breach) — rejects the rung outright.
2. Per-area-unbounded not reproducing the global fixpoint anywhere (C2a total failure) —
   the mechanism is wrong; reported as such.
3. DROP ≡ CARRY (F2) — the residual accounting is not real; reported as the headline.
4. Cost not tracking dirty areas (C4b breach) — the "compute ∝ surprise at area grain"
   claim is withdrawn and the honest cost model reported instead.

## 6. HONEST RESIDUALS EXPECTED IN ADVANCE

- Rounds are still driven by a host loop; per-area settlement here removes the **rule-level**
  global barrier, not necessarily every barrier. **Whatever remains synchronous will be named
  explicitly in the results**, including whether cross-area surprise propagation is genuinely
  event-causal (via `dirty_by_writeset`) or still mediated by a round boundary.
- `graph_rules::rule_from_node` drops `area` to the default Sym, so graph-resident `Rule`
  NODES all land in one area. That limitation is inherited, will be stated, and is not
  fixed by this rung.
- The committed vision seeds put every retinal rule in a single `"retina"` area. If that
  makes the vision-path area-grain win small or absent, it is reported as measured.
