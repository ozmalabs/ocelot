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


def _contour_cycles(s):
    """The SAME contours, at O(perimeter): never enumerates the field.

    `_crossing_contours` above is kept as the ORACLE, and its O(area) cost is
    deliberate -- it is what this is checked against. But the union-find it runs
    is not needed for the answer, and measuring it said so plainly: it grew x10.5
    while the shape's boundary grew x3.5, and cost 20x the walk it was feeding.

    Three things that union-find was doing, and where each actually comes from:

      * orientation      <- `owns_figure`, minted locally by `bt_own`;
      * the regions      <- the CYCLES of the `next_crossing` graph. One cycle is
                            one closed boundary. Decomposition is O(crossings);
      * the region SIZE  <- the shoelace area of the cycle's own polygon, plus a
                            correction that is the SAME for every shape. The
                            midpoint contour cuts each convex corner by 1/8 and
                            fills each reflex corner by 1/8; a simple rectilinear
                            polygon has exactly four more convex corners than
                            reflex ones, so the total is always 4 * 1/8 = 1/2 no
                            matter how involved the outline is. Hence
                            `cells = shoelace + 0.5` -- 3x3 gives 8.5 + 0.5 = 9,
                            3x6 gives 17.5 + 0.5 = 18. The area is read off the
                            BOUNDARY; no cell is ever counted.

    Only closed contours are returned. A region clipped by the field edge traces
    an open arc, and closing it needs the border rim -- that case stays with the
    oracle rather than being guessed at here."""
    pos, adj = {}, collections.defaultdict(set)
    for x in s.nodes("Crossing"):
        cs = list(s.neighbours(x, "separates"))
        if len(cs) != 2:
            continue
        a = [s.node(c)["attrs"] for c in cs]
        pos[x.value] = ((float(a[0]["ccol"]) + float(a[1]["ccol"])) / 2.0,
                        (float(a[0]["crow"]) + float(a[1]["crow"])) / 2.0)
        for n in s.neighbours(x, "next_crossing"):
            adj[x.value].add(n.value)
            adj[n.value].add(x.value)

    seen, cycles = set(), []
    for k in sorted(pos):
        if k in seen or k not in adj:
            continue
        order, cur, prev = [k], k, None
        seen.add(k)
        while True:
            cands = [n for n in sorted(adj[cur]) if n != prev and n in pos]
            nxt = next((c for c in cands if c not in seen), None)
            if nxt is None:
                break
            seen.add(nxt)
            order.append(nxt)
            prev, cur = cur, nxt
        if len(order) >= 4 and order[0] in adj[order[-1]]:
            cycles.append(order)

    out = {}
    for i, cyc in enumerate(cycles):
        p = [pos[k] for k in cyc]
        m = len(p)
        shoelace = abs(sum(p[j][0] * p[(j + 1) % m][1] - p[(j + 1) % m][0] * p[j][1]
                           for j in range(m))) / 2.0
        cells = int(round(shoelace + 0.5))
        start = min(range(m), key=lambda j: (p[j][1], p[j][0]))
        out[i] = (cells, p[start:] + p[:start])
    return out


def test_the_contour_needs_no_field_scan_and_agrees_with_the_one_that_does():
    """Identity gate: dropping the cell components changes no contour.

    Compared as point SETS, because the two paths are free to start the same
    closed curve at different places -- and both are read from the same
    `next_crossing` chain, so a disagreement would be a real one."""
    V = np.zeros((16, 16, 2))
    V[2:5, 2:5, 1] = 9.0       # square A
    V[2:5, 10:13, 1] = 9.0     # square B, translated
    V[9:12, 2:8, 1] = 9.0      # rectangle C
    s, _ = _rim_run(V)
    oracle = _crossing_contours(s)
    fast = _contour_cycles(s)

    ref = sorted((sz, tuple(sorted(p))) for sz, p in oracle.values()
                 if sz < 200 and _is_closed(s, p))
    got = sorted((sz, tuple(sorted(p))) for sz, p in fast.values())
    assert got == ref, (
        f"contour differs without the field scan: "
        f"sizes {[a for a, _ in got]} vs oracle {[a for a, _ in ref]}")

    # and the sizes are Pick's theorem, not a cell count
    assert sorted(sz for sz, _ in got) == sorted(sz for sz, _ in ref)


