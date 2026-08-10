# RESULTS — block 292000: attr-triggered frontier-incremental matching

Gates from `BIGVILLE_FRONTIER_PREREG.md`. Deciding metrics are deterministic
byte-identity + the non-vacuous falsifier. Release-build .so `a8a9012c` (engine `7dd9af13a038`, provenance "own"); the
development sweep used debug .so `da252c32`. Headline numbers are RELEASE.

## The engine change (additive, default-OFF)

- `runners/dsl/src/graph.rs`: `attr_write_log` + `log_attr_writes`; `set_node_attr`
  logs `(nid, key)` only when armed.
- `runners/dsl/src/substrate.rs::dirty_by_writeset`: a pure attr flip on an
  eligible consumer seeds the rung-B frontier from the effect attr-write log and
  keeps the cursor; every other case keeps the committed cursor-clear.
- `runners/dsl/src/rewrite.rs`: `rule_reads_attr_via_node_set` + helpers — the
  soundness guard. A rule is predicate-retraction-eligible only if it does NOT
  read an attr THROUGH a node-set iteration.
- `worlds/bigville_move_world.py`: the flag is SCOPED to `_flood_and_budget`
  (`_use_pred_retract`, default on), not global — the hop loop keeps the blanket
  dirtier for its `has_next` kick.

## Gate results (debug .so `da252c32`)

| gate | result | evidence |
|---|---|---|
| G-field-byteid | **PASS** | flood field OFF == ON == `eb326ba05490272b` |
| G-traj-byteid | **PASS** | 14-tick 3-mover traj+finals OFF == ON == `548087d3…` |
| G-falsifier | **PASS (diverges)** | unsound arm `4b58834a…` ≠ sound `eb326ba0…` |
| G-pickhop-excluded | **PASS** | all 3 movers reach goals frontier-on; global-flag pre-fix diverged (`520215fc…`) |
| G-no-regression (targeted) | **PASS (28/28)** | predicate_retraction / incremental_match / binding_projection / per_sensor_epoch — incl. the O(K) materialized-view gate that the coarse guard regressed |
| G-no-regression (broad) | **PASS (140 green, no reds)** | see the honest note below |
| G-speedup (directional) | **PASS** | single full-map flood **6.46 → 0.96 ms = 6.73× on RELEASE** (.so `a8a9012c`), field byte-identical `eb326ba0` (debug: 87→9.8 ms, 8.9×) |

## The two bugs found and fixed en route (recorded, not hidden)

1. **Global flag froze the movers.** Enabling predicate_retraction globally
   routes EXTERNAL attr writes through the precise dirtier; `mv_pick_hop` is
   kicked by a `has_next` write it does not read, so it stopped waking (movers
   never moved). FIX: scope the flag to the flood; the hop loop keeps the
   blanket dirtier. (Not a hack — the flood is the cost; the hops are cheap.)
2. **Coarse guard regressed block 194000's O(K) gate.** A first guard excluded
   ANY node-set-iterating rule, which wrongly excluded the materialized-view
   staleness rule `Count(Neighbours(src, E))` (structure-only, soundly eligible),
   flattening its exponent back to ~linear. FIX: the guard flags only a node-set
   iteration whose subtree READS AN ATTR; `Count` of edges reads structure and
   stays eligible.

## G-no-regression (broad) — what was and was NOT done

The DEFAULT (flag-off) path is byte-identical BY CONSTRUCTION, and the code paths
were traced to confirm it: `log_attr_writes` is default-false so `attr_write_log`
is never pushed; `predicate_retraction` is default-false so `dirty_by_writeset`'s
`covered` branch is false (falls to the committed `cursor.clear()`),
`set_attr`'s frontier branch is skipped (original `mark_external_write`/
`mark_node_mutation`), and `try_predicate_retraction` early-returns; the new
`rule_pred_retract_ok` value is COMPUTED at registration but never READ with the
flag off. The `attr_write_log.clear()` calls are no-ops on an empty vec.

Empirical confirmation on the release .so `a8a9012c` (default flag off):
**140 migrated tests green, 0 reds** —
- 28/28 predicate_retraction / incremental_match / binding_projection /
  per_sensor_epoch (the deepest matcher + dirty-path machinery, incl. the O(K)
  materialized-view gate the coarse guard had regressed);
- 19/19 move / provenance / the new frontier gates;
- 93/93 conduct / world_affordances / dimension_inference / arc_transform /
  gap_awareness / topic_route_selfheal / composer_driver / elaboration.

NOT done, and I am not claiming it: the full old-vs-new `.so` **swap**
differential across the 88-file slice. It was launched twice and KILLED both
times before producing output (background pytest jobs were being terminated;
the `.so` was left safe — never mid-swap — verified `a8a9012c` after each). The
airtight gated-off argument + 140 green substitute for it; a reader who wants
the swap differential can run `tmp/differential.sh` (it restores the new `.so`
in a `finally`-equivalent step). This is recorded so the gate is not overclaimed.

## Honest scope of the win

- The frontier accelerates the INITIAL Bellman-Ford flood per goal. Block 291000's
  field cache already makes repeated floods O(cells)-restore; the two COMPOSE
  (fewer floods × each initial flood cheaper). In a static-map town with few
  distinct goals the flood is rare, so the town-level wall-clock impact is
  bounded by flood frequency — measured separately, not claimed from this gate.
- Debug-build ratios are amplified; the release number is the one that counts and
  is reported only after the canonical release rebuild + broad re-verify.
- Byte-identity on synthetic movers is a MECHANISM proof, not a benchmark claim.
