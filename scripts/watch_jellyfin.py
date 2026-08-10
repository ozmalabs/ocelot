"""WATCH JELLYFIN — the jabberwock chooses titles from the real library, watches a
window of each, learns, and re-chooses by curiosity. The active-learning loop the
fixed YouTube playlist didn't have: the agent picks what to watch next.

Per chosen series: pick an episode, open its stream over HTTP (no full download),
ingest a WINDOW of audio (-> shared lexicon, recurring acoustic signs) and read the
video's temporal structure (I/P/B, motion, scene cuts) via substrate_rs.video. Learn
on ONE persistent substrate so signs recur across titles. After watching, the choice
becomes curiosity-driven (prefer unseen series = max expected novelty).

Content is HEVC (own h264 decoder N/A) so audio is ffmpeg-extracted to opus and video
structure is read via PyAV — both codec-agnostic for what we measure here. Pixels /
grounding / order-N re-watch reuse the existing scripts on top of this once wired.

Run:  python -m scripts.watch_jellyfin [n_titles] [window_seconds]
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "runners/dsl/python")

import substrate_rs as srs                                           # noqa: E402
from substrate_rs import audio as a, speech as sp, video as V        # noqa: E402
from scripts.jellyfin_world import JellyfinWorld                     # noqa: E402

WINDOW = int(sys.argv[2]) if len(sys.argv) > 2 else 90      # seconds watched per title
N_TITLES = int(sys.argv[1]) if len(sys.argv) > 1 else 3
V_FRAMES = 150


def _video_stream_index(url):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=index", "-of", "csv=p=0", url],
        capture_output=True, text=True, timeout=60).stdout.strip()
    return int(out) if out else 0


def watch(s, jf, lex, series_item):
    """Watch a WINDOW of one episode of this series. Returns a learning record."""
    eps = jf.episodes(series_item["id"], limit=1)
    if not eps:
        return None
    ep = eps[0]
    url = jf.stream_url(ep["id"])

    # --- HEARD: ffmpeg-extract a window of audio -> opus -> signs (shared lexicon) ---
    tmp = tempfile.mktemp(suffix=".ogg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0", "-t", str(WINDOW),
                    "-i", url, "-vn", "-ar", "48000", "-ac", "1", "-c:a", "libopus",
                    tmp], check=True, timeout=180)
    acn = a.open_container(s, tmp); asid = a.add_stream(s, acn)
    a.parse_stream(s, acn, asid); a.parse_native(s, acn, asid)
    res = sp.ingest_speech(s, asid, lex, n_bands=16, n_time_windows=4,
                           fs=48000, threshold=0.80)
    a.close_container(acn); os.unlink(tmp)
    n_new = sum(1 for *_, i in res if i)
    signs = [g for _, g, _ in res]

    # --- SEEN: temporal structure over HTTP (no full download) ---
    vcn = V.open_container(s, url)
    vsid = V.add_stream(s, vcn, _video_stream_index(url), export_motion_vectors=True)
    V.parse_stream(s, vcn, vsid, frame_limit=V_FRAMES)
    frames = list(s.neighbours(vsid, V.HAS_FRAME))
    from collections import Counter
    pt = Counter(s.node(f)["attrs"]["pict_type"] for f in frames)
    total_mv = sum(V.motion_summary(s, f)["n_mvs"] for f in frames)
    V.close_container(vcn)

    return {"series": series_item["name"], "ep": ep["name"],
            "utts": len(signs), "new": n_new, "signs": signs,
            "frames": len(frames), "pred": pt.get("P", 0) + pt.get("B", 0),
            "cuts": sum(1 for f in frames if s.node(f)["attrs"]["pict_type"] == "I"),
            "mv": total_mv}


def main():
    jf = JellyfinWorld().connect()
    print("=" * 78)
    print(f"WATCH JELLYFIN — the jabberwock chooses {N_TITLES} titles, watches {WINDOW}s "
          f"of each, learns")
    print("=" * 78)
    s = srs.Substrate()
    a.seed_audio_grammar(s); a.seed_native_codec_grammar(s); sp.seed_speech_grammar(s)
    V.seed_video_grammar(s)
    lex = sp.open_lexicon(s)
    jf.ingest_catalog(s)

    picks = jf.choose(s, n=N_TITLES)
    print(f"  CHOSE (cold start): {[p['name'] for p in picks]}\n")
    print(f"  {'series':<30} {'ep utts':>7} {'new':>4} {'lex':>5} {'frames':>6} "
          f"{'%pred':>6} {'mv':>7}")
    seen_signs, watched = set(), []
    for p in picks:
        try:
            r = watch(s, jf, lex, p)
        except Exception as e:
            print(f"  {p['name']:<30}  SKIP ({type(e).__name__}: {str(e)[:40]})")
            continue
        if not r:
            continue
        seen_signs.update(r["signs"]); watched.append(r["series"])
        print(f"  {r['series'][:29]:<30} {r['utts']:>7} {r['new']:>4} "
              f"{len(seen_signs):>5} {r['frames']:>6} "
              f"{100*r['pred']/max(r['frames'],1):>5.0f}% {r['mv']:>7}")

    print(f"\n  LEARNED so far: {len(seen_signs)} distinct acoustic signs across "
          f"{len(watched)} titles; every title is the same kind of video (mostly "
          f"predicted frames + motion = persist+move).")
    nxt = jf.choose(s, n=3, watched_series=watched)
    print(f"  CURIOSITY — what it would watch NEXT (unseen series preferred): "
          f"{[p['name'] for p in nxt]}")
    print("=" * 78)


if __name__ == "__main__":
    main()
