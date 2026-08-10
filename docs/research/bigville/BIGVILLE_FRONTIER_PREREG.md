# PREREG — block 292000: attr-triggered frontier-incremental matching

**Pre-registered before the headline number. Measure-first; the deciding
metric is deterministic byte-identity, not wall-clock.**

## The claim under test

The nav flood (`mv_relax`, a Bellman-Ford relaxation to fixpoint over a static
walkable-cell belief) is the measured cost of bigville movement (block 290000:
~79% of nav rule-fires). Blocks 192000 (incremental match) and 194000/211000
(predicate retraction) already gave the engine a frontier-incremental matcher —
but they seeded the frontier only from **edge** changes and **external** attr
writes. `mv_relax` is driven by **rule-effect** `gdist` attr writes (one
relaxation writes the next cell's `gdist`, which must wake its neighbours), so
neither path engaged and the earlier "do the rust fix" premise was falsified
(0 speedup, flood flat at ~103 ms).

**This block closes that gap:** a rule-effect attr write now seeds the
predicate-retraction frontier (only cells incident to a changed cell), so the
flood re-evaluates the frontier instead of clearing every cursor and re-scanning
all `adj` edges each pass — **byte-identically**.

## The engine change (Rust, additive, default-OFF)

- `graph.rs`: `attr_write_log: Vec<(NodeID, Sym)>` + `log_attr_writes: bool`.
  `set_node_attr` pushes `(nid, key)` **only when `log_attr_writes` is on**
  (armed together with `predicate_retraction`). Default off ⇒ nothing pushed.
- `substrate.rs::dirty_by_writeset`: a **pure attr flip** (no structural/type/
  reads_any change) on a **predicate-retraction-eligible** consumer seeds the
  rung-B frontier from the effect attr-write log and KEEPS the cursor; every
  other case keeps the committed cursor-clear. Log drained per fire.
- `substrate.rs` eligibility (`rule_pred_retract_ok`): a rule is eligible only
  if it does NOT **read an attr through a node-set iteration**
  (`rule_reads_attr_via_node_set`, rewrite.rs). This is the soundness guard —
  see below.

## Soundness — the eligibility guard (the crux)

The frontier seeds dirty bindings ONLY from nodes incident to a changed node.
That is sound iff **every attr the rule reads lives on a match-bound node**. Two
rules make the boundary precise:

- `mv_relax` reads `gdist` on its two match vars (`c`, `n`, joined by the `adj`
  edge). A `gdist` write to `n` wakes bindings where `n` is a match endpoint ⇒
  frontier is **sound** ⇒ eligible ⇒ fast.
- `mv_pick_hop` reads `gdist` inside `Argmin over Neighbours(cur, adj)` — cells
  the match never bound. A `gdist` write to one of those cells is UNREACHABLE
  from the changed-node frontier ⇒ **unsound** ⇒ must be **ineligible** (falls
  back to full re-scan, byte-identical).

The guard flags "a node-set iteration (`Neighbours`/`Argmin`/`Sum`/…) whose
subtree **reads an attr**", NOT "any node-set iteration". A node-set Term that
reads only **structure** (`Count(Neighbours(src, E))` — the materialized-view
staleness guard of block 194000) is safe: an edge/type change bumps the cursor
version and is handled structurally, so it stays eligible. (A coarser "any
node-set Term" guard regressed block 194000's O(K) gate — recorded, fixed.)

## Adapter scope (the has_next kick)

`predicate_retraction` routes EXTERNAL attr writes through the PRECISE dirtier
(a rule wakes only if it reads the written key). The flood's `mv_relax` reads
what drives it, so precise is correct. But the hop loop kicks `mv_pick_hop` with
a `has_next` write it does NOT read — that kick lands only under the default
BLANKET dirtier. So the flag is **scoped to `_flood_and_budget`** (armed around
the flood, disarmed before the hop loop), not global. This is a world-adapter
switch (`_use_pred_retract`, default on; set False for the byte-identity gate),
not agent logic.

## Gates (pass/fail, pre-registered)

1. **G-field-byteid**: the full `gdist` field after a flood is BIT-IDENTICAL
   with the frontier OFF vs ON. (PASS required.)
2. **G-traj-byteid**: the full multi-mover trajectory + final positions over a
   14-tick run is BIT-IDENTICAL OFF vs ON. (PASS required.)
3. **G-falsifier**: with `predicate_retraction_unsound` armed (drops one
   frontier node), the flood field **DIVERGES** from baseline — the gate is
   non-vacuous (the frontier is genuinely exercised, not equal to full-scan by
   accident). (DIVERGENCE required.)
4. **G-pickhop-excluded**: `mv_pick_hop` (Argmin+Neighbours reading gdist) is
   engine-ineligible; enabling the frontier GLOBALLY (without the scope) would
   diverge (verified pre-fix: `520215fc…`), and the guard prevents it.
5. **G-no-regression**: the existing predicate-retraction / incremental-match /
   binding-projection / per-sensor-epoch migrated suites stay green (the
   materialized-view O(K) gate in particular — the coarse-guard regression must
   not recur), AND the broad migrated bench flag-OFF default matches
   `results/failure_baseline.json` (the .so changed; the default path must be
   byte-identical).
6. **G-speedup (directional, NOT the deciding metric)**: a single full-map flood
   is measurably faster frontier-ON. Wall-clock is noisy and build-dependent;
   reported as a range with the build named, never as a headline point estimate.

## Anti-fabrication

- The deciding metrics are the byte-identity hashes (deterministic) and the
  green regression suite — not wall-clock.
- Any wall-clock number is reported with (a) the build (debug/release), (b)
  min-of-N reps, (c) that it is directional. The debug-build flood ratio
  observed during development (~8–9×) is NOT the headline; the release number
  under a clean measurement is, and only after the release canonical rebuild.
- The mechanism being byte-identical on synthetic movers is NOT a benchmark
  claim about the live town; the fold-in perf (block 291000 cache + this
  frontier) composes, but the town-level number is separately measured.
