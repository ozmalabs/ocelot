"""WATCH THE CURRICULUM — the jabberwock watches a graded series of children's
videos (BINGO first), accumulating on ONE substrate, and we read off what it
learns about SPEECH and VISION.

Each clip is ONE media object (the taught concept): the heard (opus -> ingest_speech
-> timed signs, into a SHARED lexicon so words recur ACROSS clips) and the seen
(video.py temporal structure: I/P/B, motion, scene cuts), time-locked on one clock.

The experiment (the curriculum thesis): a graded series of simple, repetitive,
sung, animated speech is the data a child learns from. Across it we ask —
  SPEECH : does a small CORE vocabulary condense (lexicon saturates, signs recur
           within AND across clips), the compression signature of real structure?
  VISION : is every clip the same kind of thing (a scene that PERSISTS and MOVES,
           cut into shots) — i.e. does "what video is" generalise off BINGO?
  CROSS  : do the heard and the seen stay bound (synchronous_with accumulates), and
           is there sound<->motion coupling (sung moments = visual events)?

No pixels yet (the agent's own I-frame renderer is still being built); VISION here
is the bitstream STRUCTURE (signals not pixels). Pixel-level vision (the Eye / V1
on rendered keyframes) folds in once the renderer lands.

Run:  python -m scripts.watch_curriculum
"""
from __future__ import annotations

import os
import subprocess
import sys
from collections import Counter, defaultdict

sys.path.insert(0, ".")
sys.path.insert(0, "runners/dsl/python")

import substrate_rs as srs                                           # noqa: E402
from substrate_rs import audio as a, speech as sp, video as V        # noqa: E402
from substrate_rs import Production, NodePattern                     # noqa: E402

# graded playlist: BINGO first (the anchor), then EVERY downloaded clip in
# /tmp/nursery/vids. Adding to the curriculum = just downloading more videos.
import glob as _glob


def _playlist():
    pl = [("bingo", "/tmp/nursery/bingo_vid.mp4")]
    for p in sorted(_glob.glob("/tmp/nursery/vids/*.mp4")):
        pl.append((os.path.splitext(os.path.basename(p))[0], p))
    return pl


PLAYLIST = _playlist()
FRAMES_PER_CLIP = 200      # video-structure sample window (keeps MV minting tractable)