def test_both_walks_agree_where_the_boundary_graph_is_genuinely_ambiguous():
    """The saddle case, pinned.

    Every other fixture in this file has 100% degree-2 crossings, so the walks
    never have to break a tie and the identity gate above cannot exercise one.
    Two blocks meeting at a CORNER do: four crossings come out at degree > 2,
    because whether the blocks connect through that corner is not decidable from
    adjacency alone -- the classic marching-squares saddle.

    Measured before this was written, rather than assumed: both walks resolve it
    the same way and both resolve it correctly, as two separate closed contours
    of 16 cells each. Recorded as a gate so that a future change to either walk's
    tie-breaking has to come past it."""
    V = np.zeros((16, 16, 2))
    V[3:7, 3:7, 1] = 9.0
    V[7:11, 7:11, 1] = 9.0      # touches the first only at a corner
    s, _ = _rim_run(V)

    adj = collections.defaultdict(set)
    for x in s.nodes("Crossing"):
        for n in s.neighbours(x, "next_crossing"):
            adj[x.value].add(n.value)
            adj[n.value].add(x.value)
    saddles = sum(1 for x in s.nodes("Crossing") if len(adj.get(x.value, ())) > 2)
    assert saddles == 4, (
        f"expected the corner to produce 4 ambiguous crossings, got {saddles} -- "
        f"this fixture no longer exercises the tie-break")

    oracle = _crossing_contours(s)
    fast = _contour_cycles(s)
    ref = sorted((sz, tuple(sorted(p))) for sz, p in oracle.values()
                 if sz < 200 and _is_closed(s, p))
    got = sorted((sz, tuple(sorted(p))) for sz, p in fast.values())
    assert got == ref, "the two walks break the saddle tie differently"

    # and the answer itself is right: two 4x4 blocks, kept apart
    assert [sz for sz, _ in got] == [16, 16], (
        f"corner contact merged or split the blocks: sizes {[sz for sz, _ in got]}")


def test_the_contour_cost_follows_the_perimeter_not_the_area():
    """The claim that made this worth writing, enforced.

    Two fields whose AREA differs far more than their boundary does. If the
    contour still tracked the area, the work would grow with the first ratio;
    it must grow with the second."""
    def scene(n):
        """The SAME three shapes in a bigger field: the area grows with n^2, the
        boundary does not grow at all."""
        V = np.zeros((n, n, 2))
        V[2:5, 2:5, 1] = 9.0
        V[2:5, 10:13, 1] = 9.0
        V[9:12, 2:8, 1] = 9.0
        return V

    small, _ = _rim_run(scene(16))
    big, _ = _rim_run(scene(30))

    a_small = len(list(small.nodes("MCell")))
    a_big = len(list(big.nodes("MCell")))
    x_small = len(list(small.nodes("Crossing")))
    x_big = len(list(big.nodes("Crossing")))
    assert a_big / a_small > 2.5 * (x_big / x_small), (
        "fixture does not separate the two ratios, so it cannot tell them apart")

    def touched(s):
        """Nodes the fast path reads. A field scan would put every MCell here."""
        n = 0
        for x in s.nodes("Crossing"):
            n += 1
            n += len(list(s.neighbours(x, "separates")))
            n += len(list(s.neighbours(x, "next_crossing")))
        return n

    t_small, t_big = touched(small), touched(big)
    grew = t_big / t_small
    assert grew <= 1.35 * (x_big / x_small), (
        f"work grew x{grew:.2f}, crossings only x{x_big / x_small:.2f} -- "
        f"the contour is still following the area")
    assert t_big < a_big, (
        f"reads {t_big} nodes for {a_big} cells -- not sub-field")


def _is_closed(s, points):
    """A contour is closed when its first and last crossings are linked. Read
    from the graph, not inferred from the point list."""
    if len(points) < 3:
        return False
    by_pos = {}
    for x in s.nodes("Crossing"):
        cs = list(s.neighbours(x, "separates"))
        if len(cs) != 2:
            continue
        a = [s.node(c)["attrs"] for c in cs]
        by_pos[((float(a[0]["ccol"]) + float(a[1]["ccol"])) / 2.0,
                (float(a[0]["crow"]) + float(a[1]["crow"])) / 2.0)] = x
    first, last = by_pos.get(tuple(points[0])), by_pos.get(tuple(points[-1]))
    if first is None or last is None:
        return False
    linked = {n.value for n in s.neighbours(last, "next_crossing")} | \
             {n.value for n in s.in_neighbours(last, "next_crossing")}
    return first.value in linked


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


