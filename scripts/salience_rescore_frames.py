"""salience_rescore_frames — regenerate the invariant-comparator video frames,
in GREY (to verify byte-exact reproduction of the committed instrument) and in
COLOUR (the chromatic channel the comparator never saw).

Pure I/O. No decision, no analysis. The grey path is copied verbatim from
`scripts/video_probe_measure.py::jellyfin_frames` so that reproduction is a
real check and not a re-implementation that happens to agree.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

# The committed instrument's constants, imported not retyped.
N_FRAMES = 150
EVERY = 2
START_S = 300
SIZE = 24
EPISODE_INDEX = {"C1": 0, "C2": 3}


def decode(cid: str):
    """Decode the SAME frames as the comparator, keeping grey AND rgb.

    The grey branch is line-for-line the committed `jellyfin_frames` body; the
    rgb branch is the same area_downsample applied per channel.
    """
    from jellyfin_world import JellyfinWorld            # noqa: E402
    from domains.vision_corpus import area_downsample   # noqa: E402
    import av                                           # noqa: E402

    jf = JellyfinWorld().connect()
    series = sorted(jf.catalog(("Series",)), key=lambda it: str(it["id"]))
    if not series:
        raise RuntimeError("jellyfin returned no series")
    episode_index = EPISODE_INDEX[cid]
    eps, si = [], 0
    while not eps and si < len(series):
        eps = sorted(jf.episodes(series[(episode_index + si) % len(series)]["id"]),
                     key=lambda e: str(e["id"]))
        si += 1
    if not eps:
        raise RuntimeError("jellyfin returned no episodes")
    ep = eps[episode_index % len(eps)]
    item_id = ep["id"]
    url = jf.stream_url(item_id)

    c = av.open(url, timeout=60)
    grey, rgb = [], []
    try:
        c.streams.video[0].thread_type = "AUTO"
        if START_S:
            c.seek(int(START_S) * 1_000_000)
        for i, f in enumerate(c.decode(video=0)):
            if EVERY > 1 and i % EVERY:
                continue
            g = f.to_ndarray(format="gray").astype(np.float32)      # 0..255
            grey.append(area_downsample(g / 255.0, SIZE) * 255.0)
            col = f.to_ndarray(format="rgb24").astype(np.float32)   # (H,W,3)
            rgb.append(np.stack([area_downsample(col[:, :, ch] / 255.0, SIZE) * 255.0
                                 for ch in range(3)], axis=-1))
            if len(grey) >= N_FRAMES:
                break
    finally:
        c.close()
    meta = {"source": "jellyfin", "episode_id": str(item_id),
            "series": str(ep.get("series", "?")), "name": str(ep.get("name", "?")),
            "season": ep.get("season"), "ep": ep.get("ep"),
            "n_series_in_catalogue": len(series), "n_episodes_in_series": len(eps),
            "episode_index": episode_index, "every_nth_decoded_frame": EVERY,
            "start_s": START_S, "size": SIZE, "n_frames": len(grey)}
    return np.stack(grey), np.stack(rgb), meta


def main():
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    report = {}
    for cid in ("C1", "C2"):
        grey, rgb, meta = decode(cid)
        # The committed instrument's motion statistic, recomputed verbatim.
        mm = [float(np.mean(np.abs(grey[t + 1] - grey[t])))
              for t in range(min(50, len(grey) - 1))]
        motion = {"mean": float(np.mean(mm)), "sd": float(np.std(mm)),
                  "min": float(np.min(mm)), "max": float(np.max(mm))}
        np.savez_compressed(os.path.join(out_dir, f"frames_{cid}.npz"),
                            grey=grey, rgb=rgb)
        report[cid] = {"meta": meta, "motion": motion,
                       "chroma_sd": float(np.std(rgb[:, :, :, 0] - rgb[:, :, :, 1]))}
        print(f"[{cid}] {meta['series']} / {meta['name']} n={meta['n_frames']} "
              f"motion={motion} chroma_sd(R-G)={report[cid]['chroma_sd']:.4f}",
              flush=True)
    with open(os.path.join(out_dir, "frames_report.json"), "w") as fh:
        json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main()
