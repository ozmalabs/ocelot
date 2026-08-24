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


def _true_chain(s):
    """Degree distribution and components over the TRUE crossings only."""
    import collections as _c
    tb = lambda x: float(s.node(x)["attrs"].get("true_boundary", 0.0)) > 0.5  # noqa: E731
    ids = {x.value for x in s.nodes("Crossing") if tb(x)}
    adj = _c.defaultdict(set)
    for x in s.nodes("Crossing"):
        if x.value not in ids:
            continue
        for n in s.neighbours(x, "next_crossing"):
            if n.value in ids:
                adj[x.value].add(n.value)
                adj[n.value].add(x.value)
    seen, comps = set(), []
    for k in sorted(ids):
        if k in seen:
            continue
        stack, comp = [k], []
        seen.add(k)
        while stack:
            c = stack.pop()
            comp.append(c)
            for m in adj.get(c, ()):
                if m not in seen:
                    seen.add(m)
                    stack.append(m)
        comps.append(len(comp))
    deg = _c.Counter(len(adj.get(k, ())) for k in ids)
    return ids, deg, comps


@pytest.mark.parametrize("sub", [1, 2, 4, 8])
def test_the_boundary_closes_into_one_curve_at_every_raster(sub):
    """The chain must be a single closed curve, not fragments.

    At super x8 it was not: the partial cell's coverage decides which SIDE of it
    the cut falls on, and at the four cardinal points -- where the boundary is
    tangent to the lattice and coverage peaks -- it flips. The crossing there
    attaches one row out from its neighbours', sharing no cell and with only one
    cross-pair adjacency, which neither `bt_chain_collinear` (needs A~C AND B~D)
    nor `bt_chain_perpendicular` (needs a shared cell) can link. 12 of 108
    crossings were under-connected and the contour broke into 8 components, the
    largest holding 26.

    `bt_chain_diagonal` closes it as a FALLBACK, firing only where a crossing has
    nowhere else to go -- so this also asserts degree 2 exactly, which is what an
    unguarded version destroyed (it reached one component with degree {2:28,
    3:16, 4:64})."""
    V, _ = _soft_disc_scene(41, sub)
    s, _ = _rim_run(V)
    ids, deg, comps = _true_chain(s)
    assert len(ids) > 40, f"sub={sub}: too few true crossings to be a real test"
    assert len(comps) == 1, (
        f"sub={sub}: boundary is in {len(comps)} pieces "
        f"(largest {max(comps)} of {len(ids)})")
    assert set(deg) == {2}, (
        f"sub={sub}: not a clean curve, degrees {dict(sorted(deg.items()))}")


def test_the_diagonal_fallback_adds_nothing_where_the_chain_is_already_closed():
    """It is a FALLBACK, so it must be inert on every fixture that was already
    a single degree-2 curve -- which is every hard-mask scene in this file.

    Asserted by counting the links: a hard mask's chain is fully determined by
    the collinear and perpendicular rules, so the diagonal rule firing there at
    all would mean its guard is not holding.

    `_corner_contact` is deliberately NOT in this list. It carries four genuine
    SADDLE crossings -- two blocks meeting at a corner, where whether they
    connect is not decidable from adjacency -- so degree > 2 there is correct and
    is pinned by its own test. Asserting degree <= 2 over it was this test's own
    first draft, and it failed for that reason rather than for a defect."""
    # n=41: `_soft_disc_scene` places its disc at (12, 20) radius 7, which at
    # n=25 runs off the field edge and traces an OPEN contour with degree-1
    # endpoints -- a fact about the fixture size, not about the rule. That was
    # this test's second wrong draft.
    for name, V in (("three blocks", _blocks_2d()),
                    ("hard disc", _soft_disc_scene(41, 1)[0])):
        s, _ = _rim_run(V)
        ids, deg, comps = _true_chain(s)
        assert set(deg) <= {2}, (
            f"{name}: gained a degree-{max(deg)} crossing -- the diagonal "
            f"fallback fired where the chain was already closed")
        assert len(comps) >= 1 and all(c >= 4 for c in comps), (
            f"{name}: degenerate chain {comps}")


