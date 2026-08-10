# PREDICATE RETRACTION — pre-registration (ladder rung B)

**Block 194000.** Seed block **194000–194999**. Base `main` @
`d65d13d642fc49172fe2030a2ed4810e0eb6a0f0` (rung A, INCREMENTAL MATCH, landed).
This document is committed **ALONE, BEFORE any AFTER number.**
`python3 scripts/seed_claim.py 194000 194999` → **CLEAN** (verbatim in §9).

Rung A proved the matcher was already semi-naive incremental and fixed the
GLOBAL `edge_delete_version` sledgehammer with PER-EDGE-TYPE delete versioning —
byte-identical, covered-shape `cand_enum` exponent 1.968→1.000. A's honest
boundary, and B's named target: **the eye's `retinal_mint_*` rules fall back to
full rescan byte-identically**, because their `where` reads a host-mutated attr
on a stable-edge join and `mark_node_mutation` clears the whole rule cursor every
tick. B is the per-binding **predicate-retraction** step A named: when a host
attr changes, re-evaluate only the BINDINGS whose `where`-truth can flip on that
specific node's change — a lean TREAT-flavoured alpha re-evaluation on demand,
keeping every still-valid partial match — instead of clearing the whole cursor
and re-deriving every binding.

---

## §0 THE RECON REFRAME — measured on the COMMITTED system, BEFORE anything is built

Structural diagnosis of the committed matcher (engine `48eb6e53e1d7`, this
worktree, Rust source byte-identical to base `d65d13d642`), NOT a result of this
rung. Runners: `scripts/_recon_b.py`, `scripts/_recon_b2.py`. These correct the
mission's framing with numbers.

### §0.1 THE EYE'S PER-TICK MATCH IS O(cells^1.0), NOT O(cells²) — and A's OFF≡ON on it

On the committed, task-PRUNED 2-D graph retina (onset + carve seeds loaded, a
moving-bar stimulus, one tick measured after warmup), the deterministic match
work `cand_enum` scales **linearly** in cells, and A's per-edge-type versioning
(`incremental_match` ON) changes NOTHING versus OFF — confirming A's boundary
that the eye falls back to full rescan byte-identically:

| cells | 80 | 180 | 320 | 500 | exponent |
|---|---|---|---|---|---|
| `cand_enum` OFF | 2302 | 5165 | 9182 | 14328 | **0.998** |
| `cand_enum` ON (A) | 2302 | 5165 | 9182 | 14328 | **0.998** (identical) |
| `where_evals` OFF | 2154 | 4806 | 8554 | 13298 | 0.994 |

**The "run_rules O(cells²)" the mission attributes to the eye's where-gated mint
is NOT present on the committed pruned graph path — the per-tick match is already
O(cells).** (The historical quadratic, block 182000, was task ACCUMULATION,
closed by pruning in 183000; the carve settle is a separate, non-per-tick op.)

### §0.2 WHY O(cells) IS DRIVER-BOUND, NOT MATCHER-BOUND — the decisive finding

The graph-path driver (`GraphEye.submit_photons_2d`, no accelerator) mints **one
fresh `CognitiveTask` node + `has_task` edge PER CELL, EVERY tick** — measured
exactly:

| cells | 80 | 180 | 320 | 500 |
|---|---|---|---|---|
| new `CognitiveTask` nodes this tick | 80 | 180 | 320 | 500 |

Every cell is stimulated every tick (a full sweep; dark cells still get an empty
task so the adapting floor advances). So the eye's O(cells) is the cost of the
INPUT — O(cells) fresh tasks, O(cells) `has_task` edges, O(cells) attr writes —
NOT matcher naivety. **A per-binding predicate-retraction beta-network cannot
reduce the shipped full-sweep eye below O(cells): there is no sparse set of
flipped bindings to exploit when the driver re-presents every cell.** The eye
benefits from B ONLY under a SPARSE-INPUT driver (the dirty-index sensor,
block 185000), which is a world/driver change, not a matcher change.

### §0.3 THE SHAPE B ACTUALLY REDUCES — the stable-edge attr-flip, quantified

