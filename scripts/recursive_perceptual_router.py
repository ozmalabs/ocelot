"""THE ORDER-N / RECURSIVE PERCEPTUAL ROUTER — a LAYOUT is an order-N SHAPE whose
PARTS are shapes, recognised RECURSIVELY. The base router (perceptual_router) reads
ATOMIC shapes (a single text line / a plot / a node-edge diagram) and ABSTAINS on a
multi-region PAGE — the "layout residual". This dissolves that residual the way every
residual this session dissolved: into ORDER-N.

    order-0 = an ATOMIC mark (a glyph, a point).
    order-1 = a SHAPE  (a text block, a plot, a node-edge) — the BASE router, the leaf.
    order-N = a LAYOUT = a composition of REGIONS, each a shape, RECURSIVELY:
              a page = a text block + a figure + a caption; a figure = a plot + a
              legend, deeper. Recognising a layout = RECURSIVE SEGMENTATION:

    region(image)                         <- the whole page at the top
      -> INK PROJECTIONS    the eye sums ink along rows + columns.
      -> WIDEST GUTTER      find the widest band of near-zero ink spanning the region
                            (a whitespace gutter), horizontal OR vertical.
      -> CUT + RECURSE      if a wide-enough gutter exists, CUT there into sub-regions
                            and RECURSE on each (the order-N STEP over SPACE).
      -> LEAF               if NO significant gutter (a coherent single block), STOP:
                            hand the region to the BASE shape-router
                            (perceptual_router.perceive_and_route) — recognise its
                            atomic shape, route to its handler, comprehend. (the BEDROCK)
      -> COMPOSE            the recursion returns a TREE: interior nodes = cut regions
                            (cut orientation + child reading order), leaves = {bbox,
                            recognised shape, handler result}. The page is COMPREHENDED
                            as that composition — an ordered set of {shape, content}.

THIS IS iterate_to_n OVER SPACE. domains/order_n_composition.iterate_to_n is the agent's
one recursive-composition operator: `t = bedrock; for _ in range(N): t = step(t)`. The
recursive XY-cut is that exact shape with the rule swapped to SPACE: the STEP / COMBINATION
RULE = "cut at the widest whitespace gutter"; the BEDROCK = "a region the base router
recognises as an atomic shape". A layout is just an order-N shape — the same operator that
ran the signal derivative, the relation chain, the compute tower, now SPATIAL.

THE BASE CASE IS SUBSUMED, not paralleled: a single atomic-shape image (no gutter) bottoms
out immediately at depth-1 -> identical to perceptual_router. The recursive router IS the
base router when the page has one region; the "layout residual" was just N=1 of this operator.

NO LLM, no learned layout model. The segmentation is WHITESPACE STRUCTURE read off the real
eye's ink projections (the same eye perceptual_router/the readers use); the leaf recognition
is the EXISTING base router; the page is composed as a region tree. No Rust.

HONEST: the XY-cut is tractable for WHITESPACE-SEPARATED regions (clean gutters). Overlapping
/ no-gutter / reading-order-ambiguous / deeply-nested real-world layouts are the DEEPER
residual (more order-N, harder cuts) — named below. Leaf-handler accuracy is AS MEASURED;
this adds the recursive LAYOUT decomposition, not new leaf reading.

Faithful (CLAUDE.md): ADDITIVE world adapter. The recursive segmentation WRAPS
perceptual_router; it reuses the same eye + the base router + the existing handlers. The
whitespace XY-cut is mechanical projection structure (no decisions over agent graph state).
No Rust, no rebuild.

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/recursive_perceptual_router.py
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

# THE BASE ROUTER WE WRAP — the leaf / base case, REUSED verbatim. The recursion
# bottoms out by calling perceive_and_route on a coherent single-shape region.
from scripts.perceptual_router import (
    PerceptualRouter, Handlers, RouteResult,
    recognise_language, recognise_plot, recognise_node_edge, recognise_blank,
    render_node_edge_world,
)
# THE WORLD renderers (text line / plot) — used to COMPOSE a multi-region PAGE the
# router is then handed WHOLE + unlabeled. The agent only ever sees the page pixels.
from scripts.agent_reads_through_its_eye import render_text, GW, GAP, SCALE
from scripts.agent_reads_a_graph import PlotWorld
# THE ONE OPERATOR whose SHAPE the recursive cut mirrors — iterate_to_n over SPACE.
from domains.order_n_composition import iterate_to_n

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# ===========================================================================
# THE LAYOUT TREE — the composition the recursion returns. An interior node is a
# CUT region (orientation + ordered children = the reading order); a leaf is a
# coherent single-shape region {bbox, recognised shape, routed handler result}.
# ===========================================================================

@dataclass
class RegionNode:
    """A node of the recursive layout tree. Either:
      · a LEAF  — a coherent single-shape region the base router recognised:
                  `shape` + `route` set, `children` empty.
      · INTERIOR — a region CUT into sub-regions: `cut` in {'H','V'} (a horizontal
                  cut stacks rows = vertical reading order; a vertical cut splits
                  columns = left-to-right), `children` in reading order."""
    bbox: tuple[int, int, int, int]      # (r0, r1, c0, c1) in the FULL-page frame
    depth: int                           # recursion depth (0 = the whole page)
    cut: Optional[str] = None            # 'H' / 'V' for interior; None for a leaf
    children: list["RegionNode"] = field(default_factory=list)
    shape: Optional[str] = None          # leaf: the recognised atomic shape
    route: Optional[RouteResult] = None  # leaf: the base router's result
    gutter: Optional[float] = None       # interior: the chosen gutter width (px)

    @property
    def is_leaf(self) -> bool:
        return not self.children

    def leaves(self) -> list["RegionNode"]:
        """Leaves in READING ORDER (children are stored in reading order; an
        in-order walk yields the reading sequence of the page)."""
        if self.is_leaf:
            return [self]
        out: list["RegionNode"] = []
        for ch in self.children:
            out.extend(ch.leaves())
        return out


# ===========================================================================
# THE RECURSIVE WHITESPACE XY-CUT — the order-N operator over SPACE. Given a
# region, the eye computes the horizontal + vertical ink PROJECTIONS, finds the
# widest whitespace GUTTER spanning the region, and either CUTS + recurses (the
# STEP) or, if no significant gutter, treats the region as a LEAF (the BEDROCK).
# ===========================================================================

def _ink_mask(img: np.ndarray) -> np.ndarray:
    return img > 127


def _widest_gap(profile: np.ndarray, edge_skip: int) -> tuple[int, int, int]:
    """Given a 1-D ink profile (ink count per row OR per column of the region),
    find the WIDEST run of near-zero (whitespace) cells that is INTERIOR (not the
    outer margin). Returns (gap_width, gap_start, gap_end) — the widest interior
    gutter. Margins (leading/trailing whitespace) are excluded by `edge_skip`: a
    gutter must separate ink on BOTH sides to be a real cut."""
    n = len(profile)
    empty = profile <= 0
    # find runs of empty cells.
    best = (0, -1, -1)
    i = 0
    while i < n:
        if empty[i]:
            j = i
            while j < n and empty[j]:
                j += 1
            start, end = i, j - 1
            # interior only: there must be ink before `start` and after `end`
            # (a gutter SEPARATES two inked regions; a leading/trailing run is a
            # margin, not a cut). edge_skip guards tiny border noise.
            has_left = bool(profile[:start].sum() > 0) and start > edge_skip
            has_right = bool(profile[end + 1:].sum() > 0) and (n - 1 - end) > edge_skip
            if has_left and has_right:
                width = end - start + 1
                if width > best[0]:
                    best = (width, start, end)
            i = j
        else:
            i += 1
    return best


@dataclass
class CutPolicy:
    """The bedrock test + cut thresholds for the recursive XY-cut. A region is a
    LEAF (bedrock) when no gutter is wide enough OR it is already small — then the
    base shape-router recognises it. Otherwise CUT at the widest gutter."""
    min_gutter: int = 28        # a gutter must be this many px wide to be an INTER-
                                # REGION cut. The fixed font's inter-WORD space is
                                # 21px (one space glyph), so 28 is clearly above a
                                # word gap + below a real page gutter: a text line is
                                # NOT shredded into words, a page IS cut at its
                                # region gutters. (the calibration the prompt's
                                # "wide-enough gutter" names.)
    min_region: int = 22        # a region smaller than this in the cut axis = leaf
    edge_skip: int = 2          # ignore <= this many border px when testing margins
    max_depth: int = 6          # recursion bound (a deep page still terminates)

    def choose_cut(self, img: np.ndarray
                   ) -> Optional[tuple[str, int, int, int]]:
        """The order-N STEP / bedrock test over a region image. Returns the cut
        (orientation, gap_start, gap_end, width) at the WIDEST whitespace gutter —
        horizontal (split rows) or vertical (split columns), whichever gutter is
        WIDER (cleaner). Returns None when no gutter is wide enough -> the region
        is a LEAF (bedrock = the base router recognises an atomic shape)."""
        H, W = img.shape
        ink = _ink_mask(img)
        # horizontal gutter: a band of empty ROWS (cut stacks top/bottom).
        row_ink = ink.sum(axis=1)
        hw, hs, he = _widest_gap(row_ink, self.edge_skip)
        # vertical gutter: a band of empty COLUMNS (cut splits left/right).
        col_ink = ink.sum(axis=0)
        vw, vs, ve = _widest_gap(col_ink, self.edge_skip)
        # pick the WIDER (cleaner) gutter as the cut for THIS level.
        cand = []
        if hw >= self.min_gutter:
            cand.append(("H", hs, he, hw))
        if vw >= self.min_gutter:
            cand.append(("V", vs, ve, vw))
        if not cand:
            return None                          # no gutter -> LEAF (bedrock)
        return max(cand, key=lambda t: t[3])     # widest gutter wins


# ---------------------------------------------------------------------------
# THE RECURSION — segment(region) is the order-N operator over space, written as
# the SAME recursive-composition shape as iterate_to_n (the cut = the COMBINATION
# step, an atomic-shape leaf = the BEDROCK). It returns the layout tree.
# ---------------------------------------------------------------------------

class RecursiveRouter:
    """The order-N shape router. Wraps the BASE perceptual_router: recursively
    segments a page into regions at whitespace gutters, bottoms out at the atomic
    shapes the base router recognises + routes, and composes the layout tree.

    The recursion is iterate_to_n applied to SPACE: the STEP = cut-at-the-widest-
    gutter, the BEDROCK = a region the base router recognises as an atomic shape."""

    def __init__(self, base: PerceptualRouter, handlers: Handlers,
                 policy: Optional[CutPolicy] = None):
        self.base = base                 # the base shape-router (the leaves)
        self.handlers = handlers
        self.policy = policy or CutPolicy()
        self.cut_count = 0               # how many recursive cuts were made
        self.leaf_count = 0

    def is_atomic_shape(self, img: np.ndarray, meta: Optional[dict]) -> bool:
        """A convenience bedrock predicate (used by the iterate_to_n-over-space
        demo): a region is BEDROCK when it has no INTER-REGION whitespace gutter
        (choose_cut returns None). A single text line's internal WORD gutters are
        below the cut threshold (see CutPolicy.min_gutter), so a text line is
        bedrock — exactly the spec's 'a region the base router recognises as an
        atomic shape'."""
        return self.policy.choose_cut(img) is None

    def segment(self, img: np.ndarray,
                bbox: Optional[tuple[int, int, int, int]] = None,
                depth: int = 0, meta: Optional[dict] = None) -> RegionNode:
        """RECURSIVELY SEGMENT a region into the layout tree. The order-N operator
        over space: find the widest whitespace gutter (the STEP); if one exists,
        cut + recurse on each sub-region; else this region is a LEAF -> the base
        shape-router recognises + routes it (the BEDROCK)."""
        H, W = img.shape
        if bbox is None:
            bbox = (0, H, 0, W)
        r0, r1, c0, c1 = bbox
        # BEDROCK TEST: depth bound, or no INTER-REGION whitespace gutter wide
        # enough to cut -> LEAF. A single text line's internal WORD gutters are
        # below min_gutter (an inter-region gutter is clearly wider than a word
        # space), so a text line is NOT cut into words — it is bedrock, the atomic
        # shape the base router recognises. A multi-region page HAS a wide gutter,
        # so it is cut.
        cut = (None if depth >= self.policy.max_depth
               else self.policy.choose_cut(img))
        if cut is None:
            return self._leaf(img, bbox, depth, meta)
        orient, gs, ge, gw = cut
        # the cut line = the MIDDLE of the widest gutter (cleanest split point).
        mid = (gs + ge) // 2
        node = RegionNode(bbox=bbox, depth=depth, cut=orient, gutter=float(gw))
        self.cut_count += 1
        if orient == "H":                # split ROWS -> top region, bottom region
            top = img[:mid + 1, :]
            bot = img[mid + 1:, :]
            # reading order: TOP then BOTTOM.
            node.children = [
                self.segment(top, (r0, r0 + mid + 1, c0, c1), depth + 1, meta),
                self.segment(bot, (r0 + mid + 1, r1, c0, c1), depth + 1, meta),
            ]
        else:                            # split COLUMNS -> left region, right region
            left = img[:, :mid + 1]
            right = img[:, mid + 1:]
            # reading order: LEFT then RIGHT.
            node.children = [
                self.segment(left, (r0, r1, c0, c0 + mid + 1), depth + 1, meta),
                self.segment(right, (r0, r1, c0 + mid + 1, c1), depth + 1, meta),
            ]
        return node

    def _leaf(self, img: np.ndarray, bbox, depth: int,
              meta: Optional[dict]) -> RegionNode:
        """BEDROCK: a coherent single-region image -> the base shape-router. Crop
        to the region's ink (so margins from the cut don't skew the recogniser),
        then perceive_and_route exactly as the atomic router does."""
        self.leaf_count += 1
        crop, _ = self._tight_crop(img)
        lm = self._leaf_meta(crop, meta)
        route = self.base.perceive_and_route(crop, lm)
        return RegionNode(bbox=bbox, depth=depth, shape=route.shape, route=route)

    @staticmethod
    def _tight_crop(img: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int]]:
        """Crop a region to its bounding box of ink (with a 1px border) so a cut's
        leftover whitespace margin doesn't distort the base recogniser's aspect /
        band features. Returns (cropped, (r0,r1,c0,c1) within the region)."""
        ink = _ink_mask(img)
        rows = np.nonzero(ink.any(axis=1))[0]
        cols = np.nonzero(ink.any(axis=0))[0]
        if len(rows) == 0 or len(cols) == 0:
            return img, (0, img.shape[0], 0, img.shape[1])
        r0, r1 = rows.min(), rows.max() + 1
        c0, c1 = cols.min(), cols.max() + 1
        return img[r0:r1, c0:c1], (int(r0), int(r1), int(c0), int(c1))

    @staticmethod
    def _leaf_meta(crop: np.ndarray, meta: Optional[dict]) -> dict:
        """The base handlers need a little meta (a text line needs its glyph count;
        a plot accepts OEIS candidates). For a leaf we infer the text glyph count
        from the world's fixed grid stride (the text handler already does this when
        n_glyphs is absent — we let it). Pass through any caller candidates."""
        out = dict(meta or {})
        # don't force n_glyphs — the text handler recovers it from the grid stride
        # (GW+GAP)*SCALE, which is exactly how a region of rendered text is laid out.
        out.setdefault("oeis_candidates",
                       ["A000217", "A000290", "A000027", "A005408"])
        return out

    # --- the ONE call: recursively route a whole page -> the layout tree ----
    def route_page(self, img: np.ndarray, meta: Optional[dict] = None
                   ) -> RegionNode:
        """THE ORDER-N OPERATION: hand a WHOLE page (it is NOT told its regions);
        recursively segment at whitespace gutters; recognise + route each leaf via
        the base router; return the composed layout tree (reading order = in-order
        leaves). This SUBSUMES the base router: a single-shape page bottoms out at
        depth-1 and is identical to perceive_and_route."""
        self.cut_count = 0
        self.leaf_count = 0
        return self.segment(img, None, 0, meta)


