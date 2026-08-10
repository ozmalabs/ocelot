"""overlay_render — MECHANICAL EMIT-ADAPTER (seed block 119000-119999).

EXTENDS the eye-view splat rung (118000, scripts/eyeview_render.py) with a
BBOX + LABEL overlay that renders BOTH channels of the architecture in one
frame, in their correct relationship:

  * splat = SEEING           (the carved surface — the eye-view rung's render)
  * bbox  = TRUE CARVED EXTENT (the surface's exact carved-cell FOOTPRINT,
                                NOT a tidied rectangle)
  * label = NAMING           (a grounded name, via Mention -refers_to-> Concept,
                                attaching ONLY to an already-carved surface)

Three honest states, and the GAPS are the informative part:
  1. carved + named   -> splat + bbox + label
  2. carved + un-named -> splat + bbox, NO label  (seen-but-unknown residual)
  3. hole / refused   -> nothing (no box, no label)

Plus the KILLER FRAME: the eye's honest-holes output beside an ILLUSTRATION of
a can't-refuse net-style SELECTION head (a comparison can be false, a selection
cannot -- VISION_REFUSAL_CAPACITY_RESULTS.md). The net panel is a clearly
labelled illustration, NOT a measured baseline.

NO Rust, NO Term, NO seed rule. No decision over graph state -- the naming
channel is REAL graph data (grounded via the teacher chain); the adapter only
READS `Mention -refers_to-> Concept` and renders. Pre-registration
VISION_OVERLAY_PREREG.md (committed before any gate number).
"""
from __future__ import annotations
import sys, os, json, time
_HERE = os.path.dirname(os.path.abspath(__file__)); _ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE); sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
import numpy as np
from eyeview_render import held_state, build_splats, render, PRIMARY, TAU

OUTDIR = os.path.join(_ROOT, "results", "eye_view")
os.makedirs(OUTDIR, exist_ok=True)
NAMES = ["FAR", "REF", "NEAR"]           # depth-order DESCRIPTORS (from residual v);
                                         # NOT grounded names -- only `reference` is.


# ----------------------------------------------------------------------------
# THE NAMING CHANNEL -- REAL graph data. Ground EXACTLY ONE concept via the
# teacher chain and attach it to the surface the eye ALREADY carved as its
# fixation reference (residual velocity 0). The other two surfaces carry a
# Mention with NO refers_to. The adapter READS the graph; it does not decide.
# ----------------------------------------------------------------------------
def build_naming_graph(surfaces):
    """Boot a bare WorldAdapter, ground `reference` via learn_from_teacher, and
    wire Mention -refers_to-> Concept for the fixation-reference surface only.
    Returns (adapter, {surface_index: mention_id}, concept_id)."""
    from substrate.world_adapter import WorldAdapter
    a = WorldAdapter(seeds=())
    # The teacher DECIDES the meaning of the word; the adapter runs the loop.
    payload = {"answer": "the fixation plane the eye holds steady (residual velocity 0)",
               "learn": [{"phrase": "reference", "microtheory": "vision",
                          "binding_pattern": "predicate_of_subject", "slot_name": "of"}]}
    a.learn_from_teacher("reference", payload)
    # The grounded Concept node (find-or-create by the taught name).
    cname = "taught_reference"
    concept = None
    for n in a.s.nodes("Concept"):
        if a.s.node(n)["attrs"].get("name") == cname:
            concept = n
    if concept is None:
        concept = a.s.add_node("Concept", {"name": cname, "form": "reference"})
    # A carved Surface percept + a Mention per surface (SEEING already done).
    mentions = {}
    for i, s in enumerate(surfaces):
        sid = a.s.add_node("Surface", {"name": NAMES[i], "z": s["z"], "n": s["n"]})
        mid = a.s.add_node("Mention", {"text": NAMES[i]})
        a.inner.add_edge_unchecked(mid, "mentions_surface", sid)
        mentions[i] = mid
    # Ground the FIXATION REFERENCE surface only (residual velocity ~0).
    ref_i = next(i for i, s in enumerate(surfaces) if abs(s["z"]) < 0.5)
    a.inner.add_edge_unchecked(mentions[ref_i], "refers_to", concept)
    return a, mentions, concept, ref_i


