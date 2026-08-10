"""CHARACTER THEORY OF MIND (domains/character_tom.py).

situation_model_reader.py builds a SITUATION MODEL of the story WORLD (the
glass is now on the floor, broken) but never a CHARACTER's mental state.
domains/psychology.py has a real belief/desire/intention/knowledge taxonomy,
but aimed at the AGENT's own mind, and reading_collapse's construction
codebook has no propositional-attitude construction — "Sally thinks the ball
is in the basket" has nowhere to ground. This module adds ONE construction
('propositional_attitude', signature [["ATTITUDE"]], decoded by the SAME
ShapeDecode collapse designation/possession already use) over an ATTITUDE
marker-class (believes/thinks/knows/wants/hopes/fears/wishes/doubts, seed
members; an unseen verb joins by adjacency, mirroring COS exactly) and grounds
the COMPLEMENT as a NESTED belief-world proposition (belief/knowledge) or the
character's GOAL/intentionality index (desire) — never onto the actual world.

Discriminative gates (donkey = 0, no LLM):

  * SALLY-ANNE — the headline: a nested false belief distinct from reality.
  * CHARACTER GOAL — want(crow, water/drink) grounds the crow's intentionality
    index, queryable as "what did the crow want".
  * ATTITUDE IS A CLASS — an unseen attitude verb ('suspects') joins by
    adjacency (nearness reported); a FACTUAL sentence mints no attitude.
  * GRAPH-NATIVE SOURCE AUDIT — the construction is the ShapeDecode collapse's
    verdict; the belief-world is graph nodes; no `import re`.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_character_tom.py -p no:randomly -q
"""
from __future__ import annotations

import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import character_tom as ctom             # noqa: E402
from domains import situation_model_reader as smr     # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


# --------------------------------------------------------------------------- #
#  SALLY-ANNE — nested false belief, distinct from the actual world.
# --------------------------------------------------------------------------- #
def test_sally_anne_nested_false_belief_distinct_from_actual():
    a = _fresh()
    text = "Sally thinks the ball is in the basket. The ball is in the box."
    out = ctom.read_character_tom(a, text)

    kinds = [r["kind"] for r in out["results"]]
    assert kinds == ["attitude", "factual"]

    belief = ctom.character_belief_world(a, "sally")
    assert "ball" in belief
    assert belief["ball"].get("in_basket") == 1
    assert "in_box" not in belief["ball"]

    actual = out["actual_world"]
    assert "ball" in actual
    assert actual["ball"].get("in_box") == 1
    assert actual["ball"].get("in_basket") != 1

    # THE nested belief and the actual world are genuinely DISTINCT nodes.
    assert belief["ball"] != actual["ball"]


def test_sally_anne_attitude_flavor_is_belief():
    a = _fresh()
    ctom.read_character_tom(a, "Sally thinks the ball is in the basket.")
    rec = ctom.ingest_attitude_sentence(a, "Sally thinks the ball is in the basket.", t=1)
    assert rec["membership"]["flavor"] == "belief"
    assert rec["attitude_verb"] == "think"


# --------------------------------------------------------------------------- #
#  CHARACTER GOAL — want(crow, water/drink) grounds the intentionality index.
# --------------------------------------------------------------------------- #
def test_crow_wants_water_grounds_goal():
    a = _fresh()
    rec = ctom.ingest_attitude_sentence(a, "The crow wanted water.", t=1)
    assert rec["kind"] == "attitude"
    assert rec["membership"]["flavor"] == "desire"
    assert rec["subject"] == "crow"
    assert rec["goal"] == "water"
    assert ctom.character_goal(a, "crow") == "water"


def test_crow_wants_to_drink_grounds_goal():
    a = _fresh()
    rec = ctom.ingest_attitude_sentence(a, "The crow wanted to drink.", t=1)
    assert rec["kind"] == "attitude"
    assert rec["membership"]["flavor"] == "desire"
    assert rec["goal"] == "drink"
    assert ctom.character_goal(a, "crow") == "drink"


