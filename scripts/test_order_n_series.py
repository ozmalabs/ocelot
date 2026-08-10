"""test_order_n_series — the order-N series faculty is GENERIC, not an ls20 hack.

Feed the agent hand-built synthetic grids (nothing to do with any game) through
the same thin-shim perception path and check that its layout perception groups
SEPARATED same-type objects into one series IFF they are collinear AND regularly
spaced — and binds the series collinear_with a co-axial object. A connected-
component (region) pass cannot do this; the order-N shape operator can.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

_ROOT = Path(__file__).resolve().parent.parent
for p in (str(_ROOT), str(_ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from arc3_env import GameState  # noqa: E402
from domains.curious_agent import CuriousAgent  # noqa: E402
from domains.arc3_thin import _build_thin, SELF_ID  # noqa: E402


def _grid(h, w, cells):
    g = [[0] * w for _ in range(h)]
    for (r, c, v) in cells:
        g[r][c] = v
    return g


def _series(agent):
    """All series Locations the agent perceives, as (member_type, count, orient,
    collinear_types)."""
    out = []
    for node in agent.mind_graph.nodes():
        if node.attrs.get("kind") != "series":
            continue
        coll = []
        for e in agent.mind_graph.out_edges(node.id, "collinear_with"):
            for ie in agent.mind_graph.in_edges(e.key.tgt, "within"):
                t = agent.mind_graph.node(ie.key.src).attrs.get("world_type")
                if t:
                    coll.append(t)
                    break
        out.append((node.attrs.get("member_type"), node.attrs.get("count"),
                    node.attrs.get("orientation"), sorted(set(coll))))
    return out


def _perceive(grid):
    agent = CuriousAgent()
    agent.my_world_id = SELF_ID
    sub, *_ = _build_thin(SimpleNamespace(grid=grid, score=0,
                                          state=GameState.NOT_FINISHED), None)
    agent.observe(sub)
    return _series(agent)


def main():
    cases = []

    # 1. three evenly-spaced same-type dots in a row -> ONE horizontal series.
    g = _grid(10, 20, [(2, 4, 8), (2, 8, 8), (2, 12, 8)])
    cases.append(("3 even dots, a row", g, lambda s: len(s) == 1 and
                  s[0][:3] == ("CellC8", 3, "horizontal")))

    # 2. four evenly-spaced same-type pips in a column -> ONE vertical series.
    g = _grid(20, 10, [(2, 3, 5), (5, 3, 5), (8, 3, 5), (11, 3, 5)])
    cases.append(("4 even pips, a column", g, lambda s: len(s) == 1 and
                  s[0][:3] == ("CellC5", 4, "vertical")))

    # 3. three same-type but IRREGULARLY spaced -> NO series (not even).
    g = _grid(10, 20, [(2, 4, 8), (2, 6, 8), (2, 15, 8)])
    cases.append(("3 irregular dots", g, lambda s: len(s) == 0))

    # 4. three collinear+even but DIFFERENT types -> NO series (similarity).
    g = _grid(10, 20, [(2, 4, 8), (2, 8, 5), (2, 12, 3)])
    cases.append(("3 even but mixed types", g, lambda s: len(s) == 0))

    # 5. a row of dots at the END of a bar -> series bound collinear_with the bar.
    bar = [(2, c, 11) for c in range(2, 10)]
    dots = [(2, 12, 8), (2, 15, 8), (2, 18, 8)]
    g = _grid(10, 22, bar + dots)
    cases.append(("dots at end of a bar", g, lambda s: len(s) == 1 and
                  s[0][0] == "CellC8" and "CellC11" in s[0][3]))

    ok = 0
    for name, grid, check in cases:
        s = _perceive(grid)
        passed = check(s)
        ok += passed
        print(f"  [{'PASS' if passed else 'FAIL'}] {name:24s} -> {s}")
    print(f"\n{ok}/{len(cases)} generic cases pass")
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