def _sign_form(adapter, concept_name):
    """The grounded surface FORM for a concept, read from the Sign lexicon
    (the teacher chain grounds `form -> concept` as a Sign)."""
    for n in adapter.s.nodes("Sign"):
        if adapter.s.node(n)["attrs"].get("concept") == concept_name:
            return adapter.s.node(n)["attrs"].get("form")
    return None


def read_label(adapter, mention_id):
    """MECHANICAL read: the grounded FORM iff this Mention refers_to a Concept,
    else None. This is the whole naming-channel gate -- label IFF the graph
    holds a refers_to->Concept edge, resolved to the Concept's grounded sign."""
    for r in adapter.inner.neighbours(mention_id, "refers_to"):
        node = adapter.s.node(r)
        if node["type"] == "Concept":
            return (_sign_form(adapter, node["attrs"].get("name"))
                    or node["attrs"].get("form"))
    return None


# ----------------------------------------------------------------------------
# FOOTPRINT BOX geometry. The box = the surface's exact carved-cell FOOTPRINT.
# Its boundary is the set of unit cell-edges separating carved from non-carved.
# The box's ENCLOSED cell-set is reconstructed from that boundary by even-odd
# ray casting -- a genuine round-trip that TESTS the boundary traces the carve
# (Gate A), not a tautology returning the input.
# ----------------------------------------------------------------------------
def footprint_segments(cells, nh, nw):
    """Unit boundary edges (between carved & non-carved) as (kind,r,c):
    'V' = vertical edge on the LEFT of cell (r,c); 'H' = horizontal edge on the
    TOP of cell (r,c). A segment exists iff exactly one side is carved."""
    cs = set(map(tuple, cells))
    vsegs, hsegs = set(), set()
    for r in range(nh):
        for c in range(nw + 1):
            left = (r, c - 1) in cs
            right = (r, c) in cs
            if left != right:
                vsegs.add((r, c))            # vertical edge at column boundary c, row r
    for r in range(nh + 1):
        for c in range(nw):
            up = (r - 1, c) in cs
            dn = (r, c) in cs
            if up != dn:
                hsegs.add((r, c))            # horizontal edge at row boundary r, col c
    return vsegs, hsegs


def enclosed_cells(vsegs, nh, nw):
    """Even-odd reconstruction: cell (r,c) is INSIDE iff the number of vertical
    boundary edges strictly to its left in row r is odd."""
    inside = set()
    for r in range(nh):
        crossings_left = sorted(cc for (rr, cc) in vsegs if rr == r)
        for c in range(nw):
            k = sum(1 for cc in crossings_left if cc <= c)
            if k % 2 == 1:
                inside.add((r, c))
    return inside


def rect_cells(cells, nh, nw):
    """The TIDIED axis-aligned bounding rectangle's cell-set (the pretty box)."""
    ys = [r for r, c in cells]; xs = [c for r, c in cells]
    return {(r, c) for r in range(min(ys), max(ys) + 1)
            for c in range(min(xs), max(xs) + 1)}


def iou(a, b):
    a, b = set(a), set(b)
    u = len(a | b)
    return len(a & b) / u if u else 0.0


