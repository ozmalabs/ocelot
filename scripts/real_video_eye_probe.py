#!/usr/bin/env python3
"""REAL-VIDEO EYE PROBE — point the toddler eye at real footage, measure the wall.

Pre-registration: VISION_REAL_VIDEO_PROBE_PREREG.md. Honest exploratory probe,
NO CONFIRM target. Decode a real 60-frame cut-free window of natural video (a
moving presenter), greyscale + downsample to a 64x36 grid, quantize luma to L
grey levels, and drive the EXISTING eye (`native.segment` ->
`Substrate::segment_and_track`) frame by frame. Everything is read FROM THE GRAPH
via `falling_world.read_regions`. No Rust, no seed, deterministic (no RNG).
"""
from __future__ import annotations
import json, os, subprocess, time
import numpy as np

from domains.engine_provenance import engine_preamble
engine_preamble()
from domains import falling_world as fw  # noqa: E402

CLIP = ("/home/matt/ozma/internal/research/experiments/gamma-substrate/"
        "naming_corpus/ABC_Phonics_Chant_for_Children_Sounds_and_Actions_from_A_to_.mp4")
SS, DUR, FPS = 50.0, 4.0, 15
GW, GH = 64, 36            # grid (cols x rows); aspect 1.78 ~= 854/480
LEVELS = [4, 8, 16, 32]    # L=4 is the eye's shipped default (fb downsample_quantize)
SPECKLE = 2                # count <= 2 cells = texture speckle
MIN_ORBIT = fw.MIN_ORBIT   # 4 — the order-N witness minimum


def decode_grey(clip, ss, dur, fps, gw, gh):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(dur), "-i", clip,
           "-vf", f"fps={fps},scale={gw}:{gh},format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (gw * gh)
    return np.frombuffer(raw[:n * gw * gh], dtype=np.uint8).reshape(n, gh, gw)


