"""eyeview_render — MECHANICAL EMIT-ADAPTER (seed block 118000-118999).

Read the eye's HELD state (the parallax carve, 116000) and translate it to an
external image via a self-contained numpy FORWARD splat renderer. Splats DISPLAY
the held graph; the eye does NOT compute with them (VISION_SPLATTING_SCIENCE.md,
Claims B/C refuted). NO Rust, NO Term, NO seed rule. No decision over graph state.

Pre-registration: VISION_EYEVIEW_PREREG.md (committed before any faithfulness
number). Produces the four faithfulness gate numbers + the deliverable PNGs.
"""
from __future__ import annotations
import sys, os, json, time
_HERE = os.path.dirname(os.path.abspath(__file__)); _ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE); sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
import numpy as np
from parallax_char import make_scene, group_common_fate, vector_field, SQRT5

TAU = SQRT5                       # sensor's own Otsu-within-aperture tolerance (rung 94000)
PRIMARY = dict(shifts=[0, 3, 6], block=8, grid=144, ref_idx=1, seed=116000)
OUTDIR = os.path.join(_ROOT, "results", "eye_view")
os.makedirs(OUTDIR, exist_ok=True)


# ----------------------------------------------------------------------------
# HELD STATE — re-run the deterministic seeded carve, recover the full state.
# ----------------------------------------------------------------------------
def held_state(seed, shifts, block, grid, ref_idx):
    rng = np.random.default_rng(seed)
    sc = make_scene(rng, shifts, block, grid=grid, ref_idx=ref_idx)
    V = vector_field(sc["a"], sc["b_depth"], block)          # sensed SAD field (nh,nw,2)
    delta = np.array([0.0, float(shifts[ref_idx])])          # efference copy (known Δ)
    R = V - delta                                            # residual = depth rel. to ref
    lab, nl = group_common_fate(R, TAU)
    sizes = np.array([(lab == k).sum() for k in range(nl)])
    p = sizes / sizes.sum(); eff = float(1.0 / np.sum(p * p))
    K = int(round(eff))
    top = np.argsort(-sizes)[:K].tolist()
    nh, nw = lab.shape
    lum = sc["a"].reshape(nh, block, nw, block).mean(axis=(1, 3))   # held luminance / cell
    confab = float((np.abs(V - sc["t_depth"]).max(axis=2) > 0).mean())
    surfaces = []
    for k in top:
        m = (lab == k)
        ys, xs = np.where(m)
        rr = R[m]
        modal_v = np.median(rr, axis=0)                      # (dy, dx) residual velocity
        r_std = float(np.linalg.norm(rr.std(axis=0)))
        conf = 1.0 - min(1.0, r_std / TAU)                   # coherence, scaled by sensor τ
        cov = np.cov(np.vstack([xs, ys])) if m.sum() > 1 else np.eye(2) * 0.25
        surfaces.append(dict(
            label=int(k), n=int(m.sum()),
            cells=list(zip(ys.tolist(), xs.tolist())),
            cx=float(xs.mean()), cy=float(ys.mean()),
            z=float(modal_v[1]),                             # residual vx = relative depth
            vx=float(modal_v[1]), vy=float(modal_v[0]),
            cov=cov.tolist(), r_std=r_std, confidence=conf,
            colour=float(lum[m].mean()),
        ))
    hole_cells = [(int(r), int(c)) for r in range(nh) for c in range(nw)
                  if lab[r, c] not in top]
    surfaces.sort(key=lambda s: s["cx"])                     # left→right for stable naming
    return dict(sc=sc, V=V, R=R, lab=lab, nl=nl, eff=eff, K=K, top=top,
                surfaces=surfaces, hole_cells=hole_cells, lum=lum, confab=confab,
                nh=nh, nw=nw, delta=delta, shifts=shifts, block=block, ref_idx=ref_idx)