# ===========================================================================
# THE WORLD — compose MULTI-REGION pages from the existing renderers, separated
# by WHITESPACE gutters. The router is handed the WHOLE page and is NOT told the
# regions. (The renderers are the world; the agent only ever sees the pixels.)
# ===========================================================================

def _pad_to_width(img: np.ndarray, W: int, left: int = 0) -> np.ndarray:
    """Place `img` into a width-W canvas at column `left` (whitespace elsewhere)."""
    H = img.shape[0]
    out = np.zeros((H, W), np.uint8)
    w = min(img.shape[1], W - left)
    out[:, left:left + w] = img[:, :w]
    return out


def stack_vertical(blocks: list[np.ndarray], gutter: int = 18,
                   margin: int = 12) -> np.ndarray:
    """Stack region images TOP-to-BOTTOM separated by `gutter` rows of whitespace
    (the horizontal gutters the router will cut on). Width = widest block + margins."""
    W = max(b.shape[1] for b in blocks) + 2 * margin
    pieces = [np.zeros((margin, W), np.uint8)]      # top margin
    for i, b in enumerate(blocks):
        pieces.append(_pad_to_width(b, W, left=margin))
        if i != len(blocks) - 1:
            pieces.append(np.zeros((gutter, W), np.uint8))
    pieces.append(np.zeros((margin, W), np.uint8))  # bottom margin
    return np.concatenate(pieces, axis=0)


