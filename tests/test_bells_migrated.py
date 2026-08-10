"""bigville R31 (block 320000): the church bells are the clock -- time is not forced.
The sexton rings the bell; the peal is heard across town; each resident learns the
hour from the bell and CHOOSES whether to answer. A rested sleeper wakes; an
exhausted one sleeps through and never learns the time. Gates mirror
BIGVILLE_BELLS_PREREG.md. ring/hear/wake/decide/attend are seed rules (bl_*).
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_bell_world import BigvilleBellWorld   # noqa: E402


def _town():
    w = BigvilleBellWorld()
    w.add_resident("Awake",     piety=1.0, worldly_pull=0.2, rest=1.0, asleep=0)
    w.add_resident("Rested",    piety=0.9, worldly_pull=0.2, rest=0.8, asleep=1)  # abed, rested
    w.add_resident("Exhausted", piety=1.0, worldly_pull=0.2, rest=0.1, asleep=1)  # abed, spent
    w.add_resident("Worldly",   piety=0.2, worldly_pull=0.6, rest=1.0, asleep=0)  # awake, undrawn
    return w


# ------------------------------------------------------ G-bell-tells-the-time (headline)
def test_the_bell_tells_the_time():
    w = _town()
    assert all(w.known_hour(n) is None for n in ("Awake", "Rested", "Exhausted", "Worldly")), \
        "before any bell no one knows the hour (unknown = absence)"
    w.ring_bell(8, kind="service")
    assert w.known_hour("Awake") == 8 and w.known_hour("Worldly") == 8, "hearers learn the hour from the bell"


# ------------------------------------------------------ G-rested-wake-exhausted-sleep-through (headline)
def test_the_rested_wake_and_the_exhausted_sleep_through():
    w = _town()
    w.ring_bell(8, kind="service")
    assert w.woke_at_bell("Rested") and not w.is_asleep("Rested"), "a rested sleeper wakes at the bell"
    assert w.known_hour("Rested") == 8, "and learns the hour"
    assert w.is_asleep("Exhausted"), "an exhausted sleeper does not wake"
    assert w.known_hour("Exhausted") is None, "it slept through -- it never learned the time"


# ------------------------------------------------------ G-heard-across-the-town
def test_the_peal_is_heard_across_the_town():
    w = _town()
    w.ring_bell(8, kind="service")
    # everyone who could perceive it heard the one peal; only the spent sleeper missed it.
    assert w.heard_last("Awake") and w.heard_last("Rested") and w.heard_last("Worldly")
    assert not w.heard_last("Exhausted")


# ------------------------------------------------------ G-attendance-is-chosen-not-scripted (headline)
def test_attendance_is_chosen_not_scripted():
    w = _town()
    w.ring_bell(8, kind="service")
    cong = w.congregation()
    assert "Awake" in cong and "Rested" in cong, "the drawn who heard the call answer it"
    assert "Worldly" not in cong, "one who heard but was not drawn CHOSE not to attend"
    assert "Exhausted" not in cong, "one who slept through never perceived the call, so cannot attend"


# ------------------------------------------------------ G-no-forced-global-clock (falsifier / architecture)
def test_no_bell_no_time_and_the_town_has_no_clock():
    w = _town()
    # the Town node carries no `now`/`sunday`/`day` clock driving the agents.
    town_attrs = set(w.eng.node(w._town)["attrs"])
    assert not (town_attrs & {"now", "sunday", "day", "hour", "clock", "tick"}), \
        f"the town must hold no global clock: {town_attrs}"
    # with no bell rung, nobody knows the time and nobody attends.
    assert all(w.known_hour(n) is None for n in ("Awake", "Worldly"))
    assert w.congregation() == []
    # ring at 8, then again at 12 -> hearers update the hour (time is what the bells say).
    w.ring_bell(8, kind="service")
    assert w.known_hour("Awake") == 8
    w.ring_bell(12, kind="noon")
    assert w.known_hour("Awake") == 12, "re-ringing updates the hour every hearer holds"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_response():
    src = open(os.path.join(_ROOT, "worlds", "bigville_bell_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_bells.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"bl_ring", "bl_hear_awake", "bl_wake_rested", "bl_decide", "bl_attend"} <= names, names
    assert "Argmax" in json.dumps(seed), "the answer must be an Argmax collapse in the seed"