The reducible shape is the ABSTRACT one A named: N STABLE `hub -has_cell-> cell`
+ `cell -has_flag-> flag` edges (never deleted), a where-rule reading a per-cell
attr, and each tick a SPARSE flip of the attr on only K cells. On the committed
engine, flipping K=3 cells still re-scans ALL N (a single external attr write
calls `mark_node_mutation`, which clears the whole rule's cursor → full rescan):

| N | 64 | 128 | 256 | 512 | exponent |
|---|---|---|---|---|---|
| `cand_enum`, K=3 flipped | 131 | 259 | 515 | 1027 | **0.990** |

**This O(N)-on-a-K-flip is B's genuine opportunity: reduce it to O(K).** The
shipped eye does not exhibit this shape (§0.2); a sparse-driver eye would.

### §0.4 SCOPE DECISION (honest, per the rung method)

A full TREAT/RETE per-binding beta-network with derived-tuple RETRACTION is more
than one rung. B lands the **scoped first step**: **node-seeded per-binding
re-evaluation for the FIRE direction on add-only-effect where-rules** — exactly
the eye's mint-rule shape (effects are `AddNode` a fresh event + `SetAttr` a
refractory marker; no derived tuple is retracted, so the hazard is a MISSED FIRE
of a newly-true binding, not a stale-tuple retraction). The reduction is proven
on the §0.3 abstract shape (the shape the shipped eye lacks), and the driver
boundary is named. General derived-tuple retraction (a where going FALSE
retracting a prior match) is explicitly OUT of this rung.

---

## §1 WHAT WILL BE BUILT — additive, DEFAULT OFF, one engine flag

`Substrate::predicate_retraction`, **DEFAULT FALSE**. OFF ⇒ the committed path,
byte-unchanged (so every existing gate is byte-identical BY CONSTRUCTION — the
new path is unreachable with the flag off). ON: for a where-rule with ADD-ONLY
effects whose edge-cursors are valid (no edge insert/delete since last visit) but
which was dirtied by an EXTERNAL attr write, re-evaluate ONLY the bindings that
touch the written node(s), instead of clearing the cursor and full-rescanning.

### §1.1 MECHANISM (lean-TREAT, settlement-framed)

- **Per-rule dirty-node set** `rule_dirty_nodes: Vec<FxHashSet<NodeID>>`,
  maintained ONLY when the flag is on. `set_attr` already knows the written
  `nid`; a new `mark_node_predicate_dirty(nid)` records it against each dirtied
  where-rule and, crucially, DOES NOT clear that rule's edge-cursors (the edges
  did not change). A binding whose predicate node changed is a partial match that
  must RE-SETTLE; one whose nodes were untouched keeps its assertion (the
  settlement axiom at the join layer — a tick is a settlement event with a
  residual, never a blanket re-derivation).
- **Node-seeded re-eval** in the rule-attempt path: for each dirty node `d` and
  each match position whose var can bind `d`, seed the matcher with
  `{var: d}` and drive the remaining join with `match_rule_each_with_initial`
  (the same call the incremental path uses), applying add-only effects, deduped
  by binding key. Cost = O(K · fan-out), not O(N).
- **Guard (soundness):** the node-seeded path is taken ONLY for rules whose
  effects are add-only (no `DelEdge`/`DelNode`, i.e. no derived-tuple retraction)
  AND whose edge-cursors are valid. Any other shape (edge churn, delete effects,
  repeated edge-types, `reads_external`, `k==0`) FALLS BACK to the committed
  full-rescan path byte-identically — same as OFF.
- **Integer/event native:** the dirty-node set is a set of node ids; the version
  counters are unbounded integers. No float in the matcher bookkeeping.

### §1.2 THE COVERAGE BOUNDARY — stated explicitly

**COVERED (incremental, O(K)):** add-only-effect where-rules on stable edges
dirtied by a SPARSE external attr write (the §0.3 shape). For these, a K-cell
attr flip costs O(K), not O(N).

**FALLS BACK (full rescan, byte-identical):** the SHIPPED full-sweep eye
(§0.2 — every cell dirty each tick, so K=N, no reduction, and its `has_task`
edges churn so cursors are invalid anyway); delete-effecting / retracting rules;
edge-churning rules; everything rung A already covered or fell back on. Coverage,
not correctness, is partial.

### §1.3 THE FALSIFIER — `predicate_retraction_unsound`, default false

A deliberately-broken variant that MISSES a retraction/re-fire: it re-evaluates
only a STRICT SUBSET of the dirty nodes (drops one), so a binding whose predicate
flipped to TRUE is not re-fired. It MUST diverge from the full rescan on the
sparse-flip workload — an observable (the fired-binding / minted-event set) must
move. If a broken re-eval breaks nothing, the reduction gate is too weak to trust.

**NO new Term enum variant. `runners/dsl/src/term.rs` diff MUST be EMPTY**
(engine flag/struct + PyO3 only).

---

## §2 THE PRE-REGISTERED CRITERIA (thresholds fixed BEFORE any AFTER number)

### Byte-identity (PRIMARY correctness gate) — manifold-gated on OBSERVABLES

Per the standing C2a caveat (186000/187000/188000): do NOT gate on raw
whole-graph insertion-order state. Gate on TWO orthogonal APPROXIMATE observable
checks that together pin the observable manifold:

- **C1 — DEFAULT OFF ≡ BASE engine `48eb6e53…`** on ≥5 workloads (vision +
  non-vision) + the landed 160×120 carve — byte-identical `graph_to_dict`.
  (OFF reaches no new code, so this is structural.)