def test_goal_is_an_intentionality_index_on_an_smevent():
    a = _fresh()
    ctom.ingest_attitude_sentence(a, "The crow wanted water.", t=1)
    sub = a.s
    events = [sub.node(n)["attrs"] for n in sub.nodes("SmEvent")]
    goal_events = [at for at in events if at.get("idx_protagonist") == "crow"]
    assert len(goal_events) == 1
    assert goal_events[0].get("idx_intentionality") == "water"
    assert goal_events[0].get("verb") == "want"


# --------------------------------------------------------------------------- #
#  ATTITUDE IS A CLASS — unseen verb joins by adjacency; discriminative.
# --------------------------------------------------------------------------- #
def test_unseen_attitude_verb_joins_by_adjacency():
    # a BRAND NEW agent: "suspect" is not a seed member, so the FIRST time it
    # is encountered it must resolve via ADJACENCY (nearness reported).
    a = _fresh()
    rec = ctom.ingest_attitude_sentence(a, "Sally suspects the ball is in the basket.", t=1)
    assert rec is not None
    assert rec["kind"] == "attitude"
    assert rec["attitude_verb"] == "suspect"
    mem = rec["membership"]
    assert mem["attitude"] is True
    assert mem["via"] == "adjacency"
    assert mem["nearness"] > 0.0
    assert mem["nearest"] in ("believe", "think", "know", "want")
    belief = ctom.character_belief_world(a, "sally")
    assert "ball" in belief and belief["ball"].get("in_basket") == 1

    # HAVING JOINED, the class LEARNED it — a later occurrence resolves as a
    # MEMBER (the same "joined... a member thereafter" behaviour COS documents).
    mem2 = ctom.attitude_membership(a, "suspects")
    assert mem2["attitude"] is True
    assert mem2["via"] == "member"
    assert mem2["flavor"] == mem["flavor"]


# --------------------------------------------------------------------------- #
#  COMPLEMENT-KIND GATE — a BELIEF/KNOWLEDGE attitude fires ONLY over a
#  PROPOSITIONAL complement; a bare NOMINAL complement ('had a narrow neck')
#  is NOT an attitude, it's possession wearing an adjacency-joined verb.
# --------------------------------------------------------------------------- #
def test_possession_with_nominal_complement_mints_no_attitude():
    """'The pitcher had a narrow neck.' -- 'have' joins ATTITUDE by adjacency
    (nearness to 'know'), but its complement is a bare NOUN PHRASE, not a
    clause: NO attitude construction, NO belief-world (verbatim gate case)."""
    a = _fresh()
    rec = ctom.ingest_attitude_sentence(a, "The pitcher had a narrow neck.", t=1)
    assert rec is None
    belief = ctom.character_belief_world(a, "pitcher")
    assert belief == {}
    sub = a.s
    nested = [n for n in sub.nodes("SmEntity") if sub.node(n)["attrs"].get("nested")]
    assert nested == []


def test_sally_thinks_still_fires_with_propositional_complement():
    """'Sally thinks the ball is in the basket.' -- the SAME class of gate that
    blocks 'had a narrow neck' does NOT block this: the complement grounds a
    real predication (definitional 'is_a(ball, in_basket)'), a PROPOSITION,
    so the belief-world STILL mints (verbatim gate case)."""
    a = _fresh()
    rec = ctom.ingest_attitude_sentence(a, "Sally thinks the ball is in the basket.", t=1)
    assert rec is not None
    assert rec["kind"] == "attitude"
    assert rec["membership"]["flavor"] == "belief"
    belief = ctom.character_belief_world(a, "sally")
    assert belief["ball"].get("in_basket") == 1


