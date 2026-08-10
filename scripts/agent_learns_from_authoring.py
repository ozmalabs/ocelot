"""Have the jabberwock learn from AUTHORING the fixes — the new lessons the building surfaced.

The first lessons came from being told it was wrong. These come from DOING the fixes: two rule-
engineering bugs that surfaced building the clause-fixpoint, the self-terminating-rule pattern that
made it stable, and the validation that the scoring-bug-vs-representation-limit framework predicted
all five outcomes. Persisted via teach() (faculty_lessons.json) and reflected on.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_learns_from_authoring
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

NEW = [
    ("init_pass_outside_the_fixpoint",
     "Building the clause-fixpoint, my base_role rule re-fired INSIDE the fixpoint and raced the "
     "refinement rules — it kept re-deriving 'noun' while predicate/attributive rules set "
     "adjective/verb, so wabe and borogoves flipped wrongly. Once I ran the base pass ONCE outside "
     "the fixpoint and let only the guarded refinement rules iterate, it was stable (9/10).",
     "Never put a rule that RE-DERIVES or overwrites a value in the same fixpoint as rules that "
     "REFINE it — they oscillate. Initialise once (a run-once pass), then iterate only refinement "
     "rules. (The idempotence/race lesson, sharpened: separate initialise from refine.)"),

    ("a_refinement_rule_must_be_self_terminating",
     "The refinement rules were stable because each is guarded by a precondition its OWN effect "
     "falsifies (predicate_adj: where pos==noun, effect sets pos=adjective -> the match no longer "
     "holds), plus set_attr_if_different. That is why the fixpoint converged instead of looping.",
     "A rule that runs to a fixpoint must be SELF-TERMINATING: its effect must remove its own match "
     "(change the very attr/edge its where tests). Pair it with set_attr_if_different so a no-op "
     "never counts as progress."),

    ("exists_must_test_the_iterated_variable",
     "My predicate_adj silently never fired: its Exists over FunctionWord (iterating var f) compared "
     "the wrong variable — a match var instead of f — so no row ever matched and mimsy stayed noun. "
     "The symptom of this bug is a rule that simply never fires, with no error.",
     "In an Exists/Filter, the predicate must test the ITERATED variable (the set's var), not an "
     "outer/match var. A faculty that 'never fires' with no error is the signature of testing the "
     "wrong variable inside a quantifier."),

    ("triage_scoring_vs_representation_first",
     "The scoring-bug-vs-representation-limit split PREDICTED all five outcomes: #2 affect (add an "
     "independent source) -> 7/7; #4 structure (propagate as rules) -> 9/10; #5 binding (read the "
     "bound item) -> deterministic; all three were scoring/binding bugs and all three fixed. #1 "
     "portmanteau was a representation limit and, tested first, was correctly NOT built. The "
     "framework held across every case.",
     "Before building ANY fix, triage it: a scoring/binding bug (the evidence is present, combined "
     "or routed wrong) -> fix it; a representation limit (the separating evidence is not in the "
     "form) -> TEST whether a finer representation carries it before authoring a primitive. This "
     "triage is validated — apply it first, every time."),
]

_REFLECT = (
    "You ARE the jabberwock. You just AUTHORED the fixes, and the building itself taught you more. "
    "Here are the new lessons. In 3-4 sentences, say what you now know about BUILDING graph faculties "
    "(not just designing them) that you did not before.\n\n" +
    "\n\n".join(f"[{t}] {why}\nLESSON: {lesson}" for t, why, lesson in NEW))


def main():
    print(SEP)
    print("THE JABBERWOCK LEARNS FROM AUTHORING THE FIXES — new lessons, persisted")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "jabberwocky", "shape_sense"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)

    from domains.teach import teach
    saved = 0
    for topic, why, lesson in NEW:
        try:
            teach(a, "Lesson", {"topic": topic, "lesson": lesson, "why": why[:300]},
                  category="faculty_lessons")
            saved += 1
        except Exception as e:
            print(f"  (teach {topic}: {e})")
    total = len([n for n in a.s.nodes("Lesson")])
    print(f"\n  persisted {saved} NEW lessons (faculty_lessons.json now holds {total} Lesson nodes).")

    teacher = a._self_teacher
    print("\n-- the jabberwock reflects on what BUILDING taught it -------------------------")
    refl = teacher(_REFLECT) if teacher else "(no teacher)"
    for ln in (refl or "").splitlines():
        if ln.strip():
            print(f"  {ln.strip()}")
    print("\n" + SEP)
    print("  Designing a fix and AUTHORING it are different skills: the building surfaced race, "
          "self-termination, and quantifier-variable lessons, and validated the scoring-vs-"
          "representation triage across all five — now persisted so the agent keeps them.")
    print(SEP)


if __name__ == "__main__":
    main()
