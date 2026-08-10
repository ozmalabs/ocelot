"""LIVE ls20 — the interaction-frontier question, on the real game.

The move-space loop says: when movement is exhausted, the way forward is a NON-MOVEMENT affordance (interaction).
ls20's interaction affordance is Select (ACTION5). This probes the empirical question directly: settle the slider
against a wall in each direction (movement exhausted at that stop), then try Select, and measure the world's
response (ctx['changed'] = grid cells changed). If Select changes the world beyond the settled-move baseline, the
interaction-frontier premise holds on the real game; if not, that is an honest null about ls20 (progression is
not via Select). The score is observed, never chased.

  PYTHONPATH=runners/dsl/python:. python3 scripts/arc_interaction_live.py
"""
from __future__ import annotations
import sys
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


def main():
    if not load_arc_api_key():
        print("no key"); return 1
    env = Arc3LiveEnv("ls20-9607627b"); world = ArcWorld(env)
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    sub, ctx = world.reset(); agent.perceive_frame(sub)
    print("=" * 92)
    print("LIVE ls20 — settle (movement exhausted), then INTERACT (Select); measure the world's response")
    print("=" * 92)

    # settle in each direction (3 presses -> the last are no-ops against a wall), then a Select at that stop.
    seq = []
    for d in ("Down", "Up", "Left", "Right"):
        seq += [d, d, d, "Select"]
    seq += ["Select", "Select"]                          # two more interactions for good measure

    rows = []
    for i, act in enumerate(seq):
        sub, ctx = world.apply((act,)); agent.perceive_frame(sub)
        ch = int(ctx.get("changed", 0)); sc = int(ctx.get("score", 0))
        rows.append((act, ch, sc))
        print(f"  {i+1:2} {act:7} changed={ch:4d} score={sc}", flush=True)
        if ctx.get("over") or ctx.get("won"):
            print("  game", "WON" if ctx.get("won") else "OVER"); break

    sel = [ch for a, ch, _ in rows if a == "Select"]
    mov = [ch for a, ch, _ in rows if a != "Select"]
    # settled-move baseline = the SMALL changed values among moves (no-ops against a wall + ambient dynamics)
    settled = sorted(mov)[: max(1, len(mov) // 2)]
    base = sum(settled) / len(settled) if settled else 0.0
    sel_mean = sum(sel) / len(sel) if sel else 0.0
    scores = [s for _, _, s in rows]

    print("\n" + "=" * 92)
    print(f"  Select (interaction) changed: {sel}  (mean {sel_mean:.1f})")
    print(f"  movement changed: {sorted(mov)}  (settled-baseline mean {base:.1f})")
    print(f"  score over the run: {scores[0]} -> {scores[-1]} (observed, not chased)")
    effect = sel_mean > base + 1.5 and any(c > 0 for c in sel)
    if effect:
        print("  FINDING: Select CHANGES the world beyond the settled-move baseline — the interaction-frontier")
        print("  premise HOLDS on real ls20: when movement is exhausted, interacting (Select) does something.")
    else:
        print("  FINDING (honest null): Select does NOT change the world more than a settled move — on real ls20")
        print("  progression is not via Select here. The interaction the move-space frontier needs is elsewhere")
        print("  (e.g. a Click@cell / ACTION6, or a specific contact) — the next thing to probe, reported not faked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