def quantize(luma_u8, L):
    """The eye's native scheme: v = (luma * L) // 256 -> L distinct grey levels."""
    return ((luma_u8.astype(np.int32) * L) // 256)


def run_one_level(frames_q):
    """Drive the eye over the quantized frames; return per-frame region records
    read from the graph, plus per-frame wall-clock."""
    s, ag, native = fw.boot_falling()
    game, cell_ids = fw.setup_world(native, GH, GW)
    per_frame = []          # list of {regions:[...], ...}
    walls = []
    for fi in range(frames_q.shape[0]):
        vals = frames_q[fi].reshape(-1).tolist()   # row-major GH*GW
        t0 = time.perf_counter()
        native.set_attr(game, "frame", float(fi))
        native.segment(game, GH, GW, vals, cell_ids)
        regs = fw.read_regions(native, game)
        walls.append(time.perf_counter() - t0)
        per_frame.append(regs)
    return per_frame, walls


def analyse(per_frame):
    N = len(per_frame)
    total_cells = GW * GH
    # per-frame carve stats
    n_regions = [len(f) for f in per_frame]
    n_nonground = [sum(1 for r in f if r["is_ground"] == 0.0) for f in per_frame]
    ground_frac = []
    speckle_per_frame = []
    largest_nonground_id = []
    for f in per_frame:
        gnd = [r for r in f if r["is_ground"] == 1.0]
        ground_frac.append((max((r["count"] for r in gnd), default=0.0)) / total_cells)
        speckle_per_frame.append(sum(1 for r in f if r["count"] <= SPECKLE))
        ng = [r for r in f if r["is_ground"] == 0.0]
        if ng:
            big = max(ng, key=lambda r: r["count"])
            largest_nonground_id.append((big["id"], big["count"]))
        else:
            largest_nonground_id.append((None, 0.0))
    # id lifetimes: frames each id appears in
    id_frames = {}
    id_counts = {}
    id_isground = {}
    for fi, f in enumerate(per_frame):
        for r in f:
            id_frames.setdefault(r["id"], []).append(fi)
            id_counts.setdefault(r["id"], []).append(r["count"])
            id_isground.setdefault(r["id"], []).append(r["is_ground"])
    lifetimes = {i: len(fr) for i, fr in id_frames.items()}
    # longest CONSECUTIVE run per id (id may in principle skip a frame)
    def longest_consecutive(fr):
        fr = sorted(fr); best = cur = 1
        for a, b in zip(fr, fr[1:]):
            cur = cur + 1 if b == a + 1 else 1
            best = max(best, cur)
        return best
    consec = {i: longest_consecutive(fr) for i, fr in id_frames.items()}
    n_ids = len(lifetimes)
    ephemeral = [i for i, L in lifetimes.items() if L == 1]
    churn = len(ephemeral) / n_ids if n_ids else 0.0
    # median size per id + whether the id is (mostly) ground
    id_med = {i: float(np.median(id_counts[i])) for i in id_counts}
    id_ground = {i: (np.mean(id_isground[i]) >= 0.5) for i in id_isground}

    # --- RECYCLING-ROBUST tracking (node ids are RECYCLED on death — verified,
    #     so a raw node-id is NOT a stable object handle across real-video
    #     births/deaths). Measure genuine continuity by CENTROID proximity
    #     between consecutive frames instead. ---
    CONT_R = 3.0  # a genuine same-region hop must move <= 3 cells/frame
    # per (id): map frame -> (cy,cx)
    id_pos = {}
    for fi, f in enumerate(per_frame):
        for r in f:
            id_pos.setdefault(r["id"], {})[fi] = (r["cy"], r["cx"], r["count"])
    # false-persist rate: consecutive-frame id matches whose centroid JUMPED
    # (> CONT_R) = a recycled-id collision (region A reaped, id reused by B)
    persist_pairs = 0
    false_pairs = 0
    true_runs = []          # longest genuinely-continuous single-region run
    for i, fp in id_pos.items():
        frs = sorted(fp)
        cur = 1
        best = 1
        for a, b in zip(frs, frs[1:]):
            if b == a + 1:
                persist_pairs += 1
                (ya, xa, _), (yb, xb, _) = fp[a], fp[b]
                if abs(ya - yb) + abs(xa - xb) <= CONT_R:
                    cur += 1
                    best = max(best, cur)
                else:
                    false_pairs += 1
                    cur = 1
            else:
                cur = 1
        true_runs.append((i, best))
    false_persist_rate = false_pairs / persist_pairs if persist_pairs else 0.0
    true_consec_max = max((b for _, b in true_runs), default=0)
    # genuine learning-loop candidates: NON-ground, NON-speckle regions whose
    # true continuous run >= MIN_ORBIT
    true_run_of = dict(true_runs)
    genuine_trackable = [i for i in true_run_of
                         if true_run_of[i] >= MIN_ORBIT and not id_ground.get(i, False)
                         and id_med.get(i, 0) > SPECKLE]
    # confab proxy: region-OBSERVATIONS belonging to ephemeral-or-speckle ids
    total_obs = sum(len(f) for f in per_frame)
    confab_ids = {i for i in lifetimes
                  if (lifetimes[i] == 1 or id_med[i] <= SPECKLE) and not id_ground[i]}
    confab_obs = sum(1 for f in per_frame for r in f if r["id"] in confab_ids)
    confab_obs_rate = confab_obs / total_obs if total_obs else 0.0
    nonground_ids = [i for i in lifetimes if not id_ground[i]]
    confab_id_rate = (len(confab_ids) / len(nonground_ids)) if nonground_ids else 0.0
    # learning-loop feasibility: any NON-ground, NON-speckle id with a
    # consecutive run >= MIN_ORBIT, tracked as ONE id
    coherent = [(i, consec[i], id_med[i]) for i in nonground_ids
                if consec[i] >= MIN_ORBIT and id_med[i] > SPECKLE]
    coherent.sort(key=lambda t: (-t[1], -t[2]))
    # main-object stability: modal largest-non-ground id and its run
    from collections import Counter
    lidc = Counter(i for i, _ in largest_nonground_id if i is not None)
    modal_main = lidc.most_common(1)[0] if lidc else (None, 0)
    return {
        "n_frames": N,
        "n_regions_mean": float(np.mean(n_regions)),
        "n_regions_min": int(min(n_regions)), "n_regions_max": int(max(n_regions)),
        "n_nonground_mean": float(np.mean(n_nonground)),
        "n_nonground_min": int(min(n_nonground)), "n_nonground_max": int(max(n_nonground)),
        "ground_frac_mean": float(np.mean(ground_frac)),
        "ground_frac_min": float(min(ground_frac)), "ground_frac_max": float(max(ground_frac)),
        "speckle_per_frame_mean": float(np.mean(speckle_per_frame)),
        "n_distinct_ids": n_ids,
        "n_nonground_ids": len(nonground_ids),
        "lifetime_max": int(max(lifetimes.values())) if lifetimes else 0,
        "lifetime_mean": float(np.mean(list(lifetimes.values()))) if lifetimes else 0.0,
        "consec_run_max_RAWID": int(max(consec.values())) if consec else 0,
        "churn_1frame_frac_RAWID": churn,
        "NOTE_rawid": "raw node-id metrics are CONTAMINATED by id recycling; use the robust ones below",
        "gapped_id_frac": float(np.mean([1.0 if (max(id_frames[i]) - min(id_frames[i]) + 1) != len(id_frames[i]) else 0.0 for i in id_frames])) if id_frames else 0.0,
        "false_persist_rate": false_persist_rate,
        "true_consec_run_max": int(true_consec_max),
        "n_genuine_trackable_ge4": len(genuine_trackable),
        "confab_obs_rate": confab_obs_rate,
        "confab_id_rate": confab_id_rate,
        "coherent_trackable": [{"id": int(i), "consec_run": int(c), "med_count": m}
                               for i, c, m in coherent[:10]],
        "n_coherent_trackable": len(coherent),
        "modal_main_id": (int(modal_main[0]) if modal_main[0] is not None else None,
                          int(modal_main[1])),
    }


def main():
    load0 = os.getloadavg()
    luma = decode_grey(CLIP, SS, DUR, FPS, GW, GH)
    assert luma.shape[0] >= 30, f"expected ~60 frames, got {luma.shape[0]}"
    # verify cut-free (documented in prereg)
    d = np.abs(np.diff(luma.astype(np.int32), axis=0)).mean(axis=(1, 2))
    result = {
        "clip": os.path.basename(CLIP), "ss": SS, "dur": DUR, "fps": FPS,
        "grid": [GW, GH], "n_frames_decoded": int(luma.shape[0]),
        "interframe_diff_mean": float(d.mean()), "interframe_diff_max": float(d.max()),
        "cut_free": bool((d > 20).sum() == 0),
        "levels": {},
        "wall_ms_per_frame": {},
    }
    for L in LEVELS:
        fq = quantize(luma, L)
        per_frame, walls = run_one_level(fq)
        result["levels"][str(L)] = analyse(per_frame)
        result["wall_ms_per_frame"][str(L)] = {
            "mean": float(np.mean(walls) * 1e3), "max": float(np.max(walls) * 1e3),
        }
        a = result["levels"][str(L)]
        print(f"L={L:2d}: nonground/frame mean={a['n_nonground_mean']:6.1f} "
              f"(max {a['n_nonground_max']:3d}) ground_frac={a['ground_frac_mean']:.2f} "
              f"speckle/frame={a['speckle_per_frame_mean']:5.1f} | confab_obs={a['confab_obs_rate']:.2f} "
              f"| gapped_ids={a['gapped_id_frac']:.2f} false_persist={a['false_persist_rate']:.2f} "
              f"TRUE_consec_max={a['true_consec_run_max']:2d} genuine_track>=4={a['n_genuine_trackable_ge4']:2d} "
              f"wall={result['wall_ms_per_frame'][str(L)]['mean']:.1f}ms")
    result["loadavg_start"] = list(load0)
    result["loadavg_end"] = list(os.getloadavg())
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "real_video_probe.json")
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", out)


if __name__ == "__main__":
    main()
