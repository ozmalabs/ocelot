# INCREMENTAL MATCH — pre-registration

**Block 192000.** Seed block **192000–192999**. Base `main` @
`19748634bbde9eb8b635d18728278fda90604734`. This document is committed
**ALONE, BEFORE any performance number.** `python3 scripts/seed_claim.py
192000 192999` → **CLEAN** (verbatim in §9).

The directive: the matcher is the match-layer instance of the project's core
lie — recompute the world each tick instead of processing the change. The
CORRECT architecture is INCREMENTAL MATCH: maintain partial matches, propagate
only DELTAS (node/edge add/remove) through the joins, so a tick costs O(what
changed), not O(graph²). This rung is about ARCHITECTURAL CORRECTNESS, gated by
a REDUCTION to the full-rescan oracle.

---

## §0 THE SOUNDNESS DIRECTION — stated first, because it is the whole danger

Incremental match is unsafe in the RETRACTION direction. A tick deletes
nodes/edges and flips where-clause truth; an engine that adds matches on
insertion but fails to RETRACT matches whose support vanished DIVERGES from the
full rescan on any deleting/flipping rule. The rule adopted here: **the
full-rescan `run_rules` is the correctness ORACLE; any rule shape the
incremental path does not PROVABLY handle byte-identically falls back to
full-rescan for THAT rule.** Correctness is TOTAL from day one; coverage grows
later. An incremental result that "wins" but is not byte-identical to the full
rescan is a FAILED rung.

---

## §1 THE DIAGNOSIS — measured on the COMMITTED system, before anything is built

Read on the base engine `2458afa21641ec9b701adf4436e20640` (built from base HEAD
in this worktree; == canonical, confirmed by md5; worktree Rust source is
byte-identical to the shared checkout for `rewrite.rs`/`substrate.rs`).
Structural facts about the matcher, not results of this rung.

### §1.1 THE MATCHER IS ALREADY SEMI-NAIVE INCREMENTAL — the mission's premise is
### only true because the existing cursors are INVALIDATED every tick

The live fixpoint is `Substrate::run_rules_opts` (`substrate.rs:3064`). It is
NOT a blind full rescan:

1. **Differential firing at the RULE grain already exists.** Each outer pass
   builds `to_try` = the set of DIRTY active rules (`:3148`); a clean rule is
   never attempted. `rule_dirty` is set by `mark_edge_type_dirty` /
   `mark_node_mutation` / `dirty_by_writeset` and cleared after a rule is given
   its chance. A tick with nothing dirty exits at `:3133` doing zero work.

2. **Semi-naive incremental match at the BINDING grain already exists.**
   `attempt_one_rule` (`:2545`) → `try_incremental_match` (`:2175`). Per rule,
   per edge-type, a cursor `rule_cursors[rule_idx][edge_type] = (position,
   edge_delete_version)` records the length of `edges_by_type(et)` at last
   visit. On the next visit it enumerates ONLY `edges[position..]` — the edges
   NEW since last visit — and solves the rest of the pattern with the driver's
   vars pre-bound (`:2236`, `:2300`). **This IS delta-propagation on
   INSERTION.** Cursors advance to `lengths_before` (snapshot pre-effect), so a
   rule's own new edges are processed next visit — the committed fixpoint
   semantics.

3. **`reorder_match_edges` (`rewrite.rs:815`) — the shortcut NOT to build on —
   is confirmed DEAD CODE** (referenced only by its own unit tests + one
   comment; 189000 residual 8). It is a cardinality-ordered join PLANNER over a
   full rescan, not the incremental architecture. It is NOT adopted as the fix.

### §1.2 WHERE THE O(cells²) ACTUALLY COMES FROM — the global retraction sledgehammer

`try_incremental_match` BAILS to the COLD FULL RE-MATCH (`return None`) when:
(a) `k==0`; (b) `reads_external` (FbFrameSeq poll); (c) repeated edge-types (no
lex-order dedup); (d) **ANY cursor is stale: its stored `edge_delete_version !=
the current global counter`** (`:2221`); (e) cursor MISSING (first visit /
cleared).

Case (d) is the killer. `edge_delete_version` is a **SINGLE GLOBAL counter**
(`substrate.rs:116`) bumped by:

- **`mark_node_mutation` (`:720`) on EVERY external node/attr write** — even
  though NO EDGE WAS DELETED. It is (mis)used as a blunt "a where-clause might
  have flipped, invalidate all edge cursors" signal. 187000 measured this path
  at **1,536,016 marks/tick, 100% of dirty-marks, on the shipped 160×120 Doom
  path**.
- `attempt_one_rule` after a delete-effecting rule fires (`:2774`);
  `force_all_dirty`; imprecise `dirty_by_writeset`; pending rule edits.

So on the eye path the host writes cells → `edge_delete_version` bumps → **every
rule's cursor for every edge type is stale → every dirty rule takes the COLD
full re-match → enumerates `edges_by_type(first_match_edge)` (O(cells)) and
joins → O(cells²).** The incremental infrastructure EXISTS but is DEFEATED by a
coarse, GLOBAL, over-approximate retraction/invalidation signal.

