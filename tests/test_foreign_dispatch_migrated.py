"""bigville R28 (block 316000): Word from Giantville in the paper. A traveller's
foreign news becomes a held belief (bw_news_secondhand) and the paper prints a
foreign_dispatch Story rendered by StringConcat, hedged by the belief's
credibility. Gates mirror BIGVILLE_FOREIGN_DISPATCH_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_foreign_dispatch_world import BigvilleForeignDispatchWorld   # noqa: E402


# ------------------------------------------------------ G-paper-carries-giantville-news (headline)
def test_the_paper_carries_giantville_news():
    w = BigvilleForeignDispatchWorld()
    w.bring_news("the harvest beyond the hills has failed", credibility=0.9)
    w.run()
    d = w.dispatches()
    assert len(d) == 1, f"the paper should print one Giantville dispatch: {d}"
    assert "Giantville" in d[0] and "the harvest beyond the hills has failed" in d[0]


# ------------------------------------------------------ G-hedged-by-credibility (headline)
def test_provenance_becomes_word_choice():
    """A credible report is printed confirmed; a shaky one is hedged as unconfirmed
    hearsay -- the veracity axis showing up as words."""
    hi = BigvilleForeignDispatchWorld()
    hi.bring_news("a new bridge spans the great river", credibility=0.9)
    hi.run()
    lo = BigvilleForeignDispatchWorld()
    lo.bring_news("a dragon was seen circling the crag", credibility=0.3)
    lo.run()
    assert "confirmed" in hi.dispatches()[0].lower(), hi.dispatches()
    assert "unconfirmed" in lo.dispatches()[0].lower(), lo.dispatches()
    assert "travellers bring word" in lo.dispatches()[0].lower()


# ------------------------------------------------------ G-no-traveller-no-news (frontier / falsifier)
def test_no_traveller_no_giantville_news():
    """Unknown = absence: with no traveller the publisher forms no belief and the
    paper carries nothing about Giantville."""
    w = BigvilleForeignDispatchWorld()
    w.run()
    assert w.belief_confidence() is None, "no traveller -> no held belief"
    assert w.dispatches() == [], "no traveller -> no Giantville dispatch"


# ------------------------------------------------------ G-written-once
def test_dispatch_written_once():
    w = BigvilleForeignDispatchWorld()
    w.bring_news("the toll road is closed for repairs", credibility=0.9)
    w.run()
    n = len(w.dispatches())
    for _ in range(3):
        w.run()
    assert len(w.dispatches()) == n == 1, "a dispatch must be written exactly once"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_writes_the_dispatch():
    src = open(os.path.join(_ROOT, "worlds", "bigville_foreign_dispatch_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run the engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_foreign_dispatch.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"fd_write_confirmed", "fd_write_hearsay"} <= names, names
    # the prose is StringConcat in the seed, not a Python f-string.
    assert "StringConcat" in json.dumps(seed), "the dispatch must be rendered graph-native"
