"""bigville R10c (274000) gate -- the social rungs FIRE + conservation still holds +
journals render real state + the export contract carries the active social state.

A POPULATE + ARM + EXPORT rung: the RULES already existed; these assert the trigger
entities were populated and the periodic events armed so the loaded social rules fire,
that Sigma(coin) stays invariant (no leak introduced), and that the journal/paper/board
export is a real graph read (never authored prose)."""
from __future__ import annotations

import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_integ3_world import BigvilleInteg3World, TICKS_PER_DAY  # noqa: E402
from worlds.bigville_integ3_state import export_townstate3, _render_journal  # noqa: E402

# one run reused across assertions (7 days -> a paper, a council, a drama beat, lessons).
_TICKS = 8 * TICKS_PER_DAY


@pytest.fixture(scope="module")
def town():
    w = BigvilleInteg3World(cast=16, seed=274000)
    w._c0 = w.system_coin()
    for _ in range(_TICKS):
        w.integ_step()
    return w


def test_builds_and_does_not_explode(town):
    assert town.exploded is None
    assert len(town.macro) == _TICKS


def test_conservation_still_invariant(town):
    """Activating the social rungs introduces NO coin leak (the school sub-ledger is
    closed; the journal records `coin_held` not a live balance)."""
    assert abs(town.system_coin() - town._c0) < 1e-6


def test_paper_prints_and_reaches(town):
    """THE PAPER fires: >=1 Story printed and >=1 printing informed a resident."""
    assert town.rung_fire.get("bigville_news_press", 0) >= 1
    assert town.rung_fire.get("bigville_news_reach", 0) >= 1
    assert town.papers and town.papers[0]["printed"] == 1


def test_coalition_and_informed_share(town):
    """The reach channel measures an informed-share and the coalition rule decides."""
    assert town.informed_share_series
    _t, informed, n, share, _f = town.informed_share_series[0]
    assert 0.0 <= share <= 1.0 and informed <= n


def test_council_convenes_and_posts(town):
    """THE TWO-TIER COUNCIL fires: convened + a notice recorded on the board."""
    assert town.rung_fire.get("bigville_council_gov", 0) >= 1
    assert town.council_log and town.council_log[0]["convened"] == 1


def test_journals_are_real_graph_reads(town):
    """Every living resident wrote a nightly JournalEntry, and it renders REAL state
    (the day + coin match the graph, not authored prose)."""
    assert town.rung_fire.get("bigville_journal_nightly", 0) >= 16
    got = 0
    for nm in town.people:
        if town.is_dead(nm):
            continue
        j = town.latest_journal(nm)
        assert j is not None, "living resident %s has no journal" % nm
        # the recorded coin equals the live mover coin (a real read, not invented).
        assert abs(float(j["coin_held"]) - town.coin_of(nm)) < 1.0
        line = _render_journal(j)
        assert line and line.startswith("Day ")
        got += 1
    assert got >= 10


def test_export_contract_carries_social_state(town):
    state = export_townstate3(town)
    for key in ("paper", "council_board", "collective_action", "rung_report"):
        assert key in state, "export missing %s" % key
    # every villager carries a journal field (may be null for the dead) that is a real
    # render, never authored prose.
    assert all("journal" in v for v in state["villagers"])
    living_with_journal = sum(1 for v in state["villagers"]
                              if v.get("alive") and v.get("journal"))
    assert living_with_journal >= 10


def test_regime_classifier_runs(town):
    from scripts.bigville_integ_measure import classify_regime
    verdict, ev = classify_regime(town.macro, exploded=town.exploded)
    assert verdict in ("PUNCTUATED_EQUILIBRIUM", "PUNCTUATED_WEAK", "DEAD_FIXPOINT",
                       "SMOOTH", "WHITE_NOISE", "CLEAN_PERIODIC", "FROZEN", "EXPLODED",
                       "UNRESOLVED")
    assert "activity_total" in ev or verdict in ("FROZEN", "EXPLODED")


def test_school_loud_drama_status(town):
    """Best-effort rungs report a HONEST fired/dormant status (never silently absent)."""
    rr = town.rung_report()
    for sid in ("bigville_school_learn", "bigville_loud_comm", "bigville_loud_class",
                "bigville_drama_social"):
        assert sid in rr
        assert rr[sid].startswith("fired") or rr[sid].startswith("dormant")