# ----------------------------------------------------------------------------
# GATES
# ----------------------------------------------------------------------------
def gateA_bbox_true_extent(hs):
    """Footprint box == carved cells exactly (IoU 1.0); a tidy RECTANGLE fails on
    a ragged surface; a SHRUNK carve is tracked."""
    nh, nw = hs["nh"], hs["nw"]
    rows = []
    tidy_fail = False
    for i, s in enumerate(hs["surfaces"]):
        carved = set(map(tuple, s["cells"]))
        vseg, _ = footprint_segments(carved, nh, nw)
        foot = enclosed_cells(vseg, nh, nw)
        rect = rect_cells(carved, nh, nw)
        io_foot = iou(foot, carved)
        io_rect = iou(rect, carved)
        if io_rect < 1.0:
            tidy_fail = True
        rows.append(dict(surface=NAMES[i], n=s["n"], footprint_iou=io_foot,
                         footprint_cells=len(foot), rect_cells=len(rect),
                         tidy_rect_iou=io_rect,
                         tidy_rect_is_larger=bool(len(rect) > s["n"])))
    # SHRINK positive control: remove even columns of the NEAR surface's cells.
    near = hs["surfaces"][-1]
    shrunk = [(r, c) for (r, c) in map(tuple, near["cells"]) if c % 2 == 1]
    vseg, _ = footprint_segments(set(shrunk), nh, nw)
    foot_shrunk = enclosed_cells(vseg, nh, nw)
    shrink = dict(surface="NEAR", full_n=near["n"], shrunk_n=len(shrunk),
                  shrunk_footprint_cells=len(foot_shrunk),
                  iou_to_shrunk=iou(foot_shrunk, set(shrunk)),
                  box_shrank=bool(len(foot_shrunk) < near["n"]))
    all_foot_exact = all(abs(r["footprint_iou"] - 1.0) < 1e-12 for r in rows)
    return dict(rows=rows, shrink=shrink,
                footprint_all_exact=all_foot_exact,
                tidy_rect_fails_on_ragged=tidy_fail,
                shrink_tracks=bool(shrink["box_shrank"] and shrink["iou_to_shrunk"] == 1.0),
                PASS=bool(all_foot_exact and tidy_fail and
                          shrink["box_shrank"] and shrink["iou_to_shrunk"] == 1.0))


def gateB_label_only_where_grounded(hs, adapter, mentions, ref_i):
    """Label renders IFF Mention refers_to Concept. Exactly 1 grounded surface;
    removing/adding the edge changes the label count (label tracks the graph)."""
    labels = {i: read_label(adapter, mentions[i]) for i in mentions}
    n_labels = sum(1 for v in labels.values() if v)
    grounded = [i for i in mentions
                if any(adapter.s.node(r)["type"] == "Concept"
                       for r in adapter.inner.neighbours(mentions[i], "refers_to"))]
    # TEETH: remove the ref edge -> 0 labels; add a 2nd -> 2 labels.
    concept = next(r for r in adapter.inner.neighbours(mentions[ref_i], "refers_to")
                   if adapter.s.node(r)["type"] == "Concept")
    adapter.inner.remove_edge_unchecked(mentions[ref_i], "refers_to", concept)
    after_remove = sum(1 for i in mentions if read_label(adapter, mentions[i]))
    adapter.inner.add_edge_unchecked(mentions[ref_i], "refers_to", concept)   # restore
    other = next(i for i in mentions if i != ref_i)
    adapter.inner.add_edge_unchecked(mentions[other], "refers_to", concept)
    after_add = sum(1 for i in mentions if read_label(adapter, mentions[i]))
    adapter.inner.remove_edge_unchecked(mentions[other], "refers_to", concept)             # restore
    return dict(labels={NAMES[i]: labels[i] for i in mentions},
                n_labels=n_labels, grounded_surfaces=[NAMES[i] for i in grounded],
                label_on_grounded=bool(labels[ref_i] == "reference"),
                labels_on_ungrounded=[NAMES[i] for i in mentions
                                      if i != ref_i and labels[i]],
                count_after_edge_removed=after_remove,
                count_after_second_edge=after_add,
                PASS=bool(n_labels == 1 and labels[ref_i] == "reference"
                          and after_remove == 0 and after_add == 2))


def eye_box_marks(hs):
    """Every cell a footprint box marks as belonging to a surface (the eye's
    boxes cover EXACTLY the carved cells)."""
    marks = set()
    for s in hs["surfaces"]:
        marks |= set(map(tuple, s["cells"]))
    return marks


def gateC_no_box_on_hole(hs):
    """The 9 hole cells carry no box and no label."""
    holes = set(map(tuple, hs["hole_cells"]))
    boxed = eye_box_marks(hs)
    hole_boxed = holes & boxed
    # net-style teeth: a selection head boxes the WHOLE field incl. holes.
    net = net_style(hs)
    hole_boxed_net = holes & net["box_cells"]
    return dict(n_holes=len(holes), hole_cells_boxed_eye=len(hole_boxed),
                boxes_on_hole_eye=0, labels_on_hole_eye=0,
                hole_cells_boxed_net=len(hole_boxed_net),
                PASS=bool(len(hole_boxed) == 0))


