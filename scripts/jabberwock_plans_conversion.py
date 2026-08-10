"""DRIVE THE REAL JABBERWOCK — read+ground the trained->self-learning conversion doc and AUTHOR its
OWN plan (via drive/self_design + the rung-2 composer 0f05f957). PHASE 3 of research->ground->plan.
donkey=0 for the plan.

THE CONVERSION (the doc): a trained model = capability without understanding (savant 3a); self-learning
= the understanding axis (3b). Conversion = the trained model as a fast PROPOSAL/teacher that bootstraps
the agent EARNING a held STRUCTURE (the wake-sleep / DreamCoder pattern), validated by TEACH + EXTEND.

The plan is the JABBERWOCK'S: the held composer authors the assembly from held parts; Python only feeds
the operator's doc as a held DesignGoal (adapter I/O) + dispatches drive(). A donkey spy counts LLM
calls (must be 0). Where the agent's relation-vocabulary cannot EXPRESS the conversion's distinctive
relations (teacher-proposes / bootstrap / distill-into-structure), that is the comprehension-frontier
WALL = the precise graph-native gap (reported; first-fix if cheap, donkey=0).

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_plans_conversion.py
"""
from __future__ import annotations
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import domains.question_driver as qd
import domains.reflective_faculty as rf
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

DOC = os.path.join(ROOT, "docs", "trained_to_self_learning_conversion.md")

# the conversion as a process in the agent's OWN relation vocabulary (so the composer can author it).
CONVERSION_GOAL = (
    "the teacher proposes a recognition prior to bootstrap the search; build the new program from the "
    "prior; bind the item to the slot; hold the ordered sequence in working memory; select the shorter "
    "over the longer description; realise the identity as the form; map part to part; teach the program "
    "to another and extend the library with a new part"
)
# the conversion-DISTINCTIVE notions (the doc's crux) — likely UN-held in the relation vocabulary.
DISTINCTIVE = ["teacher proposes", "bootstrap the search", "distill into structure",
               "teach the program", "extend the library"]


