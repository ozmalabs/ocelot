"""GENUINE JOINT DECODE with the GRID slot GRAMMAR — a grammar-constrained segmental Viterbi
that JOINTLY segments + recognizes the whole sentence from the raw utterance (NO oracle word
boundaries), with reliability-weighted AV-fused emissions.

GRID grammar (fixed slot order): sil command color prep letter digit adverb sil. The decode
partitions the 75-frame utterance into that slot sequence; each slot's span is scored by its
best word (AV-fused 1-NN likelihood over the slot's vocab), and the grammar (slot ORDER +
per-slot VOCAB) constrains the search. We report the CONTENT-slot (color/letter/digit) and JOINT
sentence accuracy from the joint decode, audio-only vs FUSED, cross-speaker LOSO. Unlike
grid_av_joint (oracle boundaries), this recovers the words from the stream — genuine recognition.

Run: python scripts/grid_av_decode.py [n_per_letter]   (extract per-frame cache, then decode)
"""
from __future__ import annotations
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

import scripts.grid_av_crossspeaker as X
from scripts.grid_av_crossspeaker import (v1_percepts, shapesig_feat, mouth_roi, _decode,
                                          COLORS, DIGITS, LETTERS, SPEAKERS, N_FRAMES)
from scripts.grid_av_joint import utts          # balanced-by-letter (align_text, mpg_path)
from scipy.signal import resample_poly
from substrate_rs import Substrate
from substrate_rs.speech import _audio
from domains import combinatorial_recognizer as cr

# the GRID finite-state grammar: slot order + per-slot vocabulary.
VOCABS = {
    "sil": {"sil": 0},
    "command": {"bin": 0, "lay": 1, "place": 2, "set": 3},
    "color": COLORS,
    "prep": {"at": 0, "by": 1, "in": 2, "with": 3},
    "letter": LETTERS,
    "digit": DIGITS,
    "adverb": {"again": 0, "now": 1, "please": 2, "soon": 3},
}
GRAMMAR = ["sil", "command", "color", "prep", "letter", "digit", "adverb", "sil"]
DUR = {"sil": (2, 28), "command": (3, 12), "color": (3, 12), "prep": (2, 9),
       "letter": (2, 11), "digit": (3, 12), "adverb": (3, 15)}
CONTENT = ("color", "letter", "digit")
T = 75


def slot_of(word):
    for sl, v in VOCABS.items():
        if word in v:
            return sl, v[word]
    return None


def _cache(spk):
    return f"/tmp/grid_decode_{spk}.npz"


