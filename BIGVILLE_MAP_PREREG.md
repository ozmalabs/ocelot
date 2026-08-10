# PREREG — the bigville map: generated from a spec, strong fixed-points, interiors, affordances, multi-quantisation

Until now the town was hand-edited: every place and room was minted by hand in its own world
adapter (`bigville_church_world.py` literally does `add_node("Room", {private:1})`), affordances
(`Station`, `Larder`) floated free of any building, and the rich quantization machinery
(`space_quantize.rs`, `quanta_navigation.json`) ran on grids disconnected from a semantic town.

The map process changes: **the town is generated from a spec + seed**, with **strong
fixed-points**, **building interiors with affordances**, and **multiple quantisations**. The map
is the world, so the generator is an admissible world-**builder** (mechanical graph construction,
deterministic, no agent decisions) — not agent cognition.

Design decisions (from the user):
- **Affordances reuse the existing typed nodes** (`Station{heat,prep_power,fuel,fuel_cost}`,
  `Larder`, `Bed`, …) via an `affords` edge — a generated kitchen is directly cookable by
  `fs_prepare`, no reinvention — **plus a preset library**: `CommercialKitchen` / `NormalKitchen` /
  `PoorKitchen` are named profiles with different defaults. Add a preset once; the generator drops
  it everywhere.
- **Quantisation is hierarchical** (town / building / room) by default, with the **fine tile-grain
  materialised lazily, only for a room in focus** — the existing *foveated* `space_quantize`. The
  fine grain is what enables physical interaction (bumping, squeezing past).
- **Build the whole thing, in gated steps.**

## Steps (LEDGER blocks)

- **340000 — generator core + presets + fixed-points + procedural houses.** ← this rung
- **341000 — multi-quantisation.** ✓ LANDED. `worlds/bigville_map_quantise.py` decodes the
  generated map at town grain (Places) and building grain (Rooms) and routes each by COMPOSING
  the `bigville_move_nav` Bellman flood (`mv_relax`/`mv_pick_hop`) — no new routing engine. The
  fine tile-grain is FOVEATED: `focus(room)` materialises a tile grid on demand for one room only;
  unfocused rooms stay tile-less. The fine grain makes BUMPING (two bodies, one tile) and
  SQUEEZE-PAST (stepping onto an occupied tile) visible. Gates: same-map-routes-at-two-grains
  (house→church 2 hops; bedroom→counsel 4 hops; rooms > places), lazy-foveated, bump, squeeze-past,
  composes-not-reinvents. 5/5.
