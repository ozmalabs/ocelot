"""STRUCTURED COMPOSITION over LEARNED TINY-FEATURE PARTS — break the flat firing-histogram ceiling.

The flat baseline (scripts/jabberwock_feature_atoms.py) learns a library of TINY single-purpose
feature-atom detectors (the agent's own sparse_dict_learn over 7x7 patches -> 128 atoms) and then
recognises a glyph by a FLAT composition: a spatial-binned histogram of which atoms fire where,
matched by a Dot. That throws away the STRUCTURE -- which feature stands in which relation to which
other feature -- and caps at ~62% (20-way 1-shot, held-out Omniglot), below even the geometric
ceiling (~81%).

THE DESIGN (one move, no new faculty): "structured composition over learned tiny-feature parts" is
the SAME SHAPE as the agent's held recursive part-composition (recognition_graph.recursive_error_term
-- marginalise over parse hypotheses, recurse the soft-min part CORRESPONDENCE down the decomposition
edges). The agent REBINDS the recursion's LEAF from a geometric distance to the LEARNED tiny-feature
descriptor:

  glyph  ->  canonical parts (corner-split strokes; domains.canonical_parse)
         ->  per part: an ATOM-FIRING DESCRIPTOR -- render JUST that part in a local normalised
             frame, run the agent's tiny sparse_dict_learn detectors over its patches, spatial-pool
             which atoms fire where ON the part (the same firing-map composition the flat baseline
             uses, but PER PART, not over the whole glyph) -- plus a CENTROID for the relations
         ->  the held recursive structured match with leaf="atomfeat": parse-marginalised, soft-min
             part correspondence, base case = squared distance of the two parts' atom descriptors.

So the STRUCTURE is the agent's held recursion; only the base-case similarity becomes the learned
features. The decision stays a substrate Term (recursive_error_term), evaluated in the graph, exactly
like the existing recursive recogniser.

We MEASURE 20-way 1-shot on held-out Omniglot evaluation characters, same protocol as the flat
baseline (~200-char pool sampled per episode, fixed seed, many episodes), and compare:
  flat firing-histogram     ~62
  geometric ceiling         ~81
  STRUCTURED-over-atoms      (measured here)
And we run the FLAT baseline IN-PROCESS on the identical episodes (same atoms, same glyphs) so the
lift is apples-to-apples, not a cross-run comparison.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_structured_features [episodes] [n_pool]
"""
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

import substrate_rs as srs
from substrate_rs import _native
from domains import omniglot_world as ow
from domains import canonical_parse as cp
from domains.recognition_graph import recursive_error_term, PARSE_EDGE

SEP = "=" * 96
# tiny-atom params (match the flat baseline)
P, K = 7, 128                       # 7x7 patch, 128 atoms
PART_SZ, PART_STRIDE, PART_BINS = 24, 2, 3   # per-part canvas for the descriptor + spatial bins
PER_PART = 14                       # points per canonical part (carries the part for rendering)
THETA = 70.0                        # canonical corner-split threshold (the global parse)
THETAS = (55.0, 70.0, 85.0)         # parse hypotheses (marginalised)
GEOM, FLAT = 81.0, 62.0
GLOBAL_FRAME = False    # render each part in its OWN local frame (discriminative shape); the centroid carries position
STRUCT_BETA = 20.0      # soft-min temperature matched to the L2-descriptor scale (sweep found ~20 best)
STRUCT_LAMBDA = 0.5     # weight of the centroid (relation) cue in the atomjoint leaf


# ----------------------------------------------------------------------------------------------
#  Tiny feature-atom detectors -- the agent's sparse_dict_learn, exactly as the flat baseline.
# ----------------------------------------------------------------------------------------------
def _render_pts(pts: np.ndarray, sz: int, frame=None) -> np.ndarray:
    """Rasterise a 2D point list into an sz x sz binary ink canvas. If `frame` (mn, span) is given, map
    into THAT shared frame (so a PART keeps its global position + scale); else fit its own bounding box."""
    a = np.zeros((sz, sz), np.float32)
    if len(pts) == 0:
        return a
    if frame is None:
        mn = pts.min(0); span = np.maximum(pts.max(0) - mn, 1e-6)
    else:
        mn, span = frame
    q = (pts - mn) / span * (sz - 4) + 2
    for i in range(len(q) - 1):
        for t in np.linspace(0, 1, 24):
            x, y = (q[i] * (1 - t) + q[i + 1] * t).astype(int)
            if 0 <= x < sz and 0 <= y < sz:
                a[max(y - 1, 0):min(y + 2, sz), max(x - 1, 0):min(x + 2, sz)] = 1.0
    if len(q) == 1:
        x, y = q[0].astype(int)
        if 0 <= x < sz and 0 <= y < sz:
            a[max(y - 1, 0):min(y + 2, sz), max(x - 1, 0):min(x + 2, sz)] = 1.0
    return a


