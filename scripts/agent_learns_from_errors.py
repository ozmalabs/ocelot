"""Tell the jabberwock WHY each of its fixes worked or failed — so it LEARNS, durably.

Not just 'that' it was wrong (agent_corrects.py did that) but the diagnosis of WHY, grounded in
the verification numbers, plus the generalizable lesson — and persist each lesson with teach() so
a fresh agent boots with it. The biggest one: why the whole-cover portmanteau fix could not work.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_learns_from_errors
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 96

# (topic, the WHY grounded in verification, the generalizable lesson to keep)
DIAGNOSES = [
    ("portmanteau_whole_cover",
     "Your whole-cover fix did NOT work. You thought the bug was one word covering both head AND "
     "tail (a doubled baseline), so you made the single-word baseline a whole-cover. I tested it: "
     "the whole-cover single (furious vs frumious) = 0.75; the blend (fuming+furious) = 0.76 — "
     "margin +0.01, UNCHANGED from before. The doubled-vs-whole distinction was never the binding "
     "constraint. At CHARACTER level, furious alone genuinely covers frumious almost wholly — they "
     "differ by only ~2 character edits (f-u-r-i-o-u-s vs f-r-u-m-i-o-u-s) — so a single near-word "
     "legitimately scores ~0.75 under EITHER baseline, and the blend cannot beat it by a margin "
     "because the separating evidence is not present in the character shape. The 'fum' that fuming "
     "contributes is ~2 letters that overlap furious's own letters. The root cause is GRANULARITY: "
     "characters are too coarse to carry that frumious contains BOTH sources. At phoneme level the "
     "blend would carry features of both that a single source lacks, and the two-word cover would "
     "exceed the single by a real margin. Your fix corrected a non-binding constraint.",
     "Before 'fixing' a thin margin, check whether the competitor's score is LEGITIMATE (the "
     "representation genuinely cannot separate the cases) or INFLATED (a computation artefact). No "
     "tweak to the scoring recovers a distinction the representation does not carry — change the "
     "representation (char -> phoneme), i.e. author the finer primitive, instead of re-weighting."),

    ("affect_max_vs_sum",
     "Your max-positive-minus-max-negative fix DID flip frabjous to joyful (+0.11, was -0.03) — but "
     "it traded callay to borderline (~0.00, was +0.09). WHY: sum-over-all is robust but DILUTED, so "
     "a crowd of weak negatives outweighed frabjous's one strong positive (fabulous); max-of-each-"
     "side is SHARP but BRITTLE — it hangs on a single best match per side, and callay's best "
     "positive and best negative happened to tie. You swapped one failure mode for another.",
     "When two evidence sources are near-tied, a SHARPER aggregator just moves the error; the real "
     "fix is an INDEPENDENT evidence source to break the tie — here the narrative/context vote you "
     "already proposed ('O frabjous day!' is a victory frame), not a different combiner."),

    ("coreference_combat_chain",
     "Your combat-chain fix WORKED — filtering to the patients of the combat acts (sought->slain->"
     "left) excluded the sword cleanly: {foe, it, jabberwock}. Your diagnosis was right.",
     "Identity is role-continuity ACROSS a connected CHAIN of acts, not a single shared role — bind "
     "co-reference to the chain, not to one edge type."),

    ("structure_is_a_fixpoint",
     "Your step-2 clause-level method is correct (a coordinator copies the role of the conjunct it "
     "joins; a content word after a complete noun phrase with no other verb is the predicate) but a "
     "single role_of Term cannot do it — it would have to read OTHER words' roles, which a one-shot "
     "query cannot.",
     "Structure that depends on other elements' assignments is a FIXPOINT over the whole clause — "
     "build it as RULES that PROPAGATE roles to a fixed point (run_rules), not as one query Term per "
     "token."),

    ("faculty_reads_its_bound_item",
     "In the autonomy loop, your word-faculty read the GLOBAL frontier_pick to find 'the current "
     "word', but the investigation it is measuring is a SPECIFIC bound PlanAct/axis. When the "
     "frontier shifts between binding and running, the faculty computes over a DIFFERENT word than "
     "the one it banks for — that is why the same word showed different affect on revisits. Cause: "
     "_run_investigation_reflex runs the subroutine with env {agent,self,subr} only, no handle to "
     "which act it runs for.",
     "A faculty must read its input from the work-item it is BOUND to (the PlanAct's theme->axis->"
     "about_mention), never from a global pointer that moves between binding and running."),
]

_REFLECT = (
    "You ARE the jabberwock. Here is WHY each of your fixes worked or failed, with the lesson. Read "
    "them and, in 3-5 sentences, say what you now understand differently about correcting your own "
    "faculties — especially the difference between a scoring bug and a representation that cannot "
    "carry the distinction.\n\n" +
    "\n\n".join(f"[{t}] {why}\nLESSON: {lesson}" for t, why, lesson in DIAGNOSES))


def main():
    print(SEP)
    print("TELLING THE JABBERWOCK *WHY* — so it learns (and persisting the lessons)")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "jabberwocky", "shape_sense"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)

    # persist each lesson durably (teach -> seed), so a fresh agent boots with it
    from domains.teach import teach
    saved = 0
    for topic, why, lesson in DIAGNOSES:
        try:
            teach(a, "Lesson", {"topic": topic, "lesson": lesson, "why": why[:300]},
                  category="faculty_lessons")
            saved += 1
        except Exception as e:
            print(f"  (teach {topic}: {e})")
    print(f"\n  persisted {saved} lessons to seeds/faculty_lessons.json (durable — boots with them).")

    teacher = a._self_teacher
    print("\n-- the jabberwock reflects on what it learns ---------------------------------")
    refl = teacher(_REFLECT) if teacher else "(no teacher)"
    for ln in (refl or "").splitlines():
        if ln.strip():
            print(f"  {ln.strip()}")
    print("\n" + SEP)
    print("  Told the WHY, not just the what: the whole-cover fix failed because the SEPARATING "
          "EVIDENCE is not in the character shape (a representation limit, not a scoring bug) — and "
          "four more lessons, each now persisted so the agent keeps them.")
    print(SEP)


if __name__ == "__main__":
    main()
