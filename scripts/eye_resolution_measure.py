#!/usr/bin/env python3
"""EYE RESOLUTION vs the free-fall acceleration signal (block 147000-147999).

CLAIM: grid RESOLUTION is the lever that lifts a free-fall's curvature above the
INTEGER-centroid quantization floor. The eye reports an integer cy (an in-frame
coordinate -- the frame/continuum invariant), so integer-rounding a continuous
parabola gives a FIXED ~2-cell jitter in the 2nd difference REGARDLESS of R,
while the curvature magnitude grows proportional to R. So SNR grows with R and
there is a resolution threshold R* above which the ROBUST/MDL witness (146000)
mints LatentDimension{latent:time, order:2} where a lower R floors.

This is MEASUREMENT ONLY: NO Rust, NO seed change. Every order-2 DECISION is the
seed rule (`time_infer_mint_robust` / the default exact mint); this script only
renders / ingests the cy sequence and reads the minted LatentDimension back OUT
of the graph. The witness's tolerance FALLS OUT of the integer bit-costs -- this
script adds NO tolerance constant anywhere (PROTOCOL section 13).

Parts:
  A  IDEAL ORACLE sweep over R in {64,128,256,512,1024}: render a real free-fall
     as a constant-physical-size hard disc at sub-cell position, quantize to R
     rows, read the integer centroid, and drive that cy through BOTH the ROBUST
     and the EXACT native witnesses. Record |curv|, dispersion, SNR, and each
     witness's minted order. R* = the ladder point where the robust mint flips
     to order-2 (MEASURED, never a constant -- PROTOCOL section 13).
  A-controls  const-velocity -> order-1; static -> nothing; random -> floor;
              and the EXACT witness on the SAME free-fall cy (H2).
  B  REAL VIDEO end-to-end (H2b) at 64x320 and 128x640: common-fate carve
     (`native.segment_motion`) + velocity-predictive tracker -> integer cy ->
     ROBUST witness. Plus H3: per-frame displacement (cells) vs block/aperture.

The rendering is the cross-frame map (continuous -> stepped); the observed
centroid is in-frame integer. Frame/continuum invariant, deliberately.
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

# ── APPARATUS (the SYNTHETIC cross-frame rendering map; FIXED in advance, taken
#    verbatim from the burned scoping reference res_sweep_scope.py). These are
#    NOT witness thresholds -- they define the physical fall being rendered. ──
DISC_FRAC = 0.03      # disc radius as a fraction of R (constant physical size)
DROP_FRAC = 0.90      # fraction of the field the parabola covers
N_FRAMES = 12         # samples of the continuous parabola (>=4 for an order-2 witness)
LADDER = [64, 128, 256, 512, 1024]
DT = ["pred", "coord:r", "coord:c", "val"]


# ───────────────────────────── ideal-oracle render ───────────────────────────

def fall_centroids(R, n_frames=N_FRAMES, disc_frac=DISC_FRAC, drop_frac=DROP_FRAC):
    """Render a real free-fall at grid height R; return integer centroid rows.
    Constant-physical-size hard disc, hard binary mask (the carve), centroid =
    mean masked row rounded to int (the eye reports integer cy)."""
    W = max(8, R // 5)
    cx = W / 2.0
    rad = disc_frac * R
    ts = np.arange(n_frames, dtype=float)
    g = 2.0 * drop_frac / (n_frames - 1) ** 2
    y_frac = 0.5 * g * ts ** 2
    cy_real = y_frac * R + rad + 1
    rr, cc = np.mgrid[0:R, 0:W]
    cents = []
    for yc in cy_real:
        d2 = (rr - yc) ** 2 + (cc - cx) ** 2
        mask = d2 <= rad ** 2
        if mask.sum() == 0:
            continue
        cents.append(int(round(rr[mask].mean())))
    return cents


def const_velocity_centroids(R, n_frames=N_FRAMES):
    """A rigid disc translating at CONSTANT velocity (no acceleration). Same
    render, straight-line physical y(t) -> the control that must mint order-1."""
    W = max(8, R // 5)
    cx = W / 2.0
    rad = DISC_FRAC * R
    ts = np.arange(n_frames, dtype=float)
    y_frac = (DROP_FRAC / (n_frames - 1)) * ts        # linear, constant velocity
    cy_real = y_frac * R + rad + 1
    rr, cc = np.mgrid[0:R, 0:W]
    cents = []
    for yc in cy_real:
        d2 = (rr - yc) ** 2 + (cc - cx) ** 2
        mask = d2 <= rad ** 2
        if mask.sum() == 0:
            continue
        cents.append(int(round(rr[mask].mean())))
    return cents


# ───────────────── drive a cy sequence through the ACTUAL witness ─────────────

def witness(native, cy, *, robust):
    """The Rust Term product (TUPLES) on a perceived cy: explained + order.
    A frame is a single point at (round(cy), 0). Read straight off the Term."""
    frames = [[["obj", int(round(y)), 0, "obj"]] for y in cy]
    out = {}
    for f in ("explained", "order"):
        out[f] = native.evaluate(
            {"type": "TimeInfer", "sequence": {"type": "Lit", "value": frames},
             "codebook_type": "ShapeSignature", "max_b": 8, "field": f,
             "robust": robust}, {})
    return out


def graph_mint(s, ag, native, cy, *, status):
    """Ingest cy as a motion Observation and run the seeded run_rules fixpoint;
    read the minted latent:time LatentDimension back OUT of the graph. `status`
    selects the witness rule ('motion_seq'=exact, 'motion_seq_robust'=robust).
    The order-N DECISION is the seed rule; this is pure ingest+read-back I/O."""
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
            mints.append((a.get("generator_kind"), a.get("order"),
                          tuple(a.get("coeffs") or ())))
    return st, mints


def d2_stats(cy):
    a = np.asarray(cy, dtype=np.int64)
    d1 = np.diff(a); d2 = np.diff(d1)
    med = int(np.median(d2)) if len(d2) else 0
    disp = int(d2.max() - d2.min()) if len(d2) else 0
    curv = abs(med)
    snr = round(curv / (disp + 1e-9), 3)
    exact_flat = (len(set(d2.tolist())) == 1) if len(d2) else False
    return dict(d2=d2.tolist(), curv=curv, disp=disp, snr=snr, exact_flat=exact_flat)


# ─────────────────────────── Part A: ideal-oracle sweep ───────────────────────

def part_a():
    rows = []
    for R in LADDER:
        cy = fall_centroids(R)
        stat = d2_stats(cy)
        # fresh boot per R so mints don't accumulate across the ladder.
        s, ag, native = fw.boot_falling()
        term_rob = witness(native, cy, robust=True)
        term_ex = witness(native, cy, robust=False)
        # graph mint on FRESH boots (each ingest is one Observation).
        s1, a1, n1 = fw.boot_falling()
        gst_rob, gm_rob = graph_mint(s1, a1, n1, cy, status="motion_seq_robust")
        s2, a2, n2 = fw.boot_falling()
        gst_ex, gm_ex = graph_mint(s2, a2, n2, cy, status="motion_seq")
        rows.append({
            "R": R, "n_cy": len(cy), "cy": cy, **stat,
            "term_robust_order": term_rob["order"],
            "term_robust_explained": term_rob["explained"],
            "term_exact_order": term_ex["order"],
            "term_exact_explained": term_ex["explained"],
            "graph_robust_status": gst_rob,
            "graph_robust_mint_orders": [m[1] for m in gm_rob],
            "graph_exact_status": gst_ex,
            "graph_exact_mint_orders": [m[1] for m in gm_ex],
        })
    # R* = lowest ladder R whose ROBUST graph mint carries order-2 (MEASURED).
    rstar = None
    for r in rows:
        if 2 in r["graph_robust_mint_orders"]:
            rstar = r["R"]; break
    return {"ladder": LADDER, "n_frames": N_FRAMES, "rows": rows, "R_star": rstar}


# ─────────────────────────── Part A controls ─────────────────────────────────

def part_a_controls():
    out = {}
    for R in LADDER:
        # const velocity, EXACT integer ramp (no sub-cell jitter) -> order-1, NOT
        # order-2. The clean prereg control: a rigid disc stepping an integer
        # number of cells per frame. Exact-first path mints order-1 even under
        # the robust status.
        v = max(1, R // 64)
        cye = list(range(0, v * N_FRAMES, v))
        s, ag, native = fw.boot_falling()
        st_e1, m_e1 = graph_mint(s, ag, native, cye, status="motion_seq_robust")
        # const velocity, RENDERED (sub-cell quantization jitter) -> must NOT read
        # as order-2 (the confabulation bar for the robust witness).
        cyv = const_velocity_centroids(R)
        s, ag, native = fw.boot_falling()
        st_v, m_v = graph_mint(s, ag, native, cyv, status="motion_seq_robust")
        # static -> nothing
        cys = [10] * N_FRAMES
        s, ag, native = fw.boot_falling()
        st_s, m_s = graph_mint(s, ag, native, cys, status="motion_seq_robust")
        # random -> floor (seeded, deterministic; a burned confirmatory seed)
        rng = np.random.default_rng(147000 + R)
        cyr = np.cumsum(rng.integers(-6, 7, size=N_FRAMES)).tolist()
        s, ag, native = fw.boot_falling()
        st_r, m_r = graph_mint(s, ag, native, cyr, status="motion_seq_robust")
        out[R] = {
            "const_velocity_exact": {"cy": cye, "status": st_e1,
                                     "orders": [m[1] for m in m_e1]},
            "const_velocity_rendered": {"cy": cyv, "d2": d2_stats(cyv)["d2"],
                                        "status": st_v, "orders": [m[1] for m in m_v]},
            "static": {"status": st_s, "orders": [m[1] for m in m_s]},
            "random": {"cy": cyr, "status": st_r, "orders": [m[1] for m in m_r]},
        }
    return out


# ─────────────────────────── Part B: real video ──────────────────────────────

def decode_grey(ss, dur, fps, gw, gh):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(dur), "-i", CLIP,
           "-vf", f"fps={fps},scale={gw}:{gh},format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (gw * gh)
    return np.frombuffer(raw[:n * gw * gh], dtype=np.uint8).reshape(n, gh, gw)


def quantize(luma_u8, levels=4):
    return (luma_u8.astype(np.int32) * levels) // 256


def carve_track(frames_q, gh, gw, block):
    """Common-fate carve every frame; track the falling object = LARGEST
    non-ground region by persistent id. Also record per-frame displacement of
    the tracked object (cells) for the H3 aperture characterization."""
    s, ag, native = fw.boot_falling()
    game, cell_ids = fw.setup_world(native, gh, gw)
    track, disp = [], []
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
        track.append(obj)
        prev = cur
    return s, ag, native, track


def run_real(ss, dur, fps, gw, gh, block, label):
    fq = quantize(decode_grey(ss, dur, fps, gw, gh))
    s, ag, native, track = carve_track(fq, gh, gw, block)
    run = fw.longest_continuous_run(track)
    out = {"label": label, "grid": [gw, gh], "block": block, "aperture": block,
           "fps": fps, "n_frames": int(fq.shape[0]), "n_carved": len(track),
           "n_with_obj": sum(1 for b in track if b is not None),
           "longest_run_len": len(run)}
    if len(run) >= 4:
        cy = [b["cy"] for b in run]
        ids = {b["id"] for b in run}
        cyi = [int(round(v)) for v in cy]
        out["run_one_id"] = (len(ids) == 1)
        out["cy_int"] = cyi
        out.update({"d2_" + k: v for k, v in d2_stats(cyi).items() if k != "d2"})
        out["d2"] = d2_stats(cyi)["d2"]
        # per-frame displacement of the tracked object (cells) -- H3 aperture.
        d1 = [abs(b - a) for a, b in zip(cyi, cyi[1:])]
        out["per_frame_disp_cells"] = d1
        out["max_disp_cells"] = max(d1) if d1 else 0
        out["disp_over_aperture"] = round((max(d1) if d1 else 0) / block, 2)
        # ROBUST witness (fresh boot) + EXACT witness on the SAME cy.
        sr, ar, nr = fw.boot_falling()
        st_r, m_r = graph_mint(sr, ar, nr, cyi, status="motion_seq_robust")
        se, ae, ne = fw.boot_falling()
        st_e, m_e = graph_mint(se, ae, ne, cyi, status="motion_seq")
        out["robust_status"] = st_r
        out["robust_mint_orders"] = [m[1] for m in m_r]
        out["exact_status"] = st_e
        out["exact_mint_orders"] = [m[1] for m in m_e]
    else:
        out["note"] = "longest continuous run < 4 frames -- no order-2 witness"
    return out


def part_b():
    # Two windows over the fall, matched fps, at 64x320 (FLOORED in block 145000)
    # and native-scale 128x640 (2x). Blocks per the 145000 sweep aperture.
    configs = [
        [55.0, 20.0, 2.0, 64, 320, 6, "real_64x320_b6"],
        [55.0, 20.0, 2.0, 128, 640, 6, "real_128x640_b6"],
        [60.0, 18.0, 3.0, 64, 320, 4, "real_64x320_b4_3fps"],
        [60.0, 18.0, 3.0, 128, 640, 4, "real_128x640_b4_3fps"],
    ]
    return [run_real(*c) for c in configs]


def main():
    load0 = os.getloadavg()
    result = {
        "block": "147000-147999",
        "engine_provenance": provenance_stamp(),
        "provenance_line": provenance_line(),
        "apparatus": {"disc_frac": DISC_FRAC, "drop_frac": DROP_FRAC,
                      "n_frames": N_FRAMES, "ladder": LADDER},
        "A_ideal_oracle": part_a(),
        "A_controls": part_a_controls(),
        "loadavg_start": list(load0),
    }
    print("=== PART A: ideal-oracle sweep ===")
    print(f"{'R':>5} | {'|curv|':>6} | {'disp':>4} | {'SNR':>6} | "
          f"{'robust':>6} | {'exact':>5}")
    for r in result["A_ideal_oracle"]["rows"]:
        print(f"{r['R']:>5} | {r['curv']:>6} | {r['disp']:>4} | {r['snr']:>6} | "
              f"{str(r['graph_robust_mint_orders']):>6} | "
              f"{str(r['graph_exact_mint_orders']):>5}")
    print(f"R* (robust flips to order-2) = {result['A_ideal_oracle']['R_star']}")
    if os.environ.get("EYE_RES_REAL", "1") == "1":
        result["B_real_video"] = part_b()
        print("=== PART B: real video ===")
        for r in result["B_real_video"]:
            print(f"[{r['label']}] run={r['longest_run_len']} "
                  f"robust={r.get('robust_mint_orders')} "
                  f"exact={r.get('exact_mint_orders')} "
                  f"maxdisp={r.get('max_disp_cells')}c/ap{r['aperture']}="
                  f"{r.get('disp_over_aperture')}")
    result["loadavg_end"] = list(os.getloadavg())
    outp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "results", "eye_resolution_measure.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", outp)


if __name__ == "__main__":
    main()
