"""THE LOCKED RECOGNISER ON THE FULL CONTINUOUS-UTTERANCE RECALL TEST.

The locked curated front end {cmvn_ear, vtl_formant_allpole, gammatone_flat, modspec} was selected on isolated
content-word tokens. The real deployment is CONTINUOUS speech: words segmented from running utterances, a large
vocabulary, function-word-heavy -- where the original 3-seed-cue recogniser sat at ~27% top-6 (the wall that
gated the language faculty). Does the curated recogniser lift continuous-utterance recall? Out-of-distribution
test of the curation. Seed front end vs curated front end, top-1 and top-6 recall, broken down content vs
function (the two regimes), over real continuous test utterances.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_curated_continuous_recall [vocabN]
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.self_directed_speech_world as SDW
import domains.agent_frontend as FE
from scripts.jabberwock_graph_native_recall import ranked, KREC
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_function_word_context import FUNCTION

FS = 8000
ENROL_CAP = 20


def make_substrate(curated):
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    if curated:
        FE.install_curated_frontend(s)
    else:
        FE.install_frontend(s)                          # the 3 seed cues (the original recogniser)
    return s


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    print("=" * 98)
    print("LOCKED CURATED RECOGNISER on the FULL CONTINUOUS-UTTERANCE recall test.")
    print("=" * 98)
    train, test = multi_extract()
    freq = Counter(w for (w, _g) in train)
    vocab = [w for w, n in freq.most_common() if n >= 8 and w.isalpha()][:N]
    wi = {w: i for i, w in enumerate(vocab)}

    # continuous test utterances: consecutive in-vocab words (real context).
    utts, cur = [], []
    for (w, g) in test:
        if w in wi:
            cur.append((w, np.asarray(g, dtype=np.float64)))
        else:
            if len(cur) >= 4:
                utts.append(cur)
            cur = []
    te = [(w, g) for u in utts for (w, g) in u if g.size >= int(0.04 * FS)]
    nfun = sum(1 for (w, _g) in te if w in FUNCTION)
    print(f"  vocab {len(vocab)}; {len(utts)} continuous utterances, {len(te)} word positions "
          f"({nfun} function, {len(te)-nfun} content)\n", flush=True)

    enrol_g = {}
    cap = Counter()
    for (w, g) in train:
        g = np.asarray(g, dtype=np.float64)
        if w in wi and cap[w] < ENROL_CAP and g.size >= int(0.04 * FS):
            enrol_g.setdefault(w, []).append(g); cap[w] += 1

    def run(curated):
        s = make_substrate(curated)
        banked = [(w, SDW.feature_channels(s, g, FS)) for w in enrol_g for g in enrol_g[w]]
        cands = sorted({w for (w, _v) in banked})
        agg = {"all": [0, 0, 0], "content": [0, 0, 0], "function": [0, 0, 0]}
        for (w, g) in te:
            r = ranked(SDW.feature_channels(s, g, FS), banked, cands)
            hit1, hitk = int(r[0] == w), int(w in r[:KREC])
            for key in ("all", "function" if w in FUNCTION else "content"):
                agg[key][0] += hit1; agg[key][1] += hitk; agg[key][2] += 1
        return {k: (v[0] / max(v[2], 1), v[1] / max(v[2], 1)) for k, v in agg.items()}

    print("  extracting + scoring SEED front end (3 cues)...", flush=True)
    seed = run(False)
    print("  extracting + scoring CURATED front end (4 cues)...", flush=True)
    cur_ = run(True)

    print(f"\n  {'':<12}{'SEED (3 cues)':>22}{'CURATED (4 cues)':>22}")
    print(f"  {'':<12}{'top-1':>11}{'top-6':>11}{'top-1':>11}{'top-6':>11}")
    for k in ("all", "content", "function"):
        s1, s6 = seed[k]; c1, c6 = cur_[k]
        print(f"  {k:<12}{s1*100:>10.0f}%{s6*100:>10.0f}%{c1*100:>10.0f}%{c6*100:>10.0f}%")

    print("\n" + "=" * 98)
    a_s, a_c = seed["all"][1], cur_["all"][1]
    co_s, co_c = seed["content"][1], cur_["content"][1]
    if a_c > a_s + 0.03:
        print(f"  THE CURATED RECOGNISER LIFTS CONTINUOUS-UTTERANCE RECALL: top-6 {a_s*100:.0f}% -> {a_c*100:.0f}% overall")
        print(f"  (content {co_s*100:.0f}% -> {co_c*100:.0f}%). The curated speaker-normalised + modulation front end generalises from")
        print("  isolated content words to running speech -- more of the truth is surfaced for the language faculty.")
    elif a_c >= a_s - 0.02:
        print(f"  HOLDS: curated {a_c*100:.0f}% vs seed {a_s*100:.0f}% top-6 overall (content {co_c*100:.0f}% vs {co_s*100:.0f}%) -- the curated")
        print("  front end carries over to continuous speech without regressing; function words remain the prior-bound wall.")
    else:
        print(f"  curated {a_c*100:.0f}% vs seed {a_s*100:.0f}% top-6: the isolated-word curation did not transfer to running")
        print("  speech -- continuous segmentation/coarticulation favours a different cue mix; re-curate on continuous tokens.")
    print("=" * 98)


if __name__ == "__main__":
    main()
