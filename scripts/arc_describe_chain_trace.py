"""TRACE the describe chain: recognised concepts -> describe-Goal -> utterance subgoals -> self_report. Isolated
(controlled percepts at live multiplicity: 16 static, 2 meter, 2 mover), donkey=0. Finds where the self-report
loses counts/moves despite all three being recognised."""
from __future__ import annotations
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from arc_self_report import build_describe_faculty, world_receive, self_report
from jabberwock_relaxes_recognition import self_repair_recognition
from domains.language_world import LanguageWorld, teacher_stub
from domains.language_production import LanguageProduction
from scripts.language_test import training_bank


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner
    defs = {c["name"]: c["definition"] for c in json.load(open(os.path.join(ROOT, "seeds", "gaming.json")))["concepts"]}
    build_describe_faculty(a)
    world = LanguageWorld(I, training_bank(), teacher_stub); world.run()
    world.teacher_disabled = True
    prod = LanguageProduction(world)                       # describe vocab is seeded graph data (describe_lexicon)

    print("=" * 92)
    print("TRACE the describe chain — recognised -> describe-Goal -> subgoals -> self_report (16 static/2 meter/2 mover)")
    print("=" * 92)

    scene = s.add_node("Scene", {})
    for _ in range(16):
        I.add_edge_unchecked(scene, "has_percept", s.add_node("Percept", {"kind": "static"}))
    for _ in range(2):
        I.add_edge_unchecked(scene, "has_percept", s.add_node("Percept", {"kind": "meter"}))
    for _ in range(2):
        I.add_edge_unchecked(scene, "has_percept", s.add_node("Percept", {"kind": "mover"}))

    # LIVE ORDER (as arc_run._do_self_report): receive instruction + tick FIRST (describe-Goal + subgoals minted
    # for whatever is recognised so far), THEN self-repair (relax mover), THEN tick again, THEN self_report.
    I.run_rules()                                              # initial recognition: static + meter; mover NOT yet
    world_receive(a, scene, "Describe what you see.")
    I.run_rules()                                              # describe-Goal + subgoals minted (mover unrecognised)
    self_repair_recognition(a, scene, defs, already=set())     # relax the mover
    I.run_rules()                                              # mover now recognised — does the communicate rule re-fire?

    rec = {}
    for p in I.neighbours(scene, "has_percept"):
        for con in I.neighbours(p, "is_a"):
            nm = s.node(con)["attrs"].get("name"); rec[nm] = rec.get(nm, 0) + 1
    print(f"\n  RECOGNISED: {rec}")

    gs = [g for g in s.nodes("Goal") if s.node(g)["attrs"].get("kind") == "describe_scene"]
    subgoals = [sg for g in gs for sg in I.neighbours(g, "has_subgoal")]
    about = {}
    for sg in subgoals:
        con = next(iter(I.neighbours(sg, "about")), None)
        nm = s.node(con)["attrs"].get("name") if con else "(none)"
        about[nm] = about.get(nm, 0) + 1
    print(f"  describe-Goals: {len(gs)}; utterance subgoals: {len(subgoals)}; subgoal 'about' histogram: {about}")

    _ng, _nsg, lines = self_report(a, prod)
    print(f"  self_report emits: {lines}")

    print("\n" + "=" * 92)
    print(f"  donkey: {donkey['n']}")
    print(f"  recognised concepts: {sorted(rec)}")
    print(f"  subgoals cover:      {sorted(about)}")
    print(f"  reported:            {len(lines)} lines")
    if sorted(about) != sorted(rec):
        print("  -> LOSS at the COMMUNICATE rule: subgoals do not cover every recognised concept.")
    elif len(lines) < len(set(about) - {'(none)'}):
        print("  -> LOSS at self_report: subgoals cover the concepts but production/dedup drops some.")
    else:
        print("  -> chain is COMPLETE: every recognised concept is reported (the live thinness is the wiring,")
        print("     not the chain — e.g. Features not linked, or per-frame clearing).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
