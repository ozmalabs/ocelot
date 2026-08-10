"""WATCH BINGO — the jabberwock consumes the nursery-rhyme VIDEO with audio and
video SYNCHRONOUSLY, on one clock.

This is a WORLD ADAPTER (mechanical external-I/O -> substrate, per CLAUDE.md). It
does NOT decide or reason — it translates two external streams into timed graph
nodes and hands them to the agent:

  • VIDEO — decoded by ffmpeg (the agent's own native h264 decoder is bit-exact on
    I-frames but does not yet do P/B + deblocking, so ffmpeg is the front end FOR
    NOW). Each frame -> a VideoFrame node carrying its presentation time + a small
    luma signature (a mechanical 16x9 thumbnail — the rawest visual token).
  • AUDIO — ingested by the existing native pipeline (opus -> ingest_speech ->
    AcousticSign chain). Utterance nodes already carry start_time_s / end_time_s.

Both go onto ONE timeline: every VideoFrame is linked (shows_during) to the
acoustic signs whose utterance overlaps its display interval. After this, the
agent is genuinely WATCHING — both modalities are in its graph, time-aligned, for
it to ground (recurring acoustic sign <-> recurring on-screen thing). The grounding
itself is the agent's job, not this adapter's.

The closing readout is a MEASUREMENT (emit, for the human): it surfaces the
cross-modal regularity that is now present for the agent to learn — the recurring
acoustic motif (the BINGO chorus) co-occurs with a recurring visual scene.

Run:  python -m scripts.watch_bingo
"""
from __future__ import annotations

import subprocess
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "runners/dsl/python")

import numpy as np                                                   # noqa: E402
import substrate_rs as srs                                           # noqa: E402
from substrate_rs import audio as a, speech as sp                    # noqa: E402
from substrate_rs import Production, NodePattern                      # noqa: E402

VIDEO = "/tmp/nursery/bingo_vid.mp4"
AUDIO = "/tmp/nursery/bingo.ogg"          # opus the native path decodes
FPS = 4                                    # sampling rate for watching (frames/s)
GW, GH = 16, 9                             # luma thumbnail grid (the visual token)


def decode_frames_ffmpeg(path: str, fps: int):
    """ffmpeg = the video front end FOR NOW. Returns (pts_s, luma_thumb) per frame."""
    w, h = GW * 8, GH * 8
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps},scale={w}:{h}",
           "-pix_fmt", "gray", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    # mechanical downsample to the GWxGH visual token
    thumbs = frames.reshape(len(frames), GH, 8, GW, 8).mean(axis=(2, 4))
    thumbs = thumbs.reshape(len(frames), GW * GH)
    pts = np.arange(len(frames)) / fps
    return pts, thumbs


