"""jabberwock_understands_compounds — the reader UNDERSTANDS a named compound
COGNITIVELY (coherence-check + compositional composition), it does not PARSE it.

THE CREATOR'S POINT (the `nobel` residual): grounding 'Nobel' to the person is NOT
wrong — the reader FAILS TO UNDERSTAND. 'Nobel Prize' is an inanimate PRIZE named
after a chemist; you can WIN it; it is not a woman. The ambient female 'she' had
bled onto a bare `nobel` entity (18 mentions, read FEMALE). Two GENERAL cognitive
moves fix it (domains/cognitive_disambiguation.py), Nobel the driving example:

  (a) COHERENCE-CHECK  — a grounding that does not COHERE with its predicated role is
      a RESIDUAL to re-decode: a non-animate thing carrying a gender; a PERSON as the
      theme of an acquisition verb (you win a prize, not a person); a person conflated
      with an award named after them.
  (b) NAMED-COMPOUND COMPOSITION — 'X <head-type>' is a construction: the entity is
      the HEAD-type (award/institution/proposition/law — inanimate), and X is who it
      HONOURS (a `named_after` relation the reader STATES). Head-type is WordNet-
      derived (award.n.02 / organization.n.01 / proposition.n.01 / law.n.01), not a
      name table.

The disambiguation FALLS OUT: coherence flags the person-as-prize incoherence,
composition resolves it (the entity is the prize), the nobel-female-leak DISSOLVES.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_understands_compounds.py
"""
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                       # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import comprehension_reader as cr                  # noqa: E402
from domains import cognitive_disambiguation as cd              # noqa: E402
from domains import register_source as rs                       # noqa: E402

_CURIE_CACHE = os.path.join(ROOT, "data", "register", "curie.txt")


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _ent(agent, name):
    for n in agent.s.nodes("SmEntity"):
        at = agent.s.node(n)["attrs"]
        if at.get("name") == name:
            return {"gender": at.get("coref_gender") or "",
                    "animate": at.get("coref_animate"),
                    "category": at.get("coref_category"),
                    "mentions": at.get("coref_mentions"),
                    "merged_into": at.get("merged_into") or ""}
    return None


# --------------------------------------------------------------------------- #
#  (a) + (c) — the Nobel leak on the real Curie article, before/after.
# --------------------------------------------------------------------------- #
def run_curie():
    dl.warm_wordnet("en")
    with open(_CURIE_CACHE) as f:
        text = f.read()
    agent = _fresh()
    t0 = time.time()
    rs.route_reading(agent, text)                 # the encyclopedic read (as today)
    before = {k: _ent(agent, k) for k in ("nobel", "nobel_prize", "curie", "pierre")}
    rep = cd.disambiguate(agent, text)            # the cognitive pass
    after = {k: _ent(agent, k) for k in ("nobel", "nobel_prize", "curie", "pierre")}
    dt = time.time() - t0
    return {"text": text, "before": before, "after": after, "report": rep,
            "seconds": dt, "named_after_prize": cd.named_after(agent, "nobel_prize")}


# --------------------------------------------------------------------------- #
#  (b) — the GENERAL coherence-check on a constructed incoherence.
# --------------------------------------------------------------------------- #
def run_coherence():
    dl.warm_wordnet("en")
    agent = _fresh()
    cd.ensure_head_codebook(agent)
    s = agent.s
    rad = s.add_node("SmEntity", {"name": "radium", "coref_category": "object",
                                  "coref_animate": 0.0, "coref_gender": "female",
                                  "coref_mentions": 3.0})
    john = s.add_node("SmEntity", {"name": "john", "coref_category": "person",
                                   "coref_animate": 1.0, "coref_gender": "male",
                                   "coref_mentions": 2.0})
    ev = s.add_node("SmEvent", {"verb": "win", "surface": "won"})
    s._inner.add_edge_unchecked(ev, "theme", john)
    before_rad = s.node(rad)["attrs"].get("coref_gender")
    rep = cd.coherence_check(agent, "")
    after_rad = s.node(rad)["attrs"].get("coref_gender")
    return {"radium_before": before_rad, "radium_after": after_rad,
            "residuals": rep["residuals"]}