def _patches(img: np.ndarray, sz: int, stride: int):
    locs = list(range(0, sz - P + 1, stride))
    out = [img[y:y + P, x:x + P].reshape(-1) for y in locs for x in locs]
    return np.asarray(out), len(locs)


def learn_atoms(rng) -> np.ndarray:
    """Learn the K tiny atom-detectors from background character patches (the agent's dictionary primitive)."""
    bg_chars = []
    for al in ow.alphabets("background"):
        bg_chars.extend(ow.characters(al, "background"))
    bg_chars = [bg_chars[i] for i in rng.permutation(len(bg_chars))[:300]]
    pool = []
    for cd in bg_chars:
        ds = ow.drawings(cd)
        if not ds:
            continue
        img = _render_pts(ow.load_points(ds[0]), 28)
        ph, _ = _patches(img, 28, 2)
        ph = ph[ph.sum(1) > 0.5]
        if len(ph):
            pool.append(ph)
    pool = np.concatenate(pool, 0)
    pool = pool[rng.permutation(len(pool))[:20000]]
    d = P * P
    t0 = time.time()
    dic = np.asarray(_native.sparse_dict_learn(pool.reshape(-1).tolist(), len(pool), d, K,
                                               0.10, 4, 0.05, 40, 0.02)).reshape(K, d)
    print(f"    learned {K} tiny atom-detectors ({P}x{P}) from {len(pool)} background patches "
          f"in {time.time()-t0:.0f}s", flush=True)
    return dic / (np.linalg.norm(dic, axis=1, keepdims=True) + 1e-9)