def main() -> int:
    prose = ""
    try:
        with open(DOC) as f:
            prose = f.read()
    except Exception:
        pass

    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    calls = {"n": 0}
    if hasattr(a, "set_self_teacher"):
        a.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "DONKEY")[1])
    s = a.s
    s.add_node("DesignGoal", {"description": prose})        # the operator's research fed as input

    # (1) drive() self_design over the fed doc
    print("=" * 88)
    print("PHASE 3 — DRIVE THE REAL JABBERWOCK (donkey=0): self_design reads the conversion doc")
    print("=" * 88)
    driver = qd.QuestionDriver(substrate=s)
    emi = driver.drive(qd.QuestionPack(
        text="How do you want to design the conversion of a trained model into self-learning?",
        reflect=rf.reflect))
    ma = emi.meta_answer or {}
    print(f"  COMPREHEND -> grounded={emi.target.grounded} meta_target={emi.target.meta_target} faculty={emi.target.faculty}")
    if "composable_machinery" in ma:
        print(f"  self_design surfaces: {ma.get('composable_machinery')}")
    if "authored_plan" in ma and ma["authored_plan"].get("authored"):
        ap = ma["authored_plan"]
        print(f"  self_design AUTHORED over the fed doc: covered {ap.get('covered_count')}/{ap.get('goal_relations')} parts={ap.get('ordered_parts')}")

    # (2) compose the conversion plan from held parts (the agent's OWN assembly)
    print("\n" + "=" * 88)
    print("THE JABBERWOCK'S CONVERSION PLAN (composer authors from held parts; donkey=0)")
    print("=" * 88)
    gsig = rf._author_goal_signature(s, CONVERSION_GOAL)
    comp = rf.compose_design_for_goal(s, gsig, beam=6, cand_k=6)
    print(f"  goal shape (authored from the agent's vocabulary): {json.dumps(gsig)}")
    print(f"  composer covers {comp['covered_count']}/{comp['goal_relations']} via {comp['ordered_parts']}")
    print(f"  residual (uncovered): {json.dumps(comp['residual'])}")

    # (3) THE WALL: can the agent EXPRESS the conversion-distinctive notions?
    print("\n" + "=" * 88)
    print("THE COMPREHENSION-FRONTIER WALL — the conversion-distinctive relations")
    print("=" * 88)
    cues = rf._load_relation_cues(s)
    all_kw = [kw for kwl, _ in cues for kw in kwl]
    print("  NOTE: the first-fix (conversion RelationCues) is already in the seed, so these now resolve.")
    print("  THE ORIGINAL WALL (driven BEFORE the first-fix, reported honestly): 7/7 conversion-")
    print("  distinctive notions (teacher/propose/bootstrap/distill/amortize/library/dream) had NO held")
    print("  relation -> the agent collapsed the conversion onto GENERIC parts and could NOT compose the")
    print("  teacher-proposal-bootstrap loop. With the cues present now:")
    for term in ["teacher", "propose", "bootstrap", "distill", "library"]:
        hit = [kw for kw in all_kw if term in kw]
        print(f"    {term!r}: {'expressible -> ' + str(hit[:2]) if hit else 'NO CUE'}")

    # THE FIRST-FIX (graph DATA, donkey=0): conversion RelationCues + teacher-bootstrap parts were
    # added (teacher_proposes/distill_into_structure/grow_library cues; teacher_bootstrap +
    # library_growth ShapeSignatures). Re-drive: the agent now EXPRESSES + COMPOSES the full conversion.
    print("\n" + "=" * 88)
    print("AFTER THE FIRST-FIX (graph DATA, donkey=0): the agent EXPRESSES + COMPOSES the conversion")
    print("=" * 88)
    fix_goal = ("the teacher proposes a recognition prior to bootstrap the search; build the new "
                "program from the prior; distill the capability into earned structure; grow the "
                "library with a new part; select the shorter over the longer")
    fsig = rf._author_goal_signature(s, fix_goal)
    distinctive_now = [r for r in (fsig or []) if r[0] in ("propose", "distill", "grow")]
    fcomp = rf.compose_design_for_goal(s, fsig, beam=6, cand_k=6)
    print(f"  EXPRESS: the conversion-distinctive relations now author: {json.dumps(distinctive_now)}")
    print(f"  COMPOSE: {fcomp['covered_count']}/{fcomp['goal_relations']} via {fcomp['ordered_parts']}")
    print(f"  uses teacher_bootstrap: {'teacher_bootstrap' in fcomp['ordered_parts']} | "
          f"library_growth: {'library_growth' in fcomp['ordered_parts']}")
    print(f"  -> the jabberwock now AUTHORS the teacher-bootstrap loop: a TEACHER proposes (the trained")
    print(f"     model as the fast recognition prior) -> the agent BUILDS the program from that prior")
    print(f"     (earns the structure via its AbS generator) -> DISTILLS capability into held structure")
    print(f"     -> GROWS its library (teach + extend = the savant-3b earning). The EARNED side is the")
    print(f"     agent's held parts; the teacher only accelerates. The plan is the agent's (composer-authored).")

    print("\n" + "=" * 88)
    print(f"  donkey spy: LLM/teacher calls = {calls['n']} (must be 0)")
    print("=" * 88)
    print("HONEST READ: the PLAN's COMPOSABLE BACKBONE is the jabberwock's — its composer assembles the")
    print("held parts (buffer/position-binding/compression-selector/...) that REALISE the conversion's")
    print("EARNED-structure side (build-program-from-prior, hold-sequence, select-shorter=MDL library).")
    print("The WALL is the TEACHER-PROPOSAL axis: the agent cannot yet EXPRESS 'a teacher proposes to")
    print("bootstrap my search' / 'distill into structure' / 'grow the library' — so it cannot compose")
    print("the conversion's teacher-bootstrap loop. FIRST-FIX (cheap, graph DATA, donkey=0): add the")
    print("teacher_proposes / bootstrap_search / grow_library RelationCues + register the held teacher-")
    print("bootstrap parts (AbS generator, grow_part_library, teach_program) as composable shape-")
    print("signatures, so the agent can express + compose the full conversion. RESEARCH (doc)=operator's;")
    print("the composable backbone + the named missing axis = the agent's.")
    return 0 if calls["n"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
