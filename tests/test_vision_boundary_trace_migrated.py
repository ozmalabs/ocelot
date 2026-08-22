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
