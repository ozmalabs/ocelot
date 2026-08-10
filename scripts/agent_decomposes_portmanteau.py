"""STEP 1 (cont.): the jabberwock composes the PORTMANTEAU SEARCH over its BlendCover kernel.

The kernel (BlendCover, Rust, jabberwock-authored) scores how well two known words fuse to cover
an unknown. The SEARCH/accept DECISION is composed in the graph (the AbS argmax pattern): for an
unknown word, find the pair of known WordForms with the best fused cover, and accept it as a
portmanteau only if that pair beats the best single-word cover by a margin. Meaning = the two
sources' glosses.

The agent composes two Argmax Terms (best first source, then best partner); the host chains them
and applies the margin (the only host part is the threshold + reading off the decomposition).

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_decomposes_portmanteau
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
TESTS = ["slithy", "mimsy", "frumious", "chortle", "galumph", "hello", "table"]
MARGIN = 0.04

_FIRST = (
    "You ARE the jabberwock composing the FIRST half of your portmanteau search as a Term-tree "
    "(JSON). Your kernel BlendCover scores how two known words fuse to cover an unknown. The "
    "unknown word is a Mention bound to 'u' (its text is Attr(u,'text')); the known words are "
    "WordForm nodes, each with a 'form' attribute. Compose the Term returning the WordForm that is "
    "the best FIRST source: the c1 maximising, over all WordForms c2, the BlendCover of the unknown "
    "with c1's form and c2's form.\nTerm JSON (exact fields):\n"
    '  {"type":"Var","name":"u"}  {"type":"Var","name":"c1"}  {"type":"Var","name":"c2"}\n'
    '  {"type":"Attr","node":<t>,"key":"text"}   {"type":"Attr","node":<t>,"key":"form"}\n'
    '  {"type":"NodesOfType","node_type":"WordForm"}\n'
    '  {"type":"BlendCover","unknown":<t>,"a":<t>,"b":<t>}\n'
    '  {"type":"MaxOver","source":<set>,"var_name":"c2","value":<number>}\n'
    '  {"type":"Argmax","source":<set>,"var_name":"c1","value":<number>}\n'
    "Return Argmax over WordForms c1, scored by MaxOver over WordForms c2 of "
    "BlendCover(Attr(u,'text'), Attr(c1,'form'), Attr(c2,'form')). Return ONLY the JSON Term.")

_SECOND = (
    "You ARE the jabberwock composing the SECOND half of your portmanteau search as a Term-tree "
    "(JSON). The unknown is a Mention bound to 'u'; the chosen first source is a WordForm bound to "
    "'w1'. Compose the Term returning the WordForm c2 that maximises BlendCover of the unknown's "
    "text with w1's form and c2's form.\nTerm JSON (exact fields):\n"
    '  {"type":"Var","name":"u"}  {"type":"Var","name":"w1"}  {"type":"Var","name":"c2"}\n'
    '  {"type":"Attr","node":<t>,"key":"text"}   {"type":"Attr","node":<t>,"key":"form"}\n'
    '  {"type":"NodesOfType","node_type":"WordForm"}\n'
    '  {"type":"BlendCover","unknown":<t>,"a":<t>,"b":<t>}\n'
    '  {"type":"Argmax","source":<set>,"var_name":"c2","value":<number>}\n'
    "Return Argmax over WordForms c2, scored by BlendCover(Attr(u,'text'), Attr(w1,'form'), "
    "Attr(c2,'form')). Return ONLY the JSON Term.")


def _blend(a, u_text, x, y):
    t = {"type": "BlendCover", "unknown": {"type": "Lit", "value": u_text},
         "a": {"type": "Lit", "value": x}, "b": {"type": "Lit", "value": y}}
    a.author_subroutine("_bc", t)
    return a.run_subroutine("_bc")


def main():
    print(SEP)
    print("STEP 1 (cont.) — the jabberwock composes the portmanteau SEARCH over its BlendCover kernel")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "jabberwocky", "shape_sense"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)
    teacher = a._self_teacher
    forms = {f: a.s.node(n)["attrs"]
             for n in a.s.nodes("WordForm") for f in [a.s.node(n)["attrs"].get("form")]}
    print(f"  vocabulary (known WordForms): {sorted(forms)}\n")

    first = _compose(teacher, _FIRST)
    second = _compose(teacher, _SECOND)
    if not first or not second:
        print("  (could not compose the search) — aborting"); print(SEP); return
    a.author_subroutine("blend_first", _litify(first), purpose="best first source word")
    a.author_subroutine("blend_second", _litify(second), purpose="best partner source word")
    print("  the agent composed + authored blend_first / blend_second (its graph search)\n")

    for word in TESTS:
        u = a.s.add_node("Mention", {"text": word})
        c1 = a.run_subroutine("blend_first", {"u": u})
        if c1 is None:
            print(f"  {word:10} -> (no candidate)"); continue
        w1 = a.s.node(c1)["attrs"].get("form")
        c2 = a.run_subroutine("blend_second", {"u": u, "w1": c1})
        w2 = a.s.node(c2)["attrs"].get("form") if c2 is not None else None
        pair = _blend(a, word, w1, w2) if w2 else 0.0
        # best single-word WHOLE cover = max over forms of BlendCover(word, f, f)
        single = max(_blend(a, word, f, f) for f in forms)
        is_port = (w1 != w2) and (pair - single > MARGIN)
        if is_port:
            g1, g2 = forms[w1].get("gloss"), forms[w2].get("gloss")
            print(f"  {word:10} = {w1} + {w2}  (cover {pair:.2f} vs single {single:.2f}, +{pair-single:.2f})"
                  f"  -> meaning ~ {g1} + {g2}")
        else:
            print(f"  {word:10} -> not a confident portmanteau (best pair {w1}+{w2} {pair:.2f} "
                  f"vs single {single:.2f}; margin {pair-single:+.2f})")

    print("\n" + SEP)
    print("  The jabberwock authored the BlendCover kernel (Rust) AND composed the pair-search over it "
          "(graph). It decomposes a blend into its two source shapes and reads the meaning as their "
          "composition; the accept-by-margin is where confidence lives (thin at char level by design).")
    print(SEP)


if __name__ == "__main__":
    main()
