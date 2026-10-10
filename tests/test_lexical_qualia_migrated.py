"""LEXICAL QUALIA INDEX (tranche 15): every held word links to one or more
qualia, and steering matches a turn to a filed concern by qualia, not words.

Pinned claims:
  * every held single-word Concept on a full boot carries >= 1 has_quale edge;
  * the index is native graph data: Quale nodes + a has_quale DAG, and a
    word's closure is the native ReachableFrom Term;
  * fuzzy by shared meaning: two different words meet at a shared quale;
  * extent is an exact count consistent with the closures;
  * a word the agent does not hold becomes held when WordNet gives it a sense,
    and a token with no sense and no role stays unheld;
  * steering picks by qualia (a word that never appears in the concern can
    still name it), and the generator is idempotent.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.world_adapter import WorldAdapter   # noqa: E402
from substrate.boot_all import load_all_seeds      # noqa: E402
from domains import lexical_qualia as lq           # noqa: E402

_WORD = re.compile(r"^[a-z][a-z'-]*$")


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _concept(a, name):
    hits = a.inner.nodes_where("Concept", "name", name)
    return hits[0] if hits else None


def _closure(a, node):
    return set(a.inner.evaluate({"type": "ReachableFrom", "node": {"type": "Var", "name": "w"},
                                 "edge_type": "has_quale"}, {"w": node}) or [])


def test_every_held_word_links_to_a_quale(agent):
    missing = []
    for c in agent.s.nodes("Concept"):
        nm = agent.s.node(c)["attrs"].get("name")
        if isinstance(nm, str) and _WORD.match(nm) and not lq.held_qualia(agent, c):
            missing.append(nm)
    assert missing == [], missing[:20]


def test_index_is_native_and_closure_is_reachable_from(agent):
    assert list(agent.s.nodes("QualiaIndex"))
    data = _concept(agent, "gap")
    senses = {agent.s.node(q)["attrs"]["name"] for q in lq.held_qualia(agent, data)}
    assert "gap.n.01" in senses
    clos = {agent.s.node(q)["attrs"]["name"] for q in _closure(agent, data)}
    assert senses <= clos and "entity.n.01" in clos     # hypernyms reached natively


def test_function_word_quale_is_its_closed_class_role(agent):
    the = _concept(agent, "the")
    assert {agent.s.node(q)["attrs"]["name"] for q in lq.held_qualia(agent, the)} == {"closed_class:determiner"}


def test_new_word_becomes_held_with_qualia_and_unknown_token_does_not():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    assert _concept(a, "alphabetise") is None and _concept(a, "tabulate") is None
    a.converse("Alphabetise the data.", speech_act="request")
    a.converse("Tabulate the list.", speech_act="request")
    alpha, tab = _concept(a, "alphabetise"), _concept(a, "tabulate")
    assert alpha is not None and tab is not None
    # "alphabetise" shares no letters with "arrange" but means a kind of it:
    # the word's sense alphabetize.v.01 has the quale arrange.v.01 above it.
    arrange = _concept(a, "arrange") or lq.ground_word(a, "arrange")
    shared = {a.s.node(q)["attrs"]["name"] for q in _closure(a, alpha) & _closure(a, arrange)}
    assert "arrange.v.01" in shared, "different words meet at a shared quale"
    # "tabulate" meets "arrange" at a DIFFERENT sense (arrange.v.06): senses stay distinct
    assert "arrange.v.06" in {a.s.node(q)["attrs"]["name"] for q in _closure(a, tab) & _closure(a, arrange)}
    # extent is an exact count: arrange.v.01's extent counts alphabetise and arrange
    arr = next(q for q in _closure(a, alpha) if a.s.node(q)["attrs"]["name"] == "arrange.v.01")
    assert a.s.node(arr)["attrs"]["extent"] >= 2
    a.converse("Frobnicate the zorblat.", speech_act="request")
    assert _concept(a, "zorblat") is None, "a token with no sense and no role stays unheld"


def test_steering_names_a_concern_by_qualia_not_words():
    import jabberwock_daemon as jd
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.converse("Hello.", speech_act="greeting")
    a.converse("Condense the data.", speech_act="request")
    a.converse("Alphabetise the list.", speech_act="request")
    # "ordering" never appears in either concern; it means what alphabetising does
    a.converse("Work on the ordering gap.", speech_act="request")
    p = jd._steer_tick(a)
    assert p and p[0].get("ok") and "alphabetise" in p[0].get("about", "")


def test_generators_are_idempotent():
    for script in ("gen_steer_qualia_match.py", "gen_steer_best_match.py"):
        out = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", script)],
                             capture_output=True, text=True, cwd=ROOT)
        assert out.returncode == 0 and "already applied" in out.stdout, (script, out.stdout, out.stderr)


# --- tranche 16: persisted sense table replaces in-process WordNet -----------------

def test_sense_table_reproduces_wordnet_synsets_exactly():
    """domains/wordnet_table answers from domain_data/wordnet_senses.sqlite
    with NLTK's own index and morphy; it must agree with NLTK."""
    from domains import wordnet_table as wt
    from domains.dict_teacher import _wordnet
    wn = _wordnet()
    for w in ("arranging", "geese", "ran", "better", "data", "alphabetise", "sort", "the", "zorblat"):
        assert sorted(set(wt.synsets(w))) == sorted({s.name() for s in wn.synsets(w)}), w
    assert wt.hypernyms("alphabetize.v.01") == ["arrange.v.01"]