def test_crow_wanted_water_still_grounds_goal_after_gate():
    """'The crow wanted water.' -- DESIRE keeps the noun-GOAL path valid; the
    belief/knowledge complement-kind gate does not apply to desire at all
    (verbatim gate case)."""
    a = _fresh()
    rec = ctom.ingest_attitude_sentence(a, "The crow wanted water.", t=1)
    assert rec is not None
    assert rec["kind"] == "attitude"
    assert rec["membership"]["flavor"] == "desire"
    assert rec["goal"] == "water"
    assert ctom.character_goal(a, "crow") == "water"


def test_complement_gate_is_graph_native_not_a_verb_string_check():
    """The complement-kind DECISION is read off the held nominal faculty
    (consumption_quality.is_nominal) applied to the complement's OWN
    grounding (its predication's relation head, or its cleaned surface) --
    never a Python branch on the attitude verb's lemma/surface ('have' vs
    'think' vs ...)."""
    import inspect
    src = inspect.getsource(ctom._complement_is_propositional)
    assert "cq.is_nominal" in src
    assert "lemma" not in src
    # the verb string itself never appears as a literal compared against.
    assert '"have"' not in src and "'have'" not in src
    assert '"think"' not in src and "'think'" not in src


def test_factual_sentence_mints_no_attitude():
    a = _fresh()
    rec = ctom.ingest_attitude_sentence(a, "Sally put the ball in the basket.", t=1)
    assert rec is None                    # DISCRIMINATIVE — no attitude construction


def test_factual_sentence_updates_actual_world_only():
    a = _fresh()
    out = ctom.read_character_tom(a, "Sally put the ball in the basket.")
    assert out["results"][0]["kind"] == "factual"
    belief = ctom.character_belief_world(a, "sally")
    assert belief == {}                   # no belief-world minted for a factual sentence


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT.
# --------------------------------------------------------------------------- #
def test_construction_is_the_shapedecode_verdict():
    a = _fresh()
    ctom.ensure_seeds(a)
    decode = ctom.decode_attitude_construction(a, ["sally"], ["the", "ball", "is", "in", "the", "basket"])
    assert decode["construction"] == "propositional_attitude"
    assert decode["shape_fit"] >= 1
    assert decode["residual"] == []


def test_no_import_re_in_character_tom():
    import ast
    src = inspect.getsource(ctom)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names), "import re found"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "from re import ... found"


def test_attitude_class_not_wired_into_reading_time_skeleton():
    """The ATTITUDE marker-class must NOT perturb reading_collapse's own
    construction decode for an ordinary clause (mirrors the COS class's own
    documented isolation) — 'ATTITUDE' is not in reading_collapse's `_SKELETON`
    set."""
    from domains import reading_collapse as rc
    assert "ATTITUDE" not in rc._SKELETON


def test_nested_belief_world_is_graph_nodes_not_python_state():
    a = _fresh()
    ctom.read_character_tom(a, "Sally thinks the ball is in the basket.")
    sub = a.s
    nested = [n for n in sub.nodes("SmEntity") if sub.node(n)["attrs"].get("nested")]
    assert len(nested) >= 1
    at = sub.node(nested[0])["attrs"]
    assert at.get("belief_holder") == "sally"


# --------------------------------------------------------------------------- #
#  NO REGRESSION — reused modules stay green (spot checks; the full suites run
#  separately via `pytest tests/ -k migrated`).
# --------------------------------------------------------------------------- #
def test_situation_model_reader_unaffected_by_import():
    a = _fresh()
    smr.ensure_seeds(a)
    rec = smr.ingest_predication(a, ["drop", "john", "glass"], t=1)
    assert rec["cos"] is True
    assert rec["canon"] == "drop"


def test_reading_collapse_definitional_construction_unaffected():
    from domains import reading_collapse as rc
    a = _fresh()
    rec = rc.read_clause(a, "A dog is an animal.", write=False)
    assert rec["construction"] in ("definitional", "definitional_bare")
