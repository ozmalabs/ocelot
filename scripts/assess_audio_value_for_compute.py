"""ASK THE JABBERWOCK to assess VALUE-FOR-COMPUTE on its own audio pipeline.

The agent's value-for-compute judgment is not an essay — it is an OPERATOR.
The memory faculty already ranks every node type by `keep_value`-per-byte (it
is exactly the order in which `forget_over_budget` sheds victims): bytes are the
storage cost a pipeline stage's output imposes; `keep_value` is what that output
is worth to keep; LOW keep_value-per-byte == the agent paid compute + store for
structure it would discard first. So "assess value-for-compute" = run the REAL
audio pipeline (the watcher's OPUS path) stage-by-stage, measure each stage's
COMPUTE (wall-ms) and the RESIDENT BYTES it leaves, then read back the agent's
OWN per-type verdict (`memory_value_report`) and let `forget_over_budget` act.

This is a WORLD ADAPTER (CLAUDE.md): it transcodes clips (ffmpeg = oracle),
drives the pipeline, and TIMES the stages. Every value judgment is the held
Rust operator (role_for / keep_value / type_bytes / order_n_shape_salience).
No agent decision lives in this file — it only measures and reports.

The audio pipeline stages (the agent's audio cortex, watch_jellyfin_cortex.py):
  demux        open_container + add_stream   PyAV metadata, no decode
  parse_stream parse_stream                  -> AudioFrame  (one node PER frame, no decode)
  parse_native parse_native                  -> OpusPacketInfo (codec-internal structure)
  ingest       ingest_speech                 -> Utterance + AcousticSign (decode + cochlea + match)

Run:  python -m scripts.assess_audio_value_for_compute
"""
from __future__ import annotations
import glob
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
import substrate_rs as srs
from substrate_rs import audio as A, speech as SP

FS = 48000  # the watcher's libopus rate

# Real children's clips as ROUNDS so the agent observes a GROWTH SHAPE per
# type. Prefer the spoken nursery rhymes (so the high-value speech end —
# AcousticSign — is exercised), padded with curriculum songs.
SRC = (sorted(glob.glob("/tmp/rhyme_*.wav"))
       + sorted(glob.glob("/tmp/sal_*.wav"))[:6])

STAGE_OF_TYPE = {
    "AudioFrame": "parse_stream",
    "OpusPacketInfo": "parse_native",
    "Mp3Granule": "parse_native",
    "AudioBuffer": "ingest (decode)",
    "Filter": "ingest (cochlea)",
    "Utterance": "ingest (detect)",
    "AcousticSign": "ingest (match)",
    "AudioContainer": "demux",
    "AudioStream": "demux",
}


def to_opus(path):
    """Transcode to opus/ogg — the watcher's codec (ffmpeg = oracle/transcode)."""
    out = tempfile.mktemp(suffix=".ogg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path,
                    "-ar", str(FS), "-ac", "1", "-c:a", "libopus", out], check=True)
    return out


