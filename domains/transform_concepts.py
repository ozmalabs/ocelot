"""transform_concepts — the jabberwock UNDERSTANDS a TRANSFORM EFFECT.

A general human skill (independent of any one game): recognising that an action
TRANSFORMED an object — its FORM changed — while it is still the SAME underlying
shape (a rotation / reflection / growth of the same thing, not a different thing).
Knowing "action A transforms object O this way" is what then lets a goal DEPLOY
the transform (e.g. rotate until two things match).

GRAPH-NATIVE + SELF-AUTHORED, the same pattern as area / even_collinear / gauge:
I ground only the PERCEPTUAL ATOM — an ORDER-N shape descriptor (the shape reduced
to a fixed profile, run through the agent's OWN order-N operator
`order_n_concepts.nth_order_terms`, so pixel detail / scale drop out and the
META-shape remains). The agent then COMPOSES the concepts itself, via its own
`_spec_to_term`, over two stamped signatures:

  · pose_sig  — the ORDERED order-N differences (quantised) → changes under a
                transform (rotation reorders the profile).
  · meta_sig  — the SORTED order-N differences (quantised) → INVARIANT to
                rotation/reflection (the same shape keeps the same multiset of
                local differences) — the shape's identity.

CONCEPTS the agent composes:
  · shape_transformed(x) := pose_sig(x) != pose_sig_prev(x)   (a transform happened)
  · same_meta_shape(x)   := meta_sig(x) == meta_sig_prev(x)   (still the same shape)
Together: shape_transformed AND same_meta_shape  ⇒  "the SAME shape was transformed
(rotated/flipped), not replaced" — the agent's understanding of the transform effect.
"""
from __future__ import annotations

K = 12   # fixed profile length per axis (so the descriptor is fixed-arity)


def _profile(cells):
    """Reduce a shape (a set of (row,col) cells) to a fixed-length profile: the
    row-occupancy and col-occupancy each resampled to K bins over the shape's
    bounding box. Perceptual reduction (the same class as a centroid); scale and
    absolute position drop out."""
    if not cells:
        return [0.0] * (2 * K)
    rs = [r for r, c in cells]; cs = [c for r, c in cells]
    r0, r1 = min(rs), max(rs); c0, c1 = min(cs), max(cs)
    h = (r1 - r0 + 1); w = (c1 - c0 + 1)
    rowp = [0.0] * K; colp = [0.0] * K
    for r, c in cells:
        rb = int((r - r0) * K / h) if h > 0 else 0
        cb = int((c - c0) * K / w) if w > 0 else 0
        rowp[min(rb, K - 1)] += 1.0
        colp[min(cb, K - 1)] += 1.0
    return rowp + colp


def _order_n(profile, order=2):
    """The order-N finite differences of the profile — via the agent's OWN order-N
    operator (nth_order_terms), evaluated natively. The META structure of the
    shape, with magnitude/detail differenced away."""
    from substrate_rs import Lit
    from domains.order_n_concepts import nth_order_terms
    from substrate.graph import TypedGraph
    ev = TypedGraph()._inner
    terms = nth_order_terms([Lit(float(x)) for x in profile], order)
    return [float(t.evaluate({}, ev)) for t in terms]


def _quant(vals, step=1.0):
    return tuple(int(round(v / step)) for v in vals)


def pose_sig(cells):
    """ORDERED order-N signature — rotation-SENSITIVE (the pose)."""
    return str(_quant(_order_n(_profile(cells)), step=1.0))


def _radial(cells):
    """The shape's radial profile: the distances from the centroid to each cell,
    SORTED and NORMALISED by the max — invariant to rotation, reflection AND scale
    (the identity of the shape), resampled to K bins so it is fixed-length."""
    if not cells:
        return [0.0] * K
    cy = sum(r for r, c in cells) / len(cells)
    cx = sum(c for r, c in cells) / len(cells)
    ds = sorted(((r - cy) ** 2 + (c - cx) ** 2) ** 0.5 for r, c in cells)
    mx = ds[-1] or 1.0
    ds = [d / mx for d in ds]
    # resample the sorted distance list to K bins (mean per bin)
    out = []
    n = len(ds)
    for b in range(K):
        lo = b * n // K; hi = max(lo + 1, (b + 1) * n // K)
        seg = ds[lo:hi] or [ds[min(lo, n - 1)]]
        out.append(sum(seg) / len(seg))
    return out


def meta_sig(cells):
    """Order-N over the rotation/scale-INVARIANT radial profile — the shape's
    IDENTITY: the SAME shape rotated/reflected/grown keeps the same meta_sig."""
    return str(_quant(_order_n(_radial(cells)), step=0.15))


def install_transform_concepts(agent):
    """The agent COMPOSES `shape_transformed` and `same_meta_shape` from the
    stamped pose/meta signatures, via its own _spec_to_term (idempotent)."""
    from substrate import Attr, Eq, Not, Var
    if "shape_transformed" not in agent._concept_nodes:
        # pose changed across the tick = a transform happened
        term = Not(arg=Eq(a=Attr(node=Var("x"), key="pose_sig"),
                          b=Attr(node=Var("x"), key="pose_sig_prev")))
        cid = agent.ground_concept("shape_transformed", term, domain="space")
        agent.mind_graph.node(cid).attrs["because"] = (
            "pose_sig changed across an action — the object's FORM was transformed "
            "(order-N pose descriptor; the agent's own order-N operator)")
    if "same_meta_shape" not in agent._concept_nodes:
        # meta (rotation-invariant) unchanged = still the same underlying shape
        term = Eq(a=Attr(node=Var("x"), key="meta_sig"),
                  b=Attr(node=Var("x"), key="meta_sig_prev"))
        cid = agent.ground_concept("same_meta_shape", term, domain="space")
        agent.mind_graph.node(cid).attrs["because"] = (
            "meta_sig (sorted order-N, rotation/reflection-invariant) unchanged — "
            "the SAME shape, just transformed")
    return {n: agent._concept_nodes[n] for n in ("shape_transformed", "same_meta_shape")}


def stamp_shape(agent, node_id, cells):
    """Perception: stamp an object's pose/meta signatures, carrying the previous
    values to *_prev so the authored concepts can read the change. Mechanical."""
    a = agent.mind_graph.node(node_id).attrs
    a["pose_sig_prev"] = a.get("pose_sig", "")
    a["meta_sig_prev"] = a.get("meta_sig", "")
    a["pose_sig"] = pose_sig(cells)
    a["meta_sig"] = meta_sig(cells)
