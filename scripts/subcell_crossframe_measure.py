#!/usr/bin/env python3
"""SUB-CELL CROSS-FRAME REGISTRATION vs the free-fall acceleration signal
(block 149000-149999).

CLAIM: precision belongs in the CROSS-FRAME OFFSET, not the in-frame grid.
147000 raised the in-frame resolution (where the aperture pays for it) and the
real clip still floored at a=0; 148000 decoupled the aperture but the small real
per-frame curvature stayed below the integer-CENTROID noise floor. This rung adds
precision to the ONE invariant-clean place: the per-frame DISPLACEMENT (velocity)
is `Hom(frame, frame)` — a cross-frame map where a continuous parameter is
admissible, its observable the STEPPED (finer-unit INTEGER) rendering. We REGISTER
the tracked ball's grey patch across consecutive frames at sub-cell precision and
emit the offset as a FINER-UNIT INTEGER stream (offset x S). That stream feeds the
EXISTING robust integer witness UNCHANGED (`&[Vec<i64>]`): no Rust change.

INVARIANT DISCIPLINE (audited): NO float is ever written into an in-frame
coordinate. The carve centroid enters only via `round(...)` (a coarse integer
anchor). The bilinear upsample interpolates grey VALUES inside the comparator.
The emitted offsets and the cumulative positions fed to the witness are INTEGERS
in finer units (1/S cell). See `domains/subcell_register.py`.

Parts:
  ORACLE  a textured ball rendered at KNOWN SUB-CELL parabola (anti-aliased) —
          the INTEGER centroid floors, but sub-cell registration -> finer-unit
          position -> the witness recovers the KNOWN accel_fine = a_cell * S.
          Proves the registration+witness CHAIN before blaming any real patch.
  REAL    the native 128x640 free-fall clip end-to-end: carve+track for the
          anchors, register the RAW grey patch at sub-cell -> finer-unit position
          -> witness. Compare the recovered accel to 148000's a=0.
  CTL     const-velocity -> order-1 not 2 (registration must not manufacture
          curvature); static -> nothing; random/noise -> floors.
  BI      byte-identity: the new path is a SEPARATE module, gated OFF by default;
          the existing carve/physics outputs are untouched (proven by diff scope).

S (the finer unit, 1/S cell) is a DECLARED resolution residual (§13), like
`block`/`k`; search_cells is the residual half-window in cells. NO tuned witness
tolerance is added — the witness's tolerance still falls out of integer bit-costs.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line, provenance_stamp
engine_preamble()
from domains import falling_world as fw                       # noqa: E402
from domains.motion_group_world import vector_field           # noqa: E402
from domains.subcell_register import register_residual_offset # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIP = os.path.join(ROOT, "naming_corpus", "gravity_freefall_ruler_E6jv9WTcgEQ.mp4")
DT = ["pred", "coord:r", "coord:c", "val"]
L = 4                          # the eye's shipped default quantization

# ── DECLARED RESOLUTION RESIDUALS (§13 — the finer unit + residual aperture) ──
S = 10                         # finer unit: 1/10 cell. The registration sub-cell step.
SEARCH_CELLS = 3               # residual half-window (+/- cells) absorbing anchor noise.


# ─────────────────────────── graph witness (read-back) ───────────────────────

def graph_mint(py_fine, *, status="motion_seq_robust"):
    """Ingest the finer-unit INTEGER position stream as a motion Observation; run
    the seeded run_rules fixpoint; read the minted latent:time LatentDimension
    (order, coeffs) back OUT. The order-N DECISION is the seed rule; this is pure
    ingest + read-back I/O. py_fine are already integers (finer units)."""
    s, ag, native = fw.boot_falling()
    frames = [[["obj", int(round(y)), 0, "obj"]] for y in py_fine]
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": status, "key": ["motion"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    st = s.node(o)["attrs"].get("status")
    mints = []
    for n in s.nodes("LatentDimension"):
        a = s.node(n)["attrs"]
        if a.get("name") == "latent:time":
            mints.append({"order": a.get("order"),
                          "coeffs": [list(c) for c in (a.get("coeffs") or ())],
                          "offset": list(a.get("offset") or ())})
    return st, mints


def accel_coeff(mints):
    """Order-2 acceleration coefficient (coeffs[1][0]) read from the graph mint,
    in FINER units; order-1/no mint -> None; order-2 with zero 2nd term -> 0."""
    for m in mints:
        if m["order"] == 2 and len(m["coeffs"]) >= 2:
            return m["coeffs"][1][0]
    return None


def d2i(seq):
    a = np.asarray([int(round(v)) for v in seq], dtype=np.int64)
    return np.diff(np.diff(a)).tolist()


# ─────────────── sub-cell offset stream from a tracked run ───────────────────

def subcell_position_stream(grey_raw, run):
    """`run` = list of {fi, cy, cx, count}. Register the RAW grey patch across
    consecutive tracked frames at sub-cell precision; accumulate the finer-unit
    INTEGER offsets into a finer-unit INTEGER position stream. Returns (py_fine,
    px_fine, per-pair diagnostics). The carve centroid enters only via round()."""
    py = [0]
    px = [0]
    diags = []
    for i in range(len(run) - 1):
        a, b = run[i], run[i + 1]
        anchor = (int(round(a["cy"])), int(round(a["cx"])))
        coarse = (int(round(b["cy"])) - int(round(a["cy"])),
                  int(round(b["cx"])) - int(round(a["cx"])))
        dy_f, dx_f, diag = register_residual_offset(
            grey_raw[a["fi"]], grey_raw[b["fi"]],
            anchor_prev=anchor, coarse=coarse, count=a["count"],
            S=S, search_cells=SEARCH_CELLS)
        py.append(py[-1] + dy_f)
        px.append(px[-1] + dx_f)
        diags.append(diag)
    return py, px, diags


# ─────────────────────────── decode + carve/track ────────────────────────────

def decode_grey(ss, dur, fps, gw, gh):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(dur), "-i", CLIP,
           "-vf", f"fps={fps},scale={gw}:{gh},format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (gw * gh)
    return np.frombuffer(raw[:n * gw * gh], dtype=np.uint8).reshape(n, gh, gw)


def quantize(luma_u8, levels=L):
    return (luma_u8.astype(np.int32) * levels) // 256


def carve_track_indexed(frames_q, gh, gw, block):
    """Common-fate carve every frame; track the falling object = LARGEST
    non-ground region by persistent id. Returns per-carved-frame (fi, obj|None)."""
    s, ag, native = fw.boot_falling()
    game, cell_ids = fw.setup_world(native, gh, gw)
    track = []
    prev = frames_q[0]
    for fi in range(1, frames_q.shape[0]):
        cur = frames_q[fi]
        vf = vector_field(prev, cur, block=block)
        vy = np.repeat(np.repeat(vf[:, :, 0], block, 0), block, 1)
        vx = np.repeat(np.repeat(vf[:, :, 1], block, 0), block, 1)
        full_y = np.zeros((gh, gw)); full_x = np.zeros((gh, gw))
        full_y[:vy.shape[0], :vy.shape[1]] = vy
        full_x[:vx.shape[0], :vx.shape[1]] = vx
        native.set_attr(game, "frame", float(fi))
        native.segment_motion(game, gh, gw, full_y.reshape(-1).tolist(),
                              full_x.reshape(-1).tolist(), cell_ids)
        regs = fw.read_regions(native, game)
        ng = [r for r in regs if r["is_ground"] == 0.0]
        obj = max(ng, key=lambda r: r["count"]) if ng else None
        track.append((fi, obj))
        prev = cur
    return track


def longest_run_indexed(track):
    best, cur = [], []
    for fi, b in track:
        if b is None:
            cur = []; continue
        rec = {"fi": fi, "cy": b["cy"], "cx": b["cx"], "count": b["count"], "id": b["id"]}
        if cur and rec["id"] == cur[-1]["id"]:
            cur.append(rec)
        else:
            cur = [rec]
        if len(cur) > len(best):
            best = list(cur)
    return best


# ───────────────────────────── ideal sub-cell oracle ─────────────────────────

def render_subcell_fall(*, a_cell, n_frames, cy0, gh, gw, obj, texseed, texlo, vel=0.0):
    """A textured square whose TOP-ROW follows cy(t)=cy0+vel*t+a_cell/2*t^2 at
    SUB-CELL precision, ANTI-ALIASED vertically (bilinear split between the two
    straddling integer rows). The sub-cell vertical position is thus encoded in
    the rendered grey — a stepped rendering of a continuous translation (the
    cross-frame map). Returns float grey frames (n,gh,gw) + the true sub-cell top."""
    rng = np.random.default_rng(texseed)
    tex = rng.integers(texlo, 256, size=(obj, obj)).astype(np.float64)
    cx0 = (gw - obj) // 2
    frames, true_top = [], []
    for t in range(n_frames):
        cy = cy0 + vel * t + 0.5 * a_cell * t * t
        top0 = int(np.floor(cy)); frac = cy - top0
        f = np.zeros((gh, gw), dtype=np.float64)
        for row, w in ((top0, 1.0 - frac), (top0 + 1, frac)):
            r0, r1 = max(0, row), min(gh, row + obj)
            if r1 > r0:
                f[r0:r1, cx0:cx0 + obj] += w * tex[:r1 - r0, :]
        frames.append(f)
        true_top.append(cy)
    return np.stack(frames), true_top


def part_oracle():
    """Known sub-cell parabola; anchors GIVEN (round of the true top) so this
    isolates the registration+witness CHAIN from the carve. accel_fine should
    recover a_cell*S; the INTEGER centroid (round(true top)) floors."""
    a_cell = 0.2
    gh, gw, obj, cy0, n = 200, 64, 24, 10.0, 8
    frames, true_top = render_subcell_fall(a_cell=a_cell, n_frames=n, cy0=cy0,
                                           gh=gh, gw=gw, obj=obj,
                                           texseed=149000, texlo=64)
    count = float(obj * obj)
    # GIVEN anchors from the true (rounded) top — the ideal case (no carve noise).
    run = [{"fi": t, "cy": float(round(true_top[t])), "cx": float(gw // 2),
            "count": count, "id": 1} for t in range(n)]
    py, px, diags = subcell_position_stream(frames, run)
    st_sc, m_sc = graph_mint(py)
    # INTEGER-centroid control: feed the rounded true top (integer cells) directly.
    int_cy = [int(round(v)) for v in true_top]
    st_int, m_int = graph_mint(int_cy)
    return {"a_cell": a_cell, "S": S, "target_accel_fine": a_cell * S,
            "true_top": [round(v, 3) for v in true_top],
            "subcell": {"py_fine": py, "d2_fine": d2i(py),
                        "status": st_sc, "accel_coeff": accel_coeff(m_sc),
                        "mints": m_sc},
            "integer_centroid": {"int_cy": int_cy, "d2": d2i(int_cy),
                                 "status": st_int, "accel_coeff": accel_coeff(m_int),
                                 "mints": m_int},
            "reg_diag": diags}


# ─────────────────────────────── controls ────────────────────────────────────

def part_controls():
    out = {}
    gh, gw, obj, cy0, n = 200, 64, 24, 10.0, 8
    # const-velocity (sub-cell): registration must NOT manufacture curvature.
    fr_cv, top_cv = render_subcell_fall(a_cell=0.0, n_frames=n, cy0=cy0, gh=gh,
                                        gw=gw, obj=obj, texseed=149001, texlo=64, vel=0.7)
    count = float(obj * obj)
    run_cv = [{"fi": t, "cy": float(round(top_cv[t])), "cx": float(gw // 2),
               "count": count, "id": 1} for t in range(n)]
    py_cv, _, _ = subcell_position_stream(fr_cv, run_cv)
    st_cv, m_cv = graph_mint(py_cv)
    out["const_velocity_subcell"] = {
        "vel": 0.7, "py_fine": py_cv, "d2_fine": d2i(py_cv),
        "status": st_cv, "accel_coeff": accel_coeff(m_cv), "mints": m_cv,
        "no_manufactured_curvature": accel_coeff(m_cv) in (None, 0)}
    # static: nothing moves -> registration ~0 -> no order-2.
    fr_st, top_st = render_subcell_fall(a_cell=0.0, n_frames=n, cy0=cy0, gh=gh,
                                        gw=gw, obj=obj, texseed=149002, texlo=64, vel=0.0)
    run_st = [{"fi": t, "cy": float(round(top_st[t])), "cx": float(gw // 2),
               "count": count, "id": 1} for t in range(n)]
    py_st, _, _ = subcell_position_stream(fr_st, run_st)
    st_st, m_st = graph_mint(py_st)
    out["static_subcell"] = {"py_fine": py_st, "status": st_st,
                             "accel_coeff": accel_coeff(m_st),
                             "mints_nothing": accel_coeff(m_st) in (None, 0)}
    # noise: incoherent frames -> registration of noise must not confabulate order-2.
    rng = np.random.default_rng(149003)
    fr_nz = rng.integers(0, 256, size=(n, gh, gw)).astype(np.float64)
    run_nz = [{"fi": t, "cy": float(gh // 2), "cx": float(gw // 2),
               "count": count, "id": 1} for t in range(n)]
    py_nz, _, _ = subcell_position_stream(fr_nz, run_nz)
    st_nz, m_nz = graph_mint(py_nz)
    out["noise_subcell"] = {"py_fine": py_nz, "d2_fine": d2i(py_nz),
                            "status": st_nz, "accel_coeff": accel_coeff(m_nz),
                            "floors": accel_coeff(m_nz) in (None, 0)}
    return out


# ─────────────────────────────── real clip ───────────────────────────────────

def part_real():
    configs = [
        [55.0, 20.0, 2.0, 128, 640, 6, "real_128x640_b6_2fps"],
        [50.0, 25.0, 2.0, 128, 640, 6, "real_128x640_b6_2fps_early"],
        [55.0, 20.0, 1.5, 128, 640, 6, "real_128x640_b6_1p5fps"],
    ]
    rows = []
    for ss, dur, fps, gw, gh, block, label in configs:
        grey = decode_grey(ss, dur, fps, gw, gh)
        fq = quantize(grey)
        track = carve_track_indexed(fq, gh, gw, block)
        run = longest_run_indexed(track)
        row = {"label": label, "grid": [gw, gh], "block": block, "fps": fps,
               "n_frames": int(fq.shape[0]), "run_len": len(run)}
        if len(run) >= 4:
            cyf = [r["cy"] for r in run]
            row["carve_cy_float"] = [round(v, 2) for v in cyf]
            row["carve_cy_int"] = [int(round(v)) for v in cyf]
            row["carve_d2_int"] = d2i(cyf)
            # INTEGER-centroid baseline (148000's readout): witness on int centroid.
            st_i, m_i = graph_mint([int(round(v)) for v in cyf])
            row["integer_centroid"] = {"status": st_i, "accel_coeff": accel_coeff(m_i)}
            # SUB-CELL cross-frame registration on the RAW grey.
            py, px, diags = subcell_position_stream(grey, run)
            st_s, m_s = graph_mint(py)
            row["subcell"] = {"py_fine": py, "d2_fine": d2i(py),
                              "status": st_s, "accel_coeff": accel_coeff(m_s),
                              "mints": m_s,
                              "accel_cell_equiv": (accel_coeff(m_s) / S) if accel_coeff(m_s) is not None else None}
            row["reg_diag"] = diags
        else:
            row["note"] = "run < 4 — no witness"
        rows.append(row)
    return rows


def main():
    load0 = os.getloadavg()
    result = {"block": "149000-149999",
              "engine_provenance": provenance_stamp(),
              "provenance_line": provenance_line(),
              "S": S, "search_cells": SEARCH_CELLS,
              "oracle": part_oracle(),
              "controls": part_controls(),
              "loadavg_start": list(load0)}
    orc = result["oracle"]
    print("=== IDEAL SUB-CELL ORACLE (a_cell=%.3f, S=%d -> target accel_fine=%.2f) ==="
          % (orc["a_cell"], orc["S"], orc["target_accel_fine"]))
    print("  true top:", orc["true_top"])
    print("  INTEGER centroid: d2=%s status=%s accel=%s (should FLOOR)"
          % (orc["integer_centroid"]["d2"], orc["integer_centroid"]["status"],
             orc["integer_centroid"]["accel_coeff"]))
    print("  SUB-CELL         : d2_fine=%s status=%s accel_fine=%s (target %.2f)"
          % (orc["subcell"]["d2_fine"], orc["subcell"]["status"],
             orc["subcell"]["accel_coeff"], orc["target_accel_fine"]))
    ctl = result["controls"]
    print("=== CONTROLS (sub-cell) ===")
    print("  const-velocity no manufactured curvature:",
          ctl["const_velocity_subcell"]["no_manufactured_curvature"],
          "accel_fine=", ctl["const_velocity_subcell"]["accel_coeff"],
          "d2_fine=", ctl["const_velocity_subcell"]["d2_fine"])
    print("  static mints nothing:", ctl["static_subcell"]["mints_nothing"])
    print("  noise floors:", ctl["noise_subcell"]["floors"],
          "accel_fine=", ctl["noise_subcell"]["accel_coeff"])

    if os.environ.get("SUBCELL_REAL", "1") == "1":
        result["real"] = part_real()
        print("=== REAL CLIP (128x640) ===")
        for r in result["real"]:
            if "subcell" in r:
                print("  [%s] run=%d carve_d2_int=%s" % (r["label"], r["run_len"], r["carve_d2_int"]))
                print("      INTEGER centroid: accel=%s status=%s"
                      % (r["integer_centroid"]["accel_coeff"], r["integer_centroid"]["status"]))
                print("      SUB-CELL: accel_fine=%s (=%s cell/f^2) status=%s d2_fine=%s"
                      % (r["subcell"]["accel_coeff"], r["subcell"]["accel_cell_equiv"],
                         r["subcell"]["status"], r["subcell"]["d2_fine"]))
            else:
                print("  [%s] %s" % (r["label"], r.get("note")))

    result["loadavg_end"] = list(os.getloadavg())
    outp = os.path.join(ROOT, "results", "subcell_crossframe_measure.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", outp)


if __name__ == "__main__":
    main()
