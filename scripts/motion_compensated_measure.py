#!/usr/bin/env python3
"""MOTION-COMPENSATED (PREDICTIVE-CENTER) BLOCK SEARCH vs the free-fall
acceleration signal (block 148000-148999).

CLAIM: motion-compensated block search recovers a free-fall's acceleration
where the FIXED-aperture sensor floors, by DECOUPLING the aperture from the
velocity. For each block the sensor PREDICTS its coarse displacement from the
PREVIOUS frame-pair's motion field (RAW ARRAY DATA — the codec P-frame move,
temporal smoothness of the optical flow), then searches the same small ±block
residual window CENTERED on the prediction. Total displacement = predicted +
residual, so a small aperture senses a fast fall as long as the ACCELERATION
(the residual) fits the aperture — exactly the physics: velocity is predicted
(order-1); only the small constant acceleration must fit ±block.

MEASUREMENT + SENSOR ONLY. NO agent decision in Python: the predictor reads only
the previous motion FIELD (an (nh,nw,2) numpy array). Every order-N DECISION is
the seed rule (`time_infer_mint_robust`); this script renders / carves / ingests
and reads the minted LatentDimension coeffs back OUT of the graph. The residual
window stays `block` (§13: the same declared aperture, now around a prediction —
no new constant); the predicted-vs-plain choice FALLS OUT as an argmin.

Parts:
  H1  SYNTHETIC ISOLATION — a fast textured free-fall whose per-frame
      displacement OVERRUNS the fixed aperture. carve+track+robust-witness with
      MC OFF (fixed aperture) floors / recovers a=0; with MC ON the SAME fall is
      held as one trajectory and mints order-2 with NONZERO ∝-correct accel.
  BI  BYTE-IDENTITY — predict=None and predict=0 reproduce the plain sensor
      exactly (0 mismatched vectors over several frame pairs); first frame pair
      (no prior field) falls back to the plain search.
  CTL controls: const-velocity (MC on) -> order-1 not 2; static -> nothing;
      random/noise (MC on) -> floors (no confabulated order-2).
  H2  REAL CLIP — the native 128x640 free-fall clip end-to-end with MC ON;
      compare the recovered acceleration coeffs to 147000's a=0.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line, provenance_stamp
engine_preamble()
from domains import falling_world as fw                       # noqa: E402
from domains.motion_group_world import vector_field           # noqa: E402

CLIP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "naming_corpus", "gravity_freefall_ruler_E6jv9WTcgEQ.mp4")
DT = ["pred", "coord:r", "coord:c", "val"]
L = 4                         # the eye's shipped default quantization

# ── SYNTHETIC APPARATUS (the cross-frame rendering map; FIXED in advance, NOT a
#    witness threshold). A textured square in free fall from near-rest. ──
H1_H, H1_W = 150, 96          # grid; fits the whole fall + object
H1_BLOCK = 4                  # aperture = block (the declared §13 residual)
H1_OBJ = 80                   # object extent (>> per-frame displacement over the
                              #   clean window, so a co-located block overlaps its
                              #   own prev-frame position -> temporal prediction is
                              #   valid; co-located prediction degrades once the
                              #   displacement approaches the object extent, which
                              #   is also where the downstream carve's own velocity
                              #   estimate degrades — the centroid noise NOT fixed
                              #   here).
H1_CY0 = 8                    # start row (near top, from ~rest)
H1_A = 2                      # cy = cy0 + A/2 * t^2 ; 2nd difference of cy = A.
                              #   A = the per-frame acceleration (= residual the
                              #   MC aperture absorbs) = 2 <= aperture 4. The
                              #   per-frame displacement A*t+A/2 (1,3,5,7,9,11,13)
                              #   overruns the aperture (4) by frame 2, so the
                              #   FIXED aperture floors end-to-end.
H1_NFRAMES = 8
H1_TEXSEED = 148000           # burned confirmatory seed (texture RNG)
H1_TEXLO = 64                 # texture range [64,256) -> quantizes to {1,2,3}
                              #   (distinct nonzero levels that SURVIVE L=4, so
                              #   the block-SAD is unambiguous inside the object)


# ─────────────────────────── synthetic renderer ──────────────────────────────

def render_fall(*, accel, n_frames, cy0=H1_CY0, gh=H1_H, gw=H1_W, obj=H1_OBJ,
                texseed=H1_TEXSEED, texlo=H1_TEXLO):
    """Render a textured square in free fall. Returns uint8 frames (n,gh,gw).
    cy(t) = cy0 + accel/2 * t^2 (from ~rest). Texture (not a uniform disc) so
    block-SAD is unambiguous inside the object; static 0 background."""
    rng = np.random.default_rng(texseed)
    tex = rng.integers(texlo, 256, size=(obj, obj)).astype(np.uint8)
    cx0 = (gw - obj) // 2
    frames = []
    cys = []
    for t in range(n_frames):
        cy = cy0 + 0.5 * accel * t * t
        top = int(round(cy))
        f = np.zeros((gh, gw), dtype=np.uint8)
        r0, r1 = max(0, top), min(gh, top + obj)
        if r1 > r0:
            f[r0:r1, cx0:cx0 + obj] = tex[:r1 - r0, :]
        frames.append(f)
        cys.append(top + obj / 2.0)           # true object centre row
    return np.stack(frames), cys


def render_const_velocity(*, vel, n_frames, cy0=H1_CY0, gh=H1_H, gw=H1_W,
                          obj=H1_OBJ, texseed=H1_TEXSEED, texlo=H1_TEXLO):
    """Same textured square translating at CONSTANT velocity (no acceleration)."""
    rng = np.random.default_rng(texseed)
    tex = rng.integers(texlo, 256, size=(obj, obj)).astype(np.uint8)
    cx0 = (gw - obj) // 2
    frames = []
    for t in range(n_frames):
        top = int(round(cy0 + vel * t))
        f = np.zeros((gh, gw), dtype=np.uint8)
        r0, r1 = max(0, top), min(gh, top + obj)
        if r1 > r0:
            f[r0:r1, cx0:cx0 + obj] = tex[:r1 - r0, :]
        frames.append(f)
    return np.stack(frames)


def render_static(*, n_frames, gh=H1_H, gw=H1_W, obj=H1_OBJ, texseed=H1_TEXSEED, texlo=H1_TEXLO):
    rng = np.random.default_rng(texseed)
    tex = rng.integers(texlo, 256, size=(obj, obj)).astype(np.uint8)
    cx0 = (gw - obj) // 2
    f = np.zeros((gh, gw), dtype=np.uint8)
    f[H1_CY0:H1_CY0 + obj, cx0:cx0 + obj] = tex
    return np.stack([f.copy() for _ in range(n_frames)])


def render_noise(*, n_frames, gh=H1_H, gw=H1_W, seed):
    """Full-frame incoherent noise — the predictor must not hallucinate a
    coherent order-2 fall from it."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, size=(n_frames, gh, gw)).astype(np.uint8)


