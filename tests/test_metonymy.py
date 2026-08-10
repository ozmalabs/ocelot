"""test_metonymy — the reader UNDERSTANDS regular METONYMY, the SECOND coherence
re-reading source (task-121, on top of task-120's compound composition).

Gates domains/cognitive_disambiguation.py (metonymy extension) +
seeds/metonymy_patterns.json + scripts/jabberwock_reads_metonymy.py:

  (a) author->works — 'read Shakespeare' -> theme = Shakespeare's WORKS; the reader
      STATES 'read shakespeare = read shakespeare's works' (verbatim).
  (b) place->team / place->government — 'won France' -> the French TEAM; 'Washington
      announced' -> the GOVERNMENT (agent-role shift), verbatim.
  (c) GATED (no over-fire) — 'met Shakespeare' does NOT shift ('meet' expects a
      person; a person coheres) — the theme is byte-identical.
  (d) GENERIC — any author (Dickens/Mozart) shifts via the creator TYPE, no name table.
  (e) COMPOSES with task-120 — one re-decode, three sources: compound resolves
      (task-120), metonymy resolves (task-121), neither -> HELD-OPEN.
  CROW BYTE-IDENTICAL — a fable's themes are literal; disambiguate mints/mutates
      nothing (the metonymy loop no-ops when no frame matches).
  GRAPH-NATIVE — the shift re-binds a graph edge to a `stands_for` metonym; the
      patterns are graph-resident TYPE-KEYED relations.
  NO NAME LITERAL / donkey=0 — no author/place NAME literal and no banned verb literal
      in the decision path (AST); no LLM; no `import re`.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_metonymy.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                       # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import comprehension_reader as cr                  # noqa: E402
from domains import cognitive_disambiguation as cd              # noqa: E402
import jabberwock_reads_metonymy as jrm                         # noqa: E402
import jabberwock_understands_compounds as juc                  # noqa: E402

_MODULE = os.path.join(ROOT, "domains", "cognitive_disambiguation.py")
_SEED = os.path.join(ROOT, "seeds", "metonymy_patterns.json")


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    dl.warm_wordnet("en")
    s, node = boot_core()
    return _Agent(s, node)


# --------------------------------------------------------------------------- #
#  (a) author->works — 'read Shakespeare' shifts to his works, STATED.
# --------------------------------------------------------------------------- #
def test_author_works_shift_and_stated():
    a = jrm.run_author_works()
    assert a["before"] == {"name": "shakespeare", "animate": 1.0, "category": "person"}
    assert a["after"]["name"] == "shakespeare_works"       # a BOUND theme, not a flag
    assert a["after"]["animate"] == 0.0
    assert a["after"]["category"] == "work"
    assert a["shift"]["pattern"] == "author_works"
    assert a["shift"]["verdict"] == "re_decoded"
    # the reader STATES the shift, verbatim (cognitive, not a re-label)
    assert a["shift"]["reading"] == "read shakespeare = read shakespeare's works"
    assert a["stated"] == "shakespeare stands for shakespeare's works"
    assert a["stands_for"] == "shakespeare_works"


# --------------------------------------------------------------------------- #
#  (b) place->team + place->government.
# --------------------------------------------------------------------------- #
def test_place_team_and_government():
    b = jrm.run_place_shifts()
    # place -> team ('won France')
    assert b["won_france"]["name"] == "france_team"
    assert b["won_france"]["category"] == "team"
    assert b["team"]["pattern"] == "place_team"
    assert b["team"]["reading"] == "won france = won the team representing france"
    assert b["team_stated"] == "france stands for the team representing france"
    # place -> government ('Washington announced' — an AGENT-role shift)
    assert b["govt"]["pattern"] == "place_government"
    assert b["govt"]["role"] == "agent"
    assert b["govt"]["reading"] == "washington announced = the government of washington announced"
    assert b["govt_stated"] == "washington stands for the government of washington"


# --------------------------------------------------------------------------- #
#  (c) GATED — 'met Shakespeare' does NOT shift (no over-fire).
# --------------------------------------------------------------------------- #
def test_gated_met_shakespeare_no_shift():
    c = jrm.run_gated_no_over_fire()
    assert c["before"] == c["after"]                       # byte-identical theme
    assert c["after"]["name"] == "shakespeare"
    assert c["after"]["animate"] == 1.0                    # still the person
    assert c["shifts"] == []                               # nothing shifted
    assert c["coherent"], "the person-theme of 'meet' is noted as coherent"


# --------------------------------------------------------------------------- #
#  (d) GENERIC — any author via the creator TYPE, no name table.
# --------------------------------------------------------------------------- #
def test_generic_any_author():
    d = jrm.run_generic()
    assert d["dickens"] == "dickens stands for dickens's works"
    assert d["mozart"] == "mozart stands for mozart's works"
    assert d["patterns"]["dickens"] == "author_works"
    assert d["patterns"]["mozart"] == "author_works"


# --------------------------------------------------------------------------- #
#  (e) COMPOSES with task-120 — compound | metonymy | neither(held-open).
# --------------------------------------------------------------------------- #
def test_composes_with_task_120_three_sources():
    e = jrm.run_composition()
    # the COMPOUND source (task-120) resolved this one
    assert e["compound_theme"]["name"] == "nobel_prize"
    assert e["compound_theme"]["animate"] == 0.0
    # the METONYMY source (task-121) resolved this one
    assert e["metonymy_theme"]["name"] == "orwell_works"
    assert e["metonymy_theme"]["category"] == "work"
    assert len(e["metonymy_shift"]) == 1
    # NEITHER source fits -> HELD-OPEN, not force-bound (anti-hallucination)
    assert e["held_theme"]["name"] == "mary"
    assert e["held_theme"]["animate"] == 1.0
    assert e["held"] and e["held"][0]["verdict"] == "held_open"


# --------------------------------------------------------------------------- #
#  CROW BYTE-IDENTICAL — a fable's themes are literal; metonymy no-ops.
# --------------------------------------------------------------------------- #
def test_fable_byte_identical():
    ag = _fresh()
    cr.read_and_comprehend(ag, juc.FABLE, max_sentences=40)

    def snap():
        out = {}
        for n in ag.s.nodes("SmEntity"):
            at = ag.s.node(n)["attrs"]
            nm = at.get("name")
            if nm:
                out[nm] = (at.get("coref_gender"), at.get("coref_animate"),
                           at.get("coref_category"))
        return out

    before = snap()
    rep = cd.disambiguate(ag, juc.FABLE)
    after = snap()
    assert rep["metonymy"]["shifts"] == []                 # no metonymy in a fable
    assert rep["compose"]["compositions"] == []
    assert before == after                                 # nothing minted or mutated


def test_gate_script_runs():
    # the whole gate script runs end-to-end (the executable narrative).
    a = jrm.run_author_works()
    b = jrm.run_place_shifts()
    c = jrm.run_gated_no_over_fire()
    d = jrm.run_generic()
    e = jrm.run_composition()
    jrm._print(a, b, c, d, e)


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE — the codebook is graph-resident TYPE-KEYED relations, the shift a
#  graph edge move.
# --------------------------------------------------------------------------- #
def test_codebook_is_graph_resident_and_type_keyed():
    ag = _fresh()
    cd.ensure_metonymy_codebook(ag)
    frames = cd._sel_frames(ag)
    pats = cd._metonymy_patterns(ag)
    assert frames and pats
    # every frame is keyed by a WordNet VERB synset + role + accept-set, not a verb str
    for f in frames:
        assert "." in str(f["verb_synset"])                # a WordNet synset name
        assert f["role"] in ("theme", "agent")
        assert isinstance(f["accepts"], set) and f["accepts"]
    # every pattern is a source-TYPE -> target-TYPE relation (a WordNet synset target)
    for p in pats:
        assert p["source_category"]                        # a TYPE, not a name
        assert "." in str(p["target_synset"])              # a WordNet synset name
    # the exercised patterns are present
    names = {p["pattern"] for p in pats}
    assert {"author_works", "place_team", "place_government"} <= names


def test_verb_frame_is_wordnet_derived():
    ag = _fresh()
    cd.ensure_metonymy_codebook(ag)
    assert cd.verb_frame(ag, "read", "theme") is not None      # read.v.01
    assert cd.verb_frame(ag, "reads", "theme") is not None      # morphy -> read
    assert cd.verb_frame(ag, "won", "theme") is not None        # morphy -> win
    assert cd.verb_frame(ag, "announced", "agent") is not None  # morphy -> announce
    assert cd.verb_frame(ag, "sleep", "theme") is None          # no frame -> no metonymy
    # a role a frame does not cover returns None (announce is an AGENT frame)
    assert cd.verb_frame(ag, "announced", "theme") is None


# --------------------------------------------------------------------------- #
#  NO NAME LITERAL — the fix is GENERIC (type-keyed), not a Shakespeare/France
#  special-case; and no banned verb literal drives a comparison.
# --------------------------------------------------------------------------- #
def _string_constants_non_docstring(path):
    tree = ast.parse(open(path).read())
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            b = getattr(node, "body", [])
            if b and isinstance(b[0], ast.Expr) and isinstance(getattr(b[0], "value", None), ast.Constant) \
                    and isinstance(b[0].value.value, str):
                docs.add(id(b[0].value))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            out.append(node.value)
    return out


def test_no_name_literal_in_decision_path():
    banned_names = {"shakespeare", "dickens", "mozart", "france", "washington",
                    "orwell", "nobel", "author", "writer", "composer", "painter",
                    "place", "country", "capital"}
    for lit in _string_constants_non_docstring(_MODULE):
        low = lit.lower()
        for b in banned_names:
            assert b not in low.split() and low != b, (b, lit)
    # the seed's DATA values are WordNet synsets / TYPE tags, not names
    seed = json.load(open(_SEED))
    for nd in seed["nodes"]:
        for k, v in nd.get("attrs", {}).items():
            if k in ("note", "gloss") or not isinstance(v, str):
                continue
            low = v.lower()
            for b in ("shakespeare", "dickens", "mozart", "france", "washington"):
                assert b not in low, (b, v)


def test_no_verb_literal_special_case_in_decision_path():
    # the verb class is WordNet-derived (verb_frame), not `verb == "read"` — no verb
    # form drives a COMPARISON in the module.
    tree = ast.parse(open(_MODULE).read())
    banned = {"read", "reads", "reading", "meet", "met", "win", "won", "wins",
              "announce", "announced", "announces"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for operand in [node.left, *node.comparators]:
                if isinstance(operand, ast.Constant) and isinstance(operand.value, str):
                    assert operand.value.lower() not in banned, operand.value


def test_donkey_zero_no_regex_no_llm():
    tree = ast.parse(open(_MODULE).read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(a.name != "re" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re"
    for lit in _string_constants_non_docstring(_MODULE):
        assert "openai" not in lit.lower()
        assert "anthropic" not in lit.lower()
