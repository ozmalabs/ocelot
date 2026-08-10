"""test_comprehend_recognition — the GENERAL comprehension front end
(domains/comprehend_text.py) now reads BY RECOGNITION, all the way down to the
word, with NO regex and NO whitespace-as-delimiter.

THE PRINCIPLE (non-negotiable): understanding text is COGNITION, not I/O. The
only I/O is the raw characters; WORD boundaries EMERGE by recognising the char
stream against the agent's lexicon (the same segmentation-by-recognition the
meta-layer's instruction comprehension uses, `domains/instruction_reading.py`);
and a token-sequence intent (a self-identity question) is an In/Eq/And graph
Term the Rust evaluator runs over recognised Word nodes — not a regex.

These gates are DISCRIMINATIVE (donkey=0): a whitespace `.split()` tokeniser
mis-tokenises the mis-spaced input and the graph shape then fails to fire, so a
no-op / regex implementation cannot pass them.
"""
from __future__ import annotations

import ast
import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import comprehend_text as ct

_SRC = "domains/comprehend_text.py"


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


# ---------------------------------------------------------------------------
# AST-AUDIT CLEAN (the headline) — no `import re`, no `re.`, no bare `.split()`
# tokeniser anywhere in the comprehension front end.
# ---------------------------------------------------------------------------

def test_ast_audit_clean():
    tree = ast.parse(open(_SRC).read())
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name == "re":
                    bad.append(f"import re @ line {node.lineno}")
        if isinstance(node, ast.ImportFrom) and node.module == "re":
            bad.append(f"from re import @ line {node.lineno}")
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id == "re"):
            bad.append(f"re.{node.attr} @ line {node.lineno}")
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "split"):
            bad.append(f".split() tokeniser @ line {node.lineno}")
    print(f"\nAST-AUDIT ({_SRC}): {'CLEAN' if not bad else bad}")
    assert not bad, bad


# ---------------------------------------------------------------------------
# RECOGNITION ROBUSTNESS — a mis-spaced input still comprehends to the SAME
# kind/intent as the well-spaced version; a whitespace baseline would mis-
# tokenise it and the shape would not fire.
# ---------------------------------------------------------------------------

def test_recognition_robustness_same_verdict(agent):
    spaced = ct.comprehend_text(agent, "what are you")
    misspaced = ct.comprehend_text(agent, "what areyou")     # missing space are|you
    print("\nRECOGNITION ROBUSTNESS")
    print(f"  'what are you'  -> kind={spaced.kind} meta={spaced.dispatch.get('meta_target')}")
    print(f"  'what areyou'   -> kind={misspaced.kind} meta={misspaced.dispatch.get('meta_target')}")
    print(f"  recognition('what areyou') = {ct._recognise_words(agent, 'what areyou')}")
    print(f"  whitespace .split('what areyou') = {'what areyou'.split()}  (mis-tokenised)")
    assert spaced.kind == misspaced.kind == "question"
    assert (spaced.dispatch.get("meta_target")
            == misspaced.dispatch.get("meta_target") == "self_identity")
    # recognition RECOVERS the true words; a whitespace split would NOT.
    assert ct._recognise_words(agent, "what areyou") == ["what", "are", "you"]
    assert "what areyou".split() == ["what", "areyou"]        # w1 != "are" -> shape fails


def test_recognition_robustness_is_discriminative(agent):
    # DONKEY: had comprehension used the whitespace split, w1 would be "areyou",
    # which is NOT in {are,art}, so _match_self_identity would return False.
    assert ct._match_self_identity(["what", "are", "you"]) is True
    assert ct._match_self_identity(["what", "areyou"]) is False    # the split reading


# ---------------------------------------------------------------------------
# QUESTION-SHAPE GRAPH-NATIVE — the self-identity shapes are recognised, and the
# match is the graph In/Eq/And path over Word nodes (not a regex).
# ---------------------------------------------------------------------------

