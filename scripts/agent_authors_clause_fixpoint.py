"""Author fix #4: structure is a FIXPOINT — propagate roles as RULES, not one query Term.

Lesson structure_is_a_fixpoint. role_of (step 2) read only immediate neighbours, so a coordinated
verb (gimble, joined to gyre by 'and') inherited the wrong class. The fix the jabberwock learned:
make role assignment a fixpoint over the clause. Two rules, run to a fixed point:
  base_role: every content word gets a base pos from sentence-shape (its role_of Term).
  conj_inherit: a content word whose previous token is a conjunction COPIES the pos of the
                conjunct before that conjunction (gimble <- and <- gyre = verb).
Run together, run_rules reaches the fixpoint; gimble flips noun->verb.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_authors_clause_fixpoint
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

SEP = "=" * 92
STANZA = ("the slithy toves did gyre and gimble in the wabe all mimsy were the borogoves "
          "and the mome raths outgrabe")
EXPECT = {"slithy": "adjective", "toves": "noun", "gyre": "verb", "gimble": "verb", "wabe": "noun",
          "mimsy": "adjective", "borogoves": "noun", "mome": "adjective", "raths": "noun",
          "outgrabe": "verb"}


def main():
    print(SEP)
    print("AUTHOR FIX #4 — role as a FIXPOINT over the clause (propagating rules, not one Term)")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "jabberwocky", "shape_sense"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)
    teacher = a._self_teacher

    role = _compose(teacher, _ROLE_PROMPT)
    if not role:
        print("  (role_of failed to compose) — aborting"); print(SEP); return
    role = _litify(role)

    # base_role RULE: content word with no pos yet gets the base role_of (the step-2 Term, embedded
    # as a computed set_attr). set_attr_if_different keeps it idempotent under the fixpoint.
    is_content = {"type": "Not", "arg": {"type": "Exists", "var_name": "f",
        "predicate": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "m"}, "key": "text"},
                      "b": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "form"}},
        "source": {"type": "NodesOfType", "node_type": "FunctionWord"}}}
    base_rule = {"name": "base_role",
        "match": [["msg", "has_mention", "m"]],
        "where": is_content,
        "effects": [["set_attr_if_different", "m", "pos", {"__term__": role}]]}

    # conj_inherit RULE: tokens in reading order j, p, c (c.prev=p, p.prev=j). If p is a conjunction
    # and the conjunct j already has a pos, c COPIES it — propagating the verb across 'and'.
    p_is_conj = {"type": "Exists", "var_name": "f", "predicate": {"type": "And", "items": [
        {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "form"},
         "b": {"type": "Attr", "node": {"type": "Var", "name": "p"}, "key": "text"}},
        {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "klass"},
         "b": {"type": "Lit", "value": "conjunction"}}]},
        "source": {"type": "NodesOfType", "node_type": "FunctionWord"}}
    c_is_content = {"type": "Not", "arg": {"type": "Exists", "var_name": "f",
        "predicate": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "c"}, "key": "text"},
                      "b": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "form"}},
        "source": {"type": "NodesOfType", "node_type": "FunctionWord"}}}
    conj_rule = {"name": "conj_inherit",
        "match": [["c", "prev_mention", "p"], ["p", "prev_mention", "j"]],
        "where": {"type": "And", "items": [p_is_conj, c_is_content]},
        "effects": [["set_attr_if_different", "c", "pos",
                     {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "j"}, "key": "pos"}}]]}

    # predicate_adj: a content word whose NEXT token is an auxiliary/copula is a predicate ADJECTIVE
    # ('all mimsy were ...' -> mimsy). predicate_verb: a clause-final content word preceded by a noun,
    # still tagged noun, is the clause's predicate VERB ('the mome raths outgrabe' -> outgrabe).
    def _next_is_klass(nextvar, klass):
        return {"type": "Exists", "var_name": "f", "predicate": {"type": "And", "items": [
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "form"},
             "b": {"type": "Attr", "node": {"type": "Var", "name": nextvar}, "key": "text"}},
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "klass"},
             "b": {"type": "Lit", "value": klass}}]},
            "source": {"type": "NodesOfType", "node_type": "FunctionWord"}}
    pos_is = lambda v, val: {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": v}, "key": "pos"}, "b": {"type": "Lit", "value": val}}
    # predicate adjective: content word before an auxiliary/copula ('all mimsy were' -> mimsy).
    pred_adj = {"name": "predicate_adj",
        "match": [["m", "next_mention", "p2"]],
        "where": {"type": "And", "items": [_next_is_klass("p2", "auxiliary"), pos_is("m", "noun")]},
        "effects": [["set_attr_if_different", "m", "pos", {"__term__": {"type": "Lit", "value": "adjective"}}]]}
    # attributive adjective: a (base-noun) content word whose PREV is a determiner and whose NEXT is
    # another content word is the modifier, not the head ('the slithy toves' -> slithy; the mome raths).
    prev_is_det = {"type": "Exists", "var_name": "f", "predicate": {"type": "And", "items": [
        {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "d"}, "key": "text"},
         "b": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "form"}},
        {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "klass"},
         "b": {"type": "Lit", "value": "determiner"}}]},
        "source": {"type": "NodesOfType", "node_type": "FunctionWord"}}
    next_is_content = {"type": "Not", "arg": {"type": "Exists", "var_name": "f",
        "predicate": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "p2"}, "key": "text"},
                      "b": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "form"}},
        "source": {"type": "NodesOfType", "node_type": "FunctionWord"}}}
    attr_adj = {"name": "attributive_adj",
        "match": [["d", "next_mention", "m"], ["m", "next_mention", "p2"]],
        "where": {"type": "And", "items": [prev_is_det, next_is_content, pos_is("m", "noun")]},
        "effects": [["set_attr_if_different", "m", "pos", {"__term__": {"type": "Lit", "value": "adjective"}}]]}
    pred_verb = {"name": "predicate_verb",
        "match": [["m", "prev_mention", "j"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "j"}, "key": "pos"}, "b": {"type": "Lit", "value": "noun"}},
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "m"}, "key": "pos"}, "b": {"type": "Lit", "value": "noun"}},
            {"type": "Not", "arg": {"type": "Exists", "var_name": "_n", "predicate": {"type": "Lit", "value": True},
                "source": {"type": "Neighbours", "node": {"type": "Var", "name": "m"}, "edge_type": "next_mention", "any_type": False}}}]},
        "effects": [["set_attr_if_different", "m", "pos", {"__term__": {"type": "Lit", "value": "verb"}}]]}

    # The base pass runs ONCE (host applies the agent's role_of Term), NOT as a rule inside the
    # fixpoint — a base rule that re-fires races the refinement rules (it flipped wabe/borogoves).
    # Only the guarded REFINEMENT rules go into the fixpoint; each fires once on its own case.
    _ = base_rule  # (kept for reference; not installed)
    a.author_subroutine("role_of", role, purpose="base grammatical role from sentence-shape")
    mid = a.add_inbound(STANZA)
    a.comprehend()
    fwords = {a.s.node(n)["attrs"]["form"] for n in a.s.nodes("FunctionWord")}
    for m in a.inner.neighbours(mid, "has_mention"):
        if a.s.node(m)["attrs"].get("text") in fwords:
            continue
        r = a.run_subroutine("role_of", {"m": m})
        if r:
            a.inner.set_attr(m, "pos", r)
    a.inner.load_seed_manifest({"rules": [conj_rule, attr_adj, pred_adj, pred_verb]}, a.agent)
    print("  base pass applied once (host); installed guarded refinement rules "
          "(conj_inherit + predicate_adj/verb)\n")
    a.inner.run_rules()                          # fixpoint over the REFINEMENT rules only
    fwords = {a.s.node(n)["attrs"]["form"] for n in a.s.nodes("FunctionWord")}
    correct = total = 0
    for m in a.inner.neighbours(mid, "has_mention"):
        w = a.s.node(m)["attrs"].get("text")
        if w in fwords or w not in EXPECT:
            continue
        pos = a.s.node(m)["attrs"].get("pos")
        total += 1; ok = (pos == EXPECT[w]); correct += ok
        mark = "OK" if ok else f"(expected {EXPECT[w]})"
        flag = "  <- fixed by conj_inherit" if w == "gimble" and ok else ""
        print(f"  {w:11} -> {str(pos):10} {mark}{flag}")
    print(f"\n  {correct}/{total} correct (was 7/10; the fixpoint propagates the verb across 'and').")
    print("\n" + SEP)
    print("  Structure authored as a FIXPOINT: base roles set, then the conjunction rule propagates "
          "the conjunct's role across 'and' — gimble inherits gyre's verb. Rules to a fixed point, "
          "not one query Term. (outgrabe/mimsy still need the predicate-at-clause-end rule.)")
    print(SEP)


if __name__ == "__main__":
    main()
