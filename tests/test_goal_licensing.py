"""LICENSING AT THE GOAL LEVEL + the reader-response ToM — the Jabberwocky
correction.

The reader NOT inferring the son's goal is CORRECT: the father's 'Beware the
Jabberwock, my son!' is an inherited, unjustified warning; the son is in no
need-state; the danger is never established. Collapsing it into a heroic quest
is an UNLICENSED collapse. This gate pins:

  * JABBERWOCKY — the son's goal is HELD OPEN (NO fabricated goal; an OpenGoal
    + Ambiguity node recording 'the goal/motivation is deliberately
    UNDETERMINED'); the reader-response notes 'most readers would impose a
    heroic-quest reading; the ambiguity is the point'.
  * AESOP CROW — the goal is STILL inferred (thirst -> drink is LICENSED — a
    felt need is present); crow byte-identical to its pre-change baseline.
  * DISCRIMINATIVE — the SAME threat: a declarative fear-state LICENSES a goal
    (escape); an inherited imperative warning HOLDS it open. The framing, not
    the monster, decides.
  * GRAPH-NATIVE — the licensing check is over the graph (need-state present?
    goal warranted?), never a hardcoded 'jabberwock'/verse rule; the Ambiguity
    node + the modeled default reading are graph-resident; no `import re`;
    donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_goal_licensing.py -p no:randomly -q
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
CROW = "The crow was thirsty. It found a pitcher."
FEAR = "The son was afraid of the Jabberwock."
_RECORD = "the goal/motivation is deliberately UNDETERMINED"
_NOTE = "most readers would impose a heroic-quest reading; the ambiguity is the point"


# --------------------------------------------------------------------------- #
#  JABBERWOCKY — the son's goal is HELD OPEN, nothing fabricated.
# --------------------------------------------------------------------------- #
def test_jabberwocky_goal_is_held_open_no_fabricated_goal():
    ag = _fresh()
    r = ig.read_and_infer(ag, JABBERWOCKY)

    # NO goal was minted for the son (no need-state to license one).
    assert all(not g.get("minted") for g in r["goal"])
    assert r["situation_model"].get("son", {}).get("goal") is None
    # character_tom's own query agrees: the son has no goal.
    assert ctom.character_goal(ag, "son") is None

    # the warning WAS detected and HELD OPEN (not silently ignored).
    assert len(r["warning"]) == 1
    w = r["warning"][0]
    assert w["held_open"] is True and w["licensed"] is False
    assert w["gap"]["verb"] == "beware"
    assert w["gap"]["threat"] == "jabberwock"        # read off the text, graph data
    assert w["record"] == _RECORD


def test_jabberwocky_mints_opengoal_and_ambiguity_recording_the_withholding():
    ag = _fresh()
    ig.read_and_infer(ag, JABBERWOCKY)

    open_goals = [ag.s.node(n)["attrs"] for n in ag.s.nodes("OpenGoal")]
    ambiguities = [ag.s.node(n)["attrs"] for n in ag.s.nodes("Ambiguity")]
    assert len(open_goals) == 1
    assert len(ambiguities) == 1
    # the graph RECORDS the withholding itself, verbatim.
    assert open_goals[0]["record"] == _RECORD
    assert open_goals[0]["held_open"] == 1 and open_goals[0]["licensed"] == 0
    assert ambiguities[0]["record"] == _RECORD
    assert ambiguities[0]["about"] == "goal"


def test_jabberwocky_reader_response_models_the_default_reading_without_asserting_it():
    ag = _fresh()
    ig.read_and_infer(ag, JABBERWOCKY)
    resp = rr.model_reader_response(ag)
    assert len(resp) == 1

    # the reader's OWN verdict: the ambiguity is the meaning (held open).
    qs = rr.open_questions(ag)
    assert len(qs) == 1
    assert qs[0]["question"] == "was the quest warranted?"
    assert qs[0]["theme"] == "the undetermined danger"
    assert qs[0]["asserted_by_reader"] == 0

    # the DEFAULT reading is MODELLED as another's, flagged, never asserted.
    modeled = rr.modeled_default_readings(ag)
    assert len(modeled) == 1
    m = modeled[0]
    assert m["reading"] == "heroic quest"
    assert m["note"] == _NOTE                          # verbatim
    assert m["most_impose"] == 1
    assert m["asserted_by_reader"] == 0
    # the reader ITSELF never asserts the heroic quest.
    assert rr.reader_asserts_heroic_quest(ag) is False

    # the modeled reading is edged from a modeled OTHER mind (belief-world idiom),
    # distinct from the agent's own held-open OpenGoal verdict.
    readers = ag.s.nodes("ReaderModel")
    assert len(readers) == 1
    bw = [ag.s.node(x)["attrs"].get("reading") for x in ag.s.neighbours(readers[0], "belief_world")]
    assert "heroic quest" in bw


def test_reader_response_is_idempotent():
    ag = _fresh()
    ig.read_and_infer(ag, JABBERWOCKY)
    first = rr.model_reader_response(ag)
    second = rr.model_reader_response(ag)
    assert len(first) == 1 and second == []
    assert len(ag.s.nodes("OpenQuestion")) == 1
    assert len(ag.s.nodes("ModeledReading")) == 1


# --------------------------------------------------------------------------- #
#  AESOP CROW — the goal is STILL inferred (LICENSED); crow byte-identical.
# --------------------------------------------------------------------------- #
def test_crow_goal_still_inferred_licensed():
    ag = _fresh()
    r = ig.read_and_infer(ag, CROW)
    hits = [g for g in r["goal"] if g["gap"]["entity"] == "crow" and g["minted"]]
    assert len(hits) == 1
    assert hits[0]["schema"] == "need_remedy_thirst"
    assert hits[0]["supplies"] == {"relation": "goal", "remedy": "drink"}
    assert r["situation_model"]["crow"].get("goal") == "drink"
    assert ctom.character_goal(ag, "crow") == "drink"


def test_crow_byte_identical_nothing_held_open():
    """The licensed crow path is UNTOUCHED: the crow's state slice is exactly
    the pre-change value (thirsty=1, goal='drink' — the pinned
    test_inference_generation.test_goal_from_state_thirst_crow values), no
    warning fires, and NO OpenGoal/Ambiguity/reader-response node is minted (the
    withholding machinery stays dormant on a licensed read)."""
    ag = _fresh()
    r = ig.read_and_infer(ag, CROW)
    assert r["situation_model"]["crow"] == {"thirsty": 1, "goal": "drink"}
    assert r["warning"] == []
    for t in ("OpenGoal", "Ambiguity", "OpenQuestion", "ModeledReading", "ReaderModel"):
        assert ag.s.nodes(t) == [] or len(ag.s.nodes(t)) == 0
    # the reader-response driver is a no-op on the licensed read.
    assert rr.model_reader_response(ag) == []


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE — the SAME threat: declarative fear LICENSES, imperative
#  warning HOLDS OPEN. The framing decides, not the monster.
# --------------------------------------------------------------------------- #
def test_discriminative_declarative_fear_licenses_imperative_warning_holds_open():
    # declarative 'the son was afraid' -> a felt need-state -> LICENSED -> escape.
    ag1 = _fresh()
    r1 = ig.read_and_infer(ag1, FEAR)
    fear_hits = [g for g in r1["goal"] if g["gap"]["entity"] == "son" and g["minted"]]
    assert len(fear_hits) == 1
    assert fear_hits[0]["schema"] == "need_remedy_danger"
    assert r1["situation_model"]["son"].get("goal") == "escape"
    assert r1["warning"] == []                          # no imperative -> nothing held open
    assert len(ag1.s.nodes("OpenGoal")) == 0

    # imperative 'Beware the Jabberwock' -> a directive, no state -> HELD OPEN.
    ag2 = _fresh()
    r2 = ig.read_and_infer(ag2, JABBERWOCKY)
    assert all(not g.get("minted") for g in r2["goal"])
    assert len(r2["warning"]) == 1 and r2["warning"][0]["held_open"] is True
    assert len(ag2.s.nodes("OpenGoal")) == 1

    # SAME threat token in both — the difference is the FRAMING, not the monster.
    assert "jabberwock" in FEAR.lower() and "jabberwock" in JABBERWOCKY.lower()


def test_combined_warning_plus_felt_need_licenses_not_held_open():
    """When the SAME text establishes BOTH a genuine felt need AND an imperative
    warning ('The son was afraid. Beware the Jabberwock!'), the felt need GROUNDS
    the warning -> LICENSED -> the goal is inferred and NOTHING is held open. The
    read-order robustness (a need-state already minted into a goal still counts
    as a governing need)."""
    ag = _fresh()
    r = ig.read_and_infer(ag, "The son was afraid. Beware the Jabberwock, my son!")
    assert r["situation_model"]["son"].get("goal") == "escape"    # felt need -> goal
    # a warning WAS detected but it is LICENSED (grounded) -> not held open.
    assert len(r["warning"]) == 1
    assert r["warning"][0]["licensed"] is True
    assert r["warning"][0]["held_open"] is False
    assert len(ag.s.nodes("OpenGoal")) == 0


def test_warning_membership_is_wordnet_join_not_a_hardcoded_list():
    """An UNSEEN caution imperative ('shun' is a seed form; a near synonym joins
    by WordNet path-similarity) is recognised without editing a Python list —
    the SAME join-by-adjacency mechanism COS/ATTITUDE use."""
    ag = _fresh()
    ig.ensure_seeds(ag)
    assert ig.warning_membership(ag, "beware")["warning"] is True     # seed member
    assert ig.warning_membership(ag, "shun")["warning"] is True       # seed member
    # a crow-fable action verb is NOT a warning (cleanly below threshold).
    for verb in ("drop", "pick", "reach", "find", "rise", "take"):
        assert ig.warning_membership(ag, verb)["warning"] is False


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT — no story literal, no regex, decode is graph-side.
# --------------------------------------------------------------------------- #
def _docstring_nodes(tree) -> set:
    """The id()s of every module/class/function docstring Constant — design
    prose that legitimately cites the poem, excluded from the story-literal
    scan (only EXECUTED code literals must be clean)."""
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
        # no `import re` / regex calls.
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(a.name == "re" for a in node.names), "%s: import re" % fname
            if isinstance(node, ast.ImportFrom):
                assert node.module != "re", "%s: from re import" % fname
        assert "re.compile(" not in src and "re.search(" not in src and "re.match(" not in src
        # the licensing/withholding decision is NEVER keyed on a story literal.
        # Docstrings (design prose that cites the poem) and comments are excluded;
        # only EXECUTED string literals + identifiers are scanned.
        docs = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
                low = node.value.lower()
                for b in banned:
                    assert b not in low, "%s: story literal %r in executed code" % (fname, b)
            if isinstance(node, ast.Name):
                for b in banned:
                    assert b not in node.id.lower(), "%s: story literal in identifier %r" % (fname, node.id)


def test_source_audit_licensing_is_a_graph_signal():
    src = open(os.path.join(ROOT, "domains", "inference_generation.py")).read()
    # the gate reads a graph provenance / need-state signal, not a verb literal:
    # no `if verb == "beware"` / `if need_attr == "afraid"` decides the mint.
    assert '== "beware"' not in src and "== 'beware'" not in src
    assert 'need_attr ==' not in src
    # the warning verb is recognised via the WarningLexicon codebook + WordNet
    # nearness (the SAME rc._wordnet_nearness signal), never a hardcoded list.
    assert "WarningLexicon" in src
    assert "rc._wordnet_nearness(" in src
    # the licensing gate consults the resident need-state model, graph-side.
    assert "_any_licensed_need_state" in src and "_goal_is_licensed" in src


def test_ambiguity_and_default_reading_are_graph_resident():
    ag = _fresh()
    ig.read_and_infer(ag, JABBERWOCKY)
    rr.model_reader_response(ag)
    # every artefact is a graph NODE, queryable — not a Python dict.
    assert ag.s.nodes("OpenGoal") and ag.s.nodes("Ambiguity")
    assert ag.s.nodes("OpenQuestion") and ag.s.nodes("ModeledReading")
    # the modeled default reading is graph-resident and flagged as others' (the
    # default-reading MODEL is real, not a stub string).
    m = ag.s.node(ag.s.nodes("ModeledReading")[0])["attrs"]
    assert m["most_impose"] == 1 and m["asserted_by_reader"] == 0
    assert m["reading"] == "heroic quest"


# --------------------------------------------------------------------------- #
#  THE SUMMIT SCRIPT runs clean.
# --------------------------------------------------------------------------- #
def test_summit_script_runs():
    import jabberwock_holds_open as jho
    assert jho.main() == 0