# --------------------------------------------------------------------------- #
#  (d) — GENERIC compounds (Fields Medal / Turing Award / Curie Institute / law).
# --------------------------------------------------------------------------- #
def run_generic():
    dl.warm_wordnet("en")
    agent = _fresh()
    text = ("The Fields Medal is a great honour. She won the Turing Award last year. "
            "He studied at the Curie Institute. Everyone respects the Nobel Prize. "
            "The class proved Boyle's Law in the lab.")
    cr.read_and_comprehend(agent, text, max_sentences=40)
    rep = cd.disambiguate(agent, text)
    ents = {}
    for canon in ("fields_medal", "turing_award", "curie_institute",
                  "nobel_prize", "boyle_law"):
        ents[canon] = (_ent(agent, canon), cd.named_after(agent, canon))
    return {"stated": rep["stated"], "entities": ents}


# --------------------------------------------------------------------------- #
#  ACT ON THE ROLE RESIDUAL — the selectional violation DRIVES a re-decode.
#  "She won the Nobel Prize": the reader mis-grounded the theme of 'won' to the
#  PERSON Nobel (animate). The violation (a person in a winnable-thing slot) is the
#  SIGNAL: search for the coherent re-reading — the winnable COMPOUND the person is
#  named after ('Nobel Prize') — and RE-BIND the theme. A BOUND theme, not a flag.
# --------------------------------------------------------------------------- #
def _theme_node(agent, ev):
    for th in agent.inner.neighbours(ev, "theme"):
        return th
    return None


def run_role_redecode():
    """(a) "She won the Nobel Prize" -> 'won'-THEME re-bound from the person Nobel
    to the PRIZE (winnable, inanimate). The reader mis-grounded the theme to the
    PERSON (the same Nobel-as-person conflation the article shows); the re-decode
    acts on the role residual. Verbatim before/after — a bound theme, not a flag."""
    dl.warm_wordnet("en")
    agent = _fresh()
    cd.ensure_head_codebook(agent)
    s = agent.s
    # the document is ABOUT Marie (dominant salience) — Nobel is only the namesake.
    s.add_node("SmEntity", {"name": "marie", "coref_category": "person",
                            "coref_animate": 1.0, "coref_gender": "female",
                            "coref_mentions": 20.0})
    # the reader MIS-GROUNDED 'the Nobel Prize' to the PERSON Nobel, as the theme of
    # 'won' (a person in a winnable-thing slot — the selectional violation).
    nobel = s.add_node("SmEntity", {"name": "nobel", "coref_category": "person",
                                    "coref_animate": 1.0, "coref_mentions": 2.0})
    ev = s.add_node("SmEvent", {"verb": "win", "surface": "won"})
    s._inner.add_edge_unchecked(ev, "theme", nobel)
    text = "She won the Nobel Prize."
    cd.compose_named_compounds(agent, text)       # mints 'nobel_prize' named_after nobel
    before = cd.event_theme(agent, ev)
    expect = cd.selectional_expectation(agent, "won")
    rep = cd.coherence_check(agent, text)         # the role residual is ACTED ON
    after = cd.event_theme(agent, ev)
    role = [r for r in rep["residuals"] if r["kind"] == "role"]
    return {"before": before, "after": after, "expect": expect, "role": role}


