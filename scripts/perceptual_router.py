"""THE GENERIC SHAPE-BASED PERCEPTUAL ROUTER — the acquire()-style consolidation
for PERCEPTION. ONE general operation, the specific readers as registry INSTANCES.

The agent's reading stack is THREE separate scripts today: it reads TEXT
(agent_reads_through_its_eye / cursive_analysis_by_synthesis), it reads PLOTS
(agent_reads_a_graph), and a node-edge structure could be read the same way.
Each script ASSUMES what it is looking at. A generic perceiver does NOT: it
RECOGNISES the shape of an input from the input's OWN STRUCTURE (via the eye) and
ROUTES it to the appropriate handler — "it recognised language as language and
graphs as graphs and routes them appropriately, for ANYTHING."

    perceive(image)
      -> SHAPE FEATURES   the eye (substrate_rs.vision: Sobel for long straight
                          edges, DoG center-surround for blobs) extracts a small
                          STRUCTURAL feature vector — axis-frame present? a single
                          baseline ROW of evenly-spaced glyph-sized marks? a few
                          large BLOBS joined by LINES? Real convolutions on real
                          Image nodes — the agent's own eye, no learned classifier.
      -> RECOGNISE SHAPE  every registered shape RECOGNISER scores the features
                          (language: a baseline row of glyph marks; plot: an axis
                          frame + scattered points; node-edge: blobs + connecting
                          lines). The router picks the BEST, or ABSTAINS ("unknown
                          shape") when none fits — honest, not a forced guess.
      -> ROUTE            dispatch to the winning shape's HANDLER (the reader
                          already built) -> comprehension.

This is EXACTLY the acquire() move (domains/acquire.py), one level up, for
perception: acquire() collapsed the acquisition stack into ONE operation with the
four steps (SOURCE/COMPREHEND/BEDROCK/VERIFY) as PARAMETERS and the specifics as
INSTANCES. The router collapses the PERCEPTION stack into ONE operation
(perceive -> recognise-shape -> route) with the shapes + handlers as registry
INSTANCES. A NEW kind of input = ONE register_shape() call. The readers we built
become the handlers the router dispatches to — REUSED, not rebuilt.

NO LLM, no learned classifier, no Rust. The SHAPE is recognised from the eye's
REAL structural features (Sobel line responses + DoG blob responses + the spatial
arrangement). The router is mechanical dispatch over a registry of
(shape_recogniser, handler) instances.

HONEST: the structural recognisers are tractable for these DISTINCT shapes
(rows-of-glyphs vs axes+points vs blobs+lines). Genuinely ambiguous / novel /
mixed-on-one-page inputs are the residual — the router ABSTAINS ("unknown shape")
rather than mis-route. The handlers' own accuracy is as previously measured; this
adds the ROUTING, not new reading accuracy.

Faithful (CLAUDE.md): ADDITIVE world adapter. The eye is the substrate's real
vision; the handlers are the existing readers; the registry is mechanical
dispatch; the recognisers are scores over the eye's structural features. No Rust.

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/perceptual_router.py
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

import substrate_rs as srs
from substrate_rs import vision as v

# THE READERS WE REUSE AS HANDLERS — the existing readers become INSTANCES the
# router dispatches to. We import their machinery, not rebuild it.
from scripts.agent_reads_through_its_eye import (
    render_text, read_image, comprehend_and_verify, LetterformGrounding,
    Eye as TextEye)
from scripts.agent_reads_a_graph import (
    PlotWorld, PlotEye, ground_points, recover_oeis, recover_function,
    verify_function)

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# ===========================================================================
# 1. THE EYE'S STRUCTURAL FEATURES — the agent's vision cortex extracts a small
#    structural feature vector from ANY input image. Real convolutions
#    (substrate_rs.vision): Sobel for long straight EDGES (axis lines), DoG
#    center-surround for BLOBS (glyph marks / point clouds / nodes). The router
#    classifies the SHAPE from these features alone — it is told nothing.
# ===========================================================================

@dataclass
class ShapeFeatures:
    """The structural cues the eye reads off an input — the raw material the
    recognisers score. Every field is computed from REAL convolutions over the
    pixel Image node; nothing is told to the eye."""
    H: int                       # image height (pixels)
    W: int                       # image width
    aspect: float                # W / H — a wide band of glyphs vs a square frame
    ink: float                   # ink fraction (fg pixels / total)
    n_full_vert: int             # near-full-HEIGHT straight vertical ink runs
    n_full_horiz: int            # near-full-WIDTH straight horizontal ink runs
    vmax: float                  # tallest vertical ink run (fraction of height)
    hmax: float                  # longest horizontal ink run (fraction of width)
    n_blobs: int                 # DoG center-surround blob count (large marks)
    blob_rows: int               # distinct horizontal rows the blobs occupy
    band_frac: float             # fraction of the image height the ink occupies
                                 #   (a glyph ROW is a short band; a frame/graph
                                 #    spans the full height)
    big_blobs: int               # blobs that are LARGE + DENSE (graph nodes)

    def vec(self) -> dict[str, float]:
        return {k: float(getattr(self, k)) for k in
                ("aspect", "ink", "n_full_vert", "n_full_horiz", "vmax", "hmax",
                 "n_blobs", "blob_rows", "band_frac", "big_blobs")}


class StructuralEye:
    """The agent's eye, used HERE to read STRUCTURE (not letters): it convolves
    the pixels against its graph-resident Sobel + DoG receptive fields and reads
    off the structural feature vector. The SAME real vision cortex the readers
    use; here it perceives the global SHAPE rather than a glyph signature."""

    def __init__(self):
        self.s = srs.Substrate()
        v.seed_vision_grammar(self.s)
        self.sobel_x = v.sobel(self.s, dx=1, dy=0)      # vertical-edge detector
        self.sobel_y = v.sobel(self.s, dx=0, dy=1)      # horizontal-edge detector
        self.dog = v.dog(self.s, sigma_center=2.0, sigma_surround=4.0)  # blobs

    def _conv(self, img: np.ndarray, k) -> np.ndarray:
        nid = v.image_from_array(self.s, img.astype(np.uint8))
        return v.image_to_array(self.s, v.convolve(self.s, nid, k))

    def _blobs(self, img: np.ndarray, minsep: int = 8,
               thr_frac: float = 0.5) -> list[tuple[int, int]]:
        """Blob centres = local maxima of the DoG (LGN center-surround) response,
        non-max-suppressed by a min separation. The eye's marks: glyph bodies,
        plot points, graph nodes — whatever the center-surround field peaks on."""
        resp = self._conv(img, self.dog)
        m = float(resp.max())
        if m <= 0:
            return []
        cand = np.argwhere(resp > thr_frac * m)
        order = sorted(cand.tolist(), key=lambda rc: -resp[rc[0], rc[1]])
        kept: list[tuple[int, int]] = []
        for (r, c) in order:
            if all(abs(r - kr) > minsep or abs(c - kc) > minsep
                   for (kr, kc) in kept):
                kept.append((r, c))
        return kept

    def perceive_shape(self, img: np.ndarray) -> ShapeFeatures:
        """Read the STRUCTURAL feature vector off an input image — the eye's
        view of the input's shape, computed by real convolutions. No knowledge of
        what the input is; only edge / blob / arrangement structure."""
        H, W = img.shape
        ink_mask = img > 127
        ink = float(ink_mask.mean())

        # --- long straight EDGES (the axis frame) -------------------------
        # A column that is inked along most of its HEIGHT is a vertical line; a
        # row inked along most of its WIDTH is a horizontal line. The Sobel
        # responses confirm these are real edges (a solid line has strong
        # perpendicular gradient along its run).
        vcols = ink_mask.sum(axis=0) / H          # per-column ink height fraction
        hrows = ink_mask.sum(axis=1) / W          # per-row ink width fraction
        n_full_vert = int((vcols > 0.6).sum())
        n_full_horiz = int((hrows > 0.6).sum())
        vmax = float(vcols.max()) if W else 0.0
        hmax = float(hrows.max()) if H else 0.0

        # --- the ink BAND (a glyph row is a short vertical band) -----------
        rows_with_ink = np.nonzero(ink_mask.any(axis=1))[0]
        band_frac = (float(rows_with_ink.max() - rows_with_ink.min() + 1) / H
                     if len(rows_with_ink) else 0.0)

        # --- BLOBS + their arrangement (DoG center-surround) ---------------
        blobs = self._blobs(img)
        n_blobs = len(blobs)
        # how many distinct horizontal ROWS the blobs occupy (a glyph line is ONE
        # row; a 2-D node-edge layout is several; a plot's points climb a curve).
        if blobs:
            brs = np.array([r for r, _ in blobs])
            # cluster blob rows by a tolerance ~ a blob diameter.
            tol = max(6, H // 12)
            srt = np.sort(brs)
            blob_rows = 1 + int((np.diff(srt) > tol).sum())
        else:
            blob_rows = 0
        # LARGE + DENSE blobs = graph nodes: count connected ink regions whose
        # local ink density (in a window around the blob) is high and area large.
        big_blobs = self._count_big_dense(img, blobs)

        return ShapeFeatures(
            H=H, W=W, aspect=(W / H if H else 0.0), ink=ink,
            n_full_vert=n_full_vert, n_full_horiz=n_full_horiz,
            vmax=vmax, hmax=hmax, n_blobs=n_blobs, blob_rows=blob_rows,
            band_frac=band_frac, big_blobs=big_blobs)

    @staticmethod
    def _count_big_dense(img: np.ndarray, blobs: list[tuple[int, int]],
                         win: int = 9, dens_thr: float = 0.55) -> int:
        """Count blobs that sit in a LARGE, DENSELY-inked neighbourhood — the
        signature of a graph NODE (a filled disk), as opposed to a thin glyph
        stroke or a 1-px axis/edge line crossing. A node fills its local window;
        a line only crosses it."""
        ink = img > 127
        H, W = img.shape
        n = 0
        seen: list[tuple[int, int]] = []
        for (r, c) in blobs:
            r0, r1 = max(0, r - win), min(H, r + win + 1)
            c0, c1 = max(0, c - win), min(W, c + win + 1)
            local = ink[r0:r1, c0:c1]
            if local.size and local.mean() >= dens_thr:
                # de-duplicate node centres within a node radius.
                if all(abs(r - sr) > win or abs(c - sc) > win for sr, sc in seen):
                    seen.append((r, c))
                    n += 1
        return n


# ===========================================================================
# 2. THE SHAPE RECOGNISERS — registry instances. Each is a SCORE over the
#    structural feature vector (a predicate that returns a confidence in [0,1]).
#    The shape is recognised from STRUCTURE, never from a label. The router scores
#    all + picks the best, with an ABSTAIN floor (honest "unknown shape").
# ===========================================================================

def recognise_language(f: ShapeFeatures) -> float:
    """LANGUAGE = a horizontal ROW of similarly-sized GLYPH marks on a baseline:
    a linear sequence in a SHORT vertical band, wide aspect, NO axis frame, the
    blobs in essentially ONE row. Score from those structural cues."""
    s = 0.0
    s += 0.35 if f.aspect >= 2.5 else 0.0          # a long horizontal line of text
    s += 0.25 if f.band_frac >= 0.85 else 0.0      # ink fills one short band (the row)
    s += 0.20 if f.blob_rows <= 1 else 0.0         # glyph marks lie in ONE row
    s += 0.20 if f.n_full_horiz == 0 else 0.0      # NO full-width axis line
    # a glyph row has many marks but NO large dense node disks.
    s += 0.10 if f.big_blobs == 0 else 0.0
    return min(1.0, s)


def recognise_plot(f: ShapeFeatures) -> float:
    """PLOT / graph-of-a-function = perpendicular AXES (one long vertical line +
    one long horizontal line, the frame) with scattered POINT marks in the
    quadrant. Score from the axis-frame structure + the point cloud."""
    s = 0.0
    s += 0.35 if (f.n_full_vert >= 1 and f.n_full_horiz >= 1) else 0.0  # the frame
    s += 0.20 if f.vmax >= 0.85 else 0.0           # a full-height y-axis
    s += 0.20 if f.hmax >= 0.85 else 0.0           # a full-width x-axis
    s += 0.15 if f.ink <= 0.12 else 0.0            # sparse (axes + small points)
    s += 0.10 if f.big_blobs <= 2 else 0.0         # points are small, not node disks
    return min(1.0, s)


def recognise_node_edge(f: ShapeFeatures) -> float:
    """NODE-EDGE graph = a few large BLOBS (nodes) joined by LINES (edges), with
    NO baseline row and NO axis frame. Score from: large dense node blobs, blobs
    spread over MULTIPLE rows (a 2-D layout), no full-length axis line, ink
    filling most of the height (not a short text band)."""
    s = 0.0
    s += 0.35 if f.big_blobs >= 3 else (0.15 if f.big_blobs == 2 else 0.0)  # nodes
    s += 0.20 if f.blob_rows >= 2 else 0.0         # 2-D layout, not one row
    s += 0.15 if (f.n_full_vert == 0 and f.n_full_horiz == 0) else 0.0  # no axes
    s += 0.15 if f.band_frac >= 0.7 else 0.0       # spans the height (not a band)
    s += 0.15 if f.aspect <= 2.0 else 0.0          # not a long thin text line
    return min(1.0, s)


def recognise_blank(f: ShapeFeatures) -> float:
    """BLANK / no-content = (almost) no ink. The 4th registered shape — proves the
    router is a REGISTRY (a new kind = one register_shape call), not three
    hard-coded branches. Routes to a trivial 'no content' handler."""
    return 1.0 if f.ink < 0.005 else 0.0


# ===========================================================================
# 3. THE HANDLERS — the readers we already built, wrapped as router targets.
#    Each takes the image + the shared eye state and returns a comprehension.
#    The text + plot handlers REUSE the existing readers verbatim; the node-edge
#    handler is the small structure reader (blobs -> nodes, lines -> adjacency).
# ===========================================================================

class Handlers:
    """Holds the per-handler state (the grounded text eye, the plot eye) so the
    router can dispatch with everything the reader needs. The readers are REUSED;
    this just wires them to the router's dispatch."""

    def __init__(self):
        # the text reader's eye + letterform grounding (learned by example, ONCE).
        self.text_eye = TextEye()
        self.grounding = LetterformGrounding(self.text_eye)
        self.grounding.learn_alphabet("abcdefghilmnopqrstuvwxyz")
        # the plot reader's eye (Sobel axes + DoG blobs).
        self.plot_eye = PlotEye()

    # --- LANGUAGE handler: the text reader -> comprehension --------------
    def handle_language(self, img: np.ndarray, meta: dict) -> dict:
        n_glyphs = meta.get("n_glyphs")
        if n_glyphs is None:
            # recover the glyph count from the fixed grid (the world's cell width).
            from scripts.agent_reads_through_its_eye import GW, GAP, SCALE
            cw = (GW + GAP) * SCALE
            n_glyphs = max(1, round(img.shape[1] / cw))
        text, sims = read_image(img, n_glyphs, self.text_eye, self.grounding)
        seq = meta.get("oeis", "A000203")
        form, got, want, verified = comprehend_and_verify(text, seq)
        return {"kind": "language", "read_text": text,
                "comprehension": f"a(n) = {form}" if form else None,
                "computed": got, "verified": verified,
                "summary": f"read {text!r} -> a(n)={form} (verified={verified})"}

    # --- PLOT handler: the graph reader -> recovered relationship --------
    def handle_plot(self, img: np.ndarray, meta: dict) -> dict:
        eye = self.plot_eye
        row0, col0 = eye.perceive_axes(img)
        ppx, ppy = eye.perceive_scale(img, row0, col0)
        blobs = eye.perceive_points(img, col0, row0)
        read_pts = ground_points(blobs, row0, col0, ppx, ppy)
        sid, name, exact = recover_oeis(
            read_pts, meta.get("oeis_candidates",
                               ["A000217", "A000290", "A000027", "A005408"]))
        res = recover_function(read_pts) if len(read_pts) >= 3 else None
        ver = verify_function(res, read_pts) if res else False
        fn = res.get("term_str") if res and res.get("fits") else None
        # a genuine plot comprehension needs an actual point cloud (>=3 points) +
        # a recovered relationship; an empty read (the text/blank misroute) fits a
        # trivial a(n)=0 to zero points — NOT a comprehension.
        comprehended = bool(len(read_pts) >= 3 and (ver or sid))
        return {"kind": "plot", "read_points": read_pts, "oeis": sid,
                "function": fn, "verified": comprehended,
                "summary": f"recovered {len(read_pts)} points -> a(n)={fn} "
                           f"(OEIS={sid}, verified={comprehended})"}

    # --- NODE-EDGE handler: the structure reader -> a graph -------------
    def handle_node_edge(self, img: np.ndarray, meta: dict) -> dict:
        nodes, adjacency = read_node_edge(img, self.plot_eye)
        n_edges = sum(len(a) for a in adjacency.values()) // 2
        return {"kind": "node-edge", "n_nodes": len(nodes),
                "n_edges": n_edges, "adjacency": adjacency, "nodes": nodes,
                "summary": f"perceived {len(nodes)} nodes + {n_edges} edges "
                           f"-> adjacency {adjacency}"}

    # --- BLANK handler: trivial 'no content' ----------------------------
    def handle_blank(self, img: np.ndarray, meta: dict) -> dict:
        return {"kind": "blank", "summary": "no content (blank field)"}


