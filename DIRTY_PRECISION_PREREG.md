# DIRTY-PROPAGATION PRECISION — pre-registration (block 187000)

**Committed ALONE, BEFORE any number from the mechanism.**
Seed block **187000–187999**. `python3 scripts/seed_claim.py 187000 187999` →
`SEED CLAIM 187000-187999: CLEAN -- no collision DETECTED.` (verbatim below, §9).
Base: `main` @ `4d1b7d87c8ab7e1c349ddb086eda5029749fd1c8` (the 186000 ledger commit).

---

## 0. Why this rung exists — the MEASURED blocker it inherits

Block 186000 built per-area async settlement (`run_rules_settle`, default OFF) and
returned an **HONEST NEGATIVE on the real vision path**: relabelling the retina into six
areas leaves **all six dirty on every photon tick — 2.87 ms either way**. Its diagnosis
named `dirty_by_writeset` (`runners/dsl/src/substrate.rs:648`) as an over-approximation.

**This rung does NOT assume that diagnosis is the whole story.** Step 1 is a MEASUREMENT
that attributes every dirty-mark on the real photon/Doom path to the code path that made
it. Only then does anything get built.

---

## 1. STEP 1 — THE DIAGNOSIS (measured first, no build)

The engine has **THREE** paths that set `rule_dirty`, not one:

| # | path | site | granularity |
|---|---|---|---|
| P1 | `dirty_by_writeset(fired)` | `substrate.rs:648` | writer's STATIC write-set ∩ reader's read-set, at `RuleKey = Attr(k)/Type(t)/Edge(e)` (per-KEY, not per-instance) |
| P2 | `mark_edge_type_dirty(et)` | `substrate.rs:609` | per EDGE TYPE |
| P3 | `mark_node_mutation()` | `substrate.rs:625` | **BLANKET — every rule with a where-clause, unconditionally** |

