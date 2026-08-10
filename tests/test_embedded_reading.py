"""STANCE-RELATIVE LICENSING + DECOUPLED (embedded) READING — the correction
that licensing is relative to the belief-world / stance.

The father's 'Beware the Jabberwock, my son!' yields TWO verdicts by STANCE:

  * DETACHED (the reader's OWN belief-world) — the warning is UNLICENSED as
    objective fact: the reader cannot verify it, so the danger is UNDETERMINED
    and the goal is HELD OPEN (task 101, byte-identical, unchanged).
  * EMBEDDED-CHILD (the child's nested belief-world) — the warning is LICENSED:
    the child TRUSTS the father (a licensed source WITHIN the child's world), so
    'the Jabberwock is dangerous' is established there and the quest to slay it
    is warranted. The child-model correctly believes the danger, GIVEN its model.

THE CAPABILITY = DECOUPLING modeling a belief from HOLDING it. The reader MODELS
that the child believes the danger (licensed within the child's world) WHILE NOT
HOLDING that belief itself — its own verdict stays detached (undetermined). The
belief-world BOUNDARY is MAINTAINED: the danger-belief lives ONLY in the child's
nested belief_world (a modeled object indexed to the child), NEVER in the
reader's own belief set. Immersion COLLAPSES that boundary (child's belief
becomes the reader's); the mature reading MAINTAINS it.

  * STANCE-RELATIVE PROOF — the SAME warning is UNLICENSED detached + LICENSED
    embedded (both verdicts).
  * DISCRIMINATIVE — a warning from a source the child does NOT trust (a foe)
    does NOT license the belief even embedded (trust is the signal).
  * CROW — unchanged: thirst is a felt need-state, licensed regardless of
    stance; no divergence, byte-identical.
  * GRAPH-NATIVE — the `trusts` relation + belief-world licensing are graph-
    resident (character_tom belief_world + a trusts edge); the stance is which
    belief-world frames the read; no `import re`; no story literal (AST audit);
    donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_embedded_reading.py -p no:randomly -q
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

from substrate.boot_core import boot_core                # noqa: E402
from domains import dictionary_lexicon as dl              # noqa: E402
from domains import inference_generation as ig            # noqa: E402
from domains import reader_response as rr                 # noqa: E402
from domains import character_tom as ctom                 # noqa: E402


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


JABBERWOCKY = "Beware the Jabberwock, my son! He took his vorpal sword in hand."
UNTRUSTED = "Beware the Jabberwock, my foe! He took his vorpal sword in hand."
CROW = "The crow was thirsty. It found a pitcher."
_RECORD = "the goal/motivation is deliberately UNDETERMINED"


def _real_son(ag):
    for n in ag.s.nodes("SmEntity"):
        at = ag.s.node(n)["attrs"]
        if at.get("name") == "son" and not at.get("nested"):
            return n
    return None


# --------------------------------------------------------------------------- #
#  JABBERWOCKY — BOTH stances.
# --------------------------------------------------------------------------- #
def test_jabberwocky_detached_stance_unchanged_held_open():
    """DETACHED — the reader's OWN verdict: danger UNDETERMINED, held open (task
    101, byte-identical). No goal minted for the son; OpenGoal + Ambiguity record
    the withholding."""
    ag = _fresh()
    r = ig.read_and_infer(ag, JABBERWOCKY)
    assert all(not g.get("minted") for g in r["goal"])
    assert r["situation_model"].get("son", {}).get("goal") is None
    assert ctom.character_goal(ag, "son") is None          # real son: no goal
    assert len(r["warning"]) == 1
    assert r["warning"][0]["held_open"] is True and r["warning"][0]["licensed"] is False
    assert len(ag.s.nodes("OpenGoal")) == 1 and len(ag.s.nodes("Ambiguity")) == 1
    assert ag.s.node(ag.s.nodes("OpenGoal")[0])["attrs"]["record"] == _RECORD


def test_jabberwocky_embedded_child_stance_licensed_within_child_world():
    """EMBEDDED-CHILD — the child's belief-world: father TRUSTED -> the warning
    LICENSES 'Jabberwock is dangerous' -> the quest to slay it is LICENSED within
    the child's world. Read back via character_tom's UNCHANGED belief-world
    query."""
    ag = _fresh()
    r = ig.read_and_infer(ag, JABBERWOCKY)

    emb = r["embedded"]
    assert len(emb) == 1
    e = emb[0]
    assert e["embedded"] is True and e["trusted"] is True
    assert e["threat"] == "jabberwock"            # read off the text, graph data
    assert e["belief_holder"] == "son"
    assert e["remedy"] == "slay"                  # from the WarningLexicon seed, not a literal
    assert e["licensed_within_world"] is True

    # the child's NESTED belief-world (character_tom idiom) holds the licensed danger.
    bw = ctom.character_belief_world(ag, "son")
    assert "jabberwock" in bw
    assert bw["jabberwock"]["danger"] == 1
    assert bw["jabberwock"]["licensed_within_world"] == 1
    assert bw["jabberwock"]["correct_within_world"] == 1   # the child's inference is CORRECT given its model

    # the `trusts` relation is graph-resident: the CHILD trusts the SOURCE.
    son = _real_son(ag)
    assert son is not None
    trusted_sources = ag.s.neighbours(son, "trusts")
    assert len(trusted_sources) == 1
    assert ag.s.node(trusted_sources[0])["attrs"]["role"] == "warner"


def test_stance_relative_same_warning_two_verdicts():
    """THE PROOF: the SAME warning is UNLICENSED detached AND LICENSED embedded —
    one warning, two verdicts, decided by WHOSE belief-world frames the read."""
    ag = _fresh()
    r = ig.read_and_infer(ag, JABBERWOCKY)
    # detached: unlicensed (held open).
    assert r["warning"][0]["licensed"] is False and r["warning"][0]["held_open"] is True
    # embedded: licensed (within the child's world).
    assert r["embedded"][0]["embedded"] is True and r["embedded"][0]["licensed_within_world"] is True
    # SAME warning verb + threat underlie both verdicts.
    assert r["warning"][0]["gap"]["verb"] == "beware" == r["embedded"][0]["gap"]["verb"]
    assert r["warning"][0]["gap"]["threat"] == "jabberwock" == r["embedded"][0]["threat"]


# --------------------------------------------------------------------------- #
#  DECOUPLING — model the child's belief WITHOUT holding it; boundary maintained.
# --------------------------------------------------------------------------- #
def test_reader_models_child_belief_without_holding_it_boundary_maintained():
    ag = _fresh()
    ig.read_and_infer(ag, JABBERWOCKY)
    rr.model_reader_response(ag)
    dec = rr.model_decoupled_reading(ag)
    assert len(dec) == 1

    # the reader MODELS that the child believes the danger ...
    assert rr.reader_models_child_believes_danger(ag) is True
    # ... but does NOT HOLD the danger itself: its own belief-world has no danger.
    assert rr.reader_holds_danger(ag) is False
    assert rr.reader_asserts_heroic_quest(ag) is False

    # the two are DISTINCT and the boundary is MAINTAINED — the danger-belief is
    # in the child's nested belief_world ONLY, indexed to the child.
    danger_nodes = [ag.s.node(n)["attrs"] for n in ag.s.nodes("SmEntity")
                    if ag.s.node(n)["attrs"].get("danger") == 1]
    assert len(danger_nodes) == 1
    assert danger_nodes[0]["nested"] == 1 and danger_nodes[0]["belief_holder"] == "son"

    dr = rr.decoupled_readings(ag)[0]
    assert dr["models_child_believes_danger"] == 1
    assert dr["reader_holds_danger"] == 0
    assert dr["boundary_maintained"] == 1 and dr["immersion"] == 0
    assert dr["reader_own_verdict"] == _RECORD           # the reader's own verdict stays detached


def test_decoupled_reading_is_idempotent():
    ag = _fresh()
    ig.read_and_infer(ag, JABBERWOCKY)
    first = rr.model_decoupled_reading(ag)
    second = rr.model_decoupled_reading(ag)
    assert len(first) == 1 and second == []
    assert len(ag.s.nodes("DecoupledReading")) == 1


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE — trust is the signal: an UNTRUSTED source licenses nothing.
# --------------------------------------------------------------------------- #
def test_untrusted_source_does_not_license_even_embedded():
    ag = _fresh()
    r = ig.read_and_infer(ag, UNTRUSTED)
    # still held open detached (unchanged).
    assert len(r["warning"]) == 1 and r["warning"][0]["held_open"] is True
    # but NO embedded license: the source is not trusted.
    assert len(r["embedded"]) == 1
    assert r["embedded"][0]["embedded"] is False and r["embedded"][0]["trusted"] is False
    # nothing modeled: no child danger-belief, no decoupled reading.
    assert rr.reader_models_child_believes_danger(ag) is False
    assert rr.model_decoupled_reading(ag) == []
    assert len(ag.s.nodes("DecoupledReading")) == 0
    assert len(ag.s.nodes("WarningSource")) == 0


def test_trust_membership_is_a_lexicon_signal_not_a_hardcoded_check():
    ag = _fresh()
    ig.ensure_seeds(ag)
    assert ig.trust_membership(ag, "son")["trusted"] is True        # kin -> trusted source
    assert ig.trust_membership(ag, "child")["trusted"] is True
    assert ig.trust_membership(ag, "foe")["trusted"] is False       # adversarial -> untrusted
    assert ig.trust_membership(ag, "enemy")["trusted"] is False
    # a vocative outside the codebook is `unknown` -> conservatively NOT trusted.
    unk = ig.trust_membership(ag, "wanderer")
    assert unk["trusted"] is False and unk["polarity"] == "unknown"


# --------------------------------------------------------------------------- #
#  CROW — unchanged: a felt need is licensed regardless of stance.
# --------------------------------------------------------------------------- #
def test_crow_byte_identical_no_stance_divergence():
    ag = _fresh()
    r = ig.read_and_infer(ag, CROW)
    assert r["situation_model"]["crow"] == {"thirsty": 1, "goal": "drink"}
    assert r["warning"] == [] and r["embedded"] == []
    for t in ("OpenGoal", "Ambiguity", "DecoupledReading", "WarningSource"):
        assert len(ag.s.nodes(t)) == 0
    assert rr.reader_holds_danger(ag) is False
    assert rr.reader_models_child_believes_danger(ag) is False
    assert rr.model_decoupled_reading(ag) == []


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT — trust + stance are graph signals, no story literal.
# --------------------------------------------------------------------------- #
def _docstring_nodes(tree) -> set:
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                out.add(id(body[0].value))
    return out


def test_source_audit_no_story_literal_no_regex():
    banned = ("jabberwock", "vorpal", "bandersnatch", "beamish", "manxome")
    for fname in ("inference_generation.py", "reader_response.py"):
        src = open(os.path.join(ROOT, "domains", fname)).read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(a.name == "re" for a in node.names), "%s: import re" % fname
            if isinstance(node, ast.ImportFrom):
                assert node.module != "re", "%s: from re import" % fname
        assert "re.compile(" not in src and "re.search(" not in src and "re.match(" not in src
        docs = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
                low = node.value.lower()
                for b in banned:
                    assert b not in low, "%s: story literal %r in executed code" % (fname, b)
            if isinstance(node, ast.Name):
                for b in banned:
                    assert b not in node.id.lower(), "%s: story literal in identifier %r" % (fname, node.id)


def test_source_audit_trust_and_licensing_are_graph_signals():
    src = open(os.path.join(ROOT, "domains", "inference_generation.py")).read()
    # trust is read off the TrustLexicon codebook, not a hardcoded relation check.
    assert "TrustLexicon" in src
    assert '== "father"' not in src and "== 'father'" not in src
    # the licensed quest response is seed data (WarningLexicon.licensed_response),
    # never a Python 'slay' literal decision.
    assert "licensed_response" in src
    # the embedded belief is nested + indexed to the belief_holder (character_tom idiom).
    assert "belief_world" in src and "belief_holder" in src and "trusts" in src


def test_embedded_belief_is_graph_resident_nested_and_indexed():
    ag = _fresh()
    ig.read_and_infer(ag, JABBERWOCKY)
    rr.model_reader_response(ag)
    rr.model_decoupled_reading(ag)
    # every artefact is a graph NODE / edge, queryable — not a Python dict.
    assert ag.s.nodes("WarningSource") and ag.s.nodes("DecoupledReading")
    # the child's danger-belief is nested + indexed, never on the real son.
    son = _real_son(ag)
    assert ag.s.node(son)["attrs"].get("danger") is None       # real son holds NO danger
    bw = [ag.s.node(x)["attrs"] for x in ag.s.neighbours(son, "belief_world")]
    assert any(x.get("danger") == 1 and x.get("belief_holder") == "son" for x in bw)


# --------------------------------------------------------------------------- #
#  THE DRIVER SCRIPT runs clean.
# --------------------------------------------------------------------------- #
def test_driver_script_runs():
    import jabberwock_models_the_child as jmc
    assert jmc.main() == 0