def _offset_rect(n, sub, w, h, dx):
    """A rectangle shifted by `dx` cells, so its edge does not land on a cell
    boundary. At dx=0 the edges fall exactly between cell centres and
    supersampling yields a HARD MASK -- no partial cells at all -- which is why
    an unshifted fixture cannot exercise this at any thickness."""
    V = np.zeros((n, n, 2))
    cx = cy = n / 2.0 - 0.5
    offs = [(i + 0.5) / sub - 0.5 for i in range(sub)]
    for r in range(n):
        for c in range(n):
            hits = 0
            for oy in offs:
                for ox in offs:
                    x, y = c + ox - cx - dx, r + oy - cy - dx
                    hits += (abs(x) <= w / 2 and abs(y) <= h / 2)
            V[r, c, 1] = 9.0 * hits / (sub * sub)
    return V


def _contour_area(s):
    """Largest closed sub-cell contour's shoelace area."""
    at = {c.value: s.node(c)["attrs"] for c in s.nodes("MCell")}
    pos, adj, keep = {}, collections.defaultdict(set), set()
    for x in s.nodes("Crossing"):
        xa = s.node(x)["attrs"]
        if float(xa.get("true_boundary", 0.0)) <= 0.5:
            continue
        cs = list(s.neighbours(x, "separates"))
        figs = list(s.neighbours(x, "owns_figure"))
        if len(cs) != 2 or not figs:
            continue
        a = figs[0].value
        b = cs[1].value if a == cs[0].value else cs[0].value
        pa = np.array([float(at[a]["ccol"]), float(at[a]["crow"])])
        pb = np.array([float(at[b]["ccol"]), float(at[b]["crow"])])
        t = min(2.0, max(0.0, float(xa.get("subcell_t", 0.5))))
        q = pa + t * (pb - pa)
        pos[x.value] = (float(q[0]), float(q[1]))
        keep.add(x.value)
    for x in s.nodes("Crossing"):
        if x.value not in keep:
            continue
        for n in s.neighbours(x, "next_crossing"):
            if n.value in keep:
                adj[x.value].add(n.value)
                adj[n.value].add(x.value)
    seen, best = set(), 0.0
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
        p = [pos[i] for i in order]
        m = len(p)
        if m < 6:
            continue
        best = max(best, abs(sum(p[i][0] * p[(i + 1) % m][1] - p[(i + 1) % m][0] * p[i][1]
                                 for i in range(m))) / 2.0)
    return best


@pytest.mark.parametrize("dx", [0.25, 0.5, 0.75])
def test_extent_comes_from_the_CONTOUR_not_from_counting_cells(dx):
    """How big is this object, on a real observation?

    Counting cells answers this correctly only when the object happens to be
    lattice-aligned. Shift it by any fraction of a cell -- which is the generic
    case, and the only case for a real object -- and the partial-coverage band is
    cut from BOTH sides, excluded from the region, and the count loses 20%. The
    sub-cell contour integrates that band and stays within 2%.

    Both numbers are asserted, because the point is the GAP between them: a gate
    on the contour alone would still pass if cell-counting quietly became right,
    and the claim being made is that it is not."""
    true_area = 15.0 * 7.0
    V = _offset_rect(41, 4, 15.0, 7.0, dx)
    s, _ = _rim_run(V)

    area = _contour_area(s)
    assert abs(area - true_area) / true_area < 0.05, (
        f"contour area {area:.1f} vs true {true_area:.1f} -- the sub-cell "
        f"boundary is not integrating the partial band")

    at = {c.value: s.node(c)["attrs"] for c in s.nodes("MCell")}
    cut = {(c.value, n.value) for c in s.nodes("MCell") for n in s.neighbours(c, "cuts")}
    par = {k: k for k in at}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for c in s.nodes("MCell"):
        for n in s.neighbours(c, "neighbour"):
            if (c.value, n.value) not in cut:
                a, b = find(c.value), find(n.value)
                if a != b:
                    par[max(a, b)] = min(a, b)
    ctr = next((k for k, a in at.items()
                if int(round(float(a["crow"]))) == 20
                and int(round(float(a["ccol"]))) == 20), None)
    cells = collections.Counter(find(k) for k in at)[find(ctr)]
    assert cells < 0.9 * true_area, (
        f"cell count {cells} is within 10% of the true area {true_area:.0f} -- "
        f"this fixture no longer demonstrates why the contour is needed")