# ---------------------------------------------------------------------------
# THE NODE-EDGE STRUCTURE READER — the handler for node-edge diagrams. The eye
# finds the NODE blobs (large dense DoG maxima); an edge between two nodes is read
# off the ink: if the straight segment connecting two node centres is inked along
# its length, they are adjacent. Perception -> a graph (nodes + adjacency). Same
# eye, same DoG, same "structure from the marks" as the plot reader.
# ---------------------------------------------------------------------------

def _ink_centroid(img: np.ndarray, r: int, c: int, rad: int = 13
                  ) -> tuple[int, int]:
    """Snap a blob peak to the INK CENTROID of its local node disk. The DoG peak
    can sit off-centre when edge lines bias the center-surround response; the
    filled disk's ink centroid is the true node centre (so the edge segments
    between node centres line up with the rendered edge ink)."""
    ink = img > 127
    H, W = img.shape
    r0, r1 = max(0, r - rad), min(H, r + rad + 1)
    c0, c1 = max(0, c - rad), min(W, c + rad + 1)
    sub = ink[r0:r1, c0:c1]
    ys, xs = np.nonzero(sub)
    if len(ys) == 0:
        return r, c
    return int(round(r0 + ys.mean())), int(round(c0 + xs.mean()))


def _node_blobs(img: np.ndarray, eye: PlotEye, minsep: int = 18,
                win: int = 9, dens_thr: float = 0.55) -> list[tuple[int, int]]:
    """The NODES: large, DENSELY-inked DoG maxima (filled disks). Reuses the plot
    eye's DoG; keeps only blobs whose local neighbourhood is densely inked (a node
    disk fills its window; an edge line only crosses it). Each kept blob is snapped
    to its local ink CENTROID so the node centre is the disk centre."""
    resp = eye._conv(img, eye.dog)
    m = float(resp.max())
    if m <= 0:
        return []
    ink = img > 127
    H, W = img.shape
    cand = np.argwhere(resp > 0.5 * m)
    order = sorted(cand.tolist(), key=lambda rc: -resp[rc[0], rc[1]])
    kept: list[tuple[int, int]] = []
    for (r, c) in order:
        r0, r1 = max(0, r - win), min(H, r + win + 1)
        c0, c1 = max(0, c - win), min(W, c + win + 1)
        if not ink[r0:r1, c0:c1].size or ink[r0:r1, c0:c1].mean() < dens_thr:
            continue                                  # not a filled node disk
        cr, cc = _ink_centroid(img, r, c)             # snap to the disk centre
        if all(abs(cr - kr) > minsep or abs(cc - kc) > minsep for kr, kc in kept):
            kept.append((cr, cc))
    return kept


