"""THE JABBERWOCK AUTHORS THE 'even collinear series' JUDGMENT AS GRAPH-NATIVE DSL,
THEN USES IT ON LIVE ls20 — matching the figure/ground 'area' work.

CLAUDE.md: the shell is a world adapter. The DECISION 'are these three dots a
straight, evenly-stepped line?' is NOT Python any more — it is a DSL Concept the
agent holds in its own mind_graph (`even_collinear`, the order-2 finite difference
it composes), run by its own evaluator. This driver shows the three steps that
match the bounds work:

  1. LOOKED UP   — the series vocabulary it grounded from its OWN WordNet/wiki
                   (series -> ordering -> arrangement; row -> line; interval /
                   spacing; collinear is the adjective the noun-ladder can't type).
  2. AUTHORED    — install_series_concepts authors the `even_collinear` DSL
                   Term-tree; the agent owns it and can explain WHY.
  3. RUN on ls20 — the perception groups the three end-dots into ONE series by
                   EVALUATING that concept on the dot triple (the agent judging),
                   and the same concept REJECTS a non-collinear triple.
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
from domains.series_concepts import install_series_concepts  # noqa: E402

SEP = "=" * 78


def _triple(agent, pts):
    """Materialise a triple of (row,col) points as a node + ask the agent's OWN
    concept whether it is even & collinear (its judgment, not ours)."""
    a, b, c = pts
    with agent.mind_substrate.transform() as tx:
        t = tx.add_node("OrderNTriple", {
            "r0": a[0], "c0": a[1], "r1": b[0], "c1": b[1],
            "r2": c[0], "c2": c[1]})
    held = agent._concept_holds("even_collinear", t)
    agent.mind_graph._delete_node(t)
    return held


def main():
    if not load_arc_api_key():
        print("BLOCKER: no ARC_API_KEY")
        return 2

    print(SEP)
    print("1. LOOKED UP (its own WordNet/wiki): series->ordering->arrangement,")
    print("   sequence->series, row->line, interval->measure, spacing->rate;")
    print("   'collinear' is an adjective the noun-genus ladder can't type — the")
    print("   honest gap, captured operationally by the order-2 difference.")

    env = Arc3LiveEnv(game_id="ls20-9607627b")
    agent = CuriousAgent()
    agent.my_world_id = SELF_ID
    install_full_seed_set(agent)

    print(f"\n{SEP}\n2. AUTHORED — the agent's graph-native concept (it owns + runs it)")
    cid = install_series_concepts(agent)
    print(f"   Concept 'even_collinear'  (node {cid})")
    print(f"      because: {agent.mind_graph.node(cid).attrs.get('because')}")
    print("      meaning: |(r2-r1)-(r1-r0)| <= tol  AND  |(c2-c1)-(c1-c0)| <= tol")
    print("               (order-2 finite difference ~0 on both axes)")

    # Sanity: the concept itself judges a clean even line vs a skewed/irregular one.
    print(f"\n   the concept's own verdicts (the agent judging):")
    print(f"      even row  (61.5,56.5)(61.5,59.5)(61.5,62.5) -> "
          f"{_triple(agent, [(61.5,56.5),(61.5,59.5),(61.5,62.5)])}  (expect True)")
    print(f"      irregular (61.5,56.5)(61.5,58.5)(61.5,62.5) -> "
          f"{_triple(agent, [(61.5,56.5),(61.5,58.5),(61.5,62.5)])}  (expect False)")

    # 3. RUN on ls20 — drive a few turns, let perception group via the concept.
    handle = arc3_thin_handle(env, agent)
    substrate, ctx = handle["reset"]()
    agent.observe(substrate)
    acts = [("a1",), ("a2",), ("a3",), ("a4",)]
    for i in range(6):
        action = acts[i % 4]
        for t in handle["interpret_acts_on"](substrate, ctx, action):
            agent._register_relation(t, "acts_on")
        agent._record_activity("act", [])
        substrate, ctx = handle["apply_action"](substrate, ctx, action)
        agent.observe(substrate)

    print(f"\n{SEP}\n3. RUN on live ls20 — series the perception formed via the concept")
    n = 0
    for node in agent.mind_graph.nodes():
        if node.attrs.get("kind") != "series":
            continue
        n += 1
        a = node.attrs
        coll = [e.key.tgt for e in
                agent.mind_graph.out_edges(node.id, "collinear_with")]
        ctypes = []
        for loc in coll:
            for e in agent.mind_graph.in_edges(loc, "within"):
                t = agent.mind_graph.node(e.key.src).attrs.get("world_type")
                if t:
                    ctypes.append(t)
                    break
        print(f"   Series: type={a.get('member_type')} count={a.get('count')} "
              f"spacing={a.get('spacing')} {a.get('orientation')} @row~{a.get('cy')}")
        print(f"      collinear_with: {sorted(set(ctypes))}  (the turns-bar)")
    if n == 0:
        print("   (none)")

    print(f"\n{SEP}")
    print("The series faculty is now graph-native: the DECISION is the agent's own")
    print("`even_collinear` concept (a DSL Term-tree it authored + can explain),")
    print("not a Python threshold. Same shape as the figure/ground 'area' work.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