def test_subcell_t_stays_on_the_ray_on_REAL_images():
    """The bug no synthetic fixture in this file could find.

    `bt_subcell_t`'s [0,2] bound holds only when the far plateau lies BELOW the
    band cell: the second segment's denominator is |b| - far, so if `b` is a
    LOCAL MINIMUM in its own neighbourhood then far > |b|, the denominator goes
    negative, and t is unbounded. Every synthetic fixture here guaranteed the
    descent by construction, because `far` was always the 0.0 background.

    Measured on BSDS300 natural images before the descent guard existed: t reached
    25.99, 29.99 and 53.50 -- placing a boundary tens of cells from the crossing
    that owns it. Real photometry is the only thing that exposes it, so it is
    gated on real photometry.

    Skipped rather than faked when the corpus is absent; a synthetic stand-in
    would pass while testing nothing."""
    pytest.importorskip("PIL")
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from parallax_real_char import bsds_paths
        paths = bsds_paths()[:4]
    except Exception:
        pytest.skip("BSDS300 corpus absent (data/ not symlinked)")
    if not paths:
        pytest.skip("BSDS300 corpus empty")

    from PIL import Image
    n = 33
    seen_any = False
    for path in paths:
        im = Image.open(path).convert("L")
        w, h = im.size
        im = im.crop(((w - n) // 2, (h - n) // 2, (w - n) // 2 + n, (h - n) // 2 + n))
        V = np.zeros((n, n, 2))
        V[:, :, 1] = 9.0 * np.asarray(im, dtype=float) / 255.0
        s, _ = _rim_run(V)
        ts = [float(s.node(x)["attrs"]["subcell_t"]) for x in s.nodes("Crossing")
              if "subcell_t" in s.node(x)["attrs"]]
        if not ts:
            continue
        seen_any = True
        assert all(0.0 <= t <= 2.0 for t in ts), (
            f"{path.name if hasattr(path, 'name') else path}: t off the ray "
            f"[{min(ts):.2f}, {max(ts):.2f}] -- the descent guard is not holding "
            f"on real photometry")
    if not seen_any:
        pytest.skip("no real patch produced an explicit subcell_t")


def test_a_known_object_is_recovered_from_REAL_texture():
    """Real photometry WITH ground truth: plant a disc of known area in a real
    patch and measure what comes back.

    The BSDS300 copy here ships images without segmentations, so there is no human
    boundary to score against. Planting supplies the truth instead, and keeps the
    confound real -- the background is an actual photograph, not noise with a
    convenient distribution.

    Measured across contrasts: down to contrast 4.0 (2.7x the 1.5 tolerance) real
    texture costs essentially nothing -- area within 0.5% and the boundary within
    0.06 cells of the true circle, indistinguishable from the same disc on a blank
    field. Below that it degrades, and at contrast 2.0 there is no contour at all.
    That limit is set by contrast against `mtol`, NOT by texture: at contrast 3.0
    the disc is no more salient than the 0-3.0 texture it sits in, so failing
    there is correct behaviour and not a defect."""
    pytest.importorskip("PIL")
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from parallax_real_char import bsds_paths
        paths = bsds_paths()[:1]
    except Exception:
        pytest.skip("BSDS300 corpus absent (data/ not symlinked)")
    if not paths:
        pytest.skip("BSDS300 corpus empty")

    from PIL import Image
    n, rad, sub = 41, 9.0, 4
    cx = cy = n / 2.0 - 0.5
    true_area = np.pi * rad * rad

    im = Image.open(paths[0]).convert("L")
    w, h = im.size
    im = im.crop(((w - n) // 2, (h - n) // 2, (w - n) // 2 + n, (h - n) // 2 + n))
    bg = 3.0 * np.asarray(im, dtype=float) / 255.0

    offs = [(i + 0.5) / sub - 0.5 for i in range(sub)]
    V = np.zeros((n, n, 2))
    for r in range(n):
        for c in range(n):
            hits = sum(1 for oy in offs for ox in offs
                       if (c + ox - cx) ** 2 + (r + oy - cy) ** 2 <= rad * rad)
            V[r, c, 1] = bg[r, c] + 6.0 * hits / (sub * sub)

    s, _ = _rim_run(V)
    area = _contour_area(s)
    assert abs(area - true_area) / true_area < 0.05, (
        f"planted disc area {area:.1f} vs true {true_area:.1f} -- real texture is "
        f"defeating the boundary construction at 4x the tolerance")


def test_the_adapter_reader_agrees_with_this_files_own_walk():
    """`motion_group_world.contours()` makes the capability reachable.

    Everything in this arc has been measured through helpers local to this test
    file, so nothing outside it could use the boundary representation at all. The
    adapter reader is the reference implementation a caller would actually reach
    for, and it has to agree with the walk these gates were built on -- otherwise
    the measurements describe code no consumer runs."""
    for sub in (1, 4, 8):
        V, _ = _soft_disc_scene(41, sub)
        s, _ = _rim_run(V)
        got = mgw.contours(s)
        assert got, f"sub={sub}: adapter returned no contour"
        biggest = got[0]
        mine = _contour_area(s)
        assert biggest["closed"], f"sub={sub}: largest contour not closed"
        assert abs(biggest["area"] - mine) < 1e-6, (
            f"sub={sub}: adapter area {biggest['area']:.4f} != this file's "
            f"{mine:.4f} -- the reader and the gates disagree")


def test_the_adapter_reports_saddles_rather_than_resolving_them_silently():
    """A degree > 2 crossing is a genuine ambiguity, so the reader must SAY so.

    Two blocks meeting at a corner produce four such crossings, and whether the
    blocks connect is not decidable from adjacency. The walk still returns a
    deterministic answer -- a read-order convention -- but a caller that cares
    has to be able to tell, so `branches` is reported. A reader that silently
    picked a side would look identical to one on unambiguous input."""
    s, _ = _rim_run(_corner_contact())
    got = mgw.contours(s)
    assert got, "no contours on the corner-contact fixture"
    assert sum(c["branches"] for c in got) > 0, (
        "the corner fixture has four saddle crossings and the reader reported "
        "none -- the ambiguity is being resolved silently")

    plain, _ = _rim_run(_blocks_2d())
    assert sum(c["branches"] for c in mgw.contours(plain)) == 0, (
        "branches reported on a fixture with no saddles")


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


def _soft_disc(n, sub):
    """A disc rasterised with supersampling. `sub=1` is the hard mask every other
    fixture here uses; `sub>1` gives a cell straddling the edge PARTIAL coverage,
    which is the sub-cell information a real blurred observation carries and a
    hard mask throws away."""
    V = np.zeros((n, n, 2))
    cx = cy = n / 2.0 - 0.5
    r = n * 0.35
    offs = [(i + 0.5) / sub - 0.5 for i in range(sub)]
    for row in range(n):
        for col in range(n):
            hits = sum(1 for oy in offs for ox in offs
                       if (col + ox - cx) ** 2 + (row + oy - cy) ** 2 <= r * r)
            V[row, col, 1] = 9.0 * hits / (sub * sub)
    return V


def _true_crossings(s):
    return {x.value for x in s.nodes("Crossing")
            if float(s.node(x)["attrs"].get("true_boundary", 0.0)) > 0.5}


def test_the_true_boundary_rule_is_inert_on_a_hard_mask():
    """`bt_true_boundary` must cost nothing where there is nothing to fix.

    Every other fixture in this file is a hard mask, so this rule has to leave
    them exactly as they were -- every crossing a true boundary, none dropped.
    A rule that starts discarding crossings on hard input would silently change
    every result above it."""
    s, _ = _rim_run(_soft_disc(25, 1))
    total = len(list(s.nodes("Crossing")))
    true_x = _true_crossings(s)
    assert total > 0, "fixture produced no crossings"
    assert len(true_x) == total, (
        f"{total - len(true_x)} crossings dropped on a HARD MASK -- the rule is "
        f"not inert where the boundary is already single")


def test_an_anti_aliased_edge_doubles_the_boundary_and_the_rule_halves_it_back():
    """The finding this rule exists for.

    A soft edge cuts the straddling cell from BOTH sides, so the crossings go UP
    and the partition fragments into slivers -- and no threshold repairs it
    (swept in WHY_FLOODS_EXIST.md 6h: below 3.5 the disc slivers, at 3.5 and
    above the disc merges). The discriminator is structural: a real region has an
    interior cell, a one-cell-wide band has none.

    Asserted as a RATIO against the same disc's hard mask rather than as a
    literal count, so the gate does not go stale if the fixture size changes."""
    hard, _ = _rim_run(_soft_disc(25, 1))
    n_hard = len(list(hard.nodes("Crossing")))

    soft, _ = _rim_run(_soft_disc(25, 4))
    n_soft = len(list(soft.nodes("Crossing")))
    true_x = _true_crossings(soft)

    assert n_soft > 1.5 * n_hard, (
        f"anti-aliasing did not double the boundary ({n_hard} -> {n_soft}); "
        f"this fixture no longer exercises the rule")
    assert len(true_x) < 0.75 * n_soft, (
        f"the rule kept {len(true_x)} of {n_soft} crossings -- it is not "
        f"discarding the second chain")
    assert abs(len(true_x) - n_hard) <= 0.15 * n_hard, (
        f"the rule kept {len(true_x)}, but the hard mask's own boundary is "
        f"{n_hard} -- it should recover that count, not some other one")


def test_the_true_boundary_predicate_needs_no_flood():
    """The predicate must stay LOCAL.

    "Which region is this cell in" is the O(area x iterations) question the rim
    exists to remove, so the rule must not need it. It reads a crossing's figure
    cell and that cell's immediate neighbours -- 2 hops -- and nothing else. This
    asserts the seed's own text: the rule's match binds only `owns_figure` and
    `neighbour`, and its guard counts `cuts` on ONE node."""
    blob = json.loads((ROOT / "seeds" / "vision_boundary_trace.json").read_text())
    rule = next(r for r in blob["rules"] if r["name"] == "bt_true_boundary")
    edges = {m[1] for m in rule["match"]}
    assert edges <= {"owns_figure", "neighbour"}, (
        f"match reaches beyond the crossing's own cells: {sorted(edges)}")
    body = json.dumps(rule)
    assert "mlabel" not in body, "the rule reads the flood's label"
    assert body.count('"Neighbours"') == 1, (
        "more than one neighbour expansion -- the guard is no longer local")


def _soft_disc_scene(n, sub, background=0.0, second=None):
    """A supersampled disc, optionally on a RAISED background or beside a second
    disc at a different value. Both variants exist to break anchors that only
    work on one object over a zero background -- three such were measured and
    discarded before `bt_subcell_t` (WHY_FLOODS_EXIST.md 6j)."""
    V = np.zeros((n, n, 2))
    V[:, :, 1] = background
    offs = [(i + 0.5) / sub - 0.5 for i in range(sub)]
    discs = [((12.0, 20.0), 7.0, 9.0)]
    if second is not None:
        discs.append(((29.0, 20.0), 7.0, second))
    for row in range(n):
        for col in range(n):
            for (cx, cy), rad, val in discs:
                hits = sum(1 for oy in offs for ox in offs
                           if (col + ox - cx) ** 2 + (row + oy - cy) ** 2 <= rad * rad)
                if hits:
                    V[row, col, 1] = background + (val - background) * hits / (sub * sub)
    return V, discs


def _contour_rms(s, discs, use_subcell, clip_t=False):
    """Radial error of the traced contour against the discs that generated it."""
    at = {c.value: s.node(c)["attrs"] for c in s.nodes("MCell")}
    pos, adj, keep = {}, collections.defaultdict(set), set()
    for x in s.nodes("Crossing"):
        xa = s.node(x)["attrs"]
        if float(xa.get("true_boundary", 0.0)) <= 0.5:
            continue
        cs = list(s.neighbours(x, "separates"))
        figs = list(s.neighbours(x, "owns_figure"))
        if len(cs) != 2 or not figs:
            continue
        a = figs[0].value
        b = cs[1].value if a == cs[0].value else cs[0].value
        pa = np.array([float(at[a]["ccol"]), float(at[a]["crow"])])
        pb = np.array([float(at[b]["ccol"]), float(at[b]["crow"])])
        t = float(xa.get("subcell_t", 0.5)) if use_subcell else 0.5
        # t runs along a -> b -> far, so the ray is [0,2]. `clip_t` reproduces
        # the old a->b-only placement, for the comparison gate above.
        t = min(1.0 if clip_t else 2.0, max(0.0, t))
        q = pa + t * (pb - pa)
        pos[x.value] = (float(q[0]), float(q[1]))
        keep.add(x.value)
    for x in s.nodes("Crossing"):
        if x.value not in keep:
            continue
        for n in s.neighbours(x, "next_crossing"):
            if n.value in keep:
                adj[x.value].add(n.value)
                adj[n.value].add(x.value)
    seen, errs = set(), []
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
        if len(order) < 8:
            continue
        P = np.array([pos[i] for i in order])
        (cx, cy), rad, _ = min(discs, key=lambda d: np.linalg.norm(P.mean(axis=0) - np.array(d[0])))
        errs += list(np.linalg.norm(P - np.array([cx, cy]), axis=1) - rad)
    return float(np.sqrt(np.mean(np.square(errs)))) if errs else float("nan")


def test_subcell_t_is_written_on_every_true_crossing_and_stays_on_the_ray():
    """`t` runs along a -> b -> far, so its range is [0,2], not [0,1].

    An earlier version asserted [0,1], which was the CLAMP rather than the
    geometry: with a one-cell band the level is often crossed past b's centre,
    between the band cell and the far plateau, and t up to 2 places it there. A t
    above 1 is meaningful; above 2 would be off the ray, and below 0 behind the
    figure cell. Both terms are bounded by construction, so no clamp is applied
    and this checks the construction rather than a clip."""
    for sub in (4, 8):
        V, _ = _soft_disc_scene(41, sub)
        s, _ = _rim_run(V)
        true_x = [x for x in s.nodes("Crossing")
                  if float(s.node(x)["attrs"].get("true_boundary", 0.0)) > 0.5]
        assert true_x, f"sub={sub}: fixture produced no true crossings"
        # ABSENCE IS MEANINGFUL, so the EFFECTIVE t is what gets checked.
        # `bt_subcell_t` fires only where the profile actually descends
        # (|a| > |b| > far); elsewhere no t is written and a reader falls back to
        # the midpoint, which is the honest answer for a profile that is not a
        # step. An earlier version of this test asserted PRESENCE on every true
        # crossing, which made the descent guard look like a regression when it
        # was a fix.
        ts = [float(s.node(x)["attrs"].get("subcell_t", 0.5)) for x in true_x]
        assert all(0.0 <= t <= 2.0 for t in ts), (
            f"sub={sub}: t off the ray: [{min(ts):.3f}, {max(ts):.3f}]")
        explicit = [x for x in true_x if "subcell_t" in s.node(x)["attrs"]]
        assert explicit, (
            f"sub={sub}: NO crossing carried an explicit subcell_t -- the rule is "
            f"inert here and the placement is silently all-midpoint")


def test_finer_observation_does_not_make_the_boundary_worse():
    """The inversion that clipping `t` to [0,1] caused.

    Interpolating only along a -> b and clipping is a systematic OUTWARD bias at
    every crossing whose band cell is more than half covered -- and there are
    enough of those at x8 that the clipped placement was WORSE there than at x4
    (0.169 against 0.084). Finer observation making the answer worse is the
    signature of information being fought rather than read.

    Asserted as monotonicity rather than against a literal, because the property
    that matters is the ordering, not the number."""
    _, discs = _soft_disc_scene(41, 4)
    by_sub = {}
    for sub in (4, 8):
        V, d = _soft_disc_scene(41, sub)
        by_sub[sub] = _contour_rms(_rim_run(V)[0], d, use_subcell=True)
    assert by_sub[8] <= by_sub[4], (
        f"x8 rms {by_sub[8]:.3f} is worse than x4 {by_sub[4]:.3f} -- finer "
        f"observation is degrading the boundary")

    # and the clipped placement is what it beats
    V8, d8 = _soft_disc_scene(41, 8)
    s8, _ = _rim_run(V8)
    clipped = _contour_rms(s8, d8, use_subcell=True, clip_t=True)
    assert by_sub[8] < 0.6 * clipped, (
        f"piecewise {by_sub[8]:.3f} vs clipped {clipped:.3f} -- the level is not "
        f"being placed on the segment that contains it")


def test_reading_partial_coverage_beats_the_midpoint_on_a_soft_edge():
    """Anti-aliasing is information, not noise.

    Asserted as a RATIO against the same scene's own midpoint placement, so the
    gate cannot go stale on a fixture change."""
    V, discs = _soft_disc_scene(41, 4)
    s, _ = _rim_run(V)
    mid = _contour_rms(s, discs, use_subcell=False)
    sub = _contour_rms(s, discs, use_subcell=True)
    assert sub < 0.5 * mid, (
        f"sub-cell rms {sub:.3f} vs midpoint {mid:.3f} -- partial coverage is "
        f"not being read")


def test_the_anchor_survives_a_raised_background_and_a_second_object():
    """The gate that three earlier anchors failed.

    Anchoring on the field's global extremes scored 0.456 against a midpoint's
    0.274 on two objects at different values -- WORSE than doing nothing. And an
    anchor that looked local was really a hard-coded 0.0, which only a
    zero background flatters. Both scenes here break those, and the accuracy must
    hold, not merely beat the midpoint."""
    _, base_discs = _soft_disc_scene(41, 4)
    base = _contour_rms(_rim_run(_soft_disc_scene(41, 4)[0])[0], base_discs, True)

    V2, d2 = _soft_disc_scene(41, 4, second=4.5)
    two_objects = _contour_rms(_rim_run(V2)[0], d2, True)
    V3, d3 = _soft_disc_scene(41, 4, background=3.0)
    raised = _contour_rms(_rim_run(V3)[0], d3, True)

    for name, got in (("a second object at 4.5", two_objects),
                      ("a raised 3.0 background", raised)):
        assert got <= 1.35 * base, (
            f"accuracy degrades with {name}: {got:.3f} against {base:.3f} on the "
            f"plain scene -- the anchor is assuming something about the scene")


def _block(k, pad=8, h=None):
    """A solid rectangle on a hard mask, sized to order."""
    h = k if h is None else h
    n = max(k, h) + pad
    V = np.zeros((n, n, 2))
    r0, c0 = (n - h) // 2, (n - k) // 2
    V[r0:r0 + h, c0:c0 + k, 1] = 9.0
    return V


def test_no_object_loses_its_boundary_however_thin_it_is():
    """The gate that the first version of `bt_true_boundary` failed.

    That version asked whether the figure cell had a fully-INTERIOR neighbour, as
    a proxy for "is a plateau". `neighbour` is 4-connected, so a block's corner
    cell is DIAGONAL to its interior and has none -- and anything under three
    cells thick has no interior cell at all. Measured on hard masks, where
    nothing should ever be dropped, it deleted 1x1 and 2x2 blocks and 1x9 and 2x9
    bars ENTIRELY, and dropped four corners from every rectilinear shape at every
    size.

    The inertness test above did not catch it because it used a large DISC, whose
    every figure cell does have an interior neighbour. Hence this one: thin and
    small, where a plateau proxy breaks and the value test does not."""
    for label, V in (("1x1", _block(1)), ("2x2", _block(2)), ("3x3", _block(3)),
                     ("13x13", _block(13)), ("1x9 bar", _block(9, h=1)),
                     ("2x9 bar", _block(9, h=2))):
        s, _ = _rim_run(V)
        total = len(list(s.nodes("Crossing")))
        true_x = _true_crossings(s)
        assert total > 0, f"{label}: fixture produced no crossings"
        assert len(true_x) == total, (
            f"{label}: {total - len(true_x)} of {total} crossings discarded on a "
            f"HARD MASK -- an object is losing its boundary for being small or thin")


def test_subcell_t_is_exactly_one_half_on_a_hard_mask():
    """Adoption has to be free. Every existing fixture in this tree is a hard
    mask, so a consumer that starts reading `subcell_t` must get bit-for-bit the
    midpoint it got before.

    It is exact, not approximate, and algebraically so: with no band, `b` IS the
    far plateau, so far == |b| and t = 0.5*(|a|-|b|)/(|a|-|b|) = 0.5. Asserted as
    equality rather than a tolerance, because a tolerance here would hide
    precisely the drift it exists to catch."""
    scenes = {
        "three blocks": _blocks_2d(),
        "hard disc": _soft_disc_scene(25, 1)[0],
        "corner contact": _corner_contact(),
    }
    for name, V in scenes.items():
        s, _ = _rim_run(V)
        # On a hard mask there is no band: `far` equals |b| (both the background),
        # so the descent guard declines and NO t is written -- and a reader's
        # fallback is exactly the midpoint it had before. Either route must give
        # 0.5 exactly, so the EFFECTIVE value is what is asserted.
        true_x = [x for x in s.nodes("Crossing")
                  if float(s.node(x)["attrs"].get("true_boundary", 0.0)) > 0.5]
        assert true_x, f"{name}: no true crossings"
        ts = [float(s.node(x)["attrs"].get("subcell_t", 0.5)) for x in true_x]
        assert all(t == 0.5 for t in ts), (
            f"{name}: hard mask gave an effective t != 0.5 "
            f"(max deviation {max(abs(t - 0.5) for t in ts):.3e})")


def _blocks_2d():
    V = np.zeros((16, 16, 2))
    V[2:5, 2:5, 1] = 9.0
    V[2:5, 10:13, 1] = 9.0
    V[9:12, 2:8, 1] = 9.0
    return V


def _corner_contact():
    V = np.zeros((16, 16, 2))
    V[3:7, 3:7, 1] = 9.0
    V[7:11, 7:11, 1] = 9.0
    return V


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