def quantize(luma_u8, levels=L):
    return (luma_u8.astype(np.int32) * levels) // 256


# ─────────────────────── carve + track (MC optional) ─────────────────────────

def carve_track(frames_q, gh, gw, block, *, mc):
    """Common-fate carve every frame; track the falling object = LARGEST
    non-ground region by persistent id. When `mc`, feed the PREVIOUS frame-pair's
    vector field as the per-block prediction (motion-compensated search). The
    first pair has no prior field -> predict=None -> plain search."""
    s, ag, native = fw.boot_falling()
    game, cell_ids = fw.setup_world(native, gh, gw)
    track, disp, wall = [], [], []
    prev = frames_q[0]
    prev_vf = None
    for fi in range(1, frames_q.shape[0]):
        cur = frames_q[fi]
        t0 = time.perf_counter()
        pred = None
        if mc and prev_vf is not None:
            pred = np.rint(prev_vf).astype(np.int64)      # RAW ARRAY DATA ONLY
        vf = vector_field(prev, cur, block=block, predict=pred)
        wall.append(time.perf_counter() - t0)
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
        track.append(obj)
        prev = cur
        prev_vf = vf
    return s, ag, native, track, wall


def graph_mint(cy, *, status="motion_seq_robust"):
    """Ingest cy as a motion Observation; run the seeded run_rules fixpoint; read
    the minted latent:time LatentDimension (order, coeffs) back OUT. The order-N
    DECISION is the seed rule; this is pure ingest + read-back I/O."""
    s, ag, native = fw.boot_falling()
    frames = [[["obj", int(round(y)), 0, "obj"]] for y in cy]
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
    """The order-2 acceleration coefficient read from the graph mint, or None.
    coeffs[1][0] is the constant 2nd-difference (the acceleration); order-1 or
    no mint -> None; an order-2 mint with a zero 2nd-order term -> 0."""
    for m in mints:
        if m["order"] == 2 and len(m["coeffs"]) >= 2:
            return m["coeffs"][1][0]
    return None