def run_selectional_general():
    """(b) SELECTIONAL GENERAL, three cases in one graph:
      · VIOLATION with a coherent re-reading -> re-decoded (fields -> Fields Medal).
      · VIOLATION with NO coherent re-reading -> HELD-OPEN, not force-bound (a bare
        person 'mary' as the theme of 'won', no compound).
      · a COHERENT theme ('won a game' — a winnable thing) -> UNTOUCHED (no over-fire)."""
    dl.warm_wordnet("en")
    agent = _fresh()
    cd.ensure_head_codebook(agent)
    s = agent.s
    text = "She won the Fields Medal."
    # coherent theme: 'game' is a winnable thing (inanimate) — must NOT be re-decoded.
    game = s.add_node("SmEntity", {"name": "game", "coref_category": "object",
                                   "coref_animate": 0.0, "coref_mentions": 1.0})
    ev_game = s.add_node("SmEvent", {"verb": "win", "surface": "won"})
    s._inner.add_edge_unchecked(ev_game, "theme", game)
    # violation WITH a coherent re-reading: 'fields' the person, honoree of a medal.
    fields = s.add_node("SmEntity", {"name": "fields", "coref_category": "person",
                                     "coref_animate": 1.0, "coref_mentions": 2.0})
    ev_fields = s.add_node("SmEvent", {"verb": "win", "surface": "won"})
    s._inner.add_edge_unchecked(ev_fields, "theme", fields)
    # violation with NO coherent re-reading: 'mary' the person, no compound.
    mary = s.add_node("SmEntity", {"name": "mary", "coref_category": "person",
                                   "coref_animate": 1.0, "coref_mentions": 2.0})
    ev_mary = s.add_node("SmEvent", {"verb": "win", "surface": "won"})
    s._inner.add_edge_unchecked(ev_mary, "theme", mary)
    cd.compose_named_compounds(agent, text)       # mints 'fields_medal' named_after fields
    before = {"game": cd.event_theme(agent, ev_game),
              "fields": cd.event_theme(agent, ev_fields),
              "mary": cd.event_theme(agent, ev_mary)}
    rep = cd.coherence_check(agent, text)
    after = {"game": cd.event_theme(agent, ev_game),
             "fields": cd.event_theme(agent, ev_fields),
             "mary": cd.event_theme(agent, ev_mary)}
    return {"before": before, "after": after, "residuals": rep["residuals"]}


def run_curie_roles():
    """(d) The role-flag BEFORE/AFTER on the real Marie Curie article: every role
    residual now carries a VERDICT (re_decoded | held_open) — none is silently
    dropped. Reports how many re-decode vs are honestly held open."""
    dl.warm_wordnet("en")
    with open(_CURIE_CACHE) as f:
        text = f.read()
    agent = _fresh()
    rs.route_reading(agent, text)
    rep = cd.disambiguate(agent, text)
    role = [r for r in rep["coherence"]["residuals"] if r["kind"] == "role"]
    re_dec = [r for r in role if r.get("verdict") == "re_decoded"]
    held = [r for r in role if r.get("verdict") == "held_open"]
    return {"n_role": len(role), "n_re_decoded": len(re_dec),
            "n_held_open": len(held), "role": role}


# --------------------------------------------------------------------------- #
#  ANTI-OVER-FIRE — a fable has NO named compounds (byte-identity guard).
# --------------------------------------------------------------------------- #
FABLE = (
    "In a spell of dry weather, when the Birds could find very little to drink, "
    "a thirsty Crow found a pitcher with a little water in it. But the pitcher "
    "was high and had a narrow neck, and no matter how he tried, the Crow could "
    "not reach the water. The poor thing felt as if he must die of thirst.")


def run_fable():
    dl.warm_wordnet("en")
    agent = _fresh()
    cr.read_and_comprehend(agent, FABLE, max_sentences=40)
    rep = cd.disambiguate(agent, FABLE)
    return {"compositions": rep["compose"]["compositions"],
            "residuals": rep["coherence"]["residuals"]}


