# PREDICATE RETRACTION — RESULTS (block 194000, ladder rung B)

Prereg: `PREDICATE_RETRACTION_PREREG.md`, committed ALONE (`076337baaf`) BEFORE
any AFTER number. `seed_claim(194000,194999)` CLEAN. Base `main` @ `d65d13d642`
(rung A). **This rung BUILDS Rust. CANONICAL NEEDS REBUILD ON MERGE.**
`source_match`: **own**.

---

## ⚠️ SUPERVISOR CORRECTION (2026-07-26) — §0.1's premise-correction is ITSELF wrong

**B's §0.1 claim "the eye's per-tick match is O(cells^1.0), NOT O(cells²) … the
run_rules O(cells²) is not present" is FALSE, and it is a metric-completeness
error — the exact failure the rung was warned about.** B measured `cand_enum`
(0.998, linear) and concluded the quadratic was gone. But `cand_enum` counts the
NUMBER of candidates enumerated; it does NOT count the work done INSIDE each
candidate's term evaluation. Supervisor re-measured the committed eye at 80→2880
cells, `cand_enum` alongside `run_rules` wall-clock AND the per-term counters:

| counter | exponent |
|---|---|
| `cand_enum`, `where_evals`, `cand_tested` | ~**1.00** (linear) |
| `run_rules` wall-clock | **1.61** |
| `term_eval:Attr`, `term_eval:Var`, `term_evals_total` | **1.77–1.85** |

**The eye IS ~O(cells²) — 191000's ledger row STANDS.** The quadratic is
`ct_area_effort_tracks_live_salience` (seed `cognitive_scheduler.json`): its guard
`Not(Eq(area.effort, MaxOver(Neighbours(area,has_task) as c, c.salience)))`
recomputes a MaxOver over ALL tasks-on-area for EVERY `(area,task)` candidate.
`cand_enum` is linear (O(tasks) candidates); the O(T) MaxOver INSIDE each guard is
what makes `term_eval:Attr` = O(tasks·T) = O(cells²). `cand_enum` is an INCOMPLETE
work-count; `term_evals_total` is the complete one and it tracks wall-clock.

This does not retract rung B's MECHANISM — the per-binding predicate retraction is
real, byte-identical, `term.rs`-empty, and reduces `cand_enum` O(N)→O(K) on the
abstract stable-edge attr-flip shape (that result stands). It retracts only B's
DIAGNOSTIC FRAMING that the eye needs merely a sparse driver. **The real fix is
block 195000** (`binding_projection`, built by 188000, left default-OFF): projecting
the unused `task` var fires the guard once per AREA not per task → `term_eval:Attr`
1.835→1.000, wall-clock 1.647→1.052 (8.5× at 2000 cells, gap growing), and the eye's
observables (onsets, carve polygons, `area.effort`, node counts) are IDENTICAL. The
standing lesson: **a work-count is a valid effort proxy ONLY if it is complete; an
incomplete work-count is worse than wall-clock because it looks authoritative while
hiding the quadratic. "Time is a bad proxy — because it lets you cheat and not
understand what you are doing" applies to any un-understood proxy, counts included.**

---

## TL;DR — the recon corrected the premise; the reduction is real where the shape exists

Rung A named rung B's target as "the eye's where-gated mint, needs per-binding
predicate retraction." The RECON here **measured that framing and corrected it**:

1. **The eye's per-tick match is O(cells^1.0), NOT O(cells²)** on the committed
   pruned graph path, and A's per-edge-type versioning gives OFF≡ON on it.
2. **That O(cells) is DRIVER-bound, not matcher-bound** — the driver mints one
   fresh `CognitiveTask` + `has_task` edge PER CELL every tick (a full sweep). No
   matcher change can reduce it; the eye needs a SPARSE-INPUT driver.
3. **The genuine reducible shape is the abstract stable-edge attr-flip** (N stable
   edges, K≪N attrs flipped per tick), which the committed matcher re-scans O(N).

