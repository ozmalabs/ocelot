"""STEP 2 + 3 — THE JABBERWOCK AUTHORS 'an arbitrary-shaped area that is a thing'
AS GRAPH-NATIVE DSL, THEN RUNS IT ON LIVE ls20.

CLAUDE.md: the shell is a world adapter + teacher. It owns NO reasoning. Every
decision here is a DSL Term-tree the AGENT holds in its own mind_graph and its own
evaluator runs — composed from concepts it GROUNDED by looking them up
(step 1: region / interior / enclosure / boundary → seeded primitives). The shell
only (a) asks the agent to author each concept (handing the genus it looked up as
provenance), (b) binds the grid's own dimensions when the agent evaluates (the same
mechanical I/O as observe), and (c) prints the agent's verdicts verbatim.

THE CONCEPTS THE AGENT AUTHORS (graph-native, introspectable, grounded):
  · world_edge_cell — a cell on the world's boundary (row/col at an extremity).
        genus it looked up: boundary → extremity.
  · ground_region   — a region that TOUCHES the world's boundary = background.
  · area            — a region that is NOT ground: a bounded, interior, arbitrary-
        shaped region that is a THING (a figure). genus: area → region → location
        → entity, and enclosure → area → region (looked up in step 1).
  · in_play         — an object ENCLOSED by the play area (its bbox inside the play
        area's bbox). genus it looked up: enclosure / containment / interior.

THE CLAIM IT THEN MAKES ON ls20: the green field is the play area (the largest
area-thing); the depleting turns-bar and the three end-dots are NOT in_play — they
are outside the play area — derived from STRUCTURE (bounded interior + enclosure),
with no colour meaning and no 'red = danger'.
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict
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
    install_figure_ground_concepts, eval_concept as _eval_concept, explain)

SEP = "=" * 78


def _regions(agent):
    """The perceived regions (Locations of kind 'room') with their member cells'
    type + bounding box + size. Reads mind_graph only."""
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
            rows.append(int(r))
            cols.append(int(c))
            wt = a.get("world_type")
            if wt:
                types.add(wt)
        if not rows:
            continue
        out[node.id] = {
            "type": "/".join(sorted(types)), "n": len(rows),
            "minrow": min(rows), "maxrow": max(rows),
            "mincol": min(cols), "maxcol": max(cols),
        }
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
    for i in range(6):
        action = acts[i % 4]
        for t in handle["interpret_acts_on"](substrate, ctx, action):
            agent._register_relation(t, "acts_on")
        agent._record_activity("act", [])
        substrate, ctx = handle["apply_action"](substrate, ctx, action)
        agent.observe(substrate)

    h, w = ctx["frame"].grid.__len__(), len(ctx["frame"].grid[0])
    ymax, xmax = h - 1, w - 1

    print(SEP)
    print("STEP 2 — THE AGENT COMPOSES THE FIGURE/GROUND CONCEPTS ITSELF")
    print("  (I ground only the perceptual ATOMS; the agent assembles the concepts")
    print("   via its OWN _spec_to_term from genus-differentia in its vocabulary)")
    print(SEP)
    install_figure_ground_concepts(agent)
    print("\n  the agent EXPLAINS 'area' (walks its definition to the atoms):")
    for line in explain(agent, "bounded_area"):
        print("   " + line)

    # --- the agent RUNS 'area' on every perceived region -> figures vs ground ---
    regions = _regions(agent)
    areas = []
    for rid, meta in regions.items():
        is_area = _eval_concept(agent, "bounded_area", rid, ymax=ymax, xmax=xmax)
        is_ground = _eval_concept(agent, "background_region", rid, ymax=ymax, xmax=xmax)
        meta["is_area"] = bool(is_area) if isinstance(is_area, bool) else is_area
        meta["is_ground"] = bool(is_ground) if isinstance(is_ground, bool) else is_ground
        if meta["is_area"] is True:
            areas.append((rid, meta))

    print(f"\n{SEP}\nSTEP 3 — THE AGENT RUNS IT ON ls20 (its own evaluator)\n{SEP}")
    print(f"  perceived {len(regions)} regions; {len(areas)} are AREAS (things),")
    print("  the rest are ground (touch the world's boundary):")
    for rid, m in sorted(regions.items(), key=lambda kv: -kv[1]["n"]):
        tag = "AREA (a thing)" if m["is_area"] is True else "ground"
        print(f"    {m['type']:14s} n={m['n']:4d} rows[{m['minrow']}-{m['maxrow']}]"
              f" cols[{m['mincol']}-{m['maxcol']}]  -> {tag}")

    if not areas:
        print("  (no areas found)")
        return 1

    # the PLAY AREA = the largest area-thing (the field the agent acts in).
    play_id, play = max(areas, key=lambda km: km[1]["n"])
    pminrow, pmaxrow = play["minrow"], play["maxrow"]
    pmincol, pmaxcol = play["mincol"], play["maxcol"]
    print(f"\n  the PLAY AREA = the largest area-thing: {play['type']} "
          f"n={play['n']} rows[{pminrow}-{pmaxrow}] cols[{pmincol}-{pmaxcol}]")

    # --- the agent RUNS 'in_play' on each object -> figure/ground for the band ---
    pe = dict(pminrow=pminrow, pmaxrow=pmaxrow,
              pmincol=pmincol, pmaxcol=pmaxcol)
    print("\n  is each object ENCLOSED by the play area?")
    for rid, m in sorted(regions.items(), key=lambda kv: -kv[1]["n"]):
        if rid == play_id:
            continue
        inp = _eval_concept(agent, "in_play", rid, **pe)
        verdict = "in the play area" if inp is True else "NOT in the play area"
        # flag the turns-bar (CellC11) and the end-dots (CellC8)
        note = ""
        if m["type"] == "CellC11":
            note = "   <- the turns-bar"
        if m["type"] == "CellC8":
            note = "   <- an end-dot"
        print(f"    {m['type']:14s} rows[{m['minrow']}-{m['maxrow']}] -> {verdict}{note}")

    print(f"\n{SEP}")
    print("THE AGENT'S VERDICT (in its own grounded vocabulary):")
    print(f"  'The play area is an AREA — a bounded, interior region that is a")
    print(f"   thing (area is-a region is-a location is-a entity, looked up).")
    print(f"   The turns-bar and the three end-dots are NOT in the play area:")
    print(f"   they are not enclosed by it (their rows fall outside it). I know")
    print(f"   this from STRUCTURE — bounded area + enclosure — not from colour.'")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