### §1.3 THE EYE'S MINT-RULE SHAPE — enumerated, and it is the HARDEST covered shape

`retinal_mint_onset_2d` (`seeds/retinal_onset_2d.json`, area `retina`):
- match = `retina -has_column-> column` (O(cells), ~19,200 @160×120) ⋈
  `column -rod_receptor-> rod` ⋈ `rod -has_task-> task` (0 on accel, O(cells) on
  graph path) ⋈ `retina -has_onset_params_2d-> params` (1).
- where = `And(task.kind=="…onset", task.status=="done", Not task.onset_seen==1,
  column.carve2d_epoch …)` — reads TASK + COLUMN ATTRS.
- effects = `AddNode RetinalOnsetEvent` per binding — **NON-idempotent mint.**

`retinal_mint_carve_2d`: `retina -has_carve_params_2d-> cparams`(1) ⋈
`retina -has_column-> column`(O(cells)) ⋈ `retina -has_carve_task_2d-> task`
(O(cells) on graph path) → cartesian O(cells²); where reads task/column attrs;
mints `VisionPolygon`.

**Why the eye is the HARDEST, not the easiest, covered shape.** The `has_column`
edges are STABLE across ticks (columns are not re-minted). What changes each
tick is ATTRIBUTES (`task.status → done`, epoch stamps). A binding rejected last
tick (`status != done`) becomes valid this tick on the SAME stable edges. The
semi-naive new-edges-only cursor CANNOT see this — it is the code's own
documented **"stable-edge attr-gated bug"** (`:2283`). Making the eye
incremental byte-identically requires tracking WHICH bindings' where-truth can
flip when an attr is written and re-evaluating ONLY those — a per-binding
beta-network with PREDICATE RETRACTION. That is the largest part of a real
RETE/TREAT and is explicitly out of reach of one safely-verifiable rung.

### §1.4 THE DETERMINISTIC WORK COUNT already exists (supervisor's metric-currency correction)

`scale_audit` (`scale_audit.rs`) already carries the load-independent,
deterministic work counters the scaling headline must use — NOT wall-clock:
- `CAND_ENUM` / `candidates(n, path)` (`:504`) — candidate enumerations = the
  join/match work. **This is the primary scaling metric.**
- `CAND_TESTED` (`:525`), `WHERE_EVALS` (`:539`), `BINDINGS_CLONED` (`:126`),
  `RULE_ENUMERATIONS` (`:461`), `LEAF_VISITS` (`:566`).

The exponent (match-work vs cells) is fitted on `CAND_ENUM` (and reported for
the companion counters). Wall-clock ms and "max receptors @30/60fps" are
SECONDARY REPORTED FACTS only — recorded (solo if at all), never gated, never
headlined.

---

## §2 WHAT WILL BE BUILT — additive, DEFAULT OFF, one engine flag

`Substrate::incremental_match`, **DEFAULT FALSE**. OFF ⇒ the committed path,
byte-unchanged (primary gate). ON: the correct-architecture change, with SOUND
FALLBACK for every shape not proved covered.

### §2.1 THE COVERED SHAPE (first) — RETRACTION-PRECISE CURSORS via per-edge-type delete versioning

Replace the single global `edge_delete_version` cursor-validity check with a
**per-edge-type delete version**: `edge_delete_version_by_type[et]`, bumped only
when an edge of type `et` is actually deleted (or its `edges_by_type[et]` array
is shifted). A rule's cursor for `et` is valid iff `et`'s OWN version is
unchanged since the cursor was set.

Consequence — CORRECT incremental retraction at the type grain:
- A delete of edge type X invalidates ONLY cursors reading X (exactly the rules
  whose `edges_by_type(X)` shifted → they full-rescan → RETRACT stale matches).
  Rules reading only OTHER (append-only) edge types keep their cursors → stay on
  the O(Δ) incremental path across the delete. This is the retraction hazard
  handled precisely instead of globally.
- **The where-flip invalidation that `mark_node_mutation` performs on external
  ATTR writes is PRESERVED byte-for-byte** (it dirties + must still invalidate
  the cursors of the where-rules it dirties), because an attr write flipping a
  where on a stable edge is NOT visible to the new-edges cursor. This is why the
  eye's mint rules (where reads externally-mutated attrs) STILL fall back to
  full rescan under this rung — byte-identical, and the honest scope boundary.

### §2.2 THE COVERAGE BOUNDARY — stated explicitly, as the mission requires

**COVERED (incremental, O(Δ)):** multi-edge, non-repeated-edge-type, non-
`reads_external` rules whose per-tick binding change is driven by NEW EDGES of
append-only types AND whose cursors are not invalidated by a where-flip
(i.e. their where reads no key written that tick, or they have no where). For
these, a delete of an UNRELATED edge type no longer forces a full rescan.