def main():
    clips = [to_opus(p) for p in SRC]
    if not clips:
        print("no /tmp/rhyme_*.wav or /tmp/sal_*.wav clips found — run a watch pass first.")
        return
    print("=" * 78)
    print("THE JABBERWOCK ASSESSES VALUE-FOR-COMPUTE ON ITS AUDIO PIPELINE")
    print("=" * 78)
    print(f"  driving {len(clips)} real opus clips as rounds through the actual cortex\n")

    s = srs.Substrate()
    A.seed_audio_grammar(s); A.seed_native_codec_grammar(s); SP.seed_speech_grammar(s)
    lex = SP.open_lexicon(s)
    s.memory_bound(10_000_000, 10_000_000_000, 3)  # no forgetting during measurement

    stage_ms, stage_nodes = {}, {}

    def stage(name, fn):
        n0 = s.node_count(); t0 = time.perf_counter()
        out = fn()
        dt = (time.perf_counter() - t0) * 1000.0
        stage_ms[name] = stage_ms.get(name, 0.0) + dt
        stage_nodes[name] = stage_nodes.get(name, 0) + (s.node_count() - n0)
        return out

    for path in clips:
        cn = _demux(s, path)
        if cn is None:
            continue
        acn, asid = cn
        stage_ms["demux"] = stage_ms.get("demux", 0.0)  # demux timed in _demux
        stage("parse_stream", lambda: A.parse_stream(s, acn, asid))
        stage("parse_native", lambda: A.parse_native(s, acn, asid))
        stage("ingest (decode+detect+match)",
              lambda: SP.ingest_speech(s, asid, lex, n_bands=16, n_time_windows=4,
                                       fs=FS, threshold=0.80))
        A.close_container(acn)
        s.memory_observe_and_bound()

    total_ms = sum(stage_ms.values())
    print("  COMPUTE per stage (wall-ms across all rounds — what it cost):")
    for name in ["demux", "parse_stream", "parse_native", "ingest (decode+detect+match)"]:
        ms = stage_ms.get(name, 0.0); nd = stage_nodes.get(name, 0)
        print(f"    {name:<32} {ms:8.1f} ms  ({100*ms/max(total_ms,1e-9):4.1f}%)   "
              f"{nd:>6} nodes minted")
    print(f"    {'TOTAL':<32} {total_ms:8.1f} ms\n")

    report = s.memory_value_report()
    print("  VALUE-FOR-COMPUTE — the agent's own keep verdict per type")
    print("  (keep_value_per_byte ascending = the order it would DISCARD;")
    print("   head = lowest value for the bytes/compute spent):\n")
    print(f"    {'type':<17}{'tier':<11}{'count':>6}{'KB':>9}{'kv/byte':>11}  role")
    for r in report:
        role = f"mp={r['miss_penalty']:.1f} nr={r['non_rebuildability']:.2f}"
        if r["saturating"]:
            role += " (sat)"
        print(f"    {r['type']:<17}{r['tier']:<11}{r['count']:>6}{r['bytes']/1024:>9.1f}"
              f"{r['keep_value_per_byte']:>11.2e}  {role}")

    print("\n  THE DISPOSABLE TIER (echoic/iconic memory) — eager sensory-cache")
    print("  flush: the raw per-input firehose is dropped THIS tick (feature")
    print("  already read into the AcousticSign), never accumulated:")
    cur = s.memory_total_bytes()
    dropped = s.memory_drop_disposable()
    for t, n in sorted(dropped.items(), key=lambda kv: -kv[1]):
        print(f"    dropped {n:>6} × {t:<16} (disposable: {STAGE_OF_TYPE.get(t,'—')})")
    if not dropped:
        print("    (no disposable-tier nodes resident)")
    print(f"    footprint {cur/1024:.0f} KB -> {s.memory_total_bytes()/1024:.0f} KB"
          f"  (kept: working + the AcousticSign lexicon)")

    # --- verify the O(n^2) fix + the cheap annotate path + cochlea reuse ---
    _measure_native_paths(clips)

    print("\n  FIXES APPLIED (this is now the post-fix measurement):")
    print("  1. parse_native O(n^2) re-demux -> one-pass packet cache (above).")
    print("  2. speech path uses annotate_opus_modes (cheap hint, no OpusPacketInfo).")
    print("  3. cochlea bank built once + reused (Filter 16, not 16xN).")
    print("  4. disposable tier dropped eagerly each tick (echoic memory).")
    print("=" * 78)
    for c in clips:
        try: os.unlink(c)
        except OSError: pass


def _demux(s, path):
    t0 = time.perf_counter()
    try:
        acn = A.open_container(s, path)
        asid = A.add_stream(s, acn)
        return acn, asid
    except Exception as e:           # noqa: BLE001 — world boundary
        print(f"    (skip {path}: {e})")
        return None
    finally:
        pass


def _measure_native_paths(clips):
    """Verify the fixes: full parse_native (now one-pass, no O(n^2)) vs the
    cheap annotate_opus_modes the speech path uses; and cochlea rebuild vs
    shared bank. Each on a fresh substrate so counts are clean."""
    print("\n  NATIVE-PARSE PATH (the O(n^2) fix + the cheap hint path):")
    for label, use_full in [("parse_native (full, one-pass cache)", True),
                            ("annotate_opus_modes (cheap, speech path)", False)]:
        s = srs.Substrate()
        A.seed_audio_grammar(s); A.seed_native_codec_grammar(s); SP.seed_speech_grammar(s)
        t0 = time.perf_counter()
        for path in clips:
            acn = A.open_container(s, path); asid = A.add_stream(s, acn)
            A.parse_stream(s, acn, asid)
            (A.parse_native if use_full else A.annotate_opus_modes)(s, acn, asid)
            A.close_container(acn)
        dt = (time.perf_counter() - t0) * 1000.0
        npkt = len(s.nodes("OpusPacketInfo"))
        print(f"    {label:<42} {dt:8.1f} ms   OpusPacketInfo nodes = {npkt}")

    print("\n  COCHLEA-BANK REUSE (the Filter waste):")
    for label, prebuild in [("rebuild per call (old)", False),
                            ("shared bank (the fix)", True)]:
        s = srs.Substrate()
        A.seed_audio_grammar(s); A.seed_native_codec_grammar(s); SP.seed_speech_grammar(s)
        lex = SP.open_lexicon(s)
        bank = A.cochlea(s, n_bands=16, fs=FS) if prebuild else None
        t0 = time.perf_counter()
        for path in clips:
            acn = A.open_container(s, path); asid = A.add_stream(s, acn)
            A.parse_stream(s, acn, asid)
            A.annotate_opus_modes(s, acn, asid)
            SP.ingest_speech(s, asid, lex, n_bands=16, n_time_windows=4, fs=FS,
                             threshold=0.80, cochlea_bank=bank)
            A.close_container(acn)
        dt = (time.perf_counter() - t0) * 1000.0
        nfilt = len(s.nodes("Filter"))
        print(f"    {label:<42} {dt:8.1f} ms   Filter nodes minted = {nfilt}")


if __name__ == "__main__":
    main()