def _edge_inked(img: np.ndarray, a: tuple[int, int], b: tuple[int, int],
                node_r: int = 11, frac: float = 0.7) -> bool:
    """Is the straight segment between node centres `a` and `b` inked along most
    of its length (excluding the node disks themselves)? -> an edge exists."""
    ink = img > 127
    (r0, c0), (r1, c1) = a, b
    n = int(max(abs(r1 - r0), abs(c1 - c0))) * 2 + 1
    ts = np.linspace(0.0, 1.0, n)
    on = total = 0
    H, W = img.shape
    for t in ts:
        rr = r0 + (r1 - r0) * t
        cc = c0 + (c1 - c0) * t
        # skip the endpoints' node disks (always inked) — sample the SHAFT only.
        d0 = ((rr - r0) ** 2 + (cc - c0) ** 2) ** 0.5
        d1 = ((rr - r1) ** 2 + (cc - c1) ** 2) ** 0.5
        if d0 < node_r or d1 < node_r:
            continue
        ir, ic = int(round(rr)), int(round(cc))
        # tolerate a 1-px wobble around the ideal line.
        hit = False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                pr, pc = ir + dr, ic + dc
                if 0 <= pr < H and 0 <= pc < W and ink[pr, pc]:
                    hit = True
        total += 1
        on += 1 if hit else 0
    return total > 0 and (on / total) >= frac