def test_runtime_grounding_does_not_load_the_wordnet_corpus(monkeypatch):
    """A word heard for the first time is grounded from the on-disk table: the
    lexical qualia path never calls the in-process NLTK corpus."""
    from domains import dict_teacher as dt
    calls = []
    real = dt._wordnet
    monkeypatch.setattr(dt, "_wordnet", lambda *a, **k: calls.append(1) or real(*a, **k))
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    before = len(calls)
    c = lq.ground_word(a, "alphabetise")
    assert c is not None and lq.held_qualia(a, c)
    assert len(calls) == before, "lexical qualia grounding must not touch NLTK"


# --- tranche 17: definitional grounding + the runtime coverage invariant --------

def _names(a, nodes):
    return {a.s.node(q)["attrs"]["name"] for q in nodes}


def test_jargon_word_is_grounded_through_its_definition_genus(agent):
    """'kubernetes' has no WordNet sense; its held definition ("Container
    orchestrator: ...") names the genus, so its quale is the definition whose
    parents are the genus's noun senses -- and it meets another word there."""
    k = _concept(agent, "kubernetes")
    (q,) = lq.held_qualia(agent, k)
    at = agent.s.node(q)["attrs"]
    assert at["name"] == "definition:kubernetes" and at["dimension"] == "lexical:definition"
    assert at["genus"] == "orchestrator"
    assert "orchestrator.n.01" in _names(agent, _closure(agent, k))
    ms, svc = _concept(agent, "microservice"), _concept(agent, "service")
    assert _names(agent, _closure(agent, ms) & _closure(agent, svc)) & {"service.n.01", "service.n.02"}


def test_senseless_function_word_gets_its_role_and_stub_stays_identity(agent):
    assert _names(agent, lq.held_qualia(agent, _concept(agent, "she"))) == {"closed_class:pronoun"}
    # a disambiguation stub ("Bour may refer to:") names no genus: honest identity
    assert _names(agent, lq.held_qualia(agent, _concept(agent, "bour"))) == {"identity:bour"}
    assert lq.definition_genus("bour", "Bour may refer to:") is None


def test_index_stats_match_the_graph(agent):
    import json
    seed = json.load(open(os.path.join(ROOT, "seeds", "lexical_qualia.json")))
    st = seed["stats"]
    dims = {}
    for q in agent.s.nodes("Quale"):
        d = agent.s.node(q)["attrs"]["dimension"]
        dims[d] = dims.get(d, 0) + 1
    assert dims.get("lexical:identity", 0) == st["identity_only_words"] == st["words_by_grounding"]["identity"]
    assert dims.get("lexical:definition", 0) == st["words_by_grounding"]["definition"]


def test_runtime_minted_concept_gets_qualia_when_first_referred_to():
    """A Concept minted by a path that does not know the index (as
    teach_microtheory does) gains qualia the first time a turn mentions it."""
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    c = a.s.add_node("Concept", {"name": "quokkaware",
                                 "definition": "A small marsupial mascot used in the test fixture."})
    assert not lq.held_qualia(a, c)
    a.converse("Tell me about quokkaware.", speech_act="request")
    (q,) = lq.held_qualia(a, c)
    assert a.s.node(q)["attrs"]["genus"] == "mascot"
    assert "mascot.n.01" in _names(a, _closure(a, c))


def test_steering_names_a_concern_through_a_definition():
    """'orchestrator' never appears in either concern; it is what kubernetes
    was DEFINED as. Before tranche 17 kubernetes carried only its identity
    quale and this turn fell to the clarify floor."""
    import jabberwock_daemon as jd
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.converse("Hello.", speech_act="greeting")
    a.converse("Condense the data.", speech_act="request")
    a.converse("Debug the kubernetes rollout.", speech_act="request")
    a.converse("Work on the orchestrator gap.", speech_act="request")
    p = jd._steer_tick(a)
    assert p and p[0].get("ok") and "kubernetes" in p[0].get("about", ""), p


def test_steering_aperture_generator_is_idempotent():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "gen_steer_aperture_definition.py")],
                         capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0 and "already applied" in out.stdout, (out.stdout, out.stderr)
