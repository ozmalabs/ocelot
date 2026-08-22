"""REGION BOUNDARY AS A SUBGRAPH — gate for `seeds/vision_boundary_trace.json`.

`vision_motion_group` settles grouping by DIFFUSING a label (`mo_flood`): a cell
takes the minimum label among its agreeing neighbours, iterated to fixpoint. Two
consequences follow, and this seed exists because of the second:

  * membership ends up represented as equality of a NUMBER, so reading it back
    is `Count(Filter(NodesOfType(MCell), z.mlabel == R.mlabel))` — a scan of the
    whole field per object;
  * the diffusion's speed depends on how much of it happens WITHIN one drain.
    On the committed engine a great deal does, because later bindings of a rule
    see earlier bindings' writes. Remove that (Stage A's immutable base) and the
    flood degrades to one hop per pass — which is exactly what falsified Stage A
    on the parallax fixtures (`STAGE_A_RESULTS.md` §5f).

The rim is derived from the SAME pairwise predicate with no diffusion at all: an
edge crosses a boundary or it does not, and that is decidable locally. So its
cost is independent of region size AND of the derivation mode.

These tests assert the partition is UNCHANGED. That matters: the rim is a
different REPRESENTATION of the same grouping, not a different grouping
(`WHY_FLOODS_EXIST.md` §2a — an earlier claim that boundary tracing would fix
single-linkage chaining was measured and retracted; chaining is a property of the
relation, not of the algorithm that closes it).
"""
from __future__ import annotations

import collections
import json
import pathlib

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

pytest.importorskip("substrate_rs")
import sys
sys.path.insert(0, str(ROOT / "scripts"))
from substrate.boot_core import boot_core, load_seeds_into   # noqa: E402
import domains.motion_group_world as mgw                      # noqa: E402

TOL = 1.5


def _build(V, seeds):
    s, ag = boot_core()
    load_seeds_into(s, ag, seeds)
    h = mgw.add_mfield(s, V)
    s.set_attr(h["field"], "mtol", TOL)
    s.set_attr(h["field"], "mtol_done", 1.0)
    for c in s.nodes("MCell"):
        s.set_attr(c, "mtol", TOL)
        s.set_attr(c, "mtol_done", 1.0)
        s.set_attr(c, "on_rim", 0.0)
    return s, h


def _flood_groups(s):
    g = collections.defaultdict(set)
    for c in s.nodes("MCell"):
        a = s.node(c)["attrs"]
        g[float(a["mlabel"])].add(int(float(a["cid"])))
    return {frozenset(v) for v in g.values()}


def _rim_groups(s):
    """Regions read off the rim subgraph: components of the graph MINUS the
    `cuts` edges. No label is consulted."""
    cells = list(s.nodes("MCell"))
    cid = {c.value: int(float(s.node(c)["attrs"]["cid"])) for c in cells}
    cut = {(c.value, n.value) for c in cells for n in s.neighbours(c, "cuts")}
    par = {c.value: c.value for c in cells}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for c in cells:
        for n in s.neighbours(c, "neighbour"):
            if (c.value, n.value) not in cut:
                a, b = find(c.value), find(n.value)
                if a != b:
                    par[max(a, b)] = min(a, b)
    g = collections.defaultdict(set)
    for c in cells:
        g[find(c.value)].add(cid[c.value])
    return {frozenset(v) for v in g.values()}


def _rim_run(V):
    """Derive the rim with the FLOOD DISABLED (`mflood=0`) — the point is that
    the boundary needs no diffusion, so the diffusing rule must not run."""
    s, h = _build(V, ["vision_motion_group", "vision_boundary_trace"])
    mgw.set_flag(s, marm=1.0, mcontrast=1.0, mtol_exact=TOL, mflood=0.0)
    return s, s.tick(200_000)


def _flood_run(V):
    s, h = _build(V, ["vision_motion_group"])
    return s, mgw.settle(s, marm=1.0, mcontrast=1.0, mtol_exact=TOL)