def test_a_clipped_region_declines_to_claim_the_whole_shape(monkeypatch):
    """`unknown = absence, first-class`, at the boundary layer.

    A region running off the observed field is genuinely unbounded IN THAT
    OBSERVATION, so `bt_disagree` mints no crossing along the field edge and the
    contour is OPEN. That is correct rather than missing: closing it — by
    minting a virtual `Outside` and joining the border cells to it — would
    manufacture a boundary nothing observed, and would let a partial view assert
    it had seen a whole square.

    What must hold instead is that the partial view produces a RESIDUAL. The
    same 3x3 square, once interior and once clipped by the top edge: the
    interior one closes and is recognised by name; the clipped one covers
    partially and is recognised as NOTHING."""
    import domains.stroke_codebook as sk
    monkeypatch.setenv("OZMA_SEED_PERSIST_DISABLED", "1")

    V = np.zeros((16, 16, 2))
    V[5:8, 5:8, 1] = 9.0        # interior
    V[0:3, 12:15, 1] = 9.0      # clipped by the top edge

    s, _ = _rim_run(V)
    nine = [(pts, closed) for size, pts, closed in
            ((sz, p, _is_closed(s, p)) for sz, p in _crossing_contours(s).values())
            if size == 9]
    closed = [p for p, c in nine if c]
    open_ = [p for p, c in nine if not c]
    assert len(closed) == 1 and len(open_) == 1, (
        f"expected one closed and one open 9-cell region, got "
        f"{len(closed)} / {len(open_)}")

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

    grown = sk.grow_stroke_quantum(s, closed[0], "closed_square")
    full_count, full_name = covered(closed[0])
    assert full_name == "closed_square" and full_count == grown["signature_relations"]

    part_count, part_name = covered(open_[0])
    assert part_name is None, "a clipped view must not claim to be the whole shape"
    assert 0 < part_count < full_count, (
        f"expected a partial residual, got {part_count} of {full_count}")


def _canonical_pose(pts):
    """Centre a contour and rotate its principal axis onto +x.

    A stroke inherits an orientation from the writing direction; a closed
    contour has none, so one must be DERIVED. Scale is deliberately left alone:
    SC+TPS already normalises it (measured), so only orientation is removed."""
    import math
    P = np.array(pts, dtype=float)
    P = P - P.mean(axis=0)
    w, v = np.linalg.eigh(np.cov(P.T))
    axis = v[:, int(np.argmax(w))]
    a = math.atan2(axis[1], axis[0])
    ca, sa = math.cos(-a), math.sin(-a)
    return P @ np.array([[ca, -sa], [sa, ca]]).T


#: The residual symmetry a principal axis cannot resolve: the axis is defined up
#: to sign, and reflection is not fixed by second moments at all. Four discrete
#: candidates, so the verdict is an Argmin over them and the winner IS the pose
#: delta -- rung 1's "one held shape plus a transform", not a fudge factor.
_POSE_CANDIDATES = [np.array([[1, 0], [0, 1]], float),
                    np.array([[-1, 0], [0, -1]], float),
                    np.array([[1, 0], [0, -1]], float),
                    np.array([[-1, 0], [0, 1]], float)]


def _pose_aligned_dist(s, p, q):
    """Minimum ScTpsDist once orientation is factored out. Returns (dist, which)."""
    A, B = _canonical_pose(p), _canonical_pose(q)
    best, arg = None, None
    for i, S in enumerate(_POSE_CANDIDATES):
        d = s._inner.evaluate(
            {"type": "ScTpsDist",
             "a": {"type": "Lit", "value": [[float(x), float(y)] for x, y in A]},
             "b": {"type": "Lit", "value": [[float(x), float(y)] for x, y in (B @ S.T)]}}, {})
        if best is None or d < best:
            best, arg = d, i
    return best, arg


