"""motion_group_world — a world adapter for COMMON-MOTION proto-objects
(VISION_MOTION_OBJECTS_PREREG.md).

Mechanical I/O ONLY (CLAUDE.md / PROTOCOL §0): it builds an MField + a grid of
MCell nodes each carrying a MOTION VECTOR, wires the 4-neighbourhood,
blind-writes the OFF-by-default flags, ticks to a fixpoint, and reads the
minted objects back. It makes NO objecthood decision — the tolerance, the
common-fate flood, the reference frame and the mint are ALL rules in
seeds/vision_motion_group.json.

WHAT `vector_field` IS, AND WHAT IT IS NOT
-----------------------------------------
It is the SENSOR. For compressed video the vector matrix is TRANSMITTED, not
computed — H.264 hands over motion vectors plus a residual in hardware, and
computing flow from decoded pixels discards that representation to rebuild a
worse copy of it. **That path is measurably unavailable on this corpus**: the
corpus is HEVC/H.265, and ffmpeg's HEVC decoder does not implement
`export_mvs` (probed over 8 consecutive frames spanning I, P and B pictures —
`MOTION_VECTORS` side data absent on every one, though PyAV exposes the
side-data type and accepts the flag). So this function substitutes a computed
estimate for a transmitted one, and every cost number that follows is for
COMPUTED flow.

It is NOT a percept decision. It occupies exactly the position `quantize()`
occupies for the luminance grid: an opaque external signal turned into the
smallest graph token. The objecthood decisions are all downstream, in rules.
"""
from __future__ import annotations

import numpy as np