def d2_of(cy):
    a = np.asarray([int(round(v)) for v in cy], dtype=np.int64)
    d1 = np.diff(a); d2 = np.diff(d1)
    return d2.tolist()


def run_side(frames_q, gh, gw, block, *, mc):
    s, ag, native, track, wall = carve_track(frames_q, gh, gw, block, mc=mc)
    run = fw.longest_continuous_run(track)
    out = {"n_frames": int(frames_q.shape[0]), "longest_run_len": len(run),
           "n_with_obj": sum(1 for b in track if b is not None),
           "mean_ms_per_frame": float(np.mean(wall) * 1000) if wall else 0.0}
    if len(run) >= 4:
        cy = [b["cy"] for b in run]
        cyi = [int(round(v)) for v in cy]
        ids = {b["id"] for b in run}
        d1 = [abs(b - a) for a, b in zip(cyi, cyi[1:])]
        out.update({"run_one_id": (len(ids) == 1), "cy_int": cyi,
                    "d2": d2_of(cyi), "max_disp_cells": max(d1) if d1 else 0,
                    "disp_over_aperture": round((max(d1) if d1 else 0) / block, 2)})
        st, mints = graph_mint(cyi)
        out["robust_status"] = st
        out["mints"] = mints
        out["accel_coeff"] = accel_coeff(mints)
    else:
        out["note"] = "longest continuous run < 4 frames — no order-2 witness"
        out["accel_coeff"] = None
    return out


# ─────────────────────────────── H1 synthetic ────────────────────────────────

def field_fidelity(fq, gh, gw, block, true_cy, *, mc):
    """The layer the SENSOR fixes: per frame-pair, the MEDIAN block velocity over
    the moving cells vs the TRUE per-frame displacement. MC decouples the aperture
    from the velocity, so its median tracks the true (fast) displacement where the
    fixed aperture saturates near ±block. Pure sensor read — no carve, no graph."""
    prev = fq[0]
    prev_vf = None
    rows = []
    for fi in range(1, fq.shape[0]):
        cur = fq[fi]
        pred = None
        if mc and prev_vf is not None:
            pred = np.rint(prev_vf).astype(np.int64)
        vf = vector_field(prev, cur, block=block, predict=pred)
        vy = vf[:, :, 0]
        moving = vy[np.abs(vy) > 0.5]
        med = float(np.median(moving)) if moving.size else 0.0
        rows.append({"frame": fi, "true_disp": round(true_cy[fi] - true_cy[fi - 1], 1),
                     "median_vy": med, "n_moving": int(moving.size)})
        prev = cur
        prev_vf = vf
    return rows


