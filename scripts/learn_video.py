"""LEARN WHAT VIDEO IS — the jabberwock reads BINGO as TEMPORAL STRUCTURE.

The mistake watch_bingo.py made: it decoded the video to pixels and handed the
agent 663 INDEPENDENT STILLS at timestamps. That is not what video is — it
destroys the very thing that makes a video a video. (substrate_rs.video says it
outright: "Decoding to pixels DESTROYS this structure.")

What video IS: a scene that PERSISTS and MOVES through time. The encoder already
found this — it is written in the bitstream as I/P/B frame types, per-macroblock
MOTION VECTORS, skip blocks, and coding cost. So the agent does NOT decode pixels;
it reads the STRUCTURE the encoder wrote — "signals, not pixels", the MT/V5
analogue of reading motion from V1.

The unification with the agent's audio work: a motion vector is the result of
BLOCK-MATCHING — find where this patch went in the previous frame. That is exactly
the MATCHED FILTER the agent authored for audio (XCorrPeak: correlate against a
known template to find where it went), now in 2-D over TIME. The video bitstream is
pre-computed temporal matched-filtering. Cross-speaker = voiced<->whispered =
loud<->soft = speech<->text = frame<->next-frame: ONE invariance — structure
persisting across a serialization (here the serialization axis is TIME).

This probe reads BINGO's real structure and surfaces the layers of what video is,
mirroring the nursery-rhyme AUDIO curriculum (persistence -> motion -> prediction).
It is a world adapter (read external structure into graph) + a readout (emit); the
agent's queries (scene_cuts / motion_summary / busiest_frames) do the work.

Run:  python -m scripts.learn_video
"""
from __future__ import annotations

import statistics as st
import sys
from collections import Counter

sys.path.insert(0, ".")
sys.path.insert(0, "runners/dsl/python")

import substrate_rs as srs                                           # noqa: E402
from substrate_rs import video as V                                  # noqa: E402

VIDEO = "/tmp/nursery/bingo_vid.mp4"
N_FRAMES = 240          # ~10s — enough to span several scene cuts + lots of motion


def main() -> int:
    print("=" * 74)
    print("LEARNING WHAT VIDEO IS — the jabberwock reads BINGO's temporal structure")
    print("=" * 74)

    s = srs.Substrate()
    V.seed_video_grammar(s)
    cn = V.open_container(s, VIDEO)
    sid = V.add_stream(s, cn, 0, export_motion_vectors=True)
    n = V.parse_stream(s, cn, sid, frame_limit=N_FRAMES)
    frames = list(s.neighbours(sid, V.HAS_FRAME))
    attr = lambda f: s.node(f)["attrs"]

    # ---- LAYER 0 — what video is NOT (independent stills) ----
    ptypes = Counter(attr(f)["pict_type"] for f in frames)
    n_pred = ptypes["P"] + ptypes["B"]
    print(f"\n  Read {n} frames as STRUCTURE (no pixels decoded).")
    print(f"  LAYER 0 — video is NOT independent stills:")
    print(f"    if it were, every frame would be a from-scratch I-frame. Instead")
    print(f"    {ptypes['I']}/{n} are I; {n_pred}/{n} are PREDICTED from neighbours "
          f"(P={ptypes['P']}, B={ptypes['B']}).")
    print(f"    -> {100*n_pred/n:.0f}% of the video is the encoder saying 'same scene "
          f"as next door, with changes'.")

    # ---- LAYER 1 — PERSISTENCE (the scene continues; you predict it) ----
    I_sz = [attr(f)["coded_size"] for f in frames if attr(f)["pict_type"] == "I"]
    P_sz = [attr(f)["coded_size"] for f in frames if attr(f)["pict_type"] == "P"]
    B_sz = [attr(f)["coded_size"] for f in frames if attr(f)["pict_type"] == "B"]
    print(f"\n  LAYER 1 — PERSISTENCE (coded_size = how much is NEW / unpredictable):")
    for lbl, v in (("I", I_sz), ("P", P_sz), ("B", B_sz)):
        if v:
            print(f"    {lbl}: mean {int(st.mean(v)):>6} bytes/frame  (n={len(v)})")
    print(f"    -> predicted frames cost a fraction of a fresh frame: the scene")
    print(f"       PERSISTS, the agent need only carry what CHANGED.")

    # ---- LAYER 2 — MOTION (the encoder's block-matching = matched filter) ----
    total_mv = 0
    per_frame_motion = []   # (frame_index, mean_mag, fraction_nonzero, n)
    for f in frames:
        ms = V.motion_summary(s, f)
        total_mv += ms["n_mvs"]
        if ms["n_mvs"]:
            per_frame_motion.append((attr(f)["frame_index"], ms["mean_mag"],
                                     ms["fraction_nonzero"], ms["n_mvs"]))
    moved = [m for _, m, _, _ in per_frame_motion]
    print(f"\n  LAYER 2 — MOTION ({total_mv} motion vectors = the encoder's "
          f"block-matching):")
    print(f"    a motion vector says 'this patch came from THERE in a neighbour "
          f"frame' —")
    print(f"    that IS the matched filter the agent built for audio (XCorrPeak), "
          f"in 2-D over time.")
    if moved:
        print(f"    mean motion magnitude across frames: {st.mean(moved):.2f} px "
              f"(min {min(moved):.2f}, max {max(moved):.2f})")
        busiest = sorted(per_frame_motion, key=lambda r: r[1], reverse=True)[:3]
        print(f"    busiest frames (most motion): "
              f"{[(fi, round(m,1)) for fi, m, _, _ in busiest]}")
    print(f"    -> where the motion field is coherent + large = something MOVED "
          f"(an event); where it's ~0 = the background holds still.")

    # ---- LAYER 3 — SCENE STRUCTURE (where prediction breaks = a cut) ----
    cuts = V.scene_cuts(s, sid)
    cut_times = sorted(attr(c)["time_s"] for c in cuts)
    busy = V.busiest_frames(s, sid, top_k=3)
    print(f"\n  LAYER 3 — SCENE STRUCTURE (I-frames = 'cannot predict' = a cut):")
    print(f"    {len(cuts)} scene cut(s) in this window at t="
          f"{[round(t,1) for t in cut_times]}s")
    print(f"    most NEW content (largest coded_size): frames "
          f"{[attr(b)['frame_index'] for b in busy]}")

    print(f"\n  WHAT THE AGENT NOW KNOWS VIDEO IS: not {n} pictures — ONE scene that")
    print(f"  PERSISTS (predict it) and MOVES (the motion field), cut into shots at")
    print(f"  I-frames. The 'recurring on-screen thing' to ground is a persisting,")
    print(f"  coherently-moving STRUCTURE across frames — not a still. Next: bind the")
    print(f"  recurring acoustic sign to a persisting motion/appearance object.")
    V.close_container(cn)
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
