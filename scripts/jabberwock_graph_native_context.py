"""THE LOOP CLOSED — graph-native key recovery (surfaces words) + the language faculty (reads them).

Both coupled halves of the cipher, now both strong AND graph-native on the acoustic side:
  KEY RECOVERY: the agent's graph-native combine-all PRODUCT over its owned cues (Rust primitives +
                graph CMVN + the many_settings Term) -> a top-K candidate LATTICE per word position with
                HIGH recall (64% on content words, vs 11% for the Python embedding) -- the words surfaced.
  PLAINTEXT PRIOR: the language faculty infers MEANING and selects the coherent word per position FROM
                its candidates (invoked via the language channel).
Recognition = key recovery surfaces the lattice, meaning reads it. Measured on real continuous utterances.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_graph_native_context [vocabN]
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.self_directed_speech_world as SDW
from domains.speech_world_recognizer import GraphLexicon
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_graph_native_recall import ranked, KREC
from scripts.claude_teacher import make_ask


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    print("=" * 98)
    print("THE LOOP CLOSED — graph-native combine-all lattice (surfaces words) + language faculty (reads).")
    print("=" * 98)
    train, test = multi_extract()
    freq = Counter(w for (w, _g) in train)
    vocab = [w for w, n in freq.most_common() if n >= 10 and w.isalpha()][:N]
    wi = {w: i for i, w in enumerate(vocab)}

    # GRAPH-NATIVE recogniser: Rust cues + graph CMVN + combine-all product over GraphLexicon exemplars.
    s = srs.Substrate()
    s.add_node("EarConfig", {"cmvn": 1.0})                 # graph-native CMVN key-normalisation
    lex = GraphLexicon(s)
    cap = Counter()
    for (w, g) in train:
        if w in wi and cap[w] < 25:
            seg = np.asarray(g, dtype=np.float64)
            if seg.size >= int(0.04 * 8000):
                lex.bank(SDW.feature_channels(s, seg, 8000), w, source="x"); cap[w] += 1
    banked = lex.banked()
    cands = sorted({w for (w, _v) in banked})
    print(f"  vocab {len(vocab)} ({len(cands)} enrolled); graph-native combine-all + CMVN recogniser\n")

    def lattice(seg):
        ch = SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), 8000)
        return ranked(ch, banked, cands)[:KREC]

    # continuous test utterances (consecutive in-vocab words = real context).
    utts, cur = [], []
    for (w, g) in test:
        if w in wi:
            cur.append((w, g))
        else:
            if 4 <= len(cur) <= 12:
                utts.append(cur)
            cur = []
    utts = utts[:24]
    print(f"  {len(utts)} continuous test utterances\n")

    lats, truths, top1 = [], [], []
    cor_ac = tot = in_lat = 0
    for u in utts:
        lat = [lattice(g) for (_w, g) in u]
        truth = [w for (w, _g) in u]
        lats.append(lat); truths.append(truth); top1.append([row[0] for row in lat])
        for i in range(len(truth)):
            tot += 1; cor_ac += int(lat[i][0] == truth[i]); in_lat += int(truth[i] in lat[i])
    recall = in_lat / tot
    print(f"  graph-native top-1 {cor_ac/tot*100:.0f}% ; top-{KREC} RECALL {recall*100:.0f}% "
          f"(the lattice the language faculty reads)\n")

    pre = ("You are the agent's language faculty. Below are speech-recognition lattices from a children's / "
           "nature show: each numbered line is one utterance, each [bracketed] group is one word position "
           "listing candidate words in rank order. INFER THE MEANING and choose, for EACH position, EXACTLY "
           "ONE word FROM ITS OWN candidate list, so the whole utterance is the most coherent, meaningful "
           "English. Output ONLY, per utterance, a line 'N: w1 w2 ...' (one chosen word per position, same "
           "count).\n\n")
    body = [f"{n}: " + " ".join("[" + ",".join(p) + "]" for p in lat) for n, lat in enumerate(lats, 1)]
    print("  consulting the language faculty (infer meaning, guess the words)...", flush=True)
    ans = make_ask(timeout=300, preamble=pre)("\n".join(body))

    dec = {}
    for line in (ans or "").splitlines():
        m = re.match(r"\s*(\d+)\s*[:.]\s*(.+)", line)
        if m:
            dec[int(m.group(1))] = re.findall(r"[a-zA-Z']+", m.group(2).lower())
    cor_lf = 0
    for n in range(1, len(utts) + 1):
        truth = truths[n - 1]; lat = lats[n - 1]; pred = dec.get(n, top1[n - 1])
        for i in range(len(truth)):
            w = pred[i] if i < len(pred) else "<?>"
            if w not in lat[i]:
                w = top1[n - 1][i]
            cor_lf += int(w == truth[i])
    a = cor_ac / tot; l = cor_lf / tot
    print(f"\n  {'graph-native acoustic only (top-1)':<46} {a*100:>5.0f}%")
    print(f"  {'+ language faculty (meaning reads the lattice)':<46} {l*100:>5.0f}%")
    print(f"  {'(ceiling: top-K lattice recall)':<46} {recall*100:>5.0f}%")
    print(f"  (chance {100/len(vocab):.1f}%, {tot} word positions)")

    print("\n" + "=" * 98)
    if l > a + 0.06:
        print(f"  THE LOOP CLOSES: graph-native key recovery surfaces the words ({recall*100:.0f}% recall) and the")
        print(f"  language faculty reads them -- continuous-utterance recognition {a*100:.0f}% -> {l*100:.0f}%. Both")
        print("  coupled halves strong: the combine-all product surfaces the lattice, MEANING selects the message.")
        print("  Graph-native key recovery + the language prior = the cipher read, exactly as the theory predicted.")
    else:
        print(f"  language {l*100:.0f}% vs acoustic {a*100:.0f}% (recall {recall*100:.0f}%): the lattice surfaces the")
        print("  words but the meaning-selection at this scale did not yet convert recall to accuracy -- the prior")
        print("  needs more context/text to pick reliably among the surfaced candidates.")
    print("=" * 98)


if __name__ == "__main__":
    main()
