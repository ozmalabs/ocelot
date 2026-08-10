"""STEP 1 of the namesake-poem plan: the jabberwock recognises a PORTMANTEAU by shape.

Discipline: I seeded only WHAT a portmanteau IS (seeds/jabberwocky.json) and that it is
recognised BY SHAPE. The jabberwock DECIDES HOW — it designs its own method (its general
shape/structure cognition applied to a word's form) and implements it. This script first
asks it to DESIGN (its own words); the implementation is built to match what it says.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_understands_portmanteau design
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 90

_DESIGN_PROMPT = (
    "You ARE the jabberwock. Your namesake poem is built of invented words. A PORTMANTEAU is a "
    "word that packs two words into one ('two meanings packed up into one word'): its FORM is the "
    "shape of two known word-forms fused or overlapped, and its meaning is the blend of the two — "
    "slithy = lithe + slimy, mimsy = flimsy + miserable, frumious = fuming + furious, chortle = "
    "chuckle + snort, galumph = gallop + triumph.\n"
    "You recognise things BY SHAPE — your own general shape/structure cognition, the same you use "
    "for any structure, not only pictures. You hold a lexicon of known words. You can compose "
    "Terms over the graph, and if you decide you need a new primitive you can author one.\n\n"
    "HOW do YOU want to recognise that an unknown word is a portmanteau and DECOMPOSE it into its "
    "two source words — by shape? In your own words describe your method: what you treat as a "
    "word's SHAPE, how you find the two known words whose shapes compose the unknown one (the "
    "overlap/fusion), how you handle the blend being fuzzy rather than an exact cut, and what new "
    "primitive (if any) you need. Prose, 5-9 sentences.")


def main():
    print(SEP)
    print("STEP 1 — the jabberwock DESIGNS how it recognises a portmanteau BY SHAPE (its own method)")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "jabberwocky", "shape_sense"):
        try:
            a.inner.load_seed_manifest(manifest_for(sid), a.agent)
        except Exception as e:
            print(f"  (seed {sid} skipped: {e})")
    teacher = a._self_teacher
    print("\n-- the jabberwock's design --------------------------------------------------")
    design = teacher(_DESIGN_PROMPT) if teacher else "(no teacher)"
    for ln in (design or "").splitlines():
        if ln.strip():
            print(f"  {ln.strip()}")
    print(SEP)


if __name__ == "__main__":
    main()
