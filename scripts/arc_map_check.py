"""Does the agent RECOGNISE THE SHAPES AND MAP THEM from a single perceived frame — no avatar, no nav?
Boot, reset ls20, perceive ONE frame, and dump the spatial map the agent holds. Read-only.

  ulimit -v 12000000
  PYTHONPATH=runners/dsl/python:. python3 scripts/arc_map_check.py
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
from collections import Counter


def main() -> int:
    if not load_arc_api_key():
        print("no key"); return 1
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    S = a.s
    env = Arc3LiveEnv("ls20-9607627b"); world = ArcWorld(env)
    sub, ctx = world.reset()
    a.perceive_frame(sub)                       # ONE perceive — recognition only

    print("=" * 84)
    print("WHAT MAP DOES THE AGENT BUILD FROM ONE PERCEIVED FRAME (recognition, no avatar)?")
    print("=" * 84)

    # raw observation shape
    grid = getattr(a, "_last_grid", None)
    try:
        import numpy as np
        g = np.asarray(grid); print(f"  raw frame: shape={g.shape}  values={sorted(set(g.ravel().tolist()))}")
    except Exception:
        print(f"  raw frame: {type(grid)}")

    # 1) the GRID map — Cell nodes with positions + values (the spatial layout)
    cells = [c for c in S.nodes("WorldInstance") if S.node(c)["attrs"].get("world_type") == "Cell"]
    cvals = Counter(S.node(c)["attrs"].get("value") for c in cells)
    haspos = sum(1 for c in cells if S.node(c)["attrs"].get("row") is not None)
    print(f"\n  CELL map: {len(cells)} cells ({haspos} with row/col); value histogram {dict(cvals)}")
    for c in cells[:3]:
        print("    e.g.", {k: S.node(c)['attrs'].get(k) for k in ('row', 'col', 'value', 'visited', 'wall')})

    # 2) the RECOGNISED SHAPES — Region/Feature nodes with positions
    regs = list(S.nodes("Region"))
    print(f"\n  REGIONS (recognised shapes): {len(regs)}")
    for r in regs[:5]:
        at = S.node(r)["attrs"]
        print("    ", {k: at.get(k) for k in ('rvalue', 'count', 'cy', 'cx', 'is_ground')})
    feats = list(S.nodes("Feature"))
    print(f"\n  FEATURES: {len(feats)}  kinds={dict(Counter(S.node(f)['attrs'].get('kind') for f in feats))}")
    for f in feats[:5]:
        at = S.node(f)["attrs"]
        print("    ", {k: at.get(k) for k in ('kind', 'role', 'cy', 'cx', 'rvalue')})

    # 3) any explicit spatial-map / locus nodes
    for t in ("Locus", "SpatialLocation", "Map", "Cell"):
        try:
            n = len(list(S.nodes(t)))
            if n:
                print(f"  {t}: {n}")
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