def part_h1():
    frames, true_cy = render_fall(accel=H1_A, n_frames=H1_NFRAMES)
    fq = quantize(frames)
    ideal_cyi = [int(round(v)) for v in true_cy]
    ideal_d2 = d2_of(true_cy)
    st_ideal, m_ideal = graph_mint(ideal_cyi)
    fid_off = field_fidelity(fq, H1_H, H1_W, H1_BLOCK, true_cy, mc=False)
    fid_on = field_fidelity(fq, H1_H, H1_W, H1_BLOCK, true_cy, mc=True)
    off = run_side(fq, H1_H, H1_W, H1_BLOCK, mc=False)
    on = run_side(fq, H1_H, H1_W, H1_BLOCK, mc=True)
    return {"apparatus": {"grid": [H1_W, H1_H], "block": H1_BLOCK, "aperture": H1_BLOCK,
                          "object_extent": H1_OBJ, "accel": H1_A, "cy0": H1_CY0,
                          "n_frames": H1_NFRAMES, "texseed": H1_TEXSEED},
            "true_object_cy": ideal_cyi, "true_d2": ideal_d2,
            "ideal_witness": {"status": st_ideal, "accel_coeff": accel_coeff(m_ideal),
                              "mints": m_ideal},
            "field_fidelity_off": fid_off, "field_fidelity_on": fid_on,
            "mc_off_fixed_aperture": off, "mc_on": on}


# ───────────────────────────── byte-identity ─────────────────────────────────

def part_byte_identity():
    rng = np.random.default_rng(H1_TEXSEED + 1)
    block = H1_BLOCK
    mism_none = mism_zero = tot = 0
    for _ in range(6):
        a = rng.integers(0, L, (H1_H, H1_W)).astype(float)
        b = rng.integers(0, L, (H1_H, H1_W)).astype(float)
        v_plain = vector_field(a, b, block)
        v_none = vector_field(a, b, block, predict=None)
        nh, nw = v_plain.shape[:2]
        v_zero = vector_field(a, b, block, predict=np.zeros((nh, nw, 2)))
        mism_none += int(np.sum(v_plain != v_none))
        mism_zero += int(np.sum(v_plain != v_zero))
        tot += v_plain.size
    return {"frame_pairs": 6, "total_vector_components": tot,
            "mismatch_predict_none": mism_none,
            "mismatch_predict_zero": mism_zero,
            "byte_identical": (mism_none == 0 and mism_zero == 0)}


# ─────────────────────────────── controls ────────────────────────────────────

