"""bigville block 296000 -- newspaper-writer Rung D: the publisher WRITES prose
from held beliefs; bias/capture become WORD choices.

The flagship: over the SAME held fact, a free paper and a captured paper produce
DIFFERENT prose (free names the patron; captured launders it out). The prose is
rendered by the engine's StringConcat, not a Python f-string. Gates mirror
BIGVILLE_WRITE_PREREG.md.
"""
from __future__ import annotations

import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_write_world import BigvilleWriteWorld         # noqa: E402

PUB, FAR = (27, 9), (0, 2)
SUBJ, EVENT, PLACE, PATRON = ("The Hendersons", "were evicted",
                              "on Elm Street", "John Scrooge")


def _paper(captured, *, damaging=1):
    w = BigvilleWriteWorld(captured=captured)
    w.add_publisher("iris", PUB)
    w.add_structured_reporter("alice", FAR, subject=SUBJ, event=EVENT, place=PLACE,
                              patron=PATRON, damaging=damaging, salience=3.0)
    w.run(T=90)
    return w


# --------------------------------------------------------- G-names-held-actors
def test_prose_names_the_held_actors():
    w = _paper(captured=0)
    h = w.headline()
    assert h is not None, "no story was printed"
    assert SUBJ in h and EVENT in h and PLACE in h, h
    w.close()


# --------------------------------------------------------- G-free-vs-captured
def test_free_and_captured_produce_different_prose():
    """FLAGSHIP: same held fact, different prose. Free names the patron; captured
    omits it; subject/event/place identical."""
    free = _paper(captured=0).headline()
    capt = _paper(captured=1).headline()
    assert free != capt, "free and captured printed identical prose"
    assert PATRON in free, f"free paper must name the patron: {free!r}"
    assert PATRON not in capt, f"captured paper must launder the patron: {capt!r}"
    # the underlying held fact is the same: subject/event/place survive in both.
    for tok in (SUBJ, EVENT, PLACE):
        assert tok in free and tok in capt, (tok, free, capt)


# --------------------------------------------------------- G-capture-is-targeted
def test_capture_is_targeted():
    """A captured paper still prints a NON-damaging story in full (patron clause
    present) -- capture launders only the damaging story."""
    capt_ordinary = _paper(captured=1, damaging=0).headline()
    assert PATRON in capt_ordinary, (
        f"an ordinary story must print in full even when captured: {capt_ordinary!r}")


# --------------------------------------------------------- G-only-what-is-held
def test_paper_prints_only_held_beliefs():
    """The paper prints ONLY about facts the publisher KNOWS. A rumour never
    delivered and never witnessed is never printed -- no confabulation to the page."""
    w = BigvilleWriteWorld(captured=0)
    w.add_publisher("iris", PUB)
    w.add_structured_reporter("alice", FAR, subject=SUBJ, event=EVENT, place=PLACE,
                              patron=PATRON, damaging=1, salience=3.0)
    w.add_rumor("aliens landed", salience=9.0)      # exists, never delivered/seen
    w.run(T=90)
    printed = " || ".join(t for t, _, _ in w.stories())
    assert SUBJ in printed, "the held fact should be printed"
    assert "aliens" not in printed, "a rumour never held was printed (confabulation)"
    w.close()


# --------------------------------------------------------- G-rendered-not-fstring
def test_prose_is_engine_rendered_not_a_python_fstring():
    """Source audit: the adapter builds NO headline string (no %/format/join/
    f-string over content); the story text is a StringConcat term in the seed."""
    src = open(os.path.join(_ROOT, "worlds", "bigville_write_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    # no prose assembled in Python: no %-format, .format, or join building sentences.
    assert not re.search(r'"[^"]*%s[^"]*"\s*%', src), "adapter builds a headline via %-format"
    assert ".format(" not in src, "adapter builds a headline via .format"
    import json
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_write.json")))
    blob = json.dumps(seed)
    assert "StringConcat" in blob, "the render must be a StringConcat term"
    names = {r["name"] for r in seed["rules"]}
    assert {"write_free", "write_captured_ordinary", "write_laundered"} <= names, names