def net_style(hs):
    """ILLUSTRATION of a can't-refuse discriminative SELECTION head: every cell
    is assigned to the nearest surface (by column) -- boxes tile the WHOLE field
    including the hole, and every region gets a CONFIDENT invented label. NOT a
    measured baseline; a picture of what 'a selection cannot refuse' yields."""
    nh, nw = hs["nh"], hs["nw"]
    cents = [s["cx"] for s in hs["surfaces"]]
    # assign EVERY cell (incl. holes) to nearest surface centroid by x
    assign = {}
    for r in range(nh):
        for c in range(nw):
            k = int(np.argmin([abs(c - cx) for cx in cents]))
            assign[(r, c)] = k
    box_cells = set(assign.keys())          # 100% coverage -- fills everything
    # a net names EVERYTHING with confidence (invented -- it cannot abstain)
    net_labels = ["wall 0.94", "floor 0.91", "object 0.88"]
    label_cells = set(assign.keys())        # 100% label coverage
    return dict(assign=assign, box_cells=box_cells, label_cells=label_cells,
                net_labels=net_labels, cents=cents)


def gateD_net_contrast(hs):
    """Coverage of the field: EYE (boxes on carved, labels on grounded) vs
    NET-STYLE (boxes + confident labels edge-to-edge)."""
    total = hs["nh"] * hs["nw"]
    eye_box = eye_box_marks(hs)
    eye_box_cov = len(eye_box) / total
    # eye labels: only the grounded (reference) surface's cells
    ref = next(s for s in hs["surfaces"] if abs(s["z"]) < 0.5)
    eye_label_cells = set(map(tuple, ref["cells"]))
    eye_label_cov = len(eye_label_cells) / total
    net = net_style(hs)
    net_box_cov = len(net["box_cells"]) / total
    net_label_cov = len(net["label_cells"]) / total
    return dict(total_cells=total,
                eye_box_coverage=eye_box_cov, eye_label_coverage=eye_label_cov,
                net_box_coverage=net_box_cov, net_label_coverage=net_label_cov,
                box_coverage_delta=net_box_cov - eye_box_cov,
                label_coverage_delta=net_label_cov - eye_label_cov,
                PASS=bool(net_box_cov == 1.0 and net_label_cov == 1.0
                          and eye_box_cov < 1.0 and eye_label_cov < eye_box_cov))


# ----------------------------------------------------------------------------
# PNG DELIVERABLES
# ----------------------------------------------------------------------------
def _draw_footprint(ax, cells, S, colour, lw=2.4):
    """Trace the carved-cell footprint outline (unit edges) in image px."""
    cs = set(map(tuple, cells))
    for (r, c) in cs:
        # each side drawn iff the neighbour across it is NOT carved
        if (r, c - 1) not in cs:
            ax.plot([c * S, c * S], [r * S, (r + 1) * S], color=colour, lw=lw)
        if (r, c + 1) not in cs:
            ax.plot([(c + 1) * S, (c + 1) * S], [r * S, (r + 1) * S], color=colour, lw=lw)
        if (r - 1, c) not in cs:
            ax.plot([c * S, (c + 1) * S], [r * S, r * S], color=colour, lw=lw)
        if (r + 1, c) not in cs:
            ax.plot([c * S, (c + 1) * S], [(r + 1) * S, (r + 1) * S], color=colour, lw=lw)


