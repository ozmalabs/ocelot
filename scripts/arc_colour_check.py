"""Verify the live ARC perception now carries COLOUR: perceive a few ls20 frames and print, per Feature, its
raw value (colour index) and the colour NAME the feature_birth rule stamped from the index->name palette."""
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
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    s, I = a.s, a.inner
    sub, ctx = world.reset(); a.perceive_frame(sub)
    for act in ("Down", "Up", "Left", "Right", "Down", "Up"):
        sub, ctx = world.apply((act,)); a.perceive_frame(sub)
    print("=" * 80)
    print("LIVE ls20 — Feature (value -> colour) the feature_birth palette rule stamped")
    print("=" * 80)
    feats = [f for f in s.nodes("Feature") if I.has_node(f) and s.node(f)["attrs"].get("cy") is not None]
    pair = {}
    n_col = 0
    for f in feats:
        at = s.node(f)["attrs"]
        v = at.get("value"); col = at.get("colour")
        if col is not None:
            n_col += 1
        pair[(v, col)] = pair.get((v, col), 0) + 1
    for (v, col), n in sorted(pair.items(), key=lambda kv: (kv[0][0] is None, kv[0][0])):
        print(f"  value={v!s:>6}  colour={col!s:<12}  x{n}")
    print("-" * 80)
    print(f"  {len(feats)} Features perceived; {n_col} carry a colour attr "
          f"({'ALL' if n_col == len(feats) else 'PARTIAL' if n_col else 'NONE'})")
    return 0 if n_col == len(feats) and feats else 1


if __name__ == "__main__":
    raise SystemExit(main())