def beside(left_img: np.ndarray, right_img: np.ndarray, gutter: int = 26,
           margin: int = 12) -> np.ndarray:
    """Place two region images SIDE-BY-SIDE separated by `gutter` columns of
    whitespace (the vertical gutter the router cuts on). Heights padded to match."""
    H = max(left_img.shape[0], right_img.shape[0]) + 2 * margin
    Wl, Wr = left_img.shape[1], right_img.shape[1]
    W = margin + Wl + gutter + Wr + margin
    out = np.zeros((H, W), np.uint8)
    # vertically centre each block.
    lr0 = (H - left_img.shape[0]) // 2
    rr0 = (H - right_img.shape[0]) // 2
    out[lr0:lr0 + left_img.shape[0], margin:margin + Wl] = left_img
    out[rr0:rr0 + right_img.shape[0],
        margin + Wl + gutter:margin + Wl + gutter + Wr] = right_img
    return out


def figure_block(plot_img: np.ndarray, label: str, gutter: int = 12,
                 margin: int = 6) -> np.ndarray:
    """A FIGURE = a PLOT above a LABEL line, with a small whitespace gutter between
    them — a region that is ITSELF a composition (the depth-2 / nested case). The
    router will recurse INTO this block (cut plot|label) one level deeper."""
    label_img = render_text(label)
    return stack_vertical([plot_img, label_img], gutter=gutter, margin=margin)


