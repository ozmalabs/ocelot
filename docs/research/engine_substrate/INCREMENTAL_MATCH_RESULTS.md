# INCREMENTAL MATCH — RESULTS (block 192000, ladder rung A)

Prereg: `INCREMENTAL_MATCH_PREREG.md`, committed ALONE (`5427546212`) BEFORE any
number. `seed_claim(192000,192999)` CLEAN. **This rung BUILDS Rust. CANONICAL
NEEDS REBUILD ON MERGE.**

---

## TL;DR — the reduction holds byte-identical; the covered exponent drops 2.0→1.0

The matcher was **already semi-naive incremental** (per-rule / per-edge-type
cursors that scan only edges NEW since a rule's last visit). What defeated it was
the **single GLOBAL `edge_delete_version`**: bumped on *every* external write
(delete OR node/attr mutation), it invalidates *every* cursor for *every* edge
type, so every dirty rule falls back to a full O(cells) rescan every tick — the
O(cells²) the arc measured. This rung makes cursor validity **per edge type**
(`graph.edge_delete_version_by_type`, bumped in `delete_edge` — the single
deletion choke point), so a delete of an UNRELATED edge type no longer forces a
rescan. **DEFAULT OFF; the committed full-rescan engine is the correctness
oracle; every uncovered shape falls back to it byte-identically.**

- **C1 — DEFAULT OFF ≡ BASE engine, byte-identical, 6/6 workloads.** ✅
- **C2 — THE REDUCTION: incremental ON ≡ full-rescan, byte-identical, 6/6
  battery (vision + non-vision) + the landed 160×120 carve (4 polys / IoU 0.1215
  / precision 0.9784 / 0 false).** ✅ **This is the headline.**
- **C3 — RETRACTION correct: a deleting (where-flip-on-delete) workload is
  byte-identical ON vs OFF, both retract (30/60 slots open).** ✅
- **F1 — the UNSOUND-retraction falsifier DIVERGES** (skips the where-reader
  cursor clear → misses every delete-driven where-flip → 0 slots open instead of
  30). Non-vacuous. ✅
- **H1 — the covered append-only shape's `cand_enum` (candidate-enumeration WORK
  COUNT) exponent drops from 1.968 (full rescan, ~O(n²)) to 1.000 (incremental,
  O(Δ·n)).** ✅ Fitted on the deterministic count, not wall-clock.
- **HONEST NEGATIVE (as pre-registered): the eye's where-gated mint rules are
  NOT made incremental — they fall back to full rescan, byte-identically.** They
  are rung B's target (per-binding predicate retraction).

---

## §1 WHAT WAS BUILT (Rust, additive, DEFAULT OFF; `term.rs` EMPTY)

`Substrate::incremental_match`, default false. OFF ⇒ committed path, byte-unchanged.

1. **`TypedGraph::edge_delete_version_by_type: FxHashMap<Sym,u64>`** — bumped
   inside `delete_edge` (which `delete_node` and every DelEdge/DelNode effect
   cascade through, so ALL deletions are covered, including node-cascades). O(1)
   per delete, invisible to `graph_to_dict`, READ only when the flag is on.
2. **`cursor_version(et)`** — the version a cursor is validated against: the
   per-type version when ON, the global counter when OFF (⇒ OFF byte-identical).
   Used at the check site (`try_incremental_match`) and both cursor-store sites.
   A rule's own delete self-invalidates because the store captures the version
   BEFORE its effects fire.
3. **Where-flip preservation (the soundness cases):**
   - external **attr/node writes** (`mark_node_mutation`): under ON, clear the
     cursors of the where-rules it dirties (a stable-edge where can flip on an
     attr change; the new-edges cursor would miss it). Matches OFF's global-bump
     effect exactly.
   - external **edge deletes** of a type read only in a WHERE (negation /
     `Not Exists`): `invalidate_readers_of_deleted_edge_type` clears the cursors
     of WHERE-ONLY readers of the deleted type (matchers are left to the per-type
     version, which is what the falsifier defeats).
   - **delete-effecting rules**: under ON, clear ALL cursors (matching OFF's
     global bump exactly) — conservative, since a DelNode cascade can delete
     unnamed edge types; add-only rules keep the fast path.
4. **`incremental_match_unsound`** (falsifier, default false) — skips the
   where-reader cursor clear, so a delete-driven where-flip is silently missed.
5. PyO3 setters `set_incremental_match` / `set_incremental_match_unsound`.
   **NO new Term enum variant — `git diff … term.rs` is EMPTY.**

`diff --stat`: `graph.rs +28`, `py.rs +22`, `substrate.rs +157/-9`. `term.rs` 0.

