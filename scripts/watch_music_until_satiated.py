"""WATCH THE STORYBOTS MUSIC EPISODE UNTIL THE AGENT SATIATES — then report what
it learned.

Higher-resolution full vision (VISION_SIZE bumped) + full audio, re-watching the
episode order-N times. Each pass extracts what the last couldn't; the agent
SATIATES when new learning per pass -> 0 (the order-N curriculum convergence
gate). What it learns, in its OWN held machinery:
  * an ACOUSTIC lexicon — recurring sound patterns (the episode's musical hooks),
    acquired by acquire_sign, KEEP-tier, condensing/saturating.
  * a VISUAL lexicon — recurring shots/scenes, acquired by the SAME acquire_sign
    on visual EVENTS (scene changes), saturating too.
  * CROSS-MODAL bindings — what it heard bound to what it saw on the master clock.

World adapter: points the cortex pipeline at the music episode + drives re-watch
passes; every decision (acquire/keep/forget/bind) is the held substrate operator.

Run:  python -m scripts.watch_music_until_satiated [vision_size] [max_passes]
"""
from __future__ import annotations
import subprocess
import sys
import threading
import time

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
import scripts.watch_jellyfin_cortex as W       # configure BEFORE building cortexes
W.VISION = True
W.FAST_FORWARD = True
W.VISION_SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 160   # bumped up
MAX_PASSES = int(sys.argv[2]) if len(sys.argv) > 2 else 8

import substrate_rs as srs                                       # noqa: E402
from substrate_rs import audio as A, speech as SP, video as V, vision as VIS  # noqa: E402
from substrate_rs import Production, NodePattern                 # noqa: E402
from domains.auditory_cortex import install_auditory_cortex      # noqa: E402
from scripts.jellyfin_world import JellyfinWorld                 # noqa: E402

EP_ID = "f1970fc7ace065cb9ac2867ae084282b"   # Ask the StoryBots — How Do You Make Music?


def _duration(url):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", url], capture_output=True, text=True, timeout=60).stdout.strip()
        return float(out) if out else None
    except Exception:
        return None


def main():
    print("=" * 78)
    print(f"WATCH 'How Do You Make Music?' UNTIL SATIATED  (vision {W.VISION_SIZE}px,"
          f" full audio+video, re-watch)")
    print("=" * 78)

    s = srs.Substrate()
    A.seed_audio_grammar(s); A.seed_native_codec_grammar(s); SP.seed_speech_grammar(s)
    V.seed_video_grammar(s); VIS.seed_vision_grammar(s)
    install_auditory_cortex(s)
    for src, et, tgt, prov in [("CortexStamp", "synchronous_with", "CortexStamp", "x"),
                               ("Frame", "follows", "Frame", "y")]:
        try:
            s.add_production(Production(src=NodePattern(type=src, var="a"), edge_type=et,
                                       tgt=NodePattern(type=tgt, var="b"), where=None,
                                       weight=None, provenance=prov).to_dict())
        except Exception:
            pass
    s.memory_bound(12000, 256 * 1024 * 1024, 3)
    s.memory_disposable_capacity(24 * 1024 * 1024, 3072)

    aud_lex = SP.open_lexicon(s, name="audio")
    vis_lex = SP.open_lexicon(s, name="vision")

    jf = JellyfinWorld().connect()
    url = jf.stream_url(EP_ID)
    dur = _duration(url) or 600.0
    print(f"  episode duration {dur/60:.1f} min; re-watching until new signs/pass -> 0\n")

    master = W.MasterClock(fast_forward=True)
    url_box = [url]
    commit = threading.Lock()
    acx = W.AudioCortex(s, master, aud_lex, url_box, commit)
    vcx = W.VideoCortex(s, master, url_box, commit)
    vcx.vision_lex = vis_lex                       # give the eye a lexicon
    acx.start(); vcx.start()

    def nsigns(lex):
        return len(SP.lexicon_signs(s, lex))

    print(f"  {'pass':>4} {'wall':>5} {'media':>6} {'x':>5} "
          f"{'aud':>5} {'+a':>4} {'vis':>5} {'+v':>4} {'bind':>5} {'frames':>7}")
    prev_a = prev_v = 0
    flat = 0
    rows = []
    t_start = time.time()
    for p in range(1, MAX_PASSES + 1):
        master.start_title(0.0, duration_s=dur)
        acx.ff_done = vcx.ff_done = False
        p0 = time.time()
        # let the cortexes race through the whole episode (their own threads).
        while not (acx.ff_done and vcx.ff_done):
            if time.time() - p0 > 600:            # safety
                break
            time.sleep(0.1)
        wall = time.time() - p0
        with commit:
            nb = W.bind_synchronous(s)            # bind this pass's co-temporal stamps
            na, nv = nsigns(aud_lex), nsigns(vis_lex)
            s.memory_forget_type("CortexStamp")   # retire the spent anchors
        x = dur / wall if wall else 0.0
        rows.append((p, na, na - prev_a, nv, nv - prev_v, nb, vcx._scene_idx))
        print(f"  {p:>4} {int(time.time()-t_start):>5} {int(dur):>6} {x:>5.1f} "
              f"{na:>5} {na-prev_a:>4} {nv:>5} {nv-prev_v:>4} {nb:>5} {vcx._scene_idx:>7}")
        sat_a = (na - prev_a) <= max(1, int(0.02 * na))
        sat_v = (nv - prev_v) <= max(1, int(0.02 * nv))
        flat = flat + 1 if (sat_a and sat_v) else 0
        prev_a, prev_v = na, nv
        if flat >= 2:
            print(f"\n  SATIATED — new signs/pass -> 0 for 2 passes (pass {p}).")
            break
    else:
        print(f"\n  reached max {MAX_PASSES} passes.")

    acx.stop(); vcx.stop(); time.sleep(0.3)

    # ---- WHAT IT LEARNED ----
    print("\n" + "=" * 78)
    print("WHAT IT LEARNED")
    print("=" * 78)
    a_signs = SP.lexicon_signs(s, aud_lex)
    v_signs = SP.lexicon_signs(s, vis_lex)
    print(f"  ACOUSTIC lexicon : {len(a_signs)} recurring sound patterns (the hooks)")
    print(f"  VISUAL lexicon   : {len(v_signs)} recurring shots/scenes")
    print(f"  frames SEEN      : {vcx._scene_idx} (every frame @ {W.VISION_SIZE}px, V1)")
    print(f"  visual events    : {vcx._vis_events} presented -> {vcx._vis_new} distinct signs")

    def top(signs, k=6):
        d = [SP.sign_describe(s, sid) for sid in signs]
        return sorted(d, key=lambda x: -int(x.get("hearings", 0)))[:k]

    print("\n  most-RECURRING sounds (acoustic signs by times heard — the hammered hooks):")
    for d in top(a_signs):
        print(f"    {d['id']}  heard {d['hearings']}x  (feat_len {d['feature_length']})")
    print("\n  most-RECURRING scenes (visual signs by times seen — repeated shots):")
    for d in top(v_signs):
        print(f"    {d['id']}  seen {d['hearings']}x  (feat_len {d['feature_length']})")

    # saturation curve = the order-N convergence signature
    print("\n  SATURATION CURVE (new signs per pass -> 0 == the agent satiated):")
    print("    pass:   " + "  ".join(f"{r[0]:>4}" for r in rows))
    print("    +aud:   " + "  ".join(f"{r[2]:>4}" for r in rows))
    print("    +vis:   " + "  ".join(f"{r[4]:>4}" for r in rows))
    print("=" * 78)


if __name__ == "__main__":
    main()
