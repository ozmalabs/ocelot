"""WATCH the StoryBots MUSIC episode ("Ask the StoryBots S3E1 — How Do You Make
Music?") through the full pipeline: find its salient musical SHAPES (order-N
salience / the pitch+rhythm build front-end), ingest its recurring lexicon, and wire
the episode's salient builds into the shape graph — do the episode's musical builds
LINK (by shape) to the known tada + Grieg anchors? An episode ABOUT music is the
densest test of the salient-shape machinery.

World adapter (Jellyfin stream + ffmpeg + held ops). Run: python -m scripts.watch_music_episode
"""
from __future__ import annotations
import os, subprocess, sys, tempfile
sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
import substrate_rs as srs
from substrate_rs import audio as a, speech as sp
from scripts.jellyfin_world import JellyfinWorld
from scripts.pitch_rhythm_frontend import pitch_rhythm_signature

EP_ID = "f1970fc7ace065cb9ac2867ae084282b"   # How Do You Make Music?
MINUTES = 10
WIN = 45


def main():
    jf = JellyfinWorld().connect()
    url = jf.stream_url(EP_ID)
    print("=" * 76)
    print("WATCHING: Ask the StoryBots — How Do You Make Music?")
    print("=" * 76)
    # full audio of the first MINUTES minutes
    full = tempfile.mktemp(suffix=".ogg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-t", str(MINUTES*60), "-i", url,
                    "-vn", "-ar", "48000", "-ac", "1", "-c:a", "libopus", full], check=True)

    # --- recurring LEXICON (what recurs across the episode) ---
    s = srs.Substrate(); a.seed_audio_grammar(s); a.seed_native_codec_grammar(s); sp.seed_speech_grammar(s)
    lex = sp.open_lexicon(s)
    cn = a.open_container(s, full); sn = a.add_stream(s, cn)
    a.parse_stream(s, cn, sn); a.parse_native(s, cn, sn)
    res = sp.ingest_speech(s, sn, lex, n_bands=16, n_time_windows=4, fs=48000, threshold=0.80)
    a.close_container(cn)
    import collections
    seq = [g for _, g, _ in res]
    top = collections.Counter(seq).most_common(5)
    print(f"\n  HEARD: {len(res)} utterances -> {len(set(seq))} distinct signs; "
          f"top-5 recur {[c for _,c in top]}x (the hooks the episode hammers)")

    # --- salient musical SHAPES across the episode (windowed build scan) ---
    wav = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", full, "-ar", "16000", "-ac", "1", wav], check=True)
    import wave, numpy as np
    w = wave.open(wav); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)/32768.0
    print(f"\n  SCANNING {MINUTES} min for salient musical builds ({WIN}s windows)...")
    moments = []
    for t0 in range(0, MINUTES*60 - WIN, WIN):
        seg = x[t0*sr:(t0+WIN)*sr]
        tmp = tempfile.mktemp(suffix=".wav")
        with wave.open(tmp, "w") as o:
            o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
            o.writeframes((seg*32768).astype(np.int16).tobytes())
        sig = pitch_rhythm_signature(tmp); os.unlink(tmp)
        if "rhythm_sig" in sig:
            moments.append((t0, sig.get("salience", 0.0), sig["rhythm_sig"]))
    moments.sort(key=lambda m: m[1], reverse=True)
    print(f"  found salient builds in {len(moments)} windows; top by order-N salience:")
    for t0, sal, rsig in moments[:5]:
        print(f"    @ {t0//60}:{t0%60:02d}  salience={sal:.2f}  rhythm_sig={rsig}")

    # --- do the episode's salient builds LINK to the tada + Grieg anchors? ---
    s.declare_shares_shape()
    anchors = {}
    for name, src in [("storybots_tada", "/tmp/storybots.ogg"), ("grieg_mtnking", "/tmp/mtnking.wav")]:
        if os.path.exists(src):
            asig = pitch_rhythm_signature(src)
            if "rhythm_sig" in asig:
                nid, _ = s.add_salient_shape(name, asig["rhythm_sig"]); anchors[name] = nid
    print(f"\n  do the episode's salient builds link (by shape) to the anchors {list(anchors)}?")
    linked = collections.Counter()
    for t0, sal, rsig in moments:
        nid, links = s.add_salient_shape(f"music@{t0}", rsig)
        for x_, _d in links:
            lab = s.node(x_)["attrs"].get("label", "?")
            if lab in anchors: linked[lab] += 1
    for name in anchors:
        print(f"    episode builds linking to {name}: {linked[name]} of {len(moments)}")
    print("\n  -> the music episode's salient musical shapes, its recurring hooks, and "
          "which of its builds share the tada/Grieg SHAPE.")
    os.unlink(full); os.unlink(wav)
    print("=" * 76)


if __name__ == "__main__":
    main()