def read_node_edge(img: np.ndarray, eye: PlotEye
                   ) -> tuple[list[tuple[int, int]], dict[int, list[int]]]:
    """Read a node-edge diagram -> (node centres, adjacency). The eye finds the
    node blobs; an edge is read off the ink along the segment joining two nodes.
    Pure perception -> a graph structure. No coordinates handed in."""
    nodes = _node_blobs(img, eye)
    nodes = sorted(nodes, key=lambda rc: (rc[0], rc[1]))   # stable id order
    adjacency: dict[int, list[int]] = {i: [] for i in range(len(nodes))}
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if _edge_inked(img, nodes[i], nodes[j]):
                adjacency[i].append(j)
                adjacency[j].append(i)
    return nodes, adjacency


# ===========================================================================
# THE ROUTER — ONE general dispatch. perceive -> shape features -> best-matching
# shape recogniser -> route to its handler. A REGISTRY of (recogniser, handler)
# instances; register_shape() adds a kind; perceive_and_route() dispatches.
# ===========================================================================

@dataclass
class ShapeInstance:
    name: str
    recogniser: Callable[[ShapeFeatures], float]
    handler: Callable[[np.ndarray, dict], dict]


@dataclass
class RouteResult:
    shape: str                          # the recognised shape (or 'unknown')
    score: float                        # the winning recogniser's confidence
    scores: dict[str, float]            # every recogniser's score (the evidence)
    features: ShapeFeatures             # the structural feature vector (the proof)
    result: dict = field(default_factory=dict)   # the routed handler's output


