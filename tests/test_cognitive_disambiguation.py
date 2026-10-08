"""test_cognitive_disambiguation — the reader UNDERSTANDS a named compound
(coherence-check + compositional composition), it does not PARSE it.

Gates domains/cognitive_disambiguation.py + domain_data/named_compound_heads.json +
scripts/jabberwock_understands_compounds.py:

  (a) THE NOBEL LEAK — on the real Curie article, the person-as-prize incoherence is
      caught (nobel_prize was absorbed into the person 'nobel'), and the
      nobel-female-leak is GONE (gender female -> ''); the SUBJECT 'curie' stays
      female (own evidence), 'pierre' stays male.
  (b) GENERAL COHERENCE-CHECK — a constructed incoherence (a substance gendered; a
      person as the theme of 'won') is re-checked (Nobel is ONE instance).
  (c) STATED INFERENCE — the reader STATES 'nobel prize = a prize named after nobel'
      + a `named_after` relation (cognitive, not a re-label).
  (d) GENERIC — Fields Medal / Turing Award / Curie Institute / Boyle's Law compose
      the same, head-type entities named after the person, not the persons.
  (e) COGNITIVE not parsing — NO 'nobel' literal in the decision path (AST).
  CROW BYTE-IDENTICAL — a fable has no named compounds, so disambiguate mutates
      nothing (the encyclopedic-only pass; the fable route never calls it).
  ANTI-OVER-FIRE — a person head ('laureate') is NOT demoted; a generic compound is
      not mis-composed as named-after-someone.
  GRAPH-NATIVE / donkey=0 — the coherence residual is a native Filter Term; no LLM,
      no `import re`, no 'nobel' table.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_cognitive_disambiguation.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                       # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import comprehension_reader as cr                  # noqa: E402
from domains import cognitive_disambiguation as cd              # noqa: E402
import jabberwock_understands_compounds as juc                  # noqa: E402

_CURIE_CACHE = os.path.join(ROOT, "data", "register", "curie.txt")
_HAVE_CURIE = os.path.exists(_CURIE_CACHE)
_needs_curie = pytest.mark.skipif(not _HAVE_CURIE, reason="curie cache absent")
_MODULE = os.path.join(ROOT, "domains", "cognitive_disambiguation.py")
_SEED = os.path.join(ROOT, "domain_data", "named_compound_heads.json")


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
#  (a) THE NOBEL LEAK — the real article.
# --------------------------------------------------------------------------- #
@_needs_curie
def test_nobel_leak_gone_and_incoherence_caught():
    rep = juc.run_curie()
    before, after = rep["before"], rep["after"]
    # the female leak on the bare 'nobel' namesake is GONE
    assert before["nobel"]["gender"] == "female"
    assert after["nobel"]["gender"] == ""
    # the person-as-prize incoherence was caught: 'nobel_prize' had been absorbed
    # into the person 'nobel' (merged_into), and is restored as a first-class entity
    assert before["nobel_prize"]["merged_into"] == "nobel"
    assert after["nobel_prize"]["merged_into"] == ""
    assert after["nobel_prize"]["animate"] == 0.0
    assert after["nobel_prize"]["gender"] == ""
    assert rep["named_after_prize"] == "nobel"
    inco = [c for c in rep["report"]["compose"]["compositions"] if c["incoherence"]]
    assert any(c["compound"] == "nobel_prize" for c in inco)
    # the SUBJECT and the other person keep their OWN gender (no collateral damage)
    assert after["curie"]["gender"] == "female"
    assert after["pierre"]["gender"] == "male"


# --------------------------------------------------------------------------- #
#  (b) GENERAL COHERENCE-CHECK — constructed incoherence.
# --------------------------------------------------------------------------- #
def test_general_coherence_check():
    rep = juc.run_coherence()
    assert rep["radium_before"] == "female"
    assert rep["radium_after"] == ""            # a substance has no sex -> re-decoded
    kinds = {r["kind"] for r in rep["residuals"]}
    assert "animacy_gender" in kinds            # substance-gendered residual
    assert "role" in kinds                      # person-as-theme-of-'won' residual
    role = [r for r in rep["residuals"] if r["kind"] == "role"]
    assert any(r["entity"] == "john" and r["verb"] == "win" for r in role)


# --------------------------------------------------------------------------- #
#  (c) STATED INFERENCE — cognitive, not a re-label.
# --------------------------------------------------------------------------- #
def test_states_the_inference():
    gen = juc.run_generic()
    meanings = {s["meaning"] for s in gen["stated"]}
    assert "nobel prize = a prize named after nobel" in meanings


# --------------------------------------------------------------------------- #
#  (d) GENERIC compounds.
# --------------------------------------------------------------------------- #
def test_generic_compounds():
    gen = juc.run_generic()
    expect = {"fields_medal": "fields", "turing_award": "turing",
              "curie_institute": "curie", "nobel_prize": "nobel",
              "boyle_law": "boyle"}
    for canon, honoree in expect.items():
        ent, na = gen["entities"][canon]
        assert ent is not None, canon
        assert ent["animate"] == 0.0, canon      # an award/institution is inanimate
        assert ent["gender"] == "", canon        # and carries no gender
        assert na == honoree, canon              # named after the person, not the person


def test_head_type_is_wordnet_derived_and_person_head_not_demoted():
    ag = _fresh()
    cd.ensure_head_codebook(ag)
    # award / institution / proposition / law heads are inanimate head-types
    for w in ("prize", "medal", "award", "university", "institute", "committee",
              "theorem", "law"):
        assert cd.head_type(ag, w) is not None, w
        assert cd.head_type(ag, w)[1] == 0.0, w
    # a PERSON head ('laureate' -> noun.person) is NOT a head-type -> not demoted
    assert cd.head_type(ag, "laureate") is None
    # a plain common noun is not a head-type
    assert cd.head_type(ag, "dog") is None


# --------------------------------------------------------------------------- #
#  CROW BYTE-IDENTICAL — a fable has no named compounds; disambiguate mutates
#  nothing on it.
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
    assert rep["compose"]["compositions"] == []      # no named compounds in a fable
    assert before == after                           # nothing mutated


# --------------------------------------------------------------------------- #
#  ACT ON THE ROLE RESIDUAL — the selectional violation DRIVES a re-decode.
# --------------------------------------------------------------------------- #
def test_role_redecode_won_nobel_prize():
    # (a) "She won the Nobel Prize": theme mis-grounded to the PERSON Nobel is
    # RE-BOUND to the PRIZE (winnable, inanimate) — the role residual is ACTED ON.
    rr = juc.run_role_redecode()
    assert rr["before"] == {"name": "nobel", "animate": 1.0, "category": "person"}
    assert rr["after"]["name"] == "nobel_prize"     # a BOUND theme, not a flag
    assert rr["after"]["animate"] == 0.0            # winnable, inanimate
    assert rr["expect"]["expect_animate"] == 0.0    # the selectional expectation
    role = rr["role"]
    assert len(role) == 1
    assert role[0]["verdict"] == "re_decoded"       # acted on, not merely flagged
    assert role[0]["rebound_from"] == "nobel"
    assert role[0]["rebound_to"] == "nobel_prize"


def test_selectional_general_and_no_over_fire():
    # (b) a VIOLATION with a coherent re-reading -> re-decoded; a violation with NO
    # re-reading -> HELD-OPEN (not force-bound); a COHERENT theme -> UNTOUCHED.
    sg = juc.run_selectional_general()
    # coherent theme ('game' is a winnable thing) is byte-identical — NO over-fire
    assert sg["before"]["game"] == sg["after"]["game"]
    assert sg["after"]["game"]["name"] == "game"
    # violation WITH a coherent re-reading is re-decoded (composes with the compound)
    assert sg["after"]["fields"]["name"] == "fields_medal"
    assert sg["after"]["fields"]["animate"] == 0.0
    # violation with NO coherent re-reading is HELD-OPEN (anti-hallucination)
    assert sg["after"]["mary"] == sg["before"]["mary"]
    assert sg["after"]["mary"]["name"] == "mary"
    role = {r["entity"]: r for r in sg["residuals"] if r["kind"] == "role"}
    assert role["fields"]["verdict"] == "re_decoded"
    assert role["mary"]["verdict"] == "held_open"
    assert "game" not in role                       # a coherent theme is not a residual


@_needs_curie
def test_curie_role_flags_carry_a_verdict():
    # (d) every role residual on the real article now carries a VERDICT — none is a
    # blind flag. On the real article the reader already grounds 'won'->'nobel_prize'
    # (coherent, not flagged); the remaining role flags are parse noise with no
    # re-bindable winnable compound (or the subject-guard holds), so they are
    # honestly HELD-OPEN — reported, never silently dropped.
    cr = juc.run_curie_roles()
    assert cr["n_role"] >= 1
    assert cr["n_re_decoded"] + cr["n_held_open"] == cr["n_role"]
    for r in cr["role"]:
        assert r["verdict"] in ("re_decoded", "held_open")


def test_role_residual_is_a_graph_rebind_not_a_flag():
    # the re-decode is a graph MUTATION (a theme edge moved from the person to the
    # compound), driven by the selectional predicate — not an LLM, not a Python
    # verb table. Build the mis-grounding directly and show the edge move.
    ag = _fresh()
    cd.ensure_head_codebook(ag)
    s = ag.s
    person = s.add_node("SmEntity", {"name": "turing", "coref_category": "person",
                                     "coref_animate": 1.0, "coref_mentions": 2.0})
    ev = s.add_node("SmEvent", {"verb": "win", "surface": "won"})
    s._inner.add_edge_unchecked(ev, "theme", person)
    cd.compose_named_compounds(ag, "She won the Turing Award.")
    assert cd.selectional_expectation(ag, "won") is not None      # WordNet verb frame
    assert cd.selectional_expectation(ag, "sleep") is None        # non-acquire -> no expectation
    cd.coherence_check(ag, "She won the Turing Award.")
    theme = cd.event_theme(ag, ev)
    assert theme["name"] == "turing_award"          # the edge was re-bound
    assert theme["animate"] == 0.0


# --------------------------------------------------------------------------- #
#  NO VERB LITERAL in the decision path — the fix is GENERIC (selectional
#  coherence), not a 'won'/'win'/'receive' special-case.
# --------------------------------------------------------------------------- #
def test_no_verb_literal_special_case_in_decision_path():
    # no verb-form string literal drives any COMPARISON in the module — the verb
    # class is WordNet-derived (is_acquire_verb), not `verb == "win"`.
    tree = ast.parse(open(_MODULE).read())
    banned = {"win", "won", "wins", "receive", "received", "award", "awarded",
              "earn", "earned", "get", "got", "nobel", "prize"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for operand in [node.left, *node.comparators]:
                if isinstance(operand, ast.Constant) and isinstance(operand.value, str):
                    assert operand.value.lower() not in banned, operand.value


# --------------------------------------------------------------------------- #
#  (e) COGNITIVE not parsing — no 'nobel' literal in the decision path.
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


def test_no_nobel_literal_in_decision_path():
    # no 'nobel' string literal drives any decision (docstrings excluded)
    for lit in _string_constants_non_docstring(_MODULE):
        assert "nobel" not in lit.lower(), lit
    # the seed's DATA values are WordNet synsets, not names
    import json
    seed = json.load(open(_SEED))
    for nd in seed["nodes"]:
        for v in nd.get("attrs", {}).values():
            if isinstance(v, str) and v not in (nd["attrs"].get("note", ""),
                                                nd["attrs"].get("gloss", "")):
                assert "nobel" not in v.lower(), v


def test_donkey_zero_no_regex():
    tree = ast.parse(open(_MODULE).read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(a.name != "re" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re"
    # no LLM/oracle call in the decision path
    for lit in _string_constants_non_docstring(_MODULE):
        assert "openai" not in lit.lower()


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE — the coherence residual is a native Filter Term.
# --------------------------------------------------------------------------- #
def test_coherence_residual_is_native_filter():
    ag = _fresh()
    cd.ensure_head_codebook(ag)
    s = ag.s
    s.add_node("SmEntity", {"name": "uranium", "coref_animate": 0.0,
                            "coref_gender": "female"})
    resid = cd._inanimate_gendered(ag)           # runs a native Filter Term
    names = {s.node(n)["attrs"].get("name") for n in resid}
    assert "uranium" in names
