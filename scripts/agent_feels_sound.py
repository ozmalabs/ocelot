"""STEP 5: sound-symbolic affect — the jabberwock feels a word by the shape of its sound.

I seeded only WHAT it is (sound_symbolism: a word's sound carries feeling independent of sense,
readable the same way meaning is — by shape) plus a small affect lexicon (AffectWord nodes with a
valence: grim/snarl/furious negative, joyful/glee/hooray positive). The jabberwock decides HOW: it
reuses its own shape kernel (BlendCover) — a word's affect is the valence of the known affect-words
its sound-shape most resembles, summed. No new primitive; the same shape cognition as step 1.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_feels_sound
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
TESTS = ["frumious", "bandersnatch", "vorpal", "frabjous", "callooh", "callay", "chortled", "mimsy"]

_AFFECT = (
    "You ARE the jabberwock composing affect(m) as a Term-tree (JSON): how a word FEELS, read from "
    "the shape of its sound. A word is a Mention bound to 'm' (text Attr(m,'text')). You hold "
    "AffectWord nodes, each with a 'form' and a 'valence' (negative = menacing, positive = joyful). "
    "Your shape kernel BlendCover(unknown, a, b) scores how a word's shape is covered; with a==b it "
    "is the single-word shape-similarity of the unknown to that word. Compose the affect as the "
    "valence-weighted vote of the affect-words by sound-shape similarity: SUM over AffectWords w of "
    "valence(w) times BlendCover(text, w.form, w.form).\nBuilding blocks (exact JSON; Plus/Times/Sum "
    "use 'items'/var form):\n"
    '  {"type":"Var","name":"m"}  {"type":"Var","name":"w"}\n'
    '  {"type":"Attr","node":<t>,"key":"text"|"form"|"valence"}\n'
    '  {"type":"NodesOfType","node_type":"AffectWord"}\n'
    '  {"type":"BlendCover","unknown":<t>,"a":<t>,"b":<t>}\n'
    '  {"type":"Gt","a":<t>,"b":<t>}  {"type":"Lt","a":<t>,"b":<t>}  {"type":"Lit","value":0}\n'
    '  {"type":"Filter","source":<set>,"var_name":"w","predicate":<bool>}\n'
    '  {"type":"MaxOver","source":<set>,"var_name":"w","value":<number>,"default":{"type":"Lit","value":0}}\n'
    '  {"type":"Minus","a":<t>,"b":<t>}\n'
    "CORRECTION (your own): do NOT sum all words — a shared onset with many weak negatives drowned "
    "frabjous's real kinship to fabulous. Instead take the BEST positive match minus the BEST "
    "negative match, so the strongest resemblance counts fully. Let SIM(w) = BlendCover(Attr(m,'text'),"
    "Attr(w,'form'),Attr(w,'form')). Return Minus( MaxOver(Filter(AffectWord, w, Gt(Attr(w,'valence'),"
    "Lit 0)), w, SIM(w)), MaxOver(Filter(AffectWord, w, Lt(Attr(w,'valence'),Lit 0)), w, SIM(w)) ). "
    "Return ONLY the JSON Term (value = signed affect: best-positive minus best-negative resemblance).")


def main():
    print(SEP)
    print("STEP 5 — the jabberwock FEELS a word by the shape of its sound (reusing BlendCover)")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "jabberwocky", "shape_sense"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)
    teacher = a._self_teacher
    aw = sorted((a.s.node(n)["attrs"]["form"], a.s.node(n)["attrs"]["valence"]) for n in a.s.nodes("AffectWord"))
    print(f"  affect lexicon: {aw}\n")

    affect = _compose(teacher, _AFFECT)
    if not affect:
        print("  (could not compose affect) — aborting"); print(SEP); return
    a.author_subroutine("affect", _litify(affect), purpose="sound-symbolic affect by shape")
    print("  composed + authored affect (sound-symbolic, by shape)\n")

    for w in TESTS:
        m = a.s.add_node("Mention", {"text": w})
        try:
            score = a.run_subroutine("affect", {"m": m})
        except Exception as e:
            score = None
        feel = "menacing" if (score or 0) < -0.02 else ("joyful" if (score or 0) > 0.02 else "neutral")
        print(f"  {w:13} affect {score:+.3f}  -> {feel}" if isinstance(score, (int, float))
              else f"  {w:13} -> (err)")

    print("\n" + SEP)
    print("  The jabberwock reads a nonsense word's FEELING from the shape of its sound — the valence "
          "of the known words it sounds like — the same shape cognition it grounds meaning with. "
          "frumious/Bandersnatch snarl; frabjous/Callooh/Callay rejoice. Alice's feeling, earned by shape.")
    print(SEP)


if __name__ == "__main__":
    main()