def main() -> int:
    print("=" * 74)
    print("WATCHING BINGO — video (ffmpeg) + audio (native) on one clock")
    print("=" * 74)

    s = srs.Substrate()
    a.seed_audio_grammar(s)
    a.seed_native_codec_grammar(s)
    sp.seed_speech_grammar(s)
    # Declare the cross-modal vocabulary the adapter emits: a video frame is an
    # Image (already in Γ via the vision module); permit it to co-occur with an
    # AcousticSign (mirrors audio's Image-from_input->AudioBuffer STFT bridge).
    # This is vocabulary (Γ permission), not the binding — the agent does that.
    s.add_production(Production(
        src=NodePattern(type="Image", var="f"), edge_type="shows_during",
        tgt=NodePattern(type="AcousticSign", var="g"), where=None, weight=None,
        provenance="video:frame_shows_during_sign").to_dict())

    # ---- AUDIO: native ingest -> timed AcousticSign chain ----
    lex = sp.open_lexicon(s)
    cn = a.open_container(s, AUDIO)
    sn = a.add_stream(s, cn)
    a.parse_stream(s, cn, sn)
    a.parse_native(s, cn, sn)
    res = sp.ingest_speech(s, sn, lex, n_bands=16, n_time_windows=4,
                           fs=48000, threshold=0.80)
    a.close_container(cn)
    # (utterance_node, sign_node, is_new) -> attach the time from the utterance node
    signs = []
    for utt, sign, is_new in res:
        at = s.node(utt)["attrs"]
        signs.append((float(at["start_time_s"]), float(at["end_time_s"]), sign))
    signs.sort()
    print(f"  AUDIO: {len(signs)} timed acoustic signs "
          f"({len(set(g for *_, g in signs))} distinct), "
          f"{signs[0][0]:.1f}s .. {signs[-1][1]:.1f}s")

    # ---- VIDEO: ffmpeg front end -> timed VideoFrame nodes ----
    pts, thumbs = decode_frames_ffmpeg(VIDEO, FPS)
    print(f"  VIDEO: {len(pts)} frames @ {FPS}fps ({GW}x{GH} luma token), "
          f"{pts[0]:.1f}s .. {pts[-1]:.1f}s")

    frame_ids = []
    for i, t in enumerate(pts):
        fid = s.add_node("Image", {"pts_s": float(t), "frame_index": int(i),
                                   "modality": "video", "brightness": float(thumbs[i].mean())})
        frame_ids.append(fid)

    # ---- ONE TIMELINE: link each frame to the signs it is shown during ----
    dt = 1.0 / FPS
    links = 0
    si = 0
    for i, t in enumerate(pts):
        lo, hi = t, t + dt
        for (a0, a1, sign) in signs:
            if a1 < lo:
                continue
            if a0 >= hi:
                break
            s.add_edge(frame_ids[i], "shows_during", sign)
            links += 1
    print(f"  TIMELINE: {links} frame<->sign co-occurrence edges "
          f"(the agent now perceives both streams aligned)")

    # ================= READOUT (emit / measurement for the human) =================
    # The cross-modal regularity now available for the agent to GROUND: the
    # recurring acoustic motif (the chorus) co-occurs with a recurring visual scene.
    seq = [g for *_, g in signs]
    times = [a0 for a0, _, _ in signs]

    # most-recurring acoustic sign = the hammered unit; its occurrence times
    from collections import Counter
    top_sign, top_n = Counter(seq).most_common(1)[0]
    motif_times = [t for t, g in zip(times, seq) if g == top_sign]

    # visual recurrence: cosine self-similarity of frame thumbnails
    T = thumbs - thumbs.mean(1, keepdims=True)
    T /= (np.linalg.norm(T, axis=1, keepdims=True) + 1e-6)
    S = T @ T.T
    np.fill_diagonal(S, 0.0)

    def frame_at(t):
        return min(int(round(t * FPS)), len(pts) - 1)

    motif_frames = sorted({frame_at(t) for t in motif_times})
    # mean visual similarity AMONG chorus frames vs among random frames
    def mean_sim(idx):
        idx = [i for i in idx if 0 <= i < len(pts)]
        if len(idx) < 2:
            return float("nan")
        sub = S[np.ix_(idx, idx)]
        return float(sub[np.triu_indices(len(idx), 1)].mean())

    rng = np.random.default_rng(0)
    base = np.mean([mean_sim(list(rng.choice(len(pts), len(motif_frames),
                                             replace=False))) for _ in range(50)])
    chorus = mean_sim(motif_frames)

    print("\n  CROSS-MODAL STRUCTURE NOW IN THE GRAPH (for the agent to ground):")
    print(f"    most-recurring acoustic sign fires {top_n}x at "
          f"{len(motif_frames)} distinct frame-times")
    print(f"    visual self-similarity of those frames : {chorus:+.3f}")
    print(f"    vs random frame sets (same size)       : {base:+.3f}")
    verdict = ("RECURRING SCENE aligns with the recurring sound"
               if chorus > base + 0.02 else
               "no strong scene-recurrence at this sign (try the chorus n-gram)")
    print(f"    -> {verdict}")
    print("\n  The jabberwock is watching BINGO: both modalities, one clock, in its")
    print("  graph. Grounding (bind the recurring sign to the recurring scene) is")
    print("  the agent's next move, not this adapter's.")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