P3 is reached from `add_node`, `remove_node`, `set_attr`, `set_type` — i.e. **every
external (host/adapter) write AND every `substrate.set_attr` inside the Rust runtime**,
including `run_cognitive_tasks`' task-status/output writes (`cognitive_tasks.rs:1330,
1415-1429, 1515-1523, 1706-1736`) and `GraphEye.submit_photons_2d`'s per-cell
`set_attr` + `add_node` + `prune_settled_tasks`' `remove_node`.

**Pre-registered instrument.** A build-flagged counter set (`dirty_marks` telemetry,
default OFF, no effect on graph state) that records, per `run_rules` / per tick:

- `marks_P1` / `marks_P2` / `marks_P3` — dirty-marks set by each path (a mark = a
  `rule_dirty[j] = false → true` transition, counted at the transition so a
  re-mark of an already-dirty rule is not double-counted);
- `attempted` / `progressed` per rule (already available via `SettleReport` rows and
  `rule_costs`);
- **SPURIOUS mark** := a rule that was marked dirty and then, when attempted, made
  **no progress** (`progressed == false`). This is the operational definition used
  throughout; it is an upper bound on true spuriousness (a rule can also be
  legitimately dirty and legitimately fail).
- **NO-OP WRITE** := a `set_attr` whose new value `==` the stored value.

**What the diagnosis must report BEFORE any build (§1 deliverables):**

1. `marks_P1 : marks_P2 : marks_P3` on a plain photon tick of the 186000 six-area
   retina workload, and on the 160×120 Doom carve path.
2. The spurious-mark fraction overall and per path.
3. The no-op-write fraction of all `set_attr` calls on the same path.
4. A named verdict: **which over-approximation dominates.**

**Registered branch points (so nothing is tuned post-hoc):**

- **BRANCH A — P3 dominates (>50% of marks).** Build key-precise + value-level
  external dirtying (§2).
- **BRANCH B — P1 dominates.** Build the DYNAMIC (effective) write-set: dirty from the
  keys a firing ACTUALLY mutated (value-changed only), not the rule's static write-set.
- **BRANCH C — neither dominates / marks are genuinely non-spurious.** Report the
  **NEGATIVE**: the vision path is genuinely all-dirty per tick, area-grain parallelism
  is not the win, and say so plainly. **This is an acceptable rung outcome and will not
  be argued around.**

Branches A and B are not exclusive; if both exceed 30% of marks, build both.

---

## 2. WHAT WILL BE BUILT (contingent on §1)

A single engine flag **`precise_dirty`, DEFAULT `false`**. When `false` the engine is
**byte-unchanged** (the committed code path, not a re-derivation of it). When `true`:

**A. VALUE-LEVEL (no-op writes).** `Substrate::set_attr` compares the incoming value to
the stored one. **If equal: mark NOTHING** — no dirty bit, no cursor invalidation, no
`edge_delete_version` bump. Justification (the 185000 lesson, applied not re-learned):
a write that does not change the stored value cannot change any rule's bindings or any
where-clause's truth, so running the consumers WOULD BE A GENUINE NO-OP. Nothing is
frozen; no reference state is deferred; the graph is bit-identical either way.

**B. PER-KEY external dirtying.** A changing external write dirties only the rules whose
`read_set` intersects what was written, using **exactly the predicate `dirty_by_writeset`
already uses** (so the two paths become symmetric, as that function's own comment asks):

| write | dirties rule `j` iff |
|---|---|
| `set_attr(n, k, v)`, `v` changed | `reads_any[j] ∨ (has_where[j] ∧ Attr(k) ∈ read_set[j])` |
| `add_node(t, attrs)` | `reads_any[j] ∨ Type(t) ∈ read_set[j] ∨ (has_where[j] ∧ ∃k∈attrs. Attr(k) ∈ read_set[j])` |
| `set_type(n, t')` | `reads_any[j] ∨ Type(t') ∈ read_set[j]` (structural: unconditional) |
| `remove_node(n)` | `reads_any[j] ∨ Type(type(n)) ∈ read_set[j] ∨ (has_where[j] ∧ ∃k∈attrs(n). Attr(k) ∈ read_set[j])`, **plus** `mark_edge_type_dirty(et)` for every incident edge type (a deletion must never be under-approximated) |

Cursor invalidation follows the same rule as `dirty_by_writeset`: a dirtied rule whose
hit is an Attr/Type read gets its own cursor cleared; the global `edge_delete_version`
bump is retained wherever a deletion occurs.

**C. NOTHING ELSE.** No new Term enum variant (`term.rs` must diff empty). No change to
`run_rules` / `run_rules_opts` / `run_rules_settle` semantics. Rust + PyO3 setter only.

---

## 3. HEADLINE (falsifiable)

On the REAL photon/Doom path (the 186000 six-area retina relabelling, 2.87 ms baseline),
`precise_dirty = True`:

- **H1** reduces the number of dirty AREAS per tick **below the total** on a
  partially-changing scene (static background + a moving patch), and
- **H2** reduces per-tick settlement cost correspondingly.

**If H1/H2 fail, the negative is reported plainly.** "Dirty" is not redefined to
manufacture a win.

---

## 4. PRE-REGISTERED THRESHOLDS

| id | criterion | threshold |
|---|---|---|
| **C1a** | Oracle `bash scripts/rung7_vision_bench.sh`, **failed count** | **0**, and **BEFORE == AFTER** |
| **C1b** | 34-file cross-domain regression `scripts/per_area_settlement_regression.sh`: **SET of failing node ids** | **IDENTICAL** BEFORE vs AFTER |
| **C1c** | DEFAULT path (`precise_dirty=False`) full float-exact `graph_to_dict` digest, base engine vs 187000 engine, ≥4 workloads | **identical on every workload** |
| **C1d** | `runners/dsl/src/term.rs` diff | **empty** |
| **C2a** | **BYTE-IDENTITY of the PRECISE path**: `precise_dirty=True` vs `False`, full float-exact graph digest, ≥4 workloads incl. the real 2-D retina and the 160×120 Doom carve | **identical on every workload** |
| **C2b** | Landed vision outputs under `precise_dirty=True`: Doom 160×120 carve | **4 polys, IoU 0.1215, precision 0.9784** (exact) |
| **C2c** | Non-vacuity: the precise path must actually SKIP — dirty-marks under precise < dirty-marks under over-approximate | **strict reduction ≥ 2×** on the photon path |
| **F1** | **WRONG-PRECISION FALSIFIER.** An over-aggressive predicate (drop the `reads_any` disjunct AND the `Type` disjunct — i.e. dirty only on an exact `Attr(k)` hit) MUST break byte-identity on at least one of the C2a workloads | **MUST DIVERGE** (if it does not, C2a is vacuous and the rung reports that) |
| **F2** | **NO-FREE-LUNCH.** A workload in which every write genuinely changes something and every rule genuinely reads it: precise/over-approx cost ratio | **≥ 0.95** (i.e. precise is NOT faster when there is nothing to skip); reported even if outside |
| **H1** | dirty AREAS per tick on a partially-changing scene (six-area retina, one moving patch), precise | **< 6** (strictly fewer than the total), else NEGATIVE |
| **H2** | median per-tick cost, precise / over-approximate, same scene | **≤ 0.80** (a ≥20% reduction), else NEGATIVE |
| **H3** | dirty-area count and per-tick cost reported **as a function of the scene-change fraction** (0%, 1%, 5%, 25%, 100% of cells changing) | monotone non-decreasing in change-fraction (reported either way) |

H1/H2 are the rung's headline; **C1 is the primary gate and outranks them** — a
byte-identity break voids the rung regardless of speed.

---

## 5. THE OUTCOME THAT MUST REMAIN AVAILABLE

If the measurement says the eye's areas are **genuinely coupled every tick** — the onset
rule truly writes material carve/motion/salience truly read, every tick — then no
precision helps, and the honest finding is:

> *"The eye's areas are genuinely coupled per tick; area-grain parallelism is not the
> win; the win must come from elsewhere."*

That NEGATIVE is a **full rung outcome** and will be reported with its evidence.

---

## 6. THE 185000 LESSON — the trap this rung must not fall into

185000's Branch B skipped a retina cell whose adapted floor was then FROZEN; the cell
departed from a stale reference and MANUFACTURED spurious onsets (carve precision
0.978 → 0.0). **A skip is only admissible when running the skipped thing would be a
GENUINE NO-OP.** Every skip introduced here is of that kind:

- a no-op `set_attr` leaves the graph bit-identical, so its consumers' bindings and
  where-clauses are unchanged **by construction**;
- a per-key skip only skips a rule that provably does not read the written key
  (`read_set` is an over-approx SUPERSET of true reads, so "not in read_set" ⇒ "does
  not read it" — the safe direction).

Nothing is frozen, no reference state is deferred, no residual is dropped. C2a/F1 are
the proof obligations that this reasoning is not merely plausible.

---

## 7. GATE

`tests/test_dirty_precision_migrated.py`, self-contained, pinning:
byte-identity default-off; byte-identity precise-on; the wrong-precision falsifier
(F1) as an executable divergence; the no-free-lunch control (F2); the dirty-mark
reduction at the mechanism grain; the no-op-write skip; and `term.rs` untouched.

## 8. BUILD / PROVENANCE DISCIPLINE

- Build **ONLY** in this worktree. Canonical `.so`
  (`…/gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so`, md5
  `bb3692fdfa1be1c4aa3664dc1dbffabc`, mtime Jul 25 12:07) verified UNCHANGED before
  and after. Symlink-safe copy (`ls -la` first; `cp --remove-destination`).
- If Rust changes: **"CANONICAL NEEDS REBUILD ON MERGE."**
- Provenance §10 `source_match ∈ {own, shared}`.
- Curves + raw under `results/dirty_precision/`.
- Measurement runs SOLO; multiple trials, median + spread; claims keyed to ratios.

## 9. SEED CLAIM (verbatim)

```
SEED CLAIM 187000-187999: CLEAN -- no collision DETECTED.
  Scope: 887 files with seed sinks; 603 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
