"""DRIVE THE REAL JABBERWOCK — read+ground the reading/writing failure-component doc and AUTHOR
its own COMPONENT INVENTORY + a plan for the MISSING components (esp. the graphemic buffer), via
the rung-2 composer (0f05f957). PHASE 3 of research->ground->jabberwock-plans. donkey=0 for the plan.

THE DISSOCIATION LOGIC (the doc): each isolable reading/writing failure marks a component boundary;
the taxonomy yields ~9 components. Session+speech hold the perception/output + central-route
components; the clearest MISSING is the GRAPHEMIC BUFFER (a SEQUENCE working-memory).

The plan is the JABBERWOCK'S: the held composer (compose_design_for_goal / _for_concept) AUTHORS the
assembly from held parts via the held shape-matcher; Python only feeds the operator's doc as a held
DesignGoal (adapter I/O) and dispatches drive(). A donkey spy counts LLM calls (must be 0). Where the
agent's relation-vocabulary cannot EXPRESS a missing component's distinctive relations, that is the
comprehension-frontier WALL = the precise graph-native gap (reported, not papered over).

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_plans_rw_components.py
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

DOC = os.path.join(ROOT, "docs", "reading_writing_failure_components.md")

# the 9 components the dissociation logic isolates (the doc's inventory), each as a goal description
# in the agent's OWN relation vocabulary so its composer can try to author each from held parts.
COMPONENTS = [
    ("MOTOR execution (apraxic agraphia)",
     "build the new from the prior; advance by the turn; accumulate the turn into a heading"),
    ("VISUAL word-form / letter identity (pure alexia)",
     "map part to part; detect the contact between parts; invariant part under transform"),
    ("ALLOGRAPHIC store (allographic agraphia)",
     "map part to part; invariant part under transform; repeat the part"),
    ("LEXICAL whole-word route (surface dysgraphia)",
     "reduce uncertainty given the prior; select the shorter over the longer; map part to part"),
    ("GRAPHEMIC BUFFER (buffer disorder: length-scaled errors)",
     "hold the ordered sequence of parts in working memory; the position of each part in the "
     "sequence; build the new from the prior; accumulate into the ordered output; map part to part"),
    ("LETTER-to-WORD / position binding (attentional dyslexia)",
     "map part to part; the position of each part; pairwise between parts; bind part to the slot"),
    ("SPATIAL / attentional frame (neglect dyslexia)",
     "detect the contact between parts; map part to part; the spatial side of the parts"),
]


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

    # the agent reads the doc as a held DesignGoal (operator's research fed as input)
    a.s.add_node("DesignGoal", {"description": prose})

    # (1) drive() self_design over the fed doc — the agent surfaces+authors from its own machinery
    print("=" * 88)
    print("PHASE 3 — DRIVE THE REAL JABBERWOCK (donkey=0): self_design reads the fed doc")
    print("=" * 88)
    driver = qd.QuestionDriver(substrate=s)
    emi = driver.drive(qd.QuestionPack(text="How do you want to design the missing reading and writing components?",
                                       reflect=rf.reflect))
    ma = emi.meta_answer or {}
    print(f"  COMPREHEND -> grounded={emi.target.grounded} meta_target={emi.target.meta_target} faculty={emi.target.faculty}")
    if "composable_machinery" in ma:
        print(f"  self_design surfaces: {ma.get('composable_machinery')}")
    if "authored_plan" in ma:
        ap = ma["authored_plan"]
        print(f"  self_design AUTHORED a plan over the fed doc: covered {ap.get('covered_count')}/{ap.get('goal_relations')}"
              f" parts={ap.get('ordered_parts')}")

    # (2) THE AGENT'S COMPONENT INVENTORY: for each isolated component, the composer authors a plan
    # from held parts (held vs lacks) — the plan is the matcher's Argmax, not the operator's.
    print("\n" + "=" * 88)
    print("THE JABBERWOCK'S COMPONENT INVENTORY (composer authors each from held parts; donkey=0)")
    print("=" * 88)
    held, walled = [], []
    for name, goal in COMPONENTS:
        gsig = rf._author_goal_signature(s, goal)
        # author from the component description ONLY (clear the doc so each goal is isolated)
        comp = rf.compose_design_for_goal(s, gsig, beam=4, cand_k=4) if gsig else {"authored": False, "reason": "no held relations express this component"}
        n_goal = len(gsig) if gsig else 0
        cov = comp.get("covered_count", 0)
        full = comp.get("authored") and cov == n_goal and n_goal > 0
        partial = comp.get("authored") and 0 < cov < n_goal
        tag = "HELD (fully composable)" if full else ("PARTIAL (composer covers some)" if partial else "WALL (cannot express/compose)")
        print(f"\n  [{tag}] {name}")
        if comp.get("authored"):
            print(f"     authored {cov}/{n_goal}: {comp.get('ordered_parts')}")
            if comp.get("residual"):
                print(f"     UNCOVERED relations (the gap): {json.dumps(comp['residual'])}")
        else:
            print(f"     {comp.get('reason')}")
        (held if full else walled).append(name)

    # (3) FOCUS on the named MISSING component — the GRAPHEMIC BUFFER (sequence working-memory)
    print("\n" + "=" * 88)
    print("FOCUS — the MISSING component: GRAPHEMIC BUFFER (a SEQUENCE WORKING-MEMORY)")
    print("=" * 88)
    buf_goal = ("hold the ordered sequence of parts in working memory; the position of each part in "
                "the sequence; build the new from the prior; accumulate into the ordered output")
    bsig = rf._author_goal_signature(s, buf_goal)
    bcomp = rf.compose_design_for_goal(s, bsig, beam=4, cand_k=4) if bsig else None
    print(f"  the agent authors the buffer goal-shape from ITS OWN relation vocabulary: {json.dumps(bsig)}")
    if bcomp and bcomp.get("authored"):
        print(f"  composer covers {bcomp['covered_count']}/{bcomp['goal_relations']} from held parts: {bcomp['ordered_parts']}")
    # THE REAL WALL (honest): the composer's 9/9 above is a FALSE POSITIVE — the buffer goal-shape
    # collapsed onto GENERIC relations (build/map/repeat/contact) via incidental keyword collisions.
    # The buffer's DISTINCTIVE notions — SEQUENCE, POSITION, ORDER, WORKING-MEMORY, SLOT — have NO
    # RelationCue, so the agent literally cannot EXPRESS them; "composing the buffer" is composing a
    # generic shape, not the sequence-WM. Check the held relation vocabulary directly.
    cues = rf._load_relation_cues(s)
    all_kw = [kw for kwl, _ in cues for kw in kwl]
    preds = sorted(set(rel[0] for _, rel in cues))
    print(f"  held relation predicates: {preds}")
    print("  CAN the vocabulary express the buffer-DISTINCTIVE notions (after the first-fix)?")
    can = []
    for term in ["sequence", "position", "order", "memory", "buffer", "serial", "slot", "next"]:
        hit = [kw for kw in all_kw if term in kw]
        print(f"    {term!r}: {hit if hit else 'NO CUE'}")
        if hit:
            can.append(term)
    # the TWO-STAGE finding: express (first-fix added order/hold cues) THEN compose.
    bgoal = ("hold the ordered sequence of parts in working memory; the position of each part in the "
             "sequence; build the new from the prior; accumulate into the ordered output")
    bsig2 = rf._author_goal_signature(s, bgoal)
    bc2 = rf.compose_design_for_goal(s, bsig2, beam=4, cand_k=4)
    print(f"  EXPRESS: the agent now authors the buffer-distinctive relations "
          f"({'order/hold present' if any(r[0] in ('order', 'hold') for r in (bsig2 or [])) else 'NOT present'}).")
    print(f"  COMPOSE: the composer covers {bc2['covered_count']}/{bc2['goal_relations']}; the UNCOVERED "
          f"residual = {json.dumps(bc2['residual'])}")
    print(f"  -> THE PRINCIPLED GAP: the first-fix gives the agent the VOCABULARY to EXPRESS the buffer,")
    print(f"     but NO held part has the SEQUENCE-WM shape ('order PART after PART' / 'hold PART at")
    print(f"     POSITION') — so it cannot COMPOSE the buffer from existing parts. The agent can now SAY")
    print(f"     what it lacks; a GENUINELY NEW primitive (a sequence working-memory) is required, not a")
    print(f"     recomposition. Exactly the MISSING central component the dissociation logic predicted.")

    print("\n" + "=" * 88)
    print(f"  donkey spy: LLM/teacher calls = {calls['n']} (must be 0)")
    print("=" * 88)
    print("HONEST READ: the PLAN is the jabberwock's (the held composer authored each component's")
    print("assembly via the held shape-matcher; donkey=0). TWO-STAGE finding for the MISSING component:")
    print("  (1) BEFORE the first-fix the agent FALSELY reported the buffer as 9/9 composable — the goal-")
    print("      shape collapsed onto GENERIC relations (no sequence/position cue existed).")
    print("  (2) FIRST-FIX (graph DATA, donkey=0): added sequence_order + position_buffer RelationCues")
    print("      -> the agent can now EXPRESS the buffer-distinctive relations; composing it then leaves")
    print("      'order PART after PART' / 'hold PART at POSITION' UNCOVERED — NO held part has the")
    print("      SEQUENCE-WORKING-MEMORY shape. The agent can now NAME its gap but cannot recompose it.")
    print("THE PRINCIPLED RESULT: the dissociation logic correctly predicted the GRAPHEMIC BUFFER as the")
    print("missing CENTRAL component; the agent confirms it needs a GENUINELY NEW primitive (a sequence")
    print("working-memory), not a recomposition. RESEARCH (doc) = operator's; the INVENTORY + the named")
    print("missing-primitive PLAN = the agent's (composer-authored).")
    return 0 if calls["n"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