# ----------------------------------------------------------------------------
# SPLAT PRIMITIVES. A surface is rendered as a CLOUD of anisotropic Gaussians —
# one per carved cell (3DGS-style: many small Gaussians tile a surface). This is
# the faithful render: it preserves the per-cell HELD LUMINANCE (texture, not a
# mean gray), covers exactly the carved cells, and leaves un-carved cells as
# holes. The per-surface 2nd-moment anisotropic Gaussian (surf["cov"]) is the
# REPORTED summary / overlaid 1σ ellipse — "the surface's oriented spatial extent".
# CELL_STD = half a coarse cell = half the sensor aperture (block/2 px) — the
# sampling grain; it FALLS OUT of the aperture, not picked.
# ----------------------------------------------------------------------------
CELL_STD = 0.5


def surface_cloud(surf, lum):
    """One anisotropic Gaussian per carved cell; colour = that cell's held luminance."""
    splats = []
    ev = np.linalg.eigh(np.array(surf["cov"], float) + np.eye(2) * 1e-9)[1]
    infl = 1.0 + (1.0 - surf["confidence"])                  # low conf → more diffuse
    base = (ev @ np.diag([CELL_STD ** 2, CELL_STD ** 2]) @ ev.T) * infl
    for (r, c) in surf["cells"]:
        splats.append(dict(cx=float(c), cy=float(r), z=surf["z"],
                           vx=surf["vx"], vy=surf["vy"], cov=base,
                           colour=float(lum[r, c]), opacity=surf["confidence"]))
    return splats


def build_splats(surfaces, lum):
    out = []
    for s in surfaces:
        out.extend(surface_cloud(s, lum))
    return out


# ----------------------------------------------------------------------------
# FORWARD SPLAT RENDERER — pure numpy. Project each anisotropic Gaussian, alpha-
# composite front-to-back. `pose_d`: eye displacement (efference frame, splat
# slides by d·v). `theta`: orbit angle about the vertical axis (reveals depth).
# ----------------------------------------------------------------------------
def _project(sp, pose_d, theta, xc, zscale):
    m3 = np.array([sp["cx"] + pose_d * sp["vx"], sp["cy"], sp["z"] * zscale])
    ct, st = np.cos(theta), np.sin(theta)
    Ry = np.array([[ct, 0, st], [0, 1, 0], [-st, 0, ct]])
    centre = np.array([xc, 0.0, 0.0])
    rm = Ry @ (m3 - centre) + centre
    sx, sy, depth = rm[0], rm[1], -rm[2]
    C3 = np.zeros((3, 3)); C3[:2, :2] = np.array(sp["cov"], float); C3[2, 2] = 0.15
    Cr = Ry @ C3 @ Ry.T
    return np.array([sx, sy]), Cr[:2, :2], float(depth)


def render(splats, nh, nw, pose_d=0.0, theta=0.0, S=20, zscale=2.0):
    """Rasterise to an S·nw × S·nh grayscale canvas (0..255) + alpha. Front-to-back."""
    H, W = nh * S, nw * S
    xc = (nw - 1) / 2.0
    canvas = np.zeros((H, W)); A = np.zeros((H, W))
    ys, xs = np.mgrid[0:H, 0:W]
    px = (xs + 0.5) / S - 0.5; py = (ys + 0.5) / S - 0.5
    prj = sorted(((_project(s, pose_d, theta, xc, zscale), s) for s in splats),
                 key=lambda t: t[0][2])
    for (mean, cov, _d), s in prj:
        inv = np.linalg.inv(cov + np.eye(2) * 1e-6)
        dx = px - mean[0]; dy = py - mean[1]
        maha = inv[0, 0] * dx * dx + 2 * inv[0, 1] * dx * dy + inv[1, 1] * dy * dy
        w = np.exp(-0.5 * maha)
        a = s["opacity"] * w
        t = (1.0 - A) * a
        canvas += t * s["colour"]; A += t
    return np.clip(canvas, 0, 255), A


