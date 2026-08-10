"""jabberwock_reads_metonymy — the reader UNDERSTANDS regular METONYMY, the SECOND
coherence re-reading source (task-121, on top of task-120's compound composition).

THE MOVE. A verb imposes a TYPE on its argument slots (a selectional expectation).
'read' expects a TEXT in its theme; 'won' expects a winnable/opponent; 'announce'
expects an animate/institutional AGENT. When the LITERAL binding is the WRONG type —
a PERSON as the theme of 'read', a PLACE as the theme of 'won', a PLACE as the agent
of 'announce' — that is a selectional VIOLATION. The named compound (task-120) is the
first re-reading source; when it does not fit, PRODUCTIVE, TYPE-KEYED metonymy is the
second: shift X to a related Y of the type the slot wants, and STATE the shift.

  author->works   'read Shakespeare' -> read Shakespeare's WORKS
  place->team     'won France'       -> won the French TEAM
  place->govt     'Washington announced' -> the GOVERNMENT of Washington announced

It is GATED by the selectional coherence: 'read Shakespeare' shifts (read expects a
text, a person violates); 'met Shakespeare' does NOT ('meet' expects a person, so a
person coheres — no over-fire). GENERIC: any author (Dickens/Mozart) or place shifts
via its WordNet TYPE, no name table. COMPOSES with task-120: a violation with NEITHER
a compound NOR a metonymy is HELD-OPEN (anti-hallucination). The patterns are
graph-resident TYPE-KEYED relations (seeds/metonymy_patterns.json); the shift is a
graph op (X -> metonym(X), a `stands_for` edge); no author/place NAME literal in the
decision path; donkey=0 (no LLM), no `import re`.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_metonymy.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                       # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import cognitive_disambiguation as cd              # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    dl.warm_wordnet("en")
    s, node = boot_core()
    ag = _Agent(s, node)
    cd.ensure_metonymy_codebook(ag)
    return ag


def _person(s, name):
    return s.add_node("SmEntity", {"name": name, "coref_category": "person",
                                   "coref_animate": 1.0, "coref_mentions": 2.0})


def _place(s, name):
    return s.add_node("SmEntity", {"name": name, "coref_category": "location",
                                   "coref_animate": 0.0, "coref_mentions": 2.0})


def _event(s, verb, surface, role, arg):
    ev = s.add_node("SmEvent", {"verb": verb, "surface": surface})
    s._inner.add_edge_unchecked(ev, role, arg)
    return ev


# --------------------------------------------------------------------------- #
#  (a) author->works : 'read Shakespeare' -> his WORKS, STATED.
# --------------------------------------------------------------------------- #
def run_author_works():
    ag = _fresh()
    s = ag.s
    ev = _event(s, "read", "read", "theme", _person(s, "shakespeare"))
    before = cd.event_theme(ag, ev)
    rep = cd.metonymic_redecode(ag, "")
    after = cd.event_theme(ag, ev)
    shift = [x for x in rep["shifts"] if x["rebound_from"] == "shakespeare"][0]
    return {"before": before, "after": after, "shift": shift,
            "stated": cd.metonymic_shift(ag, "shakespeare_works"),
            "stands_for": cd.stands_for(ag, "shakespeare")}


# --------------------------------------------------------------------------- #
#  (b) place->team + place->government.
# --------------------------------------------------------------------------- #
def run_place_shifts():
    ag = _fresh()
    s = ag.s
    ev_win = _event(s, "win", "won", "theme", _place(s, "france"))
    ev_ann = _event(s, "announce", "announced", "agent", _place(s, "washington"))
    rep = cd.metonymic_redecode(ag, "")
    team = [x for x in rep["shifts"] if x["rebound_from"] == "france"][0]
    govt = [x for x in rep["shifts"] if x["rebound_from"] == "washington"][0]
    return {"won_france": cd.event_theme(ag, ev_win), "team": team, "govt": govt,
            "team_stated": cd.metonymic_shift(ag, "france_team"),
            "govt_stated": cd.metonymic_shift(ag, "washington_government")}


# --------------------------------------------------------------------------- #
#  (c) GATED — 'met Shakespeare' does NOT shift (person coheres with 'meet').
# --------------------------------------------------------------------------- #
def run_gated_no_over_fire():
    ag = _fresh()
    s = ag.s
    ev = _event(s, "meet", "met", "theme", _person(s, "shakespeare"))
    before = cd.event_theme(ag, ev)
    rep = cd.metonymic_redecode(ag, "")
    after = cd.event_theme(ag, ev)
    coh = [c for c in rep["coherent"] if c["entity"] == "shakespeare"]
    return {"before": before, "after": after, "shifts": rep["shifts"],
            "coherent": coh}


# --------------------------------------------------------------------------- #
#  (d) GENERIC — any author (Dickens/Mozart) via the creator TYPE, no name table.
# --------------------------------------------------------------------------- #
def run_generic():
    ag = _fresh()
    s = ag.s
    for nm in ("dickens", "mozart"):
        _event(s, "read", "read", "theme", _person(s, nm))
    rep = cd.metonymic_redecode(ag, "")
    return {"dickens": cd.metonymic_shift(ag, "dickens_works"),
            "mozart": cd.metonymic_shift(ag, "mozart_works"),
            "patterns": {x["rebound_from"]: x["pattern"] for x in rep["shifts"]}}


# --------------------------------------------------------------------------- #
#  (e) COMPOSES with task-120 — three outcomes of the ONE re-decode:
#      compound resolves (task-120) | metonymy resolves (task-121) | neither -> held.
# --------------------------------------------------------------------------- #
def run_composition():
    ag = _fresh()
    cd.ensure_head_codebook(ag)
    s = ag.s
    # 1) COMPOUND source (task-120): person theme of 'won', honoree of a prize.
    nobel = _person(s, "nobel")
    ev_comp = _event(s, "win", "won", "theme", nobel)
    cd.compose_named_compounds(ag, "She won the Nobel Prize.")
    cd.coherence_check(ag, "She won the Nobel Prize.")        # compound re-binds
    # 2) METONYMY source (task-121): person theme of 'read' -> works.
    ev_met = _event(s, "read", "read", "theme", _person(s, "orwell"))
    # 3) NEITHER: person theme of 'won', no compound, no place->team pattern -> held.
    ev_held = _event(s, "win", "won", "theme", _person(s, "mary"))
    rep = cd.metonymic_redecode(ag, "")
    return {
        "compound_theme": cd.event_theme(ag, ev_comp),        # nobel_prize (task-120)
        "metonymy_theme": cd.event_theme(ag, ev_met),         # orwell_works (task-121)
        "held_theme": cd.event_theme(ag, ev_held),            # mary (held open)
        "held": [h for h in rep["held_open"] if h["entity"] == "mary"],
        "metonymy_shift": [x for x in rep["shifts"] if x["rebound_from"] == "orwell"]}


def _print(a, b, c, d, e):
    W = "=" * 74
    print(W)
    print("THE READER UNDERSTANDS METONYMY — the 2nd coherence re-reading source")
    print(W)
    print("(a)  author->works : 'read Shakespeare'  (theme is a PERSON — a text was")
    print("     expected; the selectional violation drives the shift)")
    print("     BEFORE theme = %s" % a["before"])
    print("     AFTER  theme = %s" % a["after"])
    print("     STATED SHIFT : %s" % a["shift"]["reading"])
    print("                  : %s" % a["stated"])
    print("     stands_for   : shakespeare -> %s" % a["stands_for"])
    print()
    print("(b)  place->team + place->government")
    print("     'won France'          theme -> %s" % b["won_france"])
    print("       %s" % b["team"]["reading"])
    print("       %s" % b["team_stated"])
    print("     'Washington announced' agent -> govt")
    print("       %s" % b["govt"]["reading"])
    print("       %s" % b["govt_stated"])
    print()
    print("(c)  GATED (no over-fire) : 'met Shakespeare' — 'meet' EXPECTS a person")
    print("     BEFORE theme = %s" % c["before"])
    print("     AFTER  theme = %s   (UNTOUCHED — a person coheres, NO shift)" % c["after"])
    print("     shifts on this event: %d (expect 0)" % len(c["shifts"]))
    print("     coherence noted: %s" % (c["coherent"][0]["why"] if c["coherent"] else None))
    print()
    print("(d)  GENERIC — any author via the creator TYPE (no name table)")
    print("     %s   [%s]" % (d["dickens"], d["patterns"].get("dickens")))
    print("     %s   [%s]" % (d["mozart"], d["patterns"].get("mozart")))
    print()
    print("(e)  COMPOSES with task-120 — one re-decode, three sources in order")
    print("     COMPOUND (task-120): won nobel -> theme %s" % e["compound_theme"])
    print("     METONYMY (task-121): read orwell -> theme %s" % e["metonymy_theme"])
    print("     NEITHER            : won mary  -> theme %s  (HELD-OPEN, not force-bound)"
          % e["held_theme"])
    print("       held: %s" % (e["held"][0]["held_reason"] if e["held"] else None))
    print(W)


if __name__ == "__main__":
    a = run_author_works()
    b = run_place_shifts()
    c = run_gated_no_over_fire()
    d = run_generic()
    e = run_composition()
    _print(a, b, c, d, e)
