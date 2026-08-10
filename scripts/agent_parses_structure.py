"""STEP 2: structure without lexis — the jabberwock assigns grammatical ROLE by sentence-shape.

I seeded only WHAT it is (autonomous_syntax: a word's role is readable from the shape of the
sentence around it even when the word is unknown; closed-class FunctionWords fix the slots). The
jabberwock decides HOW. Its morphology Term (MorphTail) returns empty on novel words, so the
suffix route would need a new primitive; the POSITION route (function-word class of neighbours +
adjacency) it can compose now. It composes role_of(m); we verify it parses Jabberwocky's first
stanza — naming what is doing what — without knowing a single content word.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_parses_structure
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

SEP = "=" * 90
STANZA = "the slithy toves did gyre and gimble in the wabe all mimsy were the borogoves and the mome raths outgrabe"
EXPECT = {"slithy": "adjective", "toves": "noun", "gyre": "verb", "gimble": "verb", "wabe": "noun",
          "mimsy": "adjective", "borogoves": "noun", "mome": "adjective", "raths": "noun",
          "outgrabe": "verb"}

_ROLE_PROMPT = (
    "You ARE the jabberwock composing role_of(m) as a Term-tree (JSON): the GRAMMATICAL ROLE of a "
    "content word from the SHAPE of the sentence around it, without knowing the word. A token is a "
    "Mention bound to 'm'; tokens are chained by 'prev_mention'/'next_mention'; the small KNOWN "
    "closed class is FunctionWord nodes (attrs 'form','klass' in determiner/auxiliary/conjunction/"
    "preposition/pronoun/relativizer). Read the klass of m's previous and next tokens and decide the "
    "role string ('noun'/'verb'/'adjective').\n"
    "Building blocks (exact JSON):\n"
    '  {"type":"Var","name":"m"}   {"type":"Var","name":"f"}\n'
    '  {"type":"Neighbours","node":<t>,"edge_type":"prev_mention","any_type":false}  (and "next_mention")\n'
    '  {"type":"Pick","source":<set>}   {"type":"Attr","node":<t>,"key":"text"}\n'
    '  {"type":"NodesOfType","node_type":"FunctionWord"}\n'
    '  {"type":"Filter","source":<set>,"var_name":"f","predicate":<bool>}\n'
    '  {"type":"Eq","a":<t>,"b":<t>}   {"type":"Attr","node":<t>,"key":"form"}   {"type":"Attr","node":<t>,"key":"klass"}\n'
    '  {"type":"Lit","value":"determiner"}   (ALL strings must be Lit, never bare)\n'
    '  {"type":"IfThenElse","cond":<bool>,"then":<t>,"other":<t>}\n'
    "Helper you will reuse: the klass of m's previous token = Attr(Pick(Filter(NodesOfType "
    "FunctionWord, f, Eq(Attr(f,'form'), Attr(Pick(Neighbours(m,'prev_mention')),'text')))),'klass') "
    "— and likewise for next_mention. A content (unknown) neighbour matches no FunctionWord, so its "
    "klass is null.\n"
    "Decide the role by the structure: an auxiliary before m (did/were) means m is a VERB; a "
    "determiner before m with another content word after means m is an ADJECTIVE; a content word "
    "before m and a function word (or nothing) after means m is a NOUN; a conjunction before m "
    "joins like-with-like. Compose role_of(m) as nested IfThenElse over the previous/next klass. "
    "Return ONLY the JSON Term (value = the role string).")


def main():
    print(SEP)
    print("STEP 2 — the jabberwock parses structure WITHOUT lexis (role by sentence-shape)")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "jabberwocky", "shape_sense"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)
    teacher = a._self_teacher
    role = _compose(teacher, _ROLE_PROMPT)
    if not role:
        print("  (could not compose role_of) — aborting"); print(SEP); return
    a.author_subroutine("role_of", _litify(role), purpose="grammatical role from sentence-shape")
    print("  the agent composed + authored role_of (its structural parse)\n")

    mid = a.add_inbound(STANZA)
    a.comprehend()
    mentions = list(a.inner.neighbours(mid, "has_mention"))
    fwords = {a.s.node(n)["attrs"]["form"] for n in a.s.nodes("FunctionWord")}
    correct = total = 0
    print(f"  parsing: {STANZA!r}\n")
    for m in mentions:
        w = a.s.node(m)["attrs"].get("text")
        if w in fwords:
            continue
        try:
            r = a.run_subroutine("role_of", {"m": m})
        except Exception as e:
            r = f"(err {type(e).__name__})"
        exp = EXPECT.get(w)
        if exp:
            total += 1
            ok = (r == exp)
            correct += ok
            print(f"  {w:11} -> {str(r):10} {'OK' if ok else '(expected ' + exp + ')'}")
    print("\n" + SEP)
    print(f"  the jabberwock parsed the stanza by SHAPE alone: {correct}/{total} content words "
          f"given their correct grammatical role — knowing none of them. Structure read without lexis.")
    print(SEP)


if __name__ == "__main__":
    main()
