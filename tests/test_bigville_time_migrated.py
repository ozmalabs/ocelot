"""bigville R3 (block 251000) -- DAY/NIGHT + the async temporal substrate gates.

Graph-native day/night: dark modulates the scaffold's occlusion sight-query RANGE;
autonomous SLEEP is a decision_value RULE; exhaustion COLLAPSE is a RULE and is
NON-restorative (the spiral); a WITNESSED collapse fires CONCERN (occlusion-gated,
reusing the 239000 affect channel); the async substrate REDUCES to the synchronous
scaffold at day=const+energy=inf; a sleeping town is CHEAP. Gates mirror
BIGVILLE_TIME_PREREG.md. No agent decision lives in Python -- every sleep / collapse
/ concern / credibility verdict is a rule (source-audit test below).
"""
from __future__ import annotations

import json
import os
import re
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_time_world import BigvilleTimeWorld, DAY, NIGHT   # noqa: E402
from worlds.bigville_sim_world import BigvilleSimWorld                 # noqa: E402

OFFICE_LOS_CELL = (21, 6)   # clear SIGHT into the office (dist 16) but BEYOND hearing
                            # (11) -> office witnessing is SIGHT-only -> the night
                            # sight-shrink gates it, hearing held constant.


# ------------------------------------------------ HEADLINE: dark gates witnessing
def _office_arm(phase):
    w = BigvilleTimeWorld(day_range=16, night_range=3)
    w.pos["villager_1"] = OFFICE_LOS_CELL       # SAME place, held constant
    w.set_phase(phase)                          # SAME scheme; only the phase differs
    for _ in range(11):
        w.step(move=False)
    b = w.backs_of("villager_1")
    w.close()
    return b


def test_headline_dark_gates_witnessing():
    """G-dark-gates-witnessing: the SAME scheme at the SAME cell is WITNESSED by DAY
    (seen_hostile>0 -> backs Mary) and NOT by NIGHT (short sight range -> seen_hostile
    0 -> backs John). The 245 credibility rule fires time-contingently, flipping on
    the day/night phase ALONE -- position + scheme + hearing all held constant."""
    day = _office_arm(DAY)
    night = _office_arm(NIGHT)
    # DAY: witnesses the office scheme -> backs Mary
    assert day["seen_hostile"] > 0 and day["backs"] == "Mary", day
    # NIGHT: sight range shrinks below the office distance -> witnesses nothing -> John
    assert night["seen_hostile"] == 0 and night["backs"] == "John", night
    # the ONLY difference is the sight-witnessed hostility: the non-sight signals
    # (paper-borne heard_claim, the seed benevolence prior) are IDENTICAL across arms,
    # so the flip is on the phase-driven sight range alone, not any other channel.
    assert day["heard_claim"] == night["heard_claim"], (day, night)
    assert day["seen_benevolent"] == night["seen_benevolent"], (day, night)


# ------------------------------------------------ async determinism (reduction)
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


def test_async_reduces_to_scaffold_and_is_deterministic():
    """G-async-determinism (LOAD-BEARING): with day=const + energy=inf + no movers the
    async substrate is DECISION-IDENTICAL to the synchronous scaffold over 14 ticks
    (so every 245/247/248 landed number is UNCHANGED), and a repeat run reproduces
    byte-identically (seeded, deterministic scheduling -- not wall-clock)."""
    T = 14
    scaffold = _decisions(BigvilleSimWorld().run(T))
    red = _decisions(BigvilleTimeWorld(day_const=True).run(T, move=True))
    red2 = _decisions(BigvilleTimeWorld(day_const=True).run(T, move=True))
    assert red == scaffold, "async(day=const,energy=inf) must equal the scaffold"
    assert red == red2, "async scheduling must be deterministic across runs"


# ------------------------------------------------ sleep is chosen (vs defer / collapse)
def _sleep_traj(ticks=8, **cfg):
    base = dict(energy=20.0, safe=1.0, sleep_threshold=50.0)
    base.update(cfg)
    w = BigvilleTimeWorld()
    w.add_mover("v", (14, 8))
    w.configure_time("v", **base)
    w.set_phase(NIGHT)
    traj = [dict(**{k: w.sleep_state("v")[k] for k in ("sleep_kind", "asleep", "energy")})
            for _ in _iter(w, ticks)]
    w.close()
    return traj


def _iter(w, ticks):
    for _ in range(ticks):
        w.run_sleep_decisions()
        yield True


def test_sleep_is_chosen_busy_defers_no_option_collapses():
    """G-sleep-is-chosen: a tired+safe+late+IDLE agent elects to SLEEP and restful
    sleep replenishes to rest_cap; a BUSY agent (high goal_urgency) DEFERS; removing
    the sleep option (sleep_enabled=0) makes it run to COLLAPSE. The decision_value
    trade-off (sleep_drive vs goal_urgency) is a RULE."""
    idle = _sleep_traj(goal_urgency=0.0)
    busy = _sleep_traj(goal_urgency=100.0)
    noopt = _sleep_traj(goal_urgency=0.0, sleep_enabled=0.0, energy=2.0)
    # idle chose restful sleep and replenished to rest_cap (100)
    assert idle[-1]["sleep_kind"] == 1 and idle[-1]["energy"] == 100.0, idle
    # busy DEFERRED -- never asleep, energy unchanged (kept pursuing the goal)
    assert all(t["asleep"] == 0 and t["sleep_kind"] == 0 for t in busy), busy
    assert busy[-1]["energy"] == 20.0, busy
    # failing control: option removed -> collapse (kind 2), not a chosen sleep
    assert noopt[-1]["sleep_kind"] == 2, noopt


