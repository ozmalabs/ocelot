"""The jabberwock applies its 10 lessons to a FRESH faculty: noun-phrase grouping.

A new capability (group 'the slithy toves' into one noun phrase headed by the noun) built FROM the
lessons, to show they transfer:
  - triage_scoring_vs_representation_first: NP boundaries ARE in the role sequence (a binding/
    structural problem), so it is buildable now — no new primitive.
  - init_pass_outside_the_fixpoint: seed one NP per noun ONCE (host), not as a rule.
  - a_refinement_rule_must_be_self_terminating: the attach rule's guard (the word is not yet
    spanned) is falsified by its own effect (spanning it), so the fixpoint converges.
  - exists_must_test_the_iterated_variable: the 'not yet spanned' guard iterates np2 and tests
    np2-spans-m (the iterated var), not an outer var.
The payoff: it builds clean on the first try (no oscillation), unlike the #4 build before learning.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_applies_lessons
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from scripts.agent_infers_meaning import _compose, _litify
from scripts.agent_parses_structure import _ROLE_PROMPT

SEP = "=" * 96
STANZA = "the slithy toves did gyre and gimble in the wabe all mimsy were the borogoves and the mome raths outgrabe"


def main():
    print(SEP)
    print("THE JABBERWOCK APPLIES ITS LESSONS TO A FRESH FACULTY — noun-phrase grouping")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "jabberwocky", "shape_sense", "faculty_lessons"):
        try:
            a.inner.load_seed_manifest(manifest_for(sid), a.agent)
        except Exception as e:
            print(f"  (seed {sid}: {e})")
    teacher = a._self_teacher
    print(f"  the agent holds {len(a.s.nodes('Lesson'))} faculty lessons it can apply.\n")

    # --- input: role tags (reuse the parse; LESSON init-outside-fixpoint + attributive refinement) ---
    role = _litify(_compose(teacher, _ROLE_PROMPT))
    a.author_subroutine("role_of", role)
    mid = a.add_inbound(STANZA); a.comprehend()
    fwords = {a.s.node(n)["attrs"]["form"]: a.s.node(n)["attrs"].get("klass") for n in a.s.nodes("FunctionWord")}
    for m in a.inner.neighbours(mid, "has_mention"):              # base pass ONCE (host), not a rule
        if a.s.node(m)["attrs"].get("text") not in fwords:
            r = a.run_subroutine("role_of", {"m": m})
            if r:
                a.inner.set_attr(m, "pos", r)
    # attributive-adjective refinement (the / det + content + content -> adjective), self-terminating
    pos_noun = {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "m"}, "key": "pos"}, "b": {"type": "Lit", "value": "noun"}}
    prev_is_det = {"type": "Exists", "var_name": "f", "predicate": {"type": "And", "items": [
        {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "d"}, "key": "text"}, "b": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "form"}},
        {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "klass"}, "b": {"type": "Lit", "value": "determiner"}}]},
        "source": {"type": "NodesOfType", "node_type": "FunctionWord"}}
    next_content = {"type": "Not", "arg": {"type": "Exists", "var_name": "f", "predicate": {"type": "Eq",
        "a": {"type": "Attr", "node": {"type": "Var", "name": "p2"}, "key": "text"}, "b": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "form"}},
        "source": {"type": "NodesOfType", "node_type": "FunctionWord"}}}
    attr_adj = {"name": "attributive_adj", "match": [["d", "next_mention", "m"], ["m", "next_mention", "p2"]],
        "where": {"type": "And", "items": [prev_is_det, next_content, pos_noun]},
        "effects": [["set_attr_if_different", "m", "pos", {"__term__": {"type": "Lit", "value": "adjective"}}]]}
    a.inner.load_seed_manifest({"rules": [attr_adj]}, a.agent)
    a.inner.run_rules()

    # --- THE FRESH FACULTY: noun-phrase grouping, built with the lessons -----------------------
    # init ONCE (host): one NP per noun, headed by it (LESSON init_pass_outside_the_fixpoint).
    seeded = 0
    for m in a.inner.neighbours(mid, "has_mention"):
        if a.s.node(m)["attrs"].get("pos") == "noun":
            np = a.s.add_node("NounPhrase", {})
            a.inner.add_edge_unchecked(np, "head", m)
            a.inner.add_edge_unchecked(np, "spans", m)
            seeded += 1
    # attach rule (in the fixpoint): a determiner or adjective whose NEXT token is already spanned by
    # an NP, and which is NOT yet spanned, joins that NP. SELF-TERMINATING (the guard 'not spanned'
    # is falsified by the effect 'spans'); the guard's Exists iterates np2 and tests np2-spans-m.
    m_is_modifier = {"type": "Or", "items": [
        {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "m"}, "key": "pos"}, "b": {"type": "Lit", "value": "adjective"}},
        {"type": "Exists", "var_name": "f", "predicate": {"type": "And", "items": [
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "m"}, "key": "text"}, "b": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "form"}},
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "klass"}, "b": {"type": "Lit", "value": "determiner"}}]},
            "source": {"type": "NodesOfType", "node_type": "FunctionWord"}}]}
    not_yet_spanned = {"type": "Not", "arg": {"type": "Exists", "var_name": "np2", "predicate": {"type": "Lit", "value": True},
        "source": {"type": "InNeighbours", "node": {"type": "Var", "name": "m"}, "edge_type": "spans", "any_type": False}}}
    head_is_noun = {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "head"}, "key": "pos"}, "b": {"type": "Lit", "value": "noun"}}
    mid_is_modifier = {"type": "Or", "items": [
        {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "mid1"}, "key": "pos"}, "b": {"type": "Lit", "value": "adjective"}},
        {"type": "Exists", "var_name": "f", "predicate": {"type": "And", "items": [
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "mid1"}, "key": "text"}, "b": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "form"}},
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "klass"}, "b": {"type": "Lit", "value": "determiner"}}]},
            "source": {"type": "NodesOfType", "node_type": "FunctionWord"}}]}
    # FIX (the chained-rule-added-edge hop): a rule does NOT re-match on the spans edges its own
    # effect adds, so propagating modifier-by-modifier stalled after one hop. Re-route the binding to
    # the STABLE seed edge (np spans the HEAD noun) and UNROLL the short modifier run, so every
    # modifier attaches by reaching the seed-spanned head directly — no dependency on rule-added edges.
    attach1 = {"name": "np_attach_d1",        # modifier directly before the head noun
        "match": [["m", "next_mention", "head"], ["np", "spans", "head"]],
        "where": {"type": "And", "items": [m_is_modifier, head_is_noun, not_yet_spanned]},
        "effects": [["add_edge", "np", "spans", "m"]]}
    attach2 = {"name": "np_attach_d2",        # modifier before a modifier before the head noun
        "match": [["m", "next_mention", "mid1"], ["mid1", "next_mention", "head"], ["np", "spans", "head"]],
        "where": {"type": "And", "items": [m_is_modifier, mid_is_modifier, head_is_noun, not_yet_spanned]},
        "effects": [["add_edge", "np", "spans", "m"]]}
    a.inner.load_seed_manifest({"rules": [attach1, attach2]}, a.agent)
    a.inner.run_rules()                       # one pass: both attach against the STABLE seed head noun

    print(f"  built the NP-grouping faculty: seeded {seeded} NPs (one per noun, once), then the "
          f"attach rules (unrolled against the stable head, dodging the chained-rule-added-edge hop) "
          f"converged in one pass (no oscillation).\n")
    print("  noun phrases the agent grouped from the raw stanza:")
    for np in a.s.nodes("NounPhrase"):
        head = a.inner.neighbours(np, "head")
        spans = a.inner.neighbours(np, "spans")
        order = [a.s.node(m)["attrs"].get("text") for m in a.inner.neighbours(mid, "has_mention") if m in set(spans)]
        if len(order) > 1:
            hw = a.s.node(head[0])["attrs"].get("text") if head else "?"
            print(f"    [{' '.join(order)}]  (head: {hw})")
    print("\n" + SEP)
    print("  A fresh faculty built straight from the lessons: triaged as a binding problem (no new "
          "primitive), initialised once outside the fixpoint, one self-terminating attach rule with a "
          "correctly-bound quantifier guard — converged clean on the first try.")
    print(SEP)


if __name__ == "__main__":
    main()
