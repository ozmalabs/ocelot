"""bigville R49 (block 359000): a NOTICEBOARD in the town square. Agents write/give/relay notes
(held items); this adds POSTING (pin a held note on the board -- must be present) and READING
(anyone at the square reads it). A local, public medium. Gates mirror the seed description.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_noticeboard_world import BigvilleNoticeboardWorld as NB   # noqa: E402


# ------------------------------------------------------ G-post-requires-presence (headline)
def test_posting_requires_being_at_the_square_and_holding_the_note():
    w = NB(); w.add_agent("Mary")
    w.write_note("Mary", "service on Sunday")
    w.post("Mary", "service on Sunday")                 # Mary is not at the square
    assert w.board_contents() == [], "you cannot post from afar -- you must be at the board"
    w.go_to_square("Mary"); w.post("Mary", "service on Sunday")
    assert w.board_contents() == ["service on Sunday"], "present + holding -> the note is pinned up"
    assert w.holder_of_note("service on Sunday") is None, "it leaves the poster's hand -- now public"


# ------------------------------------------------------ G-read-is-local (headline)
def test_only_those_who_visit_the_square_read_the_board():
    w = NB(); w.add_agent("Mary"); w.add_agent("Visitor"); w.add_agent("Homebody")
    w.write_note("Mary", "market day tomorrow")
    w.go_to_square("Mary"); w.post("Mary", "market day tomorrow")
    w.go_to_square("Visitor")
    assert w.has_read("Visitor", "market day tomorrow"), "someone at the square reads the board"
    assert not w.has_read("Homebody", "market day tomorrow"), \
        "someone who never visits never sees it -- the board is a LOCAL public medium"


# ------------------------------------------------------ G-relay-then-post (headline)
def test_a_relayed_note_can_be_posted_and_reaches_the_public():
    w = NB()
    for n in ("Author", "Courier", "Poster", "Townsfolk"):
        w.add_agent(n)
    w.write_note("Author", "help wanted: cook")
    w.give_note("Author", "Courier", "help wanted: cook")   # hand it on...
    w.give_note("Courier", "Poster", "help wanted: cook")   # ...and on (a relay of hand-offs)
    assert w.holder_of_note("help wanted: cook") == "Poster", "the note travelled by relay"
    w.go_to_square("Poster"); w.post("Poster", "help wanted: cook")
    assert w.board_contents() == ["help wanted: cook"], "the courier posts what he was given"
    w.go_to_square("Townsfolk")
    assert w.has_read("Townsfolk", "help wanted: cook"), "a relayed note reaches the public board"


# ------------------------------------------------------ G-multiple-notices
def test_the_board_holds_multiple_notices():
    w = NB(); w.add_agent("A"); w.add_agent("B"); w.add_agent("Reader")
    w.write_note("A", "lost dog"); w.write_note("B", "room to let")
    w.go_to_square("A"); w.post("A", "lost dog")
    w.go_to_square("B"); w.post("B", "room to let")
    assert w.board_contents() == ["lost dog", "room to let"]
    w.go_to_square("Reader")
    assert set(w.reads_of("Reader")) == {"lost dog", "room to let"}, "a visitor reads every posted notice"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_posting():
    src = open(os.path.join(_ROOT, "worlds", "bigville_noticeboard_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_noticeboard.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"nb_post", "nb_read"} <= names, names
    post = [r for r in seed["rules"] if r["name"] == "nb_post"][0]
    assert ["agent", "at", "square"] in post["match"] and ["agent", "holds", "note"] in post["match"], \
        "posting requires presence at the square and holding the note (physical)"
    read = [r for r in seed["rules"] if r["name"] == "nb_read"][0]
    assert ["reader", "at", "square"] in read["match"], "reading the board requires being present"