B builds the node-seeded per-binding re-evaluation (lean-TREAT), **DEFAULT OFF**,
and **reduces that shape O(N)→O(K), byte-identical**, with the unsound falsifier
biting. The shipped eye is NOT reduced (measured, byte-identical fallback) — the
pre-registered honest negative.

- **C1 — DEFAULT OFF ≡ base engine.** ✅ (the OFF path reaches no new code; the
  full engine-semantics gate set + eye suite + vision oracle are byte-unchanged).
- **C2 — THE REDUCTION: node-seeded ON ≡ full-rescan OFF, byte-identical** on the
  covered shape across N∈{64,256} × K∈{1,3,7} — float-exact `graph_to_dict`. ✅
- **H1 — covered `cand_enum` exponent 0.981 (full rescan, ~O(N)) → 0.000
  (node-seeded, FLAT at K=3 → count 6/6/6/6).** ✅ Linear→constant.
- **F1 — the UNSOUND falsifier (drops one dirty node) DIVERGES** from full rescan
  (fired-edge observable moves). Non-vacuous. ✅
- **F2 — no-free-lunch:** on a non-covered control (no external flip), ON ≡ OFF,
  work within 1.05×. ✅
- **C3 — `term.rs` diff EMPTY.** ✅
- **HONEST NEGATIVE (pre-registered): the shipped full-sweep eye is NOT reduced**
  — pred-ON ≡ pred-OFF, `cand_enum` 9182 both, onsets 1593 both. The named next
  lever is the sparse-input driver.

---

## §0 THE RECON (measured on the committed engine `48eb6e53`, source == base)

Runners: `scripts/_recon_b.py`, `scripts/_recon_b2.py`.

### §0.1 The eye's per-tick match is O(cells^1.0), and A's OFF≡ON on it

| cells | 80 | 180 | 320 | 500 | exponent |
|---|---|---|---|---|---|
| `cand_enum` OFF | 2302 | 5165 | 9182 | 14328 | **0.998** |
| `cand_enum` ON (A, per-type) | 2302 | 5165 | 9182 | 14328 | **0.998** (identical) |

The "run_rules O(cells²)" the mission attributed to the eye's where-gated mint is
**not present** on the committed pruned path — it is O(cells). (The historical
quadratic, block 182000, was task ACCUMULATION, closed by pruning in 183000.)

### §0.2 The O(cells) is DRIVER-bound — the decisive finding

`GraphEye.submit_photons_2d` (graph path) mints one fresh `CognitiveTask` +
`has_task` edge PER CELL, EVERY tick:

| cells | 80 | 180 | 320 | 500 |
|---|---|---|---|---|
| new `CognitiveTask` this tick | 80 | 180 | 320 | 500 |

Every cell is stimulated every tick, so the eye's O(cells) is the cost of the
INPUT, not matcher naivety. A per-binding beta-network cannot reduce a full sweep
below O(cells): there is no sparse flipped-binding set to exploit.

### §0.3 The reducible shape — stable-edge attr-flip, quantified (committed)

N stable `hub→cell`+`cell→flag` edges; flip an attr on K=3 cells/tick. The
committed matcher re-scans ALL N:

| N | 64 | 128 | 256 | 512 | exponent |
|---|---|---|---|---|---|
| `cand_enum`, K=3 flipped | 131 | 259 | 515 | 1027 | **0.990** |

---

## §1 WHAT WAS BUILT (Rust, additive, DEFAULT OFF; `term.rs` EMPTY)

`Substrate::predicate_retraction`, default false. OFF ⇒ committed path,
byte-unchanged (the whole path is unreachable with the flag off).

