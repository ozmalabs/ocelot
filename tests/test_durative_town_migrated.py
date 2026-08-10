"""Gate for the FAST-TICK / SURPRISE-GATED town (block 283000,
worlds/bigville_durative_town_world.py).

The master tick is the HOP (no teleport); a DECISION fires on SURPRISE -- observation
!= the resident's held social prediction -- not on a clock and not on an enumerated
"encounter" event. The discriminating test (surprise vs event): a PREDICTED meeting
fires NO decision (you set out to meet them) yet still produces a habitual chat; an
UNPREDICTED meeting fires a decision. Between surprises a resident just continues its
durative action -- so decisions are O(surprise), not O(residents x ticks).

Scope: this harness demonstrates the CLOCK (fast hop tick, durative walk, surprise-
gated decision sparsity, walk-and-talk). The prediction-as-dict is a demonstrator
stand-in for the graph-native held-prediction (perception's held-surface/residual);
the actual conduct/speech CHOICE at a surprise point is the collapse (282000) /
speech faculty (278000), out of scope here. See BIGVILLE_DURATIVE_TOWN_RESULTS.md.
"""
from worlds.bigville_durative_town_world import BigvilleDurativeTownWorld as W
from worlds.bigville_durative_town_world import _adjacent


def _meeting_tick(w, a, b):
    for t, pos in w.pos_log:
        if _adjacent(pos[a], pos[b], w.range_r):
            return t
    return None


def _decisions_at(w, tick, who):
    return [d for d in w.decisions if d["tick"] == tick and d["who"] in who]


def test_no_teleport_hop_is_one_step():
    w = W([{"name": "A", "pos": (0, 0), "goal": (8, 3)}])
    w.run(20)
    assert w.max_hop == 1                     # every tick moves at most one cell
    assert w.pos["A"] == (8, 3)               # and it did arrive


def test_a_predicted_walk_fires_no_decisions():
    """Walking a known route with nobody unexpected -> ZERO decisions; the resident
    just continues (the habitual fast path, no collapse)."""
    w = W([{"name": "A", "pos": (0, 0), "goal": (10, 0)}])
    w.run(10)
    assert w.decision_count() == 0


def test_surprise_gates_decisions_not_encounters():
    """THE discriminator. Same crossing geometry, two prediction states:
    unexpected -> a decision at the meeting; predicted -> none (but still a chat)."""
    unexp = W([{"name": "A", "pos": (0, 0), "goal": (6, 0)},
               {"name": "B", "pos": (3, -2), "goal": (3, 3)}])
    unexp.run(8)
    mt = _meeting_tick(unexp, "A", "B")
    assert len(_decisions_at(unexp, mt, {"A", "B"})) >= 1     # surprise -> decision

    pred = W([{"name": "A", "pos": (0, 0), "goal": (6, 0), "expect": ["B"]},
              {"name": "B", "pos": (3, -2), "goal": (3, 3), "expect": ["A"]}])
    pred.run(8)
    mt2 = _meeting_tick(pred, "A", "B")
    assert _decisions_at(pred, mt2, {"A", "B"}) == []         # predicted -> no decision
    assert len(pred.conversation_between("A", "B")) >= 1      # ...yet they still chat


def test_conversation_unfolds_along_a_route():
    """The payoff: a conversation spans a shared route -- utterances spoken while
    the speaker is still WALKING (impossible under the coarse teleport tick)."""
    w = W([{"name": "A", "pos": (0, 0), "goal": (6, 0)},
           {"name": "B", "pos": (1, 0), "goal": (7, 0)}])   # B one step ahead, same road
    w.run(8)
    assert len(w.conversation_between("A", "B")) >= 2       # multiple turns
    assert len(w.utterances_while_moving()) >= 1            # spoken while walking


def test_decisions_are_sparse():
    """In a mostly-predicted town, decisions are far fewer than residents x ticks
    (the fast clock costs O(surprise))."""
    residents = [{"name": n, "pos": (i, 0), "goal": (i, 8), "expect": []}
                 for i, n in enumerate("ABCDE")]           # parallel lanes, no crossings
    w = W(residents)
    w.run(8)
    assert w.decision_count() < len(residents) * 8 * 0.25  # << residents x ticks
    assert w.max_hop == 1


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
