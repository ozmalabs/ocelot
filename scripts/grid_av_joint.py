"""JOINT GRID-sentence AV recognition — fuse all three word slots (COLOR, LETTER, DIGIT) from
each utterance. Every GRID sentence contains all three words ("bin BLUE at F TWO now"), so one
utterance yields one (color, letter, digit) triple. Each slot is recognized by reliability-
weighted AV fusion (audio formant-shape + vision V1->shape_signature, both cross-speaker-
invariant), and we report per-slot AND JOINT (all-three-correct) accuracy, audio-only vs fused.
Cross-speaker leave-one-speaker-out, 4 GRID speakers. Reuses the cross-speaker AV machinery.

The point: fusion helps most on the weak slot (LETTER), and joint accuracy COMPOUNDS that — the
all-three-correct rate should gain more from fusion than any single slot.

Run: python scripts/grid_av_joint.py [n_per_letter]   (extract->cache per speaker, then fuse)
"""
from __future__ import annotations
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import sys
import tarfile
import zipfile
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from huggingface_hub import hf_hub_download, HfApi

import scripts.grid_av_crossspeaker as X      # v1/shapesig/mouth_roi/_decode/vocabs/helpers
from scripts.grid_av_crossspeaker import (v1_percepts, shapesig_feat, mouth_roi, _decode,
                                          COLORS, DIGITS, LETTERS, SPK_DIR, SPEAKERS, N_FRAMES)
from scipy.signal import resample_poly
from substrate_rs import Substrate
from substrate_rs.speech import _audio
from domains import combinatorial_recognizer as cr

SLOTS = [("color", COLORS), ("letter", LETTERS), ("digit", DIGITS)]
LETTER_IDX = 3


def parse_slots(text):
    """{slot: (start, end, label)} for all three slots, or None if any missing."""
    rows = [ln.split() for ln in text.splitlines() if len(ln.split()) == 3]
    out = {}
    for name, vocab in SLOTS:
        for st, en, w in rows:
            if w in vocab:
                out[name] = (int(st), int(en), vocab[w]); break
    return out if len(out) == 3 else None


def utts(spk, n_per_letter):
    """yield (align_text, mpg_path) balanced by LETTER char (the 25-class bottleneck); mpgs
    streamed to disk (low memory)."""
    import shutil
    outdir = f"/tmp/grid_ex/{spk}"; os.makedirs(outdir, exist_ok=True)
    if spk == "s1":
        files = HfApi().list_repo_files("wissemkarous/lipreading", repo_type="dataset")
        ids = [f.split("/")[-1][:-6] for f in files if f.endswith(".align")]
        mpgs = set(f.split("/")[-1][:-4] for f in files if f.endswith(".mpg"))
        byl = defaultdict(list)
        for i in ids:
            if i in mpgs and len(i) > LETTER_IDX:
                byl[i[LETTER_IDX]].append(i)
        for c in byl:
            for uid in byl[c][:n_per_letter]:
                aln = open(hf_hub_download("wissemkarous/lipreading",
                           f"Data/data/alignments/s1/{uid}.align", repo_type="dataset")).read()
                yield aln, hf_hub_download("wissemkarous/lipreading",
                           f"Data/data/s1/{uid}.mpg", repo_type="dataset")
    else:
        tar = tarfile.open(f"{SPK_DIR}/{spk}.tar")
        aligns = {os.path.basename(m.name)[:-6]: tar.extractfile(m).read().decode()
                  for m in tar.getmembers() if m.name.endswith(".align")}
        z = zipfile.ZipFile(f"{SPK_DIR}/{spk}.zip")
        byl = defaultdict(list)
        for n in z.namelist():
            if n.endswith(".mpg"):
                uid = os.path.basename(n)[:-4]
                if len(uid) > LETTER_IDX and uid in aligns:
                    byl[uid[LETTER_IDX]].append((uid, n))
        for c in byl:
            for uid, n in byl[c][:n_per_letter]:
                path = f"{outdir}/{uid}.mpg"
                if not os.path.exists(path):
                    with z.open(n) as src, open(path, "wb") as dst:
                        shutil.copyfileobj(src, dst, 1 << 20)
                yield aligns[uid], path