**FALLS BACK (full rescan, byte-identical):** everything else — repeated
edge-types, `reads_external`, `k==0`, batch rules, and critically **any rule
dirtied by a where-flip on stable edges (the eye's mint-rule shape).** Full
rescan is the SAME result; coverage, not correctness, is what is partial.

### §2.3 THE FALSIFIER — `incremental_match_unsound`, default false

A deliberately-broken variant that MISSES a retraction: it validates a cursor
against a per-edge-type version that is NOT bumped on delete of that type (or
uses a stale global==current test while the covered path advanced). It MUST
diverge from the full rescan on a deleting workload. If a broken retraction
breaks nothing, the reduction gate is too weak to trust.

**NO new Term enum variant. `runners/dsl/src/term.rs` diff MUST be EMPTY**
(engine flag/struct + PyO3 only).

---

## §3 THE PRE-REGISTERED CRITERIA (thresholds fixed BEFORE any number)

### Reduction (PRIMARY correctness gate)
- **C1 — DEFAULT OFF ≡ BASE engine, whole-graph float-exact `graph_to_dict`,
  ≥5 workloads incl. ≥1 non-vision, + the landed 160×120 carve (4 polys / IoU
  0.1215 / precision 0.9784 / 0 false).** OFF must be byte-identical to the base
  engine `2458afa2…`.
- **C2 — INCREMENTAL ON ≡ FULL RESCAN, byte-identical, same ≥5 workloads +
  landed carve + a firing incremental workload (append-only multi-edge rule).**
  This is the reduction — the headline correctness claim.
- **C3 — RETRACTION: a DELETING rule workload is byte-identical ON vs full
  rescan** (a rule that deletes edges of type X while an append-only rule reads
  type Y — Y keeps its cursor, X's consumers retract).
- **C4 — `term.rs` diff EMPTY.**

### Scaling (count-based, per the metric-currency correction)
- **H1 — On the COVERED incremental workload, `CAND_ENUM`-vs-cells exponent
  drops from ≈2.0 (full rescan) to ≤1.2 (incremental ≈ O(Δ)).** Fitted on the
  deterministic work count, not ms. Reported for `CAND_TESTED` / `WHERE_EVALS` /
  `BINDINGS_CLONED` too.
- **H2 (secondary, reported not gated) — wall-clock ms + max receptors @30/60fps
  on whatever path the covered shape reaches.** Solo if recorded. NOT a claim.
- **HONEST NEGATIVE ALLOWED AND EXPECTED — the eye's mint shape stays full
  rescan** (needs per-binding where-retraction). Reported as the named next
  lever, not hidden.

### Falsifier
- **F1 — `incremental_match_unsound` DIVERGES from full rescan on the C3
  deleting workload** (byte-identity broken AND an observable moved). Non-vacuous.

### No-free-lunch
- **F2 — on a control where the covered shape does not apply (all rules fall
  back), incremental ON ≡ OFF and costs ≤ ~1.05× the work count.**

---

## §4 PROVENANCE & DISCIPLINE (committed to up front)

- **SEPARATE prereg commit** (this file ALONE) BEFORE any number.
- **Seed block 192000–192999**, `seed_claim` CLEAN (§9).
- **Oracle** `bash scripts/rung7_vision_bench.sh` — BEFORE == AFTER, 0 failed.
  (worktree-without-`data/` condition; report the exact counts both sides.)
- **Cross-domain regression** `scripts/per_area_settlement_regression.sh` (34
  named files, never a `-k` selector) — BEFORE == AFTER, failing node-id SET
  compared, not a count.
- **Gate** `tests/test_incremental_match_migrated.py` — pins C1/C2 (reduction),
  C3 (retraction), F1 (unsound falsifier), H1 (covered-path work-count
  exponent), at the mechanism grain.
- **BUILD SAFETY (LESSON 9b).** Canonical `.so` md5
  **`2458afa21641ec9b701adf4436e20640`** verified BEFORE first `cp`, AFTER every
  `cp`, at final commit; worktree `.so` a REAL FILE each time; build ONLY in
  this worktree via `scripts/engine_build.sh` (`--remove-destination`, never
  through a symlink). **CANONICAL NEEDS REBUILD ON MERGE.**
- **`source_match ∈ {own, shared}`** (§10).
- Curves under `results/incremental_match/`.

---

## §5 HONEST RESIDUALS ANTICIPATED

1. The eye's O(cells²) mint shape is a where-flip-on-stable-edge problem; this
   rung does NOT make it incremental — it falls back byte-identically. The named
   next lever is a per-binding beta-network with predicate retraction (the large
   RETE). This rung lands the retraction-precise cursor infrastructure + the
   reduction gate + a covered append-only shape with its work-count exponent
   dropped, and names the eye explicitly.
2. Per-edge-type versioning is byte-identical but its WIN is on workloads with
   deletes concentrated in some edge types while other append-only rules read
   others; whether the shipped vision path pulls it is an empirical question the
   results doc will answer honestly (a negative there, like 187000/189000, is a
   valid outcome).

---

## §9 SEED CLAIM (verbatim)

```
SEED CLAIM 192000-192999: CLEAN -- no collision DETECTED.
  Scope: 893 files with seed sinks; 613 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## §10 PROVENANCE

`source_match = "own"` (rung engine built in THIS worktree). `stale_rust = []`.
Base engine md5 `2458afa21641ec9b701adf4436e20640` (== canonical, confirmed).
