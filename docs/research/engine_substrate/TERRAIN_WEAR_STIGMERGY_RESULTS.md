# Probe 2 — traversal wears grass toward path

**Status: measurement complete. Landed in `~/ozmadev/bigville` (separate repo, uncommitted):
a `TERRAIN_WEAR` data table in `domains/bigville_entities.py` and its enactment in
`worlds/bigville_world.py`. Bigville suite 211/211 green.** This runs probe 2 of
`AFFECT_WEIGHTED_ROUTE_VALUATION_DESIGN.md` §9 and closes the composition claim in §8.

Probe 1 (`DESIRE_PATH_PRECONDITION_RESULTS.md`) gave residents differing route valuations
but left the note's own objection standing: *"disposition alone gives heterogeneity with no
accumulation, and nothing persists."*

## 1. Data, not world code

Bigville is a generic experiment backend, so the wear rule is declared alongside
`TERRAIN_MOVEMENT` rather than written into the world:

```python
TERRAIN_WEAR = {
    "grass": {"wears_to": "path",  "passes_to_form":  40.0, "ticks_to_fade": 400.0,
              "load_sensitive": True},
    "tree":  {"wears_to": "grass", "passes_to_form": 120.0, "ticks_to_fade": 600.0,
              "load_sensitive": True},
}
```

A terrain with no record here is inert. Nothing in the world code names `grass` or `path`.

Four design points, each load-bearing rather than decorative:

- **One accumulator, read in two directions.** A cell keeps the terrain it was *seeded* as
  (`base_terrain`) plus `wear` ∈ [0,1]. Wearing and fading are the same quantity, so a
  formed path is never confused with a built one. Ground seeded as `path` has no record and
  is permanent infrastructure; a path that *wore* into existence is only ever the far end of
  grass's accumulator and stops being a path when the traffic does. **Reversion needs no
  second field** — the target is `base_terrain`.
- **Interpolated, not switched.** `terrain_state` blends the movement read-off across the
  accumulator, so part-worn ground is already part-easier. This is what lets traffic recruit
  traffic; a threshold-only flip would make wear invisible until it trips, and there would be
  no feedback to converge on.
- **Counts, not deltas.** `passes_to_form` / `ticks_to_fade` are the quantities an
  experimenter is actually asking about ("how many crossings make a path?"), rather than
  per-event increments they would have to convert.
- **Enactment at one site.** `_move_actor_to` is the single place a resident arrives
  anywhere, so footfall hooks there rather than in any caller that happens to move someone.

The split from probe 1 holds: **route choice is cognition and lives in the seed rule; ground
wearing under load is physics and lives in world code.**

## 2. The mechanism works, both directions

40 crossings of one grass cell, then 400 idle turns:

| passes | wear | terrain | stamina_mult |
|---|---|---|---|
| 0 | 0.000 | grass | 1.0000 |
| 10 | 0.275 | grass | 0.9038 |
| 20 | 0.550 | grass | 0.8075 |
| 30 | 0.825 | grass | 0.7113 |
| 40 | 1.000 | **path** | 0.6500 |
| +400 idle | 0.003 | **grass** | 0.9991 |

Monotone throughout. Increment is 0.0275 = `1.1/40`, so `load_sensitive` is live — the
walker's `carry_ratio` of 0.1 is in the number.

## 3. Recruitment — the result probe 2 exists for

The §8 claim is not that ground wears; it is that *the impatient cut the corner, the cut is
recorded as reduced cost, and the reduced cost recruits the less impatient.* A mixed-stamina
population repeatedly chooses between a shorter grass shortcut and a longer made path. Only
the chosen route wears. **No resident's disposition ever changes.**

```
turn   wear   stam   users
   0  0.000  1.000   3/5  [1.0, 0.75, 0.5]
   6  0.605  0.788   5/5  [1.0, 0.75, 0.5, 0.25, 0.0]
  12  1.000  0.650   5/5  [1.0, 0.75, 0.5, 0.25, 0.0]
```

**3/5 → 5/5, monotone.** The two spent residents were refusing the shortcut at turn 0 and
take it by turn 6, because the first three wore it cheaper.

### Both halves are necessary — measured, not asserted

Three arms, identical but for the named change:

| arm | users | terrain |
|---|---|---|
| **both** (mixed population + wear) | 3/5 → **5/5** | path forms |
| **stigmergy alone** (uniform tired + wear) | 0/5 → 0/5 | no path |
| **disposition alone** (mixed, wear disabled) | 3/5 → 3/5 | no path |

