"""CAN WE WATCH FASTER THAN REAL TIME, OR ARE WE COMPUTE-LIMITED?

The watcher pins the master clock to wall time (it WATCHES at 1x by design). This
asks the orthogonal question: with the clock UNPINNED, how many media-seconds can
the pipeline actually process per wall-second? factor > 1 == faster-than-real-time
is possible; the bottleneck (decode vs per-tick re-seek vs network) tells us what
caps it. Read NUMBERS, not booleans.

World adapter: drives the REAL cortex code (VideoCortex.process_chunk /
AudioCortex.process_chunk) in a tight loop with an explicit stream position and
NO wall sleep, over a fixed media span. Reports media-sec / wall-sec (= x
real-time) for:
  A. video, watcher pattern (per-window av.open+seek, 8 frames/0.5s), LOCAL file
  B. video, sequential full decode (open once, EVERY frame) — the decode ceiling
  C. video, watcher pattern on the JELLYFIN HEVC stream (adds network)
  D. audio, watcher pattern (ffmpeg -ss + ingest per 1s), LOCAL file

Run:  python -m scripts.measure_watch_throughput
"""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
import threading
import time

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
import substrate_rs as srs
from substrate_rs import audio as A, speech as SP, video as V
from substrate_rs import Production, NodePattern
from domains.auditory_cortex import install_auditory_cortex
from scripts.watch_jellyfin_cortex import (
    VideoCortex, AudioCortex, MasterClock,
    VIDEO_CHUNK_S, VIDEO_FRAMES_PER_TICK, AUDIO_CHUNK_S,
)

LOCAL = "recordings/doom_20k.mp4"   # h264 320x240 30fps, 666s (no network)
SPAN_S = 60.0                        # media span to process per measurement


def _fresh():
    s = srs.Substrate()
    A.seed_audio_grammar(s); A.seed_native_codec_grammar(s); SP.seed_speech_grammar(s)
    V.seed_video_grammar(s); install_auditory_cortex(s)
    for src, et, tgt, prov in [
        ("CortexStamp", "synchronous_with", "CortexStamp", "cx:stamp_sync"),
        ("Frame", "follows", "Frame", "cx:frame_follows"),
    ]:
        try:
            s.add_production(Production(
                src=NodePattern(type=src, var="a"), edge_type=et,
                tgt=NodePattern(type=tgt, var="b"), where=None, weight=None,
                provenance=prov).to_dict())
        except Exception:
            pass
    s.memory_bound(50_000, 256 * 1024 * 1024, 3)
    s.memory_disposable_capacity(8 * 1024 * 1024, 1024)
    return s


def drive_video(url, span_s, label):
    """Run the REAL VideoCortex.process_chunk back-to-back, clock unpinned."""
    s = _fresh()
    cortex = VideoCortex(s, MasterClock(), [url], threading.Lock())
    t0 = time.perf_counter()
    pos = 0.0; produced = 0; ticks = 0
    while pos < span_s:
        p, _ = cortex.process_chunk(pos)
        produced += p; ticks += 1; pos += VIDEO_CHUNK_S
    wall = time.perf_counter() - t0
    factor = span_s / wall if wall else 0.0
    print(f"  {label}")
    print(f"    {span_s:.0f}s media in {wall:.2f}s wall  ->  {factor:5.1f}x real-time   "
          f"({ticks} windows, {produced} frames minted, {produced/wall:.0f} fr/s)")
    return factor


def drive_video_sequential(url, span_s, label):
    """Decode EVERY frame sequentially (open once, no re-seek) — the raw decode
    ceiling, ignoring the cortex's 8-frame subsample + per-window re-open."""
    import av
    s = _fresh()
    t0 = time.perf_counter()
    frames = 0; media_t = 0.0
    container = av.open(url)
    vstream = container.streams.video[0]
    tb = (vstream.time_base.numerator / vstream.time_base.denominator
          if vstream.time_base else 0.0)
    for packet in container.demux(vstream):
        if packet.size == 0:
            continue
        for frame in packet.decode():
            ft = float(frame.pts) * tb if frame.pts is not None else 0.0
            media_t = max(media_t, ft)
            # mint the same structure the cortex does (Frame node)
            s.add_node("Frame", {"pict_type": str(frame.pict_type),
                                 "time_s": ft, "coded_size": int(packet.size)})
            frames += 1
        if media_t >= span_s:
            break
    container.close()
    wall = time.perf_counter() - t0
    factor = media_t / wall if wall else 0.0
    print(f"  {label}")
    print(f"    {media_t:.0f}s media ({frames} frames, EVERY frame) in {wall:.2f}s wall  "
          f"->  {factor:5.1f}x real-time   ({frames/wall:.0f} fr/s)")
    return factor


def drive_audio(url, span_s, label, fs=48000):
    """Run the REAL AudioCortex.process_chunk back-to-back, clock unpinned."""
    s = _fresh()
    lex = SP.open_lexicon(s)
    cortex = AudioCortex(s, MasterClock(), lex, [url], threading.Lock())
    t0 = time.perf_counter()
    pos = 0.0; produced = 0; ticks = 0
    while pos < span_s:
        p, _ = cortex.process_chunk(pos)
        produced += p; ticks += 1; pos += AUDIO_CHUNK_S
    wall = time.perf_counter() - t0
    factor = span_s / wall if wall else 0.0
    print(f"  {label}")
    print(f"    {span_s:.0f}s media in {wall:.2f}s wall  ->  {factor:5.1f}x real-time   "
          f"({ticks} chunks, {produced} utterances)")
    return factor


def main():
    print("=" * 78)
    print("WATCH THROUGHPUT — media-seconds processed per wall-second (clock unpinned)")
    print("=" * 78)

    if os.path.exists(LOCAL):
        print("\nVIDEO (local h264 320x240 30fps — pure compute, no network):")
        drive_video(LOCAL, SPAN_S, "A. watcher pattern (per-window open+seek, 8 frames/0.5s)")
        drive_video_sequential(LOCAL, SPAN_S, "B. sequential full decode (every frame) = decode ceiling")
        print("\nAUDIO (local, ffmpeg -ss + ingest per 1s):")
        drive_audio(LOCAL, SPAN_S, "D. watcher pattern (transcode+detect+cochlea+match)")
    else:
        print(f"  (local {LOCAL} not found)")

    # C. real-world: the Jellyfin HEVC stream (adds network + bigger frames)
    print("\nVIDEO (Jellyfin HEVC stream — adds network + real resolution):")
    try:
        from scripts.jellyfin_world import JellyfinWorld
        jf = JellyfinWorld().connect()
        s = _fresh(); jf.ingest_catalog(s)
        media = s.nodes("Media") or s.nodes("Movie") or s.nodes("Series")
        if media:
            item = media[0]
            iid = s.node(item)["attrs"].get("jellyfin_id") or s.node(item)["attrs"].get("id")
            url = jf.stream_url(iid)
            drive_video(url, SPAN_S, "C. watcher pattern on the live HEVC stream")
        else:
            print("  (no catalog items)")
    except Exception as e:               # noqa: BLE001 — world boundary
        print(f"  (jellyfin path skipped: {e})")

    print("\n" + "=" * 78)
    print("  factor > 1 => faster-than-real-time is possible (clock is the only")
    print("  thing holding it to 1x); the gap between A and B isolates per-window")
    print("  re-open cost; C vs A isolates network; D is the audio ceiling.")
    print("=" * 78)


if __name__ == "__main__":
    main()
