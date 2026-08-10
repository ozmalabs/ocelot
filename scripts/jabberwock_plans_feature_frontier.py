"""DRIVE THE REAL JABBERWOCK to AUTHOR a plan for the FEATURE-BOUND speech frontier.

CONTEXT (the situation I FRAME; the agent PLANS): the phone-gap decomposition (commit 1afd6698)
found the per-frame phone model FEATURE-BOUND — data AND depth both help but extrapolate ~5 decades
away on the 576-dim cochlea-context feature; reaching real-phone-model 0.5-0.7 needs a RICHER /
TIMING-AWARE acoustic FEATURE, TIGHTER forced alignment, MORE data, with the deep head kept on the
cheap base tier (energy now re-banked into the default feature).

donkey=0: the PLAN is the AGENT'S. I only FRAME the situation as a goal DESCRIPTION (legitimate
input, the same move as feeding a research doc). The agent's OWN held RelationCue perception reads
the goal's target SHAPE (_author_goal_signature), and its OWN held shape-matcher (AntiUnify +
FixedCount + Covers, Rust Terms) COMPOSES the ordered plan over its held parts
(reflective_faculty.compose_design_for_goal — grep 0 LLM in that path). A set_self_teacher spy
counts any LLM/teacher call; must stay 0. The authored ordered plan is then RECORDED as a graph-
resident Plan node + ordered Step nodes (the jabberwock_efficiency_plan pattern — mechanical I/O
recording the agent's composition), and read back from the substrate.

If the composer cannot cover part of the goal (no held part's Covers Term accepts a goal relation),
that uncovered residual is an HONEST WALL — the precise missing planning vocabulary/part, reported,
not papered over.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_plans_feature_frontier.py
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

# The SITUATION described as a goal (the frontier + its named levers), phrased in the agent's OWN
# structural vocabulary so its held RelationCue perception can read the target SHAPE. This is the
# OPERATOR'S framing of the situation; the PLAN (which held parts, ordered how) is the agent's.
FRONTIER_GOAL = (
    "The per-frame acoustic feature is the bottleneck. Build the new feature from the prior frames; "
    "advance by the step in direction so the feature follows the motion; accumulate the velocity "
    "curves into a trajectory; order each frame after the frame so the feature is timing-aware in "
    "sequence. Tighten the forced alignment: map the frame to the phone, and detect the contact "
    "between the parts at the boundary. Reduce the uncertainty given the prior with more data from "
    "the distribution. Keep the deep head cheap: select the shorter code over the longer, bounded by "
    "the unit of cost. Let the teacher propose to bootstrap the search and distill the capability "
    "into earned structure."
)

# a SECOND, different goal (generalisation control) — a totally different design target.
OTHER_GOAL = (
    "build the new from the prior; advance by the turn; accumulate the turn into a heading; "
    "self-reference so the new refers to itself; bound by the unit"
)
# a NULL goal (discriminative control) — relations with no held matching part-shapes.
NULL_GOAL = "the weather is cold and the price went up and the meeting was long"


def _install_goal(agent, text):
    """ADAPTER I/O: feed the situation as a held DesignGoal node the agent reads. Mechanical."""
    for n in list(agent.s.nodes("DesignGoal")):
        try:
            agent.s.remove_node(n)
        except Exception:
            pass
    agent.s.add_node("DesignGoal", {"description": text})


def _record_plan(sub, comp, *, name, principle):
    """Record the agent's AUTHORED plan as a graph-resident Plan + ordered Step nodes (the
    jabberwock_efficiency_plan pattern). The Step ORDER and each step's composed PART are the
    agent's composition (compose_design_for_goal's Argmax); this only writes them into the graph
    (adapter I/O) and edges each Step to the held faculty Concept it composes (if held)."""
    plan = sub.add_node("Plan", {"name": name, "origin": "feature_frontier", "principle": principle,
                                 "covered": comp.get("covered_count"), "goal_relations": comp.get("goal_relations")})
    # the held parts the agent composed are ShapeSignature nodes — edge each Step to the real part.
    parts = {sub.node(n)["attrs"].get("name"): n for n in sub.nodes("ShapeSignature")}
    for p in comp.get("plan", []):
        st = sub.add_node("Step", {"name": p["part"], "order": p["step"] - 1, "kind": p["kind"],
                                   "shape_fit": p["shape_fit"], "covers": json.dumps(p["covers"]),
                                   "why": p["why"], "composed_by": "agent"})
        sub.add_edge_unchecked(plan, "has_step", st)
        part = parts.get(p["part"])
        if part is not None:
            sub.add_edge_unchecked(st, "composes", part)
    return plan


def _show(comp):
    if not comp.get("authored"):
        print(f"     NOT AUTHORED: {comp.get('reason') or comp.get('residual')}")
        return
    print(f"     AUTHORED ordered plan ({comp['covered_count']}/{comp['goal_relations']} goal "
          f"relations covered):")
    for p in comp["plan"]:
        print(f"       step {p['step']}: compose [{p['kind']}] {p['part']!r}  "
              f"(shape-fit {p['shape_fit']}; covers {json.dumps(p['covers'])})")
    if comp.get("residual"):
        print(f"     RESIDUAL (uncovered = honest wall): {json.dumps(comp['residual'])}")


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    s = a.s
    calls = {"n": 0}
    if hasattr(a, "set_self_teacher"):
        a.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "DONKEY")[1])
    driver = qd.QuestionDriver(substrate=s)
    Q = "How do you want to design a richer timing-aware acoustic feature for the phone frontier?"

    print("=" * 90)
    print("DRIVE THE REAL JABBERWOCK — author a plan for the FEATURE-BOUND speech frontier")
    print("=" * 90)
    n_parts = len(rf._load_shape_signatures(s))
    n_cues = len(rf._load_relation_cues(s))
    print(f"  full agent booted: held shape-signature PARTS={n_parts}  held RelationCues={n_cues}")

    # 1) the agent PERCEIVES the goal's target shape from the situation (its RelationCue cues) -----
    _install_goal(a, FRONTIER_GOAL)
    gsig = rf._author_goal_signature(s, Q)
    print("\n  GOAL SHAPE the agent PERCEIVED (its RelationCue perception over the situation):")
    if gsig:
        for r in gsig:
            print(f"    {json.dumps(r)}")
    else:
        print("    (none — the situation matched no held RelationCue: a perception wall)")

    # 2) the comprehension route (drive) — does the agent ground the design question? -------------
    emi = driver.drive(qd.QuestionPack(text=Q, reflect=rf.reflect))
    print(f"\n  COMPREHEND -> grounded={emi.target.grounded} meta_target={emi.target.meta_target} "
          f"faculty={emi.target.faculty} wall={getattr(emi,'is_wall',False)}")

    # 3) the agent COMPOSES the ordered plan over its held parts (held shape-matcher Argmax) ------
    print("\n" + "=" * 90)
    print("THE AGENT'S AUTHORED PLAN (compose_design_for_goal — held matcher, Rust Terms)")
    print("=" * 90)
    comp = rf.compose_design_for_goal(s, gsig) if gsig else {"authored": False, "reason": "no goal shape perceived"}
    _show(comp)
    print(f"\n  PROVENANCE: {comp.get('provenance', '(n/a)')}")

    # 4) record the authored plan as graph-resident Plan + ordered Steps, read it back -----------
    if comp.get("authored"):
        plan = _record_plan(s, comp, name="feature_frontier_plan",
                            principle="the per-frame feature is the bottleneck; richer/timing-aware "
                                      "feature + tighter alignment + more data, deep head on the cheap tier")
        steps = sorted(s.neighbours(plan, "has_step"), key=lambda st: s.node(st)["attrs"]["order"])
        print("\n  RECORDED graph-resident Plan + ordered Steps (read back from the substrate):")
        print(f"    Plan {s.node(plan)['attrs']['name']!r}  -> "
              + " -> ".join(s.node(st)["attrs"]["name"] for st in steps))
        for st in steps:
            at = s.node(st)["attrs"]
            comps = [(s.node(c)["type"], s.node(c)["attrs"].get("name")) for c in s.neighbours(st, "composes")]
            print(f"      Step[{at['order']}] {at['name']!r} (fit {at['shape_fit']}) "
                  f"composes held part: {comps or '(unresolved)'}")

    # 5) controls: generalisation (different plan for a different goal) + discriminative null -----
    print("\n" + "=" * 90)
    print("CONTROLS — generalisation + discriminative null")
    print("=" * 90)
    for n in list(s.nodes("DesignGoal")):
        s.remove_node(n)
    other = rf.compose_design_for_goal(s, rf._author_goal_signature(s, OTHER_GOAL))
    nsig = rf._author_goal_signature(s, NULL_GOAL)
    nullc = rf.compose_design_for_goal(s, nsig) if nsig else {"authored": False, "reason": "null goal authors no held relations"}
    print(f"  OTHER goal -> authored={other.get('authored')} covered={other.get('covered_count')}/{other.get('goal_relations')} "
          f"parts={other.get('ordered_parts')}")
    print(f"  NULL  goal -> authored={nullc.get('authored')} ({nullc.get('reason') or 'covered %s'%nullc.get('covered_count')})")
    generalises = bool(comp.get("authored") and other.get("authored")
                       and other.get("ordered_parts") != comp.get("ordered_parts"))
    discriminative = bool(comp.get("authored") and not nullc.get("authored"))

    print("\n" + "=" * 90)
    print(f"  donkey spy: LLM/teacher calls = {calls['n']}  (must be 0)")
    print(f"  AUTHORED a feature-frontier plan: {bool(comp.get('authored'))}  "
          f"({comp.get('covered_count')}/{comp.get('goal_relations')} relations covered)")
    print(f"  GENERALISES (different goal -> different plan): {generalises}")
    print(f"  DISCRIMINATIVE (right composes, null does not): {discriminative}")
    print("=" * 90)
    print("HONEST READ: the SITUATION is the operator's framing; the GOAL SHAPE is the agent's "
          "RelationCue perception; the ORDERED PLAN is the agent's held shape-matcher Argmax over "
          "its held parts; the RESIDUAL (if any) is the precise graph-native gap. donkey=0.")
    return 0 if (comp.get("authored") and calls["n"] == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