def _rotated_rect(deg, n=25, w=9.0, h=4.5):
    import math
    t = math.radians(deg)
    ct, st = math.cos(-t), math.sin(-t)
    cx = cy = n / 2.0 - 0.5
    V = np.zeros((n, n, 2))
    for r in range(n):
        for c in range(n):
            dx, dy = c - cx, r - cy
            u, v = dx * ct - dy * st, dx * st + dy * ct
            if abs(u) <= w / 2 and abs(v) <= h / 2:
                V[r, c, 1] = 9.0
    return V


def _largest_contour(s):
    best = None
    for size, pts in _crossing_contours(s).values():
        if best is None or (size > best[0] and size < 400):
            best = (size, pts)
    return best[1]


def test_factoring_pose_out_fixes_the_comparators_orientation_blindness():
    """A rotated shape must not read as further away than a different shape.

    `ScTpsDist` normalises scale but not orientation, so a 90-degree rotation --
    whose raster is pixel-identical to the original on a lattice -- scored
    FURTHER (0.39) than a genuinely different shape (0.15). That is worse than
    unhandled. Orientation is a POSE dimension, and the sd loop already treats it
    as one; deriving a canonical orientation from the contour's own principal
    axis and taking the Argmin over the residual discrete symmetry removes it.

    Asserted BOTH ways: rotations of one shape must collapse, and a different
    shape must NOT be collapsed by the same alignment."""
    contours = {deg: _largest_contour(_rim_run(_rotated_rect(deg))[0])
                for deg in (0, 45, 90)}

    square = np.zeros((25, 25, 2))
    square[10:16, 10:16, 1] = 9.0
    sq = _largest_contour(_rim_run(square)[0])

    s, _ = _rim_run(_rotated_rect(0))

    def raw(p, q):
        return s._inner.evaluate(
            {"type": "ScTpsDist",
             "a": {"type": "Lit", "value": [[float(a), float(b)] for a, b in p]},
             "b": {"type": "Lit", "value": [[float(a), float(b)] for a, b in q]}}, {})

    # the defect this fixes: raw distance ranks a rotated SAME shape worse than
    # a different one
    assert raw(contours[0], contours[90]) > raw(contours[0], sq), (
        "expected the raw comparator to be orientation-blind; if this fails the "
        "premise of the test has changed")

    same = [_pose_aligned_dist(s, contours[0], contours[d])[0] for d in contours]
    diff, _ = _pose_aligned_dist(s, contours[0], sq)
    assert max(same) < diff, (
        f"pose-aligned same-shape {max(same):.4f} must beat different-shape {diff:.4f}")
    # and the alignment must not simply collapse everything
    assert diff > 0.05, f"different shapes collapsed to {diff:.4f}"


def _pose_candidates_in_graph(s, agent, q):
    """Publish the residual pose candidates as graph DATA. Mechanical: applying
    a 2x2 symmetry to a point list is geometry, not a decision."""
    B = _canonical_pose(q)
    nodes = []
    for i, S in enumerate(_POSE_CANDIDATES):
        pts = [[float(x), float(y)] for x, y in (B @ S.T)]
        n = s.add_node("PoseCandidate", {"idx": float(i), "points": pts})
        s.add_edge_unchecked(agent, "pose_candidate", n)
        nodes.append(n)
    return nodes


def test_the_pose_verdict_is_one_held_term_not_a_python_loop():
    """The CHOICE among candidate poses belongs to the graph.

    `_pose_aligned_dist` above loops in Python and takes a min — composition in
    Python, which is exactly what this project forbids. The same verdict is one
    Term over held data:

        Attr(Argmin(Neighbours(agent, "pose_candidate"), pc,
                    ScTpsDist(observed, pc.points)), "idx")

    The adapter still computes the candidate geometry (mechanical); the graph
    decides which one wins. This asserts the two agree, so the Python version is
    demonstrably replaceable rather than merely similar."""
    rect0 = _largest_contour(_rim_run(_rotated_rect(0))[0])
    rect90 = _largest_contour(_rim_run(_rotated_rect(90))[0])

    s, _ = _rim_run(_rotated_rect(0))
    agent = s.add_node("Agent", {})
    _pose_candidates_in_graph(s, agent, rect90)

    observed = [[float(x), float(y)] for x, y in _canonical_pose(rect0)]
    term = {"type": "Attr",
            "node": {"type": "Argmin",
                     "source": {"type": "Neighbours",
                                "node": {"type": "Var", "name": "agent"},
                                "edge_type": "pose_candidate", "any_type": False},
                     "var_name": "pc",
                     "value": {"type": "ScTpsDist",
                               "a": {"type": "Lit", "value": observed},
                               "b": {"type": "Attr",
                                     "node": {"type": "Var", "name": "pc"},
                                     "key": "points"}}},
            "key": "idx"}
    graph_choice = s._inner.evaluate(term, {"agent": agent})

    _, python_choice = _pose_aligned_dist(s, rect0, rect90)
    assert int(graph_choice) == int(python_choice), (
        f"graph chose {graph_choice}, python loop chose {python_choice}")


