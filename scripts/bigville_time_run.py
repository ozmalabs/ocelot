#!/usr/bin/env python3
"""bigville R3 (block 251000) -- DAY/NIGHT + the async temporal substrate runner.

Produces every pre-registered number (BIGVILLE_TIME_PREREG.md) and writes
results/bigville_time/results.json. Read-only glass-box: the adapter advances the
clock, applies rule-decided state, ticks, and reads. Every decision is a RULE.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_time_world import BigvilleTimeWorld, DAY, NIGHT   # noqa: E402
from worlds.bigville_sim_world import BigvilleSimWorld                 # noqa: E402
from domains.engine_provenance import engine_provenance               # noqa: E402

OFFICE_LOS_CELL = (21, 6)   # clear SIGHT line into John's office (dist 16), BEYOND
                            # hearing range (11) -> office witnessing is SIGHT-only,
                            # so the sight-range shrink at night gates it cleanly.


# ------------------------------------------------ G-dark-gates-witnessing (HEADLINE)
def g_dark():
    arms = {}
    for phase, label in ((DAY, "day"), (NIGHT, "night")):
        w = BigvilleTimeWorld(day_range=16, night_range=3)
        w.pos["villager_1"] = OFFICE_LOS_CELL       # SAME place, held constant
        w.set_phase(phase)                          # SAME scheme; only the phase differs
        for _ in range(11):
            w.step(move=False)
        b = w.backs_of("villager_1")
        arms[label] = dict(pos=list(b["pos"]), sight_range=w._sight_range,
                           seen_hostile=b["seen_hostile"],
                           seen_benevolent=b["seen_benevolent"],
                           heard_claim=b["heard_claim"], backs=b["backs"])
        w.close()
    passed = (arms["day"]["seen_hostile"] > 0 and arms["day"]["backs"] == "Mary"
              and arms["night"]["seen_hostile"] == 0 and arms["night"]["backs"] == "John")
    return dict(gate="G-dark-gates-witnessing", passed=passed, arms=arms,
                note=("SAME villager, SAME cell; seen_benevolent + heard_claim IDENTICAL "
                      "across arms -- ONLY seen_hostile (the sight-witnessed office "
                      "scheme) differs, flipping the 245 credibility rule on phase alone"))


# ------------------------------------------------ G-async-determinism (reduction)
def _decisions(frames):
    out = []
    for f in frames:
        row = []
        for inh in f["inhabitants"]:
            s = inh["state"]
            row.append((inh["id"], s.get("backs"), s.get("held_intent"),
                        s.get("inferred_disposition"), s.get("goal"),
                        inh.get("x"), inh.get("y")))
        np = f.get("newspaper")
        out.append((f["tick"], tuple(row), np.get("frame") if np else None))
    return out


def g_async(T=14):
    base = BigvilleSimWorld().run(T)
    scaffold = _decisions(base)
    # reduction limit: day=constant + energy=inf (no movers, no sleep/collapse)
    red = BigvilleTimeWorld(day_const=True)
    red_dec = _decisions(red.run(T, move=True))
    red2 = BigvilleTimeWorld(day_const=True)
    red2_dec = _decisions(red2.run(T, move=True))
    identical = (scaffold == red_dec)
    deterministic = (red_dec == red2_dec)
    return dict(gate="G-async-determinism", passed=(identical and deterministic),
                reduces_to_scaffold=identical, deterministic_repeat=deterministic,
                ticks=T,
                note=("day=const + energy=inf + no movers => decision-identical to the "
                      "synchronous scaffold over %d ticks (245/247/248 numbers unchanged); "
                      "a repeat run is byte-identical (seeded deterministic scheduling)" % T))


# ------------------------------------------------ G-sleep-is-chosen
def _sleep_traj(ticks=8, **cfg):
    base = dict(energy=20.0, safe=1.0, sleep_threshold=50.0)
    base.update(cfg)
    w = BigvilleTimeWorld()
    w.add_mover("v", (14, 8))
    w.configure_time("v", **base)
    w.set_phase(NIGHT)
    traj = []
    for _ in range(ticks):
        w.run_sleep_decisions()
        s = w.sleep_state("v")
        traj.append(dict(kind=s["sleep_kind"], asleep=s["asleep"],
                         collapsed=s["collapsed"], energy=s["energy"]))
    w.close()
    return traj


def g_sleep():
    idle = _sleep_traj(goal_urgency=0.0)          # tired+safe+late+idle -> chooses sleep
    busy = _sleep_traj(goal_urgency=100.0)        # unfinished high-urgency goal -> DEFERS
    noopt = _sleep_traj(goal_urgency=0.0, sleep_enabled=0.0, energy=2.0)  # option removed
    passed = (idle[-1]["kind"] == 1 and idle[-1]["energy"] == 100.0        # chose restful
              and all(t["kind"] == 0 and t["asleep"] == 0 for t in busy)   # deferred
              and noopt[-1]["kind"] == 2)                                  # ran to collapse
    return dict(gate="G-sleep-is-chosen", passed=passed,
                idle_final=idle[-1], busy_final=busy[-1], noopt_final=noopt[-1],
                idle_energy_curve=[t["energy"] for t in idle],
                busy_energy_curve=[t["energy"] for t in busy],
                noopt_energy_curve=[t["energy"] for t in noopt],
                note=("decision_value trade-off: sleep_drive vs goal_urgency. idle "
                      "chooses restful sleep (energy->rest_cap 100); busy DEFERS "
                      "(never asleep); sleep_enabled=0 removes the option -> collapse"))


# ------------------------------------------------ G-collapse-nonrestorative-and-witnessed
def _concern_case(phase, ticks=4):
    w = BigvilleTimeWorld(day_range=16, night_range=3)
    w.add_mover("victim", (5, 4))
    w.configure_time("victim", energy=2.0, sleep_enabled=0.0)   # cannot sleep -> collapses
    w.add_mover("witness", OFFICE_LOS_CELL)                     # LOS to office by day only
    w.attach_affect("witness")
    w.set_phase(phase)
    for _ in range(ticks):
        w.run_sleep_decisions()
        w.register_collapse_and_concern()
    return dict(victim=w.sleep_state("victim"), witness=w.affect_state("witness"),
                concern_nodes=w.concern_count(), close=w.close)


def g_collapse():
    # post-restful energy for the reference (a chosen restful sleep reaches rest_cap)
    ref = _sleep_traj(goal_urgency=0.0)
    post_restful = ref[-1]["energy"]
    day = _concern_case(DAY)
    night = _concern_case(NIGHT)
    post_collapse = day["victim"]["energy"]
    day["close"](); night["close"]()
    passed = (post_collapse < post_restful                         # the spiral
              and day["victim"]["sleep_kind"] == 2                 # was a collapse
              and day["concern_nodes"] == 1                        # witnessed -> concern
              and day["witness"]["concerned"] == 1
              and day["witness"]["arousal"] > 0
              and night["concern_nodes"] == 0                      # occluded -> NO concern
              and night["witness"]["concerned"] == 0)
    return dict(gate="G-collapse-nonrestorative-and-witnessed", passed=passed,
                post_restful_energy=post_restful, post_collapse_energy=post_collapse,
                spiral=(post_collapse < post_restful),
                witnessed_day=dict(concern_nodes=day["concern_nodes"],
                                   arousal=day["witness"]["arousal"],
                                   valence=day["witness"]["valence"],
                                   concerned=day["witness"]["concerned"]),
                occluded_night=dict(concern_nodes=night["concern_nodes"],
                                    arousal=night["witness"]["arousal"],
                                    valence=night["witness"]["valence"],
                                    concerned=night["witness"]["concerned"]),
                note=("collapse is NON-restorative (post-collapse %s < post-restful %s); "
                      "a WITNESS with line-of-sight fires concern (arousal up, valence "
                      "down, Concern node); the SAME collapse OCCLUDED at night (short "
                      "sight range) fires none -- concern is occlusion-gated (ties G-dark)"
                      % (post_collapse, post_restful)))


# ------------------------------------------------ G-sleeping-is-cheap
def g_cheap(day_ticks=5, night_ticks=5):
    """Per-tick movement-engine work: a DAY block where movers navigate (floods +
    hops) vs a NIGHT block where the town is asleep. By DAY (lateness=0) movers can
    only navigate; by NIGHT they are tired (depleted by the day) + safe + late ->
    SLEEP -> not scheduled -> near-zero work (compute proportional to surprise). A
    slow night-replenish keeps them asleep through the night. Night must be CHEAPER
    per tick than day."""
    w = BigvilleTimeWorld(day_range=16, night_range=3)
    routes = [("m0", (2, 2), (27, 15)), ("m1", (27, 2), (2, 15)), ("m2", (2, 15), (27, 2))]
    for name, start, goal in routes:
        w.add_mover(name, start, goal, energy=100.0, energy_cost=6.0)
        # carry a bedroll (safe); rest slowly so a night's sleep does not fully wake
        # them mid-night -> a sleeping town stays asleep and stays cheap.
        w.configure_time(name, safe=1.0, sleep_threshold=60.0, rest_gain=5.0)
    w.set_phase(DAY)
    for _ in range(day_ticks):
        w.step(move=True)
    w.set_phase(NIGHT)
    for _ in range(night_ticks):
        w.step(move=True)
    cost = w.day_night_cost()
    asleep = sum(1 for n in ("m0", "m1", "m2")
                 if w.sleep_state(n)["asleep"] == 1)
    w.close()
    passed = cost["night_mean"] < cost["day_mean"] and asleep == 3
    return dict(gate="G-sleeping-is-cheap", passed=passed,
                day_mean=cost["day_mean"], night_mean=cost["night_mean"],
                day_total=cost["day_total"], night_total=cost["night_total"],
                day_ticks=cost["day_ticks"], night_ticks=cost["night_ticks"],
                movers_asleep_at_night=asleep, per_tick=cost["per_tick"],
                note=("movement-engine rule-fire steps per tick: DAY movers navigate "
                      "(floods+hops); NIGHT movers sleep -> not scheduled -> ~0 work "
                      "(compute proportional to surprise). Night cheaper than day."))


def main():
    prov = engine_provenance()
    gates = [g_dark(), g_async(), g_sleep(), g_collapse(), g_cheap()]
    all_pass = all(g["passed"] for g in gates)
    out = dict(block=251000, all_pass=all_pass,
               engine=dict(source_match=prov["source_match"],
                           sha256=prov["sha256"][:16]),
               gates=gates)
    dst = os.path.join(_ROOT, "results", "bigville_time")
    os.makedirs(dst, exist_ok=True)
    with open(os.path.join(dst, "results.json"), "w") as f:
        json.dump(out, f, indent=1)
    for g in gates:
        print("%-42s %s" % (g["gate"], "PASS" if g["passed"] else "FAIL"))
    print("ALL_PASS =", all_pass, "| engine source_match =", prov["source_match"])
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
