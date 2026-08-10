"""robust_geometry_measure — block 211000. Does a SEEN geometry feature beat chance on real E1M1?

The 209000 geometry channel (SEEN depth-from-motion per-column) is CHANCE (AUC 0.508). This
block ships a SEEN STRUCTURAL horizontal-edge feature (`col_structural_level` in
`domains/doom_pattern_eye.py`) — the ORTHOGONAL twin of the vertical-gradient texture channel —
and measures it against a depth-EDGE (occluding-contour) scoring oracle.

HARD CONSTRAINT (209000): the geometry signal is SEEN rendered pixels (integer luma) ONLY. The
VizDoom depth buffer / sectors / labels / texture names are a SCORING ORACLE, never fed to the
eye (AST-audited by `assert_no_oracle_in_geometry_eye` below + the migrated test).

    PYTHONPATH=. python3 scripts/robust_geometry_measure.py

Integer-native, no Rust, no seed change: the geometry feature is mechanical eye I/O over pixels.
"""
from __future__ import annotations
import argparse, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import domains.doom_pattern_eye as eye

GH, GW = 240, 320
OUTDIR = os.path.join(ROOT, "results", "pattern_eye")

# Two independent E1M1 routes (validated out-of-sample). action[3] is the 4-button vector
# (MOVE_FORWARD, TURN_LEFT, TURN_RIGHT, USE); the 3-vector stored on the frame is [fwd,L,R].
ROUTES = {
    "walk_rturn": [([0, 0, 1, 0] if i % 18 in (14, 15, 16) else [1, 0, 0, 0]) for i in range(300)],
    "walk_lturn": [([0, 1, 0, 0] if i % 30 in (24, 25, 26, 27) else [1, 0, 0, 0]) for i in range(300)],
}