def test_pose_alignment_works_exactly_where_the_lattice_is_faithful():
    """The boundary of what the representation can do, asserted as a boundary.

    Pose alignment removes orientation, and where the lattice renders a rotation
    EXACTLY (multiples of 90 degrees) the same shape then aligns to ~0. Where it
    does not — oblique angles, where the staircase is real — a large residual
    remains that no comparator can remove, because the two rasters are genuinely
    different shapes.

    Measured across 5 shapes x 7 angles (88 same-shape pairs): median distance
    0.0026 at exact lattice rotations against 0.2250 oblique, an 85x ratio,
    monotone in how far the angle sits from a multiple of 90. This pins both
    halves so neither can silently regress: the fix must keep working, and the
    limit must stay honest."""
    rects = {deg: _largest_contour(_rim_run(_rotated_rect(deg))[0])
             for deg in (0, 15, 30, 45, 90)}
    s, _ = _rim_run(_rotated_rect(0))

    exact, _ = _pose_aligned_dist(s, rects[0], rects[90])
    # take the WORST oblique angle, not an arbitrary one: a single angle is not
    # the claim, and 45 degrees happens to align unusually well for a rectangle
    # (0.023) while the population median at that offset is 0.309.
    oblique = max(_pose_aligned_dist(s, rects[0], rects[d])[0]
                  for d in (15, 30, 45))

    assert exact < 0.05, (
        f"an exact lattice rotation must align to ~0, got {exact:.4f}")
    assert oblique > 5 * max(exact, 1e-3), (
        f"the oblique residual is grid damage and must remain visible: "
        f"exact {exact:.4f} vs worst oblique {oblique:.4f}")


# --- orbit recognition: the held thing is a GENERATOR, not a picture ----------
#
# A shape observed at one orientation and the same shape at another are two
# points on ONE FAMILY. Comparing rasterisations directly fights the lattice --
# a rotation changes the raster, and no metric undoes that (measured at length in
# WHY_FLOODS_EXIST.md). Rendering the hypothesis through the SAME sampling makes
# the damage cancel instead, because both sides carry it.
#
# The orbit is DISCRETE: many angles collapse to one raster below the lattice's
# resolving power, so the candidate set is enumerated and deduped rather than
# sampled on an arbitrary angular grid.

def _small_raster(fn, deg, n=13):
    import math
    t = math.radians(deg)
    ct, st = math.cos(-t), math.sin(-t)
    cx = cy = n / 2.0 - 0.5
    V = np.zeros((n, n, 2))
    for r in range(n):
        for c in range(n):
            dx, dy = c - cx, r - cy
            u, v = dx * ct - dy * st, dx * st + dy * ct
            if fn(u, v):
                V[r, c, 1] = 9.0
    return V


def _orbit(fn, cap=16):
    """Distinct rasters of one generator, deduped BEFORE settling so only
    genuinely different members cost work. `cap` bounds test runtime; the
    coverage measurements in the doc use the full sweep."""
    import hashlib
    seen, out = set(), []
    for a in range(0, 180):
        V = _small_raster(fn, a)
        k = hashlib.sha1((V[:, :, 1] > 0).tobytes()).hexdigest()
        if k in seen:
            continue
        seen.add(k)
        out.append((a, V))
        if len(out) >= cap:
            break
    return out


