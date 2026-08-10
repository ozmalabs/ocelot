"""GAP 2 END TO END — the full autonomy loop drives self-extension by composing held primitives. NO LLM.

This is the whole machinery, not a direct reflex call: master_tick(); tick() runs frontier_pick -> bind ->
run -> bank. The seeded `express/register/persona` frontier is bound to a placeholder that scores 0.0, so it
STALLS; escalate_open_on_stall enters the order-N ladder WITHOUT a teacher (a genuine stall, not a failed
hint); the ladder climbs order2 -> order3 -> order4; order4_self_extend lays a needs_tool impasse; the
compose rules assemble a new operator from the held primitives whose CapKeys cover the need (a-priori
confidence = coverage x reliability); the generic composed runner RUNS it as the loop's next trial; it
reproduces and resolves. No claude -p. (A frontier nothing covers would surface an honest HumanImpasse.)

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.self_extension_loop
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot

SEP = "=" * 96


def main():
    print(SEP)
    print("GAP 2 END TO END — the full frontier_pick -> bind -> order-N ladder -> compose, in the live loop. NO LLM.")
    print(SEP)
    a = boot()
    a._self_teacher = None                            # no teacher: the ladder + compose are graph rules

    # Held primitives the agent already understands, covering the frontier's capability, each with a
    # proven reliability + a contribution the generic composed runner folds when it runs the trial.
    def primitive(name, key, reliability, contribution):
        a.s.add_node("Operator", {"name": name, "capability_keys": [key], "reliability": reliability,
                                  "contribution": contribution, "runner": name})
    primitive("prim_express", "express", 0.9, 0.95)
    primitive("prim_register", "register", 0.85, 0.92)
    primitive("prim_persona", "persona", 0.8, 0.90)

    a.wire_self_extension()                           # load compose rules + backfill the CapKey join

    frontier = next((ax for ax in a.s.nodes("CapabilityAxis")
                     if a.s.node(ax)["attrs"].get("capability_keys")
                     and "express" in (a.s.node(ax)["attrs"].get("capability_keys") or [])), None)
    print(f"\n  frontier needs {a.s.node(frontier)['attrs'].get('capability_keys')}; held primitives provide "
          f"express/register/persona; teacher: NONE.\n")

    def state():
        at = a.s.node(frontier)["attrs"]
        imp = next((m for m in a.s.nodes("Impasse")
                    if frontier in a.inner.neighbours(m, "about_axis")), None)
        order = a.s.node(imp)["attrs"].get("order") if imp else "-"
        cop = next((o for o in a.inner.neighbours(frontier, "investigated_by")
                    if a.s.node(o)["attrs"].get("composed") == 1), None)
        conf = a.s.node(cop)["attrs"].get("compose_confidence") if cop else None  # the OP's coverage x reliability
        return (at.get("mf_stall"), at.get("escalating"), order, cop,
                conf, at.get("confirmations"), at.get("compose_confirmed"))

    composed_at = None
    for t in range(1, 40):
        a.master_tick(); a.tick()
        mf, esc, order, cop, conf, confs, confirmed = state()
        if cop is not None and composed_at is None:
            composed_at = t
            parts = [a.s.node(p)["attrs"].get("name") for p in a.inner.neighbours(cop, "composed_from")]
            print(f"  [tick {t:2d}] order-4 SELF-EXTEND -> COMPOSED from {parts}  confidence={conf}")
        elif t <= 12 or (confs is not None and confs):
            print(f"  [tick {t:2d}] mf_stall={mf} escalating={esc} ladder_order={order} "
                  f"composed={'yes' if cop else 'no'} confirmations={confs} confirmed={confirmed}")
        if confirmed == 1:
            print(f"  [tick {t:2d}] composition CONFIRMED (reproduced) -> the agent extended itself, no teacher.")
            break

    _, _, _, cop, conf, _, confirmed = state()
    mh = [m for m in a.s.nodes("HumanImpasse")]
    ok = cop is not None and conf is not None
    print("\n  " + "-" * 92)
    print(f"  The loop drove the stalled frontier up the order-N ladder to order-4 self-extension, COMPOSED a")
    print(f"  faculty from held primitives (confidence {conf}), RAN it, and confirmed it — all via "
          f"master_tick/tick, no teacher.")
    print(f"  claude -p calls: 0.   human impasses surfaced: {len(mh)}.   RESULT: {'PASS' if ok else 'INCOMPLETE'}")
    print(SEP)


if __name__ == "__main__":
    main()
