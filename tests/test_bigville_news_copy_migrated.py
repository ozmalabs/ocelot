"""bigville: THE PRINTED NEWSPAPER CARRIES ITS STORY (the news seam).

The press-printed newspaper (414000) is a physical Good. Holding a copy (a Good `of_paper` the paper)
confers readership -- np_copy_confers_reading adds the `reads` edge the existing news/reach layer
(np_reader_learns) already acts on. So a BOUGHT paper, not just a subscription, informs the reader --
and, because np_reader_learns requires literacy, an illiterate holder learns nothing. No decision in
Python: the reader-learning is a seed rule; the adapter only gives a copy and reads the outcome.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_news_world import BigvilleNewsWorld                    # noqa: E402


def _town_with_story():
    w = BigvilleNewsWorld()
    w.add_town(); w.add_event(truth_value=5); w.add_reporter("Nib", witnessed=1)
    w.add_paper("Herald"); w.add_story(reporter_bias=0)
    return w


# ------------------------------------------------------ G-a-bought-paper-informs (headline)
def test_holding_a_bought_newspaper_informs_a_non_subscriber():
    w = _town_with_story()
    w.add_resident("Buyer", witnessed=0, reads=0, literate=1)   # NOT subscribed
    w.give_newspaper("Buyer")                                   # but holds a bought copy
    w.add_resident("Nobody", witnessed=0, reads=0, literate=1)  # no paper at all
    w.publish()
    assert w.knows_event_flag_of("Buyer") == 1, "holding the printed paper carries the story to the reader"
    assert w.knows_event_flag_of("Nobody") == 0, "no paper, no subscription -> does not know the news"
    assert w.knows_event_of("Buyer") == w.content(), "and what he learns IS the printed story's content"


# ------------------------------------------------------ G-literacy-gates-the-paper (headline)
def test_an_illiterate_holder_learns_nothing_from_the_paper():
    w = _town_with_story()
    w.add_resident("Literate", witnessed=0, reads=0, literate=1); w.give_newspaper("Literate")
    w.add_resident("Illiterate", witnessed=0, reads=0, literate=0); w.give_newspaper("Illiterate")
    w.publish()
    assert w.knows_event_flag_of("Literate") == 1, "a literate holder reads it and learns"
    assert w.knows_event_flag_of("Illiterate") == 0, "an illiterate holder holds the paper but cannot read it"


# ------------------------------------------------------ G-subscription-still-works (no regression)
def test_a_subscriber_still_learns_without_a_physical_copy():
    w = _town_with_story()
    w.add_resident("Subscriber", witnessed=0, reads=1, literate=1)   # the old path: subscription
    w.publish()
    assert w.knows_event_flag_of("Subscriber") == 1, "subscription still informs -- the copy path is additive"


# ------------------------------------------------------ G-the-seam (source audit)
def test_possession_confers_reading_via_a_seed_rule():
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_news_copy.json")))
    r = next(x for x in seed["rules"] if x["name"] == "np_copy_confers_reading")
    assert ["res", "has_good", "copy"] in r["match"] and ["copy", "of_paper", "paper"] in r["match"], \
        "the rule keys on HOLDING a copy of the paper"
    assert r["effects"] == [["add_edge", "res", "reads", "paper"]], "possession confers the reads edge; the rest is the existing layer"