# ===========================================================================
# RENDERING THE LAYOUT TREE — the composition, in reading order.
# ===========================================================================

def render_tree(node: RegionNode, indent: int = 0) -> list[str]:
    pad = "  " * indent
    if node.is_leaf:
        r = node.route
        shp = (node.shape or "unknown").upper()
        summ = r.result.get("summary") if r else "(no route)"
        return [f"{pad}- LEAF [{node.bbox}] shape={shp}: {summ}"]
    rd = "top->bottom" if node.cut == "H" else "left->right"
    out = [f"{pad}+ CUT-{node.cut} (gutter {node.gutter:.0f}px, {rd}) "
           f"[{node.bbox}] depth={node.depth}"]
    for ch in node.children:
        out.extend(render_tree(ch, indent + 1))
    return out


def comprehend_leaf(node: RegionNode) -> str:
    """A one-line COMPREHENSION of a leaf region — shape + the routed content."""
    r = node.route
    if r is None:
        return "(no content)"
    res = r.result
    k = res.get("kind")
    if k == "language":
        return f"TEXT {res.get('read_text')!r} -> {res.get('comprehension')}"
    if k == "plot":
        return (f"FIGURE/PLOT a(n)={res.get('function')} "
                f"(OEIS={res.get('oeis')}, verified={res.get('verified')})")
    if k == "node-edge":
        return (f"NODE-EDGE {res.get('n_nodes')} nodes / "
                f"{res.get('n_edges')} edges")
    if k == "blank":
        return "BLANK"
    return res.get("summary", "?")


