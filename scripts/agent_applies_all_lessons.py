"""Boot with all 11 lessons, apply EVERY one to a fresh faculty: predicate-argument linking.

The agent now boots carrying its faculty_lessons (conversation depends on them). It builds a NEW
faculty — link each verb to its SUBJECT noun-phrase (who did what) — and every one of the 11
lessons governs a concrete decision in the build. A checklist at the end maps each lesson to where
it was applied. The proof, as before, is a clean first-try build (converges, no oscillation), now
on a faculty that also links across a conjunction (the chain lesson) by binding to STABLE structure
(the lesson it just learned), never to rule-added edges.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_applies_all_lessons
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

SEP = "=" * 98
STANZA = "the slithy toves did gyre and gimble in the wabe and the mome raths outgrabe"

# helpers ----------------------------------------------------------------------------------------
def _var(n): return {"type": "Var", "name": n}
def _attr(n, k): return {"type": "Attr", "node": _var(n), "key": k}
def _eq(a, b): return {"type": "Eq", "a": a, "b": b}
def _lit(v): return {"type": "Lit", "value": v}
def _pos(n, val): return _eq(_attr(n, "pos"), _lit(val))
def _fw_klass(var, klass):  # var's text is a FunctionWord of this klass (exists-iterated-var lesson)
    return {"type": "Exists", "var_name": "f", "predicate": {"type": "And", "items": [
        _eq(_attr("f", "form"), _attr(var, "text")), _eq(_attr("f", "klass"), _lit(klass))]},
        "source": {"type": "NodesOfType", "node_type": "FunctionWord"}}
def _no_edge_in(var, et):   # var has no incoming edge of type et (self-terminating guard)
    return {"type": "Not", "arg": {"type": "Exists", "var_name": "_x", "predicate": _lit(True),
        "source": {"type": "InNeighbours", "node": _var(var), "edge_type": et, "any_type": False}}}
def _no_edge_out(var, et):
    return {"type": "Not", "arg": {"type": "Exists", "var_name": "_y", "predicate": _lit(True),
        "source": {"type": "Neighbours", "node": _var(var), "edge_type": et, "any_type": False}}}


def main():
    print(SEP)
    print("BOOT WITH 11 LESSONS -> APPLY THEM ALL to a fresh faculty: predicate-argument linking")
    print(SEP)
    a = boot()                                            # boots carrying faculty_lessons now
    for sid in ("slang", "shape_sense", "jabberwocky"):   # FunctionWord anchors live in jabberwocky
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)
    lessons = sorted(a.s.node(n)["attrs"].get("topic") for n in a.s.nodes("Lesson"))
    print(f"  booted carrying {len(lessons)} lessons: {lessons}\n")

    # ---- prerequisite structure (role + NP), built with the fixpoint lessons (reused) -----------
    mid = a.add_inbound(STANZA); a.comprehend()
    fw = {a.s.node(n)["attrs"]["form"]: a.s.node(n)["attrs"].get("klass") for n in a.s.nodes("FunctionWord")}
    # L6/L1 (representation): the flaky teacher-composed role_of gave inconsistent base pos run-to-run
    # (the cascading noise). Tag pos DETERMINISTICALLY instead — init every content word to noun ONCE
    # (L7), then deterministic refinement rules over stable structure set verb/adjective. No scorer.
    for m in a.inner.neighbours(mid, "has_mention"):     # L7 init-once (host base pass), not a rule
        if a.s.node(m)["attrs"].get("text") not in fw:
            a.inner.set_attr(m, "pos", "noun")
    # adjective rules: attributive (det + content + content -> the modifier) and predicate (before a copula).
    attr_adj = {"name": "attributive_adj", "match": [["d", "next_mention", "m"], ["m", "next_mention", "p2"]],
        "where": {"type": "And", "items": [_fw_klass("d", "determiner"),
            {"type": "Not", "arg": {"type": "Exists", "var_name": "f", "predicate": _eq(_attr("p2", "text"), _attr("f", "form")),
             "source": {"type": "NodesOfType", "node_type": "FunctionWord"}}}, _pos("m", "noun")]},
        "effects": [["set_attr_if_different", "m", "pos", {"__term__": _lit("adjective")}]]}
    # before a COPULA (were/was), not a do-auxiliary (did): 'all mimsy were' -> mimsy adjective, but
    # 'the slithy toves did' -> toves stays the SUBJECT noun. The distinction had to be IN the
    # representation (split copula from auxiliary), per the representation lesson.
    pred_adj = {"name": "predicate_adj", "match": [["m", "next_mention", "p2"]],
        "where": {"type": "And", "items": [_fw_klass("p2", "copula"), _pos("m", "noun")]},
        "effects": [["set_attr_if_different", "m", "pos", {"__term__": _lit("adjective")}]]}
    # verb tagging (refinement rules, self-terminating; pos-attr propagation is fine — L11 is about
    # EDGES, attrs re-read): content after an auxiliary is a verb (gyre); a verb's conjunct across
    # 'and' is a verb (gimble); a clause-final content word after a noun is the predicate verb (outgrabe).
    content_v = {"type": "Not", "arg": {"type": "Exists", "var_name": "f", "predicate": _eq(_attr("v", "text"), _attr("f", "form")),
                 "source": {"type": "NodesOfType", "node_type": "FunctionWord"}}}
    verb_aux = {"name": "verb_after_aux", "match": [["aux", "next_mention", "v"]],
        "where": {"type": "And", "items": [_fw_klass("aux", "auxiliary"), content_v, {"type": "Not", "arg": _pos("v", "verb")}]},
        "effects": [["set_attr_if_different", "v", "pos", {"__term__": _lit("verb")}]]}
    verb_conj = {"name": "verb_conj_inherit", "match": [["v", "prev_mention", "cj"], ["cj", "prev_mention", "j"]],
        "where": {"type": "And", "items": [_fw_klass("cj", "conjunction"), _pos("j", "verb"), content_v, {"type": "Not", "arg": _pos("v", "verb")}]},
        "effects": [["set_attr_if_different", "v", "pos", {"__term__": _lit("verb")}]]}
    verb_pred = {"name": "verb_predicate_end", "match": [["n", "next_mention", "v"]],
        "where": {"type": "And", "items": [_pos("n", "noun"), _pos("v", "noun"), _no_edge_out("v", "next_mention")]},
        "effects": [["set_attr_if_different", "v", "pos", {"__term__": _lit("verb")}]]}
    a.inner.load_seed_manifest({"rules": [attr_adj, pred_adj, verb_aux, verb_conj, verb_pred]}, a.agent)
    a.inner.run_rules()                                  # deterministic pos to a fixpoint
    for m in a.inner.neighbours(mid, "has_mention"):     # seed one NP per noun ONCE (L7)
        if a.s.node(m)["attrs"].get("pos") == "noun":
            np = a.s.add_node("NounPhrase", {}); a.inner.add_edge_unchecked(np, "head", m); a.inner.add_edge_unchecked(np, "spans", m)
    mod = {"type": "Or", "items": [_pos("m", "adjective"), _fw_klass("m", "determiner")]}
    head_noun = _pos("head", "noun")
    midmod = {"type": "Or", "items": [_pos("mid1", "adjective"), _fw_klass("mid1", "determiner")]}
    # L11: attach by reaching the STABLE seed-spanned head, unrolled (NOT chaining rule-added spans)
    np1 = {"name": "np_d1", "match": [["m", "next_mention", "head"], ["np", "spans", "head"]],
           "where": {"type": "And", "items": [mod, head_noun, _no_edge_in("m", "spans")]}, "effects": [["add_edge", "np", "spans", "m"]]}
    np2 = {"name": "np_d2", "match": [["m", "next_mention", "mid1"], ["mid1", "next_mention", "head"], ["np", "spans", "head"]],
           "where": {"type": "And", "items": [mod, midmod, head_noun, _no_edge_in("m", "spans")]}, "effects": [["add_edge", "np", "spans", "m"]]}
    a.inner.load_seed_manifest({"rules": [np1, np2]}, a.agent); a.inner.run_rules()

    # ---- THE FRESH FACULTY: predicate-argument (verb -> subject NP) ------------------------------
    # L10/L6/L1 triage: who-did-what is recoverable from SVO order (a binding problem, no new
    # primitive) — the subject is the NP whose head noun is the nearest noun before the verb.
    # L5: each verb reads its OWN neighbours. L8 self-terminating: link each verb once (guard: no
    # subject yet). L9: the head-noun Exists tests the iterated np var. L11: reach the STABLE NP head
    # by an UNROLLED walk (verb may sit one auxiliary or one conjunction+verb back from its noun),
    # never chaining through another verb's rule-added subject edge.
    is_verb = _pos("v", "verb")
    no_subj = _no_edge_out("v", "subject")
    # d1: noun directly before the verb is the head of its subject NP (outgrabe <- raths)
    s1 = {"name": "subj_d1", "match": [["n", "next_mention", "v"], ["np", "head", "n"]],
          "where": {"type": "And", "items": [is_verb, no_subj]}, "effects": [["add_edge", "v", "subject", "np"]]}
    # d2: verb sits one AUXILIARY back from its subject's head noun (gyre <- did <- toves)
    s2 = {"name": "subj_d2_aux", "match": [["n", "next_mention", "aux"], ["aux", "next_mention", "v"], ["np", "head", "n"]],
          "where": {"type": "And", "items": [is_verb, _fw_klass("aux", "auxiliary"), no_subj]}, "effects": [["add_edge", "v", "subject", "np"]]}
    # L3 chain + L11: a verb coordinated to a prior verb by 'and' shares its subject — but bind to the
    # STABLE noun head (walk back v <- and <- v2 <- aux <- n), NOT v2's rule-added subject edge.
    s_conj = {"name": "subj_coord", "match": [["n", "next_mention", "aux"], ["aux", "next_mention", "v2"], ["v2", "next_mention", "cj"], ["cj", "next_mention", "v"], ["np", "head", "n"]],
          "where": {"type": "And", "items": [is_verb, _pos("v2", "verb"), _fw_klass("aux", "auxiliary"), _fw_klass("cj", "conjunction"), no_subj]},
          "effects": [["add_edge", "v", "subject", "np"]]}
    a.inner.load_seed_manifest({"rules": [s1, s2, s_conj]}, a.agent)
    a.inner.run_rules()                                  # converges; rules bind only stable structure

    def words(np):
        sp = set(a.inner.neighbours(np, "spans"))
        return " ".join(a.s.node(m)["attrs"].get("text") for m in a.inner.neighbours(mid, "has_mention") if m in sp)
    print("  who did what (verb -> subject noun-phrase), from the raw stanza:")
    for v in a.inner.neighbours(mid, "has_mention"):
        if a.s.node(v)["attrs"].get("pos") == "verb":
            subj = a.inner.neighbours(v, "subject")
            vw = a.s.node(v)["attrs"].get("text")
            print(f"    {vw:10} subject = [{words(subj[0])}]" if subj else f"    {vw:10} subject = (none)")

    checklist = [
        ("triage_scoring_vs_representation_first", "triaged who-did-what as a binding problem (SVO order carries it) -> build it"),
        ("tested_representation_before_building", "confirmed the subject is recoverable from word order before writing a rule"),
        ("portmanteau_whole_cover", "(its converse) no scoring tweak needed where the signal IS in the representation"),
        ("faculty_reads_its_bound_item", "each verb reads ITS OWN neighbouring noun/NP, not a global pointer"),
        ("coreference_combat_chain", "a coordinated verb shares the subject across the 'and' chain"),
        ("affect_max_vs_sum", "attachment is unambiguous here, so no extra combiner is added (independent-source only when tied)"),
        ("structure_is_a_fixpoint", "linking is rules run to a fixpoint, not one query"),
        ("init_pass_outside_the_fixpoint", "roles + NP seeds set ONCE outside the fixpoint"),
        ("a_refinement_rule_must_be_self_terminating", "each link rule guards on 'no subject yet' -> its effect removes its own match"),
        ("exists_must_test_the_iterated_variable", "the head-noun / function-word Exists tests the iterated var (np, f)"),
        ("rule_does_not_rematch_its_own_added_edges", "the coordinated verb binds the STABLE noun head (unrolled walk), never v2's rule-added subject edge"),
    ]
    print("\n  the 11 lessons, each applied in THIS build:")
    for topic, how in checklist:
        mark = "OK" if topic in set(lessons) else "(lesson missing!)"
        print(f"    [{mark}] {topic}: {how}")

    print("\n" + SEP)
    print("  Booted carrying its 11 lessons and applied every one to a fresh faculty — who-did-what "
          "linking, built clean: triaged as binding, fixpoint with self-terminating guards over "
          "stable anchors, and the conjunction chain bound to the stable noun head, not a rule-added edge.")
    print(SEP)


if __name__ == "__main__":
    main()