# ---------------------------------------------------------------- SCORING ORACLE (depth buffer)
def depth_edge_oracle(db, pct=95):
    """A column is a DEPTH EDGE (occluding contour / door frame / recess boundary / corner) iff
    its central-band median depth has |horizontal gradient| in the top (100-pct)% for the frame.
    Computed PURELY from the depth buffer (SCORING ONLY) — NO luma, never fed to the eye."""
    import numpy as np
    col = np.median(db[GH // 3: 2 * GH // 3], 0)
    if col.max() - col.min() < 1.0:
        return None
    grad = np.abs(np.gradient(col))
    return (grad >= max(np.percentile(grad, pct), 1.0)).astype(int)


def struct_oracle_209000(db):
    """209000's `_struct_oracle` (depth deviation OR gradient, ~42% positive) — deviation-dominated
    and a POOR target for an edge feature; reported only for apples-to-apples continuity."""
    import numpy as np
    col = np.median(db[GH // 3: 2 * GH // 3], 0)
    if col.max() - col.min() < 1.0:
        return None
    dev = col - np.median(col); grad = np.abs(np.gradient(col))
    return ((dev >= max(np.percentile(dev, 85), 0.5)) | (grad >= np.percentile(grad, 92))).astype(int)


# ---------------------------------------------------------------- SEEN features (luma / motion)
def feat_geometry_shipped(rgb):
    """The SHIPPED geometry channel: eye.col_structural_level (SEEN structural horizontal edge)."""
    lvl, _ = eye.col_structural_level(rgb)
    return lvl.astype(float)


def feat_hgrad_raw(rgb):
    """Raw per-column horizontal-gradient energy (no ambient subtraction) — the ranking core."""
    import numpy as np
    lum = eye._luma_int(rgb).astype(np.int64)
    band = np.abs(np.diff(lum, axis=1))[GH // 4: 3 * GH // 4]
    e = np.zeros(GW); e[1:] = band.sum(0); return e


def feat_structural_continuous(rgb):
    """The shipped geometry feature's structural energy BEFORE the recogniser's coarse 0..K
    quantisation: horizontal-gradient energy minus the integer ambient median, clipped at 0. The
    honest information content of the channel (quantising to 0..8 for the graph costs some ranking)."""
    import numpy as np
    e = feat_hgrad_raw(rgb).astype(np.int64)
    return np.maximum(0, e - int(np.median(e))).astype(float)


def feat_texture(rgb):
    """The 209000 texture channel (vertical gradient) — control for separability."""
    lvl, _ = eye.col_texture_level(rgb)
    return lvl.astype(float)


def feat_dfm_baseline(frames, fi):
    """209000's SEEN depth-from-motion geometry (col_geometry_level) — but that function now ships
    the new feature, so we recompute the ORIGINAL depth-from-motion deviation here for the baseline."""
    import numpy as np
    z = np.full(GW, np.nan)
    if fi < 1 or frames[fi - 1]["action"] != [1, 0, 0]:
        return z
    px0, py0, _ = frames[fi - 1]["pose"]; px1, py1, _ = frames[fi]["pose"]
    Tw = math.hypot(px1 - px0, py1 - py0)
    if Tw < 1.0:
        return z
    from scripts.depth_from_motion_probe import (estimate_foe, radial_decompose,
        depth_from_motion, flag_movers, _flow_field)
    vy, vx = _flow_field(frames, fi, GH, GW, 16, None)
    if (np.sqrt(vy * vy + vx * vx) > 0.5).sum() < 8:
        return z
    foe, _ = estimate_foe(vy, vx)
    if foe is None:
        return z
    dec = radial_decompose(vy, vx, foe)
    flagged, _ = flag_movers(dec["tangential_mag"], dec["valid"])
    depth, dvalid = depth_from_motion(vy, vx, foe)
    good = dvalid & (~flagged)
    for gc in range(GW):
        col = depth[:, gc][good[:, gc]]
        if col.size >= 2:
            z[gc] = float(np.median(col)) * Tw
    m = ~np.isnan(z); out = np.full(GW, np.nan)
    if m.sum() >= 4:
        out[m] = np.abs(z[m] - np.median(z[m]))
    return out


# ---------------------------------------------------------------- metrics
def _auc(score, lab):
    import numpy as np
    score = np.asarray(score, float); lab = np.asarray(lab, int)
    m = np.isfinite(score); score, lab = score[m], lab[m]
    pos, neg = score[lab == 1], score[lab == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None, 0, 0
    allv = np.concatenate([pos, neg]); order = allv.argsort()
    ranks = np.empty(len(allv)); sv = allv[order]; i = 0
    while i < len(sv):
        j = i
        while j + 1 < len(sv) and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0; i = j + 1
    r = ranks[:len(pos)].sum()
    return (r - len(pos) * (len(pos) - 1) / 2) / (len(pos) * len(neg)), len(pos), len(neg)


def _auc_ci(score, lab, frame, n_boot=400, seed=0):
    """Frame-level bootstrap 95% CI (columns within a frame are correlated)."""
    import numpy as np
    a, npos, nneg = _auc(score, lab)
    if a is None:
        return None, None, None, npos, nneg
    score = np.asarray(score, float); lab = np.asarray(lab, int); frame = np.asarray(frame)
    rng = np.random.default_rng(seed)
    uf = np.unique(frame); idx_by = {f: np.where(frame == f)[0] for f in uf}
    boots = []
    for _ in range(n_boot):
        pick = rng.choice(uf, len(uf), replace=True)
        idx = np.concatenate([idx_by[f] for f in pick])
        ab, _, _ = _auc(score[idx], lab[idx])
        if ab is not None:
            boots.append(ab)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return round(a, 3), round(float(lo), 3), round(float(hi), 3), npos, nneg


# ---------------------------------------------------------------- no-oracle AST audit
def assert_no_oracle_in_geometry_eye():
    """RUNTIME source-audit: the geometry eye reads ONLY rendered pixels. Forbid any ACCESS of an
    oracle buffer / texture name in col_structural_level / col_geometry_level / region_descriptor."""
    import inspect, ast
    funcs = (eye._luma_int, eye.col_structural_level, eye.col_geometry_level, eye.region_descriptor)
    src = "\n".join(inspect.getsource(f) for f in funcs)
    tree = ast.parse(src)
    bad_attrs = {"depth_buffer", "labels_buffer", "labels", "sectors", "depth"}
    bad_subs = {"depth", "label", "texture", "linedef", "sectors"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in bad_attrs, f"G-no-oracle VIOLATION: geometry eye accesses .{node.attr}"
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            assert node.slice.value not in bad_subs, f"G-no-oracle VIOLATION: geometry eye indexes [{node.slice.value!r}]"
    return True


# ---------------------------------------------------------------- capture
def _capture(route):
    import numpy as np
    import scripts.doom_pattern_eye_run as R
    g, gv = R._game()
    frames = []
    for act in route:
        if g.is_episode_finished():
            break
        st = g.get_state()
        if st is None:
            break
        rgb, db = R._grab(g)
        frames.append({"rgb": rgb.astype(np.uint8), "depth": np.asarray(db, float),
                       "pose": R._pose(g, gv), "action": [1, 0, 0] if act[0] == 1 else act[:3]})
        g.make_action(act, 1)
    g.close()
    return frames


# ---------------------------------------------------------------- measure
def measure(frames_by_route, pct=95):
    import numpy as np
    assert_no_oracle_in_geometry_eye()

    # per-column samples pooled across routes, tagged by (route, frame) for the CI
    stat = {}       # feature -> lists
    STATIC = {"geometry_shipped": feat_geometry_shipped,
              "structural_continuous": feat_structural_continuous,
              "hgrad_raw": feat_hgrad_raw, "texture": feat_texture}
    for k in list(STATIC) + ["dfm_baseline_209000"]:
        stat[k] = {"depth_edge": ([], [], []), "struct_209000": ([], [], [])}
    # texture-stratified store for the shipped geometry channel (G-both-channels)
    strat = {"geo": [], "tex_raw": [], "lab": []}

    for route, frames in frames_by_route.items():
        for fi in range(len(frames)):
            db = frames[fi]["depth"]
            lab_e = depth_edge_oracle(db, pct)
            lab_s = struct_oracle_209000(db)
            rgb = frames[fi]["rgb"]
            fid = f"{route}:{fi}"
            static_vals = {k: fn(rgb) for k, fn in STATIC.items()}
            dfm = feat_dfm_baseline(frames, fi)
            for oname, lab in (("depth_edge", lab_e), ("struct_209000", lab_s)):
                if lab is None:
                    continue
                for k, s in static_vals.items():
                    for gc in np.where(np.isfinite(s))[0]:
                        stat[k][oname][0].append(float(s[gc])); stat[k][oname][1].append(int(lab[gc]))
                        stat[k][oname][2].append(fid)
                for gc in np.where(np.isfinite(dfm))[0]:
                    stat["dfm_baseline_209000"][oname][0].append(float(dfm[gc]))
                    stat["dfm_baseline_209000"][oname][1].append(int(lab[gc]))
                    stat["dfm_baseline_209000"][oname][2].append(fid)
            # texture strata use the depth-edge oracle
            if lab_e is not None:
                geo_raw = feat_hgrad_raw(rgb); tex_raw = None
                lum = eye._luma_int(rgb); band = lum[GH // 4: 3 * GH // 4]
                tex_raw = np.abs(np.diff(band, axis=0)).sum(0)
                for gc in range(GW):
                    strat["geo"].append(geo_raw[gc]); strat["tex_raw"].append(tex_raw[gc])
                    strat["lab"].append(int(lab_e[gc]))

    out = {"oracle_pct": pct, "features": {}}
    for k in stat:
        out["features"][k] = {}
        for oname in ("depth_edge", "struct_209000"):
            sc, lb, fr = stat[k][oname]
            a, lo, hi, npos, nneg = _auc_ci(np.array(sc), np.array(lb), np.array(fr))
            out["features"][k][oname] = {"auc": a, "ci95": [lo, hi], "n_pos": npos, "n_neg": nneg}

    # G-both-channels: geometry separates depth-edges WITHIN texture strata
    geo = np.array(strat["geo"]); tex = np.array(strat["tex_raw"]); lab = np.array(strat["lab"])
    qs = np.percentile(tex, [0, 33, 66, 100])
    strata = []
    for i in range(3):
        m = (tex >= qs[i]) & (tex <= qs[i + 1])
        a, npos, nneg = _auc(geo[m], lab[m])
        strata.append({"texture_range": [round(float(qs[i]), 0), round(float(qs[i + 1]), 0)],
                       "geometry_auc": None if a is None else round(a, 3),
                       "n_pos": npos, "n_neg": nneg})
    out["both_channels_texture_strata"] = {
        "note": "geometry (horizontal edge) AUC vs depth-edge WITHIN each texture-quantile stratum; "
                ">0.5 => geometry adds signal BEYOND texture (matched texture)",
        "corr_geo_texture": round(float(np.corrcoef(geo, tex)[0, 1]), 3),
        "strata": strata}
    return out


def run(outdir=OUTDIR, pct=95):
    os.makedirs(outdir, exist_ok=True)
    frames_by_route = {r: _capture(seq) for r, seq in ROUTES.items()}
    res = measure(frames_by_route, pct)
    res["routes"] = {r: len(f) for r, f in frames_by_route.items()}
    res["headline"] = ("SEEN structural horizontal-edge geometry beats chance vs a depth-EDGE oracle; "
                       "geometry-from-motion (209000) was chance (0.508)")
    with open(os.path.join(outdir, "robust_geometry.json"), "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=2))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=OUTDIR)
    ap.add_argument("--pct", type=int, default=95); args = ap.parse_args()
    try:
        import vizdoom  # noqa
        R_WAD = "/home/matt/.local/share/Steam/steamapps/common/Ultimate Doom/base/DOOM.WAD"
        if not os.path.exists(R_WAD):
            raise RuntimeError("WAD absent")
    except Exception as e:
        print("SKIP: VizDoom/WAD unavailable:", e)
        raise SystemExit(0)
    run(args.out, args.pct)