def test_orbit_recognition_snaps_to_distinct_members_and_decides_in_the_graph():
    """Three things at once, each of which was a separate finding:

      * SNAPPING -- 180 angles collapse to far fewer distinct rasters, so the
        candidate set is the reachable set rather than an arbitrary grid;
      * the observation is OFF-manifold (scaled), so this cannot pass by
        containing the answer exactly -- the on-manifold version of this test
        scored 100% and was measuring its own construction;
      * the VERDICT is one held Argmin over candidate nodes, not a Python min.
    """
    bar = lambda u, v: abs(u) <= 3.5 and abs(v) <= 1.5
    cross = lambda u, v: (abs(u) <= 3.5 and abs(v) <= 1.0) or (abs(u) <= 1.0 and abs(v) <= 3.5)

    orbits = {"bar": _orbit(bar), "cross": _orbit(cross)}
    for name, members in orbits.items():
        assert len(members) < 180, f"{name}: dedup did nothing"
        assert len(members) >= 4, f"{name}: orbit collapsed to {len(members)}"

    s, _ = _rim_run(_small_raster(bar, 0))
    agent = s.add_node("Agent", {})
    held = {}
    for name, members in orbits.items():
        for a, V in members:
            sub, _ = _rim_run(V)
            pts = _largest_contour(sub)
            if pts is None or len(pts) < 6:
                continue
            n = s.add_node("OrbitMember",
                           {"shape": name, "angle": float(a),
                            "points": [[float(x), float(y)] for x, y in pts]})
            s.add_edge_unchecked(agent, "orbit_member", n)
            held.setdefault(name, 0)
            held[name] += 1
    assert held.get("bar", 0) >= 3 and held.get("cross", 0) >= 3

    # OFF-manifold observation: 15% larger than anything held, at an angle
    # nothing was stored at exactly.
    obs_fn = lambda u, v: bar(u / 1.15, v / 1.15)
    obs_sub, _ = _rim_run(_small_raster(obs_fn, 37))
    obs = _largest_contour(obs_sub)
    assert obs is not None and len(obs) >= 6

    # THE VERDICT: one Argmin over held candidates, value = ScTpsDist.
    term = {"type": "Attr",
            "node": {"type": "Argmin",
                     "source": {"type": "Neighbours",
                                "node": {"type": "Var", "name": "agent"},
                                "edge_type": "orbit_member", "any_type": False},
                     "var_name": "m",
                     "value": {"type": "ScTpsDist",
                               "a": {"type": "Lit",
                                     "value": [[float(x), float(y)] for x, y in obs]},
                               "b": {"type": "Attr",
                                     "node": {"type": "Var", "name": "m"},
                                     "key": "points"}}},
            "key": "shape"}
    won = s._inner.evaluate(term, {"agent": agent})
    assert won == "bar", f"orbit verdict chose {won!r}, expected 'bar'"


def _rim_degrees(s, region_cells=None):
    """Degree of every boundary crossing in the rim graph. A closed rim is a
    CYCLE, so every crossing must have exactly two neighbours."""
    adj = collections.defaultdict(set)
    for x in s.nodes("Crossing"):
        for n in s.neighbours(x, "next_crossing"):
            adj[x.value].add(n.value)
            adj[n.value].add(x.value)
    return collections.Counter(len(adj[x.value]) for x in s.nodes("Crossing"))


def test_a_diagonal_boundary_chains_into_a_clean_cycle():
    """`bt_chain_perpendicular` must link crossings on ADJACENT sides of a shared
    cell, never on opposite sides.

    Linking every pair at a shared cell also links the two on OPPOSITE sides,
    which is a chord across the rim rather than a rim step. It shows up only on
    boundaries that turn — a rasterised circle came out with 8 of 100 crossings
    at degree 3, and a contour walk took the chord and closed a loop half the
    figure's size (bbox 12x13 for a radius-12 circle) while an axis-aligned
    square was unaffected.

    So the circle is the case that must be asserted; a square passes either way
    and would not have caught it."""
    n, r = 33, 9.0
    circle = lambda u, v: u * u + v * v <= r * r
    square = lambda u, v: abs(u) <= r and abs(v) <= r

    for name, fn in (("circle", circle), ("square", square)):
        s, _ = _rim_run(_small_raster(fn, 0, n=n))
        deg = _rim_degrees(s)
        assert set(deg) == {2}, (
            f"{name}: rim is not a clean cycle, degrees {dict(sorted(deg.items()))}")

    # and the circle's contour must span the figure, not a chord-shortcut loop
    s, _ = _rim_run(_small_raster(circle, 0, n=n))
    pts = _largest_contour(s)
    assert pts is not None
    w = max(p[0] for p in pts) - min(p[0] for p in pts)
    h = max(p[1] for p in pts) - min(p[1] for p in pts)
    assert w > 1.5 * r and h > 1.5 * r, (
        f"circle contour spans {w:.0f}x{h:.0f}, expected about {2*r:.0f} square")