def part_controls():
    out = {}
    # const velocity (MC on) -> the predictor must NOT manufacture curvature.
    # A CONSTANT velocity ABOVE the aperture (vel=7 > aperture 4) so the MC path
    # is genuinely engaged. Two readings:
    #   (a) FIELD level (where the predictor operates, noise-free): the median
    #       block velocity is ~constant -> its 2nd difference is ~0. MC carries
    #       the constant velocity forward as constant; it invents no acceleration.
    #   (b) WITNESS level: the MC-tracked trajectory does NOT carry the parabola
    #       signature a real fall does (no nonzero constant-positive curvature).
    #   (a real fall's field 2nd difference is the acceleration, and its witness
    #    mints exactly that — H1.) The downstream carve centroid noise can drive
    #    the MDL witness to over-fit a noisy near-line to high order, so the
    #    faithful discriminator is the FIELD curvature + the absence of the
    #    parabola signature, NOT a bare "mints order-1".
    CV_VEL = 6                                              # > aperture 4: MC engaged
    fq_cv = quantize(render_const_velocity(vel=CV_VEL, n_frames=H1_NFRAMES))
    true_cv = [H1_CY0 + CV_VEL * t + H1_OBJ / 2.0 for t in range(H1_NFRAMES)]
    fid_cv = field_fidelity(fq_cv, H1_H, H1_W, H1_BLOCK, true_cv, mc=True)
    cv_field_med = [r["median_vy"] for r in fid_cv]
    # frame 1 is the PLAIN bootstrap (no prior field, saturates below vel because
    # vel>aperture); MC then CONVERGES to the constant velocity over a couple of
    # frames (each step climbs by at most the aperture) and HOLDS a flat plateau.
    # The steady TAIL (second half) 2nd difference is the curvature the predictor
    # adds ONCE CONVERGED — for a real fall this tail carries the acceleration
    # (nonzero); for constant velocity it is ~0.
    tail = cv_field_med[len(cv_field_med) // 2:]
    cv_field_d2_steady = np.diff(np.diff(tail)).tolist()
    cv = run_side(fq_cv, H1_H, H1_W, H1_BLOCK, mc=True)
    cv_mints = cv.get("mints") or []
    no_parabola = cv.get("accel_coeff") in (None, 0)
    field_flat = all(abs(x) <= 1.0 for x in cv_field_d2_steady)   # constant-velocity field
    out["const_velocity_mc_on"] = {"longest_run_len": cv["longest_run_len"],
                                   "vel": CV_VEL, "aperture": H1_BLOCK,
                                   "field_median_vy": cv_field_med,
                                   "field_2nd_diff_steady": cv_field_d2_steady,
                                   "field_constant_velocity": field_flat,
                                   "robust_status": cv.get("robust_status"),
                                   "mints": cv_mints,
                                   "cy_int": cv.get("cy_int"), "d2": cv.get("d2"),
                                   "accel_coeff": cv.get("accel_coeff"),
                                   "no_manufactured_curvature": field_flat and no_parabola}
    # static (MC on) -> nothing carved / no mint.
    fq = quantize(render_static(n_frames=H1_NFRAMES))
    stt = run_side(fq, H1_H, H1_W, H1_BLOCK, mc=True)
    out["static_mc_on"] = {"longest_run_len": stt["longest_run_len"],
                           "note": stt.get("note"),
                           "mints": stt.get("mints"), "accel_coeff": stt.get("accel_coeff"),
                           "mints_nothing": stt.get("accel_coeff") is None}
    # random/noise (MC on) -> floors (no confabulated coherent order-2).
    fq = quantize(render_noise(n_frames=H1_NFRAMES, seed=H1_TEXSEED + 2))
    nz = run_side(fq, H1_H, H1_W, H1_BLOCK, mc=True)
    out["noise_mc_on"] = {"longest_run_len": nz["longest_run_len"],
                          "robust_status": nz.get("robust_status"),
                          "mints": nz.get("mints"), "accel_coeff": nz.get("accel_coeff"),
                          "floors": nz.get("accel_coeff") in (None, 0)}
    return out


# ─────────────────────────────── H2 real clip ────────────────────────────────

def decode_grey(ss, dur, fps, gw, gh):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(dur), "-i", CLIP,
           "-vf", f"fps={fps},scale={gw}:{gh},format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (gw * gh)
    return np.frombuffer(raw[:n * gw * gh], dtype=np.uint8).reshape(n, gh, gw)


def part_h2():
    # Native 128x640, the same windows 147000 drove (a=0 there under the fixed
    # aperture). MC ON vs OFF, coeffs read from the graph.
    configs = [
        [55.0, 20.0, 2.0, 128, 640, 6, "real_128x640_b6_2fps"],
        [60.0, 18.0, 3.0, 128, 640, 4, "real_128x640_b4_3fps"],
    ]
    rows = []
    for ss, dur, fps, gw, gh, block, label in configs:
        fq = quantize(decode_grey(ss, dur, fps, gw, gh))
        off = run_side(fq, gh, gw, block, mc=False)
        on = run_side(fq, gh, gw, block, mc=True)
        rows.append({"label": label, "grid": [gw, gh], "block": block, "fps": fps,
                     "n_frames": int(fq.shape[0]),
                     "mc_off": off, "mc_on": on})
    return rows


def main():
    load0 = os.getloadavg()
    result = {"block": "148000-148999",
              "engine_provenance": provenance_stamp(),
              "provenance_line": provenance_line(),
              "H1_synthetic": part_h1(),
              "byte_identity": part_byte_identity(),
              "controls": part_controls(),
              "loadavg_start": list(load0)}

    h1 = result["H1_synthetic"]
    print("=== H1 SYNTHETIC (fast free-fall, aperture-overrunning) ===")
    print(f"  true object cy: {h1['true_object_cy']}  true d2: {h1['true_d2']}")
    print(f"  ideal witness accel_coeff = {h1['ideal_witness']['accel_coeff']} "
          f"(aperture={h1['apparatus']['aperture']})")
    print("  FIELD FIDELITY (median block vy vs true disp; the sensor layer):")
    print("    frame :  " + "  ".join(f"{r['frame']}" for r in h1['field_fidelity_on']))
    print("    true  :  " + "  ".join(f"{r['true_disp']:g}" for r in h1['field_fidelity_on']))
    print("    OFF   :  " + "  ".join(f"{r['median_vy']:g}" for r in h1['field_fidelity_off']))
    print("    ON    :  " + "  ".join(f"{r['median_vy']:g}" for r in h1['field_fidelity_on']))
    off, on = h1["mc_off_fixed_aperture"], h1["mc_on"]
    print(f"  MC OFF (fixed aperture): run={off['longest_run_len']} "
          f"status={off.get('robust_status')} accel_coeff={off.get('accel_coeff')} "
          f"cy={off.get('cy_int')}")
    print(f"  MC ON                  : run={on['longest_run_len']} "
          f"one_id={on.get('run_one_id')} status={on.get('robust_status')} "
          f"accel_coeff={on.get('accel_coeff')} cy={on.get('cy_int')} d2={on.get('d2')}")
    bi = result["byte_identity"]
    print(f"=== BYTE-IDENTITY OFF: none={bi['mismatch_predict_none']} "
          f"zero={bi['mismatch_predict_zero']} / {bi['total_vector_components']} "
          f"-> byte_identical={bi['byte_identical']}")
    ctl = result["controls"]
    print("=== CONTROLS (MC on) ===")
    cvc = ctl['const_velocity_mc_on']
    print(f"  const-velocity (vel={cvc['vel']}>ap{cvc['aperture']}) no manufactured curvature: "
          f"{cvc['no_manufactured_curvature']} (field vy={cvc['field_median_vy']} "
          f"steady d2={cvc['field_2nd_diff_steady']} accel_coeff={cvc['accel_coeff']})")
    print(f"  static -> mints nothing: {ctl['static_mc_on']['mints_nothing']}")
    print(f"  noise -> floors: {ctl['noise_mc_on']['floors']} "
          f"(accel_coeff={ctl['noise_mc_on']['accel_coeff']})")

    if os.environ.get("MC_REAL", "1") == "1":
        result["H2_real_video"] = part_h2()
        print("=== H2 REAL CLIP (128x640) ===")
        for r in result["H2_real_video"]:
            print(f"  [{r['label']}] MC OFF: run={r['mc_off']['longest_run_len']} "
                  f"accel={r['mc_off'].get('accel_coeff')} "
                  f"status={r['mc_off'].get('robust_status')} "
                  f"maxdisp={r['mc_off'].get('max_disp_cells')}c/ap{r['block']} "
                  f"|| MC ON: run={r['mc_on']['longest_run_len']} "
                  f"accel={r['mc_on'].get('accel_coeff')} "
                  f"status={r['mc_on'].get('robust_status')} "
                  f"maxdisp={r['mc_on'].get('max_disp_cells')}c")

    result["loadavg_end"] = list(os.getloadavg())
    outp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "results", "motion_compensated_measure.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", outp)


if __name__ == "__main__":
    main()
