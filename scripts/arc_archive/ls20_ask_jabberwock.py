"""ls20_ask_jabberwock — ASK THE JABBERWOCK (its own voice), DIAGNOSTIC ONLY.

The established method (arc3_live_selfassess): boot the full-stack agent, let it
play the live ls20 game a few turns through the THIN shim, then surface its OWN
introspection VERBATIM — what kinds it perceives, what it holds-but-cannot-ground,
what it is impassed on — and, paired with that, the concrete structure it built
for the bottom UI band (the depleting turns-bar + the three end dots) and whether
it formed ANY relation among the dots, or between the dots and the bar.

This shell authors NO diagnosis and NO fix. It drives fixed actions only (to
deplete the bar) and prints the agent's verdicts. The point is to hear the agent
name — or, by omission, reveal — the faculty it is missing, before we grow it.
"""
from __future__ import annotations

import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for p in (str(_ROOT), str(_ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["ARC3_THIN"] = "1"
os.environ["ARC3_FULL"] = "1"

from _arc3_load_key import load_arc_api_key  # noqa: E402
from arc3_live_env import Arc3LiveEnv  # noqa: E402
from domains.curious_agent import CuriousAgent  # noqa: E402
from domains.arc3_thin import arc3_thin_handle, SELF_ID  # noqa: E402
from domains.arc3_full_seed import install_full_seed_set  # noqa: E402

SEP = "=" * 78


def _band_objects(agent, rows=range(58, 64)):
    """The Locations (perceived objects) the agent built that lie in the band,
    with their type + column span. Reads mind_graph only."""
    cell_loc = {}
    cell_meta = {}
    for node in agent.mind_graph.nodes():
        a = node.attrs
        wt = a.get("world_type", "")
        if not isinstance(wt, str) or not wt.startswith("CellC"):
            continue
        r = a.get("last_row", a.get("row"))
        c = a.get("last_col", a.get("col"))
        if r is None or int(r) not in rows:
            continue
        loc = None
        for e in agent.mind_graph.out_edges(node.id, "within"):
            loc = e.key.tgt
            break
        cell_loc[node.id] = loc
        cell_meta[node.id] = (int(r), int(c), wt)
    regions = defaultdict(list)
    for nid, loc in cell_loc.items():
        regions[loc].append(cell_meta[nid])
    return regions, cell_loc, cell_meta


def _relations_among(agent, node_ids):
    """Any non-structural relation edges among a set of nodes (does the agent
    link the dots to each other / to the bar?). Excludes the bookkeeping edges
    (within/adjacent_to/has_cell) so only SEMANTIC relations show."""
    skip = {"within", "adjacent_to", "has_cell", "mapped_region", "inhabits"}
    ids = set(node_ids)
    out = []
    for nid in node_ids:
        for e in agent.mind_graph.out_edges(nid):
            if e.key.edge_type in skip:
                continue
            if e.key.tgt in ids:
                out.append((nid, e.key.edge_type, e.key.tgt))
    return out


def main():
    if not load_arc_api_key():
        print("BLOCKER: no ARC_API_KEY")
        return 2
    env = Arc3LiveEnv(game_id="ls20-9607627b")
    agent = CuriousAgent()
    agent.my_world_id = SELF_ID
    rep = install_full_seed_set(agent)
    print(f"booted full stack: concepts {rep.get('concepts_before')} -> "
          f"{rep.get('concepts_after')}  seeds={rep.get('seeds_installed')}")

    handle = arc3_thin_handle(env, agent)
    substrate, ctx = handle["reset"]()
    agent.observe(substrate)

    acts = [("a1",), ("a2",), ("a3",), ("a4",)]
    N = 8
    for i in range(N):
        action = acts[i % 4]
        touched = handle["interpret_acts_on"](substrate, ctx, action)
        for t in touched:
            agent._register_relation(t, "acts_on")
        agent._record_activity("act", touched)
        substrate, ctx = handle["apply_action"](substrate, ctx, action)
        agent.observe(substrate)

    print(f"\n{SEP}\nASK THE JABBERWOCK — after {N} turns on live ls20\n{SEP}")

    # --- 1. the agent's OWN voice, verbatim ---
    print("\n-- name_my_world() --")
    print("  ", agent.name_my_world())

    print("\n-- ask_for_guidance(): what kinds it perceives --")
    g = agent.ask_for_guidance()
    print("   i_perceive_kinds:", g.get("i_perceive_kinds"))

    print("\n-- unresolved_impasses(): what it is stuck on --")
    imps = agent.unresolved_impasses()
    if not imps:
        print("   (none — it raises no impasse about the band)")
    for im in imps[:10]:
        a = agent.mind_graph.node(im).attrs
        print("   ", {k: a.get(k) for k in ("reason", "question", "over")})

    print("\n-- held_predicates(): known-unknowns it cannot yet ground --")
    held = agent.held_predicates()
    if not held:
        print("   (none)")
    for h in held[:10]:
        print("   ", h["name"], "awaits", h["awaits"])

    # --- 2. the concrete structure it built for the band ---
    regions, cell_loc, cell_meta = _band_objects(agent)
    print(f"\n-- objects it built in the band: {len(regions)} Locations --")
    dot_locs = []
    bar_loc = None
    for loc, members in sorted(regions.items(), key=lambda kv: -len(kv[1])):
        types = Counter(m[2] for m in members)
        cols = sorted(c for (_r, c, _t) in members)
        span = f"cols {cols[0]}-{cols[-1]}" if cols else "?"
        tag = ""
        if list(types) == ["CellC8"]:
            dot_locs.append(loc)
            tag = "  <- a DOT"
        if list(types) == ["CellC11"]:
            bar_loc = loc
            tag = "  <- the BAR"
        print(f"   Loc {loc}: {len(members):3d} cells {dict(types)} {span}{tag}")

    # --- 3. does it relate the dots to each other / to the bar? ---
    print(f"\n-- relations among the {len(dot_locs)} dot-objects"
          f" and the bar --")
    # collect the cell nodes of dots + bar
    dot_cells = [nid for nid, loc in cell_loc.items() if loc in set(dot_locs)]
    bar_cells = [nid for nid, loc in cell_loc.items() if loc == bar_loc]
    rels = _relations_among(agent, dot_cells + bar_cells)
    sem = [r for r in rels]
    if not sem:
        print("   NONE. The three dots are unrelated objects; nothing links")
        print("   them to each other or to the collinear depleting bar.")
    else:
        for s in sem[:20]:
            print("   ", s)

    # --- 4. did the order-N series faculty group the dots + tie to the bar? ---
    print("\n-- order-N SERIES the agent now perceives (kind='series') --")
    n_series = 0
    for node in agent.mind_graph.nodes():
        if node.attrs.get("kind") != "series":
            continue
        n_series += 1
        a = node.attrs
        members = [e.key.src for e in agent.mind_graph.in_edges(node.id, "within")]
        coll = [e.key.tgt for e in
                agent.mind_graph.out_edges(node.id, "collinear_with")]
        # what type are the collinear (other) objects?
        coll_types = []
        for loc in coll:
            for e in agent.mind_graph.in_edges(loc, "within"):
                ct = agent.mind_graph.node(e.key.src).attrs.get("world_type")
                if ct:
                    coll_types.append(ct)
                    break
        print(f"   Series {node.id}: type={a.get('member_type')} "
              f"count={a.get('count')} spacing={a.get('spacing')} "
              f"orient={a.get('orientation')} @row~{a.get('cy')}")
        print(f"      members={len(members)}  collinear_with "
              f"{len(coll)} other objects (types {Counter(coll_types)})")
    if n_series == 0:
        print("   (none formed)")

    print(f"\n{SEP}\nVERDICT (read the above): does the jabberwock, in its own")
    print("voice, GROUP the three dots and tie them to the turn-bar — or is")
    print("that faculty simply absent?")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
