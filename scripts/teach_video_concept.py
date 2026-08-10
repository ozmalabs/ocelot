"""TEACH THE CONCEPT OF A VIDEO — audio and video are ONE thing, not two streams.

Until now the substrate opened BINGO twice: an AudioContainer (sound) and a
VideoContainer (picture), as if they were unrelated. They are NOT. A video is ONE
event-stream perceived in TWO modalities that are time-locked and co-refer to the
SAME happenings: when the dog appears, the word "Bingo" is sung — one event, heard
and seen. That binding IS the concept; without it, grounding meaning is impossible
(you can only learn "the sound means the thing on screen" if sound and thing are
known to be the same event).

This builds BINGO as one MEDIA object from the SINGLE file (stream 0 = h264 video,
stream 1 = opus audio), and installs the structure that says they are linked:

  Media ──has_modality──▶ VideoStream   (the seen)
        ──has_modality──▶ AudioStream    (the heard)
  Utterance ──synchronous_with──▶ Frame  (time-locked: same moment of one event)
  Media ──is_a──▶ Concept{audiovisual_event}   (the principle the agent holds)

Both modalities live on ONE clock (Frame.time_s, Utterance.start_time_s). The
binding edges make "what was sung at t" and "what was on screen at t" reach each
other — the prerequisite for grounding a recurring SOUND to a recurring SIGHT.

This is world-structure / ontology (what a video IS), seeded like the audio and
video grammars. The agent does the grounding (bind recurring co-occurrences into
referents); this only makes the link EXIST so it can.

Run:  python -m scripts.teach_video_concept
"""
from __future__ import annotations

import sys
from collections import Counter

sys.path.insert(0, ".")
sys.path.insert(0, "runners/dsl/python")

import substrate_rs as srs                                           # noqa: E402
from substrate_rs import audio as a, speech as sp, video as V        # noqa: E402
from substrate_rs import Production, NodePattern                     # noqa: E402

BINGO = "/tmp/nursery/bingo_vid.mp4"          # ONE file, two modalities
N_VIDEO_FRAMES = 240


def _perm(s, src, edge, tgt, prov):
    s.add_production(Production(
        src=NodePattern(type=src, var="s"), edge_type=edge,
        tgt=NodePattern(type=tgt, var="t"), where=None, weight=None,
        provenance=prov).to_dict())


def main() -> int:
    print("=" * 74)
    print("TEACHING THE CONCEPT OF A VIDEO — the heard and the seen are ONE event")
    print("=" * 74)

    s = srs.Substrate()
    a.seed_audio_grammar(s)
    a.seed_native_codec_grammar(s)
    sp.seed_speech_grammar(s)
    V.seed_video_grammar(s)
    # the cross-modal vocabulary that makes a video ONE thing
    _perm(s, "Media", "has_modality", "VideoStream", "av:media_has_video")
    _perm(s, "Media", "has_modality", "AudioStream", "av:media_has_audio")
    _perm(s, "Utterance", "synchronous_with", "Frame", "av:utterance_sync_frame")
    _perm(s, "Media", "is_a", "Concept", "av:media_is_a_concept")

    # ---- THE PRINCIPLE, as a concept the agent holds ----
    concept = s.add_node("Concept", {
        "name": "audiovisual_event",
        "definition": "A video is one event-stream in two time-locked modalities; "
                      "the heard (audio) and the seen (video) co-refer to the same "
                      "happenings. Sound and sight at the same time are aspects of "
                      "ONE event, not unrelated streams.",
        "origin": "taught",
    })

    # ---- ONE media object, two modalities from the SAME file ----
    media = s.add_node("Media", {"name": "BINGO", "path": BINGO})
    s.add_edge(media, "is_a", concept)

    # VIDEO modality (structure — the seen): frames + motion, no pixels needed here
    vcn = V.open_container(s, BINGO)
    vsid = V.add_stream(s, vcn, 0, export_motion_vectors=True)
    V.parse_stream(s, vcn, vsid, frame_limit=N_VIDEO_FRAMES)
    s.add_edge(media, "has_modality", vsid)
    frames = list(s.neighbours(vsid, V.HAS_FRAME))

    # AUDIO modality (the heard): opus -> timed acoustic signs
    acn = a.open_container(s, BINGO)
    asid = a.add_stream(s, acn)             # picks the opus audio stream
    a.parse_stream(s, acn, asid)
    a.parse_native(s, acn, asid)
    lex = sp.open_lexicon(s)
    res = sp.ingest_speech(s, asid, lex, n_bands=16, n_time_windows=4,
                           fs=48000, threshold=0.80)
    s.add_edge(media, "has_modality", asid)

    # collect timed utterances (the heard events)
    utts = []   # (start, end, sign_node, utt_node)
    for utt, sign, _is_new in res:
        at = s.node(utt)["attrs"]
        utts.append((float(at["start_time_s"]), float(at["end_time_s"]), sign, utt))

    # frame lookup by time
    fr = sorted(((float(s.node(f)["attrs"]["time_s"]), f) for f in frames))
    f_t = [t for t, _ in fr]
    import bisect
    vid_span = (f_t[0], f_t[-1]) if f_t else (0, 0)

    # ---- BIND: time-lock each utterance to the frames it is heard OVER ----
    bound = 0
    for (a0, a1, sign, utt) in utts:
        if a1 < vid_span[0] or a0 > vid_span[1]:
            continue                          # outside the parsed video window
        lo = bisect.bisect_left(f_t, a0)
        hi = bisect.bisect_right(f_t, a1)
        for _, f in fr[lo:hi]:
            s.add_edge(utt, "synchronous_with", f)
            bound += 1

    print(f"\n  ONE media object 'BINGO' with TWO modalities on one clock:")
    print(f"    seen : VideoStream — {len(frames)} frames "
          f"({vid_span[0]:.1f}s..{vid_span[1]:.1f}s)")
    print(f"    heard: AudioStream — {len(utts)} timed utterances "
          f"({len(set(g for *_ , g, _ in utts))} distinct signs)")
    print(f"    LINKED: {bound} synchronous_with edges (heard-event time-locked to "
          f"seen-frame)")
    print(f"    concept installed: audiovisual_event (Media is_a -> it)")

    # ---- confirm the link is traversable BOTH ways (heard<->seen) ----
    utts_in = [(a0, a1, g, u) for (a0, a1, g, u) in utts
               if vid_span[0] <= a0 <= vid_span[1]]
    if utts_in:
        a0, a1, g, u = utts_in[len(utts_in) // 2]
        seen = list(s.neighbours(u, "synchronous_with"))
        print(f"\n  the link is real (a sample moment, both directions):")
        print(f"    HEARD a sign at t={a0:.1f}s  -->  SEEN frames "
              f"{[s.node(x)['attrs']['frame_index'] for x in seen]} at the same moment")
        if seen:
            anyf = seen[0]
            back = [x for x in s.in_neighbours(anyf, "synchronous_with")]
            print(f"    and from that SEEN frame back to the HEARD utterances: "
                  f"{len(back)} (the heard and the seen reach each other)")

    print(f"\n  The agent no longer has two unrelated streams — it has ONE video: a")
    print(f"  thing it both hears and sees, time-locked, co-referring to the same")
    print(f"  events. Grounding (recurring SOUND <-> recurring SIGHT = a referent)")
    print(f"  is now possible — that is the agent's next move.")
    V.close_container(vcn)
    a.close_container(acn)
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