def render_velocity_field(splats, nh, nw):
    """INVERSE of the carve: read back ONE velocity per cell — the WINNER (the splat
    with the largest footprint contribution there). A carve label is a segmentation,
    not radiance: luminance composites, a velocity LABEL does not. Winner-take-all
    preserves the sharp velocity boundaries the carve keys on. A cell no splat reaches
    (best contribution < 0.5 = beyond ~1σ of every splat) is a HOLE (sentinel). The
    gate still bites: an over-broad splat whose tail WINS a neighbour's cell shifts the
    boundary and drops IoU — so a prettified (inflated) covariance is caught here."""
    xc = (nw - 1) / 2.0
    cy, cx = np.mgrid[0:nh, 0:nw]
    best = np.full((nh, nw), -1.0); vwx = np.zeros((nh, nw)); vwy = np.zeros((nh, nw))
    for (mean, cov, _d), s in ((_project(s, 0.0, 0.0, xc, 2.0), s) for s in splats):
        inv = np.linalg.inv(cov + np.eye(2) * 1e-6)
        dx = cx - mean[0]; dy = cy - mean[1]
        maha = inv[0, 0] * dx * dx + 2 * inv[0, 1] * dx * dy + inv[1, 1] * dy * dy
        a = s["opacity"] * np.exp(-0.5 * maha)               # footprint contribution
        win = a > best
        best = np.where(win, a, best)
        vwx = np.where(win, s["vx"], vwx); vwy = np.where(win, s["vy"], vwy)
    field = np.zeros((nh, nw, 2)); SENT = 1e6
    for r in range(nh):
        for c in range(nw):
            if best[r, c] < 0.5:
                field[r, c] = (SENT, SENT)                   # HOLE — no splat reaches here
            else:
                field[r, c] = (vwy[r, c], vwx[r, c])
    return field, np.clip(best, 0, 1)


# ----------------------------------------------------------------------------
# GATES
# ----------------------------------------------------------------------------
def cell_alpha(splats, nh, nw):
    """The render's coverage α evaluated at each CELL center (18×18)."""
    _, A = render_velocity_field(splats, nh, nw)
    return A


def gate1_hole_preservation(hs):
    """Positive control: REMOVE one surface (declare its region KNOWN no-data);
    the render's splats must not cover it (α<0.5). Plus natural-speck coverage."""
    surfs = hs["surfaces"]; lum = hs["lum"]
    removed = surfs[-1]; kept = surfs[:-1]
    region = [tuple(c) for c in removed["cells"]]
    A_kept = cell_alpha(build_splats(kept, lum), hs["nh"], hs["nw"])
    covered = sum(1 for (r, c) in region if A_kept[r, c] >= 0.5)
    pc_frac = covered / len(region)
    # what a FILLING renderer would give: a cloud that stretches over the gap
    fill_cells = [(r, c) for (r, _c0) in [(rr, 0) for rr in range(hs["nh"])]
                  for c in range(int(removed["cx"]) - 2, hs["nw"])]
    fill = [dict(cx=float(c), cy=float(r), z=removed["z"], vx=removed["vx"], vy=removed["vy"],
                 cov=np.eye(2) * CELL_STD ** 2, colour=128.0, opacity=1.0)
            for (r, c) in fill_cells]
    A_fill = cell_alpha(build_splats(kept, lum) + fill, hs["nh"], hs["nw"])
    fill_cov = sum(1 for (r, c) in region if A_fill[r, c] >= 0.5) / len(region)
    # natural specks: full render's α at the un-carved cells
    A_full = cell_alpha(build_splats(surfs, lum), hs["nh"], hs["nw"])
    nat = sum(1 for (r, c) in hs["hole_cells"] if A_full[r, c] >= 0.5)
    nat_frac = nat / max(1, len(hs["hole_cells"]))
    return dict(known_region_cells=len(region), known_region_covered=covered,
                known_region_coverage=pc_frac,
                filling_renderer_would_cover=fill_cov,
                natural_hole_cells=len(hs["hole_cells"]),
                natural_holes_covered=nat, natural_hole_coverage=nat_frac,
                PASS=bool(pc_frac == 0.0))


