"""The jabberwock CONSUMES THE RAW POEM graph-native — no hand-fed structure.

Correction: earlier steps hand-fed pre-parsed data (Act tuples with roles already assigned, a
picked word list). That is pre-digestion. Here the ONLY host I/O is feeding the raw poem text;
the world adapter tokenises it into Message + Mention nodes + prev/next adjacency (mechanical),
and the jabberwock does everything else over that graph: it finds its OWN unknown words
(oov_mentions), assigns each a grammatical role (role_of, from sentence-shape), reads each one's
affect (affect, by sound-shape), and decomposes the blends (BlendCover search) — all over the
actual tokens it pulled from the raw text, nothing handed to it.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_consumes_poem
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from scripts.agent_infers_meaning import _compose, _litify, _OOV_PROMPT
from scripts.agent_parses_structure import _ROLE_PROMPT
from scripts.agent_feels_sound import _AFFECT
from scripts.agent_decomposes_portmanteau import _FIRST, _SECOND

SEP = "=" * 96

# The RAW poem text — fed as-is. The agent tokenises and consumes it; nothing is pre-parsed.
RAW = (
    "'Twas brillig, and the slithy toves did gyre and gimble in the wabe; "
    "all mimsy were the borogoves, and the mome raths outgrabe. "
    "Beware the Jabberwock, my son! The jaws that bite, the claws that catch! "
    "He took his vorpal sword in hand; long time the manxome foe he sought. "
    "The vorpal blade went snicker-snack! He left it dead, and with its head "
    "he went galumphing back. O frabjous day! Callooh! Callay! He chortled in his joy."
)


def main():
    print(SEP)
    print("THE JABBERWOCK CONSUMES THE RAW POEM — graph-native, nothing pre-parsed")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "jabberwocky", "shape_sense"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)
    teacher = a._self_teacher

    # the only host I/O: feed the raw text. The adapter tokenises -> Mentions + adjacency.
    mid = a.add_inbound(RAW)
    a.comprehend()
    n_tok = len(list(a.inner.neighbours(mid, "has_mention")))
    print(f"\n  fed the raw poem ({n_tok} tokens); the agent tokenised + comprehended it itself.\n")

    # the agent composes the faculties it will run over what it extracted
    print("  composing faculties (oov-detector, role, affect, blend-search)...", flush=True)
    oov = _compose(teacher, _OOV_PROMPT)
    role = _compose(teacher, _ROLE_PROMPT)
    affect = _compose(teacher, _AFFECT)
    first = _compose(teacher, _FIRST)
    second = _compose(teacher, _SECOND)
    if not all((oov, role, affect, first, second)):
        print("  (a faculty failed to compose) — aborting"); print(SEP); return
    a.author_subroutine("oov_mentions", _litify(oov))
    a.author_subroutine("role_of", _litify(role))
    a.author_subroutine("affect", _litify(affect))
    a.author_subroutine("blend_first", _litify(first))
    a.author_subroutine("blend_second", _litify(second))

    fwords = {a.s.node(n)["attrs"]["form"] for n in a.s.nodes("FunctionWord")}

    # the agent finds ITS OWN unknown words in the raw text
    oov_ids = a.run_subroutine("oov_mentions", {"msg": mid}) or []
    unknown = [(m, a.s.node(m)["attrs"].get("text")) for m in oov_ids]
    unknown = [(m, w) for m, w in unknown if w and w not in fwords and len(w) > 2]
    print(f"  the agent found {len(unknown)} unknown words in the poem itself: "
          f"{sorted(set(w for _, w in unknown))}\n")

    def blend_of(word):
        u = a.s.add_node("Mention", {"text": word})
        c1 = a.run_subroutine("blend_first", {"u": u})
        if c1 is None:
            return None
        w1 = a.s.node(c1)["attrs"].get("form")
        c2 = a.run_subroutine("blend_second", {"u": u, "w1": c1})
        w2 = a.s.node(c2)["attrs"].get("form") if c2 is not None else None
        return (w1, w2) if (w1 and w2 and w1 != w2) else None

    print("  each unknown word, consumed from the raw text — role | affect | shape-decomposition:")
    seen = set()
    for m, w in unknown:
        if w in seen:
            continue
        seen.add(w)
        try:
            r = a.run_subroutine("role_of", {"m": m})
        except Exception:
            r = "?"
        try:
            sc = a.run_subroutine("affect", {"m": m})
            feel = "menacing" if (sc or 0) < -0.02 else ("joyful" if (sc or 0) > 0.02 else "neutral")
        except Exception:
            feel = "?"
        bl = blend_of(w)
        bls = f"{bl[0]}+{bl[1]}" if bl else "-"
        print(f"    {w:13} role={str(r):10} feel={feel:9} blend={bls}")

    # narrative cores, derived from the raw text: the words the agent parsed as VERBS
    verbs = []
    for m in a.inner.neighbours(mid, "has_mention"):
        w = a.s.node(m)["attrs"].get("text")
        if w in fwords:
            continue
        try:
            if a.run_subroutine("role_of", {"m": m}) == "verb":
                verbs.append(w)
        except Exception:
            pass
    print(f"\n  act-cores it derived from the raw text (words parsed as verbs): {verbs}")

    print("\n" + SEP)
    print("  Fed only the raw poem, the jabberwock tokenised it, found its own unknown words, and ran "
          "its faculties over them — role, affect, and shape-decomposition — plus pulled the verb cores "
          "of the narrative straight from the text. Nothing pre-parsed; consumed graph-native.")
    print(SEP)


if __name__ == "__main__":
    main()