def vector_field(a, b, block: int, radius: int | None = None,
                 predict=None):
    """The VECTOR MATRIX between two consecutive frames: one integer
    displacement per block, returned as an (nh, nw, 2) array of `(vy, vx)`.

    `radius = block` BY DEFAULT, AND THIS FALLS OUT OF OVERLAP: beyond a
    displacement of its own extent a block shares no pixels at all with its
    source, so the match stops being coarse and becomes unconstrained. It is a
    geometric limit of the aperture, not a tuned search budget.

    `block` ITSELF IS A DECLARED MAGIC-NUMBER RESIDUAL (§13), exactly as `k`
    is — it is the sensor's aperture and it is NOT claimed to fall out. The
    §13 claim this rung makes is scoped to the GROUPING CRITERION, which is in
    the seed and contains no constant.

    TIE-BREAK: candidate offsets are visited in ascending displacement
    magnitude, so an exact tie keeps the SMALLEST displacement — minimal
    motion explains the data (Occam), not an arbitrary scan order. A raw
    row-major scan would silently bias every tie to the corner offset
    (-r, -r).

    ── MOTION-COMPENSATED (PREDICTIVE-CENTER) SEARCH — block 148000, DEFAULT OFF ──
    `predict` is an OPTIONAL `(nh, nw, 2)` array of per-block PREDICTED integer
    displacements (typically the PREVIOUS frame-pair's `vector_field` output —
    RAW MOTION-FIELD ARRAY DATA, never graph/agent state; the codec P-frame
    move: the optical flow is temporally smooth, so last step's displacement is
    this step's coarse guess). When supplied, each block ALSO searches the same
    ±`r` aperture window CENTERED ON ITS PREDICTION, so the total sensable
    displacement = predicted + residual and a small aperture senses fast motion
    as long as the ACCELERATION (the residual) fits within ±`r`. The aperture is
    thereby DECOUPLED from the velocity.

    This introduces NO new constant: the residual window stays `r` (= `block`),
    the same geometric aperture, and the predicted-vs-plain choice FALLS OUT as
    an argmin — every block keeps whichever candidate (plain OR predicted) has
    the LOWER block-SAD, so the predicted center can never make a block WORSE
    than the plain search (a wrong prediction, e.g. a leading-edge block whose
    predicted center is 0, degrades gracefully to the plain result).

    DEFAULT OFF / BYTE-IDENTITY: `predict=None` (the default) runs ONLY the
    plain search — literally the original code path. A supplied `predict` that
    is ZERO everywhere adds a predicted pass whose candidates coincide exactly
    with the already-evaluated plain candidates and can never STRICTLY beat
    them, so the output is byte-identical to the plain search. MC-search is
    engaged only by a non-None, non-zero `predict`.
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    r = block if radius is None else int(radius)
    H, W = a.shape
    nh, nw = H // block, W // block

    def blocks(x):
        return (x[:nh * block, :nw * block]
                .reshape(nh, block, nw, block).transpose(0, 2, 1, 3))

    A = blocks(a)
    bp = np.pad(b, r, mode="edge")
    best = np.full((nh, nw), np.inf)
    vy = np.zeros((nh, nw))
    vx = np.zeros((nh, nw))

    offsets = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)]
    offsets.sort(key=lambda o: (o[0] * o[0] + o[1] * o[1], o[0], o[1]))

    # PASS 1 — the plain search, centered at zero displacement. This is the
    # ORIGINAL function body, unchanged: it fixes the byte-identity floor.
    for dy, dx in offsets:
        sh = bp[r + dy:r + dy + H, r + dx:r + dx + W]
        sad = np.abs(A - blocks(sh)).sum(axis=(2, 3))
        upd = sad < best
        best = np.where(upd, sad, best)
        vy = np.where(upd, float(dy), vy)
        vx = np.where(upd, float(dx), vx)

    if predict is None:
        return np.stack([vy, vx], axis=-1)

    # PASS 2 — the predicted search, centered per-block on `predict`. Total
    # displacement = predicted center + residual offset; a candidate only wins
    # if it is STRICTLY better (lower SAD) than the plain result, so PASS 2 is
    # the "pick the lower-SAD of predicted-vs-plain" choice, falling out as an
    # argmin — NOT a tuned acceptance threshold. Vectorised across blocks by a
    # per-block gather (edge-clamped indices reproduce PASS 1's edge padding).
    pred = np.asarray(predict, dtype=np.float64)
    py = np.rint(pred[:, :, 0]).astype(np.int64)          # (nh, nw)
    px = np.rint(pred[:, :, 1]).astype(np.int64)
    row_tl = (np.arange(nh) * block).reshape(nh, 1, 1, 1)  # block top-left rows
    col_tl = (np.arange(nw) * block).reshape(1, nw, 1, 1)  # block top-left cols
    ii = np.arange(block).reshape(1, 1, block, 1)          # within-block row
    jj = np.arange(block).reshape(1, 1, 1, block)          # within-block col
    pyb = py.reshape(nh, nw, 1, 1)
    pxb = px.reshape(nh, nw, 1, 1)
    for dy, dx in offsets:
        R = np.clip(row_tl + pyb + dy + ii, 0, H - 1)      # (nh, nw, block, 1)
        C = np.clip(col_tl + pxb + dx + jj, 0, W - 1)      # (nh, nw, 1, block)
        S = b[R, C]                                        # (nh, nw, block, block)
        sad = np.abs(A - S).sum(axis=(2, 3))
        upd = sad < best
        best = np.where(upd, sad, best)
        vy = np.where(upd, (py + dy).astype(np.float64), vy)
        vx = np.where(upd, (px + dx).astype(np.float64), vx)

    return np.stack([vy, vx], axis=-1)


def add_mfield(s, vfield) -> dict:
    """Create an MField + one MCell per block, each carrying its motion vector
    `v = [vy, vx]` as ONE attribute, with 4-neighbour edges. Returns a handle."""
    vfield = np.asarray(vfield, dtype=np.float64)
    nh, nw = vfield.shape[0], vfield.shape[1]
    field = s.add_node("MField", {
        "H": float(nh), "W": float(nw),
        "mtol": 0.0, "mtol_done": 0.0,
        "dom_done": 0.0, "dom_root": -1.0, "dom_v": [0.0, 0.0],
    })
    index: dict = {}
    cell_ids: list = []
    for r in range(nh):
        for c in range(nw):
            cid = float(r * nw + c)
            n = s.add_node("MCell", {
                "crow": float(r), "ccol": float(c),
                "v": [float(vfield[r, c, 0]), float(vfield[r, c, 1])],
                "cid": cid,
                "mlabel": cid,      # init = own cid, exactly like bo_label's glabel
                "pd": 0.0, "pd_done": 0.0,
                # the tolerance the cell APPLIES, broadcast by mo_tol_broadcast.
                # Initialised to 0 so a cell that never received it floods as if
                # under exact equality — a silent partial failure, which is why
                # `assert_settled` checks the broadcast reached every cell.
                "mtol": 0.0, "mtol_done": 0.0,
            })
            # add_edge_unchecked: EXTERNAL world scaffolding (grid membership +
            # the 4-neighbourhood), not an agent claim — the same bypass
            # border_ownership_world / vision_ground / colour_world use.
            s.add_edge_unchecked(field, "has_cell", n)
            index[(r, c)] = n
            cell_ids.append(n)
    for r in range(nh):
        for c in range(nw):
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < nh and 0 <= cc < nw:
                    s.add_edge_unchecked(index[(r, c)], "neighbour", index[(rr, cc)])
    return {"field": field, "cell_ids": cell_ids, "index": index, "H": nh, "W": nw}


def set_flag(s, *, marm: float, mcontrast: float = 1.0,
             mtol_exact: float = 0.0, mflood: float = 0.0) -> None:
    """Blind-write the flags on every MotionParams node. No read, no branch.

    `mcontrast = 0.0` DISARMS the dominant-motion contrast and is the
    dead-instrument control — expressed as graph DATA, never a Python code
    path (PROTOCOL §0)."""
    for p in s.nodes("MotionParams"):
        s.set_attr(p, "marm", float(marm))
        s.set_attr(p, "mcontrast", float(mcontrast))
        s.set_attr(p, "mtol_exact", float(mtol_exact))
        s.set_attr(p, "mflood", float(mflood))


def tick(s, max_steps: int = 200_000) -> int:
    """run_rules to a joint fixpoint. Returns the sweep count."""
    return s.tick(max_steps)


def settle(s, *, marm: float = 1.0, mcontrast: float = 1.0,
           mtol_exact: float = 0.0, max_steps: int = 200_000) -> int:
    """Advance the clock through the two phases and return total sweeps.

    PHASE 1 (`mflood = 0`) derives the field's dispersion and its tolerance and
    broadcasts it. PHASE 2 (`mflood = 1`) runs the common-fate flood, the
    reference frame and the mint, with every cell's tolerance already in place.

    The split is NOT a convenience. Measured on this engine: a binding evaluated
    before the tolerance existed is not fully re-examined after it is written, so
    a single-phase run floods partly under the initial 0.0 and reports a genuine
    fixpoint over an unsettled flood. `assert_settled` is the independent check
    that this actually worked; the caller must not trust the sweep count alone.

    All the adapter does here is raise a flag and advance time — every decision
    is still in the rules."""
    set_flag(s, marm=marm, mcontrast=mcontrast, mtol_exact=mtol_exact, mflood=0.0)
    n = s.tick(max_steps)
    set_flag(s, marm=marm, mcontrast=mcontrast, mtol_exact=mtol_exact, mflood=1.0)
    return n + s.tick(max_steps)


def assert_settled(s, handle: dict) -> dict:
    """INSTRUMENT CHECK, not a decision. Verify from the settled graph that

      (a) the tolerance broadcast reached EVERY cell, and
      (b) the common-fate flood is genuinely at its fixpoint —
          no cell retains an admissible neighbour carrying a smaller label.

    Both are recomputed here in the reader, INDEPENDENTLY of the rules that
    produced them, because this engine has been observed to report a settled
    fixpoint over a demonstrably unsettled flood when a guard reads an
    attribute written mid-fixpoint on a node outside its match neighbourhood.
    A partially-floded field is indistinguishable, by eye, from a legitimately
    fragmented one — and it inflates the object count, which is this rung's
    headline. Returns the counts; the caller aborts on a non-zero verdict."""
    import math
    idx = handle["index"]
    at = {rc: s.node(n)["attrs"] for rc, n in idx.items()}
    no_tol = sum(1 for a in at.values() if float(a.get("mtol_done", 0.0)) < 0.5)
    unsettled = 0
    for (r, c), a in at.items():
        lab = float(a.get("mlabel", -1.0))
        tol = float(a.get("mtol", 0.0))
        v = a.get("v", (0.0, 0.0))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            b = at.get((r + dr, c + dc))
            if b is None:
                continue
            w = b.get("v", (0.0, 0.0))
            d = math.dist((float(v[0]), float(v[1])), (float(w[0]), float(w[1])))
            if d <= tol and float(b.get("mlabel", -1.0)) < lab:
                unsettled += 1
    return {"cells_without_tolerance": int(no_tol), "unsettled_pairs": int(unsettled)}


# --- readouts (pure mechanical queries, no decision) -------------------------
def objects(s) -> list[dict]:
    """Every minted MotionObject, sorted by root."""
    out = []
    for p in s.nodes("MotionObject"):
        a = p if isinstance(p, dict) else s.node(p)["attrs"]
        v = a.get("v", (0.0, 0.0))
        out.append({
            "root": int(round(float(a.get("root", -1.0)))),
            "members": int(round(float(a.get("members", 0.0)))),
            "v": (float(v[0]), float(v[1])),
            "disp": float(a.get("disp", 0.0)),
            "contrast": float(a.get("contrast", 0.0)),
        })
    out.sort(key=lambda d: d["root"])
    return out


def contours(s) -> list[dict]:
    """Every closed boundary the `vision_boundary_trace` seed has traced.

    MECHANICAL, and offered ALONGSIDE `objects()` rather than replacing it. The
    two answer different questions and disagree on real observations: `objects()`
    reports `members`, a CELL COUNT, and a cell count loses ~20% of an object the
    moment it is not lattice-aligned, because the partial-coverage band at its
    edge is cut from both sides and belongs to neither region
    (`WHY_FLOODS_EXIST.md` §6n). The contour integrates that band, so its `area`
    is within 2% and — the property that makes it usable — does not depend on how
    finely the observation happened to be sampled.

    Every value here was decided by a rule; this only walks and reports:

      * which crossings are real boundary  <- `true_boundary` (`bt_true_boundary`)
      * where in the cell each one sits    <- `subcell_t` (`bt_subcell_t`),
                                              absent meaning the midpoint
      * which crossing follows which       <- `next_crossing` (the three chain rules)

    `branches` is reported rather than resolved. A crossing of degree > 2 is a
    genuine saddle — two blocks meeting at a corner, where whether they connect is
    not decidable from adjacency — and the walk's successor choice there is a
    read-order convention, not a fact about the world. A caller that cares must
    look at `branches`; a caller that does not gets a deterministic answer.
    """
    attrs = {c.value: s.node(c)["attrs"] for c in s.nodes("MCell")}
    pos, adj, keep = {}, {}, set()
    for x in s.nodes("Crossing"):
        xa = s.node(x)["attrs"]
        if float(xa.get("true_boundary", 0.0)) <= 0.5:
            continue
        cells = list(s.neighbours(x, "separates"))
        figs = list(s.neighbours(x, "owns_figure"))
        if len(cells) != 2 or not figs:
            continue
        fig = figs[0].value
        oth = cells[1].value if fig == cells[0].value else cells[0].value
        t = float(xa.get("subcell_t", 0.5))
        t = min(2.0, max(0.0, t))
        fc, oc = attrs[fig], attrs[oth]
        fx, fy = float(fc["ccol"]), float(fc["crow"])
        ox, oy = float(oc["ccol"]), float(oc["crow"])
        pos[x.value] = (fx + t * (ox - fx), fy + t * (oy - fy))
        keep.add(x.value)
    for x in s.nodes("Crossing"):
        if x.value not in keep:
            continue
        adj.setdefault(x.value, set())
        for n in s.neighbours(x, "next_crossing"):
            if n.value in keep:
                adj.setdefault(x.value, set()).add(n.value)
                adj.setdefault(n.value, set()).add(x.value)

    out, seen = [], set()
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
        pts = [pos[i] for i in order]
        m = len(pts)
        if m < 3:
            continue
        closed = order[0] in adj[order[-1]]
        shoelace = abs(sum(pts[i][0] * pts[(i + 1) % m][1]
                           - pts[(i + 1) % m][0] * pts[i][1]
                           for i in range(m))) / 2.0
        out.append({
            "points": pts,
            "closed": bool(closed),
            "area": float(shoelace) if closed else 0.0,
            "branches": sum(1 for i in order if len(adj[i]) > 2),
        })
    out.sort(key=lambda d: (-d["area"], -len(d["points"])))
    return out


def field_attr(s, handle: dict, key: str):
    return s.node(handle["field"])["attrs"].get(key)


def labels(s, handle: dict) -> dict:
    """(row, col) -> settled motion label. Mechanical."""
    return {rc: float(s.node(n)["attrs"].get("mlabel", -1.0))
            for rc, n in handle["index"].items()}


def vectors(s, handle: dict) -> dict:
    """(row, col) -> the cell's motion vector, read back from the graph."""
    out = {}
    for rc, n in handle["index"].items():
        v = s.node(n)["attrs"].get("v", (0.0, 0.0))
        out[rc] = (float(v[0]), float(v[1]))
    return out


def support(s, handle: dict, roots) -> dict:
    """root -> the sorted (row, col) set of cells carrying that motion label.
    Membership is recovered exactly as the incumbent recovers proto support:
    `mlabel == root`, because a root cell has `mlabel == cid`."""
    lab = labels(s, handle)
    return {int(root): sorted(rc for rc, l in lab.items()
                              if int(round(l)) == int(root))
            for root in roots}
