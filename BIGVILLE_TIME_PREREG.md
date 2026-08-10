# BIGVILLE R3 — DAY/NIGHT + THE ASYNC TEMPORAL SUBSTRATE (block 251000) — PRE-REGISTRATION

**Pre-registered BEFORE any number.** Spec: `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md`
§2.5 (TIME/ENERGY/DAY-NIGHT — the async substrate), §3 R3 (gates), §4 (async-
determinism / energy-spiral / sleeping-is-cheap RISKS). Architecture rule
(`experiments/gamma-substrate/CLAUDE.md`): every DECISION is a graph RULE; the world
adapter only advances the clock, applies state, ticks, and reads. Builds ON R1
(`bigville_move_world` + `bigville_move_energy`/`bigville_move_nav`), R2
(`bigville_need_world` + `bigville_need_*`), the scaffold (`bigville_sim_world`, whose
occlusion-gated LOS query RANGE the dark modulates), and REUSES the 239000 affect /
co-regulation machinery (`affective_state_core` AffectiveState + the arousal channel)
and the per-node async-epoch idiom (188000/177000; the `*_epoch` per-node clocks the
co-reg seed already rides).

## Seed claim — `python scripts/seed_claim.py 251000 251999` (verbatim)

```
SEED CLAIM 251000-251999: CLEAN -- no collision DETECTED.
  Scope: 971 files with seed sinks; 681 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
EXIT=0
```

Block 251000–251999 is CLEAN. All R3 numbers are deterministic (no RNG).

## Design commitments (bind before any number)

1. **Zero new Rust.** All decisions compose existing DSL Terms; `runners/dsl` diff
   EMPTY (incl. `term.rs`). If a new primitive seems required → STOP and report.
2. **Dark modulates the EXISTING query, no new perception system.** The scaffold's
   occlusion-gated `can_see` is overridden ONLY to consult a phase-driven sight
   RANGE (`_sight_range`, DAY = full `SIGHT_RANGE=7`, NIGHT = short); `_occluded`,
   `perceives`, `can_hear`, and the whole perception pipeline are unchanged. Dark
   shortens SIGHT only (a physical world fact, mechanical ingest — NOT an agent
   decision), never hearing.
3. **Async, not lockstep.** A world clock the adapter advances; agents act on their
   own tempo (an asleep/idle agent is not scheduled → produces ~0 work). Scheduling
   order is DETERMINISTIC (seeded fixed order over agent names), never wall-clock.
4. **Every decision is a RULE** in the isolated movement engine (`self.eng`), not
   Python: the sleep-or-defer decision (`bt_decide_sleep`, a `decision_value`
   trade-off), collapse (`bt_collapse`), replenish (`bt_replenish`), wake
   (`bt_wake`), and the witnessed-collapse concern (`bt_concern`). Source-audit gate.
5. **Additive only.** All-new `bigville_time_` files; no edit to any tracked file
   (subclass/import R1/R2 + scaffold + 239 seeds).

## Pre-registered gates

### G-dark-gates-witnessing (HEADLINE)
The SAME scheme at the SAME place (a villager at a fixed cell with day-range LOS into
John's occluded office) is WITNESSED by DAY and NOT by NIGHT (sight range shrinks
below the office distance). The 245 witness→credibility rule (`bd_villager_backs`)
therefore fires TIME-CONTINGENTLY: DAY arm `seen_hostile > 0` → **backs Mary**; NIGHT
arm `seen_hostile == 0` → **backs John**. Position + scheme held constant; the backing
flips on the day/night phase ALONE. **PASS** iff the DAY arm backs Mary with
`seen_hostile>0` and the NIGHT arm backs John with `seen_hostile==0`, same villager,
same cell. Ties the 245/247 credibility chain to WHEN as well as WHERE.

