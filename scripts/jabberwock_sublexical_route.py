"""The jabberwock builds the SUB-LEXICAL RULE-ASSEMBLY ROUTE (dual-route N6).

The disorders spike (speech_disorders_capability_grounding.md) diagnosed the project as
"surface-only" / phonological dyslexia: it has the WHOLE-FORM LEXICAL route (word-template
match) but lacks the GENERATIVE SUB-LEXICAL route — assemble a word from its sub-word parts
via the lexicon (phone-seq -> word), which can recognise NOVEL words that have NO whole-word
template (exactly what phonological dyslexia loses; conduction-aphasia nonword repetition).

  LEXICAL route   : clip -> whole-word feature -> nearest WORD-TEMPLATE. Can only return
                    words it has a template for (the lexicon-as-exemplars).
  SUB-LEXICAL     : clip -> per-frame phone -> phone STRING -> rank lexicon entries by
                    phone-seq edit distance (assembly via rules). Needs only the phone-seq,
                    NOT an acoustic template -> recognises NOVEL words generatively.

Tested on CLEAN word clips (oracle boundaries — the setting where the route CAN work; the
continuous setting is acoustic-floor/chance per commit 178936e1) WITH the discriminative
control (AUC: does the TRUE word's phone-seq match the decoded string better than other
lexicon words?). THE DISSOCIATION: on NOVEL words (no template), the lexical route scores 0
(structurally), the sub-lexical route recognises them — the dual-route double dissociation.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_sublexical_route.py [Kseen] [Knovel]
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
from scripts.jabberwock_reads_oov_from_phones import phones as cmu_phones
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda
from scripts.jabberwock_subword_recognizer import _load_ph, norm_edit
from scripts.jabberwock_earns_phone_model import ctxd


def _wfeat(fr, Ln=20):
    """whole-word content feature (peel + resample + velocity) for the lexical route."""
    fr = np.asarray(fr, float)
    n = len(fr); idx = np.linspace(0, n - 1, Ln); lo = np.floor(idx).astype(int)
    hi = np.clip(lo + 1, 0, n - 1); t = (idx - lo)[:, None]
    x = (fr - fr.mean(0)); x = x[lo] * (1 - t) + x[hi] * t
    d = np.vstack([np.zeros((1, x.shape[1])), np.diff(x, axis=0)])
    v = np.concatenate([x, d], axis=1).reshape(-1)
    return v / max(np.linalg.norm(v), 1e-9)


def main():
    Kseen = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    Knovel = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    train = _load_ph("train-clean-100_*.pkl", 12)
    dev = _load_ph("dev-clean_*.pkl", 12)
    print("=" * 84)
    print("SUB-LEXICAL RULE-ASSEMBLY ROUTE — generative phone-assembly vs lexical templates")
    print("=" * 84)

    # ---- PHONE MODEL (per-frame, flat-start + deltas; the dorsal front end) ----
    phset = sorted({p for _w, _f, ph in train for p in ph})
    pi = {p: i for i, p in enumerate(phset)}
    Xtr, Ytr = [], []
    for w, fr, ph in train:
        cx = ctxd(fr); n = len(cx); P = len(ph)
        for i in range(n):
            Xtr.append(cx[i]); Ytr.append(ph[int(i * P / n)])
        if len(Xtr) >= 40000:
            break
    Xtr = np.array(Xtr); nP = len(phset); Pd = min(120, Xtr.shape[0] - nP - 1)
    mu, Wp = _fit_pca(Xtr, Pd); Wl = _fit_lda((Xtr - mu) @ Wp, Ytr, k=min(Pd, nP - 1))
    def penc(Z):
        R = ((np.asarray(Z) - mu) @ Wp) @ Wl
        return R / np.clip(np.linalg.norm(R, axis=1, keepdims=True), 1e-9, None)
    Etr = penc(Xtr); cent, cph = [], []
    rng = np.random.default_rng(0)
    for p in phset:
        Zp = Etr[[i for i in range(len(Ytr)) if Ytr[i] == p]]
        C = Zp[rng.choice(len(Zp), min(4, len(Zp)), replace=False)].copy() if len(Zp) else None
        if C is None:
            continue
        for _ in range(5):
            lab = (((Zp[:, None] - C[None]) ** 2).sum(2)).argmin(1)
            for k in range(len(C)):
                m = Zp[lab == k]
                if len(m):
                    C[k] = m.mean(0)
        for c in C:
            cent.append(c); cph.append(pi[p])
    cent = np.array(cent); cent /= np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)
    cph = np.array(cph)

    def decode_clip(fr):
        idx = cph[(penc(ctxd(fr)) @ cent.T).argmax(1)]
        seq, prev = [], -1
        for k in idx:
            if k != prev:
                seq.append(phset[k]); prev = k
        return seq
    print(f"  phone model: {nP} phones, {len(cent)} centroids", flush=True)

    # ---- vocab split: SEEN (whole-word templates) vs NOVEL (lexicon only, no template) ----
    sw = Counter(w for w, _, _ in train); qw = Counter(w for w, _, _ in dev)
    func = set(w for w, _ in sw.most_common(50))
    content = [w for w, _ in sw.most_common() if w not in func and len(w) >= 4 and qw[w] >= 1
               and cmu_phones(w)]
    seen = content[:Kseen]; novel = content[Kseen:Kseen + Knovel]
    lex = {w: [str(x) for x in cmu_phones(w)] for w in seen + novel}   # full lexicon (phone-seqs)
    sset = set(seen)

    # whole-word templates for SEEN only (the lexical route's inventory)
    by = defaultdict(list)
    for w, fr, ph in train:
        if w in sset and len(by[w]) < 20:
            by[w].append(_wfeat(fr))
    wt_words = [w for w in seen if by[w]]
    WT = np.array([np.mean(by[w], 0) for w in wt_words])
    WT /= np.clip(np.linalg.norm(WT, axis=1, keepdims=True), 1e-9, None)
    print(f"  seen={len(wt_words)} (templates)  novel={len(novel)} (lexicon only)", flush=True)

    lex_words = wt_words + novel
    lex_seqs = [lex[w] for w in lex_words]

    def evaluate(words, tag):
        q = [(w, fr) for w, fr, ph in dev if w in set(words)]
        rng.shuffle(q); q = q[:400]
        lex_t1 = sub_t1 = sub_t5 = 0; pos, neg = [], []
        for w, fr in q:
            # LEXICAL route: nearest whole-word template (over SEEN templates only)
            j = int((WT @ _wfeat(fr)).argmax()); lex_t1 += (wt_words[j] == w)
            # SUB-LEXICAL route: decode phones -> rank ALL lexicon entries by phone-seq edit
            ds = decode_clip(fr)
            costs = np.array([norm_edit(ds, s) for s in lex_seqs])
            order = np.argsort(costs)
            cand = [lex_words[k] for k in order[:5]]
            sub_t1 += (cand[0] == w); sub_t5 += (w in cand)
            ti = lex_words.index(w)
            pos.append(costs[ti])
            negi = rng.choice([k for k in range(len(lex_words)) if lex_words[k] != w], 1)[0]
            neg.append(costs[negi])
        n = max(len(q), 1); pos = np.array(pos); neg = np.array(neg)
        auc = float(np.mean(pos[:, None] < neg[None, :]))
        print(f"  [{tag:6}] LEXICAL top1 {lex_t1/n:.3f} | SUB-LEXICAL top1 {sub_t1/n:.3f} "
              f"top5 {sub_t5/n:.3f}  AUC {auc:.3f}  ({len(q)} clips)", flush=True)
        return lex_t1 / n, sub_t1 / n, auc

    t0 = time.time()
    ls, ss, sa = evaluate(seen, "SEEN")
    ln, sn, na = evaluate(novel, "NOVEL")
    print("=" * 84)
    print(f"  DISSOCIATION (novel words): LEXICAL top1 {ln:.3f} (structurally ~0, no template) "
          f"vs SUB-LEXICAL top1 {sn:.3f}  AUC {na:.3f}")
    print(f"  [{time.time()-t0:.0f}s]")
    ok = na > 0.6 and sn > 5 * (1 / (len(lex_words)))
    print(f"  {'SUB-LEXICAL ROUTE WORKS: recognises NOVEL words generatively (AUC>0.6) where the' if ok else 'sub-lexical route is acoustic-floor-bound (AUC~0.5): the phone model caps it'}")
    if ok:
        print("  lexical route is structurally 0 — the dual-route double dissociation, on clean clips.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