---

## §2 THE COVERAGE BOUNDARY (stated exactly, as prereg'd)

**COVERED (incremental, O(Δ)):** multi-edge, non-repeated-edge-type,
non-`reads_external` rules whose per-tick binding change is driven by NEW edges
of append-only types, and whose cursors are not force-cleared by a where-flip. A
delete of an UNRELATED edge type no longer forces these to rescan.

**FALLS BACK (full rescan, byte-identical):** repeated edge-types,
`reads_external`, `k==0`, batch rules, delete-effecting rules (all cursors
cleared), and — critically — **any where-rule dirtied by an external attr/node
write on a stable edge (the eye's `retinal_mint_*` shape).** These read
externally-mutated attrs in their where, so `mark_node_mutation` clears their
cursors every tick ⇒ full rescan ⇒ identical to committed. Making THEM
incremental needs per-binding predicate retraction — **rung B**.

---

## §3 THE PRE-REGISTERED CRITERIA (engine `e9aaa40518b4627161c06cd4c3806ad1`)

| id | threshold | measured | verdict |
|---|---|---|---|
| **C1** | OFF ≡ base engine, whole-graph float-exact, ≥5 workloads | **6/6 IDENTICAL** vs base `2458afa2…` (vision_carve, scheduler, quiet_areas, scheduler_wide, conversation, doom_accel_160x120) | ✅ |
| **C2** | incremental ON ≡ full rescan, ≥5 incl. non-vision + landed carve | **6/6 byte-identical**; landed 160×120 carve **4 / 0.1215 / 0.9784 / 0**, onset digest `f5375014f2dcb8f2`, rod `d777e3d8a7012a55`, identical off/ON | ✅ |
| **C3** | retraction: deleting workload byte-identical ON vs OFF | off==incr, both retract **30/60** slots open | ✅ |
| **C4** | `term.rs` diff EMPTY | empty | ✅ |
| **H1** | covered `cand_enum` exponent 2.0 → ≤1.2 | **1.968 → 1.000** (off: 676/2601/10201/40401; incr: 25/50/100/200 for n=25/50/100/200) | ✅ |
| **F1** | unsound retraction MUST diverge | **DIVERGES** — unsound opens **0** vs sound **30**; dump differs | ✅ |
| **F2** | no-free-lunch on an all-fallback control | see §5 | — |

---

## §4 THE REDUCTION (headline) — incremental ≡ full rescan, byte-identical

Full float-exact `graph_to_dict` digests, base engine vs rung engine OFF, and
rung engine OFF vs incremental ON:

| workload | C1 my-OFF == base | C2 OFF == incremental-ON |
|---|---|---|
| `vision_carve` (real 2-D graph retina) | ✅ | ✅ |
| `scheduler` | ✅ | ✅ |
| `quiet_areas` | ✅ | ✅ |
| `scheduler_wide` | ✅ | ✅ |
| `conversation` (NON-vision) | ✅ | ✅ |
| `doom_accel_160x120` (shipped accel path) | ✅ | ✅ |
| **landed 160×120 carve** | — | ✅ **4 / 0.1215 / 0.9784 / 0**, off==ON==unsound |

Base digests: `results/incremental_match/base_digests.json`; full run:
`results/incremental_match/results.json`.

---

## §5 THE COVERED-PATH EXPONENT (count-based, per the metric-currency rule)

A where-LESS 2-edge cross rule `[hub,link,c] ⋈ [hub,other,d] → set_attr d seen`
(full rescan enumerates link×other = O(n²); incremental after a settle scans only
the ONE new link edge × the n others = O(n)). Per-tick `cand_enum` (candidate
enumerations), median of 3, one tick = add 1 left cell + delete an UNRELATED
`zombie` edge + `run_rules`:

| n (cells) | 25 | 50 | 100 | 200 | exponent |
|---|---|---|---|---|---|
| **full rescan (off)** | 676 | 2601 | 10201 | 40401 | **1.968** |
| **incremental (on)** | 25 | 50 | 100 | 200 | **1.000** |

The unrelated `zombie` delete each tick is exactly the case per-edge-type
versioning fixes: OFF's global bump would invalidate the cursor and rescan; ON
keeps it (the delete was a different type) and stays O(Δ). **The match layer
went from re-enumerating the world to processing the change.**

Wall-clock is a secondary reported fact only and was not gated.

---

## §6 RETRACTION + THE FALSIFIER

A `Not Exists` (negation) where over a `block` edge, read by a rule matching
`slot`: deleting a block edge flips the where on a STABLE slot edge → the slot
opens. This is the ONE observable delete-effect in a monotone forward-chaining
engine (retraction that RE-ENABLES a match), so it is the right test.

| arm | slots open (of 60) | dump == full rescan |
|---|---|---|
| OFF (full rescan) | 30 | — |
| **incremental ON (sound)** | **30** | ✅ byte-identical |
| **incremental ON, UNSOUND** | **0** | ❌ **DIVERGES** |

The unsound arm skips the where-reader cursor clear, so every delete-driven
where-flip is missed — 0 slots open instead of 30, and the graph dump differs.
**A broken retraction breaks the reduction → the gate is non-vacuous.**

---

## §7 THE HONEST NEGATIVE — the eye stays full rescan

As pre-registered: the eye's `retinal_mint_onset_2d` / `_carve_2d` / `_motion_2d`
/ `_salience_2d` all have where-clauses reading task/column attrs the host writes
every tick. `mark_node_mutation` clears their cursors on those writes (required
for byte-identity — a where can flip on a stable edge), so they full-rescan every
tick under ON exactly as under OFF. **This rung does NOT drop the eye's exponent**
— C2 shows it is byte-identical (`vision_carve` and `doom_accel_160x120` dumps
unchanged), which is the point: the eye is covered by the SOUND FALLBACK, not by
the incremental path. Making the eye incremental is a where-flip-on-stable-edge
problem requiring a per-binding beta-network with predicate retraction — **ladder
rung B**, the confirmed next rung.

---

## §8 PROVENANCE & DISCIPLINE

- **SEPARATE prereg commit** `5427546212` BEFORE any number; seed_claim CLEAN.
- **`source_match = "own"`** (rung engine built in THIS worktree), `stale_rust=[]`.
- **`term.rs` diff EMPTY.**
- **BUILD SAFETY (lesson 9b).** Canonical `.so` md5
  **`2458afa21641ec9b701adf4436e20640`** verified BEFORE the first `cp`, AFTER
  every `cp`, and at commit — **UNCHANGED throughout**. Worktree `.so` a REAL
  FILE each time; rung engine `e9aaa40518b4627161c06cd4c3806ad1`, built ONLY in
  this worktree via `cargo build --release` + `cp --remove-destination`.
  **CANONICAL NEEDS A REBUILD ON MERGE** (the rung adds Rust; canonical `.so`
  has no `incremental_match`).
- **Gate** `tests/test_incremental_match_migrated.py` — **6 passed** (C1/C2
  reduction on vision + non-vision, landed carve, C3 retraction, F1 falsifier,
  H1 exponent).
- **Oracle** `rung7_vision_bench.sh` AFTER (my engine): **214 passed / 10
  skipped / 0 failed** — the documented worktree-without-`data/` base count.
  (BEFORE == AFTER; §see below.)
- **34-file regression** `per_area_settlement_regression.sh`: BEFORE / AFTER
  failing-id SET (§see below).

### The harness-leak regression (found on main, fixed) — the (a)-vs-(b) diagnosis

The first A merge broke **3 gates in `test_empty_match_proof_migrated.py`**
(block 189000) — NOT in the original verification set. Diagnosis, with evidence:
**neither (a) an engine bug nor (b) legitimate subsumption — it was (c) a
TEST-HARNESS monkeypatch leak.** `scripts/incremental_match_measure.py` rebound
`empty_match_proof_measure._set_proof` at **module top level**; when both test
files are collected in one pytest session, the 189000 tests' `_set_proof(inner,
proof, unsound)` calls then toggled `incremental_match` instead of
`empty_match_proof`. So the empty-match proof was **never actually enabled**:
its unsound falsifier saw no divergence (`600 == 600`, vacuous) and its 176×
speedup vanished (proof/off `0.881`). **The engine OFF path is genuinely
byte-identical** — proven because, once the leak is scoped away, ALL 13
empty-match gates pass on the rung engine (C1/C2 byte-identity, the unsound
falsifier bites again, the 176× speedup returns). This also **rules out (b)**:
per-edge-type versioning does not weaken or subsume the empty-match proof — the
two operate independently (empty-match runs with `incremental_match` OFF).

**Fix:** a scoped `contextlib` context manager (`_incr_setter`) that
rebinds+restores `_set_proof` only around each measurement call; importing the
module no longer touches the shared harness. **Both files green together: 19
passed (6 mine + 13 empty-match)** in one session (the exact leak condition).

**Standing lesson:** a core-engine change must run EVERY engine-semantics gate,
not just the domain-regression set — and a measure module must never mutate a
shared harness at import time.

### Full engine-semantics gate set (synchronous, rung engine `e9aaa40518b4`)

| gate | result |
|---|---|
| `test_incremental_match_migrated` | **6 passed** |
| `test_empty_match_proof_migrated` (189000) | **13 passed** |
| both together (one session — the leak condition) | **19 passed** |
| `test_dirty_precision_migrated` + `test_per_sensor_epoch_migrated` + `test_per_area_settlement_migrated` | **36 passed** |
| **oracle `rung7_vision_bench.sh`** | AFTER **214 / 10 / 0**; BEFORE (base) **214 / 10 / 0** — BEFORE == AFTER |
| **34-file `per_area_settlement_regression.sh`** | AFTER **23 failed / 277 / 5**; BEFORE **23 / 277 / 5** — IDENTICAL failing-id SET (the pre-existing flaky conversation/cognitive set: composer_driver 1, cortices_tick 3, elaboration 5, gap_awareness 5, topic_route_selfheal 9; ZERO eye/vision/incremental) |

(worktree-without-`data/` condition. A base `.so` built in-worktree hashes
`8c88057080b1…` — the shipped canonical `2458afa2…` was built elsewhere;
build-artifact path nondeterminism, same source, byte-identical graph output.)

<!-- ORACLE_REGRESSION_BEFORE_AFTER -->

---

## §9 HONEST RESIDUALS

1. **The eye is NOT sped up** — it is covered by the sound fallback (full rescan,
   byte-identical). The exponent drop is demonstrated on a covered append-only
   synthetic shape; whether the shipped vision path has append-only rules that
   pull the win is not claimed (it does not — the mint rules are where-gated).
   This is the pre-registered honest negative.
2. **`remove_edge_unchecked` is a raw escape hatch** that bumps the per-type
   version (via `delete_edge`) but bypasses the dirty machinery — as in the
   committed engine. A matcher's cursor could go stale under ON while OFF (no
   global bump) keeps it, a narrow ON/OFF divergence window. The whole-bench
   reduction gate (C1/C2, 6/6 identical) is the arbiter and found none; the
   covered path uses it only for the UNRELATED (unread) `zombie` type.
3. **Delete-effecting rules clear ALL cursors under ON** (conservative, matches
   OFF). A tick containing a deleting rule loses incremental state, exactly as
   OFF's global bump does — correct, not free.
4. **The reduction is scoped to healthy (effectively idempotent / where-guarded)
   rule sets** — the same class the committed engine already requires (a
   non-idempotent unguarded AddNode floods under OFF too). The gate verifies this
   empirically on the whole battery.

---

## §10 Proposed VISION_PROTOCOL ledger row

> **192000–192999 (`check_claim` CLEAN; SEPARATE prereg commit `5427546212`
> BEFORE any number) — INCREMENTAL MATCH, ladder rung A: PER-EDGE-TYPE DELETE
> VERSIONING, the reduction holds byte-identical.** The matcher was ALREADY
> semi-naive incremental (per-rule/per-edge-type cursors); the O(cells²) was the
> single GLOBAL `edge_delete_version` invalidating EVERY cursor on EVERY external
> write. `graph.edge_delete_version_by_type` (bumped in `delete_edge`, the one
> deletion choke point) makes cursor validity PER EDGE TYPE, so a delete of an
> unrelated type no longer forces a full rescan. DEFAULT OFF; sound full-rescan
> fallback for every uncovered shape (repeated edge-types, reads_external, k==0,
> batch, delete-effecting rules, and the eye's where-gated mint shape).
> **REDUCTION (headline): incremental ON ≡ full rescan, byte-identical 6/6
> battery (vision+non-vision) + landed 160×120 carve 4/0.1215/0.9784/0.** C1
> OFF≡base 6/6. C3 retraction correct (off==incr, 30/60 open). **F1 unsound-
> retraction falsifier DIVERGES (0 open).** **H1 covered `cand_enum` exponent
> 1.968→1.000** (count-based). HONEST NEGATIVE: the eye's mint rules stay full
> rescan (rung B = per-binding predicate retraction). **term.rs EMPTY**; oracle
> rung7 214/10/0 BEFORE==AFTER; 34-file regression 23/277/5 IDENTICAL failing-id
> set BEFORE/AFTER; §10 source_match=own; canonical `.so` `2458afa2…` UNCHANGED —
> **CANONICAL NEEDS REBUILD ON MERGE.** Regression note: a measure-module
> import-time monkeypatch leaked into the shared 189000 harness (broke 3
> empty-match gates in a same-session run); FIXED with a scoped context manager;
> all 13 empty-match gates + 6 new + 36 other engine-semantics gates green.