### G-sleep-is-chosen
A low-energy agent in a SAFE spot LATE (night) elects to SLEEP (`asleep→1`,
`sleep_kind=chosen`) and restful sleep REPLENISHES its R1 energy budget. A BUSY agent
(unfinished HIGH-urgency goal, same energy/safe/late) DEFERS (stays awake) — the
`decision_value` trade-off (sleep-drive vs goal-urgency). **Failing control:** remove
the sleep option (`sleep_enabled=0`) → the agent CANNOT sleep → depletes to COLLAPSE.
**PASS** iff: (a) tired+safe+late+idle → chosen sleep + energy rises to `rest_cap`;
(b) tired+safe+late+busy → defers (no sleep); (c) sleep_enabled=0 → runs to collapse.

### G-collapse-nonrestorative-and-witnessed
Pushing PAST the energy threshold (`energy < e_collapse`, sleep unavailable) →
INVOLUNTARY collapse-sleep WHEREVER the agent is (`collapsed→1`), and it is
NON-RESTORATIVE: post-collapse energy (`collapse_cap`) < post-restful-sleep energy
(`rest_cap`) — the spiral. A WITNESS to the collapse fires CONCERN (`bt_concern`
mints a `Concern` node + raises the witness's AffectiveState arousal / lowers valence);
an OCCLUDED collapse (no line-of-sight, so no `witnesses` edge minted) fires NO
concern. **PASS** iff: post-collapse energy < post-restful energy; a witness with LOS
to the collapse has a Concern node + arousal rise; an occluded observer has neither.
The witness/occlusion contingency reuses G-dark's phase-driven sight range.

### G-async-determinism (LOAD-BEARING, §4)
With day=CONSTANT (phase locked DAY → full sight range) + energy=∞ (no slow-down, no
sleep, no collapse) and NO movers, the async substrate is DECISION-IDENTICAL to the
current synchronous scaffold: `BigvilleTimeWorld(reduction=True).run(T)` produces
frame-by-frame IDENTICAL drama decisions (John held/stated, Mary inference/goal/claim,
every villager `backs`, reporter frame, newspaper) to `BigvilleSimWorld().run(T)` — so
every 245/247/248 landed number is UNCHANGED. Scheduling order is seeded/deterministic
(a repeat run is byte-identical). **PASS** iff the two frame streams are equal field-
for-field over T ticks AND a repeat run reproduces byte-identically.

### G-sleeping-is-cheap
Per-tick work (rule-fire steps, reusing R1's `_cost_steps` meter) measured across the
day/night phase: NIGHT (most agents asleep/idle → near-zero surprise → not scheduled)
must be CHEAPER per tick than DAY (agents navigating: floods + hops). **PASS** iff
mean night per-tick rule-fire steps < mean day per-tick rule-fire steps (report the
day-vs-night cost). A night MORE expensive than day would be the falsifier.

### G-discipline
- `runners/dsl` diff EMPTY (no Rust); `source_match in {own, shared}` (own build here).
- Canonical `.so` md5 unchanged start==end (recorded: `fd82dc2978dbb055496dd82390ac2ebe`).
- Oracles `rung7_vision_bench.sh` + `per_area_settlement_regression.sh`: fail-set ⊆
  the enumerated `results/failure_baseline.json`; `test_failure_baseline_migrated`
  green; ZERO new reds. (A pre-existing main provenance red is NOT mine; the
  enumerated baseline is the arbiter.)
- Source-audit: the world adapter runs no rule engine (`graph_rewrite`/`gr.run`/
  `_match`/`_apply`/`make_rule`) and holds no sleep/concern decision — all in seeds.
- Failing controls that ACTUALLY fail (busy defers; sleep_enabled=0 collapses;
  occluded → no concern).

## Honest scope
Synthetic small-cast model (the 245 scaffold cast + R1/R2 movers). Mechanism-proven ≠
benchmark. N-scope: the gates use a handful of agents; the async/sleeping-is-cheap
cost claim is a per-tick rule-fire-step ratio, not a wall-clock 200-agent measurement.