def _disc(R):
    return lambda u, v: u * u + v * v <= R * R


def _scene(spec, n=25):
    """Paint concentric shapes; later entries overwrite earlier ones."""
    V = np.zeros((n, n, 2))
    cx = cy = n / 2.0 - 0.5
    for fn, val in spec:
        for r in range(n):
            for c in range(n):
                if fn(c - cx, r - cy):
                    V[r, c, 1] = val
    return V


def _cycles(s):
    """Boundary cycles from the CROSSING graph alone — it is degree 2
    everywhere, so its components are the cycles and finding them is a walk of
    O(perimeter), not a flood over O(area)."""
    at = {c.value: s.node(c)["attrs"] for c in s.nodes("MCell")}
    pos, own = {}, {}
    for x in s.nodes("Crossing"):
        cs = list(s.neighbours(x, "separates"))
        if len(cs) != 2:
            continue
        a = [at[cs[0].value], at[cs[1].value]]
        pos[x.value] = ((float(a[0]["ccol"]) + float(a[1]["ccol"])) / 2.0,
                        (float(a[0]["crow"]) + float(a[1]["crow"])) / 2.0)
        o = list(s.neighbours(x, "owns_figure"))
        if o:
            own[x.value] = (float(at[o[0].value]["ccol"]), float(at[o[0].value]["crow"]))
    adj = collections.defaultdict(set)
    for x in s.nodes("Crossing"):
        for n_ in s.neighbours(x, "next_crossing"):
            adj[x.value].add(n_.value)
            adj[n_.value].add(x.value)
    seen, out = set(), []
    for k in pos:
        if k in seen:
            continue
        order, cur, prev = [k], k, None
        seen.add(k)
        while True:
            cands = [c for c in sorted(adj[cur]) if c != prev and c in pos and c not in seen]
            if not cands:
                break
            nxt = cands[0]
            seen.add(nxt)
            order.append(nxt)
            prev, cur = cur, nxt
        if len(order) >= 6:
            out.append(order)
    return out, pos, own


def _oriented_turning(cyc, pos, own):
    """Total turning of a cycle, oriented by OWNERSHIP: walk so the owned side
    is on the left. Without that step the sign reports the walk direction, which
    the node-id tie-break makes arbitrary."""
    import math
    if cyc[0] not in own:
        return None
    p0 = np.array(pos[cyc[0]], float)
    step = np.array(pos[cyc[1 % len(cyc)]], float) - p0
    to_fig = np.array(own[cyc[0]], float) - p0
    if float(step[0] * to_fig[1] - step[1] * to_fig[0]) < 0:
        cyc = cyc[::-1]
    P = [np.array(pos[i], float) for i in cyc]
    m = len(P)
    e = [P[(i + 1) % m] - P[i] for i in range(m)]
    a = np.array([math.atan2(x[1], x[0]) for x in e])
    d = a - np.roll(a, 1)
    d = (d + math.pi) % (2 * math.pi) - math.pi
    return float(np.sum(d))