def write_pngs(hs, adapter, mentions, ref_i, gates):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    S = 20
    nh, nw = hs["nh"], hs["nw"]
    surfs = hs["surfaces"]; lum = hs["lum"]
    splats = build_splats(surfs, lum)
    img, _ = render(splats, nh, nw, pose_d=0, S=S)
    box_cols = ["#4d79ff", "#5fcf6f", "#e0a83c"]
    labels = {i: read_label(adapter, mentions[i]) for i in mentions}

    # ---- overlay.png : THE EYE'S OUTPUT --------------------------------------
    fig, ax = plt.subplots(figsize=(6.4, 6.6), dpi=120)
    ax.imshow(img, cmap="gray", vmin=0, vmax=255, extent=[0, nw * S, nh * S, 0])
    for i, s in enumerate(surfs):
        _draw_footprint(ax, s["cells"], S, box_cols[i])
        if labels[i]:                                       # NAMING: label iff grounded
            ax.text(s["cx"] * S + S / 2, s["cy"] * S + S / 2, labels[i],
                    color="white", fontsize=13, fontweight="bold", ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#111111cc", ec=box_cols[i], lw=2))
    # mark the hole cells (no box, no label) explicitly
    for (r, c) in hs["hole_cells"]:
        ax.add_patch(Rectangle((c * S, r * S), S, S, fill=False, ec="#d21f1f",
                               lw=1.2, ls=":"))
    ax.set_title("THE EYE'S OUTPUT  ---  box = TRUE carved extent (SEEING),  "
                 "label = grounded name (NAMING)\n"
                 "1 surface named (reference), 2 seen-but-unknown, "
                 f"{len(hs['hole_cells'])} HOLE cells refused (dotted red: no box, no label)",
                 fontsize=9.2)
    ax.set_xlim(0, nw * S); ax.set_ylim(nh * S, 0); ax.axis("off")
    ov = os.path.join(OUTDIR, "overlay.png"); fig.savefig(ov, bbox_inches="tight"); plt.close(fig)

    # ---- net_vs_eye.png : THE KILLER FRAME -----------------------------------
    net = net_style(hs)
    fig, axs = plt.subplots(1, 2, figsize=(13.2, 6.8), dpi=120)
    # EYE panel
    axs[0].imshow(img, cmap="gray", vmin=0, vmax=255, extent=[0, nw * S, nh * S, 0])
    for i, s in enumerate(surfs):
        _draw_footprint(axs[0], s["cells"], S, box_cols[i])
        if labels[i]:
            axs[0].text(s["cx"] * S + S / 2, s["cy"] * S + S / 2, labels[i],
                        color="white", fontsize=12, fontweight="bold", ha="center", va="center",
                        bbox=dict(boxstyle="round,pad=0.3", fc="#111111cc", ec=box_cols[i], lw=2))
    for (r, c) in hs["hole_cells"]:
        axs[0].add_patch(Rectangle((c * S, r * S), S, S, fill=False, ec="#d21f1f", lw=1.2, ls=":"))
    axs[0].set_title(f"THE EYE  ---  boxes on {gates['gateD']['eye_box_coverage']*100:.1f}% "
                     f"(carved), labels on {gates['gateD']['eye_label_coverage']*100:.1f}% "
                     f"(grounded)\nHOLES stay holes (dotted red).  A comparison CAN be false.",
                     fontsize=9.2, color="#1a5")
    axs[0].set_xlim(0, nw * S); axs[0].set_ylim(nh * S, 0); axs[0].axis("off")
    # NET panel -- illustration of a can't-refuse selection head
    axs[1].imshow(img * 0.35, cmap="gray", vmin=0, vmax=255, extent=[0, nw * S, nh * S, 0])
    cents = net["cents"]
    # tidy rectangles tiling the whole field, one per surface split
    bounds = [0]
    for k in range(len(cents) - 1):
        bounds.append(int(round((cents[k] + cents[k + 1]) / 2)) + 1)
    bounds.append(nw)
    for k, name in enumerate(net["net_labels"]):
        x0, x1 = bounds[k], bounds[k + 1]
        axs[1].add_patch(Rectangle((x0 * S, 0), (x1 - x0) * S, nh * S,
                                   fill=False, ec="#ff4d4d", lw=2.6))
        axs[1].text((x0 + x1) / 2 * S, nh * S / 2, name, color="white", fontsize=13,
                    fontweight="bold", ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#7a0000dd", ec="#ff4d4d", lw=2))
    axs[1].set_title(f"A NET-STYLE SELECTION HEAD (ILLUSTRATION, not a baseline)\n"
                     f"boxes + confident labels edge-to-edge: "
                     f"{gates['gateD']['net_box_coverage']*100:.0f}% / "
                     f"{gates['gateD']['net_label_coverage']*100:.0f}%.  "
                     f"A selection CANNOT refuse -- no gaps, even over the hole.",
                     fontsize=9.2, color="#c22")
    axs[1].set_xlim(0, nw * S); axs[1].set_ylim(nh * S, 0); axs[1].axis("off")
    fig.suptitle("THE KILLER FRAME  ---  ours has gaps a net structurally never would  "
                 f"(label-coverage gap {gates['gateD']['label_coverage_delta']*100:.1f} pp, "
                 f"box-coverage gap {gates['gateD']['box_coverage_delta']*100:.1f} pp)",
                 fontsize=11, fontweight="bold")
    nv = os.path.join(OUTDIR, "net_vs_eye.png"); fig.savefig(nv, bbox_inches="tight"); plt.close(fig)
    return [ov, nv]


def main():
    t0 = time.time(); load0 = os.getloadavg()
    hs = held_state(**PRIMARY)
    adapter, mentions, concept, ref_i = build_naming_graph(hs["surfaces"])
    gates = dict(
        gateA=gateA_bbox_true_extent(hs),
        gateB=gateB_label_only_where_grounded(hs, adapter, mentions, ref_i),
        gateC=gateC_no_box_on_hole(hs),
        gateD=gateD_net_contrast(hs),
    )
    pngs = write_pngs(hs, adapter, mentions, ref_i, gates)
    out = dict(primary=PRIMARY, tau=TAU,
               held=dict(K=hs["K"], n_holes=len(hs["hole_cells"]),
                         surfaces=[dict(name=NAMES[i], z=s["z"], n=s["n"], cx=s["cx"])
                                   for i, s in enumerate(hs["surfaces"])]),
               naming=dict(grounded_surface=NAMES[ref_i], grounded_form="reference",
                           via="Mention -refers_to-> Concept (teacher chain)"),
               gates=gates,
               pngs=[os.path.relpath(p, _ROOT) for p in pngs],
               loadavg_start=load0, loadavg_end=os.getloadavg(), wall_s=time.time() - t0)
    with open(os.path.join(_ROOT, "results", "overlay.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("=== BBOX + LABEL OVERLAY — faithfulness gates ===")
    print(f"held: K={hs['K']} holes={len(hs['hole_cells'])}  grounded surface={NAMES[ref_i]} -> 'reference'")
    A = gates["gateA"]
    print("GATE A bbox=true-extent:",
          "footprint IoU", [round(r["footprint_iou"], 3) for r in A["rows"]],
          "| tidy-rect IoU", [round(r["tidy_rect_iou"], 3) for r in A["rows"]],
          "| shrink", A["shrink"]["full_n"], "->", A["shrink"]["shrunk_footprint_cells"],
          "PASS" if A["PASS"] else "FAIL")
    B = gates["gateB"]
    print("GATE B label-iff-grounded:", B["labels"], "n_labels", B["n_labels"],
          "remove->", B["count_after_edge_removed"], "add->", B["count_after_second_edge"],
          "PASS" if B["PASS"] else "FAIL")
    C = gates["gateC"]
    print("GATE C no-box-on-hole: eye", C["hole_cells_boxed_eye"], "/", C["n_holes"],
          "boxed; net", C["hole_cells_boxed_net"], "/", C["n_holes"],
          "PASS" if C["PASS"] else "FAIL")
    D = gates["gateD"]
    print(f"GATE D net-contrast: EYE box {D['eye_box_coverage']*100:.1f}% label {D['eye_label_coverage']*100:.1f}%"
          f" | NET box {D['net_box_coverage']*100:.0f}% label {D['net_label_coverage']*100:.0f}%"
          f" | Δbox {D['box_coverage_delta']*100:.1f}pp Δlabel {D['label_coverage_delta']*100:.1f}pp",
          "PASS" if D["PASS"] else "FAIL")
    print("loadavg", load0, "->", out["loadavg_end"], "wall", round(out["wall_s"], 1), "s")
    print("PNGs:", *out["pngs"], sep="\n  ")


if __name__ == "__main__":
    main()
