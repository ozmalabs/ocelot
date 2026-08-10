"""ls20_band_probe — DIAGNOSTIC ONLY (not agent code, not a solver).

Drive the jabberwock on the live ls20 game for a few turns through the THIN shim,
then introspect — purely READING agent state — what perceptual structure it forms
about the bottom UI band (the depleting turns-bar + the three end dots), and
whether its general change/implied-rule machinery already ties the bar's depletion
to the passage of turns.

This writes NOTHING into the agent's decision path. It drives fixed actions only to
make the bar deplete, and observes. The point is to find the genuine gap, not to
hack a turn-bar detector.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "scripts"))

from _arc3_load_key import load_arc_api_key  # noqa: E402
from arc3_live_env import Arc3LiveEnv  # noqa: E402
from domains.curious_agent import CuriousAgent  # noqa: E402
from domains.arc3_thin import arc3_thin_handle, SELF_ID  # noqa: E402


def _band_cells(agent, rows=range(58, 64)):
    """Every CellC node the agent currently perceives in the bottom band, by
    (row, col) -> world_type. Reads mind_graph only."""
    out = {}
    for node in agent.mind_graph.nodes():
        a = node.attrs
        wt = a.get("world_type", "")
        if not isinstance(wt, str) or not wt.startswith("CellC"):
            continue
        r = a.get("last_row", a.get("row"))
        c = a.get("last_col", a.get("col"))
        if r is None or int(r) not in rows:
            continue
        out[(int(r), int(c))] = (node.id, wt)
    return out


def _regions_in_band(agent, band):
    """Group the band cells by the Location the agent merged them into."""
    from collections import defaultdict
    regions = defaultdict(list)
    for (r, c), (n, wt) in band.items():
        loc = None
        for e in agent.mind_graph.out_edges(n, "within"):
            loc = e.key.tgt
            break
        regions[loc].append((r, c, wt))
    return regions


def main():
    if not load_arc_api_key():
        print("BLOCKER: no ARC_API_KEY")
        return 2
    env = Arc3LiveEnv(game_id="ls20-9607627b")
    agent = CuriousAgent()
    agent.my_world_id = SELF_ID
    handle = arc3_thin_handle(env, agent)

    substrate, ctx = handle["reset"]()
    agent.observe(substrate)

    from arc3_env import ACTION1, ACTION2, ACTION3, ACTION4
    acts = [("a1",), ("a2",), ("a3",), ("a4",)]
    N = 6
    for i in range(N):
        action = acts[i % 4]
        touched = handle["interpret_acts_on"](substrate, ctx, action)
        for t in touched:
            agent._register_relation(t, "acts_on")
        agent._record_activity("act", touched)
        substrate, ctx = handle["apply_action"](substrate, ctx, action)
        agent.observe(substrate)

    print(f"=== after {N} turns on ls20 ===")
    band = _band_cells(agent)
    # summarise the band by colour and row
    from collections import Counter
    by_type = Counter(wt for (_n, wt) in band.values())
    print(f"band cells (rows 58-63): {len(band)}  by type: {dict(by_type)}")

    regions = _regions_in_band(agent, band)
    print(f"\nLocations the agent merged the band into: {len(regions)}")
    for loc, members in sorted(regions.items(),
                               key=lambda kv: -len(kv[1])):
        types = Counter(m[2] for m in members)
        cols = sorted(c for (_r, c, _t) in members)
        span = f"cols {cols[0]}-{cols[-1]}" if cols else "?"
        print(f"  Location {loc}: {len(members)} cells {dict(types)} {span}")

    # --- did the general change machinery notice the bar depletion? ---
    hist = getattr(agent, "_change_history", [])
    band_changes = [c for c in hist
                    if isinstance(c, dict) and c.get("y") in range(58, 64)]
    print(f"\nchange-instances captured in band: {len(band_changes)} "
          f"(total history {len(hist)})")
    cc = Counter((c.get("frm"), c.get("to")) for c in band_changes)
    for (frm, to), n in cc.most_common(8):
        print(f"  {frm} -> {to} : {n}")

    try:
        rules = agent.induce_change_rules()
        print(f"\ninduce_change_rules -> {len(rules) if rules else 0} rules")
        for r in (rules or [])[:12]:
            print(f"  {r}")
    except Exception as e:
        print(f"\ninduce_change_rules raised: {type(e).__name__}: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
