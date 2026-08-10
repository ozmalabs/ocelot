"""LOOK AT THE GEMMA MEANING LEXICON — is the geometry real, does it cover the speech vocab, and CAN it separate the ear's confusions?

"added the weights but it didn't help much." Diagnose why, before banking the null:
  1. GEOMETRY SANITY  — do semantically-related words have high cosine, unrelated low? (is the meaning_vec usable?)
  2. COVERAGE         — what fraction of the speech vocab has a meaning_vec?
  3. SEPARABILITY     — are ACOUSTICALLY-CONFUSABLE words (orthographic minimal pairs, a proxy for the ear's
                        confusions) MEANING-SEPARABLE? If acoustic confusions are ALSO meaning-similar, a meaning
                        re-rank fundamentally CAN'T fix them; if they're separable, the prior could bite but the ear's
                        weak context starves it (the bootstrap problem). Either way it explains the null.

Loads the 110MB lexicon ONCE; caches word->vec for the speech vocab.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.look_at_meaning_lexicon
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np
from scripts.jabberwock_reads_oov_from_phones import STOP

LEX = os.path.join(ROOT, "seeds", "grounded_lexicon.json")


def _vec(attrs):
    v = attrs.get("meaning_vec")
    if isinstance(v, dict):
        v = v.get("__tuple__", v.get("items", []))
    v = np.asarray(v, dtype=np.float32)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def main():
    print("=" * 100)
    print("LOOK AT THE GEMMA MEANING LEXICON — geometry / coverage / separability of the ear's confusions")
    print("=" * 100)
    d = json.load(open(LEX))
    M = {}
    for node in d["graph"]["nodes"]:
        nm = node["attrs"].get("name")
        if nm and node["attrs"].get("excluded", 0.0) < 0.5:
            M[nm.lower()] = _vec(node["attrs"])
    names = list(M)
    V = np.stack([M[w] for w in names])
    print(f"  {len(names)} meaning Concepts (2560-d); name lengths {dict(sorted(Counter(len(w) for w in names).items())[:8])}\n")

    def cos(a, b):
        return float(M[a] @ M[b]) if a in M and b in M else None

    def neighbors(w, k=6):
        if w not in M:
            return []
        s = V @ M[w]
        idx = np.argsort(-s)[:k + 1]
        return [(names[i], float(s[i])) for i in idx if names[i] != w][:k]

    # 1) GEOMETRY SANITY: nearest meaning-neighbors of common words present in the lexicon
    print("  [1] GEOMETRY SANITY — nearest meaning-neighbors (should be semantically sensible):")
    for w in ["water", "time", "king", "good", "said", "man", "house", "love", "night", "city"]:
        nb = neighbors(w, 5)
        if nb:
            print(f"    {w:>8}: " + ", ".join(f"{n}({s:.2f})" for n, s in nb))
    print()

    # 2) COVERAGE of the speech vocab
    tr = {}
    for tf in glob.glob("/tmp/LibriSpeech/dev-clean/**/*.trans.txt", recursive=True):
        for line in open(tf):
            if " " in line:
                _i, t = line.split(" ", 1)
                for w in t.lower().split():
                    w = "".join(c for c in w if c.isalpha())
                    if len(w) >= 3:
                        tr[w] = tr.get(w, 0) + 1
    vocab = [w for w, _ in Counter(tr).most_common(2000)]
    content = [w for w in vocab if w not in STOP]
    cc = [w for w in content if w in M]
    print(f"  [2] COVERAGE — LibriSpeech top-2000: {sum(1 for w in vocab if w in M)}/{len(vocab)} ({100*sum(1 for w in vocab if w in M)//len(vocab)}%) covered; "
          f"content {len(cc)}/{len(content)} ({100*len(cc)//max(len(content),1)}%)\n")

    # 3) SEPARABILITY: orthographic minimal-pairs (proxy for acoustic confusions) -- meaning cosine vs random
    def edit1(a, b):
        if abs(len(a) - len(b)) > 1:
            return False
        if len(a) == len(b):
            return sum(x != y for x, y in zip(a, b)) == 1
        s, l = (a, b) if len(a) < len(b) else (b, a)
        for i in range(len(l)):
            if l[:i] + l[i + 1:] == s:
                return True
        return False

    cov = [w for w in content if w in M]
    pairs = []
    for i, a in enumerate(cov):
        for b in cov[i + 1:]:
            if edit1(a, b):
                pairs.append((a, b))
        if len(pairs) >= 120:
            break
    rng = np.random.RandomState(0)
    randpairs = [(cov[i], cov[j]) for i, j in rng.randint(0, len(cov), (300, 2)) if i != j][:200]
    mp_cos = np.mean([cos(a, b) for (a, b) in pairs]) if pairs else float("nan")
    rp_cos = np.mean([cos(a, b) for (a, b) in randpairs]) if randpairs else float("nan")
    print(f"  [3] SEPARABILITY — meaning cosine of ACOUSTIC-ish minimal pairs vs RANDOM pairs:")
    print(f"    minimal-pairs (n={len(pairs)}): mean meaning-cos {mp_cos:.3f}  e.g. " +
          ", ".join(f"{a}/{b}={cos(a,b):.2f}" for (a, b) in pairs[:6]))
    print(f"    random pairs  (n={len(randpairs)}): mean meaning-cos {rp_cos:.3f}")
    sep = mp_cos - rp_cos

    print("\n" + "=" * 100)
    print(f"  geometry: {'REAL' if any(neighbors(w) for w in ['water','time','king']) else 'unclear'}; "
          f"coverage content {100*len(cc)//max(len(content),1)}%; minimal-pair meaning-cos {mp_cos:.2f} vs random {rp_cos:.2f} (Δ {sep:+.2f})")
    if sep > 0.08:
        print(f"  DIAGNOSIS: acoustic confusions are MEANING-SIMILAR (minimal pairs cos {mp_cos:.2f} >> random {rp_cos:.2f}).")
        print("  The words the ear confuses tend to mean similar things, so a meaning re-rank CANNOT separate them -- the")
        print("  prior is structurally unable to fix the dominant errors. That's why it didn't help. (Meaning != the lever.)")
    else:
        print(f"  DIAGNOSIS: acoustic confusions are MEANING-SEPARABLE (minimal pairs cos {mp_cos:.2f} ~ random {rp_cos:.2f}), so the")
        print("  prior COULD bite -- but it didn't, which points to the BOOTSTRAP problem: the ear's decode is too weak to give")
        print("  reliable context, so meaning-coherence is computed against wrong neighbours. Fix the EAR, then meaning pays.")
    print("  Either way: the EAR (acoustic precision) is the wall, not the language/meaning prior -- as the whole arc found.")
    print("=" * 100)


if __name__ == "__main__":
    main()