The uniform arm contains **exactly the same spent walkers** who end up using the path in the
mixed arm. Alone they never build it: nobody is impatient enough to seed it and the mechanism
never starts. This is the sharpest form of §8's claim — the infrastructure is a readout of
the population's *spread* of disposition, not of its average.

## 4. In a live 100-resident town

The synthetic fixture proves the loop closes. The town says what it does at scale — and the
honest answer is split.

100 residents, 1953 walkable cells, 150–200 turns, deterministic across repeats
(`(2, 64.7776)` on three runs).

**Formation is rare.** Only 2 grass cells ever cross the threshold, and they are isolated
chokepoints, not a trail. This does **not** move when the parameters do:

| passes_to_form | ticks_to_fade | cells with wear | formed |
|---|---|---|---|
| 40 | 400 | 15 | 2 |
| 40 | 2000 | 128 | 2 |
| 15 | 2000 | 212 | 2 |
| 15 | 100000 (fade off) | 225 | **2** |

`worn>0` swings 15 → 225 while `formed` sits at 2 even with fade switched off. The cause is
measurable rather than mysterious: traffic concentrates, and a dozen cells stall *just* below
the threshold — a contiguous corridor (13,14)…(21,14) all at wear 0.999, identical because
one route is walked by the same walkers the same number of times. Formation is
threshold-limited, not accumulation-limited.

**But the wear field is genuinely trail-shaped**, which counting `formed` completely hides.
Contiguity of the worn set against a null of the same number of cells scattered at random
over the same grass (200 draws):

| threshold | cells | observed | random mean (95th pct) |
|---|---|---|---|
| wear > 0.25 | 96 | **92.7%** | 20.7% (30.2%) |
| wear > 0.50 | 33 | **75.8%** | 7.6% (18.2%) |
| wear > 0.75 | 15 | **66.7%** | 4.4% (13.3%) |

All three are far outside the null's 95th percentile, and the largest connected components
are clean straight runs — (28,29)→(35,29) and (13,14)→(18,14). **The town is laying down
coherent linear trails; the discrete relabel simply lags far behind the field that would
justify it.**

## 5. What this does NOT establish

- **No completed desire path in a live town.** Two isolated chokepoint cells is not a trail.
  The synthetic recruitment result is a *mechanism* proof; the town has not been shown to
  produce emergent infrastructure end to end. Per this repo's standing rule,
  synthetic-proven mechanism ≠ benchmark value — both are reported.
- **The threshold semantics are the next question, and are unexamined.** A corridor sitting
  at 0.999 while two chokepoints relabel suggests formation should perhaps depend on a cell's
  *neighbourhood* — a path is a connected thing — rather than on each cell independently
  crossing a scalar bar. That is a design question this probe raises and does not answer, and
  it is the obvious candidate for the "number where a shape belongs" critique.
- **Parameters are uncalibrated.** The defaults (40 / 400) were chosen to be legible, not
  derived from anything. The sweep characterises the regime; it does not identify a right
  setting, and deliberately does not pick the flattering one.
- **One map, one seed, one population.** Town100 only.
- **No test was added.** The mechanism is exercised by probes, not by the suite. The 211
  existing tests pass and one of them (`test_no_python_decides_the_world`) constrains it, but
  nothing pins the wear behaviour itself.
- **Route choice still ignores wear when planning.** Wear changes the cost of a cell the
  resident is *offered*; nothing routes *toward* a forming trail deliberately.

## 6. Note on the architecture guard

`test_no_python_decides_the_world` forbids the substring `_apply` in `worlds/bigville_world.py`,
and the first version of this work named a method `_apply_wear`. The guard is a crude
substring check and it fired on a false positive — but it fired, and the method was renamed
to `_advance_wear` rather than the guard weakened. A blunt guard that occasionally
inconveniences correct code is doing its job; editing it to accommodate new code is how such
guards stop working.

## 7. Reproduce

```bash
cd ~/ozmadev/bigville
python3 <scratchpad>/wear_probe.py         # formation and fade
python3 <scratchpad>/recruitment_probe.py  # 3/5 -> 5/5
python3 <scratchpad>/controls_probe.py     # three-arm necessity control
python3 <scratchpad>/wear_sweep.py         # parameter regime
python3 <scratchpad>/trail_null.py         # contiguity vs scattered null
python3 -m pytest -q tests/                # 211 passed
```

**Instrument caveat.** `wear_dist.py` printed wear to three decimals, so cells at 0.9996
displayed as `1.000` and appeared to contradict the sweep's `formed = 2`. There was no bug;
the probe's own rounding manufactured the discrepancy. Third time this session a probe's
presentation, not the system, produced the anomaly — the tell each time was a number that was
*too* clean.