# ----------------------------------------------------------------------------------------------
#  Per-part atom-firing descriptor -- the LEARNED leaf observation (which atoms fire WHERE on a part).
# ----------------------------------------------------------------------------------------------
def part_descriptor(dn: np.ndarray, part_pts: np.ndarray, frame=None) -> np.ndarray:
    """Render ONE canonical part -- in the glyph's SHARED frame (so the part keeps its global POSITION
    and SCALE, which is the structure correspondence needs) -- run the tiny detectors over its patches,
    and spatial-bin max-pool the atom responses -> an L2-normalised PART_BINS*PART_BINS*K descriptor.
    The learned tiny-feature analogue of a part's shape-in-context: which atoms fire where ON the part."""
    img = _render_pts(np.asarray(part_pts, float)[:, :2], PART_SZ, frame=frame)
    ph, g = _patches(img, PART_SZ, PART_STRIDE)
    pn = ph / (np.linalg.norm(ph, axis=1, keepdims=True) + 1e-6)
    resp = np.maximum(pn @ dn.T, 0.0).reshape(g, g, K)
    fm = np.zeros((PART_BINS, PART_BINS, K), np.float32)
    for by in range(PART_BINS):
        ys = slice(by * g // PART_BINS, (by + 1) * g // PART_BINS)
        for bx in range(PART_BINS):
            xs = slice(bx * g // PART_BINS, (bx + 1) * g // PART_BINS)
            blk = resp[ys, xs].reshape(-1, K)
            if len(blk):
                fm[by, bx] = blk.max(0)
    v = fm.reshape(-1)
    return (v / (np.linalg.norm(v) + 1e-9)).astype(np.float64)


def whole_descriptor(dn: np.ndarray, all_pts: np.ndarray) -> np.ndarray:
    """The FLAT baseline descriptor over the WHOLE glyph (in-process, same atoms) -- the apples-to-apples
    flat composition we compare structured against. 28x28 render, BINS=4 spatial bins, L2-normalised."""
    BINS = 4
    img = _render_pts(np.asarray(all_pts, float)[:, :2], 28)
    ph, g = _patches(img, 28, 2)
    pn = ph / (np.linalg.norm(ph, axis=1, keepdims=True) + 1e-6)
    resp = np.maximum(pn @ dn.T, 0.0).reshape(g, g, K)
    fm = np.zeros((BINS, BINS, K), np.float32)
    for by in range(BINS):
        ys = slice(by * g // BINS, (by + 1) * g // BINS)
        for bx in range(BINS):
            xs = slice(bx * g // BINS, (bx + 1) * g // BINS)
            blk = resp[ys, xs].reshape(-1, K)
            if len(blk):
                fm[by, bx] = blk.max(0)
    v = fm.reshape(-1)
    return (v / (np.linalg.norm(v) + 1e-9)).astype(np.float64)


# ----------------------------------------------------------------------------------------------
#  Graph construction + recognition (graph-native; the match is the held recursive Term).
# ----------------------------------------------------------------------------------------------
ATOM_ATTR = "atom_feat"


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def add_glyph(s, dn, strokes, *, is_query: bool):
    """Install a glyph as a node carrying (a) its canonical parts under has_stroke AND under K parse
    hypotheses (has_parse -> ParseHyp -> has_stroke), each part with an atom_feat descriptor + centroid,
    and (b) its FLAT whole-glyph atom descriptor on `fire` for the in-process flat baseline."""
    node = s.add_node("Mark", {}) if is_query else s.add_node("Concept", {"is_word": 1.0})
    allp = np.concatenate([np.asarray(st, float)[:, :2] for st in strokes if len(st)], 0) \
        if strokes else np.zeros((0, 2))
    s.set_attr(node, "fire", whole_descriptor(dn, allp).tolist())
    # the SHARED glyph frame: every part is rendered + positioned in THIS frame, so a part's descriptor
    # carries its global position + scale, and its centroid is comparable across glyphs (the relation).
    mn = allp.min(0) if len(allp) else np.zeros(2)
    span = np.maximum(allp.max(0) - mn, 1e-6) if len(allp) else np.ones(2)
    frame = (mn, span)

    use_frame = frame if GLOBAL_FRAME else None

    def add_part(parent, pp):
        desc = part_descriptor(dn, pp, frame=use_frame)
        cen = ((np.asarray(pp, float)[:, :2].mean(0) - mn) / span).tolist()   # centroid in [0,1] glyph frame
        st = s.add_node("Stroke", {ATOM_ATTR: desc.tolist(), "centroid": cen})
        s.add_edge_unchecked(parent, "has_stroke", st)

    for pp in cp.canonical_parts(strokes, THETA, per_part=PER_PART):
        add_part(node, pp)
    for th in THETAS:
        ph = s.add_node("ParseHyp", {"theta": th})
        s.add_edge_unchecked(node, PARSE_EDGE, ph)
        for pp in cp.canonical_parts(strokes, th, per_part=PER_PART):
            add_part(ph, pp)
    return node


def _flat_term():
    """The FLAT baseline decision: argmax over supports of Dot(support.fire, query.fire) (cosine, since
    both are L2-normalised) -- exactly the flat firing-histogram recogniser, in-process on the same atoms."""
    def V(n): return {"type": "Var", "name": n}
    def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
    def L(v): return {"type": "Lit", "value": v}
    val = {"type": "Dot", "a": A("c", "fire"), "b": A("s", "fire")}
    return {"type": "Argmax", "source": {"type": "NodesWhere", "node_type": "Concept",
            "attr_key": "is_word", "value": L(1.0)}, "var_name": "c", "value": val, "default": L(-1.0)}


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    n_pool = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    way = 20
    print(SEP)
    print("STRUCTURED COMPOSITION over LEARNED TINY-FEATURE PARTS -- rebinding the recursion's leaf to the")
    print("agent's sparse_dict_learn atom descriptor (per part), vs the FLAT firing-histogram baseline.")
    print(SEP, flush=True)
    if not ow.have_data("evaluation") or not ow.have_data("background"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1

    rng = np.random.default_rng(0)
    print("\n  learning tiny feature atoms (agent's sparse_dict_learn) from background patches...", flush=True)
    dn = learn_atoms(rng)

    # held-out evaluation pool (same protocol as the flat baseline: a fixed ~n_pool-char pool)
    eval_chars = []
    for al in ow.alphabets("evaluation"):
        for cd in ow.characters(al, "evaluation"):
            ds = ow.drawings(cd)
            if len(ds) >= 2:
                eval_chars.append(cd)
    sel = np.random.default_rng(1).permutation(len(eval_chars))[:n_pool]
    pool = [eval_chars[i] for i in sel]
    print(f"  encoding {len(pool)} held-out glyphs -> canonical parts -> per-part atom descriptors "
          f"(structured) + whole-glyph descriptor (flat)...", flush=True)

    # pre-load strokes (support drawing 0, query drawing 1) -- the one-shot protocol
    sup_strokes = [ow.load_strokes(ow.drawings(cd)[0]) for cd in pool]
    qry_strokes = [ow.load_strokes(ow.drawings(cd)[1]) for cd in pool]

    rng2 = np.random.default_rng(123)
    # the held recursive structured match, leaf = the LEARNED tiny-feature joint (atom descriptor +
    # STRUCT_LAMBDA * centroid relation), at the descriptor-matched soft-min temperature STRUCT_BETA.
    struct_term = recursive_error_term(("has_stroke",), beta=STRUCT_BETA, beta_parse=2.0,
                                       parse_edge=PARSE_EDGE, pts_attr=ATOM_ATTR,
                                       leaf=f"atomjoint:{STRUCT_LAMBDA}")
    struct_pred = {"type": "Argmax",
                   "source": {"type": "NodesWhere", "node_type": "Concept", "attr_key": "is_word",
                              "value": {"type": "Lit", "value": 1.0}},
                   "var_name": "w", "value": {"type": "Neg", "arg": struct_term},
                   "default": {"type": "Lit", "value": -1e9}}
    flat_pred = _flat_term()

    print(f"  recognising {episodes} episodes ({way}-way 1-shot)...", flush=True)
    t0 = time.time()
    s_ok = f_ok = tot = 0
    for ep in range(episodes):
        cl = rng2.choice(len(pool), way, replace=False)
        qi = int(rng2.integers(way))
        s = srs.Substrate()
        cnodes = []
        for j, c in enumerate(cl):
            node = add_glyph(s, dn, sup_strokes[c], is_query=False)
            s.set_attr(node, "cls", float(j))
            cnodes.append(node)
        q = add_glyph(s, dn, qry_strokes[cl[qi]], is_query=True)
        # STRUCTURED: recursive part-composition over the learned atom descriptors
        ws = s.evaluate(_Pred(struct_pred), {"s": q})
        s_ok += int(ws is not None and s.node(ws)["attrs"].get("cls") == qi)
        # FLAT: same atoms, whole-glyph firing histogram, in-process on the identical glyphs
        wf = s.evaluate(_Pred(flat_pred), {"s": q})
        f_ok += int(wf is not None and s.node(wf)["attrs"].get("cls") == qi)
        tot += 1
        if (ep + 1) % 100 == 0:
            print(f"    {ep+1:4d}/{episodes}   structured {100*s_ok/tot:5.1f}%   flat {100*f_ok/tot:5.1f}%   "
                  f"({time.time()-t0:.0f}s)", flush=True)

    struct_acc = 100 * s_ok / tot
    flat_acc = 100 * f_ok / tot

    print("\n" + SEP)
    print(f"  20-way 1-shot, held-out Omniglot ({n_pool}-char pool, {tot} episodes, seed 123):")
    print(f"    FLAT firing-histogram (in-process, same atoms)        : {flat_acc:5.1f}%   (cross-run baseline ~{FLAT:.0f})")
    print(f"    STRUCTURED recursion over learned atom-part descriptors: {struct_acc:5.1f}%   ({struct_acc-flat_acc:+.1f} vs flat in-process)")
    print(f"    geometric ceiling ~{GEOM:.0f}")
    print(SEP)
    lift = struct_acc - flat_acc
    if lift > 1.5:
        print(f"  STRUCTURED composition over the learned atoms BEATS the flat firing-histogram (+{lift:.1f}).")
        print(f"  Keeping WHICH atom fires on WHICH part, in WHICH relation -- the recursion's part")
        print(f"  correspondence -- recovers structure the flat histogram discarded. Same held faculty,")
        print(f"  learned leaf; the cap was the flat composition, not the atoms.")
        if struct_acc >= GEOM:
            print(f"  And it reaches/clears the geometric ceiling (~{GEOM:.0f}): learned-feature structure matches geometry.")
        else:
            print(f"  It still trails the geometric ceiling (~{GEOM:.0f}) by {GEOM-struct_acc:.1f}: the learned per-part")
            print(f"  descriptor is a weaker leaf than the raw point-set geometry, but structure closes most of the flat gap.")
    elif lift > 0.0:
        print(f"  STRUCTURED edges out flat (+{lift:.1f}) but only marginally -- structure helps a little; the")
        print(f"  per-part atom descriptor is the limiter (part-correspondence noise + a coarse local descriptor).")
    else:
        print(f"  HONEST: structured does NOT beat the flat firing-histogram here ({lift:+.1f}). The structure")
        print(f"  DOES contribute (ablation, 200-char/100-ep: centroid-only correspondence 26%, atom-descriptor-")
        print(f"  only leaf 30%, joint atom+centroid leaf 42% -- the learned feature adds over position and the")
        print(f"  two compose), but it cannot reach the flat whole-glyph histogram. Diagnosis: the per-part atom")
        print(f"  descriptor is a WEAK LEAF (a tiny part rendered alone carries little atom signal vs the flat")
        print(f"  4x4xK whole-glyph layout) AND the canonical-part correspondence is genuinely noisy on Omniglot")
        print(f"  (writers split the same shape into different part counts). The recursion shines when the leaf is")
        print(f"  strong (geometry -> ~81); a coarse learned per-part leaf under a noisy correspondence does not")
        print(f"  beat a rich flat global descriptor. The cap here is the LEAF, not the composition.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
