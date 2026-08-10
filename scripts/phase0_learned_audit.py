"""PHASE 0 learned-latent — LEAK AUDIT. The result (raw 81 / CMVN 97 @400-way cross-speaker) is 3x the jabberwock's
predicted DENT (30-33). The memory's iron lesson: a too-good number is a leak until a control says otherwise. Run the
controls on the IDENTICAL extraction (cached so we audit, not re-guess):
  (0) speaker DISJOINTNESS — print train vs test speaker IDs; assert no overlap.
  (1) LABEL-SHUFFLE control — permute the bank's word labels; RAW-L must collapse to ~chance (1/400=0.25%). If it stays
      high the pipeline leaks identity through something other than word content.
  (2) DISJOINT-STATS CMVN — per-speaker CMVN where the mean/std come from a speaker's stat-half, applied to the held-out
      test-half (the tested tokens never enter their own normaliser). If 97 was self-normalisation it drops here.
  (3) UTTERANCE-DISJOINT bank — drop any bank word whose source utterance text overlaps a test utterance (guards the
      shared-sentence contextual-leak: wav2vec2 frames carry whole-utterance context).
  (4) RAW-L / SFA-L re-reported for reference.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.phase0_learned_audit
"""
from __future__ import annotations

import glob
import os
import pickle
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

from scripts.phase0_learned_latent import (
    w2v_all_layers, _coch, _l2rows, cold_feat, recog, fit_pca, pca_apply,
    N_BANK, KMAX, NWAY, N_TEST, FPS,
)
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW

LAYER = 6
CACHE = "/tmp/p0lat_cache_L6.pkl"
SFA_K = 16


def build_cache():
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-5:], spks[:-5]

    def gather(spk_list, cap):
        out = []; nu = 0
        for sp in spk_list:
            for (f, t) in by_spk[sp]:
                if nu >= cap:
                    break
                x, fs = load_flac(f); x = np.asarray(x, np.float64); nu += 1
                try:
                    segs = align_utt(x, fs, t)
                except Exception:
                    continue
                M = w2v_all_layers(x, fs)[LAYER]; fps = len(M) / (len(x) / fs)
                uid = os.path.basename(f)[:-5]
                for (w, t0, t1) in segs:
                    if len(w) < MINW:
                        continue
                    s0, s1 = int(t0 * fs), int(t1 * fs)
                    if s1 - s0 < int(0.05 * fs):
                        continue
                    a, b = int(t0 * fps), max(int(t0 * fps) + 1, int(t1 * fps))
                    lat = M[a:b]
                    if lat.shape[0] < 1:
                        continue
                    out.append((w, sp, uid, cold_feat(_coch(x[s0:s1])), lat.astype(np.float32)))
            if nu >= cap:
                break
        return out

    print("  [audit] extracting layer 6 (cache miss)...", flush=True)
    data = {"train": gather(train_spk, N_BANK), "test": gather(test_spk, 999),
            "train_spk": train_spk, "test_spk": test_spk}
    with open(CACHE, "wb") as fh:
        pickle.dump(data, fh)
    return data


def proto(bank, vocab):
    PW = np.stack([np.stack([e.mean(0) for e in bank[w]]).mean(0) for w in vocab])
    return PW / (np.linalg.norm(PW, axis=1, keepdims=True) + 1e-9)


def run(bank_words, test_words, vset, vocab, shuffle=False, seed=0):
    bank = defaultdict(list); cnt = defaultdict(int)
    keys = [w for (w, *_r) in bank_words]
    if shuffle:
        rng = np.random.RandomState(seed); perm = rng.permutation(len(keys))
        keys = [keys[i] for i in perm]
    for t, kw in zip(bank_words, keys):
        if kw in vset and cnt[kw] < KMAX:
            bank[kw].append(t[-1]); cnt[kw] += 1
    eff = [w for w in vocab if bank[w]]                       # robust: only words with >=1 bank exemplar
    effset = set(eff)
    PW = proto(bank, eff)
    toks = [(t[0], t[-1]) for t in test_words if t[0] in effset][:N_TEST]
    return 100 * np.mean([recog(tr, bank, eff, PW) == w for (w, tr) in toks]), len(toks)