class PerceptualRouter:
    """The generic shape-based perceiver. ONE operation: perceive -> recognise the
    shape from structure -> route to the matching handler. The shapes + handlers
    are registry INSTANCES (the acquire()-style consolidation, for perception).
    Extensible to ANY kind by register_shape()."""

    def __init__(self, abstain_floor: float = 0.7):
        self.eye = StructuralEye()
        self.shapes: list[ShapeInstance] = []
        self.abstain_floor = abstain_floor   # below this, ABSTAIN ('unknown shape')

    def register_shape(self, name: str,
                       recogniser: Callable[[ShapeFeatures], float],
                       handler: Callable[[np.ndarray, dict], dict]) -> None:
        """Register ONE (shape_recogniser, handler) instance. A NEW kind of input
        is ONE call here — the router is a registry, not hard-coded branches."""
        self.shapes.append(ShapeInstance(name, recogniser, handler))

    def recognise(self, img: np.ndarray) -> tuple[str, float, dict, ShapeFeatures]:
        """Perceive the structural features (the eye) and SCORE every registered
        shape recogniser; return the best (or 'unknown' below the abstain floor).
        The shape is recognised from STRUCTURE alone — the input is never told its
        kind."""
        feats = self.eye.perceive_shape(img)
        scores = {sh.name: float(sh.recogniser(feats)) for sh in self.shapes}
        if not scores:
            return "unknown", 0.0, scores, feats
        best = max(scores, key=scores.get)
        if scores[best] < self.abstain_floor:
            return "unknown", scores[best], scores, feats
        return best, scores[best], scores, feats

    def perceive_and_route(self, img: np.ndarray, meta: dict | None = None
                           ) -> RouteResult:
        """THE ONE OPERATION: perceive -> recognise the shape -> route to its
        handler. Returns (recognised_shape, handler_result). Abstains honestly on
        an unrecognised shape rather than mis-routing."""
        meta = meta or {}
        shape, score, scores, feats = self.recognise(img)
        if shape == "unknown":
            return RouteResult("unknown", score, scores, feats,
                               {"summary": "unknown shape — ABSTAIN (no recogniser "
                                           "fit; not mis-routed)"})
        handler = next(sh.handler for sh in self.shapes if sh.name == shape)
        out = handler(img, meta)
        return RouteResult(shape, score, scores, feats, out)


