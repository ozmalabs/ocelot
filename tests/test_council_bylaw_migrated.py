"""bigville R32 (block 322000): the council's meeting schedule is a bylaw, enacted by
the beadle, on bell time -- not now_day % cadence. Gates mirror
BIGVILLE_COUNCIL_BYLAW_PREREG.md. count/ring/convene are seed rules (cb_*).
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_council_bylaw_world import BigvilleCouncilBylawWorld   # noqa: E402


def _council(interval=3):
    w = BigvilleCouncilBylawWorld()
    for n in ("Ada", "Bram", "Cato"):
        w.add_councillor(n, bloc="poor")
    for n in ("Dane", "Esme"):
        w.add_councillor(n, bloc="rich")
    w.set_meeting_bylaw(interval)
    return w


# ------------------------------------------------------ G-schedule-is-a-bylaw (headline)
def test_the_meeting_schedule_is_a_bylaw():
    w = _council(interval=3)
    assert w.meeting_interval() == 3, "the interval is a Law in the book (a bylaw)"
    town_attrs = set(w.eng.node(w._town)["attrs"])
    assert not (town_attrs & {"now_day", "cadence", "day", "now"}), \
        f"no global day/cadence clock on the town: {town_attrs}"
    seed = json.dumps(json.load(open(os.path.join(_ROOT, "seeds", "bigville_council_bylaw.json"))))
    assert "Mod" not in seed, "no integer-modulo scheduling in the seed"


# ------------------------------------------------------ G-beadle-rings-on-schedule (headline)
def test_the_beadle_convenes_the_council_on_the_bylaw_interval():
    w = _council(interval=3)
    assert w.meetings_convened() == 0
    w.toll_curfew(); assert w.meetings_convened() == 0, "no meeting on day 1"
    w.toll_curfew(); assert w.meetings_convened() == 0, "no meeting on day 2"
    w.toll_curfew(); assert w.meetings_convened() == 1, "the beadle rings the assembly on day 3"
    assert w.days_since_meeting() == 0, "the tally resets after the meeting"


# ------------------------------------------------------ G-convene-on-the-bell-not-math
def test_no_curfew_no_meeting():
    w = _council(interval=3)
    # never toll the bell -> the beadle never counts, the council never convenes.
    w.run()
    assert w.meetings_convened() == 0 and w.days_since_meeting() == 0


# ------------------------------------------------------ G-amend-the-bylaw-changes-the-calendar (headline)
def test_the_council_amends_its_own_calendar():
    w = _council(interval=3)
    for _ in range(3):
        w.toll_curfew()
    assert w.meetings_convened() == 1 and w.meeting_interval() == 3
    # the council votes to meet more often: every 2 days.
    w.amend_meeting_bylaw(2, aids_bloc="poor", threshold=3)
    assert w.meeting_interval() == 2, "the bylaw is amended by the council's own vote"
    base = w.meetings_convened()
    w.toll_curfew(); w.toll_curfew()
    assert w.meetings_convened() == base + 1, "now a meeting falls after 2 curfew days, not 3"


# ------------------------------------------------------ G-no-integer-clock (falsifier / architecture)
def test_meetings_recur_every_interval_by_the_actor_not_a_modulo():
    w = _council(interval=2)
    convened_on = []
    for day in range(1, 7):
        w.toll_curfew()
        convened_on.append(w.meetings_convened())
    # a meeting every 2 days: cumulative counts 0,1,1,2,2,3
    assert convened_on == [0, 1, 1, 2, 2, 3], convened_on


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_schedules_the_council():
    src = open(os.path.join(_ROOT, "worlds", "bigville_council_bylaw_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden!r}"
    # the schedule must be graph data, not a Python modulo -- checked at the seed/town
    # level in the other gates (no `Mod` in the seed, no `now_day`/`cadence` on the town).
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_council_bylaw.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"cb_beadle_counts", "cb_ring_assembly", "cb_convene"} <= names, names