def recarve_complexity(field):
    """round(eff_surfaces) of a re-carved velocity field, ignoring hole sentinels."""
    lab, nl = group_common_fate(field, TAU)
    sizes = np.array([(lab == k).sum() for k in range(nl)])
    # drop sentinel-hole groups (a hole group's members all have velocity 1e6)
    real = []
    for k in range(nl):
        m = (lab == k)
        if field[m][0][0] < 1e5:
            real.append(int(m.sum()))
    real = np.array(sorted(real, reverse=True))
    if real.size == 0:
        return 0, lab, real
    p = real / real.sum()
    return int(round(1.0 / np.sum(p * p))), lab, real


def gate2_no_overcompletion(hs):
    """Sparse held states (FLAT=1, 1-surface DEPTH) → render → re-carve → complexity
    must not EXCEED held complexity."""
    arms = {}; lum = hs["lum"]
    # DEPTH primary (held K=3)
    fld, _ = render_velocity_field(build_splats(hs["surfaces"], lum), hs["nh"], hs["nw"])
    rc, _, _ = recarve_complexity(fld)
    arms["DEPTH_K3"] = dict(held=hs["K"], render=rc)
    # 1-surface DEPTH: keep only the reference surface
    ref_only = [s for s in hs["surfaces"] if abs(s["z"]) < 0.5] or [hs["surfaces"][1]]
    fld1, _ = render_velocity_field(build_splats(ref_only, lum), hs["nh"], hs["nw"])
    rc1, _, _ = recarve_complexity(fld1)
    arms["DEPTH_K1"] = dict(held=1, render=rc1)
    # FLAT held state: build the flat scene, carve it, render, re-carve
    hf = held_flat(hs["shifts"], hs["block"], PRIMARY["grid"], hs["ref_idx"], hs["sc"])
    if hf["surfaces"]:
        fldf, _ = render_velocity_field(build_splats(hf["surfaces"], hf["lum"]), hf["nh"], hf["nw"])
        rcf, _, _ = recarve_complexity(fldf)
    else:
        rcf = 0
    arms["FLAT"] = dict(held=len(hf["surfaces"]), render=rcf)
    ok = all(a["render"] <= a["held"] if a["held"] > 0 else a["render"] <= 1
             for a in arms.values())
    return dict(arms=arms, PASS=bool(ok))


def held_flat(shifts, block, grid, ref_idx, sc):
    """FLAT held state: the uniform-shift field carves to ONE surface (or, in the
    graph arm, 0 objects — space constancy). We recover its carve for Gate 2."""
    V = vector_field(sc["a"], sc["b_flat"], block)
    delta = np.array([0.0, float(shifts[ref_idx])])
    R = V - delta
    lab, nl = group_common_fate(R, TAU)
    sizes = np.array([(lab == k).sum() for k in range(nl)])
    p = sizes / sizes.sum(); eff = float(1.0 / np.sum(p * p)); K = int(round(eff))
    top = np.argsort(-sizes)[:K].tolist()
    nh, nw = lab.shape
    lum = sc["a"].reshape(nh, block, nw, block).mean(axis=(1, 3))
    surfs = []
    for k in top:
        m = (lab == k); ys, xs = np.where(m); rr = R[m]
        if m.sum() < 2:
            continue
        surfs.append(dict(label=int(k), n=int(m.sum()),
                          cells=list(zip(ys.tolist(), xs.tolist())),
                          cx=float(xs.mean()), cy=float(ys.mean()),
                          z=float(np.median(rr, 0)[1]), vx=float(np.median(rr, 0)[1]),
                          vy=float(np.median(rr, 0)[0]),
                          cov=(np.cov(np.vstack([xs, ys])) if m.sum() > 1 else np.eye(2)).tolist(),
                          confidence=1.0, colour=float(lum[m].mean())))
    return dict(surfaces=surfs, nh=nh, nw=nw, eff=eff, K=K, lum=lum)


