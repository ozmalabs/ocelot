"""THROW IT ALL IN. Point the agent at the WHOLE library and let it rip — full
audio + full video, fast-forward, autonomous curiosity choice, one acoustic + one
visual lexicon persisting ACROSS every show — then dump whatever emerged.

No curriculum, no layer climbing. The open question: does the lexicon SATURATE
across the whole library? If new-signs-per-title trends toward 0, the agent has
found a FINITE shared vocabulary of sounds + scenes across all the content (and a
sign learned on one show recurs in the next). That's the thing to watch for.

World adapter: drives the held cortex pipeline over jf.choose picks; every
acquire/keep/forget/bind is the substrate's own operator.

Run:  python -m scripts.watch_everything [wall_seconds] [vision_size]
"""
from __future__ import annotations
import subprocess
import sys
import threading
import time

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
import scripts.watch_jellyfin_cortex as W
W.VISION = True
W.FAST_FORWARD = True
RUN_SECONDS = int(sys.argv[1]) if len(sys.argv) > 1 else 240
W.VISION_SIZE = int(sys.argv[2]) if len(sys.argv) > 2 else 96     # breadth over a few shows

import substrate_rs as srs                                        # noqa: E402
from substrate_rs import audio as A, speech as SP, video as V, vision as VIS  # noqa: E402
from substrate_rs import Production, NodePattern                  # noqa: E402
from domains.auditory_cortex import install_auditory_cortex       # noqa: E402
from scripts.jellyfin_world import JellyfinWorld                  # noqa: E402


def _duration(url):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", url], capture_output=True, text=True, timeout=60).stdout.strip()
        return float(out) if out else None
    except Exception:
        return None


def main():
    print("=" * 80)
    print(f"THROW IT ALL IN — whole library, full A/V, fast-forward, {W.VISION_SIZE}px vision")
    print("=" * 80)

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
    s.memory_bound(16000, 384 * 1024 * 1024, 3)
    s.memory_disposable_capacity(24 * 1024 * 1024, 3072)

    aud_lex = SP.open_lexicon(s, name="audio")
    vis_lex = SP.open_lexicon(s, name="vision")
    jf = JellyfinWorld().connect(); jf.ingest_catalog(s)

    master = W.MasterClock(fast_forward=True)
    url_box = [None]
    commit = threading.Lock()
    acx = W.AudioCortex(s, master, aud_lex, url_box, commit)
    vcx = W.VideoCortex(s, master, url_box, commit)
    vcx.vision_lex = vis_lex
    acx.start(); vcx.start()

    def nsigns(lex):
        return len(SP.lexicon_signs(s, lex))

    print(f"  {'#':>2} {'title':<30} {'min':>5} {'x':>5} "
          f"{'aud':>5} {'+a':>4} {'vis':>5} {'+v':>4} {'bind':>6} {'nodes':>6} {'MB':>5}")
    watched = []
    snaps = []
    media_total = 0.0
    prev_a = prev_v = 0
    bind_total = 0
    t0 = time.time()
    def robust(fn, *a, tries=4, **k):
        for i in range(tries):
            try:
                return fn(*a, **k)
            except Exception:
                time.sleep(2 * (i + 1))     # transient Jellyfin hiccup -> back off
        return None

    while time.time() - t0 < RUN_SECONDS:
        picks = robust(jf.choose, s, n=1, watched_series=watched)
        if not picks:
            if time.time() - t0 < RUN_SECONDS - 20:
                continue                    # network blip — keep trying
            break
        title = picks[0]
        eps = robust(jf.episodes, title["id"], limit=1)
        if not eps:
            watched.append(title["name"]); continue
        url = robust(jf.stream_url, eps[0]["id"])
        if not url:
            watched.append(title["name"]); continue
        dur = float(eps[0].get("runtime_s") or 0.0) or _duration(url) or 600.0
        url_box[0] = url
        master.start_title(0.0, duration_s=dur)
        acx.ff_done = vcx.ff_done = False
        p0 = time.time()
        while not (acx.ff_done and vcx.ff_done):
            if time.time() - t0 > RUN_SECONDS or time.time() - p0 > 300:
                break
            time.sleep(0.1)
        consumed = master.position() or 0.0
        media_total += consumed
        with commit:
            nb = W.bind_synchronous(s); bind_total += nb
            na, nv = nsigns(aud_lex), nsigns(vis_lex)
            n_nodes = s.node_count(); mb = s.memory_total_bytes() / 1024 / 1024
            s.memory_forget_type("CortexStamp")
        watched.append(title["name"])
        snaps.append((title["name"], consumed, na, na - prev_a, nv, nv - prev_v, nb))
        x = consumed / (time.time() - p0) if time.time() - p0 else 0.0
        print(f"  {len(watched):>2} {title['name'][:30]:<30} {consumed/60:>5.1f} {x:>5.1f} "
              f"{na:>5} {na-prev_a:>4} {nv:>5} {nv-prev_v:>4} {nb:>6} {n_nodes:>6} {mb:>5.0f}")
        prev_a, prev_v = na, nv
        url_box[0] = None

    acx.stop(); vcx.stop(); time.sleep(0.3)

    # ---- WHAT EMERGED ----
    a_signs = SP.lexicon_signs(s, aud_lex)
    v_signs = SP.lexicon_signs(s, vis_lex)
    print("\n" + "=" * 80)
    print("WHAT EMERGED")
    print("=" * 80)
    print(f"  watched          : {len(watched)} titles, {media_total/60:.1f} min of "
          f"programming in {time.time()-t0:.0f}s wall ({media_total/(time.time()-t0):.1f}x)")
    print(f"  ACOUSTIC lexicon : {len(a_signs)} signs   VISUAL lexicon : {len(v_signs)} signs")
    print(f"  cross-modal binds: {bind_total}   frames seen: {vcx._scene_idx}   "
          f"visual events: {vcx._vis_events}")

    # The key signal: does the per-title NEW-sign count fall as more shows go in?
    print("\n  LIBRARY SATURATION (new signs as each show is added — does it converge?):")
    print("    show#:  " + " ".join(f"{i+1:>4}" for i in range(len(snaps))))
    print("    +aud :  " + " ".join(f"{r[3]:>4}" for r in snaps))
    print("    +vis :  " + " ".join(f"{r[5]:>4}" for r in snaps))
    if len(snaps) >= 3:
        first = snaps[0][3] + snaps[0][5]
        last = snaps[-1][3] + snaps[-1][5]
        verdict = ("CONVERGING — shared vocabulary across the library"
                   if last < 0.5 * max(first, 1) else "still growing — diverse content")
        print(f"    -> {verdict} (first show +{first} new, last +{last})")

    def top(signs, k=8):
        d = [SP.sign_describe(s, sid) for sid in signs]
        return sorted(d, key=lambda x: -int(x.get("hearings", 0)))[:k]

    print("\n  most-UNIVERSAL sounds (heard most across the whole library):")
    for d in top(a_signs):
        print(f"    {d['id']}  heard {d['hearings']}x")
    print("\n  most-UNIVERSAL scenes (seen most across the whole library):")
    for d in top(v_signs):
        print(f"    {d['id']}  seen {d['hearings']}x")

    # node census — what structure is resident
    cen = {}
    for nid in s.nodes():
        t = s.node(nid)["type"]; cen[t] = cen.get(t, 0) + 1
    print("\n  resident structure (top node types):")
    for t, c in sorted(cen.items(), key=lambda x: -x[1])[:12]:
        print(f"    {t:<20} {c}")
    print("=" * 80)


if __name__ == "__main__":
    main()
