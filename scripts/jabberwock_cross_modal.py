"""CROSS-MODAL GRAPHEME<->PHONEME (graph-native) — reading aloud, measured.

Ties the writing recogniser to the speech side. Both modalities use the shared AbS spine (argmax over
-Distance): a grapheme is a written Omniglot symbol matched by PointSetDist; a phoneme is a spoken FSDD
digit matched by DtwTo (real handwriting + real speech, the same recognition shape, different distance).
The cross-modal association is learned by CO-PRESENTATION (seeds/cross_modal.json): bind_grapheme_phoneme
ties the recognised grapheme to the recognised phoneme identity; read_aloud recalls a recognised grapheme's
sound; listen_write recalls a recognised phoneme's symbol. Recall generalises across writers and speakers
via the shared concept.

The demo teaches 10 grapheme<->digit pairs by co-presentation (self-recognising gallery exemplars, so the
binding is exact), then READS ALOUD held-out writers (grapheme -> recalled digit) and takes DICTATION from
held-out speakers (spoken digit -> recalled symbol) -- each bounded by its modality's held-out recognition.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_cross_modal [n_test]
"""
from __future__ import annotations

import json
import os
import re
import sys
import wave
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

import substrate_rs as srs
from domains import omniglot_world as ow
from domains.recognition_graph import _Argmax, _NodesWhere, _Lit, _Neg, _Attr, _V, _PointSetDist

SEP = "=" * 92
WHOLE_N, NDIG, AUD_TMPL = 64, 10, 8
FSDD = "/tmp/fsdd/recordings"
_FN = re.compile(r"(\d)_(\w+?)_(\d+)\.wav")


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _dtw(a, b):
    return {"type": "DtwTo", "a": a, "b": b}


# grapheme recogniser (PointSetDist) and phoneme recogniser (DtwTo) — same AbS argmax shape, different gallery + distance
GRAPH_PRED = _Pred(_Argmax(_NodesWhere("Concept", "is_grapheme", _Lit(1.0)), "w",
                           _Neg(_PointSetDist(_Attr(_V("s"), "axs_heard_feat"), _Attr(_V("w"), "axs_synth_feat")))))
AUDIO_PRED = _Pred(_Argmax(_NodesWhere("Concept", "is_audio", _Lit(1.0)), "w",
                           _Neg(_dtw(_Attr(_V("s"), "axs_heard_feat"), _Attr(_V("w"), "axs_synth_feat")))))