1. **`mark_node_predicate_dirty(nid, key)`** — the predicate-retraction twin of
   `mark_external_write`. For an UNCOVERED where-rule it clears the cursor
   (committed full-rescan fallback); for a COVERED rule (`rule_pred_retract_ok`)
   it records `nid` in `rule_dirty_nodes[rule]` and KEEPS the cursor. Bumps no
   global version (no edge deleted).
2. **`try_predicate_retraction(rule_idx)`** — engages only when every match-edge
   cursor is provably UNCHANGED (per-type version match AND position == current
   `edges_by_type` length, i.e. no new edges and no delete). It then drives from
   the edges INCIDENT to each dirty node (`out_edges_slice`/`in_edges_slice`,
   O(degree) — NOT a full population scan), seeds both endpoints, solves the rest
   of the pattern with that edge removed (the semi-naive driver, re-seeded on
   "edges touching a dirty node"), applies add-only effects deduped by binding
   key, undoes no-ops, and re-stores cursors. Any structural change ⇒ clear the
   dirty set + cursor and fall through to the committed cold rescan.
3. **`rule_pred_retract_ok`** (computed at `add_rule`): has-where, add-only
   effects (no `DelEdge`/`DelNode`/`ReplaceValue`/…), non-repeated edge types,
   non-`reads_external`, k≥1. The FIRE direction only — no derived-tuple
   retraction (the next rung).
4. **`predicate_retraction_unsound`** (falsifier, default false) — drops one
   dirty node ⇒ a flipped-to-true binding is never re-fired ⇒ diverges.
5. PyO3 setters `set_predicate_retraction` / `set_predicate_retraction_unsound`.
   **NO new Term enum variant — `git diff d65d13d642 HEAD … term.rs` is EMPTY.**

`diff --stat` vs base: `substrate.rs +~180`, `py.rs +~25`. `term.rs` 0.

---

## §2 THE COVERAGE BOUNDARY (as prereg'd)

**COVERED (incremental, O(K)):** add-only-effect where-rules on stable edges
dirtied by a SPARSE external attr write. A K-node flip costs O(K), not O(N). The
guard must be STRUCTURAL (an edge) or externally cleared — an attr SELF-guard
(`Not attr==1` where the effect writes that attr) triggers the committed
effect-driven cursor clear on the confirmation pass and is NOT reduced (a further
boundary — see §5).

**FALLS BACK (full rescan, byte-identical):** the SHIPPED full-sweep eye (§0.2 —
every cell dirty, `has_task` edge churn invalidates the cursor, so node-seed never
engages); delete/retracting rules; edge-churning rules; `reads_external`; k==0;
everything rung A already covered or fell back on.

---

## §3 THE PRE-REGISTERED CRITERIA

| id | threshold | measured | verdict |
|---|---|---|---|
| **C1** | OFF ≡ base engine | full engine-semantics gate set (61) + eye suite (50) + vision oracle (214/10) byte-unchanged; OFF reaches no new code | ✅ |
| **C2** | node-seeded ON ≡ full rescan, byte-identical | float-exact dump identical, N∈{64,256} × K∈{1,3,7}; N=128/K=5 `identical=True` | ✅ |
| **H1** | covered `cand_enum` exponent O(N) → O(K) | **0.981 → 0.000** (off 67/131/259/515; on **6/6/6/6** flat at K=3) | ✅ |
| **F1** | unsound MUST diverge | **DIVERGES** — dump differs from full rescan when one dirty node is dropped | ✅ |
| **F2** | no-free-lunch on a non-covered control | ON ≡ OFF, work ≤ 1.05× | ✅ |
| **C3** | `term.rs` diff EMPTY | empty | ✅ |

Raw: `results/predicate_retraction/results.json`.

### The reduction (H1), count-based

One tick = flip `armed` on K=3 cells + `run_rules`. Per-tick `cand_enum`:

| N (cells) | 64 | 128 | 256 | 512 | exponent |
|---|---|---|---|---|---|
| **full rescan (off)** | 67 | 131 | 259 | 515 | **0.981** |
| **node-seeded (on)** | 6 | 6 | 6 | 6 | **0.000** |