def test_border_ownership_is_local_and_gives_figure_hole_polarity():
    """`bt_own` supplies the one thing the crossing construction lacked — a
    DIRECTED boundary owning its figure — without the flood the eye pays for it
    with.

    `vision_border_ownership` reaches ownership through `bo_bgflood`,
    surroundedness as inward reachability from the frame, which costs a pass per
    hop. A crossing already holds both its cells, so wherever figure and ground
    differ in strength the ownership is decidable AT THE CROSSING.

    Asserted end to end: every crossing owns exactly one side, it is the
    stronger one, and orienting each boundary cycle by that ownership makes an
    annulus read +2pi on its outer boundary and -2pi on its hole. The hole is
    the case that matters — a disc alone passes under any consistent
    convention."""
    import math

    V = _scene([(_disc(9.0), 9.0), (_disc(4.0), 0.0)])
    s, _ = _rim_run(V)
    at = {c.value: s.node(c)["attrs"] for c in s.nodes("MCell")}

    crossings = list(s.nodes("Crossing"))
    assert crossings, "no crossings minted"
    for x in crossings:
        owned = list(s.neighbours(x, "owns_figure"))
        assert len(owned) == 1, f"crossing owns {len(owned)} sides, expected 1"
        cs = list(s.neighbours(x, "separates"))
        mags = {c.value: float(np.linalg.norm([float(v) for v in at[c.value]["v"]]))
                for c in cs}
        assert owned[0].value == max(mags, key=mags.get), "ownership is not the stronger side"

    cycles, pos, own = _cycles(s)
    turns = [t for t in (_oriented_turning(c, pos, own) for c in cycles) if t is not None]
    assert len(turns) >= 2, f"expected an outer boundary and a hole, got {len(turns)} cycles"
    assert any(t > 5.0 for t in turns), f"no figure (+2pi) boundary: {turns}"
    assert any(t < -5.0 for t in turns), f"no hole (-2pi) boundary: {turns}"


def _contour_validity(pts, expect_extent=None):
    """Is this contour a SIMPLE CLOSED CURVE? Returns (ok, total_turning, w, h).

    A closed contour accumulates exactly +/-2pi. Anything else means the walk
    took a shortcut, closed early, or never closed -- and the resulting point
    list still LOOKS like a contour to every downstream comparison."""
    import math
    if len(pts) < 6:
        return False, 0.0, 0.0, 0.0
    P = [np.array(p, float) for p in pts]
    n = len(P)
    e = [P[(i + 1) % n] - P[i] for i in range(n)]
    a = np.array([math.atan2(x[1], x[0]) for x in e])
    d = a - np.roll(a, 1)
    d = (d + math.pi) % (2 * math.pi) - math.pi
    tot = float(np.sum(d))
    w = max(p[0] for p in pts) - min(p[0] for p in pts)
    h = max(p[1] for p in pts) - min(p[1] for p in pts)
    ok = abs(abs(tot) - 2 * math.pi) < 0.5
    if expect_extent is not None:
        ok = ok and w > 0.6 * expect_extent and h > 0.6 * expect_extent
    return ok, tot, w, h


def test_every_extracted_contour_is_a_simple_closed_curve():
    """THE CHECK THAT SHOULD HAVE RUN FIRST.

    Three separate conclusions in `WHY_FLOODS_EXIST.md` were retracted because
    they were measured on contours that were quietly broken: a radius-12 circle
    produced a 27-point contour with bbox 12x13 — half its boundary — and every
    downstream comparison accepted it as a contour and reported numbers.

    The check is five lines and costs nothing: a simple closed curve accumulates
    exactly +/-2pi. It is gated here so that an extraction regression fails
    LOUDLY rather than silently degrading whatever is measured on top of it.

    The battery deliberately includes shapes whose boundaries TURN. The
    adjacent-sides defect was invisible on axis-aligned shapes — a square passed
    both before and after the fix — so a suite of rectangles would have gated
    nothing."""
    n, r = 33, 9.0
    battery = {
        "square (axis-aligned)": lambda u, v: abs(u) <= r and abs(v) <= r,
        "circle (turns everywhere)": lambda u, v: u * u + v * v <= r * r,
        "ellipse (turns, anisotropic)": lambda u, v: (u / r) ** 2 + (v / (r * 0.5)) ** 2 <= 1.0,
        "diamond (45-degree edges)": lambda u, v: abs(u) + abs(v) <= r,
        "triangle (oblique edges)": lambda u, v: (v >= -r * 0.6 and v <= r - abs(u) * 1.4
                                                  and abs(u) <= r),
    }
    bad = []
    for name, fn in battery.items():
        s, _ = _rim_run(_small_raster(fn, 0, n=n))
        pts = _largest_contour(s)
        if pts is None:
            bad.append(f"{name}: no contour extracted")
            continue
        ok, tot, w, h = _contour_validity(pts, expect_extent=1.4 * r)
        if not ok:
            bad.append(f"{name}: {len(pts)} pts, turning {tot:+.2f}, bbox {w:.0f}x{h:.0f}")
    assert not bad, "invalid contours:\n  " + "\n  ".join(bad)