# ------------------------------------------------ collapse non-restorative + witnessed
def _concern_case(phase, ticks=4):
    w = BigvilleTimeWorld(day_range=16, night_range=3)
    w.add_mover("victim", (5, 4))
    w.configure_time("victim", energy=2.0, sleep_enabled=0.0)   # cannot sleep -> collapse
    w.add_mover("witness", OFFICE_LOS_CELL)                     # LOS to office by day only
    w.attach_affect("witness")
    w.set_phase(phase)
    for _ in range(ticks):
        w.run_sleep_decisions()
        w.register_collapse_and_concern()
    out = dict(victim=w.sleep_state("victim"), witness=w.affect_state("witness"),
               concern=w.concern_count())
    w.close()
    return out


def test_collapse_is_nonrestorative_and_witnessed_concern_is_occlusion_gated():
    """G-collapse-nonrestorative-and-witnessed: exhaustion collapse recovers only to
    collapse_cap, STRICTLY BELOW a restful sleep's rest_cap (the spiral). A collapse
    with a witness in line-of-sight fires CONCERN (a Concern node + the witness's
    arousal up / valence down); the SAME collapse OCCLUDED (night short range) fires
    NONE -- concern is occlusion-gated (ties to G-dark)."""
    post_restful = _sleep_traj(goal_urgency=0.0)[-1]["energy"]     # a restful sleep -> 100
    day = _concern_case(DAY)
    night = _concern_case(NIGHT)
    post_collapse = day["victim"]["energy"]
    # the spiral: post-collapse energy strictly below post-restful energy
    assert day["victim"]["sleep_kind"] == 2, day
    assert post_collapse < post_restful, (post_collapse, post_restful)
    # WITNESSED (day): concern fires -- a Concern node + an affective response
    assert day["concern"] == 1 and day["witness"]["concerned"] == 1, day
    assert day["witness"]["arousal"] > 0 and day["witness"]["valence"] < 5.0, day
    # OCCLUDED (night): the same collapse draws NO concern
    assert night["concern"] == 0 and night["witness"]["concerned"] == 0, night
    assert night["witness"]["arousal"] == 0.0, night


# ------------------------------------------------ sleeping is cheap
def test_sleeping_is_cheap_night_cheaper_than_day():
    """G-sleeping-is-cheap: movement-engine per-tick work in a DAY block (movers
    navigate: floods + hops) vs a NIGHT block (the town sleeps -> not scheduled ->
    near-zero work). Night is CHEAPER per tick than day (compute proportional to
    surprise)."""
    w = BigvilleTimeWorld(day_range=16, night_range=3)
    for name, start, goal in (("m0", (2, 2), (27, 15)), ("m1", (27, 2), (2, 15)),
                              ("m2", (2, 15), (27, 2))):
        w.add_mover(name, start, goal, energy=100.0, energy_cost=6.0)
        w.configure_time(name, safe=1.0, sleep_threshold=60.0, rest_gain=5.0)
    w.set_phase(DAY)
    for _ in range(5):
        w.step(move=True)
    w.set_phase(NIGHT)
    for _ in range(5):
        w.step(move=True)
    cost = w.day_night_cost()
    asleep = sum(1 for n in ("m0", "m1", "m2") if w.sleep_state(n)["asleep"] == 1)
    w.close()
    assert asleep == 3, "the town should be asleep through the night"
    assert cost["night_mean"] < cost["day_mean"], cost
    # a sleeping night is DRAMATICALLY cheaper (near-zero work), not marginally
    assert cost["night_mean"] < 0.1 * cost["day_mean"], cost


# ------------------------------------------------ discipline / source-audit
def test_decisions_are_rules_not_python():
    """Source-audit: the world adapter runs NO rule engine and holds no sleep /
    collapse / concern decision; the decisions live in the seeds (bt_decide_sleep,
    bt_collapse, bt_replenish, bt_wake, bt_concern)."""
    wf = open(os.path.join(_ROOT, "worlds", "bigville_time_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "gr._match", "gr._apply"):
        assert forbidden not in wf, f"world adapter calls a rule engine: {forbidden}"
    sleep = json.load(open(os.path.join(_ROOT, "seeds", "bigville_time_sleep.json")))
    concern = json.load(open(os.path.join(_ROOT, "seeds", "bigville_time_concern.json")))
    names = {r["name"] for r in sleep["rules"]} | {r["name"] for r in concern["rules"]}
    assert {"bt_decide_sleep", "bt_collapse", "bt_replenish", "bt_wake",
            "bt_concern"} <= names, names
    # the sleep decision is a decision_value trade-off (IfThenElse over energy/urgency)
    dec = next(r for r in sleep["rules"] if r["name"] == "bt_decide_sleep")
    assert "goal_urgency" in json.dumps(dec) and "sleep_threshold" in json.dumps(dec)


def test_no_new_rust_and_engine_invariant():
    """No new Rust primitive: the R3 seeds compose existing DSL Terms only, and the
    engine provenance asserts the INVARIANT (source_match in {own, shared}) -- never a
    pinned md5 (lesson 7b)."""
    from domains.engine_provenance import engine_provenance
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), p
    used = set()
    for seed in ("bigville_time_sleep", "bigville_time_concern"):
        d = json.load(open(os.path.join(_ROOT, "seeds", seed + ".json")))
        used |= set(re.findall(r'"type":\s*"([A-Z][A-Za-z]+)"', json.dumps(d)))
    known = {"Attr", "Var", "Lit", "Plus", "Minus", "Times", "Max", "Lt", "Gte",
             "Eq", "Gt", "And", "Not", "IfThenElse", "Exists", "Neighbours"}
    assert used <= known, f"unexpected Term(s) -- new Rust? {used - known}"