_SELF_ID = ["what are you", "who are you", "what kind of thing are you",
            "what sort of manner are you"]


@pytest.mark.parametrize("text", _SELF_ID)
def test_self_identity_shapes_recognised(agent, text):
    comp = ct.comprehend_text(agent, text)
    assert comp.kind == "question" and comp.reflexive is True
    assert comp.dispatch.get("meta_target") == "self_identity"


def test_question_shape_is_the_graph_in_eq_and_path(agent):
    # the shape is evaluated as an In/Eq/And Term by the Rust evaluator over
    # scratch Word nodes carrying the recognised `text` attr.
    s, nodes = ct._scratch_words(["what", "are", "you"])
    assert s is not None, "native substrate required for the graph shape match"
    p1 = ct._And([ct._In("w0", ct._WHO_WHAT), ct._In("w1", ct._ARE_ART),
                  ct._In("w2", ct._YOU_THOU)])
    hit = bool(s.evaluate(p1, {"w0": nodes[0], "w1": nodes[1], "w2": nodes[2]}))
    print("\nQUESTION-SHAPE GRAPH-NATIVE")
    print(f"  In/And term over Word{{what,are,you}} = {hit}")
    assert hit is True
    # a non-matching triple is False -> a genuine graph decision, not a constant.
    s2, n2 = ct._scratch_words(["what", "shape", "you"])
    miss = bool(s2.evaluate(p1, {"w0": n2[0], "w1": n2[1], "w2": n2[2]}))
    print(f"  In/And term over Word{{what,shape,you}} = {miss}")
    assert miss is False
    # the kind-shape uses Eq(what)+In(kind_nouns)+Eq(of):
    s3, n3 = ct._scratch_words(["what", "kind", "of", "thing", "are", "you"])
    head = ct._And([ct._Eq("w0", "what"), ct._In("w1", ct._KIND_NOUNS),
                    ct._Eq("w2", "of")])
    khit = bool(s3.evaluate(head, {"w0": n3[0], "w1": n3[1], "w2": n3[2]}))
    print(f"  Eq/In/And head over Word{{what,kind,of}} = {khit}")
    assert khit is True


# ---------------------------------------------------------------------------
# OUTPUT-CONTRACT STABLE — the {kind, intent, dispatch, gaps} verdicts the
# callers rely on are unchanged, now produced by recognition + graph matches.
# ---------------------------------------------------------------------------

def test_output_contract_stable(agent):
    # table fast-path
    c = ct.comprehend_text(agent, "How are you organised?")
    assert c.fastpath is True and c.dispatch["path"] == "table"
    # imperative
    c = ct.comprehend_text(agent, "look left")
    assert c.kind == "instruction" and c.dispatch["predicate"] == "look"
    # declarative
    c = ct.comprehend_text(agent, "The rule hop_descend_gradient modifies gravity.")
    assert c.kind == "statement" and c.dispatch["path"] == "statement"
    # satisfiable (leading enumerate verb over held data)
    c = ct.comprehend_text(agent, "Name one of your rules.")
    assert c.dispatch["path"] == "satisfiable" and c.dispatch["target"] == "rules"
    # politeness strip by recognition + self-identity shape
    c = ct.comprehend_text(agent, "Pray, tell me plainly: what are you?")
    assert c.dispatch.get("meta_target") == "self_identity"
    # honest self-process floor still reached
    c = ct.comprehend_text(agent, "How do you dream?")
    assert c.dispatch.get("path") == "honest_self"


def test_politeness_strip_is_recognition_based(agent):
    # the leading marker is peeled by the FIRST RECOGNISED WORD, not a regex.
    assert ct._strip_politeness(agent, "Pray, tell me the time") == "tell me the time"
    assert ct._strip_politeness(agent, "kindly open the door") == "open the door"
    # nothing to strip -> unchanged
    assert ct._strip_politeness(agent, "open the door") == "open the door"