def utt_features(mpg_path, slots, afeat):
    """decode the utterance ONCE; extract per-slot (label, vshape, aud) from each slot's seg."""
    fr = _decode(mpg_path, "video")
    ab = _decode(mpg_path, "audio")
    a = np.concatenate(ab, axis=1).mean(0) if ab[0].ndim == 2 else np.concatenate(ab)
    a8 = resample_poly(a, 8000, 44100)
    out = {}
    for name, (st, en, lab) in slots.items():
        f0, f1 = max(0, st // 1000 - 2), min(75, en // 1000 + 2)
        roi = mouth_roi(fr, f0, f1)
        idx = np.linspace(0, len(roi) - 1, N_FRAMES).round().astype(int)
        G = np.stack([v1_percepts(roi[i]) for i in idx])
        s0, s1 = int(st / 1000 / 25 * 8000), int(max(en // 1000, st // 1000 + 1) / 25 * 8000)
        out[name] = (lab, shapesig_feat(G), afeat(a8[s0:s1]))
    return out


def _cache(spk):
    return f"/tmp/grid_joint_{spk}.npz"


def extract(n_per_letter):
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=24, fs=8000)

    def afeat(a):
        M = X.cshape(X.cframes(s, bank, np.asarray(a, float)))
        idx = np.linspace(0, len(M) - 1, 8).round().astype(int)
        return np.stack([M[i] for i in idx]).flatten()

    for spk in SPEAKERS:
        if os.path.exists(_cache(spk)):
            print(f"  {spk}: cached, skip", flush=True); continue
        cols = {f"{nm}_{k}": [] for nm, _ in SLOTS for k in ("lab", "V", "A")}
        nok = 0
        for aln, mpg in utts(spk, n_per_letter):
            slots = parse_slots(aln)
            if not slots:
                continue
            try:
                feats = utt_features(mpg, slots, afeat)
                for nm, _ in SLOTS:
                    lab, V, A = feats[nm]
                    cols[f"{nm}_lab"].append(lab); cols[f"{nm}_V"].append(V); cols[f"{nm}_A"].append(A)
                nok += 1
            except Exception as e:
                print("  skip", spk, type(e).__name__, str(e)[:40])
        np.savez(_cache(spk), **{k: np.array(v) for k, v in cols.items()})
        print(f"  {spk}: {nok} utterances (x3 slots) cached", flush=True)


def load_all():
    spk, data = [], {f"{nm}_{k}": [] for nm, _ in SLOTS for k in ("lab", "V", "A")}
    for si, sp in enumerate(SPEAKERS):
        z = np.load(_cache(sp))
        n = len(z[f"{SLOTS[0][0]}_lab"])
        spk += [si] * n
        for k in data:
            data[k].append(z[k])
    return np.array(spk), {k: np.concatenate(v) for k, v in data.items()}


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print("=" * 76)
    print("JOINT GRID-SENTENCE AV — fuse COLOR+LETTER+DIGIT slots, leave-one-speaker-out")
    print("=" * 76)
    if not all(os.path.exists(_cache(sp)) for sp in SPEAKERS):
        extract(n_per)
    np.ones((4, 4)) @ np.ones((4, 4))
    s = Substrate()
    spk, D = load_all()
    print(f"  loaded {len(spk)} utterances x 3 slots across {len(set(spk))} speakers", flush=True)

    MAXC = max(len(v) for _, v in SLOTS)
    # is_word starts 0; set_active toggles exactly this slot's candidate Concepts on, so the
    # held term's Argmax ranges over the right candidate set (slots have 4/10/25 classes).
    word_node = {d: s.add_node("Concept", {"name": f"c{d}", cr.WORD_ATTR: 0.0}) for d in range(MAXC)}
    term = cr.predict_reliability_weighted_term()
    am = lambda p: max(p, key=p.get)

    def lk(q, Xtr, Wtr, cands):
        return cr.channel_likelihood(q, Xtr, Wtr, cands)

    def calib(Xt, Wt, cands):
        n = max(1, len(Xt) // 5); pm = np.random.RandomState(0).permutation(len(Xt))
        Xs, Ws = Xt[pm], Wt[pm]
        return np.mean([am(lk(q, Xs[n:], Ws[n:], cands)) == w for q, w in zip(Xs[:n], Ws[:n])])

    def set_active(cands):
        active = set(cands)
        for d, nid in word_node.items():
            s.set_attr(nid, cr.WORD_ATTR, 1.0 if d in active else 0.0)

    def fuse(pa, pv, ra, rv, cands):
        for d in cands:
            s.set_attr(word_node[d], cr.P_FLAT_ATTR, float(pa[d]))
            s.set_attr(word_node[d], cr.P_TRANS_ATTR, float(pv[d]))
            s.set_attr(word_node[d], cr.R_FLAT_ATTR, float(ra))
            s.set_attr(word_node[d], cr.R_TRANS_ATTR, float(rv))
        win = s._inner.evaluate(term, {})       # held reliability-weighted Argmax over cands
        return next(d for d, n in word_node.items() if n == win)

    print(f"\n  {'held-out':9} | {'COLOR a/f':>12} {'LETTER a/f':>12} {'DIGIT a/f':>12} "
          f"| {'JOINT a/f':>12}")
    print("  " + "-" * 70)
    agg = defaultdict(list)
    for ho in sorted(set(spk)):
        tr, te = spk != ho, np.where(spk == ho)[0]
        per = {}
        correct_a = {nm: np.zeros(len(te), bool) for nm, _ in SLOTS}
        correct_f = {nm: np.zeros(len(te), bool) for nm, _ in SLOTS}
        for nm, vocab in SLOTS:
            cands = list(range(len(vocab)))
            set_active(cands)                       # held Argmax ranges over this slot only
            Vtr, Atr, Wtr = D[f"{nm}_V"][tr], D[f"{nm}_A"][tr], D[f"{nm}_lab"][tr]
            ra, rv = calib(Atr, Wtr, cands), calib(Vtr, Wtr, cands)
            a_acc = f_acc = 0
            for k, i in enumerate(te):
                pa = lk(D[f"{nm}_A"][i], Atr, Wtr, cands)
                pv = lk(D[f"{nm}_V"][i], Vtr, Wtr, cands)
                lab = D[f"{nm}_lab"][i]
                ca = am(pa) == lab; cf = fuse(pa, pv, ra, rv, cands) == lab
                correct_a[nm][k] = ca; correct_f[nm][k] = cf
                a_acc += ca; f_acc += cf
            per[nm] = (a_acc / len(te), f_acc / len(te))
            agg[nm + "_a"].append(per[nm][0]); agg[nm + "_f"].append(per[nm][1])
        ja = np.mean(np.all([correct_a[nm] for nm, _ in SLOTS], axis=0))
        jf = np.mean(np.all([correct_f[nm] for nm, _ in SLOTS], axis=0))
        agg["joint_a"].append(ja); agg["joint_f"].append(jf)
        print(f"  {SPEAKERS[ho]:9} | "
              f"{per['color'][0]:.2f}/{per['color'][1]:.2f}   "
              f"{per['letter'][0]:.2f}/{per['letter'][1]:.2f}   "
              f"{per['digit'][0]:.2f}/{per['digit'][1]:.2f}  | "
              f"{ja:.2f}/{jf:.2f}")
    print("  " + "-" * 70)
    g = {k: np.mean(v) for k, v in agg.items()}
    print(f"  {'MEAN':9} | {g['color_a']:.2f}/{g['color_f']:.2f}   "
          f"{g['letter_a']:.2f}/{g['letter_f']:.2f}   {g['digit_a']:.2f}/{g['digit_f']:.2f}  | "
          f"{g['joint_a']:.2f}/{g['joint_f']:.2f}")
    print("=" * 76)
    print("  a/f = audio-only / reliability-weighted FUSED; JOINT = all three slots correct.")
    print(f"  fusion lift: color {g['color_f']-g['color_a']:+.3f}  letter "
          f"{g['letter_f']-g['letter_a']:+.3f}  digit {g['digit_f']-g['digit_a']:+.3f}  "
          f"JOINT {g['joint_f']-g['joint_a']:+.3f}")


if __name__ == "__main__":
    main()