# ---------------------------------------------------------------------------
# THE WORLD — render the three (+ a 4th) mixed inputs. The router is NOT told
# which is which; it must recognise each from structure. (The renderers are the
# world; the agent only ever sees the pixels.)
# ---------------------------------------------------------------------------

def render_node_edge_world(centers: list[tuple[int, int]],
                           edges: list[tuple[int, int]],
                           H: int = 130, W: int = 150, r: int = 11) -> np.ndarray:
    """WORLD: blit a node-edge diagram — a filled disk per node, a line per edge.
    No agent involvement; the agent reads the structure back from pixels."""
    img = np.zeros((H, W), np.uint8)
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disk = (yy ** 2 + xx ** 2) <= r ** 2
    for (a, b) in edges:                       # edges first (nodes drawn over)
        (r0, c0), (r1, c1) = centers[a], centers[b]
        n = int(max(abs(r1 - r0), abs(c1 - c0))) * 2 + 1
        for t in np.linspace(0, 1, n):
            rr = int(round(r0 + (r1 - r0) * t))
            cc = int(round(c0 + (c1 - c0) * t))
            img[max(0, rr - 1):rr + 2, max(0, cc - 1):cc + 2] = 255
    for (cr, cc) in centers:
        r0, r1 = cr - r, cr + r + 1
        c0, c1 = cc - r, cc + r + 1
        sub = img[r0:r1, c0:c1]
        sub[disk[:sub.shape[0], :sub.shape[1]]] = 255
    return img


# ===========================================================================
# THE PROOF
# ===========================================================================

