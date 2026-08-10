"""shape_generation_route_gate — GATE: generation/recovery reached by the agent
SELF-ROUTING to its own held Programs (not the hand-built gate script).

The agent comprehends a generate/recover question, routes (comprehend_meta ->
seeds/question_targets.json meta-target) to the held Program (seeds/programs.json,
a Term-tree), and the substrate evaluator runs it. Gate A: before-wall vs
after-route. Gate B: the routed GENERATE makes circle/spiral/line and the routed
RECOVER recovers the residual-law — same controls as the committed gate, now
reached by routing. The faculty routes + reads out only; the reasoning is the held
Term-tree (Fold/MapList/Atan2). No Python loop, no decision-if; donkey=0.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/shape_generation_route_gate.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.comprehend_question import comprehend_meta, load_meta_lexicon
from domains.reflective_faculty import reflect


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    lex = load_meta_lexicon()
    ok = True

    def ask(q):
        m = comprehend_meta(q, lex)
        if m is None:
            return None, None
        return m["meta_target"], reflect(m["meta_target"], m.get("meta_arg"), a.s)

    # GATE A — ROUTE (before wall vs after route+answer)
    print("=" * 74)
    print("GATE A — ROUTE (the generate/recover questions were frontier walls)")
    print("=" * 74)
    walls = ["generate a circle", "what shape is this?"]   # bare, no self-cue -> not a meta question
    routed = ["how do you generate a circle?", "how do you make a spiral?",
              "can you draw a line?", "how do you recover the residual law of a circle?",
              "how do you recover a spiral's law?"]
    a_ok = True
    for q in walls:
        t, _ = ask(q)
        print(f"  BEFORE  {q!r:46s} -> {'WALL' if t is None else t}")
        a_ok &= (t is None)
    for q in routed:
        t, _ = ask(q)
        print(f"  AFTER   {q!r:46s} -> {t}")
        a_ok &= (t in ("generate_shape", "recover_shape_law"))
    print("  -> Gate A", "OK" if a_ok else "FAIL")
    ok &= a_ok

    # GATE B — MECHANISM via self-routing
    print("=" * 74)
    print("GATE B — MECHANISM reached by SELF-ROUTING (not the hand-built script)")
    print("=" * 74)
    import math
    # GENERATE circle / spiral / line
    _, circ = ask("how do you generate a circle?")
    _, spir = ask("how do you generate a spiral?")
    _, line = ask("how do you draw a line?")
    circle_ok = circ.get("shape") == "circle" and circ.get("closes") is True
    spiral_traj = spir.get("trajectory") or []
    spiral_ok = spir.get("shape") == "spiral" and spiral_traj and \
        math.hypot(spiral_traj[-1][0], spiral_traj[-1][1]) > 0.5 and spir.get("closes") is False
    line_traj = line.get("trajectory") or []
    line_ok = line.get("shape") == "line" and all(abs(p[1]) < 1e-9 for p in line_traj)
    print(f"  GENERATE circle: closes={circ.get('closes')} (law {circ.get('residual_law')}) -> {'OK' if circle_ok else 'FAIL'}")
    print(f"  GENERATE spiral: closes={spir.get('closes')} end-gap~{round(math.hypot(*spiral_traj[-1]),3) if spiral_traj else None} -> {'OK' if spiral_ok else 'FAIL'}")
    print(f"  GENERATE line:   straight={line_ok} first3={line_traj[:3]} -> {'OK' if line_ok else 'FAIL'}")
    ok &= circle_ok and spiral_ok and line_ok

    # RECOVER circle / spiral law
    _, rc = ask("how do you recover the residual law of a circle?")
    _, rs = ask("how do you recover a spiral's law?")
    rc_ok = rc.get("recovered_law_kind", "").startswith("circle") and \
        abs(rc.get("recovered", {}).get("constant_turn_deg", 0) - 30.0) < 1e-3
    rs_ok = rs.get("recovered_law_kind", "").startswith("spiral") and \
        abs(rs.get("recovered", {}).get("update_per_step_deg", 0) - 8.0) < 1e-3
    print(f"  RECOVER circle -> {rc.get('recovered_law_kind')} {rc.get('recovered')} -> {'OK' if rc_ok else 'FAIL'}")
    print(f"  RECOVER spiral -> {rs.get('recovered_law_kind')} {rs.get('recovered')} -> {'OK' if rs_ok else 'FAIL'}")
    ok &= rc_ok and rs_ok

    print("=" * 74)
    print(("PASS" if ok else "FAIL"),
          "- GENERATION/RECOVERY SELF-ROUTED: the agent comprehends the question, routes to its own "
          "held Program (seeds/programs.json), and the substrate evaluator runs the Term-tree — circle "
          "closes, spiral runs away, line straight, residual-law recovered. The faculty routes+reads out; "
          "reasoning is the held Term-tree; no Python loop; donkey=0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