def extract(n_per_letter):
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=24, fs=8000)

    def aud_frames(a8):
        L = np.log(X.cframes(s, bank, np.asarray(a8, float)) + 1e-6)    # raw log-cochlea (n,24)
        E = L.mean(1)                                                   # per-frame log-ENERGY =
        AUD = L - E[:, None]                                            # exactly what SHAPE removes
        flux = np.concatenate([[0.0], np.maximum(0.0, np.diff(L, axis=0)).sum(1)])
        idx = np.linspace(0, len(L) - 1, T).round().astype(int)
        return AUD[idx], flux[idx], E[idx]                             # (75,24),(75,),(75,)

    for spk in SPEAKERS:
        if os.path.exists(_cache(spk)):
            print(f"  {spk}: cached, skip", flush=True); continue
        V1s, AUDs, ODFs, Es, SEGS = [], [], [], [], []
        nok = 0
        for aln, mpg in utts(spk, n_per_letter):
            try:
                fr = _decode(mpg, "video")
                roi = mouth_roi(fr, 0, len(fr))                         # fixed face ROI, all frames
                V1 = np.stack([v1_percepts(roi[i]) for i in range(T)]).astype(np.float32)
                ab = _decode(mpg, "audio")
                a = np.concatenate(ab, axis=1).mean(0) if ab[0].ndim == 2 else np.concatenate(ab)
                AUD, ODF, E = aud_frames(resample_poly(a, 8000, 44100))
                segs = []
                for ln in aln.splitlines():
                    p = ln.split()
                    if len(p) == 3 and slot_of(p[2]):
                        sl, lab = slot_of(p[2])
                        segs.append((sl, lab, int(p[0]) // 1000, max(int(p[1]) // 1000,
                                                                     int(p[0]) // 1000 + 1)))
                V1s.append(V1); AUDs.append(AUD.astype(np.float32))
                ODFs.append(ODF.astype(np.float32)); Es.append(E.astype(np.float32))
                SEGS.append(segs); nok += 1
            except Exception as e:
                print("  skip", spk, type(e).__name__, str(e)[:40])
        np.savez(_cache(spk), V1=np.array(V1s), AUD=np.array(AUDs), ODF=np.array(ODFs),
                 E=np.array(Es), SEGS=np.array(SEGS, dtype=object))
        print(f"  {spk}: {nok} utterances (per-frame V1+audio+segs) cached", flush=True)


def aspan(AUD, a, b):
    idx = np.linspace(a, b - 1, 8).round().astype(int)
    return AUD[idx].flatten()


def vspan(V1, a, b):
    idx = np.linspace(a, b - 1, N_FRAMES).round().astype(int)
    return shapesig_feat(V1[idx])


def build_exemplars(V1s, AUDs, SEGS):
    ex = {sl: {"A": [], "V": [], "W": []} for sl in VOCABS}
    for V1, AUD, segs in zip(V1s, AUDs, SEGS):
        for sl, lab, f0, f1 in segs:
            f0 = max(0, f0); f1 = min(T, max(f1, f0 + 2))
            ex[sl]["A"].append(aspan(AUD, f0, f1)); ex[sl]["V"].append(vspan(V1, f0, f1))
            ex[sl]["W"].append(lab)
    for sl in ex:
        for k in ("A", "V"):
            ex[sl][k] = np.array(ex[sl][k])
        ex[sl]["W"] = np.array(ex[sl]["W"])
    return ex


def _fused_word(slot, sp, t, V1, AUD, ex, R, use_visual):
    vocab = VOCABS[slot]; cands = list(range(len(vocab))); e = ex[slot]; ra, rv = R[slot]
    pa = cr.channel_likelihood(aspan(AUD, sp, t), e["A"], e["W"], cands)
    pv = cr.channel_likelihood(vspan(V1, sp, t), e["V"], e["W"], cands) if use_visual else None
    best, bs = 0, -1e18
    for w in cands:
        sc = ra * np.log(pa[w] + 1e-9) + (rv * np.log(pv[w] + 1e-9) if use_visual else 0.0)
        if sc > bs:
            bs, best = sc, w
    return bs, best


def precompute_em(V1, AUD, ex, R):
    """audio emission (score, best-word) for every (slot, sp, t) span — ONCE per utterance, so
    the onset-weight sweep reuses it (the channel_likelihood is the cost; the Viterbi is cheap)."""
    em = {}
    for slot in VOCABS:
        lo, hi = DUR[slot]; cands = list(range(len(VOCABS[slot]))); e = ex[slot]; ra, _ = R[slot]
        for t in range(1, T + 1):
            for sp in range(max(0, t - hi), t - lo + 1):
                pa = cr.channel_likelihood(aspan(AUD, sp, t), e["A"], e["W"], cands)
                best, bs = 0, -1e18
                for w in cands:
                    sc = ra * np.log(pa[w] + 1e-9)
                    if sc > bs:
                        bs, best = sc, w
                em[(slot, sp, t)] = (bs, best)
    return em


def viterbi_em(em, ODF, onset_w):
    """grammar segmental Viterbi over precomputed audio emissions + a VAD term from the audio
    flux ENVELOPE (the shape-discarded energy cue): spectral flux is LOW in silence, HIGH in
    speech, so reward the `sil` slots over LOW-flux spans and word slots over HIGH-flux spans.
    This anchors the speech region (boundary-onset peaks hurt — phoneme onsets != word
    boundaries). onset_w scales the VAD term. Returns the parse."""
    on = ODF / (ODF.max() + 1e-9)
    cs = np.concatenate([[0.0], np.cumsum(on)])

    def vad(sp, t):
        return (cs[t] - cs[sp]) / max(t - sp, 1)        # mean normalized flux over the span

    NEG = -1e18
    dp = [[NEG] * (T + 1) for _ in range(len(GRAMMAR) + 1)]
    dp[0][0] = 0.0
    bp = {}
    for g, slot in enumerate(GRAMMAR):
        lo, hi = DUR[slot]
        for t in range(1, T + 1):
            for sp in range(max(0, t - hi), t - lo + 1):
                if dp[g][sp] <= NEG / 2 or (slot, sp, t) not in em:
                    continue
                e = em[(slot, sp, t)]
                v = vad(sp, t)
                bonus = onset_w * ((1.0 - v) if slot == "sil" else v)
                sc = dp[g][sp] + e[0] + bonus
                if sc > dp[g + 1][t]:
                    dp[g + 1][t] = sc; bp[(g + 1, t)] = (sp, e[1])
    parse = []; g, t = len(GRAMMAR), T
    while g > 0:
        sp, w = bp[(g, t)]
        parse.append((GRAMMAR[g - 1], w, sp, t)); g, t = g - 1, sp
    return parse[::-1]


GRAMMAR_SPEECH = ["command", "color", "prep", "letter", "digit", "adverb"]


def vad_region(E, thr=0.40):
    """energy VAD: the speech region = frames whose SMOOTHED log-ENERGY (the cue shape
    discarded) is above a floor. The 6 GRID words live inside it; the sil ends are below it.
    Smoothing + thr=0.40 minimizes the speech-extent error (~4 frames; GRID leading sil carries
    breath/noise energy, so a raw threshold triggers too early)."""
    e = (E - E.min()) / (E.max() - E.min() + 1e-9)
    es = np.convolve(e, np.ones(3) / 3, mode="same")
    above = np.where(es > thr)[0]
    if len(above) < 6:
        return 0, T
    return int(above[0]), int(above[-1]) + 1


def otsu(vals, bins=40):
    """label-free bimodal split (Otsu): the threshold on [0,1] energies that maximizes the
    between-class (silence vs speech) variance. Lets the VAD ADJUST to each speaker's own
    energy distribution instead of a global cutoff."""
    h, edges = np.histogram(np.clip(vals, 0, 1), bins=bins, range=(0, 1))
    p = h / (h.sum() + 1e-9)
    mids = (edges[:-1] + edges[1:]) / 2
    omega = np.cumsum(p); mu = np.cumsum(p * mids); muT = mu[-1]
    denom = omega * (1 - omega) + 1e-9
    sb = (muT * omega - mu) ** 2 / denom
    return float(mids[int(np.argmax(sb))])


def viterbi_vad(em, E, thr=0.40):
    """decode the 6-WORD grammar (no sil) over the energy-VAD speech region [s0,s1] — the
    discarded energy level sets the OUTER boundaries; emissions place the inner ones."""
    s0, s1 = vad_region(E, thr)
    GR = GRAMMAR_SPEECH
    NEG = -1e18
    dp = [[NEG] * (T + 1) for _ in range(len(GR) + 1)]
    dp[0][s0] = 0.0
    bp = {}
    for g, slot in enumerate(GR):
        lo, hi = DUR[slot]
        for t in range(s0 + 1, min(s1, T) + 1):
            for sp in range(max(s0, t - hi), t - lo + 1):
                if dp[g][sp] <= NEG / 2 or (slot, sp, t) not in em:
                    continue
                e = em[(slot, sp, t)]
                sc = dp[g][sp] + e[0]
                if sc > dp[g + 1][t]:
                    dp[g + 1][t] = sc; bp[(g + 1, t)] = (sp, e[1])
    ends = [(dp[len(GR)][t], t) for t in range(max(1, s1 - 4), min(T, s1 + 4) + 1)
            if dp[len(GR)][t] > NEG / 2]
    if not ends:
        return None
    _, end = max(ends)
    parse = []; g, t = len(GR), end
    while g > 0:
        sp, w = bp[(g, t)]; parse.append((GR[g - 1], w, sp, t)); g, t = g - 1, sp
    return parse[::-1]


def recognize(parse, V1, AUD, ex, R, rec_visual):
    """content-slot words from the parse: audio-best (already in parse) or AV-fused over the
    decoded span (rec_visual) — recognition within the audio-determined boundaries."""
    out = {}
    for slot, word, sp, t in parse:
        if slot in CONTENT:
            out[slot] = _fused_word(slot, sp, t, V1, AUD, ex, R, True)[1] if rec_visual else word
    return {sl: out.get(sl) for sl in CONTENT}


def calib(Xt, Wt, cands):
    if len(set(Wt)) < 2:
        return 1.0
    n = max(1, len(Xt) // 5); pm = np.random.RandomState(0).permutation(len(Xt))
    Xs, Ws = Xt[pm], Wt[pm]
    am = lambda p: max(p, key=p.get)
    return float(np.mean([am(cr.channel_likelihood(q, Xs[n:], Ws[n:], cands)) == w
                          for q, w in zip(Xs[:n], Ws[:n])]))


def load_all():
    out = {sp: np.load(_cache(sp), allow_pickle=True) for sp in SPEAKERS}
    return out


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    n_test = int(os.environ.get("DECODE_NTEST", "30"))
    print("=" * 76)
    print("GENUINE JOINT DECODE — GRID grammar segmental Viterbi (joint segment+recognize)")
    print("=" * 76)
    if not all(os.path.exists(_cache(sp)) for sp in SPEAKERS):
        extract(n_per)
    np.ones((4, 4)) @ np.ones((4, 4))
    Z = load_all()
    tot = sum(len(Z[sp]["V1"]) for sp in SPEAKERS)
    print(f"  loaded {tot} utterances across {len(SPEAKERS)} speakers; {n_test} decoded/speaker",
          flush=True)

    # AUDIO ENERGY-VAD SEGMENTER, threshold FIXED (0.40) vs PER-SPEAKER ADAPTIVE (Otsu on the
    # held-out speaker's own energies — the VAD fires + adjusts to each speaker).
    def perframe_norm(Earr):
        out = []
        for e in Earr:
            es = np.convolve((e - e.min()) / (e.max() - e.min() + 1e-9),
                             np.ones(3) / 3, mode="same")
            out.append(es)
        return np.concatenate(out)

    print(f"\n  energy-VAD segmenter, threshold FIXED 0.40 vs PER-SPEAKER ADAPTIVE (Otsu)")
    print(f"  {'segmenter':18} | {'COLOR':>6} {'LETTER':>6} {'DIGIT':>6} | "
          f"{'JOINT(audio)':>12} {'JOINT(AV)':>10}")
    print("  " + "-" * 70)
    agg = defaultdict(list); spk_thr = {}
    for ho in SPEAKERS:
        V1tr = np.concatenate([Z[sp]["V1"] for sp in SPEAKERS if sp != ho])
        AUtr = np.concatenate([Z[sp]["AUD"] for sp in SPEAKERS if sp != ho])
        SEtr = np.concatenate([Z[sp]["SEGS"] for sp in SPEAKERS if sp != ho])
        ex = build_exemplars(V1tr, AUtr, SEtr)
        R = {sl: (calib(ex[sl]["A"], ex[sl]["W"], list(range(len(VOCABS[sl])))),
                  calib(ex[sl]["V"], ex[sl]["W"], list(range(len(VOCABS[sl]))))) for sl in VOCABS}
        V1te = Z[ho]["V1"][:n_test]; AUte = Z[ho]["AUD"][:n_test]
        ODte = Z[ho]["ODF"][:n_test]; Ete = Z[ho]["E"][:n_test]; SEte = Z[ho]["SEGS"][:n_test]
        truth = [{sl: lab for sl, lab, _, _ in segs} for segs in SEte]
        # PER-SPEAKER adaptive threshold: Otsu on this speaker's pooled normalized frame energies
        # (label-free, from the held-out speaker's OWN audio).
        thr_a = otsu(perframe_norm(Ete)); spk_thr[ho] = thr_a
        n = len(V1te)
        st = {m: {"cc": {c: 0 for c in CONTENT}, "ja": 0, "jr": 0}
              for m in ("base", "fix", "adapt")}
        for V1, AUD, ODF, E, gt in zip(V1te, AUte, ODte, Ete, truth):
            em = precompute_em(V1, AUD, ex, R)
            modes = (("base", viterbi_em(em, ODF, 0.0)),
                     ("fix", viterbi_vad(em, E, 0.40)),
                     ("adapt", viterbi_vad(em, E, thr_a)))
            for name, parse in modes:
                if parse is None:
                    parse = viterbi_em(em, ODF, 0.0)
                da = recognize(parse, V1, AUD, ex, R, False)
                dr = recognize(parse, V1, AUD, ex, R, True)
                st[name]["ja"] += all(da[c] == gt.get(c) for c in CONTENT)
                st[name]["jr"] += all(dr[c] == gt.get(c) for c in CONTENT)
                for c in CONTENT:
                    st[name]["cc"][c] += dr[c] == gt.get(c)
        for name in st:
            for c in CONTENT:
                agg[f"{name}_{c}"].append(st[name]["cc"][c] / n)
            agg[f"{name}_ja"].append(st[name]["ja"] / n); agg[f"{name}_jr"].append(st[name]["jr"] / n)
        print(f"    [{ho}] adaptive thr={thr_a:.2f}; decoded {n} utts", flush=True)
    for name, label in (("base", "sil-grammar"), ("fix", "energy-VAD fixed"),
                        ("adapt", "energy-VAD adaptive")):
        m = lambda k: np.mean(agg[f"{name}_{k}"])
        print(f"  {label:18} | {m('color'):6.2f} {m('letter'):6.2f} {m('digit'):6.2f} | "
              f"{m('ja'):12.3f} {m('jr'):10.3f}")
    print("=" * 76)
    print(f"  per-speaker adaptive thresholds: "
          + "  ".join(f"{s}={spk_thr[s]:.2f}" for s in SPEAKERS))
    bjr = np.mean(agg["base_jr"]); fjr = np.mean(agg["fix_jr"]); ajr = np.mean(agg["adapt_jr"])
    print(f"  JOINT(AV): baseline {bjr:.3f} -> fixed-VAD {fjr:.3f} -> per-speaker-adaptive "
          f"{ajr:.3f} (adaptive lift over fixed {ajr-fjr:+.3f}, over baseline {ajr-bjr:+.3f})")


if __name__ == "__main__":
    main()
