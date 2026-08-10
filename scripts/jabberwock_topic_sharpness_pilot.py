"""TOPIC-SHARPNESS PILOT — the agent's pre-build ABORT GATE for the consolidation decode.

Move (B) re-ranks the realigned top-K by P(word | S), S = chapter/document TOPIC inferred from co-text. Before building
the full decode, the agent pre-committed a gate: median over targets of log2 P(target|S) - log2 P(target) must be
>= 0.5 BITS (topic boosts the true word >= ~1.4x over marginal), else S is too flat -> ABORT, don't report a null
dressed as a finding. This measures exactly that, text-only + fast, on LibriSpeech dev-clean.

Two boosts per target occurrence:
  ORACLE  = log2 P_loo(w | its true chapter) - log2 P(w)   [leave-one-utterance-out doc, the topical CEILING]
  DETECT  = log2 P_loo(w | argmax-chapter from co-text) - log2 P(w)   [topic INFERRED from utterance co-text minus
            the target token -- the realistic, anti-leak detector]
Reported for the 24 held-out TARGETS (frequent content words = the actual candidate set) AND a RARE-word contrast
(corpus count in [3,12]) -- because frequent words are the LEAST topical, so the gate may say "abort for THIS set,
build only if the candidate set is rare content words".

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_topic_sharpness_pilot
"""
from __future__ import annotations

import glob
import math
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.phonebank import _meta
from scripts.jabberwock_reads_oov_from_phones import STOP

DEV = "/home/matt/data/LibriSpeech/dev-clean"
ALPHA = 0.1                 # add-alpha smoothing for P(w|doc)
GATE_BITS = 0.5            # the agent's pre-committed abort threshold
MAX_OCC = 60               # cap occurrences per target word (speed)


def content(toks):
    return [w for w in toks if w.isalpha() and len(w) >= 3 and w not in STOP]


def main():
    print("=" * 100)
    print("TOPIC-SHARPNESS PILOT — does knowing the topic boost the true word >= 0.5 bits? (the agent's abort gate)")
    print("=" * 100)

    # chapters = documents; each = list of utterances (content-word token lists)
    docs = defaultdict(list)
    for tf in glob.glob(os.path.join(DEV, "**", "*.trans.txt"), recursive=True):
        chap = os.path.basename(tf)[:-len(".trans.txt")]      # spk-chap
        for line in open(tf):
            line = line.strip()
            if " " not in line:
                continue
            _id, text = line.split(" ", 1)
            docs[chap].append(content(text.lower().split()))
    chaps = list(docs)
    gcount = Counter()
    dcount = {c: Counter() for c in chaps}
    for c in chaps:
        for utt in docs[c]:
            gcount.update(utt); dcount[c].update(utt)
    N_g = sum(gcount.values()); V = len(gcount)
    dN = {c: sum(dcount[c].values()) for c in chaps}
    print(f"  {len(chaps)} chapters (documents); {N_g} content tokens; vocab {V}\n", flush=True)

    def logP(w):
        return math.log2(gcount[w] / N_g) if gcount[w] > 0 else math.log2(0.5 / N_g)

    def logP_doc(w, c, minus=None):
        """P(w|doc c) add-alpha, leave-one-utterance-out via subtracting `minus` Counter."""
        n = dcount[c][w] - (minus[w] if minus else 0)
        tot = dN[c] - (sum(minus.values()) if minus else 0)
        return math.log2((n + ALPHA) / (tot + ALPHA * V))

    def detect(cotext):
        """argmax chapter by co-text log-likelihood (smoothed); cotext = Counter of content words (target excised)."""
        best, bs = None, -1e18
        for c in chaps:
            s = 0.0
            for w, k in cotext.items():
                s += k * math.log((dcount[c][w] + ALPHA) / (dN[c] + ALPHA * V))
            if s > bs:
                bs, best = s, c
        return best

    def measure(wordset, label):
        oracle, detected, n = [], [], 0
        for c in chaps:
            for utt in docs[c]:
                uc = Counter(utt)
                for w in set(utt) & wordset:
                    if n >= MAX_OCC * len(wordset):
                        break
                    minus = uc                       # leave THIS utterance out of the doc estimate
                    base = logP(w)
                    oracle.append(logP_doc(w, c, minus) - base)
                    co = Counter(uc); co[w] -= 1
                    if co[w] <= 0: del co[w]
                    if not co:
                        continue
                    chat = detect(co)
                    detected.append(logP_doc(w, chat, uc if chat == c else None) - base)
                    n += 1
        med = lambda a: sorted(a)[len(a) // 2] if a else float("nan")
        frac = lambda a: sum(x >= GATE_BITS for x in a) / len(a) if a else 0.0
        print(f"  {label}: {len(detected)} occ | ORACLE median {med(oracle):+.2f} bits (>= {GATE_BITS}: {frac(oracle)*100:.0f}%)"
              f" | DETECTED median {med(detected):+.2f} bits (>= {GATE_BITS}: {frac(detected)*100:.0f}%)")
        return med(detected)

    _spk, targets, _clips = _meta()
    tset = set(targets) & set(gcount)
    print(f"  held-out TARGETS ({len(tset)}): {sorted(tset)}\n", flush=True)
    print("  median log2 P(w|topic) - log2 P(w), per occurrence:\n", flush=True)
    t_det = measure(tset, "TARGETS (frequent content words = the 100-way candidate set)")

    rare = {w for w, c in gcount.items() if 3 <= c <= 12 and w.isalpha() and len(w) >= 4}
    # cap rare set size for the detector cost
    rare = set(sorted(rare)[:200])
    r_det = measure(rare, "RARE contrast (corpus count 3-12)              ")

    print("\n" + "=" * 100)
    print(f"  gate = DETECTED median >= {GATE_BITS} bits.  TARGETS detected {t_det:+.2f} | RARE detected {r_det:+.2f}")
    if t_det >= GATE_BITS:
        print(f"  GATE PASS for the target set ({t_det:+.2f} >= {GATE_BITS}): topic converts recall on the actual 100-way")
        print("  candidate words -> BUILD the full fused decode (realigned lattice + topic-prior re-rank + shuffle control).")
    elif r_det >= GATE_BITS:
        print(f"  GATE: targets too FLAT ({t_det:+.2f} < {GATE_BITS}) — the held-out targets are FREQUENT content words (least")
        print(f"  topical) — BUT rare words clear it ({r_det:+.2f}). The honest move: build only if the candidate set is")
        print("  RARE content words (the BPL-style regime), not these frequent targets. Re-pin the candidate set first.")
    else:
        print(f"  GATE FAIL (targets {t_det:+.2f}, rare {r_det:+.2f}, both < {GATE_BITS}): no natural topic S on this set is")
        print("  sharp enough to convert recall. ABORT the build; report the flat-S finding (the agent's pre-commitment).")
    print("=" * 100)


if __name__ == "__main__":
    main()
