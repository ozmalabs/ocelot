"""bigville block 297000 -- fold-in: the LIVE town's weekly headline is RENDERED
from the week's real event, not a Python f-string.

Gates mirror BIGVILLE_HEADLINE_FOLDIN_PREREG.md. The existing integ3/news gates
(kept green by the additive design) are asserted by their own suites; here we
assert the render, the real name, the free-vs-captured launder, and the source
audit.
"""
from __future__ import annotations

import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_integ3_world import (BigvilleInteg3World,       # noqa: E402
                                          TICKS_PER_DAY, PAPER_EVERY_DAYS)

_DEATH = dict(subject="Ada Lovelace", event_verb="has died", place="this week",
              patron="", damaging=0, has_patron=0)
_HOMELESS = dict(subject="Several families", event_verb="were left without a roof",
                 place="in Bigville", patron="the council", damaging=1, has_patron=1)


def _print_one(captured, fields):
    w = BigvilleInteg3World(cast=10, seed=274000)
    w.eng.set_attr(w._paper, "captured", float(captured))
    w._print_paper(truth_value=30.0, kind="weekly", story_fields=fields)
    return w.papers[-1]["headline"]


# ------------------------------------------------------ G-headline-rendered
def test_weekly_headline_is_rendered_prose_not_fstring():
    h = _print_one(0, _DEATH)
    assert h.endswith("."), f"headline should be a rendered sentence: {h!r}"
    assert "Ada Lovelace" in h and "has died" in h, h
    assert not re.match(r"week \d+:", h), "still the old f-string template"


# ------------------------------------------------------ G-real-name (live run)
def test_live_run_headline_names_a_real_dead_resident():
    """Over a live run, a death-lead headline names a resident actually in the
    death_log (writes about a real held event, by name)."""
    w = BigvilleInteg3World(cast=12, seed=274000)
    w.run_town(T=TICKS_PER_DAY * PAPER_EVERY_DAYS * 6 + 5)
    death_names = {str(d.get("name", "")) for d in w.death_log}
    death_leads = [p for p in w.papers if "has died" in p.get("headline", "")]
    assert death_leads, "no death-lead headline was rendered across 6 weeks"
    for p in death_leads:
        named = any(nm and nm in p["headline"] for nm in death_names)
        assert named, ("a death headline named no real death_log resident: %r"
                       % p["headline"])


# ------------------------------------------------------ G-free-vs-captured (live)
def test_free_vs_captured_launder_in_the_live_town():
    free = _print_one(0, _HOMELESS)
    capt = _print_one(1, _HOMELESS)
    assert free != capt, "free and captured printed identical prose"
    assert "the council" in free, f"free paper must name the patron: {free!r}"
    assert "the council" not in capt, f"captured paper must launder the patron: {capt!r}"
    # the event survives in both (same held story, different framing).
    for tok in ("Several families", "were left without a roof"):
        assert tok in free and tok in capt


# ------------------------------------------------------ G-no-python-prose
def test_no_python_builds_the_weekly_headline():
    """Source audit: the integ3 weekly path builds no sentence -- the old
    'week %d: %d passings %d without a roof' f-string is gone, and the headline is
    the graph-rendered `text`."""
    src = open(os.path.join(_ROOT, "worlds", "bigville_integ3_world.py")).read()
    assert "passings" not in src, "the old f-string headline template is still present"
    assert not re.search(r'"week %d[^"]*"\s*%', src), "weekly headline still built by %-format"
    import json
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_headline.json")))
    assert "StringConcat" in json.dumps(seed)
    names = {r["name"] for r in seed["rules"]}
    assert {"hl_render_full", "hl_render_plain", "hl_render_laundered"} <= names, names
