# Incremental perception redesign (jabberwock-authored, 2026-06-20)

The fundamental design for O(changed)-after-turn-1 perception. Authored by the
agent via claude_teacher in response to "ask the jabberwock about the fundamental
design of the overall solution". Oracle: scripts/perception_incremental_oracle.py
-> var/perception_oracle.json (the parity target).

---

I've now read the real pipeline end to end — adapter, seeds, and the Rust engine. I have everything I need. Here is the diagnosis and the redesign.

---

## What the code actually does (the anti-pattern, confirmed)

The agent **already holds a persistent world model** and then throws it away every frame:

- `ingest` (`world_adapter.py:2839-2865`) keys every world node by `(type, id)` into a persistent `WorldInstance`. Unchanged cells **dedup to the same node** (that's why node count is flat at ~11,760). Cross-frame identity already exists on the agent side.
- But the *type* carries the value (`CellC<v>`), so a value change mints a fresh instance and the position-hygiene pass (`:2873-2885`) deletes the old one — identity is silently broken exactly at the cells that change, the `within` edge to its Region is lost, and the persistent model can't be updated in place.
- `build_world` (`arc.py:106-134`) re-emits all 4096 cells + the full 4-neighbour lattice every turn, even though it *also* already computes the `changes` list and mints `ChangeEvent` nodes (`arc.py:121-143`). The deltas are right there, unused for perception.
- `perceive_frame` (`world_adapter.py:4069-4080`) then re-stamps `cc_label` on **all** cells, re-floods from scratch, and re-stamps `cc_ready` on **all** cells.
- On `tick`, `cc_materialise` matches `[game has_cell cell]` — **all 4096 edges** — gated by a `cc_ready` where-clause; Regions are minted *fresh per frame* (gated by `frame`); `region_correspondence` re-pairs this frame's Regions against last frame's (`avatar_agency.json`); `mark_floor` re-scans all cells.

And here is **why the engine's incremental machinery can't save it**, precisely: the all-cells `self.inner.set_attr(...)` loop routes through `mark_node_mutation` (`substrate.rs:419-422` → `290-305`), which on **every** call bumps `edge_delete_version` and dirties **every** where-rule. That invalidates the semi-naive cursors (`run_rules` cold path `:1333-1408`), so `cc_materialise` falls back to a full re-match over all 4096 `has_cell` edges. The seed *defeats* the engine by re-touching every cell. (`relax_to_fixpoint` itself is innocent — it writes via `graph.set_node_attr` directly, `py.rs:2090-2092`, no dirtying.)

---

## (A) The fundamental design — the one central idea

> **Stop re-perceiving. Perception is the in-place application of the frame's `ChangeEvent`s to a standing world model — re-label only the changed cells and their flood frontier, repair only the Regions those cells touch, and *move* a figure-Region rather than re-deriving it — with every perception rule driven by the `has_change` relation (the ~6 genuinely-new edges), never by `has_cell` (the 4096 standing edges).**

Identity is **carried**, not rediscovered. Cost is bounded by what changed, not by the grid. Positions on the five axes:

**1. Persistent world model — yes, decisively.** The agent owns one standing set of `Cell` nodes, the static `neighbour` lattice, persistent `Region`s, and the map. The world delivers **deltas** after frame 0 (full grid once, to seed the model; thereafter `Game`/`Body` attr updates + `ChangeEvent`s + `Action` only; the lattice is static and never re-emitted). Emitting deltas is *still a pure pipe* — diffing `prev_grid` against the current frame is mechanical I/O translation (the world already does it at `arc.py:121-124`), and a `ChangeEvent{frm,to,row,col}` is a faithful statement "this pixel changed," not a relevance judgment. The agent still decides what the change *means*. The current full-snapshot re-ingest is the thing to drop.

**2. Incremental connected components — seeded flood from the change frontier, identity in the Region node.** A flat re-flood is O(cells) and unnecessary. The correct incremental update: a changed cell (a) leaves its old Region, (b) joins the Region its new same-value neighbours already belong to (read `within` off a neighbour — one hop), (c) starts a new Region if it has no same-value neighbour. **Merge** (a cell bridges two same-value Regions) and **split** (a cell's departure disconnects a Region) are the only non-local cases, and they are rare and *bounded*: re-flood **only the affected Region's cells** with `relax_to_fixpoint` over the subset — which it already supports (it reads out-of-subset neighbour labels, writes only the subset). For the headline workload — a rigid figure stepping one cell — there is no merge/split at all; it's pure membership rewrite. So: incremental CC is the right framing for correctness, but the *common* path is even cheaper (membership join via a neighbour's `within`), and the subset-flood primitive already exists for the rare structural case.

**3. Region identity over time — the Region node IS the identity; `region_correspondence` is deleted.** A `Region` is persistent. Its `cells`/`count`/`centroid`/`bbox`/`shape` are updated in place when its membership changes. Motion (`drow`/`dcol`) is the centroid delta of *the same Region* between frames — not a fresh-Region-paired-to-old-Region search (which is O(regions²) today). `avatar_votes` accrue on the persistent figure-Region; the `controls` edge attaches once and stays. Lifecycle: **appear** = new Region (a changed cell with no same-value-Region neighbour); **vanish** = `count`→0, delete; **merge/split** = the bounded subset re-flood above. This removes `region_correspondence` and `cc_prune_old_regions` entirely.

**4. Rule firing discipline — anchor on `has_change`, not `has_cell`.** This is the lever that makes the engine's existing machinery work *for* us. A rule matching `[game has_change ce]` sees a relation with ~6 edges; even a full re-match is O(changed). The `ChangeEvent`s are genuinely new each frame, so the semi-naive cursor sees exactly the delta. Mutations happen as **rule effects** (driven by `has_change`), which wake consumers via the *precise* `dirty_by_writeset` path (`substrate.rs:313-328`, `:1416`) — not the coarse `mark_node_mutation`. The adapter does **zero** per-cell `set_attr`, so the only external mutation per frame is the ~6 `ChangeEvent` ingests + the `Game.frame` bump. The division of labour: the **engine** already gives O(Δedges) matching via cursors + writeset waking; the **seed** just has to stop anchoring on the big relation and stop re-stamping every cell. The seeds were defeating an engine that was already correct.

**5. New Rust — essentially none.** Everything is expressible in the existing DSL + effects (`set_attr`, `add_edge`, `del_edge`, `add_node_if_absent`, `del_node` all exist; `relax_to_fixpoint` already takes a subset). There is **one tiny latent engine bug** to fix, not a new primitive: `add_edge_unchecked` (`py.rs:2270-2272`, the path `ingest` uses) inserts the edge but **never calls `mark_edge_type_dirty`** — so a `has_change`-reading rule with no where-clause would not wake. Today this is masked by the all-cells `set_attr` storm dirtying everything. Once that storm is gone, `add_edge_unchecked` must wake its consumers. Fix: make it call `mark_edge_type_dirty(et)` (one line — unchecked edges should still wake readers; the "unchecked" refers to *admissibility*, not *observability*). That is the whole Rust change.

---

## (B) Concrete graph-native realization

**World adapter (`worlds/arc.py build_world`) — stays a pure pipe, emits deltas:**
- Frame 0 (and on `Reset`): emit the full grid **once** as persistent `Cell` nodes keyed by **position** (`id="{r}_{c}"`), with `value` as a *mutable attr* — **not** in the type. Emit the static `neighbour` lattice once. (The CC flood already reads `value` as an attr — `region_grouping.json` `cc_relax_step` compares `Attr(n,"value")` — so nothing in perception depends on `CellC<v>` typing.)
- Frame N>0: emit only the `Game`/`Body` attr updates, the `ChangeEvent`s (already minted, `arc.py:138-143`), and the `Action`. No cell loop, no lattice. `build_world` itself becomes O(changed).
- The handful of navigation productions that key on `CellC4`/`CellC9` (`arc3_navigation.json:18-65`) move from type-match to a `value`-attr where-clause (`value==4` wall, `value==9` avatar). Mechanical seed edit; removes the node-churn-on-value-change problem at its root and means **cell identity is position-stable**, so `within` survives a value change.

**`perceive_frame` (`world_adapter.py:4056`) — collapses to ingest + tick:**
- Delete the all-cells `cc_label`/`cc_ready` restamp loop (`:4069-4079`) entirely. The adapter ingests the deltas and calls `tick()`. That's it — a pure sequencer, as the architecture law wants. All labeling now happens inside rules.

**New/changed seeds (the agent's perception, as graph data):**

1. `region_grouping` (rewrite): replace `cc_materialise`'s `[game has_cell cell]` driver. New rule `cell_joins_region` matches `[game has_change ce] [ce at_cell cell] [cell neighbour nb]`, where `value(nb)==value(cell)`, effect: `add_edge cell within Region-of(nb)` (read via `nb within region`) and remove the stale `within`. A companion `changed_cell_new_region` (add_node_if_absent keyed on the cell's own min-id) fires when no same-value neighbour has a Region. Both are O(changed × 4). Keep `cc_relax_step` only for the rare merge/split subset re-flood, seeded from the affected Region's cells.
2. `region_grouping` (bounds): `cc_region_bounds` stays *structurally* (it computes count/centroid/bbox/`shape_descriptor` over `InNeighbours(region, within)`), but its match changes from "every Region this frame" to **only Regions whose membership changed this frame** — mark a Region `dirty` as an effect of `cell_joins_region`, and match `cc_region_bounds` on that dirty flag (cleared after). Unchanged Regions keep their attrs; their rules never re-fire (the engine's cursor + writeset waking now does exactly the right thing).
3. `avatar_agency`: **delete `region_correspondence`** and the fresh-Region machinery. `avatar_vote`/`avatar_confirm` now read `drow`/`dcol` off the **persistent** figure-Region (centroid delta, set by `cc_region_bounds` when its membership shifted). `controls` and `MotorEffect` attach to the persistent Region. Drop `cc_prune_old_regions`.
4. `arc3_navigation`: `mark_floor_as_location` and `max_region_count` fire only when the floor Region's membership changed (same dirty-flag gate) — for a moving figure inside a static room, the floor is unchanged, so the map is **not rebuilt** at all after frame 1.
5. A small `prune_consumed_changes` rule: `del_node` `ChangeEvent`s with `frame < game.frame`, so `has_change` stays at the current frame's ~6 edges (keeps the cursor re-match O(changed)).

**Rust:** the one-line `mark_edge_type_dirty` in `add_edge_unchecked` (`py.rs:~2272`). Nothing else.

---

## (C) Parity verification — the incremental model must equal the full re-perceive

The redesign must produce the **same** Regions, bounds, avatar discovery, and map as today. Verify by an **equivalence harness, not a rewrite of the bench**:

1. **Golden trace.** Take a real ls20 episode (the `arc3_live_env` capture). Run **today's** full-re-perceive `perceive_frame` and snapshot, per frame: the set of Regions as **canonical sets of member positions** (identity-independent), each Region's `count/cy/cx/h/w/sd`, the `controls` edge target (as a position-set), each `MotorEffect{action,drow,dcol}`, and the set of `SpatialLocation` cells. This is the oracle.
2. **Incremental run.** Run the new delta-driven pipeline over the identical frame sequence; take the same snapshots.
3. **Assert frame-by-frame equality** of: (a) the partition of cells into Region position-sets (merges/splits included — this is the strict CC-correctness check); (b) every Region's bounds attrs (centroid/bbox/shape, within fp tolerance for `sd`); (c) the avatar's controlled position-set and the learned `MotorEffect`s; (d) the `SpatialLocation` set. Region *node identity* differs by construction (that's the point), so compare by position-set, not NodeID.
4. **Adversarial frames** to exercise the non-local cases the moving-figure happy path skips: a figure that **splits** (a wall removed mid-body), two figures that **merge**, a figure that **vanishes** (recolored to background), and a figure **appearing**. These are where incremental CC can silently diverge; the partition-equality assert catches it.
5. **Cost assertion** (the actual goal): assert `inner.run_rules` touches O(changed) bindings after frame 1 — instrument the per-rule match count and assert `cc`/region rules see ≤ k·|ChangeEvents|, not |cells|. Frame-1-onward wall-clock should drop from ~15s to the single-digit-ms range; frame 0 stays O(cells) (cold flood, expected).

Pass = identical perception, O(changed) cost. That is the design: one persistent model, deltas applied in place, identity carried, rules anchored on the change set — and the engine's existing incremental machinery finally doing the work it was built for.

---

One note before you act on this: it changes the cell-typing contract (`CellC<v>` → `Cell` + `value` attr) and deletes `region_correspondence`, so the `arc3_game`/`shape_sense`/routing seeds that read those need a sweep. Want me to (a) write the equivalence harness in (C) first against the current pipeline so we have the oracle locked before touching seeds, or (b) draft the reworked `region_grouping` + `avatar_agency` seeds and the `arc.py` delta emitter? I'd do (a) first — the oracle is what makes the rest safe.

---

## Lesson learned — fixpoint idempotence (oscillation bug, 2026-06-20)

The Stage-2a rules were correct but frame-0 `run_rules` never reached a fixpoint
(steps climbed without bound while Regions were already correct). Recorded as a
durable `TaughtHint` the agent boots with (`seeds/rule_authoring_lessons.json`).

**Invariant:** a Rule on the fixpoint engine must be a NO-OP when re-fired on the
same binding — either its `match`+`where` goes false after its own effects
(self-disabling, like a `del_edge` that removes the matched edge), or every effect
is idempotent. The trap: a non-idempotent `set_attr` (RHS reads its own target, or
writes a flag another Rule resets) on a binding that stays matchable — two Rules
flip the value forever, both "progressing".

**Detect statically** (no engine run): (1) any `set_attr` whose RHS reads its own
target (`x=f(x)`); (2) any `(var, attr-key)` written by ≥2 Rules with neither gated
on a monotone stamp → a producer/consumer flip.

**Worst form** — an accumulator (`b.avatar_votes = b.avatar_votes + 1`) on a
persistent match grows *unboundedly within one frame*; guard with a per-frame stamp
(`voted_frame != game.frame`, set in the same effect). This is the guard the avatar
rewire must use.
