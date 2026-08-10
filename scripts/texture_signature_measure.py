"""texture_signature_measure — block 214000. MEASURE whether a richer INTEGER texture
descriptor (colour-as-a-sign + pattern-as-arrangement) recovers the texture-FAINT doors
(sec83/sec85) that the 209000 edge-density SCALAR missed, WITHOUT false-positive on plain walls.

The eye reads ONLY rendered RGB pixels (integer luma + integer colour channels). The VizDoom
depth buffer is a SCORING ORACLE ONLY (labels door vs wall columns / filters mid-distance
frames); it never enters any descriptor. Run FOREGROUND:

    PYTHONPATH=. python3 scripts/texture_signature_measure.py
"""
from __future__ import annotations
import json, math, os

import numpy as np

import domains.doom_pattern_eye as eye

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "results", "pattern_eye")
WAD = "/home/matt/.local/share/Steam/steamapps/common/Ultimate Doom/base/DOOM.WAD"
GH, GW = 240, 320
CBAND = (GH // 4, 3 * GH // 4)                 # central row band (same as the eye)
CCOLS = slice(3 * GW // 8, 5 * GW // 8)        # central column quarter (the faced feature)

# 210000's door table — strong (sec26/69) + faint (sec83/85). approach = start offset on an
# OPENABLE face; the faint sectors are the 210000 residual (n_use=0, 0 opens).
DOORS = [
    {"sector": 26, "center": (1544, -2496), "approach": (-130, 0), "class": "strong"},
    {"sector": 69, "center": (3008, -4640), "approach": (0, -130), "class": "strong"},
    {"sector": 85, "center": (3008, -4024), "approach": (0, -130), "class": "faint"},
    {"sector": 83, "center": (2928, -3840), "approach": (-130, 0), "class": "faint"},
]


# ---------------------------------------------------------- candidate descriptors (integer, RGB only)
def _luma(rgb):
    a = np.asarray(rgb).astype(np.int32)
    return (77 * a[..., 0] + 150 * a[..., 1] + 29 * a[..., 2]) >> 8


def old_tex_energy(rgb):
    """The 209000 SCALAR, PRE-quantisation: per-column vertical luma-gradient energy (integer)."""
    lum = _luma(rgb)
    band = lum[CBAND[0]:CBAND[1]]
    return np.abs(np.diff(band, axis=0)).sum(0).astype(np.int64)


def old_tex_level(rgb, div=100, k=8):
    """The 209000 SCALAR: per-column vertical luma-gradient energy // div, 0..k."""
    return np.minimum(k, old_tex_energy(rgb) // div).astype(np.int64)


def colour_contrast(rgb):
    """PRE-quantisation COLOUR-as-a-sign: per-column integer chroma-L1 contrast from the frame's
    ambient wall chroma (RGB only). Returns integer array (contrast*4 to keep sub-unit signal)."""
    a = np.asarray(rgb).astype(np.int64)[CBAND[0]:CBAND[1]]
    mr = a[..., 0].mean(0); mg = a[..., 1].mean(0); mb = a[..., 2].mean(0)
    m = (77 * mr + 150 * mg + 29 * mb) / 256.0
    cr, cg, cb = mr - m, mg - m, mb - m
    ar, ag, ab = np.median(cr), np.median(cg), np.median(cb)
    l1 = np.abs(cr - ar) + np.abs(cg - ag) + np.abs(cb - ab)
    return np.rint(l1 * 4).astype(np.int64)


def colour_level(rgb, div=8, k=8):
    """COLOUR-as-a-sign: per-column INTEGER chroma contrast from the frame's ambient wall.
    Per column mean (R,G,B) over the band -> integer luma m -> chroma (R-m,G-m,B-m). Ambient
    = per-channel MEDIAN chroma across columns. level = L1(chroma - ambient)//div, 0..k. A door
    whose material/hue differs from its wall reads high EVEN at matched luma-gradient; a plain
    wall IS the ambient -> ~0. RGB channels only, NO depth/labels/texture-name."""
    a = np.asarray(rgb).astype(np.int32)[CBAND[0]:CBAND[1]]
    mr = a[..., 0].mean(0); mg = a[..., 1].mean(0); mb = a[..., 2].mean(0)   # per-column mean colour
    m = (77 * mr + 150 * mg + 29 * mb) / 256.0                              # per-column luma
    cr, cg, cb = mr - m, mg - m, mb - m                                     # per-column chroma vector
    ar, ag, ab = np.median(cr), np.median(cg), np.median(cb)                # ambient wall chroma
    l1 = np.abs(cr - ar) + np.abs(cg - ag) + np.abs(cb - ab)                # chroma contrast (float mean, quantised)
    return np.minimum(k, (l1.astype(np.int64)) // div).astype(np.int64)


def pattern_signature(rgb):
    """PATTERN-as-arrangement: per-column INTEGER 4-bin orientation histogram of the luma
    gradient over the band. Bins: 0=horizontal-edge(|gx|>|gy|), 1=vertical-edge(|gy|>=|gx|),
    2=diag+ (gx*gy>0), 3=diag- (gx*gy<0). Each bin = summed |gradient| magnitude. Captures
    ARRANGEMENT, not just total energy. Returns hist[4, GW] integer."""
    lum = _luma(rgb).astype(np.int64)[CBAND[0]:CBAND[1]]
    gy = np.zeros_like(lum); gx = np.zeros_like(lum)
    gy[1:, :] = np.diff(lum, axis=0)          # vertical gradient
    gx[:, 1:] = np.diff(lum, axis=1)          # horizontal gradient
    mag = np.abs(gx) + np.abs(gy)
    horiz = (np.abs(gx) > np.abs(gy))
    diagp = (gx * gy > 0)
    hist = np.zeros((4, lum.shape[1]), np.int64)
    hist[0] = (mag * (horiz)).sum(0)
    hist[1] = (mag * (~horiz)).sum(0)
    hist[2] = (mag * (diagp & horiz)).sum(0)
    hist[3] = (mag * ((~diagp) & horiz)).sum(0)
    return hist


def _central(vec):
    """Central-column median score (integer)."""
    return int(np.median(np.asarray(vec)[CCOLS]))


# ------------------------------------------------------------------------------ VizDoom capture
def _game():
    import vizdoom as vzd
    g = vzd.DoomGame()
    g.set_doom_game_path(WAD); g.set_doom_scenario_path(WAD); g.set_doom_map("E1M1")
    g.set_screen_resolution(vzd.ScreenResolution.RES_320X240); g.set_screen_format(vzd.ScreenFormat.RGB24)
    g.set_depth_buffer_enabled(True); g.set_sectors_info_enabled(True); g.add_game_args("-nomonsters")
    g.set_render_hud(False); g.set_render_weapon(False)
    g.set_window_visible(False); g.set_mode(vzd.Mode.PLAYER); g.set_doom_skill(3)
    for b in (vzd.Button.MOVE_FORWARD, vzd.Button.TURN_LEFT, vzd.Button.TURN_RIGHT, vzd.Button.USE):
        g.add_available_button(b)
    gv = vzd.GameVariable
    for v in (gv.POSITION_X, gv.POSITION_Y, gv.ANGLE):
        g.add_available_game_variable(v)
    g.set_seed(1234); g.init(); g.new_episode()
    return g, gv


def _pose(g, gv):
    return (g.get_game_variable(gv.POSITION_X), g.get_game_variable(gv.POSITION_Y),
            g.get_game_variable(gv.ANGLE))


def _grab(g):
    st = g.get_state()
    a = np.array(st.screen_buffer)
    rgb = np.transpose(a, (1, 2, 0)) if a.shape[0] == 3 else a
    return rgb.copy(), np.array(st.depth_buffer, copy=True).astype(float)


def _central_depth(db):
    """SCORING ORACLE ONLY: median depth of the central patch (how near the faced surface is)."""
    return float(np.median(db[CBAND[0]:CBAND[1], GW * 3 // 8:GW * 5 // 8]))


def _door_frames(door, dists=(220, 190, 160, 130, 100)):
    """Warp the agent to a set of FIXED distances along the door's openable face-normal, orient
    at the door, and grab ONE frame each (matched distances across all doors; no fragile
    navigation). The door is a central blob with wall around it. Tag each frame with the
    (geometric) pose-distance to the door centre; capture 2 frames per distance for stability."""
    dx, dy = door["center"]; ux, uy = door["approach"]; n = math.hypot(ux, uy)
    rows = []
    for d in dists:
        g, gv = _game()
        ax, ay = dx + ux / n * d, dy + uy / n * d
        g.send_game_command("warp %d %d" % (ax, ay)); g.make_action([0, 0, 0, 0], 1)
        px, py, _ = _pose(g, gv)
        if math.hypot(px - ax, py - ay) > 70:         # warp landed in a wall -> skip this distance
            g.close(); continue
        want = math.degrees(math.atan2(dy - py, dx - px)) % 360
        for _ in range(50):
            _, _, ang = _pose(g, gv)
            err = (want - ang + 180) % 360 - 180
            if abs(err) < 5:
                break
            g.make_action([0, 1, 0, 0] if err > 0 else [0, 0, 1, 0], 2)
        for _ in range(2):
            if g.is_episode_finished():
                break
            rgb, db = _grab(g)
            px, py, _ = _pose(g, gv)
            rows.append(_score_frame(rgb, db, door["sector"], door["class"], d,
                                     dist=math.hypot(px - dx, py - dy)))
            g.make_action([0, 0, 0, 0], 1)
        g.close()
    return rows


def _wall_frames():
    """Plain-wall control (209000 scenes): orient to open floor and walk toward a plain wall."""
    import vizdoom as vzd
    rows = []
    PLAINS = [(15, "R", 8), (15, "L", 7), (20, "R", 9), (24, "L", 8), (30, "R", 7), (40, "R", 7)]
    for turns, d, fwd in PLAINS:
        g, gv = _game()
        TL, TR = [0, 1, 0, 0], [0, 0, 1, 0]
        for _ in range(turns):
            g.make_action(TL if d == "L" else TR, 3)
        for k in range(fwd):
            if g.is_episode_finished():
                break
            rgb, db = _grab(g)
            rows.append(_score_frame(rgb, db, -1, "wall", k, dist=999))
            g.make_action([1, 0, 0, 0], 3)
        g.close()
    return rows


def _score_frame(rgb, db, sector, klass, k, dist=999):
    ph = pattern_signature(rgb)              # [horiz, vert, diag+, diag-] energy per column
    total = ph.sum(0)
    with np.errstate(divide="ignore", invalid="ignore"):
        hfrac = np.where(total > 0, (ph[0] * 8) // np.maximum(total, 1), 0)          # coarse 0..8
        hshare = np.where(total > 0, (ph[0] * 1000) // np.maximum(total, 1), 0)      # fine 0..1000
    return {
        "sector": sector, "class": klass, "k": k,
        "dist": round(float(dist), 1), "central_depth": round(_central_depth(db), 1),
        "tex_energy": _central(old_tex_energy(rgb)),      # RAW 209000 feature (pre-quantisation)
        "colour_contrast": _central(colour_contrast(rgb)),  # RAW colour feature (chroma*4, pre-quant)
        "hshare": _central(hshare),                        # RAW arrangement: horizontal-edge share ‰
        "old_tex": _central(old_tex_level(rgb)),          # quantised 0..8 (the shipped scalar)
        "colour": _central(colour_level(rgb)),            # quantised 0..8
        "hfrac": _central(hfrac),
        # the EYE's actual richer descriptor (from doom_pattern_eye) -> fed to the graph
        "eye_tex": int(np.median(eye.col_texture_level(rgb)[0][CCOLS])),
        "eye_colour": int(np.median(eye.col_colour_level(rgb)[0][CCOLS])),
        "eye_pattern": int(np.median(eye.col_pattern_level(rgb)[0][CCOLS])),
    }


# ------------------------------------------------------------------------------ AUC + bootstrap
def _auc(score, lab):
    score = np.asarray(score, float); lab = np.asarray(lab)
    pos, neg = score[lab == 1], score[lab == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None
    allv = np.concatenate([pos, neg]); order = allv.argsort(); ranks = np.empty(len(allv), float)
    sv = allv[order]; i = 0
    while i < len(sv):
        j = i
        while j + 1 < len(sv) and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0; i = j + 1
    return (ranks[:len(pos)].sum() - len(pos) * (len(pos) - 1) / 2) / (len(pos) * len(neg))


def _auc_ci(score, lab, n=2000, seed=214):
    score = np.asarray(score, float); lab = np.asarray(lab); rng = np.random.default_rng(seed)
    base = _auc(score, lab)
    if base is None:
        return None, None, None
    boots = []
    idx = np.arange(len(lab))
    for _ in range(n):
        s = rng.choice(idx, len(idx), replace=True)
        a = _auc(score[s], lab[s])
        if a is not None:
            boots.append(a)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return round(base, 3), round(lo, 3), round(hi, 3)


def run(outdir=OUTDIR):
    os.makedirs(outdir, exist_ok=True)
    door_rows, wall_rows = [], []
    for d in DOORS:
        door_rows += _door_frames(d)
    wall_rows += _wall_frames()

    # MID distance = the door is a central blob with wall around it (pose-distance 70..190 units;
    # the 210000 texture-readable band). Depth is NOT used to filter (pose-distance is geometric).
    LO, HI = 70, 240

    def mid(rows, sector):
        return [x for x in rows if x["sector"] == sector and LO <= x["dist"] <= HI]
    per_door = {}
    for d in DOORS:
        r = mid(door_rows, d["sector"])
        if r:
            per_door[str(d["sector"])] = {
                "class": d["class"], "n_mid_frames": len(r),
                "median_tex_energy": int(np.median([x["tex_energy"] for x in r])),
                "median_colour_contrast_x4": int(np.median([x["colour_contrast"] for x in r])),
                "median_old_tex": int(np.median([x["old_tex"] for x in r])),
                "median_colour": int(np.median([x["colour"] for x in r])),
                "median_hfrac": int(np.median([x["hfrac"] for x in r])),
            }

    # AUC: door-central (mid-distance) vs wall-central, per RAW channel
    def channel_auc(chan, klasses):
        ds = [x[chan] for x in door_rows if x["class"] in klasses and LO <= x["dist"] <= HI]
        ws = [x[chan] for x in wall_rows]
        s = np.array(ds + ws, float); lab = np.array([1] * len(ds) + [0] * len(ws))
        return _auc_ci(s, lab), len(ds), len(ws)

    aucs = {}
    for name, klasses in [("all_doors", ("strong", "faint")), ("faint_only", ("faint",)),
                          ("strong_only", ("strong",))]:
        aucs[name] = {}
        for chan in ("tex_energy", "colour_contrast", "hshare"):
            (base, lo, hi), npos, nneg = channel_auc(chan, klasses)
            aucs[name][chan] = {"auc": base, "ci": [lo, hi], "n_door": npos, "n_wall": nneg}

    # ---- END-TO-END GRAPH GATE: feed the eye's richer descriptor through the held seed rules,
    #      compare against the OLD 209000 scalar recognition, on the SAME real frames.
    def graph_recognise(rows):
        """Run each region's eye-descriptor through the richer-texture seed; return recognised list."""
        wa = eye.fresh_texture_adapter(); S, I = wa.s, wa.inner
        game = S.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom"})
        eye.install_texture(wa, game, salience_floor=2)
        rids = [eye.ingest_texture_region(wa, game, x["eye_tex"], x["eye_colour"], x["eye_pattern"],
                                          meta={"i": i}) for i, x in enumerate(rows)]
        out = eye.recognise_texture(wa, rids)
        return [out[r]["recognised_as"] == "door" for r in rids]

    def old_scalar_recognise(rows):
        """The 209000 scalar recognition on the SAME frames: |tex_level-6| < match_thresh(3)."""
        return [abs(x["old_tex"] - 6) < 3 for x in rows]

    door_mid = [x for x in door_rows if LO <= x["dist"] <= HI]
    faint_mid = [x for x in door_mid if x["class"] == "faint"]
    strong_mid = [x for x in door_mid if x["class"] == "strong"]

    def rate(recog_fn, rows):
        r = recog_fn(rows)
        return round(float(np.mean(r)), 3) if rows else None

    def via_counts(rows):
        wa = eye.fresh_texture_adapter(); S, I = wa.s, wa.inner
        game = S.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom"})
        eye.install_texture(wa, game, salience_floor=2)
        rids = [eye.ingest_texture_region(wa, game, x["eye_tex"], x["eye_colour"], x["eye_pattern"]) for x in rows]
        out = eye.recognise_texture(wa, rids)
        c = {}
        for r in rids:
            v = out[r]["recog_via"]
            if v:
                c[v] = c.get(v, 0) + 1
        return c

    graph_gate = {
        "richer_graph": {
            "faint_recognition": rate(graph_recognise, faint_mid),
            "strong_recognition": rate(graph_recognise, strong_mid),
            "wall_false_positive": rate(graph_recognise, wall_rows),
            "faint_via": via_counts(faint_mid),
        },
        "old_scalar_209000": {
            "faint_recognition": rate(old_scalar_recognise, faint_mid),
            "strong_recognition": rate(old_scalar_recognise, strong_mid),
            "wall_false_positive": rate(old_scalar_recognise, wall_rows),
        },
        "n_faint": len(faint_mid), "n_strong": len(strong_mid), "n_wall": len(wall_rows),
        "operating_point": "door pattern_sig=7 arr_thresh=1, colour_min=4, salience_floor=2",
    }

    summary = {
        "block": 214000,
        "per_door_mid_distance": per_door,
        "auc_door_vs_wall_raw": aucs,
        "graph_gate": graph_gate,
        "n_door_frames": len(door_rows), "n_wall_frames": len(wall_rows),
        "note": ("colour_contrast = per-column integer chroma-L1 contrast (x4) from ambient wall "
                 "(RGB only); tex_energy = 209000 RAW vertical-gradient energy; hfrac = horizontal "
                 "share of pattern energy. Pose-distance (geometric) filters mid frames; depth is "
                 "NEVER in a descriptor. AUC on RAW features so quantisation can't hide signal."),
    }
    with open(os.path.join(outdir, "texture_signature.json"), "w") as f:
        json.dump({"summary": summary, "door_rows": door_rows, "wall_rows": wall_rows}, f, indent=2)
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    try:
        import vizdoom  # noqa
        if not os.path.exists(WAD):
            raise RuntimeError("WAD absent")
    except Exception as e:
        print("SKIP: VizDoom/WAD unavailable:", e); raise SystemExit(0)
    run()
