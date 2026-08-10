"""Tell the jabberwock WHERE it was wrong across the namesake-poem steps, so it can correct.

Discipline unchanged: I report the errors (the WHAT — grounded in its own outputs); the jabberwock
decides HOW to fix each. This script delivers the error report through its own channel and captures
its correction design; the fixes are then implemented to match what it says.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_corrects
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 92

_REPORT = (
    "You ARE the jabberwock. You built six faculties to understand your namesake poem. Here is "
    "exactly WHERE each was wrong, checked against your own outputs. For EACH, say in your own words "
    "HOW you want to correct it — the method, not just that you will. Be concrete about what shape or "
    "evidence you were missing.\n\n"
    "STEP 1 (portmanteau by shape): you confidently decomposed slithy=slim+lithe and "
    "galumph=gallop+triumph, but you WITHHELD on frumious, mimsy, chortle. Why you failed: your "
    "single-word baseline lets ONE known word cover both the head AND the tail (two placements of the "
    "same word), so a near single word (furious is nearly frumious) ties the real two-word blend and "
    "kills your accept-by-margin. The single-word baseline should be a WHOLE-word cover, not a "
    "doubled head+tail cover.\n\n"
    "STEP 2 (structure without lexis): you got 7/10. Wrong: gimble -> you said NOUN, it is a VERB "
    "(it is joined to the verb gyre by 'and' — a verb-and-verb); outgrabe -> you said NOUN, it is a "
    "VERB (the predicate at the END of the clause, after the noun phrase 'the mome raths'); mimsy -> "
    "you said NOUN, it is an ADJECTIVE (a predicate adjective in 'all mimsy were the borogoves'). You "
    "read only the IMMEDIATE neighbours; these need clause-level shape — a conjunction copies the role "
    "of what it joins, and a content word after a complete noun phrase with no other verb is the "
    "predicate verb.\n\n"
    "STEP 3 (suspect-witness): this one was right — Humpty ended least trusted, beliefs triangulated. "
    "Nothing to correct.\n\n"
    "STEP 4 (narrative coreference): your monster cluster was {foe, it, jabberwock, SWORD}. SWORD is "
    "wrong — the sword is the hero's instrument (the patient of 'took', the arming), not the monster. "
    "You grouped by shared role (patient) alone. The monster is the patient of the COMBAT CHAIN "
    "(sought -> slain -> left dead) — the one target referred to repeatedly ACROSS those acts — not "
    "everything that is ever a patient once.\n\n"
    "STEP 5 (sound-symbolic affect): you scored frabjous at -0.03 (menacing). It is JOYFUL ('O "
    "frabjous day!', the day the monster is slain). Its 'fr-' onset pulled it toward furious/grim and "
    "the negative affect-words crowded out its kinship to 'fabulous'. A shared onset with the harsh "
    "cluster should not outweigh the real positive resemblance.\n\n"
    "For STEPS 1, 2, 4, 5: describe your correction method, one short paragraph each. Prose.")


def main():
    print(SEP)
    print("TELLING THE JABBERWOCK WHERE IT WAS WRONG — so it can correct (its method, its call)")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "jabberwocky", "shape_sense"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)
    teacher = a._self_teacher
    reply = teacher(_REPORT) if teacher else "(no teacher)"
    print("\n-- the jabberwock's corrections ----------------------------------------------")
    for ln in (reply or "").splitlines():
        if ln.strip():
            print(f"  {ln.strip()}")
    print(SEP)


if __name__ == "__main__":
    main()