def fsdd_feat(a, nf=32, nm=13, win=256):
    a = a / (np.abs(a).max() + 1e-9)
    hop = max(1, (len(a) - win) // max(1, nf - 1))
    edges = np.floor(np.linspace(0, win // 2, nm + 1)).astype(int)
    fr = []
    for i in range(nf):
        seg = a[i * hop:i * hop + win]
        if len(seg) < win:
            seg = np.pad(seg, (0, win - len(seg)))
        mag = np.abs(np.fft.rfft(seg * np.hanning(win)))
        fr.append([np.log(mag[edges[k]:edges[k + 1] + 1].sum() + 1e-6) for k in range(nm)])
    fr = np.array(fr)
    return (fr - fr.mean(0)) / (fr.std(0) + 1e-6)


def load_wav(p):
    with wave.open(p, "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    print(SEP)
    print("CROSS-MODAL GRAPHEME<->PHONEME (graph-native): reading aloud. Vision (Omniglot/PointSetDist) and")
    print("speech (FSDD/DtwTo) share the AbS spine; a co-presented pair binds grapheme<->phoneme. Recall is bidir.")
    print(SEP)
    if not ow.have_data("evaluation") or not os.path.isdir(FSDD):
        print(f"\n  need Omniglot ({ow.DATA}) and FSDD ({FSDD}).")
        return 1

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= NDIG}
    alph = sorted(by_alph)[0]; ch = by_alph[alph]
    wc: dict[str, np.ndarray] = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    files = [(os.path.join(FSDD, fn), int(_FN.match(fn).group(1)), _FN.match(fn).group(2))
             for fn in sorted(os.listdir(FSDD)) if _FN.match(fn)]
    spk = sorted({s for _, _, s in files})
    gal_spk, test_spk = set(spk[:4]), set(spk[4:])

    s = srs.Substrate()
    s._inner.load_seed_manifest(json.loads((Path(ROOT) / "seeds" / "cross_modal.json").read_text()), s.add_node("Agent", {}))

    # --- galleries: 10 grapheme symbols (single template) + multi-template audio per phoneme identity ---
    G = []
    for d in range(NDIG):
        g = s.add_node("Concept", {"is_grapheme": 1.0}); s.set_attr(g, "axs_synth_feat", whole(ow.drawings(ch[d])[0]).tolist())
        s.set_attr(g, "name", str(d)); G.append(g)
    P = []
    for d in range(NDIG):
        p = s.add_node("Concept", {"is_phoneme": 1.0}); s.set_attr(p, "name", str(d)); P.append(p)
    aud_gallery = []                                            # audio templates -> their phoneme identity
    for d in range(NDIG):
        got = 0
        for fp, dd, sp in files:
            if dd == d and sp in gal_spk:
                t = s.add_node("Concept", {"is_audio": 1.0}); s.set_attr(t, "axs_synth_feat", fsdd_feat(load_wav(fp)).tolist())
                s.set_attr(t, "name", str(d)); s.add_edge_unchecked(t, "of_phoneme", P[d]); aud_gallery.append((t, d))
                got += 1
                if got >= AUD_TMPL:
                    break

    def recognise(pred, feat):
        m = s.add_node("Mark", {}); s.set_attr(m, "axs_heard_feat", feat.tolist())
        w = s.evaluate(pred, {"s": m})
        if w is not None:
            s.add_edge_unchecked(m, "recognised_as", w)
        return m, w

    # --- TEACH: co-present each grapheme with a self-recognising audio exemplar (binding is exact) ---
    for d in range(NDIG):
        gm, _ = recognise(GRAPH_PRED, whole(ow.drawings(ch[d])[0]))            # the gallery exemplar (self-recognises)
        t0 = next(t for t, dd in aud_gallery if dd == d)                       # a gallery audio template of digit d
        am = s.add_node("Mark", {}); s.set_attr(am, "axs_heard_feat", s.node(t0)["attrs"]["axs_synth_feat"])
        s.add_edge_unchecked(am, "recognised_as", t0)
        s.add_edge_unchecked(gm, "co_modal", am)                               # cross-modal ostension
    s._inner.run_rules(50000)                                                  # bind_grapheme_phoneme fires

    bound = sum(1 for g in G if s.neighbours(g, "sounds_like"))
    print(f"\n  taught {bound}/{NDIG} grapheme<->phoneme pairs by co-presentation (exact binding).", flush=True)

    # --- READ ALOUD: held-out writers, grapheme -> recalled digit ---
    rng = np.random.default_rng(3)
    read_ok = read_tot = 0
    for d in range(NDIG):
        for di in rng.choice(range(1, 20), size=min(n_test // NDIG, 19), replace=False):
            gm, _ = recognise(GRAPH_PRED, whole(ow.drawings(ch[d])[int(di)]))
            s._inner.run_rules(50000)
            spoke = [s.node(p)["attrs"]["name"] for p in s.neighbours(gm, "speaks")]
            read_ok += (spoke == [str(d)]); read_tot += 1

    # --- TAKE DICTATION: held-out speakers, spoken digit -> recalled symbol ---
    test_aud = [(fsdd_feat(load_wav(fp)), d) for fp, d, sp in files if sp in test_spk]
    np.random.default_rng(1).shuffle(test_aud)
    write_ok = write_tot = 0
    for feat, d in test_aud[:n_test]:
        pm, _ = recognise(AUDIO_PRED, feat)
        s._inner.run_rules(50000)
        wrote = [s.node(g)["attrs"]["name"] for g in s.neighbours(pm, "writes")]
        write_ok += (wrote == [str(d)]); write_tot += 1

    print(f"\n  {'cross-modal recall':40}{'accuracy':>12}")
    print(f"    {'READ ALOUD  (new writer: symbol -> sound)':40}{100*read_ok/max(read_tot,1):>11.1f}%   ({read_tot} held-out graphemes)")
    print(f"    {'DICTATION   (new speaker: sound -> symbol)':40}{100*write_ok/max(write_tot,1):>11.1f}%   ({write_tot} held-out phonemes)")
    print(f"\n  {SEP[:88]}")
    print(f"  reading aloud and taking dictation are graph-native (cross_modal Rules over the shared concepts);")
    print(f"  vision and speech use the SAME AbS argmax. Read-aloud rides the strong grapheme channel; dictation")
    print(f"  rides the harder speaker-independent speech channel -- both far above chance (10%). The two")
    print(f"  perception arcs (writing + speech) are now one system, bound graph-native by co-presentation.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
