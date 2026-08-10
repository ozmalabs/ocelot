# Bigville 100-resident cast + expanded map — PRE-REGISTRATION (blocks 305000–309000)

**Committed BEFORE any measurement.** Gates and thresholds are fixed here; the
implementation that follows may not move a threshold to make a number pass.

## Goal

Give bigville a full **100-resident cast**, pre-seeded with jobs / houses /
role-identity / drawn personality params, and **an expanded map** (a bigger grid
with houses, workplaces, resource sites and roads) sized to hold them. Delivered
as deterministic SEED/config DATA + a loader/world + a gate test — NO agent
decision logic in Python (cast + map are graph data; this is seed-builder work,
which the architecture rule explicitly permits).

## What it must fit into (do NOT modify these — read-only context)

- The R1–R3 production economy: `Deposit{kind: fish/lumber/stone, stock,
  growback, capacity}` on the map (fish from water, lumber from forest, stone
  from a quarry); `Shop{trade, input_kind, output_kind, …}`; `Store`/`Stock`;
  labourers walk the nav flood to a deposit and extract. Reuse
  `BigvilleTradeWorld.add_deposit / add_shop / add_supplier / add_labourer` by
  IMPORT, never copy; never edit the economy files.
- `build_town()` (30×18) and every test that depends on it: **byte-unchanged**.
  A NEW builder `build_town_100()` is added; `build_town()` is untouched.
- Register/param conventions: names in the Pratchett register style (extend
  `bigville_townspeople_30.json`); personality/emotion params DRAWN from seeded
  Normals (`numpy.default_rng(seed)`), never cloned; literacy ~ Bernoulli;
  class ∈ {rich, middle, poor}.

## Role model (fixed here)

100 residents across a realistic occupational pyramid. Three gate-relevant
groups:

- **LOW / labourers** (mobile, low role-identity): labourer, farm_labourer,
  fisher, forester, quarrier, servant.
- **HIGH / owners + tradesmen** (sticky, high role-identity): fishmonger,
  carpenter, mason, baker, innkeeper, landlord, banker, shopkeeper, mayor,
  pastor, doctor.
- **MIDDLE** (neither gate group): farmer, teacher, reporter, clerk, councillor,
  miller, constable, midwife.

`role_identity` ∈ [0,1] is drawn per-resident from `Normal(role_mean, role_sd)`
(clipped), with LOW means ≈0.20–0.28 and HIGH means ≈0.82–0.93 — this is R4's
labour-mobility switching FRICTION, seeded but switchable.

## Map model (fixed here)

A new grid (target ≈50×40) built by `build_town_100(seed)`:
a connected PATH road lattice; a WATER lake, a FOREST (TREE) patch and a QUARRY
(WALL) rock face as the three resource bodies; a central market SQUARE; ~20 named
workplace plots; a pool of farm plots; and ≥100 home plots. Homes, workplaces and
deposits are all selected from the SINGLE LARGEST walkable connected component so
mutual reachability is guaranteed by construction; the fish/lumber/stone deposits
sit on walkable cells orthogonally adjacent to water/forest/quarry respectively.
Tile codes reuse `bigville_sim_world`'s (GRASS/PATH/WALL/FLOOR/SQUARE/TREE/WATER;
SOLID = WALL/TREE/WATER).

## Gates (thresholds FIXED — the test asserts exactly these)

- **G-count**: exactly 100 `Resident` records; all names DISTINCT (100 unique).
- **G-everyone-housed-and-employed**: every resident has a `home_cell` AND a
  `workplace_cell`; both are WALKABLE (in the nav cell graph); a nav/BFS path
  exists home→work for two arbitrary residents (and, stronger, all homes +
  workplaces lie in one connected component — asserted).
- **G-role-identity-distribution**: mean role_identity of the HIGH group ≥ 0.80,
  mean of the LOW group ≤ 0.35, and role_identity is NOT constant (overall
  variance > 0). Report both group means + the spread.
- **G-params-not-cloned**: every drawn personality/emotion param has variance > 0
  across the cast (no zero-variance cloning tell). Report the per-param variance.
- **G-job-mix-realistic**: report the full job histogram; assert `labourer` is
  the single plurality role, and the HIGH owners+tradesmen group is a small
  minority (≤ 20 of 100, and strictly fewer than the LOW group).
- **G-resources-on-map**: fish, lumber AND stone deposits exist, each on a
  walkable cell in the connected component, with kinds exactly {fish, lumber,
  stone} matching the economy; each is orthogonally adjacent to its resource body
  (water/forest/quarry).
- **G-deterministic**: same seed ⇒ identical cast + map. Two in-memory
  regenerations hash-identical, AND the committed `seeds/bigville_cast100.json`
  hash-matches a fresh regeneration.
- **G-no-mutation**: `build_town()` returns the 30×18 grid byte-unchanged (pinned
  dimensions + a content hash), and a representative slice of the existing
  bigville migrated suites (move / resource / trade) still passes.
- **G-no-python-decision**: the new world adapter contains no rule-engine call
  (`graph_rewrite` / `gr.run` / `make_rule` / `_match` / `_apply`) — source audit.

## Discipline

Measure-first; deterministic (seeded numpy RNG); anti-fabrication (report the REAL
histogram, group means, variances, map size, reachability). Commit prereg FIRST,
then the implementation. Commit only the new files, explicit paths, on main, no push.

## Honest-residual policy

Residuals (e.g. workplaces represented as tile plots rather than fully walled
buildings; the drama scaffold's small cast coexisting as separate nodes) are
recorded in the commit message and the final report, not hidden.
