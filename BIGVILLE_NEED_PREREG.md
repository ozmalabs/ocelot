# BIGVILLE R2 — NEEDS → GOALS + PREFERENCE / satisficing (block 250000) — PRE-REGISTRATION

**Status: pre-registered, no numbers yet. 2026-07-29.** The rung after R1
(movement+energy, block 249000). Builds ON R1 by IMPORT: a DRIVE above threshold
mints a spatial GOAL, and WHICH good the goal targets is the substrate's own
`decision_value` Argmax over REACHABLE satisfiers weighted by a per-villager
PREFERENCE minus TRAVEL-COST. The chosen source becomes the R1 nav target.

Base worktree merge-base: `0bc0c206f95915b27385588ad978b26306e2d255`.
Isolated NON-nested worktree; own-engine build; ZERO Rust
(`runners/dsl` diff EMPTY — the target is no new primitive).

## Seed claim (verbatim `check_claim(250000, 250999)`)

```
SEED CLAIM 250000-250999: CLEAN -- no collision DETECTED.
  Scope: 971 files with seed sinks; 681 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## The decision, graph-native (the value trade-off)

    value(good) = preference[villager][good] · need_urgency − cost_on · travel_cost(distance to a source)

(PRICE is deferred to the economy rung R4 — R2 is preference vs travel-cost.)
Every decision is a RULE composing EXISTING Terms
(Argmax / MaxOver / Sum / IfThenElse / Eq / Plus / Minus / Times / Gte /
NodesOfType / Neighbours / Attr) — the SAME `decision_value` Argmax FAMILY as
245's `ss_choose_burn` / the ToM abductive decode. NO Python `if hungry and
apples_far: bread`. Source-audit clean.

Reuses the 207000 `drives` seed BY IMPORT: each villager (a Mover) carries
`enabled=1` + `has_active_drive`→Drive so `drives`' own `drive_urge` rule computes
`urge = |v_d − c_d|`. Per-villager PREFERENCE weights seeded ~Normal (heterogeneous
— apples≻bread for one, ale≻bread for another). NEW seeds:
`bigville_need_drive_goal.json` (arbitrate + goal-form), `bigville_need_choice.json`
(the choice-distance flood + the preference/satisficing Argmax).

## Pre-registered gates

### G-drive-forms-goal (load-bearing, à la Harlow 233000)
- A hungry villager (`SUSTENANCE` drive above `hunger_threshold`) forms a food goal
  (`get_food`).
- **Ablate the drive** (remove the Drive node) → no drive above threshold → the
  arbitration finds nothing → **NO goal** (`goal is None`). Prediction: PASS.
- **Two competing drives → the higher wins** (the same Argmax family): with
  `SUSTENANCE.urge > FATIGUE.urge` the villager forms `get_food`; swap the urges
  (`FATIGUE.urge > SUSTENANCE.urge`) and it forms `go_home` instead. The higher
  drive's goal is the one formed. Prediction: PASS.
  - NOTE: the spec named `conflicting_goals_default` for arbitration, but that seed
    is a text-disclaimer codebook with **no rules**. The load-bearing directive is
    the Argmax family (the "do NOT invent a parallel chooser" constraint), which
    `nd_arbitrate` reuses; the mislabeled seed is not loaded. Recorded honestly.

### G-preference-satisficing (HEADLINE — the flip on distance alone)
- A villager that PREFERS apples to bread (`pref: apple=5, bread=4, ale=1`),
  **held constant**, targets **APPLES when the orchard is near** and **BREAD when
  the orchard is moved FAR** — the choice flips on travel-cost alone, preference
  unchanged. Prediction: near→apple, far→bread. PASS.

**Failing controls** (each MUST change the outcome):
- **preference ablated (equal weights)** → picks the **NEAREST** satisfier
  regardless (never the far orchard). Prediction: PASS.
- **travel-cost ablated (`cost_on=0`)** → **ALWAYS the top-preference good** however
  far (apple, even at the far orchard) — proves cost is load-bearing. Prediction: PASS.
- **an ale-preferring villager** (`pref: ale=6, bread=3, apple=1`) makes a
  **DIFFERENT** choice (ale) in the same town — preference is per-villager, not
  global. Prediction: PASS.

### G-discipline (a rung that violates any is void)
- NON-nested worktree; own-engine build (`cargo build --release` in THIS worktree);
  `source_match ∈ {own, shared}` (INVARIANT, never a pinned `.so` md5 — lesson 7b).
- `runners/dsl` (incl `term.rs`) diff EMPTY. All new files prefixed `bigville_need_`;
  no existing tracked file edited (subclass/import R1 + the scaffold + reuse `drives`).
- Oracles `rung7_vision_bench.sh` + `per_area_settlement_regression.sh`: fail-set ⊆
  the enumerated `results/failure_baseline.json`; `test_failure_baseline_migrated`
  green; ZERO new reds. (A PRE-EXISTING main provenance red,
  `test_engine_provenance_migrated`, is NOT ours; the enumerated baseline is the
  arbiter.)
- Canonical shared `.so` md5 UNCHANGED start==end. Commits on this branch only
  (supervisor merges + writes the ledger).

## Honest scope
Synthetic model of a preference/satisficing mechanism on a small cast + a compact
grid. Mechanism-proven ≠ benchmark value. N-scope: a handful of villagers, three
goods, one town. No claim about real economics.