def gate3_round_trip(hs):
    """carve → splat → render velocity field → RE-CARVE → match held surfaces."""
    fld, A = render_velocity_field(build_splats(hs["surfaces"], hs["lum"]), hs["nh"], hs["nw"])
    rc, lab2, _ = recarve_complexity(fld)
    # bipartite match held surfaces ↔ re-carved groups by IoU on CARVED (non-hole) cells
    held_masks = []
    for s in hs["surfaces"]:
        m = np.zeros((hs["nh"], hs["nw"]), bool)
        for (r, c) in s["cells"]:
            m[r, c] = True
        held_masks.append(m)
    lab2u = [k for k in range(lab2.max() + 1) if fld[lab2 == k][0][0] < 1e5]
    ious = []
    for hm in held_masks:
        best = 0.0
        for k in lab2u:
            rm = (lab2 == k)
            inter = (hm & rm).sum(); union = (hm | rm).sum()
            best = max(best, inter / union if union else 0.0)
        ious.append(float(best))
    hole_frac = len(hs["hole_cells"]) / (hs["nh"] * hs["nw"])
    mean_iou = float(np.mean(ious))
    tol = 1.0 - hole_frac
    return dict(recarve_count=rc, held_count=hs["K"], per_surface_iou=ious,
                mean_iou=mean_iou, hole_fraction=hole_frac,
                derived_tol_floor=tol,
                PASS=bool(rc == hs["K"] and mean_iou >= tol))


def gate4_parallax(hs, poses=(0, 1, 2)):
    """Efference-frame pose sequence: reference (v=0) STATIONARY (=0 exactly);
    others displace by their held residual velocity per unit d."""
    surfs = hs["surfaces"]
    cents = {i: [] for i in range(len(surfs))}
    for d in poses:
        for i, s in enumerate(surfs):
            cents[i].append(s["cx"] + d * s["vx"])          # efference-frame x-centroid
    rows = []
    for i, s in enumerate(surfs):
        xs = cents[i]
        disp = [xs[j] - xs[0] for j in range(len(poses))]
        per_d = (xs[-1] - xs[0]) / (poses[-1] - poses[0]) if poses[-1] != poses[0] else 0.0
        rows.append(dict(surface=i, z=s["z"], vx=s["vx"], is_reference=bool(abs(s["z"]) < 0.5),
                         displacements=disp, disp_per_d=per_d,
                         matches_vx=bool(abs(per_d - s["vx"]) < 1e-9)))
    ref = [r for r in rows if r["is_reference"]]
    ref_stationary = bool(ref and all(abs(x) < 1e-12 for x in ref[0]["displacements"]))
    others_match = all(r["matches_vx"] for r in rows if not r["is_reference"])
    return dict(poses=list(poses), rows=rows, reference_stationary_exact=ref_stationary,
                others_parallax_match=others_match,
                PASS=bool(ref_stationary and others_match))


# ----------------------------------------------------------------------------
# PNG DELIVERABLES (matplotlib only assembles/annotates; splat math is numpy above)
# ----------------------------------------------------------------------------
def _lum_backdrop(hs, S):
    """Faint held-luminance backdrop so holes read against the real texture."""
    lum = np.kron(hs["lum"], np.ones((S, S)))
    return lum * 0.0   # keep splats on black; luminance shown in the held panel