def _blocks(n, jump=9.0):
    V = np.zeros((1, n, 2))
    V[0, n // 2:, 1] = jump
    return V


def test_rim_reproduces_the_flood_partition():
    """The rim is a different representation of the SAME grouping."""
    for n in (8, 32, 64):
        V = _blocks(n)
        sf, _ = _flood_run(V)
        sb, _ = _rim_run(V)
        assert _flood_groups(sf) == _rim_groups(sb), f"n={n}: partitions differ"


def test_rim_cost_does_not_grow_with_region_size():
    """The flood propagates one hop per firing; the rim decides each edge
    locally. So the rim's sweep count must not track the region's extent."""
    counts = {n: _rim_run(_blocks(n))[1] for n in (8, 32, 64, 128)}
    assert len(set(counts.values())) == 1, f"rim sweeps varied with size: {counts}"


def test_rim_is_invariant_to_the_derivation_mode():
    """Stage A (immutable derivation base) removes same-round visibility, which
    is what the flood's speed rests on. The rim must not care, because it never
    reads a value another binding of the same rule just wrote.

    This is the property the seed exists for; it is asserted on the rim's own
    output rather than on a sweep count so it cannot pass by accident."""
    import substrate_rs._native as native

    V = _blocks(64)

    def rim_state():
        s, sweeps = _rim_run(V)
        cuts = sum(len(s.neighbours(c, "cuts")) for c in s.nodes("MCell"))
        links = sum(len(s.neighbours(c, "rim_next")) for c in s.nodes("MCell"))
        rim = sum(1 for c in s.nodes("MCell")
                  if float(s.node(c)["attrs"].get("on_rim", 0.0)) > 0.5)
        return (sweeps, cuts, links, rim, _rim_groups(s))

    native.stage_a_enable(False)
    committed = rim_state()
    try:
        native.stage_a_enable(True)
        staged = rim_state()
    finally:
        native.stage_a_enable(False)

    assert committed == staged, f"rim differed by mode: {committed} vs {staged}"


def test_seed_introduces_no_new_constant():
    """§13 discipline, as `vision_motion_group` and `parallax_efference` hold it:
    the only bare literals admissible here are flag guards (0.5) and 0/1
    sentinels. The agreement tolerance must be READ from the field (`mtol`),
    never written into this seed."""
    blob = json.loads((ROOT / "seeds" / "vision_boundary_trace.json").read_text())
    lits = []

    def walk(n):
        if isinstance(n, dict):
            if n.get("type") == "Lit":
                lits.append(n.get("value"))
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(blob["rules"])
    assert set(lits) <= {0.5, 0.0, 1.0}, f"unexpected literal in seed: {sorted(set(lits))}"
    assert json.dumps(blob["rules"]).count('"mtol"') >= 2, "tolerance must come from the field"


def test_crossings_are_one_node_per_disagreement_and_idempotent():
    """`bt_mint_crossing` reifies the boundary itself: one `Crossing` per
    disagreeing pair, not per directed `cuts` edge.

    `cuts` is symmetric because the predicate is, so the naive mint would emit
    two nodes per boundary. The `Lt(R.cid, n.cid)` guard makes one ordering
    canonical and `add_node_if_absent` keyed on (lo, hi) makes re-firing a
    no-op, so this asserts BOTH: the count matches the undirected pair count,
    and a second settle adds nothing."""
    V = _blocks(16)
    s, _ = _rim_run(V)

    pairs = {frozenset((c.value, n.value))
             for c in s.nodes("MCell") for n in s.neighbours(c, "cuts")}
    crossings = list(s.nodes("Crossing"))
    assert len(crossings) == len(pairs), (
        f"{len(crossings)} Crossing nodes for {len(pairs)} disagreeing pairs")

    # every crossing separates exactly the two cells it was minted from
    for x in crossings:
        assert len(s.neighbours(x, "separates")) == 2

    before = len(crossings)
    s.tick(200_000)
    assert len(list(s.nodes("Crossing"))) == before, "mint is not idempotent"


def _crossing_contours(s):
    """Walk `next_crossing` per region -> ordered contours. Mechanical.

    Unlike the rim-CELL walk this needs no start convention, no initial heading
    and no turn preference: crossings chain through `bt_chain_collinear` and
    `bt_chain_perpendicular`, and a crossing of degree > 2 is a real saddle
    rather than a place a convention has to decide."""
    cells = list(s.nodes("MCell"))
    cutset = {(c.value, n.value) for c in cells for n in s.neighbours(c, "cuts")}
    par = {c.value: c.value for c in cells}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for c in cells:
        for n in s.neighbours(c, "neighbour"):
            if (c.value, n.value) not in cutset:
                a, b = find(c.value), find(n.value)
                if a != b:
                    par[max(a, b)] = min(a, b)
    region_of = {c.value: find(c.value) for c in cells}
    sizes = collections.Counter(region_of.values())

    pos, sides = {}, {}
    for x in s.nodes("Crossing"):
        cs = list(s.neighbours(x, "separates"))
        if len(cs) != 2:
            continue
        a = [s.node(c)["attrs"] for c in cs]
        pos[x.value] = ((float(a[0]["ccol"]) + float(a[1]["ccol"])) / 2.0,
                        (float(a[0]["crow"]) + float(a[1]["crow"])) / 2.0)
        sides[x.value] = {region_of[c.value] for c in cs}
    adj = collections.defaultdict(set)
    for x in s.nodes("Crossing"):
        for n in s.neighbours(x, "next_crossing"):
            adj[x.value].add(n.value)
            adj[n.value].add(x.value)

    out = {}
    for reg in sizes:
        mine = [k for k, v in sides.items() if reg in v]
        if len(mine) < 4:
            continue
        sub = {k: (adj[k] & set(mine)) for k in mine}
        start = min(sub, key=lambda k: (pos[k][1], pos[k][0]))
        order, cur, prev = [start], start, None
        while True:
            cands = [n for n in sorted(sub[cur]) if n != prev]
            if not cands:
                break
            nxt = cands[0]
            if nxt == start or nxt in order:
                break
            order.append(nxt)
            prev, cur = cur, nxt
        out[reg] = (sizes[reg], [pos[i] for i in order])
    return out


def _signature(s, points, segments=8):
    return s._inner.evaluate(
        {"type": "StrokeQuantize",
         "points": {"type": "Lit", "value": [[float(a), float(b)] for a, b in points]},
         "segments": segments, "turn_bins": 8, "len_bins": 4,
         "grid": 8, "scale_bins": 4, "invariant_only": True}, {})["signature"]


def test_same_shape_gives_one_signature_and_a_different_shape_does_not():
    """THE PAYOFF a contour has and a label field cannot have.

    Two identical squares at different positions must quantise to the SAME
    invariant signature -- one held shape differing by pose, which is what the
    sd loop is built to exploit. A rectangle must NOT match them.

    Both halves are asserted deliberately. An earlier version of this chain
    reported all regions matching, and it was three DEGENERATE straight-line
    contours matching vacuously (`WHY_FLOODS_EXIST.md`); an equality assertion
    on its own cannot tell that apart from success."""
    V = np.zeros((16, 16, 2))
    V[2:5, 2:5, 1] = 9.0       # square A
    V[2:5, 10:13, 1] = 9.0     # square B, translated
    V[9:12, 2:8, 1] = 9.0      # rectangle C

    s, _ = _rim_run(V)
    contours = _crossing_contours(s)

    squares = [pts for size, pts in contours.values() if size == 9]
    rects = [pts for size, pts in contours.values() if size == 18]
    assert len(squares) == 2, f"expected two 9-cell squares, got {len(squares)}"
    assert len(rects) == 1, f"expected one 18-cell rectangle, got {len(rects)}"

    # the contours must be real closed loops, not degenerate segments
    for pts in squares + rects:
        w = max(p[0] for p in pts) - min(p[0] for p in pts)
        h = max(p[1] for p in pts) - min(p[1] for p in pts)
        assert w > 0 and h > 0, f"degenerate contour, bbox {w}x{h}"

    sig_a, sig_b = (_signature(s, p) for p in squares)
    sig_c = _signature(s, rects[0])
    assert sig_a == sig_b, "same shape, different pose -> signatures must match"
    assert sig_a != sig_c, "square and rectangle must not share a signature"


def test_a_region_contour_goes_through_the_sd_loop(monkeypatch):
    """A region boundary reaches the substrate's OWN codebook, not just a
    signature comparison.

    Mint a quantum from one square's contour; a DIFFERENT region of the same
    shape must then be recognised against it BY NAME, and a genuinely different
    shape must leave a residual (partial coverage, no name) — which is the
    condition `sd_mint_quantum` fires on. That is the whole reason a contour
    beats a label: three regions under `mo_flood` are three unrelated integers
    and there is nothing to recognise.

    `OZMA_SEED_PERSIST_DISABLED` is `teach`'s own guard: it keeps the live-graph
    install (which is what `ShapeDecode` reads) and skips only the write into
    the real seed dir. Stubbing `teach` instead removes the node as well, which
    silently makes this test inert."""
    import domains.stroke_codebook as sk
    monkeypatch.setenv("OZMA_SEED_PERSIST_DISABLED", "1")

    V = np.zeros((16, 16, 2))
    V[2:5, 2:5, 1] = 9.0
    V[2:5, 10:13, 1] = 9.0
    V[9:12, 2:8, 1] = 9.0

    s, _ = _rim_run(V)
    contours = _crossing_contours(s)
    squares = [pts for size, pts in contours.values() if size == 9]
    rects = [pts for size, pts in contours.values() if size == 18]
    assert len(squares) == 2 and len(rects) == 1

    nat = s._inner

    def covered(points):
        sig = sk._quantize(nat, points, segments=sk.DEFAULT_SEGMENTS,
                           turn_bins=sk.DEFAULT_TURN_BINS,
                           len_bins=sk.DEFAULT_LEN_BINS, grid=sk.DEFAULT_GRID,
                           scale_bins=sk.DEFAULT_SCALE_BINS,
                           canonical_pose=True)["signature"]
        base = {"goal": {"type": "Lit", "value": sig}, "beam": 1, "max_steps": 1,
                "cand_k": 1, "wild_objects": False, "type": "ShapeDecode"}
        return (int(nat.evaluate({**base, "field": "covered_count"}, {}) or 0),
                nat.evaluate({**base, "field": "covered_by"}, {}))

    # nothing held yet -> nothing recognised (guards against a vacuous pass)
    assert covered(squares[1]) == (0, None)

    grown = sk.grow_stroke_quantum(s, squares[0], "region_square")
    assert grown["node"] is not None, "mint did not install a node"

    count_b, name_b = covered(squares[1])
    assert name_b == "region_square", f"same shape not recognised: {(count_b, name_b)}"
    assert count_b == grown["signature_relations"]

    count_c, name_c = covered(rects[0])
    assert name_c is None, "a different shape must not be recognised as the square"
    assert 0 < count_c < count_b, f"expected a partial residual, got {count_c}"
