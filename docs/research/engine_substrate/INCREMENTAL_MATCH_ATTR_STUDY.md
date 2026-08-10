# Frontier-incremental `mv_relax` — engine map + minimal byte-identical change

READ-ONLY study. Goal: make the Bellman-Ford flood (`mv_relax` in
`seeds/bigville_move_nav.json`) re-evaluate only the *frontier* (cells adjacent
to a cell whose `gdist` just changed) instead of re-scanning ALL `(c,adj,n)`
pairs every pass, producing a **byte-identical** fixpoint (a perf mirror).

All cites are `path:line` against the tree at study time. Nothing here was edited.

---

## Sec 1 — the run_rules loop + the dirty model (per-RULE, not per-binding)

There are **two** `run_rules` implementations. The one the move world hits is the
**Substrate method**, not the free function.

- **Free function** `rewrite::run_rules` / `run_rules_opts`
  (`runners/dsl/src/rewrite.rs:1940`, `:1964`). Loops rules in order, no dirty
  set, no cursors — every pass re-matches every rule. This drives the *graph-Rule
  store* (productions); the seed-installed rules do **not** use it
  (`substrate.rs:2940-2942` calls it "the twin hook … which the vision seeds do
  not use"). Ignore it for `mv_relax`.

- **Substrate method** `Substrate::run_rules` → `run_rules_opts` →
  `run_rules_opts_filtered` (`runners/dsl/src/substrate.rs:3446`, `:3496`,
  `:3500`). This is what `bigville_move_world.py:158` calls. Its pass structure:
  1. force-dirty `reads_external` rules (`substrate.rs:3563-3572`) — n/a here.
  2. fast-exit if **no active rule's dirty bit is set** (`:3579-3586`).
  3. snapshot the dirty set into `to_try` (`:3599-3612`), **clear those bits**
     (`:3628`), then for each `rule_idx` in `to_try` call
     `attempt_one_rule(rule_idx)` (`:3632-3637`).
  4. exit when a whole pass makes no progress (`:3638-3642`).

**The dirty model is PER-RULE, not per-binding.** The dirty set is
`rule_dirty: Vec<bool>` — one bit per rule (`substrate.rs:77`). When a rule's
dirty bit is set, `attempt_one_rule` re-derives **the rule's ENTIRE binding
set** (subject to the semi-naive cursor, sec 2), never a specific affected
binding. There is no per-binding dirty structure on the default path.

`attempt_one_rule` (`substrate.rs:2267`+, dispatch body at `:2958-3140`) picks
one of four evaluation strategies, in this priority:
```
if rule.batch                 → batch_apply_rule          (substrate.rs:2958)
else if try_predicate_retraction(idx).is_some()           (substrate.rs:2986)  ← rung B
else if try_incremental_match(idx).is_some()              (substrate.rs:2991)  ← rung A / semi-naive cursor
else  → cold full re-match (snapshot all bindings, fire each once) (substrate.rs:2994-3139)
```
After a rule progresses, `dirty_by_writeset(rule_idx)` (`substrate.rs:3151`)
decides which rules' bits to re-set for the next pass, and whether to invalidate
their cursors.

---

## Sec 2 — access analysis + THE EXACT REASON incremental_match doesn't help

### What `mv_relax` derives

`RewriteRule::derive_access` (`rewrite.rs:445-487`) computes, for `mv_relax`
(match `[["c","adj","n"]]`, where reads `gdist[n]`,`gdist[c]`, effect writes
`gdist[c]`):

- `read_set  = { Edge(adj), Attr(gdist) }` — match edge types inserted at
  `rewrite.rs:450-452`; where `Attr` reads collected by `collect_term_reads`
  (`:457-459`, `:619-622`).
- `write_set = { Attr(gdist) }` — effect access at `:460-464`, `:709-712`.
- `reads_any = false`, `writes_any = false` (precise; no opaque Term).
  So `mv_relax` is **NOT** flagged `reads_any` — it gets a precise read_set. It is
  never "opaque / always-dirty".
- `batch_safe = false` — `derive_access:477-480` requires
  `read_set.is_disjoint(&write_set)`, and `mv_relax` reads *and* writes
  `Attr(gdist)`. So `mv_relax` runs on the **cold / incremental** path, not
  `batch_apply_rule`.

### The dirtying chain when `mv_relax` fires

`mv_relax`'s `gdist` write is a **rule effect**, applied by
`apply_rule_full` → `Effect::SetAttr` → `graph.set_node_attr(nid,key,v)`
(`rewrite.rs:1581-1588`; graph choke point `graph.rs:747`). It writes the graph
**directly** — it does **NOT** go through `Substrate::set_attr`. Dirtying happens
afterwards, once, in `dirty_by_writeset(mv_relax)` (`substrate.rs:1190`):

- `writes_any` is false, so it takes the write-set loop (`:1204-1270`).
- For consumer `j = mv_relax` itself: `read_set` contains `Attr(gdist)` ⇒
  `hits_attr = true` (`:1245-1247`), `has_where = true`. So
  `attr_flip = (hits_attr && has_where) = true` (`:1260`), and the branch at
  `:1266-1268` **clears `mv_relax`'s cursor** (`self.rule_cursors[j].clear()`)
  and re-sets its dirty bit (`:1265`).

The comment at `:1249-1256` states exactly why: an attr write can flip a
where-clause on an **already-matched (stable) edge**, and the semi-naive cursor
only re-scans NEW edges, so the only correct thing the committed engine can do is
**clear the cursor → force a full re-match**.

### Why `set_incremental_match(True)` is a no-op here

`incremental_match` (block 192000, `substrate.rs:237-260`) changes **exactly one
thing**: the version a cursor is validated against — `cursor_version`
(`substrate.rs:948-954`) returns the **per-edge-type** `edge_delete_version_by_type`
instead of the single global `edge_delete_version`. That only matters when
**deletes** of *other* edge types would otherwise invalidate an unrelated
cursor.

The `mv_relax` flood performs **zero deletes** — it only writes the `gdist`
attr. So per-type vs global delete-versioning is identical (both unchanged), and
`incremental_match` has nothing to act on. Meanwhile `dirty_by_writeset` has
**already cleared the cursor** on every fire (above), so
`try_incremental_match` (`substrate.rs:2547`) finds no valid cursor and the pass
falls through to the **cold full re-match** — enumerating all `adj` edges — every
single pass. Bellman-Ford ⇒ ~diameter passes × full `E(adj)` enumeration ⇒ the
~103 ms.

**THE EXACT REASON = (b)+(c) combined, precisely:** dirtying is per-RULE, and a
rule's own precise `Attr(gdist)` write hits its own where-reading `read_set`, so
`dirty_by_writeset:1266-1268` **clears `mv_relax`'s cursor**, forcing a full
`adj` re-scan next pass. `incremental_match` only alters cursor *delete*-version
validation, which a delete-free flood never exercises — so it changes nothing.
It is **not** (a): `mv_relax` is precise, not `reads_any`.

### Why `set_binding_projection(True)` is a no-op here

`binding_projection` (block 188000) dedups a binding set on the variables the
where/effects actually reference, and only applies when
`RewriteRule::project_vars` is `Some` — i.e. some match var is referenced
**nowhere** (`derive_projection`, `rewrite.rs:492-537`). `mv_relax` references
**both** `c` and `n` (n in the where and in the effect value; c in the where and
as the effect target), so `any_unused = false` ⇒ `project_vars = None`
(`:519-535`). The flag reads nothing for this rule. No effect.

---

## Sec 3 — existing per-binding machinery (block 194000) and its trigger coverage

There **already is** node-seeded, per-binding, attr-triggered re-evaluation —
**`predicate_retraction`** (block 194000, "ladder rung B"). It is the exact
shape this task wants, and it is byte-identity + falsifier gated. It is a
**different flag** from the two the measurement enabled, and it currently has a
**coverage hole** that stops it firing during a rule-effect flood.

Structures / flags:
- `predicate_retraction: bool` (default false) + `predicate_retraction_unsound`
  falsifier (`substrate.rs:261-279`); toggles `set_predicate_retraction`
  (`:928-937`), PyO3 `set_predicate_retraction` (`py.rs:3265`).
- `rule_dirty_nodes: Vec<FxHashSet<NodeID>>` — per-rule set of externally-written
  nodes since last visit (`substrate.rs:283`).
- `rule_pred_retract_ok: Vec<bool>` — per-rule static eligibility, computed in
  `add_rule` (`substrate.rs:2167-2179`): has a where, k≥1 match edges, no
  repeated edge type, not `reads_external`, and **add-only effects** (`AddEdge /
  AddNode / AddNodeIfAbsent / SetAttr / SetAttrIfDifferent`).
  **`mv_relax` satisfies all of these** ⇒ `rule_pred_retract_ok = true`.

The re-evaluator `try_predicate_retraction` (`substrate.rs:2413-2545`):
1. bails to full rescan unless the flag is on, the rule is eligible, and
   `rule_dirty_nodes[idx]` is **non-empty** (`:2414-2424`).
2. validates every match-edge cursor is unchanged (version match AND no new
   edges) — else clears and falls through (`:2430-2441`). For `mv_relax` the
   `adj` edges are static, so this always holds.
3. **MATCH PHASE**: for each dirty node `d`, drives from edges **incident to `d`**
   (`out_edges_slice`/`in_edges_slice`, O(degree(d))), seeding `d` at *both*
   endpoints across every match position, solving the rest of the pattern
   (`:2457-2511`). This is the frontier: only bindings touching a changed node.
4. **APPLY PHASE**: dedup by canonical binding key, apply add-only effects once,
   undo genuine no-ops (`:2513-2533`) — so no-progress detection stays intact.
5. re-stores cursors at current (unchanged) lengths/versions (`:2535-2543`).

**The trigger coverage hole (why rung B does NOT help the flood today):**
`rule_dirty_nodes` is populated **only** by `mark_node_predicate_dirty`
(`substrate.rs:1458-1483`), which is called **only** from `Substrate::set_attr`
(`substrate.rs:1438-1441`) — i.e. an **EXTERNAL host attr write**. A rule-effect
attr write (`mv_relax`'s own `gdist` write) goes through
`graph.set_node_attr` + `dirty_by_writeset`, which **never** touches
`rule_dirty_nodes` and instead **clears the cursor** (sec 2). So during a
`run_rules` flood, `rule_dirty_nodes[mv_relax]` stays empty,
`try_predicate_retraction` returns `None` at `:2420-2424`, and even with
`predicate_retraction` ON the flood falls to full re-match.

Confirmed by the measurement harness `scripts/predicate_retraction_measure.py`:
it only ever flips attrs via `s.set_attr(...)` (host writes, line 92) and its
covered shape is an **external** stable-edge attr flip (module docstring
lines 7-13). No test exercises rung B on a **rule-effect** write. Nothing in
`worlds/` or `scripts/bigville*` enables `predicate_retraction` at all — the
move world instead sidesteps re-flooding with a Python `_field_cache`
(`bigville_move_world.py:131-163`), but the **first** flood per goal is still the
full O(cells×passes) Bellman-Ford this study targets.

---

## Sec 4 — THE MINIMAL BYTE-IDENTICAL CHANGE

**Chosen option: (ii) extend the existing rule-effect dirty path to seed the
already-built node-seeded re-evaluator** — i.e. teach `dirty_by_writeset` the
`mark_node_predicate_dirty` move for rule-effect attr writes. This reuses
`try_predicate_retraction`, its eligibility, cursor-keep, dedup, no-op-undo,
byte-identity gate, and falsifier **verbatim**. It is strictly smaller and safer
than building a new per-node dirty set (option i) or a separate frontier
worklist (option iii), both of which would duplicate machinery that already
exists and already has a falsifier.

The ONLY genuinely new bookkeeping is **capturing which node ids a rule effect
wrote**, because `dirty_by_writeset(fired)` today knows the fired rule's
write-*keys* (`write_set`) but not the written *nodes*. Two contained edits:

**Edit A — capture written attr nodes (one choke point).**
`graph.set_node_attr` (`graph.rs:747`) is the single point every rule-effect
attr write passes through. Add an opt-in log
`Vec<(NodeID, Sym)>` on `TypedGraph`, pushed here, populated **only when a
Substrate-set mirror flag is on** (mirror of `predicate_retraction`, set in
`set_predicate_retraction`). This parallels the existing `pending_*` queues on
`TypedGraph` (`graph.rs:258-286`) that the Substrate already drains between
passes. Gating the push keeps the default path (flag off) byte- and
cost-identical. (The written node is also present in
`UndoStep::AttrSet{nid,key,old}` — `rewrite.rs` UndoStep enum ~`:768-790` — but
the progressing outcome's undo log is dropped inside each sub-path, so the
graph-level log is the single-site capture, not a multi-site one.)

**Edit B — seed rung B from the rule-effect path.**
In `dirty_by_writeset` (`substrate.rs:1190`), in the precise write-set loop,
when `self.predicate_retraction` is on: for a consumer `j` with
`rule_pred_retract_ok[j] && !reads_any` whose `read_set` intersects a written
`Attr(key)`, **instead of** clearing `j`'s cursor (`:1266-1268`), drain the
Edit-A log and `rule_dirty_nodes[j].insert(nid)` for each written node,
**keeping** the cursor — exactly what `mark_node_predicate_dirty:1470-1481`
does for the external path. Uncovered consumers keep the committed
cursor-clear (byte-identical). This makes the rule-effect path and the external
path symmetric — the same symmetry `add_rule:2114-2131` already established for
edge-read dirtying.

Then `attempt_one_rule`'s existing dispatch (`substrate.rs:2986`) routes
`mv_relax` into `try_predicate_retraction`, which now finds a non-empty
`rule_dirty_nodes` and re-evaluates only the frontier.

**Behind which flag:** the **existing `predicate_retraction`** flag (default
false). No new public toggle. The `binding_projection` / `incremental_match`
flags are irrelevant to this rule and need not be touched.

**Blast radius:**
- **Default (flag off): byte- and cost-identical.** Edit A's push is gated;
  Edit B's branch is inside `if self.predicate_retraction`.
- **Edge/Type-triggered rules: unchanged.** Edits touch only the precise
  `Attr(key)` write branch; structural (Edge/Type) writes still dirty +
  keep/clear cursors exactly as before (`dirty_by_writeset:1242-1244,1257-1259`).
- **`reads_any` / `writes_any` rules: unchanged** — excluded by
  `!reads_any` and by the `writes_any` early blanket-dirty (`:1191-1202`).
- **Other substrates: opt-in only** — nothing changes unless a caller enables
  `predicate_retraction`. The move world would enable it (or a narrow
  flood-only wrapper would).
- **Rules ineligible for rung B** (has delete effects, repeated edge type, no
  where, `reads_external`) are excluded by `rule_pred_retract_ok`
  (`add_rule:2167-2179`) and keep the committed cursor-clear.

---

## Sec 5 — byte-identity risks + verification plan

### Why it stays byte-identical (the argument)

- **Fixpoint uniqueness / order-independence.** `mv_relax`'s guard
  `gdist[n]+1 < gdist[c]` makes every relaxation strictly decreasing; the
  fixpoint is the unique shortest-path field. Node-seeded re-evaluation and full
  re-scan reach the **same** field regardless of visit order (min is
  associative/commutative). `try_predicate_retraction` re-seeds from a changed
  node across **both** endpoints of every match position (`:2467-2510`), so a
  cell newly relaxed as a *neighbour* (`n`) is also re-driven — no frontier
  binding is missed.
- **Float exactness.** `gdist` values are `BIG` then integer distances, exactly
  representable in f64 — no drift. (Contrast the `dirty_overaggressive` "within
  1e-9" falsifier, `substrate.rs:1420-1422`, which is deliberately unsound.)
- **No-op detection intact.** The apply phase undoes non-progressing bindings
  (`:2530-2532`), so run_rules' `!any_progress` termination is unaffected.

### Risks to actively check

1. **Cursor staleness.** Edit B keeps the cursor on an attr write; if any `adj`
   edge changed in the same pass, the kept cursor would be wrong. Mitigated:
   `try_predicate_retraction:2430-2441` re-validates (length + version) and bails
   to full rescan on any mismatch. Verify the flood does no edge mutation (it
   doesn't) and that a mixed edge+attr pass still bails correctly.
2. **Self-write interaction.** `mv_relax` is its own consumer. Confirm the
   written-node set for a fired binding `(c,n)` seeds `c`, and that re-driving
   from `c` re-checks `(c'∈nbr(c), n=c)` so a lowered `gdist[c]` propagates
   outward.
3. **Multi-node / batch-apply.** The cold path fires **all** distinct bindings
   per visit; Edit A must log **every** written node that visit (not just the
   last), else the frontier under-seeds and work is silently lost (the unsafe
   direction, cf. `substrate.rs:219-223`).
4. **Ordering vs the existing `_field_cache`.** The Python cache
   (`bigville_move_world.py:148-163`) restores fields via external `set_attr`;
   ensure the new rule-effect seeding composes with a cache miss (fresh flood)
   and doesn't perturb `_cost_steps` accounting in a way the gate reads.

### Concrete verification plan

Rebuild note: this change **will** rebuild the PyO3 `.so` (current md5
`fd82dc2978dbb055496dd82390ac2ebe`), so re-verify broadly, not just the flood.

1. **New byte-identity gate on the flood itself** (the missing coverage). Mirror
   `scripts/predicate_retraction_measure.py::byte_identity` but drive the writes
   from a **rule effect**, not `s.set_attr`: build the `bigville_move_nav` graph,
   run `mv_relax` to fixpoint with `predicate_retraction` OFF vs ON, and assert
   the **full float-exact `gdist` field is identical**, while `cand_enum`
   (scale_audit) drops from O(passes·E) to O(frontier). Add the unsound-arm
   falsifier (`predicate_retraction_unsound`, `:2446-2450`) and assert it
   **diverges** — the gate must be demonstrably non-vacuous.
2. **Move-world end-to-end diff.** `tests/test_bigville_move_migrated.py`
   (positions/backing/energy curve) and
   `tests/test_nav_field_cache_migrated.py::test_field_cache_is_byte_identical`
   (`:31-36`) must stay green with the flag both off and on — every resident's
   position every tick identical.
3. **Other floods (regression for the shared engine change).** Run with the flag
   off (must be byte-identical to baseline) AND on:
   - `tests/test_predicate_retraction_migrated.py` (rung B external shape — must
     still pass; proves Edit B didn't regress the existing path).
   - `tests/test_incremental_match_migrated.py` (rung A — must be unaffected).
   - `tests/test_quanta_navigation_migrated.py`,
     `tests/test_vision_floor_migrated.py`,
     `tests/test_spatial_routing_migrated.py`,
     `tests/test_arc_ls20_mapnav_migrated.py`,
     `tests/test_active_exploration_migrated.py` — other flood/`qf_*`/nav seeds.
4. **Broad bench.** `pytest tests/ -k migrated` against
   `results/failure_baseline.json`
   (`tests/test_failure_baseline_migrated.py`) — the enumerated node-id baseline;
   assert **no new red node ids** vs baseline (the CLAUDE.md rule: a baseline is
   a list of ids, never a count). Run with `chess` installed and `data/`
   symlinked so the reds are the known 144-145, not the 565 data-absent set.
5. **Perf confirmation.** Time the first `move_one` flood on the real bigville
   grid with the flag on: expect the ~103 ms full-scan flood to collapse toward
   O(frontier). Report **both** the synthetic per-tick `cand_enum` exponent and
   the wall-clock on the real world (synthetic mechanism ≠ benchmark value).

### What determinism to diff

The float-exact per-cell `gdist` field (all `MoveCell` nodes), every
`run_rules` visit; and — for the move world — every mover's `pos` at every tick.
`scale_audit` `cand_enum` / `where_evals` are the **cost** witnesses (they may
differ; that is the point) but must never be part of the identity assertion.