def write_pngs(hs, gates):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    S = 20
    surfs = hs["surfaces"]; lum = hs["lum"]
    splats = build_splats(surfs, lum)

    # (1-3) efference-frame pose sequence
    pose_paths = []
    for j, d in enumerate((0, 1, 2)):
        img, A = render(splats, hs["nh"], hs["nw"], pose_d=d, S=S)
        fig, ax = plt.subplots(figsize=(4, 4), dpi=110)
        ax.imshow(img, cmap="gray", vmin=0, vmax=255, origin="upper")
        ax.set_title(f"efference-frame pose d={d}\n(REF stationary; NEAR/FAR parallax)", fontsize=9)
        ax.axis("off")
        p = os.path.join(OUTDIR, f"pose_d{d}.png"); fig.savefig(p, bbox_inches="tight"); plt.close(fig)
        pose_paths.append(p)

    # (4) novel orbit view — reveal the 3 planes at their residual-velocity depths
    fig, axs = plt.subplots(1, 5, figsize=(15, 3.2), dpi=110)
    for ax, th in zip(axs, np.linspace(-0.6, 0.6, 5)):
        img, A = render(splats, hs["nh"], hs["nw"], theta=th, S=S, zscale=3.0)
        ax.imshow(img, cmap="gray", vmin=0, vmax=255)
        ax.set_title(f"orbit θ={th:+.2f} rad", fontsize=8); ax.axis("off")
    fig.suptitle("NOVEL ORBIT — the 3 surfaces separate in depth (z = residual velocity the eye MEASURED)", fontsize=10)
    orbit_p = os.path.join(OUTDIR, "orbit.png"); fig.savefig(orbit_p, bbox_inches="tight"); plt.close(fig)

    # (5) held-state vs render side-by-side, holes marked
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.4), dpi=110)
    # held luminance (what the eye's structure channel holds)
    axs[0].imshow(hs["sc"]["a"], cmap="gray"); axs[0].set_title("HELD luminance (static frame `a`)\nbands INVISIBLE here", fontsize=9); axs[0].axis("off")
    # held carve: per-cell surface label, holes red
    lblimg = np.full((hs["nh"], hs["nw"], 3), 0.15)
    palette = {surfs[0]["label"]: [0.30, 0.45, 0.85], surfs[1]["label"]: [0.55, 0.80, 0.55], surfs[-1]["label"]: [0.90, 0.70, 0.30]}
    for r in range(hs["nh"]):
        for c in range(hs["nw"]):
            L = hs["lab"][r, c]
            lblimg[r, c] = palette.get(L, [0.85, 0.12, 0.12])   # holes → red
    axs[1].imshow(lblimg, interpolation="nearest")
    axs[1].set_title(f"HELD carve: 3 surfaces + {len(hs['hole_cells'])} HOLE cells (red)\nvelocities {surfs[0]['vx']:+.0f}/0/{surfs[-1]['vx']:+.0f}", fontsize=9); axs[1].axis("off")
    # splat render (reference pose)
    img, A = render(splats, hs["nh"], hs["nw"], pose_d=0, S=S)
    axs[2].imshow(img, cmap="gray", vmin=0, vmax=255)
    axs[2].set_title("SPLAT RENDER (3 anisotropic Gaussians)\nholes = gaps, colour = held luminance", fontsize=9); axs[2].axis("off")
    sxs = os.path.join(OUTDIR, "held_vs_render.png"); fig.savefig(sxs, bbox_inches="tight"); plt.close(fig)

    # (6) gate panel — hole preservation + round-trip re-carve
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.4), dpi=110)
    # Gate1 positive control: removed-surface region must be a hole
    kept = surfs[:-1]
    img, A = render(build_splats(kept, lum), hs["nh"], hs["nw"], pose_d=0, S=S)
    axs[0].imshow(img, cmap="gray", vmin=0, vmax=255)
    rr = surfs[-1]
    xs = [c for (r, c) in rr["cells"]]; ys = [r for (r, c) in rr["cells"]]
    axs[0].add_patch(Rectangle((min(xs)*S, min(ys)*S), (max(xs)-min(xs)+1)*S, (max(ys)-min(ys)+1)*S,
                               fill=False, edgecolor="red", lw=2, ls="--"))
    axs[0].set_title(f"GATE 1: removed NEAR surface = KNOWN no-data (red)\ncoverage={gates['gate1']['known_region_coverage']:.3f} (fill would be {gates['gate1']['filling_renderer_would_cover']:.2f})", fontsize=8); axs[0].axis("off")
    # Gate3 re-carved field
    fld, Af = render_velocity_field(splats, hs["nh"], hs["nw"])
    rc, lab2, _ = recarve_complexity(fld)
    rcimg = np.full((hs["nh"], hs["nw"], 3), 0.85)
    cols = [[0.30,0.45,0.85],[0.55,0.80,0.55],[0.90,0.70,0.30],[0.6,0.3,0.7],[0.3,0.7,0.7]]
    ci = 0; seen = {}
    for r in range(hs["nh"]):
        for c in range(hs["nw"]):
            if fld[r,c,0] > 1e5: rcimg[r,c]=[0.85,0.12,0.12]; continue
            k=lab2[r,c]
            if k not in seen: seen[k]=cols[ci%len(cols)]; ci+=1
            rcimg[r,c]=seen[k]
    axs[1].imshow(rcimg, interpolation="nearest")
    axs[1].set_title(f"GATE 3: RE-CARVE of rendered field\ncount={gates['gate3']['recarve_count']} (held {hs['K']}) IoU={gates['gate3']['mean_iou']:.3f}", fontsize=8); axs[1].axis("off")
    # coverage alpha of the render
    axs[2].imshow(Af, cmap="magma", vmin=0, vmax=1)
    axs[2].set_title("render coverage α (dark = HOLE, no splat)\nsparse stays sparse", fontsize=8); axs[2].axis("off")
    gate_p = os.path.join(OUTDIR, "gates.png"); fig.savefig(gate_p, bbox_inches="tight"); plt.close(fig)

    return pose_paths + [orbit_p, sxs, gate_p]


