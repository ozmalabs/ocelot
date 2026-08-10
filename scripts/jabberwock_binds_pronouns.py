"""jabberwock_binds_pronouns -- COREFERENCE WIRED INTO THE READING PATH.

Demo + honest report for domains/coref_entities.py (gated by tests/
test_coref_into_entities.py). The situation-model reader
(domains/situation_model_reader.py) mints SmEntity/SmEvent nodes from read
text but used to be coreference-BLIND: a pronoun argument minted its OWN
literal SmEntity ("he") instead of resolving to the protagonist it denotes
("john"), so a state change attributed to "he" landed on a throwaway node.

domains/reference_resolution.py already has a real resolver (Centering Theory
Cf/Cb, the Givenness Hierarchy, agreement filtering) for the CONVERSATION path,
but its antecedent RANKING is a Python `max()`/if-else picker over graph-
resident attrs -- NOT graph-native -- and its state shape (a conversational
`frame` dict + a ConversationWorld-specific `_concept_nodes` index) does not
transplant onto SmEntity / [rel, arg0, arg1] triples. coref_entities.py reuses
reference_resolution's DATA (`_CF_RANK`, `_PRONOUNS`) and documented algorithm,
but RE-EXPRESSES the antecedent choice as an `Argmax` Term-tree over the
resident SmEntity pool, evaluated natively (substrate.evaluate / Rust) -- the
same migration native_vote.py performed on a Python `Counter.most_common`
k-NN decision.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 \
     scripts/jabberwock_binds_pronouns.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import coref_entities as ce              # noqa: E402
from domains import reference_resolution as rr        # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def fresh():
    s, node = boot_core()
    return _Agent(s, node)


def hr(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def dump_resolutions(res):
    for r in res:
        print("  ", json.dumps(r, default=str))


def main():
    dl.warm_wordnet("en")

    # ----------------------------------------------------------------- #
    hr("GRAPH-NATIVE SOURCE AUDIT")
    # ----------------------------------------------------------------- #
    import inspect
    proc_src = inspect.getsource(rr.DiscourseStore.reference_resolution_procedure)
    print("reference_resolution.reference_resolution_procedure ranks survivors with:")
    for line in proc_src.splitlines():
        if "max(" in line or "cb_survivor is not None" in line:
            print("   PY-PICKER >>", line.strip())
    print()
    print("VERDICT: reference_resolution's antecedent ranking is a Python")
    print("max()/if-else over graph-resident attrs -- NOT graph-native.")
    print("Its frame-dict state shape is conversation-specific and does not")
    print("transplant onto SmEntity triples, so coref_entities.py imports its")
    print("DATA (_CF_RANK, _PRONOUNS) and RE-EXPRESSES the ranking as its own")
    print("Argmax Program:")
    term = ce.antecedent_argmax_term(ce._PRONOUNS["he"], None)
    print(json.dumps(term, indent=2))
    resolve_src = inspect.getsource(ce.resolve_pronoun)
    assert "max(" not in resolve_src and "sorted(" not in resolve_src
    print("\ncoref_entities.resolve_pronoun contains no max()/sorted() -- the")
    print("winner above is native.evaluate(term, {}) 's own return value.")

    # ----------------------------------------------------------------- #
    hr("HEADLINE -- 'John met Bill. He left the room.'")
    # ----------------------------------------------------------------- #
    ag = fresh()
    r = ce.read_into_situation_model(ag, "John met Bill. He left the room.")
    print("textbase:", json.dumps(r["textbase"], default=str))
    print("resolutions:")
    dump_resolutions(r["resolutions"])
    he = [x for x in r["resolutions"] if x["surface"] == "he"][0]
    print(f"\n'he' -> SmEntity {he['concept']!r} via {he['rule']} (margin={he['margin']:.3f})")
    print("situation_model['john'] =", json.dumps(r["situation_model"]["john"], default=str))
    assert he["resolved"] and he["concept"] == "john"
    assert "he" not in r["situation_model"]

    # ----------------------------------------------------------------- #
    hr("CROSS-SENTENCE -- named antecedent ('Mary ... She ...')")
    # ----------------------------------------------------------------- #
    ag2 = fresh()
    r2 = ce.read_into_situation_model(
        ag2, "The cup is fragile. Mary entered the kitchen. She dropped the cup.")
    print("textbase:", json.dumps(r2["textbase"], default=str))
    print("resolutions:")
    dump_resolutions(r2["resolutions"])
    print("situation_model['mary'] =", json.dumps(r2["situation_model"]["mary"], default=str))
    print("situation_model['cup']  =", json.dumps(r2["situation_model"]["cup"], default=str))
    assert r2["situation_model"]["mary"]["location"] == "kitchen"
    assert r2["situation_model"]["cup"]["broken"] == 1

    # ----------------------------------------------------------------- #
    hr("CROSS-SENTENCE -- repeated pronoun, no named antecedent ('She ... She ...')")
    # ----------------------------------------------------------------- #
    ag3 = fresh()
    r3 = ce.read_into_situation_model(
        ag3, "The cup is fragile. She entered the kitchen. She dropped the cup.")
    print("textbase:", json.dumps(r3["textbase"], default=str))
    print("resolutions:")
    dump_resolutions(r3["resolutions"])
    she = [x for x in r3["resolutions"] if x["surface"] == "she"]
    print(f"\n1st 'she': resolved={she[0]['resolved']} ({she[0].get('reason')})")
    print(f"2nd 'she': resolved={she[1]['resolved']} -> {she[1].get('concept')}"
          f" (margin={she[1].get('margin')})")
    print("Both mentions converge on ONE persistent SmEntity 'she':",
          json.dumps(r3["situation_model"]["she"], default=str))
    assert not she[0]["resolved"] and she[1]["resolved"] and she[1]["concept"] == "she"

    # ----------------------------------------------------------------- #
    hr("HELD-OPEN / DISCRIMINATIVE -- a genuine tie")
    # ----------------------------------------------------------------- #
    ag4 = fresh()
    ce._touch_entity(ag4, "John arrived.", "john", "agent", 1)
    ce._touch_entity(ag4, "Bill arrived.", "bill", "agent", 1)
    rec = ce.resolve_pronoun(ag4, "he", "He left.", 2, ce._current_cb(ag4))
    print(json.dumps(rec, default=str, indent=2))
    assert not rec["resolved"] and rec["margin"] == 0.0
    print("\nContrast: the HEADLINE's 'he' (margin=1.0, role-rank distinguishes")
    print("agent from patient) IS bound; a TRUE tie (margin=0.0) is HELD OPEN --")
    print("the same Argmax Program, a different verdict, gated by the RI-Val margin.")

    # ----------------------------------------------------------------- #
    hr("FEATURAL FILTER -- 'it' never binds a grounded person")
    # ----------------------------------------------------------------- #
    ag5 = fresh()
    ce._touch_entity(ag5, "The woman arrived.", "woman", "agent", 1)
    rec5 = ce.resolve_pronoun(ag5, "it", "It left.", 2, ce._current_cb(ag5))
    print("only-candidate-is-a-person:", json.dumps(rec5, default=str))
    assert not rec5["resolved"]

    ag6 = fresh()
    r6 = ce.read_into_situation_model(
        ag6, "The woman entered the kitchen. It left the room.")
    it = [x for x in r6["resolutions"] if x["surface"] == "it"][0]
    print("person-and-object-both-resident:", json.dumps(it, default=str))
    assert it["resolved"] and it["concept"] == "kitchen" and it["concept"] != "woman"

    # ----------------------------------------------------------------- #
    hr("FEATURAL FILTER -- 'they' requires a plural antecedent")
    # ----------------------------------------------------------------- #
    ag7 = fresh()
    r7 = ce.read_into_situation_model(
        ag7, "The woman entered the kitchen. They left the room.")
    they_singular = [x for x in r7["resolutions"] if x["surface"] == "they"][0]
    print("singular referent:", json.dumps(they_singular, default=str))
    assert not they_singular["resolved"]

    ag8 = fresh()
    r8 = ce.read_into_situation_model(
        ag8, "The children entered the kitchen. They left the room.")
    they_plural = [x for x in r8["resolutions"] if x["surface"] == "they"][0]
    print("plural referent (children -- WordNet morphy children->child):",
          json.dumps(they_plural, default=str))
    assert they_plural["resolved"] and they_plural["concept"] == "children"

    # ----------------------------------------------------------------- #
    hr("ALL GATES PASSED")
    # ----------------------------------------------------------------- #
    print("See tests/test_coref_into_entities.py for the pytest-gated version")
    print("and CLAUDE.md / domains/coref_entities.py's module docstring for the")
    print("full honest-coverage report.")


if __name__ == "__main__":
    main()