# ===========================================================================
# THE PROOF
# ===========================================================================

def main():
    banner("THE ORDER-N / RECURSIVE PERCEPTUAL ROUTER — a LAYOUT is an order-N "
           "SHAPE whose PARTS are shapes, recognised RECURSIVELY")
    print("  The base router (perceptual_router) reads ATOMIC shapes and ABSTAINS")
    print("  on a multi-region PAGE — the 'layout residual'. This dissolves it into")
    print("  ORDER-N: a page is a region containing sub-regions (text + figure +")
    print("  caption), each a shape, RECURSIVELY. The router RECURSIVELY SEGMENTS")
    print("  the input (recursive whitespace XY-cut = iterate_to_n over SPACE: find")
    print("  the widest whitespace gutter, cut, recurse), bottoms out at the ATOMIC")
    print("  shapes the BASE router recognises + routes, and COMPOSES the layout")
    print("  tree. The SAME shape-router at the leaves; the recursion is the order-N")
    print("  operator applied to space. No LLM, no learned layout model, no Rust.\n")

    # build the BASE router (the leaves) + the recursive wrapper.
    base = PerceptualRouter()
    handlers = Handlers()
    base.register_shape("language", recognise_language, handlers.handle_language)
    base.register_shape("plot", recognise_plot, handlers.handle_plot)
    base.register_shape("node-edge", recognise_node_edge, handlers.handle_node_edge)
    base.register_shape("blank", recognise_blank, handlers.handle_blank)
    router = RecursiveRouter(base, handlers)
    print(f"  BASE router registered shapes (the LEAVES): "
          f"{[sh.name for sh in base.shapes]}")
    print(f"  RecursiveRouter wraps it: segment -> (leaf = base router) -> compose.")

    # ===================================================================== #
    # PROOF #1 — a >=3-REGION PAGE handed WHOLE + unlabeled.                #
    # text line ABOVE a plot (triangular numbers) ABOVE a caption line.     #
    # ===================================================================== #
    banner("PROOF #1 — a 3-REGION PAGE (TEXT / PLOT / CAPTION, whitespace-"
           "separated) handed WHOLE + UNLABELED -> recursively segmented + routed")
    text_top = render_text("sum of divisors of n")
    plot_mid = PlotWorld(ppx=12, ppy=4, margin=16).render(
        [(n, n * (n + 1) // 2) for n in range(0, 7)])     # triangular numbers
    caption = render_text("the triangular numbers")
    page = stack_vertical([text_top, plot_mid, caption], gutter=36, margin=12)
    print(f"  composed page image: shape (H,W) = {page.shape}  (the agent sees the")
    print(f"  WHOLE page as PIXELS; it is NOT told there are 3 regions)\n")

    tree = router.route_page(page)
    print(f"  RECURSIVELY SEGMENTED: {router.cut_count} cuts -> "
          f"{router.leaf_count} leaf regions. The LAYOUT TREE:")
    for ln in render_tree(tree):
        print("    " + ln)

    leaves = tree.leaves()
    print(f"\n  THE PAGE COMPREHENDED as an ordered composition of "
          f"{len(leaves)} regions (reading order):")
    for i, lf in enumerate(leaves):
        print(f"    region {i + 1}: {comprehend_leaf(lf)}")

    # what the page SHOULD decompose to, in reading order.
    shapes_seq = [lf.shape for lf in leaves]
    p1_text = any(lf.shape == "language" and
                  lf.route.result.get("verified") for lf in leaves)
    p1_plot = any(lf.shape == "plot" and
                  lf.route.result.get("verified") for lf in leaves)
    p1_caption = sum(1 for lf in leaves if lf.shape == "language") >= 2
    p1_order = (shapes_seq[:1] == ["language"] and "plot" in shapes_seq
                and shapes_seq[-1] == "language")
    print(f"\n  reading-order shapes: {shapes_seq}")
    print(f"  -> text->divisor_sum verified: {p1_text}; "
          f"plot->n(n+1)/2 verified: {p1_plot}; caption is text: {p1_caption}; "
          f"order text..plot..caption: {p1_order}")

    # ===================================================================== #
    # PROOF #2 — a 2-COLUMN page (TEXT | PLOT), a VERTICAL gutter.          #
    # ===================================================================== #
    banner("PROOF #2 — a 2-COLUMN page (TEXT | PLOT, a VERTICAL whitespace "
           "gutter) -> the router cuts VERTICALLY (left->right reading order)")
    col_text = render_text("squares of n")
    col_plot = PlotWorld(ppx=12, ppy=3, margin=16).render(
        [(n, n * n) for n in range(0, 8)])               # squares
    page2 = beside(col_text, col_plot, gutter=40, margin=12)
    print(f"  composed 2-column page: shape {page2.shape}  (whole + unlabeled)\n")
    tree2 = router.route_page(page2)
    print(f"  SEGMENTED: {router.cut_count} cuts -> {router.leaf_count} leaves. "
          f"TREE:")
    for ln in render_tree(tree2):
        print("    " + ln)
    leaves2 = tree2.leaves()
    print(f"\n  reading order (left->right): "
          f"{[lf.shape for lf in leaves2]}")
    for i, lf in enumerate(leaves2):
        print(f"    region {i + 1}: {comprehend_leaf(lf)}")
    top_is_vcut = tree2.cut == "V"
    p2_text = any(lf.shape == "language" for lf in leaves2)
    p2_plot = any(lf.shape == "plot" and lf.route.result.get("verified")
                  for lf in leaves2)
    print(f"\n  -> top-level cut is VERTICAL (a column gutter): {top_is_vcut}; "
          f"text leaf: {p2_text}; plot leaf verified: {p2_plot}")

    # ===================================================================== #
    # PROOF #3 — ORDER-N / NESTED: a region that is ITSELF a composition.   #
    # a page = TEXT line ABOVE a FIGURE, where the FIGURE = a PLOT above a   #
    # LABEL line -> the router recurses one level DEEPER (depth-2 tree).     #
    # ===================================================================== #
    banner("PROOF #3 — ORDER-N / NESTED: a FIGURE is ITSELF a composition "
           "(a PLOT + a LABEL) -> the recursion goes one level DEEPER (depth-2)")
    heading = render_text("a figure with its own caption")
    fig = figure_block(
        PlotWorld(ppx=12, ppy=5, margin=16).render(
            [(n, 2 * n + 1) for n in range(0, 7)]),       # odd numbers 2n+1
        "odd numbers", gutter=34, margin=6)               # plot|label gutter (>28)
    # the OUTER heading|figure gutter is WIDER (48) than the figure's internal
    # plot|label gutter (34) -> the recursion cuts the page first, then recurses
    # INTO the figure (the depth-2 / nested case).
    page3 = stack_vertical([heading, fig], gutter=48, margin=12)
    print(f"  composed nested page: shape {page3.shape}  (a HEADING above a FIGURE;")
    print(f"  the FIGURE is itself a PLOT above a LABEL — the router is NOT told)\n")
    tree3 = router.route_page(page3)
    max_depth = max(lf.depth for lf in tree3.leaves())
    print(f"  SEGMENTED: {router.cut_count} cuts -> {router.leaf_count} leaves, "
          f"max leaf depth = {max_depth} (>=2 => it recursed INTO the figure). "
          f"TREE:")
    for ln in render_tree(tree3):
        print("    " + ln)
    leaves3 = tree3.leaves()
    print(f"\n  reading order: {[lf.shape for lf in leaves3]}")
    for i, lf in enumerate(leaves3):
        print(f"    region {i + 1} (depth {lf.depth}): {comprehend_leaf(lf)}")
    p3_nested = max_depth >= 2
    p3_plot = any(lf.shape == "plot" for lf in leaves3)
    print(f"\n  -> NESTED recursion (a region that is itself a composition) "
          f"depth>=2: {p3_nested}; the figure's PLOT recognised: {p3_plot}")

    # ===================================================================== #
    # THE BASE CASE IS SUBSUMED — a single atomic-shape image (no gutter).  #
    # ===================================================================== #
    banner("BASE CASE SUBSUMED — a single ATOMIC-shape image (NO gutter) bottoms "
           "out at depth-1 -> IDENTICAL to perceptual_router (the order-1 case)")
    atomic_inputs = [
        ("a lone TEXT line", render_text("number of divisors of n"),
         {"oeis": "A000005"}),
        ("a lone PLOT", PlotWorld(ppx=12, ppy=4, margin=16).render(
            [(n, n * (n + 1) // 2) for n in range(0, 7)]), {}),
        ("a lone NODE-EDGE diagram", render_node_edge_world(
            centers=[(28, 30), (28, 118), (100, 30), (100, 118)],
            edges=[(0, 1), (0, 2), (1, 3), (2, 3)]), {}),
    ]
    subsumed_ok = True
    for name, img, meta in atomic_inputs:
        # the recursive router on the atomic image:
        rec_tree = router.route_page(img, meta)
        rec_leaf = rec_tree.leaves()[0]
        # the BASE router directly on the same (ink-cropped) image — the recursive
        # router crops to ink at a leaf, so compare against the same crop.
        crop, _ = router._tight_crop(img)
        base_res = base.perceive_and_route(crop, meta)
        depth1 = (rec_tree.is_leaf)           # bottomed out immediately
        same_shape = (rec_leaf.shape == base_res.shape)
        subsumed_ok = subsumed_ok and depth1 and same_shape
        print(f"  {name}: recursive -> depth-1 leaf shape={rec_leaf.shape.upper()} "
              f"(no cut); base router -> {base_res.shape.upper()}  "
              f"[same={same_shape}, immediate-leaf={depth1}]")
    print(f"  -> the order-N router SUBSUMES the atomic router on single-shape "
          f"input (the residual dissolved, not a parallel path): "
          f"{'OK' if subsumed_ok else 'MISMATCH'}")

    # ===================================================================== #
    # IT IS iterate_to_n OVER SPACE — name/show the recursion as the SAME   #
    # recursive-composition shape the agent already runs.                   #
    # ===================================================================== #
    banner("IT IS iterate_to_n OVER SPACE — the recursive XY-cut IS the agent's "
           "ONE order-N operator, with the rule = CUT + the bedrock = atomic shape")
    # demonstrate the SHAPE literally: iterate_to_n applied to a region with the
    # cut-at-widest-gutter STEP yields the same leaf segmentation our recursion does.
    def _space_step(regions: list[tuple[np.ndarray, tuple]]
                    ) -> list[tuple[np.ndarray, tuple]]:
        """ONE order-N STEP over SPACE: cut each not-yet-bedrock region at its
        widest whitespace gutter into sub-regions; bedrock regions (no gutter)
        pass through. This is iterate_to_n's `step` with the COMBINATION RULE =
        whitespace-cut and the BEDROCK = a region with no wide gutter."""
        nxt: list[tuple[np.ndarray, tuple]] = []
        for im, bb in regions:
            cut = router.policy.choose_cut(im)
            if cut is None:
                nxt.append((im, bb))            # BEDROCK — atomic shape, passes through
                continue
            orient, gs, ge, gw = cut
            mid = (gs + ge) // 2
            r0, r1, c0, c1 = bb
            if orient == "H":
                nxt.append((im[:mid + 1, :], (r0, r0 + mid + 1, c0, c1)))
                nxt.append((im[mid + 1:, :], (r0 + mid + 1, r1, c0, c1)))
            else:
                nxt.append((im[:, :mid + 1], (r0, r1, c0, c0 + mid + 1)))
                nxt.append((im[:, mid + 1:], (r0, r1, c0 + mid + 1, c1)))
        return nxt

    H, W = page.shape
    bedrock = [(page, (0, H, 0, W))]            # the whole page = the BEDROCK input
    print("  BEDROCK (the iterate_to_n input) = the whole page, ONE region.")
    print("  STEP (the COMBINATION RULE) = cut every region at its widest "
          "whitespace gutter.")
    counts = []
    for N in range(0, 5):
        regions = iterate_to_n(bedrock, _space_step, N)   # the SAME operator
        n_bedrock = sum(1 for im, _ in regions
                        if router.policy.choose_cut(im) is None)
        counts.append((N, len(regions), n_bedrock))
        print(f"    iterate_to_n(page, cut_step, N={N}) -> {len(regions)} regions, "
              f"{n_bedrock} are bedrock (atomic shapes)")
    converged = counts[-1][1] == counts[-1][2]   # all regions are bedrock leaves
    final_leaves = counts[-1][2]
    print(f"  -> iterate_to_n OVER SPACE converges to the leaf segmentation "
          f"({final_leaves} atomic regions, all bedrock): {converged}")
    print(f"  -> SAME operator as the signal derivative / relation chain / compute")
    print(f"     tower (domains/order_n_composition.iterate_to_n) — the rule is the")
    print(f"     only knob: here STEP=whitespace-cut, BEDROCK=atomic shape. A LAYOUT")
    print(f"     is an order-N SHAPE.")
    matches_recursion = (final_leaves == len(tree.leaves()))
    print(f"  -> matches the recursive route_page leaf count "
          f"({len(tree.leaves())}): {matches_recursion}")

    # ===================================================================== #
    # HONEST RESIDUAL.                                                      #
    # ===================================================================== #
    banner("HONEST — the deeper residual (named, not faked)")
    print("  WHAT WORKED: the shape router is now ORDER-N. A LAYOUT is recognised")
    print("  as a RECURSIVE COMPOSITION of shapes: recursive whitespace XY-cut")
    print("  (iterate_to_n over SPACE) -> the BASE shape-router at the leaves -> the")
    print("  page composed as a layout tree (regions -> shapes -> routed -> compre-")
    print("  hended, reading order). The 'layout residual' dissolved into the order-N")
    print("  operator — the same one that unified composition / comprehension / the")
    print("  math tower. The base case is SUBSUMED (single-shape page = N=1).")
    print()
    print("  THE DEEPER RESIDUAL (more order-N, harder cuts):")
    print("   · WHITESPACE-SEPARATED regions only: the XY-cut needs CLEAN gutters.")
    print("     Overlapping / touching regions (no gutter between them) cannot be")
    print("     cut by projection — that is the deeper residual.")
    print("   · NO-GUTTER / non-Manhattan layouts (an L-shaped wrap, a figure inset")
    print("     INTO text, diagonal flow) break the recursive XY-cut (it assumes a")
    print("     region splits cleanly H or V).")
    print("   · READING-ORDER ambiguity: the in-order walk assumes top->bottom /")
    print("     left->right. True multi-column flow (read col-1 fully, THEN col-2)")
    print("     vs row-major needs an order model beyond the cut tree.")
    print("   · DEEPLY-NESTED real layouts (figure-in-figure, tables, nested panels)")
    print("     are more order-N — the recursion is general but each leaf still")
    print("     needs the base router to recognise an ATOMIC shape it knows.")
    print("   · LEAF accuracy is AS MEASURED (the existing handlers). This adds the")
    print("     recursive LAYOUT decomposition, NOT new leaf-reading accuracy.")

    # ===================================================================== #
    # SUMMARY.                                                              #
    # ===================================================================== #
    banner("SUMMARY")
    rows = [
        ("PROOF#1: 3-region page (text/plot/caption) recursively segmented + "
         "routed", router is not None and len(leaves) >= 3),
        ("PROOF#1: text->divisor_sum verified + plot->n(n+1)/2 verified + caption "
         "text + reading order", p1_text and p1_plot and p1_caption and p1_order),
        ("PROOF#2: 2-column page cut VERTICALLY (left->right), both regions routed",
         top_is_vcut and p2_text and p2_plot),
        ("PROOF#3: NESTED figure (plot+label) recursed depth>=2, plot recognised",
         p3_nested and p3_plot),
        ("BASE CASE SUBSUMED: single atomic shape -> depth-1 leaf == base router",
         subsumed_ok),
        ("iterate_to_n OVER SPACE: converges to the leaf segmentation, matches "
         "route_page", converged and matches_recursion),
    ]
    all_ok = True
    for label, ok in rows:
        all_ok = all_ok and ok
        print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    print(f"\nRESULT: {'ALL OK' if all_ok else 'see failures above'} — the "
          f"shape-based router is ORDER-N: a LAYOUT is recognised as a RECURSIVE "
          f"composition of shapes (recursive whitespace XY-cut = iterate_to_n over "
          f"SPACE; the base router at the leaves; the page composed as a layout "
          f"tree). The 'layout residual' dissolved into the order-N operator; the "
          f"base case is subsumed; whitespace-separated layouts tractable, "
          f"overlapping/no-gutter/nested are the deeper residual.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