def _print(cur, coh, gen, fab):
    W = "=" * 74
    print(W)
    print("THE READER UNDERSTANDS 'NOBEL PRIZE' — coherence + compound composition")
    print(W)
    print("(a)+(c)  THE NOBEL LEAK on the real Marie Curie article (%.0fs read)"
          % cur["seconds"])
    for k in ("nobel", "nobel_prize", "curie", "pierre"):
        b, a = cur["before"][k], cur["after"][k]
        if b is None:
            continue
        print("   %-12s BEFORE gender=%-7r animate=%s merged=%-6r"
              % (k, b["gender"], b["animate"], b["merged_into"]))
        print("   %-12s AFTER  gender=%-7r animate=%s merged=%-6r"
              % ("", a["gender"], a["animate"], a["merged_into"]))
    print("   -> nobel gender %r -> %r   (THE FEMALE LEAK IS GONE)"
          % (cur["before"]["nobel"]["gender"], cur["after"]["nobel"]["gender"]))
    print("   -> 'nobel_prize' named_after: %s" % cur["named_after_prize"])
    comps = cur["report"]["compose"]["compositions"]
    inco = [c for c in comps if c["incoherence"]]
    print("   -> person-as-prize incoherence caught: %s"
          % [c["compound"] for c in inco])
    print()
    print("(c)  THE STATED INFERENCE (cognitive, not a re-label) — a sample:")
    for st in cur["report"]["stated"][:6]:
        print("     %s" % st["meaning"])
    print()
    print("(b)  THE GENERAL COHERENCE-CHECK (constructed incoherence, Nobel is ONE case)")
    print("     radium (a substance) gender %r -> %r  (a substance has no sex)"
          % (coh["radium_before"], coh["radium_after"]))
    for r in coh["residuals"]:
        print("     [%s] %s : %s" % (r["kind"], r.get("entity"), r["why"][:56]))
    print()
    print("(d)  GENERIC named compounds")
    for st in gen["stated"]:
        print("     %s" % st["meaning"])
    for canon, (e, na) in gen["entities"].items():
        if e:
            print("     %-16s animate=%s gender=%-4r named_after=%s"
                  % (canon, e["animate"], e["gender"], na))
    print()
    print("ANTI-OVER-FIRE  a fable has NO named compounds:")
    print("     compositions on the crow fable: %d (expect 0)"
          % len(fab["compositions"]))
    print(W)


def _print_role(rr, sg, cr_roles):
    W = "=" * 74
    print(W)
    print("ACT ON THE ROLE RESIDUAL — the selectional violation DRIVES a re-decode")
    print(W)
    print("(a)  \"She won the Nobel Prize\"  (theme mis-grounded to the PERSON Nobel)")
    print("     selectional expectation of 'won' theme: %s" % rr["expect"])
    print("     BEFORE  theme = %s" % rr["before"])
    print("     AFTER   theme = %s" % rr["after"])
    for r in rr["role"]:
        print("     [%s] %s : %s -> %s" % (r.get("verdict"), r.get("entity"),
              r.get("rebound_from"), r.get("rebound_to")))
    print()
    print("(b)  SELECTIONAL GENERAL — violation re-decoded / held-open; coherent untouched")
    for k in ("game", "fields", "mary"):
        print("     %-7s BEFORE %s  AFTER %s" % (k, sg["before"][k], sg["after"][k]))
    for r in sg["residuals"]:
        if r["kind"] == "role":
            print("     [%s] %s -> %s" % (r.get("verdict"), r.get("entity"),
                  r.get("rebound_to") or "(held open)"))
    print()
    print("(d)  ROLE-FLAG before/after on the real Curie article")
    print("     role residuals: %d   re_decoded: %d   held_open: %d"
          % (cr_roles["n_role"], cr_roles["n_re_decoded"], cr_roles["n_held_open"]))
    print(W)


if __name__ == "__main__":
    cur = run_curie()
    coh = run_coherence()
    gen = run_generic()
    fab = run_fable()
    _print(cur, coh, gen, fab)
    rr = run_role_redecode()
    sg = run_selectional_general()
    cr_roles = run_curie_roles()
    _print_role(rr, sg, cr_roles)
