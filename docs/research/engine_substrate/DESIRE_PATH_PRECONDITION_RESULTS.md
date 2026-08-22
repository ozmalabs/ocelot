# Wiring energy into hop cost in bigville — the ocelot backend, and two corrections

**Status: measurement complete. Edits landed in `~/ozmadev/bigville` (separate repo,
uncommitted): `seeds/bigville_actor_decision.json` v1.0.0 → v1.1.0, and its adapter mirror
in `worlds/bigville_world.py`. Bigville suite 211/211 green. The graph rule is validated by
execution on ocelot's Rust engine, 30/30 against the Python fallback.**

This runs probe 1 of `AFFECT_WEIGHTED_ROUTE_VALUATION_DESIGN.md` §9 and corrects that
document twice.

## 0. Two corrections, both mine

**Correction 1 — the site named in §8 is dead code.** §8 reported, as measured facts about
a running system, that `bigville_move_nav.json`'s `mv_relax` floods with a hardcoded
`Lit 1` hop cost and that no per-resident attribute reaches `gdist`. Every one of those
statements is a true description of that JSON. The conclusion drawn from them was still
wrong, because **those rules never execute**:

- `bigville/runtime.py::load_seed_manifest` — *"Retain seeded graph data **without executing
  an external rule engine**."*
- `bigville/runtime.py::settle` — *"Compatibility no-op"*, `return 0`.
- `worlds/bigville_move_world.py` drives its entire flood and hop loop through
  `self.eng.settle(1000000)` — five call sites, all no-ops.
- **No test imports the move world.**

§8's "every resident routes identically" holds there for a more basic reason than the one
given: in that seed, nobody routes at all. A static read of seed JSON was reported as a
property of a running system — the defect class that document exists to catalogue.

**Correction 2 — the first fix went into the wrong backend.** Bigville has pluggable
backends. `cheap` (`backends/cheap.py`, `DeterministicBackend` + `psi_can`) is the default
*game-AI* backend; routing belongs to the **ocelot** backend. An initial wire into `cheap`'s
`path_preferred` bonus was **reverted by hand** — not with `git checkout`, which would have
destroyed uncommitted work in those same files.

That reverted work did surface one finding worth keeping on the record, **unfixed**: in the
cheap path, `PsiState.from_context` computes `fatigue = _clamp(1.0 - float(energy))` while
`BigvilleWorld.energy` returns `stamina_reserve * 100.0`. For any energy at or above 1.0 the
result clamps to exactly `0.0`, so a resident at 2% stamina and one at 100% both report
`fatigue = 0.0`, and the largest row of the CAN `EDGES` table (`comfort 1.5, survival 0.4,
duty -0.35`) is dead in production. Two energy conventions coexist in bigville's own tests
(`100`, `80`, and `0.8`). Left alone as out of scope for the ocelot path.

## 1. The ocelot route decision

`OcelotBackend.decide` scores nothing itself; it delegates to
`world.resident_plan_from_context()` → `_decide_actor` → `BigvilleOcelotActor.decide`, whose
graph-native form is `seeds/bigville_actor_decision.json::oa_choose_option`:

```
Argmax over (agent -has_option-> candidate) by  Plus(candidate.score, Lit 0.0)
```

**That `Lit 0.0` is an empty slot** — structurally the same defect as `mv_relax`'s `Lit 1`,
and the `Plus(x, Lit 0)` coercion idiom used throughout these seeds.

The waste is the striking part. `_actor_options` already publishes a full physical cost
channel onto every move affordance:

| terrain | speed | move_time | **stamina_multiplier** |
|---|---|---|---|
| path | 1.35 | 0.75 | **0.65** |
| grass | 1.00 | 1.00 | **1.00** |
| tree | 0.45 | 2.20 | **2.00** |
| water | 0.00 | 999.0 | **4.00** |

`terrain`, `terrain_speed`, `terrain_move_time`, `terrain_stamina_multiplier`,
`route_terrain`, `path_preferred` — **all six published, none read.** Route choice was raw
`score`, and this is the per-cell cost channel `MoveCell` (`cx`, `cy`, `gdist` only) never
had.

The Python fallback tie-breaks on `-int(n)` — **lowest node id wins**, i.e. option creation
order. Insertion order as a navigation policy, the `TIE_CONSEQUENTIALITY_RESULTS.md` finding
again, inside the social simulation.

## 2. The wire

Selection becomes the affordance's own score less what the route costs **this** body:

```
score  -  EFFORT_TO_SCORE * terrain_stamina_multiplier * (1 - stamina_reserve)
```

Two properties make this the right shape rather than another knob:

- **Zero at full reserve.** A rested resident is byte-unchanged, so the change is a pure
  extension into the depleted region the old constant never described — the same shape that
  made the constant safe to replace. Terrain costs nothing you care about when fresh and
  dominates when you are spent.
- **Absent-attribute-safe.** Non-move options (`rest`, `work`, `eat`) carry no
  `terrain_stamina_multiplier`; the `Plus(Attr, Lit 0)` idiom coerces the absence to `0.0`,
  so their valuation is untouched.

