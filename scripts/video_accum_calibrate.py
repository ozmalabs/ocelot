"""VIDEO ACCUMULATION — MEASURE CALIBRATION (protocol section 1).

Seeds 74900-74999, DECLARED BURNED PILOT. Establishes that the two candidate
read-outs have DYNAMIC RANGE before any arm is run:

  * an IDEAL codebook  -- the grown one, i.e. what the mechanism produces;
  * a NULL codebook    -- K entries of calibration noise, which holds no video
                          content at all and is the metric's floor.

It DOES NOT run the size-matched control, which is the confirmatory contrast.
C1 only. If a read-out cannot separate IDEAL from NULL it is blind and must not
be used (section 1 clause 4, and the rung-8B lesson).
"""
from __future__ import annotations

import importlib.util as iu
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from domains import engine_provenance as ep  # noqa: E402

ep.engine_preamble()

import numpy as np  # noqa: E402

from domains import video_accumulation_world as aw  # noqa: E402


def _vp():
    spec = iu.spec_from_file_location("vp", str(HERE / "video_probe_measure.py"))
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def eval_pass(entries, qr, gr, held, seed):
    w = aw.AccumWorld("ncc")
    w.calibrate(np.random.RandomState(seed), 8)
    w.run()
    w.install_codebook(entries)
    w.freeze()
    per_frame_acc, per_frame_max = [], []
    hist = {}
    for t in held:
        a, m = [], []
        for i in range(16):
            w.present(qr[t][i], gr[t][i], tag=f"ev_{t}_{i}")
            w.run()
            r = w.read_full()
            w.refreeze()
            hist[r["status"]] = hist.get(r["status"], 0) + 1
            a.append(1.0 if r["status"] == "is_held" else 0.0)
            m.append(float(r["is_max"]))
        per_frame_acc.append(float(np.mean(a)))
        per_frame_max.append(float(np.mean(m)))
    k, f = w.assert_frozen()
    return {"K": k, "floor": f, "status_hist": hist,
            "accept": float(np.mean(per_frame_acc)),
            "mean_is_max": float(np.mean(per_frame_max)),
            "acc_rows": per_frame_acc, "max_rows": per_frame_max}


def main():
    print(ep.provenance_line())
    train, held = aw.block_split(150)
    vp = _vp()
    frames, meta = vp.jellyfin_frames(150, every=2, start_s=300, size=aw.GRID,
                                      episode_index=0)
    assert meta.get("episode_id") == "08630d4b7b215c469df19b9c42d7b617"
    q = [aw.quantize(f) for f in frames]
    qr = [aw.regions_of(x) for x in q]
    gr = [aw.grey_regions_of(f) for f in frames]

    w = aw.AccumWorld("ncc")
    w.calibrate(np.random.RandomState(74902), 8)
    w.run()
    t0 = time.time()
    mints = []
    for t in train:
        for i in range(16):
            k0 = w.codebook_size()
            w.present(qr[t][i], gr[t][i], tag=f"{t}_{i}")
            w.run()
            if w.codebook_size() > k0:
                mints.append((t, i))
    print(f"GROW: {len(train)} frames, K={w.codebook_size()}, "
          f"{len(mints)} mints, {time.time()-t0:.1f}s")
    K = len(mints)

    out = {"provenance": ep.provenance_line(), "K": K,
           "mints": [[int(t), int(i)] for t, i in mints]}

    ideal = [(f"{t}_{i}", qr[t][i], gr[t][i]) for t, i in mints]
    rng = np.random.RandomState(74903)
    null = [(f"null_{j}",
             rng.randint(0, aw.K_LEVELS, (aw.REGION, aw.REGION)),
             rng.randint(0, 256, (aw.REGION, aw.REGION)).astype(float))
            for j in range(K)]

    for name, ents in (("IDEAL", ideal), ("NULL", null)):
        t0 = time.time()
        r = eval_pass(ents, qr, gr, held, 74904)
        out[name] = r
        print(f"{name}: K={r['K']} floor={r['floor']:.4f} "
              f"accept={r['accept']:.4f} mean_is_max={r['mean_is_max']:.4f} "
              f"({time.time()-t0:.1f}s)")

    for m, key in (("accept", "acc_rows"), ("mean_is_max", "max_rows")):
        a = np.asarray(out["IDEAL"][key])
        b = np.asarray(out["NULL"][key])
        print(f"  RANGE[{m}]: ideal={a.mean():.4f} null={b.mean():.4f} "
              f"delta={(a-b).mean():+.4f} sd_ideal={a.std(ddof=1):.4f}")

    for frac in (0.25, 0.5):
        kk = max(1, int(K * frac))
        r = eval_pass(ideal[:kk], qr, gr, held, 74904)
        out[f"IDEAL_K{kk}"] = r
        print(f"IDEAL@K={kk}: accept={r['accept']:.4f} "
              f"mean_is_max={r['mean_is_max']:.4f} floor={r['floor']:.4f}")

    p = ROOT / "results/video_accum_calibrate.json"
    p.write_text(json.dumps(out, indent=1, default=float))
    print(f"wrote {p}")


if __name__ == "__main__":
    main()
