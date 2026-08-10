"""bigville R30 (block 319000): the church -- Mary the pastor, a non-denominational
public congregation (emergent, each resident's collapse over {go,stay}), and a
private counsel room whose confidences stay confidential. Gates mirror
BIGVILLE_CHURCH_PREREG.md. hold/decide/enter/counsel are seed rules (ch_*).
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_church_world import BigvilleChurchWorld   # noqa: E402

# a piety-spread congregation with differing creeds (non-denominational must not gate).
_FLOCK = [
    ("Devout",    dict(piety=1.0, worldly_pull=0.2, creed="methodist")),
    ("Moderate",  dict(piety=0.5, worldly_pull=0.3, creed="quaker")),
    ("Worldly",   dict(piety=0.2, worldly_pull=0.5, creed="none")),
    ("Faithless", dict(piety=0.05, worldly_pull=0.4, creed="atheist")),
]


def _church(pastor_draw=0.8, flock=_FLOCK):
    w = BigvilleChurchWorld(pastor_draw=pastor_draw)
    for n, d in flock:
        w.add_resident(n, **d)
    return w


# ------------------------------------------------------ G-service-held / pastor-is-Mary (headline)
def test_mary_holds_a_service_at_a_nondenominational_church():
    w = _church()
    assert w.pastor_name() == "Mary", "Mary is the pastor"
    assert w.is_non_denominational(), "the church is non-denominational"
    w.sunday()
    assert w.congregation_size() >= 1, "a service was held and drew a congregation"


# ------------------------------------------------------ G-emergent-congregation (headline)
def test_the_congregation_emerges_from_piety():
    w = _church()
    w.sunday()
    cong = w.congregation()
    assert "Devout" in cong, "the devout attend"
    assert "Faithless" not in cong, "the faithless stay away"
    assert 1 <= w.congregation_size() < len(_FLOCK), f"emergent, not everyone/no-one: {cong}"


# ------------------------------------------------------ G-private-counsel-is-confidential (headline)
def test_private_counsel_eases_distress_and_stays_confidential():
    w = _church()
    w.seek_counsel("Worldly", confides="I stole from the collection plate", distress=1.0)
    assert w.distress_of("Worldly") == 0.5, "the private counsel eased the distress"
    disclosures = w.private_disclosures()
    assert len(disclosures) == 1, "Mary holds exactly what was confided"
    content, private, public = disclosures[0]
    assert content == "I stole from the collection plate"
    assert private == 1.0 and public == 0.0, "the confession is confidential -- never public"


# ------------------------------------------------------ G-non-denominational
def test_creed_does_not_gate_attendance():
    """A pious resident of a minority creed attends -- attendance is faith, not creed."""
    w = BigvilleChurchWorld(pastor_draw=0.8)
    w.add_resident("PiousQuaker", piety=1.0, worldly_pull=0.2, creed="quaker")
    w.add_resident("PiousPagan", piety=1.0, worldly_pull=0.2, creed="pagan")
    w.sunday()
    assert set(w.congregation()) == {"PiousQuaker", "PiousPagan"}, \
        "both attend regardless of creed (non-denominational)"


# ------------------------------------------------------ G-pastor-draw-is-load-bearing
def test_a_more_drawing_pastor_gathers_a_larger_congregation():
    big = _church(pastor_draw=0.8); big.sunday()
    small = _church(pastor_draw=0.3); small.sunday()
    assert big.congregation_size() > small.congregation_size(), \
        f"draw is load-bearing: {big.congregation()} vs {small.congregation()}"


# ------------------------------------------------------ G-attendance-is-the-residents-decision
def test_residents_diverge_on_the_same_service():
    w = _church()
    w.sunday()
    cong = set(w.congregation())
    assert cong and cong != {n for n, _ in _FLOCK}, "some attend, some do not -- their own decision"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_attendance():
    src = open(os.path.join(_ROOT, "worlds", "bigville_church_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_church.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"ch_hold_service", "ch_decide", "ch_enter", "ch_counsel_private"} <= names, names
    assert "Argmax" in json.dumps(seed), "the attend decision must be an Argmax collapse in the seed"