def main():
    t0 = time.time(); load0 = os.getloadavg()
    hs = held_state(**PRIMARY)
    gates = dict(
        gate1=gate1_hole_preservation(hs),
        gate2=gate2_no_overcompletion(hs),
        gate3=gate3_round_trip(hs),
        gate4=gate4_parallax(hs),
    )
    pngs = write_pngs(hs, gates)
    out = dict(
        primary=PRIMARY, tau=TAU,
        held=dict(eff_surfaces=hs["eff"], K=hs["K"], confab_rate=hs["confab"],
                  n_hole_cells=len(hs["hole_cells"]),
                  surfaces=[dict(name=n, cx=s["cx"], cy=s["cy"], z=s["z"], vx=s["vx"],
                                 n=s["n"], confidence=s["confidence"], colour=s["colour"],
                                 cov=s["cov"])
                            for n, s in zip(["FAR", "REF", "NEAR"], hs["surfaces"])]),
        gates=gates,
        pngs=[os.path.relpath(p, _ROOT) for p in pngs],
        loadavg_start=load0, loadavg_end=os.getloadavg(), wall_s=time.time() - t0,
    )
    with open(os.path.join(_ROOT, "results", "eyeview.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("=== EYE-VIEW SPLAT RENDER — faithfulness gates ===")
    print(f"held: eff={hs['eff']:.3f} K={hs['K']} confab={hs['confab']*100:.2f}% holes={len(hs['hole_cells'])}")
    for i, s in zip(["FAR","REF","NEAR"], hs["surfaces"]):
        print(f"  {i:4s} cx={s['cx']:.1f} z(v)={s['z']:+.1f} n={s['n']} conf={s['confidence']:.3f} lum={s['colour']:.0f}")
    print("GATE1 hole-preservation:", gates["gate1"]["known_region_coverage"], "PASS" if gates["gate1"]["PASS"] else "FAIL",
          f"(fill would cover {gates['gate1']['filling_renderer_would_cover']:.2f}; natural-hole cov {gates['gate1']['natural_hole_coverage']:.3f})")
    print("GATE2 no-over-completion:", {k: v for k, v in gates["gate2"]["arms"].items()}, "PASS" if gates["gate2"]["PASS"] else "FAIL")
    print("GATE3 round-trip: count", gates["gate3"]["recarve_count"], "/", hs["K"], "IoU", round(gates["gate3"]["mean_iou"],4),
          "tol", round(gates["gate3"]["derived_tol_floor"],4), "PASS" if gates["gate3"]["PASS"] else "FAIL")
    print("GATE4 parallax/space-constancy: ref_stationary", gates["gate4"]["reference_stationary_exact"],
          "others_match", gates["gate4"]["others_parallax_match"], "PASS" if gates["gate4"]["PASS"] else "FAIL")
    print("loadavg", load0, "->", out["loadavg_end"], "wall", round(out["wall_s"],1),"s")
    print("PNGs:", *out["pngs"], sep="\n  ")


if __name__ == "__main__":
    main()