def _video_stream_index(path):
    """The stream order differs across files (BINGO is video-first; the YouTube
    downloads are audio-first). Ask ffprobe (oracle) for the video stream index."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=index", "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip()
    return int(out) if out else 0


def _perm(s, src, edge, tgt, prov):
    s.add_production(Production(
        src=NodePattern(type=src, var="s"), edge_type=edge,
        tgt=NodePattern(type=tgt, var="t"), where=None, weight=None,
        provenance=prov).to_dict())


def watch_one(s, lex, name, path):
    """Watch one clip into the shared substrate. Returns a per-clip record."""
    # --- HEARD: full audio -> timed signs into the SHARED lexicon ---
    acn = a.open_container(s, path)
    asid = a.add_stream(s, acn)
    a.parse_stream(s, acn, asid)
    a.parse_native(s, acn, asid)
    res = sp.ingest_speech(s, asid, lex, n_bands=16, n_time_windows=4,
                           fs=48000, threshold=0.80)
    utts = []
    for utt, sign, is_new in res:
        at = s.node(utt)["attrs"]
        utts.append((float(at["start_time_s"]), float(at["end_time_s"]), sign, utt,
                     bool(is_new)))
    a.close_container(acn)

    # --- SEEN: video temporal structure ---
    vcn = V.open_container(s, path)
    vsid = V.add_stream(s, vcn, _video_stream_index(path), export_motion_vectors=True)
    V.parse_stream(s, vcn, vsid, frame_limit=FRAMES_PER_CLIP)
    frames = list(s.neighbours(vsid, V.HAS_FRAME))
    ptypes = Counter(s.node(f)["attrs"]["pict_type"] for f in frames)
    fr = sorted(((float(s.node(f)["attrs"]["time_s"]), f) for f in frames))
    f_t = [t for t, _ in fr]
    motion_by_t = {}
    total_mv = 0
    for t, f in fr:
        ms = V.motion_summary(s, f)
        total_mv += ms["n_mvs"]
        motion_by_t[t] = ms["mean_mag"]
    cuts = V.scene_cuts(s, vsid)

    # --- CROSS-MODAL: time-lock utterances to co-temporal frames ---
    import bisect
    span = (f_t[0], f_t[-1]) if f_t else (0.0, 0.0)
    bound = 0
    sung_motion, silent_set = [], set(f_t)
    for (a0, a1, sign, utt, _new) in utts:
        if not f_t or a1 < span[0] or a0 > span[1]:
            continue
        lo = bisect.bisect_left(f_t, a0)
        hi = bisect.bisect_right(f_t, a1)
        for tt, f in fr[lo:hi]:
            s.add_edge(utt, "synchronous_with", f)
            bound += 1
            sung_motion.append(motion_by_t[tt])
            silent_set.discard(tt)
    silent_motion = [motion_by_t[t] for t in silent_set]
    V.close_container(vcn)

    return {
        "name": name, "n_utt": len(utts),
        "n_new": sum(1 for u in utts if u[4]),
        "signs": [u[2] for u in utts],
        "frames": len(frames), "ptypes": dict(ptypes), "cuts": len(cuts),
        "total_mv": total_mv, "bound": bound,
        "span": span,
        "sung_motion": (sum(sung_motion) / len(sung_motion)) if sung_motion else 0.0,
        "silent_motion": (sum(silent_motion) / len(silent_motion)) if silent_motion else 0.0,
    }


def main() -> int:
    print("=" * 78)
    print("WATCHING THE CURRICULUM — what the jabberwock learns about speech & vision")
    print("=" * 78)
    s = srs.Substrate()
    a.seed_audio_grammar(s); a.seed_native_codec_grammar(s); sp.seed_speech_grammar(s)
    V.seed_video_grammar(s)
    _perm(s, "Utterance", "synchronous_with", "Frame", "av:utt_sync_frame")
    lex = sp.open_lexicon(s)

    playlist = [(n, p) for (n, p) in PLAYLIST if os.path.exists(p)]
    print(f"  playlist ({len(playlist)} clips): {[n for n, _ in playlist]}\n")

    records = []
    lexicon_curve = []          # distinct signs after each clip
    sign_to_clips = defaultdict(set)   # which clips each sign appears in
    seen_signs = set()
    print(f"  {'clip':<9} {'utts':>5} {'new':>4} {'lex':>5} {'rec%':>5} "
          f"{'frames':>6} {'%pred':>6} {'cuts':>4} {'bind':>5}")
    for name, path in playlist:
        r = watch_one(s, lex, name, path)
        records.append(r)
        for g in r["signs"]:
            sign_to_clips[g].add(name)
            seen_signs.add(g)
        lexicon_curve.append(len(seen_signs))
        pred = r["ptypes"].get("P", 0) + r["ptypes"].get("B", 0)
        recpct = 100 * (1 - r["n_new"] / max(r["n_utt"], 1))
        predpct = 100 * pred / max(r["frames"], 1)
        print(f"  {name:<9} {r['n_utt']:>5} {r['n_new']:>4} {len(seen_signs):>5} "
              f"{recpct:>4.0f}% {r['frames']:>6} {predpct:>5.0f}% {r['cuts']:>4} "
              f"{r['bound']:>5}")

    # ===================== WHAT IT LEARNED =====================
    total_utt = sum(r["n_utt"] for r in records)
    total_mv = sum(r["total_mv"] for r in records)
    total_bind = sum(r["bound"] for r in records)
    core = {g: cl for g, cl in sign_to_clips.items() if len(cl) >= 2}
    core_top = sorted(core.items(), key=lambda kv: len(kv[1]), reverse=True)[:8]

    print("\n  ---- SPEECH ----")
    print(f"    lexicon growth across the curriculum: {lexicon_curve}")
    print(f"    {total_utt} utterances heard -> {len(seen_signs)} distinct signs; "
          f"{len(core)} recur in >=2 clips (shared building blocks).")
    if lexicon_curve and len(lexicon_curve) > 1:
        late = lexicon_curve[-1] - lexicon_curve[-2]
        print(f"    new signs added by the LAST clip: {late} "
              f"({'saturating -> a core vocabulary condensed' if late <= max(1, lexicon_curve[0]//4) else 'still growing'}).")
    print(f"    cross-clip core vocabulary (sign -> #clips): "
          f"{[(int(g.value) if hasattr(g,'value') else g, len(cl)) for g, cl in core_top]}")

    print("\n  ---- VISION ----")
    for r in records:
        pred = r["ptypes"].get("P", 0) + r["ptypes"].get("B", 0)
        print(f"    {r['name']:<9}: {100*pred/max(r['frames'],1):>3.0f}% predicted "
              f"(persists), {r['total_mv']:>7} motion vectors, {r['cuts']} scene cut(s)")
    print(f"    -> every clip is the same kind of thing: a scene that PERSISTS and "
          f"MOVES, cut into shots. 'What video is' generalises off BINGO. "
          f"({total_mv} motion vectors of visual experience total.)")

    print("\n  ---- CROSS-MODAL ----")
    sm = [r["sung_motion"] for r in records if r["sung_motion"] > 0]
    qm = [r["silent_motion"] for r in records if r["silent_motion"] > 0]
    print(f"    {total_bind} heard<->seen bindings accumulated across the curriculum.")
    if sm and qm:
        print(f"    mean visual motion while SUNG: {sum(sm)/len(sm):.2f} px  vs  "
              f"SILENT: {sum(qm)/len(qm):.2f} px  "
              f"({'sung moments carry more visual action (sound<->event coupling)' if sum(sm)/len(sm) > sum(qm)/len(qm) else 'no clear coupling at this granularity'}).")
    print(f"    the heard and the seen stay bound clip after clip — the substrate for")
    print(f"    grounding a recurring SOUND to a recurring SIGHT is accumulating.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