`EFFORT_TO_SCORE = 6.0` is **one scalar, and it is the honest weak point** — exactly the
class CLAUDE.md flags. It is a unit conversion from stamina multipliers to affordance-score
units; the *shape* around it (proportional to both the terrain's own cost and to depletion)
carries the behaviour, and the constant only sets how loudly it speaks.

`oa_choose_option` has **five** `set_attr` effects (action/kind/trade/recipe/target), each
with its own `Argmax`. All five were rewritten. They must share one value function or
different attributes could be read off different options — a latent hazard in the original
that the edit preserves correctly rather than introduces.

`_decide_actor` now publishes `stamina_reserve` onto the mind before deciding. Terrain cost
is a property of the route and is already published; how hard it bites is a property of the
body, which the mind cannot observe for itself. Mechanical world→mind translation, no decision.

## 3. Result

Threshold: **how much better must a rough tree shortcut (`stamina_multiplier` 2.00) be
before this resident takes it over a made path (0.65)?**

| stamina_reserve | cuts shortcut at advantage |
|---|---|
| 1.00 (fresh) | **0.0** — unchanged from today |
| 0.75 | 2.1 |
| 0.50 | 4.1 |
| 0.25 | 6.1 |
| 0.00 (spent) | **8.1** |

Exactly `6.0 × (2.00 − 0.65) × depletion`. Before the wire every row read 0.0: terrain was
not consulted at all.

**The desire-path precondition is met on the ocelot path** — the population no longer routes
as one body, and the differentiating quantity is a real physical cost the world was already
publishing.

## 4. The graph rule is validated by execution, not by inspection

Bigville's runtime cannot run its own seed rules, so a seed edit there is unexecuted JSON —
precisely the `mv_relax` failure mode in §0. So `oa_choose_option` was installed on
**ocelot's real Rust engine** (`boot_core` + `load_seed_manifest` + `run_rules`) and compared
against bigville's Python fallback across 30 (reserve × advantage) cells:

```
cells: 30   disagreements: 0
GRAPH RULE == PYTHON FALLBACK
```

including the one exact-tie cell (`reserve=1.0, advantage=0.0`, both options valued 10.0),
which both resolve identically.

## 5. What this does NOT establish

- **No trail forms.** This is heterogeneity of disposition only. §8's own claim is that
  desire paths need heterogeneity **and** stigmergic accumulation, and *neither suffices
  alone*. Traversal does not write back to terrain — walking over grass does not yet wear it
  toward `path`. That is probe 2, unrun, and it is the half that makes a path *persist*.
- **One junction, synthetic affordances.** Two constructed options, not a live town run.
- **`EFFORT_TO_SCORE` is uncalibrated.** 6.0 was chosen to make the effect legible against
  typical affordance scores (10–100), not derived. Whether it is the right loudness against
  real competing goals is unmeasured.
- **The tie-break is untouched.** `-int(n)` still decides exact ties in the fallback, and
  enumeration order in the rule. The wire reduces how often ties occur; it does not represent
  a tie-break.
- **Nothing about ocelot's own routing.** `qf_relax` / `portal.cost` and the
  `TIE_CONSEQUENTIALITY_RESULTS.md` routing ties are untouched.

## 6. Defects found, recorded, not fixed

- **The cheap-path `fatigue` pinning** (§0, correction 2) — live, silent, whole-network-row.
- **`cheap.py::_choice_key` is dead code.** Defined, never called; the live decider is
  `psi_can.choose`. It carries a stale duplicate of the path bonus and its own final
  tie-break, `str(option.get("target",""))` — **alphabetical by target name**, the same
  decide-ties-by-the-alphabet shape as `recognise_meta_shape` in `SHAPE_AUDIT.md`.
- **The cheap-path tie-break is noise, and per-turn.** `psi_can.tie_break` is
  `blake2b(character_id : turn : action : target)`. Per-character, which looks like
  disposition, but `turn` is in the payload, so the same resident breaks the same tie
  differently on consecutive turns. Nothing can accumulate across a flip-flopping choice, so
  it would actively prevent trail formation even once accumulation exists.

## 7. Reproduce

```bash
cd ~/ozmadev/bigville && python3 -m pytest -q tests/     # 211 passed
cd ~/ozmadev/bigville && python3 <scratchpad>/ocelot_route_probe.py
cd ~/ozmadev/ocelot   && python3 <scratchpad>/graph_table.py  /tmp/graph.json
cd ~/ozmadev/bigville && python3 <scratchpad>/mirror_table.py /tmp/mirror.json
```

**Instrument caveat, recorded because it produced a false result twice.** Both probes were
initially written as *reimplementations* of the code under test rather than calls into it.
The first hardcoded its own copy of the cheap path's `3.0` and reported HOMOGENEOUS after a
working wire had landed. The second used its own tie rule and reported a seed-rule
disagreement that was a property of the probe. Neither would have been caught by reading the
probe; both were caught by a result being implausible — identical to four decimal places, and
a single disagreement sitting exactly on an exact tie. **A probe that re-derives the quantity
it is measuring is measuring itself.**