- **342000 — routing rework (landmark-based).** ✓ LANDED. *User critique: "the flood is too
  complicated — that's not how people route; they route to landmarks in steps, which is much
  cheaper."* Correct. The town-wide Bellman flood is removed; `worlds/bigville_map_quantise.py`
  now routes to LANDMARKS in steps — a short coarse chain (`src → Square → dst`) refined locally
  within each building (foveated: only the building you're in). **The cost is invariant to town
  size**: a landmark route touches only the two endpoint buildings + the landmark chain (7 nodes
  for bedroom→counsel, whether the town has 6 houses or 40), while a flood touches ~every room
  (24 → 84). The three grains now fall straight out of the hierarchy: landmark chain (coarse) →
  interior door-walk (building) → lazy tiles (room). Gates: landmark-route, cost-invariant,
  multi-grain, lazy-foveated, bump/squeeze, no-flood-no-decision. 6/6.
- **343000 — food-lifecycle migration.** ✓ LANDED. `worlds/bigville_map_kitchen.py` runs the real
  `fs_prepare`/`fs_eat` against the GENERATED `Station`: a cook prepares a meal in the inn's
  generated commercial kitchen (quality 1.54); the same cook in a poor house's hearth gets 0.91
  (tier shapes the meal); a kitchenless house cannot cook — the food stays raw, and eaten raw it
  gives nutrition 0.6 + illness 0.3 versus a cooked meal's 4.0 + no illness. That last case is the
  glass-box of the **social determinants of health**: the affordance distribution (who has a
  kitchen) drives who eats well. Gates: cook-in-generated-kitchen, tier-shapes-meal,
  kitchenless-and-health, rules-cook-adapter-wires. 4/4.
- **344000 — institutions migrate onto the generated map.** ✓ LANDED (partial, honestly scoped).
  The generator now emits behavioural ROLE edges — `town -has_church->`, `-has_jail->`, `-has_inn->`,
  `-has_market->`, `-has_council->` the generated place — plus role attrs (`non_denominational`) and
  staff attrs (`draw`), via `role_place()`/`staff_node()`. **The CHURCH adapter is fully migrated**:
  `BigvilleChurchWorld` no longer hand-mints the church/Mary/counsel-room — it binds to the generated
  fixed-point, and all 7 church gates stay green (service, emergent congregation, confidential
  counsel). **The JAIL rule fires on the generated jail** (`jl_imprison` imprisons into the
  generated jail place via `has_jail`). The INN is a generated place whose kitchen already runs the
  food lifecycle (343000). Honest residual: the jail's and inn's full behavioural adapters extend
  the court / open-economy worlds, whose towns would also need migrating — a mechanical follow-on now
  that the role anchors exist; not done here. Gates: role-anchors, church-migrated, jail-rule-on-
  generated-jail, inn-is-generated. 4/4 (+7 church green).
- **(deferred)** the determinants-of-health sweep (see the memory note); the jail/inn full-adapter
  town migration.

## Step 340000 — the mechanism (`worlds/bigville_map_generator.py`)

`Town -has_place-> Place{kind,name,wealth,x,y} -has_room-> Room{kind,name,private,x,y}`;
`Room -affords-> <AffordanceNode>` (from a preset); `Room -door-> Room` (interior);
`Place -entrance-> Room -street-> Square` (exterior). `PRESETS` = the affordance library;
`DEFAULT_SPEC` = the fixed-points + per-wealth house distributions. `generate()` places the
fixed-points first (deterministic), then fills houses from the distributions under a seeded RNG.

### Gates (block 340000)
1. **G-deterministic:** same seed → same town (`fingerprint`); a different seed → a different fill.
2. **G-fixed-points-always-present (HEADLINE):** under every seed the church has Mary + her
   **private** counsel room + a bell; the inn has a (commercial) kitchen; the jail has cells; the
   market and council hall exist.
3. **G-houses-vary-cooking (HEADLINE):** across houses, some have a kitchen and some don't; a
   kitchenless house has **no** heated `Station` (it genuinely cannot cook). This is a spec
   distribution (`kitchen_prob_by_wealth`), not hand-editing.
4. **G-presets-differ:** commercial > normal > poor kitchen `prep_power`; the inn is fitted
   commercial by the spec.
5. **G-affordances-reuse-real-station (HEADLINE):** a generated kitchen affords a real `Station`
   carrying exactly the keys `fs_prepare` reads (`heat/prep_power/fuel/fuel_cost`) — composition,
   not reinvention.
6. **G-add-to-the-generator (source audit):** the builder runs no rule engine and makes no agent
   decisions; the town is DATA (a preset library + a spec); "houses may or may not cook" is a spec
   distribution.

## Scope / honesty
- `.so` untouched; the generator is pure Python world-construction (like the grid materializer or
  `worlds.chess_world`) — it emits graph data the agent then perceives/navigates.
- The generator emits coordinates + the containment hierarchy so 341000's quantisation composes;
  it does not itself route.
- Full food-lifecycle integration (a cook actually preparing a meal in a *generated* kitchen) lands
  in 342000's migration, where the food/tools rules run against generated affordances.
- Streets are a single town square hub in this rung; a richer road graph is a refinement (composes
  with the same `street`/`portal` edges).
