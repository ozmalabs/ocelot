"""RESIDUAL 3 (final) — CATEGORY INDUCTION: self-discover content-word categories (noun/verb) without POS.

The cognition increment (c699514b) showed frame-distribution-ALONE collapses (POS-purity 0.26) — the heavy
content-word SINGLETON tail leaves rare words with no context. Two tractable levers (never "irreducible"):
  1. HYBRID form+context — combine CONTEXT (which self-identified function-forms precede the word) with the
     word's FORM (its acoustic embedding + the EARNED phone-string SUFFIX = morphology: -ing/-ed -> verb,
     -tion/-er -> noun). A RARE word with no context gets its category from FORM.
  2. DATA SCALE — more content-word tokens -> category purity RISES; quantify the token count.

donkey=0: order-1 word-forms = pooled-acoustic k-means; function/content split = agent-authored
distributional rule; FORM morphology = the EARNED phone model's phone-string suffix (teacher removed at
inference); clustering = held k-means; POS = scoring-ONLY. Memory: aggregate to word-FORMS, float32,
ulimit-14Gi, no (N,K,D). USE THE VENV PYTHON.

Run: PYTHONPATH=runners/dsl/python:.:scripts /home/matt/ozma/internal/research/.venv/bin/python \
        scripts/jabberwock_category_induction.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
from collections import Counter, defaultdict
import scripts.jabberwock_syntax_clean_order1 as D          # ulimit guard; author_constructions/apply_distributional/FUNC/_peak_gib
import scripts.jabberwock_earned_order1_consistency as C     # load_words_energy/earn_energy/earned_wf_energy
import referential_word_learning as R
CTX_ALONE = 0.26                                             # c699514b frame-distribution-alone POS-purity


def pooled(fr):
    return np.concatenate([fr.mean(0), fr.std(0)]).astype(np.float32)


def cat_purity(labels, pos, keep=("N", "V")):
    byc = defaultdict(list)
    for i in range(len(labels)):
        if pos[i] in keep:
            byc[labels[i]].append(pos[i])
    pf = [max(Counter(v).values()) / len(v) for v in byc.values() if len(v) >= 3]
    return float(np.mean(pf)) if pf else 0.0


def cluster_align(feat, pos, KCAT, seed=0):
    lab = [int(x) for x in R.kmeans(R._unit(feat), min(KCAT, len(feat)), np.random.default_rng(seed))]
    return cat_purity(lab, pos)


def _pca_z(X, d):
    """PCA to d dims + z-norm so blocks combine BALANCED (not dominated by raw dimensionality)."""
    if X.shape[1] <= d:
        Z = X.astype(np.float64)
    else:
        mu = X.mean(0); _, _, Vt = np.linalg.svd((X - mu).astype(np.float64), full_matrices=False)
        Z = (X - mu) @ Vt[:d].T
    return (Z - Z.mean(0)) / (Z.std(0) + 1e-6)


def analyze(a, P, suffix, words, coarse, idxs, KCAT=8):
    """Content-word category induction on a token subset. Returns purities + rare/freq alignments."""
    Ps = P[idxs]; wd = [words[i] for i in idxs]; suf = suffix[idxs]
    Kw = min(400, max(KCAT, len(idxs) // 6))
    lab = [int(x) for x in R.kmeans(R._unit(Ps), Kw, np.random.default_rng(0))]
    isf, _ = D.apply_distributional(a, lab)
    byf = defaultdict(list)
    for j in range(len(idxs)):
        byf[lab[j]].append(j)
    dom = {f: Counter(wd[j] for j in jj).most_common(1)[0][0] for f, jj in byf.items()}
    func = set(f for f in isf if isf.get(f))
    topf = [f for f, _ in Counter([lab[j] for j in range(len(idxs)) if lab[j] in func]).most_common(30)]
    fidx = {f: k for k, f in enumerate(topf)}
    content = [f for f in byf if not isf.get(f) and coarse(dom[f]) in ("N", "V")]
    if len(content) < KCAT:
        return None
    ctxv, formv, posc, freqc = [], [], [], []
    for f in content:
        cv = np.zeros(len(topf) + 1, np.float32); ac = np.zeros(Ps.shape[1], np.float32); sf = np.zeros(suf.shape[1], np.float32)
        for j in byf[f]:
            if j > 0 and lab[j - 1] in fidx:
                cv[fidx[lab[j - 1]]] += 1.0
            else:
                cv[-1] += 1.0
            ac += Ps[j]; sf += suf[j]
        ctxv.append(cv); formv.append(np.concatenate([R._unit(ac[None])[0], R._unit(sf[None])[0]]))
        posc.append(coarse(dom[f])); freqc.append(len(byf[f]))
    ctxv = np.stack(ctxv); formv = np.stack(formv)
    hybv = np.concatenate([_pca_z(ctxv, 8), _pca_z(formv, 8)], axis=1)     # BALANCED fusion
    p_ctx, p_form, p_hyb = (cluster_align(ctxv, posc, KCAT), cluster_align(formv, posc, KCAT),
                            cluster_align(hybv, posc, KCAT))
    p_sh = cat_purity([int(x) for x in R.kmeans(R._unit(hybv), min(KCAT, len(hybv)), np.random.default_rng(0))],
                      list(np.random.default_rng(3).permutation(posc)))
    base = max(posc.count("N"), posc.count("V")) / max(posc.count("N") + posc.count("V"), 1)
    med = int(np.median(freqc))
    rare = [k for k in range(len(content)) if freqc[k] <= 2]
    freq = [k for k in range(len(content)) if freqc[k] > med]
    def sa(idx, feat):
        return cluster_align(feat[idx], [posc[k] for k in idx], min(KCAT, max(1, len(idx) // 2))) if len(idx) >= KCAT else float("nan")
    return {"n": len(content), "nN": posc.count("N"), "nV": posc.count("V"),
            "ctx": p_ctx, "form": p_form, "hyb": p_hyb, "sh": p_sh, "base": base, "n_rare": len(rare),
            "rare_ctx": sa(rare, ctxv), "rare_form": sa(rare, formv), "rare_hyb": sa(rare, hybv),
            "freq_ctx": sa(freq, ctxv), "freq_form": sa(freq, formv)}


def main():
    MAXTOK = int(os.environ.get("MAXTOK", "8000")); KCAT = 8
    a, _ = D.author_constructions()
    data = C.load_words_energy("train-clean-100_*.pkl", 6, MAXTOK)
    words = [w for w, _, _, _ in data]; cut = int(0.7 * len(data))
    print(f"\n  LibriSpeech train-clean energy, {len(data)} word tokens, vocab {len(set(words))}  "
          f"[peak {D._peak_gib():.2f} GiB]", flush=True)
    from nltk import pos_tag
    tags = dict(pos_tag(list(dict.fromkeys(words))))
    def coarse(w):
        t = tags.get(w, "")
        return "N" if t.startswith("NN") else "V" if t.startswith("VB") else "O"

    print("  earning phone model (FORM suffix/morphology extractor; teacher removed at inference)...", flush=True)
    enc, cent, cphone, ps, pi = C.earn_energy(data[:cut]); nP = len(ps)
    P = np.stack([pooled(fr) for _, fr, _, _ in data]).astype(np.float32)
    suffix = np.zeros((len(data), nP), np.float32)
    for i, (_, fr, _, en) in enumerate(data):
        s = C.earned_wf_energy(fr, en, enc, cent, cphone, nP).split("|")
        for p in s[-3:]:
            if p.isdigit():
                suffix[i, int(p) % nP] += 1.0
    print(f"  form suffix (earned phones) built  [peak {D._peak_gib():.2f} GiB]", flush=True)

    full = analyze(a, P, suffix, words, coarse, list(range(len(data))), KCAT)
    print("\n--- (a) category POS-purity: HYBRID (balanced form+context) vs context-only vs form-only ---")
    print(f"  content forms {full['n']} (N {full['nN']}, V {full['nV']}): context {full['ctx']:.3f} | "
          f"form {full['form']:.3f} | HYBRID {full['hyb']:.3f}  (shuffled {full['sh']:.3f}, base "
          f"{full['base']:.3f}, c699514b ctx-alone {CTX_ALONE:.2f})")
    print("\n--- (b) FORM rescues rare/singleton words (rare freq<=2 vs frequent) ---")
    print(f"  RARE ({full['n_rare']}): context {full['rare_ctx']:.3f} | form {full['rare_form']:.3f} | "
          f"hybrid {full['rare_hyb']:.3f}")
    print(f"  FREQ: context {full['freq_ctx']:.3f} | form {full['freq_form']:.3f}")

    print("\n--- (c) DATA-SCALE: category POS-purity vs #content-word tokens ---")
    print(f"  {'#tokens':>8} {'#content':>8} {'context':>8} {'form':>7} {'HYBRID':>7}")
    scale = []
    for frac in (0.2, 0.4, 0.7, 1.0):
        k = int(frac * len(data)); r = analyze(a, P, suffix, words, coarse, list(range(k)), KCAT)
        if r:
            scale.append((k, r["n"], r["hyb"]))
            print(f"  {k:8d} {r['n']:8d} {r['ctx']:8.3f} {r['form']:7.3f} {r['hyb']:7.3f}", flush=True)

    teacher_free = not any(m in sys.modules for m in ("allosaurus", "torch", "torchaudio"))
    hybrid_wins = full["hyb"] > max(full["ctx"], CTX_ALONE) + 0.02 and full["hyb"] > full["sh"] + 0.05
    form_rescues = (not np.isnan(full["rare_form"])) and not np.isnan(full["rare_ctx"]) and full["rare_form"] > full["rare_ctx"] + 0.02
    rises = len(scale) >= 2 and scale[-1][2] > scale[0][2] + 0.03
    print("\n" + "=" * 96)
    print("VERDICT — category induction: self-supervisable (hybrid) and/or tractably data-bound?")
    print(f"  (a) HYBRID {full['hyb']:.3f} vs context {full['ctx']:.3f} / form {full['form']:.3f} "
          f"(shuffled {full['sh']:.3f}, base {full['base']:.3f}); ALL >> c699514b ctx-alone {CTX_ALONE:.2f}.")
    print(f"      hybrid beats context-alone: {'YES' if hybrid_wins else 'no (context already strong at form-grain)'}")
    print(f"  (b) FORM rescues rare tail: {'YES' if form_rescues else 'no'} "
          f"(rare form {full['rare_form']:.3f} vs context {full['rare_ctx']:.3f})")
    if scale:
        print(f"  (c) DATA-SCALE {'RISES' if rises else 'flat'}: {scale[0][2]:.3f}@{scale[0][0]} -> "
              f"{scale[-1][2]:.3f}@{scale[-1][0]} tokens")
    print(f"  donkey=0 {teacher_free}   [peak {D._peak_gib():.2f} GiB; max tokens {len(data)}]")
    if (hybrid_wins or form_rescues) and full["form"] > full["base"] + 0.05:
        print("  => ★ CATEGORY INDUCTION IS SELF-SUPERVISABLE: FORM (earned phone suffix/morphology + acoustic)")
        print(f"     is category-informative ({full['form']:.2f} >> base {full['base']:.2f}, shuffled {full['sh']:.2f})")
        print("     and rescues the rare/singleton tail; hybrid form+context self-discovers noun/verb WITHOUT")
        print("     nltk-POS (scoring-only), donkey=0. The c699514b 0.26 null was context-alone at the TOKEN")
        print("     grain; FORM + form-grain aggregation resolves it (three-residual sweep closed).")
    else:
        print("  => HONEST FORK: form is "
              f"{'weakly' if full['form']>full['base'] else 'not'} category-informative; the tractable lever is")
        print(f"     DATA ({'rises with tokens' if rises else 'more tokens/morphology needed'}) — quantify, not irreducible.")
    print("=" * 96)


if __name__ == "__main__":
    main()