The full rescan re-enumerates all N cells to find the K that flipped; the
node-seeded path drives only from the K flipped cells' incident edges. The count
goes LINEAR→CONSTANT (K fixed) — a stronger drop than rung A's 1.968→1.000,
because A reduced O(n²)→O(Δ·n) while B reduces O(N)→O(K).

---

## §4 THE HONEST NEGATIVE (pre-registered) — the shipped eye is not reduced

Predicate-retraction ON vs OFF on the real 2-D graph retina (16×20, moving bar):

| | `cand_enum` | onsets |
|---|---|---|
| pred OFF | 9182 | 1593 |
| pred ON | 9182 | 1593 |

**IDENTICAL** — the eye falls back byte-identically. Why: the driver re-mints a
task + `has_task` edge per cell each tick, so (a) the cursor is invalidated by new
edges every tick (node-seed never engages) and (b) every cell is dirty (K=N). The
reduction requires a SPARSE-INPUT driver (the dirty-index sensor, block 185000) so
the eye PRESENTS the §0.3 sparse shape. That is the named next lever.

---

## §5 RESIDUALS (measured / named honestly)

1. **The shipped full-sweep eye is not reduced** (§4). Named next lever: the
   sparse-input driver so the eye presents the covered shape.
2. **An attr SELF-guard is not reduced.** A covered rule whose guard reads an attr
   its own effect writes (`Not onset_seen==1`, the eye's onset rule) triggers the
   committed effect-driven cursor clear on the fixpoint confirmation pass → O(N)
   confirmation. The reduction lands cleanly only when the guard is STRUCTURAL (an
   edge, as in the gate workload) or externally cleared. Fully reducing the
   attr-self-guard case needs node-grained propagation through the rule-effect
   dirty path (`dirty_by_writeset`) — the next increment.
3. **Derived-tuple RETRACTION is out of scope** — B does the FIRE direction on
   add-only-effect rules only. A where going FALSE retracting a prior derived
   match (the full RETE beta-memory) is the rung after this.
4. **Whether any shipped seed rule outside the eye organically presents the
   covered sparse shape** is unmeasured here; a negative there would be valid.

---

## §6 PROVENANCE, GATES, DISCIPLINE

- **Prereg committed ALONE** (`076337baaf`) BEFORE any AFTER number.
- **Seed block 194000–194999**, `seed_claim` CLEAN.
- **`term.rs` diff EMPTY** vs base `d65d13d642` (verified).
- **Engine-semantics gate set (lesson 12), ONE synchronous session — 61 passed:**
  `test_incremental_match_migrated` (6), `test_empty_match_proof_migrated` (13),
  `test_dirty_precision_migrated` (10), `test_per_sensor_epoch_migrated` (9),
  `test_per_area_settlement_migrated` (17), `test_predicate_retraction_migrated`
  (6). **Eye suite (one session): 50 passed** (`test_2d_retina`,
  `test_retinal_onset`, `test_async_carve`, `test_photon_grapheye`,
  `test_eye_graphnative_event`, `test_2d_motion_salience`).
- **Oracle `bash scripts/rung7_vision_bench.sh`: BEFORE == AFTER == 214 passed /
  10 skipped / 0 failed** (data-less worktree condition). BEFORE = base engine
  rebuilt from `d65d13d642`; AFTER = rung-B engine; identical.
- **Measure module IMPORT-INERT** — flags toggled only inside the `_flags` scoped
  context manager, never at module top level.
- **BUILD SAFETY.** Canonical `.so` md5 **`66b8532ca658b0edc7fcf82eec869ef6`**
  verified untouched before/after every build and at final commit. Worktree `.so`
  a real file, built via `scripts/engine_build.sh`. **CANONICAL NEEDS REBUILD ON
  MERGE.**
- `source_match`: **own**.
