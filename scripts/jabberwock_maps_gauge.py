"""THE JABBERWOCK UNDERSTANDS THE CONCEPT OF A GAUGE/BAR AND MAPS IT ON ls20.

Not a hard-coded "3 dots = last 3 turns" binding (that is dynamic + situational).
Instead: the agent grounded the concept of a gauge (gauge -> measuring instrument),
COMPOSED a recogniser for it (an elongated, out-of-play strip whose substance is
consumed each action — its OWN induced change-rule), and RECOGNISES the ls20 strip
as one, mapping the collinear series of dots as its SCALE. The precise reading is
then a dynamic consequence of the mapping, not a rule.

Shell = world adapter + teacher: the agent composes + runs every concept.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["ARC3_THIN"] = "1"
os.environ["ARC3_FULL"] = "1"

from _arc3_load_key import load_arc_api_key  # noqa: E402
from arc3_live_env import Arc3LiveEnv  # noqa: E402
from domains.curious_agent import CuriousAgent  # noqa: E402
from domains.arc3_thin import arc3_thin_handle, SELF_ID  # noqa: E402
from domains.arc3_full_seed import install_full_seed_set  # noqa: E402
from domains.figure_ground_concepts import (  # noqa: E402
    install_figure_ground_concepts, eval_concept, explain)
from domains.gauge_concepts import install_gauge_concept  # noqa: E402

SEP = "=" * 78


def _regions(agent):
    out = {}
    for node in agent.mind_graph.nodes():
        if node.attrs.get("kind") != "room":
            continue
        rows, cols, types = [], [], set()
        for e in agent.mind_graph.in_edges(node.id, "within"):
            a = agent.mind_graph.node(e.key.src).attrs
            r = a.get("last_row", a.get("row"))
            c = a.get("last_col", a.get("col"))
            if r is None:
                continue
            rows.append(int(r)); cols.append(int(c))
            wt = a.get("world_type")
            if wt:
                types.add(wt)
        if rows:
            out[node.id] = {"type": "/".join(sorted(types)), "n": len(rows),
                            "minrow": min(rows), "maxrow": max(rows),
                            "mincol": min(cols), "maxcol": max(cols)}
    return out


def main():
    if not load_arc_api_key():
        print("BLOCKER: no ARC_API_KEY")
        return 2
    env = Arc3LiveEnv(game_id="ls20-9607627b")
    agent = CuriousAgent()
    agent.my_world_id = SELF_ID
    install_full_seed_set(agent)
    handle = arc3_thin_handle(env, agent)
    substrate, ctx = handle["reset"]()
    agent.observe(substrate)
    acts = [("a1",), ("a2",), ("a3",), ("a4",)]
    for i in range(8):
        action = acts[i % 4]
        for t in handle["interpret_acts_on"](substrate, ctx, action):
            agent._register_relation(t, "acts_on")
        agent._record_activity("act", [])
        substrate, ctx = handle["apply_action"](substrate, ctx, action)
        agent.observe(substrate)

    # the agent INDUCES its change-rules from the turns it watched (so the gauge
    # recogniser can read which type is being consumed each action).
    agent.induce_change_rules()

    h, w = len(ctx["frame"].grid), len(ctx["frame"].grid[0])
    ymax, xmax = h - 1, w - 1

    print(SEP)
    print("THE AGENT COMPOSES 'gauge' AND MAPS IT (it grounded gauge->measuring")
    print("instrument; here it composes the recogniser + recognises the instance)")
    print(SEP)
    install_figure_ground_concepts(agent)
    install_gauge_concept(agent)
    print("\n  the agent EXPLAINS 'gauge' (walks it to the atoms):")
    for line in explain(agent, "gauge"):
        print("   " + line)

    # play area (largest bounded_area) -> its bbox, for the NOT in_play test.
    regions = _regions(agent)
    areas = [(rid, m) for rid, m in regions.items()
             if eval_concept(agent, "bounded_area", rid, ymax=ymax, xmax=xmax) is True]
    play_id, play = max(areas, key=lambda km: km[1]["n"])
    pe = dict(pminrow=play["minrow"], pmaxrow=play["maxrow"],
              pmincol=play["mincol"], pmaxcol=play["maxcol"])

    print(f"\n{SEP}\nWHICH PERCEIVED REGIONS ARE A GAUGE? (the agent's recogniser)\n{SEP}")
    gauges = []
    for rid, m in sorted(regions.items(), key=lambda kv: -kv[1]["n"]):
        is_g = eval_concept(agent, "gauge", rid, **pe)
        if is_g is True:
            gauges.append((rid, m))
            # map its scale: the series collinear_with it
            scale = 0
            for e in agent.mind_graph.out_edges(rid, "collinear_with"):
                if agent.mind_graph.node(e.key.tgt).attrs.get("kind") == "series":
                    scale = agent.mind_graph.node(e.key.tgt).attrs.get("count", 0)
            for e in agent.mind_graph.in_edges(rid, "collinear_with"):
                if agent.mind_graph.node(e.key.src).attrs.get("kind") == "series":
                    scale = agent.mind_graph.node(e.key.src).attrs.get("count", 0)
            print(f"  GAUGE: {m['type']} strip spanning cols[{m['mincol']}-{m['maxcol']}]"
                  f" rows[{m['minrow']}-{m['maxrow']}]")
            print(f"     depletes each action (its induced rule frm={m['type']}),")
            print(f"     out of the play area, with a collinear SCALE of {scale} markers.")

    if not gauges:
        print("  (no gauge recognised)")
        return 1

    print(f"\n{SEP}")
    print("THE MAPPING (the agent's, in its own concepts):")
    print("  'That strip is a GAUGE — an elongated out-of-play indicator whose")
    print("   substance is consumed once per action (my induced rule). Its extent")
    print("   measures a quantity that falls each turn; the collinear markers are")
    print("   its SCALE. How much is left, and what the markers count down to, I")
    print("   READ from the gauge as it changes — it is not a fixed rule.'")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