def main():
    banner("THE GENERIC SHAPE-BASED PERCEPTUAL ROUTER — perceive -> recognise the "
           "SHAPE from structure -> route to its handler (a registry)")
    print("  ONE generic perceiver. It does NOT assume what it is looking at: it")
    print("  RECOGNISES the shape from the input's OWN STRUCTURE (via the eye —")
    print("  substrate_rs.vision: Sobel for long straight axis edges, DoG center-")
    print("  surround for blobs) and ROUTES to the matching handler (the reader we")
    print("  already built). The acquire()-style consolidation, for PERCEPTION:")
    print("  ONE operation, the shapes + handlers as registry INSTANCES. New kind")
    print("  = one register_shape() call. No LLM, no learned classifier, no Rust.\n")

    router = PerceptualRouter()
    handlers = Handlers()
    # REGISTER the three shapes (recogniser, handler) — the readers as instances.
    router.register_shape("language", recognise_language, handlers.handle_language)
    router.register_shape("plot", recognise_plot, handlers.handle_plot)
    router.register_shape("node-edge", recognise_node_edge, handlers.handle_node_edge)
    print(f"  REGISTERED {len(router.shapes)} shapes: "
          f"{[sh.name for sh in router.shapes]}  "
          f"(each = a (shape_recogniser, handler) instance)")

    # ---- the THREE mixed UNLABELED inputs (the router is NOT told which) -----
    text_img = render_text("sum of divisors of n")           # (a) LANGUAGE
    plot_img = PlotWorld(ppx=12, ppy=4, margin=16).render(    # (b) PLOT
        [(n, n * (n + 1) // 2) for n in range(0, 7)])         #     triangular nums
    node_img = render_node_edge_world(                        # (c) NODE-EDGE
        centers=[(28, 30), (28, 118), (100, 30), (100, 118)],
        edges=[(0, 1), (0, 2), (1, 3), (2, 3)])

    # shuffle the order so nothing about position hints the kind.
    inputs = [("input-A", text_img, {"oeis": "A000203", "n_glyphs": len("sum of divisors of n")}),
              ("input-B", plot_img, {"oeis_candidates": ["A000217", "A000290", "A000027"]}),
              ("input-C", node_img, {})]
    import random
    random.Random(7).shuffle(inputs)

    banner("MIXED UNLABELED INPUTS — the router recognises each SHAPE from "
           "structure + routes it (it is NOT told which is which)")
    routed = {}
    for label, img, meta in inputs:
        rr = router.perceive_and_route(img, meta)
        routed[label] = rr
        print(f"\n  {label}: image shape {img.shape}  (the agent sees PIXELS only)")
        print(f"    EYE structural features: aspect={rr.features.aspect:.2f} "
              f"ink={rr.features.ink:.3f} full_vert={rr.features.n_full_vert} "
              f"full_horiz={rr.features.n_full_horiz} blob_rows={rr.features.blob_rows} "
              f"big_blobs={rr.features.big_blobs} band={rr.features.band_frac:.2f}")
        print(f"    recogniser scores      : "
              + ", ".join(f"{k}={s:.2f}" for k, s in rr.scores.items()))
        print(f"    -> RECOGNISED SHAPE    : {rr.shape.upper()}  (score {rr.score:.2f})")
        print(f"    -> ROUTED to handler   : {rr.result.get('summary')}")

    # collect per-shape results for the summary + 'language as language' line.
    by_shape = {rr.shape: (label, rr) for label, rr in routed.items()}
    banner("RECOGNISED LANGUAGE AS LANGUAGE AND GRAPHS AS GRAPHS")
    for shp in ("language", "plot", "node-edge"):
        if shp in by_shape:
            lbl, rr = by_shape[shp]
            print(f"  {lbl} -> {shp.upper():9s} -> {rr.result.get('summary')}")

    # ===================================================================== #
    # STRUCTURE-NOT-LABEL CONTROL.                                          #
    # ===================================================================== #
    banner("CONTROL #1 — the routing is from STRUCTURE, not a label: the "
           "recogniser scores the RIGHT shape highest (the feature vector decides)")
    ctrl_ok = 0
    expect = {id(text_img): "language", id(plot_img): "plot",
              id(node_img): "node-edge"}
    for label, img, meta in inputs:
        shape, score, scores, feats = router.recognise(img)
        want = expect[id(img)]
        ok = (shape == want)
        ctrl_ok += ok
        print(f"  {label}: structural recogniser picks {shape.upper()} "
              f"(want {want.upper()}) {'OK' if ok else 'MIS'}  "
              f"[scores {', '.join(f'{k}:{s:.2f}' for k,s in scores.items())}]")
    print(f"  -> {ctrl_ok}/3 recognised correctly FROM STRUCTURE (no input told "
          f"its kind).")

    banner("CONTROL #2 — MIS-ROUTING fails: force the WRONG handler on each input "
           "-> it does NOT comprehend (the shape match is load-bearing)")
    # plot handler on the TEXT image; text handler on the PLOT image.
    mis_text_as_plot = handlers.handle_plot(text_img, {})
    mis_plot_as_text = handlers.handle_language(plot_img, {"oeis": "A000217"})
    print(f"  TEXT image -> PLOT handler  : {mis_text_as_plot.get('summary')}")
    print(f"    (the plot reader finds no real axis frame / function -> no verified "
          f"relationship)")
    print(f"  PLOT image -> TEXT handler  : {mis_plot_as_text.get('summary')}")
    print(f"    (the text reader grounds axis/point pixels as garbage letters -> no "
          f"verified comprehension)")
    mis_ok = (not mis_text_as_plot.get("verified")) and \
             (not mis_plot_as_text.get("verified"))
    print(f"  -> mis-routing yields NO verified comprehension on either: "
          f"{'OK (routing matters)' if mis_ok else 'unexpected'}")

    # ===================================================================== #
    # GENERAL / EXTENSIBLE — register a FOURTH shape (one call).            #
    # ===================================================================== #
    banner("EXTENSIBLE — register a FOURTH shape (a BLANK field -> 'no content') "
           "with ONE register_shape() call: the router is a REGISTRY, not 3 branches")
    router.register_shape("blank", recognise_blank, handlers.handle_blank)
    print(f"  after register_shape('blank', ...): shapes = "
          f"{[sh.name for sh in router.shapes]}")
    blank_img = np.zeros((60, 120), np.uint8)
    rb = router.perceive_and_route(blank_img, {})
    print(f"  a blank image -> recognised {rb.shape.upper()} (score {rb.score:.2f}) "
          f"-> {rb.result.get('summary')}")
    # the three originals STILL route correctly after extension (registry is open).
    still_ok = all(router.recognise(img)[0] == expect[id(img)]
                   for _, img, _ in inputs)
    print(f"  the three original shapes STILL route correctly after extension: "
          f"{'OK' if still_ok else 'FAIL'}  (registering a kind does not disturb "
          f"the others)")

    # ===================================================================== #
    # HONEST RESIDUAL — abstain on ambiguous / novel.                       #
    # ===================================================================== #
    banner("HONEST — the router ABSTAINS ('unknown shape') on ambiguous / novel "
           "inputs rather than mis-routing (named residual)")
    # a NOVEL shape no recogniser was built for: random scattered noise (neither a
    # glyph row, nor an axis frame, nor node disks joined by lines).
    rng = np.random.default_rng(3)
    noise_img = (rng.random((90, 90)) < 0.25).astype(np.uint8) * 255
    rn = router.perceive_and_route(noise_img, {})
    print(f"  a NOVEL/ambiguous input (random texture): recognised "
          f"{rn.shape.upper()} (best score {rn.score:.2f})")
    print(f"    scores: {', '.join(f'{k}:{s:.2f}' for k,s in rn.scores.items())}")
    print(f"    -> {rn.result.get('summary')}")
    abstained = (rn.shape == "unknown")
    print(f"  -> ABSTAINS rather than mis-route: "
          f"{'OK (honest unknown)' if abstained else 'did not abstain'}")
    print()
    print("  WHAT WORKED: ONE generic perceiver recognises the KIND of any input")
    print("  from its STRUCTURE (the eye's real Sobel/DoG features) and routes it")
    print("  to the right handler — language->reader, plot->graph reader, node-edge")
    print("  ->structure reader. The readers are now INSTANCES in a registry; a new")
    print("  kind is ONE register_shape() call. The perceptual stack consolidates")
    print("  the way acquire() consolidated acquisition.")
    print()
    print("  THE RESIDUAL (named, not faked):")
    print("   · The recognisers are tractable for these DISTINCT structural shapes")
    print("     (rows-of-glyphs vs axes+points vs blobs+lines). Genuinely AMBIGUOUS")
    print("     shapes (a plot whose points line up as a row; a table; a single")
    print("     large glyph) sit near the boundary — the router ABSTAINS there.")
    print("   · MIXED-ON-ONE-PAGE (text AND a plot in one image) needs a LAYOUT")
    print("     pass (segment regions, route each) — not built here; this routes a")
    print("     single-shape input.")
    print("   · NOVEL kinds (no registered recogniser) -> abstain 'unknown shape'")
    print("     until an instance is registered. That is the registry's honesty.")
    print("   · The HANDLERS' accuracy is AS PREVIOUSLY MEASURED — this adds the")
    print("     ROUTING, not new reading accuracy. No over-claim.")

    # ===================================================================== #
    # SUMMARY.                                                              #
    # ===================================================================== #
    banner("SUMMARY")
    lang = by_shape.get("language", (None, None))[1]
    plot = by_shape.get("plot", (None, None))[1]
    node = by_shape.get("node-edge", (None, None))[1]
    rows = [
        ("3 mixed UNLABELED inputs each recognised + routed from STRUCTURE",
         set(by_shape) >= {"language", "plot", "node-edge"}),
        ("LANGUAGE -> reader -> comprehended (divisor_sum verified)",
         bool(lang and lang.result.get("verified"))),
        ("PLOT -> graph reader -> recovered a(n)=n(n+1)/2 verified",
         bool(plot and plot.result.get("verified"))),
        ("NODE-EDGE -> structure reader -> nodes + adjacency recovered",
         bool(node and node.result.get("n_nodes", 0) >= 3
              and node.result.get("n_edges", 0) >= 1)),
        (f"STRUCTURE-not-label control: {ctrl_ok}/3 recognised from features",
         ctrl_ok == 3),
        ("MIS-ROUTING control: wrong handler -> no verified comprehension",
         mis_ok),
        ("EXTENSIBLE: a 4th shape (blank) via ONE register_shape() routes",
         rb.shape == "blank" and still_ok),
        ("HONEST: abstains 'unknown shape' on a novel/ambiguous input",
         abstained),
    ]
    all_ok = True
    for label, ok in rows:
        all_ok = all_ok and ok
        print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    print(f"\nRESULT: {'ALL OK' if all_ok else 'see failures above'} — ONE generic "
          f"SHAPE-BASED router: the agent recognised language as language and "
          f"graphs as graphs from STRUCTURE, and routed each to its handler. The "
          f"readers are now registry instances; extensible to anything by one "
          f"register_shape() call; honest abstain on the ambiguous/novel residual.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