- **C2 — PREDICATE-RETRACTION ON ≡ FULL RESCAN** on the sparse-flip workload AND
  a sparse-driver eye, gated on **(a) the carve VisionPolygon set / IoU** AND
  **(b) the onset-or-fired digest** (two orthogonal observables), plus the
  fired-binding set. This is the reduction — the headline correctness claim.
- **C3 — `term.rs` diff EMPTY.**

### Scaling (count-based, per the metric-currency rule)

- **H1 — On the covered §0.3 sparse-flip shape, `cand_enum`-vs-N exponent drops
  from ≈1.0 (full rescan re-scans all N) to ≈0.0 (O(K), K fixed) — reported as
  the count at fixed K across N (flat), the AFTER of §0.3's 131/259/515/1027.**
  Fitted on the deterministic `cand_enum` work count, not wall-clock. Reported
  for `cand_tested` / `where_evals` too.
- **HONEST NEGATIVE, PRE-REGISTERED AND EXPECTED — the SHIPPED full-sweep eye is
  NOT reduced by B** (§0.2: driver-bound O(cells); K=N; edge churn). Reported as
  the measured boundary, with the sparse-input driver named as the next lever.

### Falsifier

- **F1 — `predicate_retraction_unsound` DIVERGES from full rescan** on the C2
  sparse-flip workload (fired-binding / minted-event observable moves). Non-vacuous.

### No-free-lunch

- **F2 — on a control where the covered shape does not apply (all rules fall
  back), ON ≡ OFF and costs ≤ ~1.05× the `cand_enum` work count.**

---

## §3 PROVENANCE & DISCIPLINE (committed to up front)

- **SEPARATE prereg commit** (this file ALONE) BEFORE any AFTER number.
- **Seed block 194000–194999**, `seed_claim` CLEAN (§9).
- **Oracle** `bash scripts/rung7_vision_bench.sh` — BEFORE == AFTER, exact counts
  both sides (data-present 224/0, or the data-less worktree condition; report both).
- **THE ENGINE-SEMANTICS GATE SET (lesson 12), run SYNCHRONOUSLY in one session:**
  `test_incremental_match_migrated`, `test_empty_match_proof_migrated`,
  `test_dirty_precision_migrated`, `test_per_sensor_epoch_migrated`,
  `test_per_area_settlement_migrated`, plus the eye suite. Each file's pass count
  recorded. (All are byte-unchanged: the flag is OFF for every one of them.)
- **Gate** `tests/test_predicate_retraction_migrated.py` — pins C1/C2 (reduction),
  H1 (covered-path work-count), F1 (unsound falsifier), at the mechanism grain.
- **The measure module is IMPORT-INERT** (the exact A revert bug): it NEVER
  mutates shared state (flag/env/monkeypatch) at MODULE TOP LEVEL — only inside a
  scoped context manager around each call.
- **BUILD SAFETY (LESSON 9b).** Canonical `.so` md5
  **`66b8532ca658b0edc7fcf82eec869ef6`** verified BEFORE first build, AFTER, and
  at final commit; worktree `.so` a REAL FILE (built via `scripts/engine_build.sh`,
  `--remove-destination`, never through a symlink). Build ONLY in this worktree.
  **CANONICAL NEEDS REBUILD ON MERGE.**
- **`source_match ∈ {own, shared}`** — never a pinned hash.
- Curves under `results/predicate_retraction/`.

---

## §4 HONEST RESIDUALS ANTICIPATED

1. **The shipped full-sweep eye is not reduced by B** (§0.2). This is the
   pre-registered negative: the eye's O(cells) is the driver's O(cells) input,
   not a naive matcher. The named next lever is the sparse-input driver
   (dirty-index, 185000) so the eye PRESENTS the §0.3 sparse shape B reduces.
2. **General derived-tuple retraction is out of scope** (§0.4): B does the FIRE
   direction on add-only-effect rules. A where going FALSE retracting a prior
   derived match (the full RETE beta-memory) is the next rung after this.
3. Whether any shipped seed rule (outside the eye) organically presents the
   covered sparse shape is an empirical question the results doc answers honestly
   (a negative there is a valid outcome, like 187000/189000).

---

## §9 SEED CLAIM (verbatim)

```
SEED CLAIM 194000-194999: CLEAN -- no collision DETECTED.
  Scope: 894 files with seed sinks; 609 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## §10 PROVENANCE

`source_match`: `own` (this rung builds Rust in this worktree). Engine at prereg
time `48eb6e53e1d7` (worktree, source byte-identical to base `d65d13d642`).
Canonical `.so` `66b8532ca658b0edc7fcf82eec869ef6`, untouched.