def main():
    print("=" * 100)
    print("PHASE 0 learned-latent — LEAK AUDIT (controls on the 81/97 result)")
    print("=" * 100)
    if os.path.exists(CACHE):
        with open(CACHE, "rb") as fh:
            data = pickle.load(fh)
        print(f"  [audit] loaded cache {CACHE}")
    else:
        data = build_cache()
    train, test = data["train"], data["test"]
    train_spk, test_spk = data["train_spk"], data["test_spk"]

    # (0) disjointness
    print(f"\n(0) SPEAKERS  train({len(train_spk)})={train_spk}")
    print(f"             test({len(test_spk)})={test_spk}")
    overlap = set(train_spk) & set(test_spk)
    print(f"    overlap = {overlap or 'NONE (disjoint ✓)'}")

    vc = defaultdict(int)
    for (w, sp, uid, cf, lat) in train:
        vc[w] += 1
    vocab = [w for w, c in sorted(vc.items(), key=lambda kv: -kv[1])[:NWAY] if c >= 2]
    vset = set(vocab)

    # PCA space on raw bank latents (shared)
    mu_r, V_r = fit_pca([lat for (w, sp, uid, cf, lat) in train])
    raw_bank = [(w, sp, uid, pca_apply(lat, mu_r, V_r)) for (w, sp, uid, cf, lat) in train]
    raw_test = [(w, sp, uid, pca_apply(lat, mu_r, V_r)) for (w, sp, uid, cf, lat) in test]

    # (4) RAW-L reference
    rawL, ntok = run(raw_bank, raw_test, vset, vocab)
    print(f"\n(4) RAW-L (reference):                 {rawL:.1f}%   ({ntok} tokens)")

    # (1) label-shuffle control on RAW-L
    sh, _ = run(raw_bank, raw_test, vset, vocab, shuffle=True, seed=1)
    sh2, _ = run(raw_bank, raw_test, vset, vocab, shuffle=True, seed=2)
    print(f"(1) LABEL-SHUFFLE control (→chance):   {sh:.1f}% / {sh2:.1f}%   (chance≈{100/len(vocab):.2f}%; must collapse)")

    # (2) disjoint-stats CMVN: each speaker split stat-half / eval-half; stats from stat-half only.
    def cmvn_disjoint(words):
        bysp = defaultdict(list)
        for t in words:
            bysp[t[1]].append(t)
        out_eval, stats = [], {}
        for sp, ws in bysp.items():
            h = max(1, len(ws) // 2)
            X = np.concatenate([t[4] for t in ws[:h]], 0)
            stats[sp] = (X.mean(0), X.std(0) + 1e-5)
        for sp, ws in bysp.items():
            mu, sd = stats[sp]
            for t in ws[len(ws) // 2:]:
                out_eval.append((t[0], sp, t[2], (t[4] - mu) / sd))
        return out_eval, stats
    # bank: disjoint-cmvn over train (use full train stats for bank, eval-half for test)
    def cmvn_with(words, stats_src):
        bysp = defaultdict(list)
        for t in words:
            bysp[t[1]].append(t)
        st = {}
        for sp, ws in bysp.items():
            X = np.concatenate([t[4] for t in ws], 0); st[sp] = (X.mean(0), X.std(0) + 1e-5)
        return st
    tr_stats = cmvn_with(train, None)
    cm_bank_raw = [(t[0], t[1], t[2], (t[4] - tr_stats[t[1]][0]) / tr_stats[t[1]][1]) for t in train]
    cm_test_eval, _ = cmvn_disjoint(test)   # test stats from disjoint half
    mu_c, V_c = fit_pca([t[3] for t in cm_bank_raw])
    cm_bank = [(t[0], t[1], t[2], pca_apply(t[3], mu_c, V_c)) for t in cm_bank_raw]
    cm_test = [(t[0], t[1], t[2], pca_apply(t[3], mu_c, V_c)) for t in cm_test_eval]
    cmvnD, ntok2 = run(cm_bank, cm_test, vset, vocab)
    print(f"(2) CMVN disjoint-stats:               {cmvnD:.1f}%   ({ntok2} eval-half tokens; vs oracle 97.3)")

    # (3) utterance-disjoint bank: drop bank words from any train utterance that is the SAME SENTENCE as a test utterance
    #     (Jaccard >= 0.5 on content words) -- guards the shared-sentence contextual leak from wav2vec2's whole-utt context.
    STOP = set("the a an of to and in is it that this was for on with as at by be or are his her my your "
               "he she they we you not but had has have were their them from him me all so if no".split())
    def content(words):
        return {w for w in words if len(w) >= 4 and w not in STOP}
    test_utt_words = defaultdict(set)
    for (w, sp, uid, cf, lat) in test:
        test_utt_words[uid].add(w)
    test_bags = [content(b) for b in test_utt_words.values()]
    test_bags = [b for b in test_bags if b]
    train_utt = defaultdict(set)
    for (w, sp, uid, cf, lat) in train:
        train_utt[uid].add(w)
    bad_utts = set()
    for tu, tw in train_utt.items():
        ctw = content(tw)
        if not ctw:
            continue
        for cb in test_bags:
            if len(ctw & cb) / len(ctw | cb) >= 0.5:
                bad_utts.add(tu); break
    ud_bank = [(w, sp, uid, p) for (w, sp, uid, p) in raw_bank if uid not in bad_utts]
    udL, _ = run(ud_bank, raw_test, vset, vocab)
    print(f"(3) UTTERANCE-DISJOINT bank (RAW-L):   {udL:.1f}%   (dropped {len(bad_utts)} shared-sentence utts; vs raw {rawL:.1f})")

    # SFA reference
    sp_means = []
    bysp_tr = defaultdict(list)
    for (w, sp, uid, cf, lat) in train:
        bysp_tr[sp].append(lat)
    for sp, L_ in bysp_tr.items():
        sp_means.append(np.concatenate(L_, 0).mean(0))
    SM = np.stack(sp_means); SM = SM - SM.mean(0)
    _, _, Vt = np.linalg.svd(SM, full_matrices=False)
    Vsp = Vt[:SFA_K].T.astype(np.float32)
    def sfa(lat):
        lat = np.asarray(lat, np.float32); return lat - (lat @ Vsp) @ Vsp.T
    mu_s, V_s = fit_pca([sfa(t[4]) for t in train])
    sf_bank = [(t[0], t[1], t[2], pca_apply(sfa(t[4]), mu_s, V_s)) for t in train]
    sf_test = [(t[0], t[1], t[2], pca_apply(sfa(t[4]), mu_s, V_s)) for t in test]
    sfaL, _ = run(sf_bank, sf_test, vset, vocab)
    print(f"(SFA) speaker-subspace projected:      {sfaL:.1f}%   (vs raw {rawL:.1f})")

    print("\n" + "=" * 100)
    print("  READING:")
    print(f"   • label-shuffle {sh:.1f}/{sh2:.1f}% ~chance → pipeline carries WORD CONTENT, not a trivial leak" if max(sh, sh2) < 5
          else f"   • LABEL-SHUFFLE STAYED HIGH ({max(sh,sh2):.1f}%) → PIPELINE LEAK, the 81/97 is an artifact.")
    print(f"   • CMVN disjoint-stats {cmvnD:.1f}% vs oracle 97.3 → {'holds, not self-normalisation' if cmvnD > 80 else 'DROP = self-normalisation leak'}")
    print(f"   • utterance-disjoint {udL:.1f}% vs raw {rawL:.1f} → {'holds, not shared-sentence context' if udL > rawL-8 else 'DROP = contextual sentence leak'}")
    print("=" * 100)


if __name__ == "__main__":
    main()
