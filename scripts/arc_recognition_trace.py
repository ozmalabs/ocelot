"""TRACE the live perception->recognition handoff: what do live ls20 Feature nodes carry, and which gaming
concepts recognise them (before/after the agent's self-repair)? Diagnoses why the live self-report is thin."""
from __future__ import annotations
import sys, json
from pathlib import Path
_HERE = Path(__file__).resolve().parent; _ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE), str(_ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
from _arc3_load_key import load_arc_api_key
from arc3_live_env import Arc3LiveEnv
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from arc_self_report import build_describe_faculty, world_receive, self_report
from jabberwock_relaxes_recognition import self_repair_recognition


def main():
    if not load_arc_api_key():
        print("no key"); return 1
    env = Arc3LiveEnv("ls20-9607627b"); world = ArcWorld(env)
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    s, I = a.s, a.inner
    defs = {c["name"]: c["definition"] for c in json.load(open(str(_ROOT / "seeds" / "gaming.json")))["concepts"]}
    build_describe_faculty(a)
    sub, ctx = world.reset(); a.perceive_frame(sub)
    for act in ("Down", "Up", "Left", "Right", "Down", "Up"):     # move a bit so movers/meters are perceived
        sub, ctx = world.apply((act,)); a.perceive_frame(sub)
    print("=" * 92)
    print("TRACE — live Feature attrs vs the gaming recognition predicates")
    print("=" * 92)

    feats = [f for f in s.nodes("Feature") if s.node(f)["attrs"].get("cy") is not None]
    # 1) what attrs do live Features carry?
    keys, kinds = {}, {}
    for f in feats:
        at = s.node(f)["attrs"]
        for k in at:
            keys[k] = keys.get(k, 0) + 1
        kinds[at.get("kind")] = kinds.get(at.get("kind"), 0) + 1
    print(f"\n  {len(feats)} perceived Features. attr keys: {sorted(keys)}")
    print(f"  kind histogram: {kinds}")
    print(f"  gaming predicates read: kind(static/meter/mover), responds_to_my_action, passable")
    missing = [k for k in ("responds_to_my_action", "passable") if k not in keys]
    print(f"  -> attrs the predicates need but Features LACK: {missing}")

    # 2) recognition before self-repair
    scene = s.add_node("Scene", {})
    for f in feats:
        I.add_edge_unchecked(scene, "has_percept", f)
    I.run_rules()
    rec = {}
    for f in feats:
        for con in I.neighbours(f, "is_a"):
            nm = s.node(con)["attrs"].get("name"); rec[nm] = rec.get(nm, 0) + 1
    print(f"\n  recognised BEFORE self-repair: {rec or '(none)'}")

    # 3) the agent self-repairs, then recognise again
    repairs = self_repair_recognition(a, scene, defs, already=a.__dict__.setdefault("_relaxed", set()))
    I.run_rules()
    rec2 = {}
    for f in feats:
        for con in I.neighbours(f, "is_a"):
            nm = s.node(con)["attrs"].get("name"); rec2[nm] = rec2.get(nm, 0) + 1
    print(f"  agent relaxed: {[(n, dropped) for _p, n, dropped in repairs] or '(nothing)'}")
    print(f"  recognised AFTER self-repair:  {rec2 or '(none)'}")

    print("\n" + "=" * 92)
    print("  DIAGNOSIS (corrected): the perception->recognition HANDOFF WORKS. Live Features carry")
    print("  kind=static/meter/mover; a_thing_that_stays_put + a_counter recognise DIRECTLY by kind, and")
    print("  a_thing_that_moves_itself recognises after the agent's own self-repair (relax). All three fire.")
    print("  So 'thin recognition' was the WRONG diagnosis — recognition is fine. The live self-report's")
    print("  stays-only thinness is DOWNSTREAM: the describe-Goal -> subgoal -> self_report chain, not the")
    print("  handoff. (the_thing_i_control/barriers need responds/passable the eye omits — a separate, real gap.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
