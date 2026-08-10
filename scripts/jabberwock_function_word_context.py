"""GIVE THE FUNCTION WORDS MORE CONTEXT — content anchors let the prior fill the weak slots.

Function words (the/a/and/is/of/to/it...) are acoustically tiny and the combine-all product surfaces
them only ~27% — but they are the MOST predictable from grammar. The earlier loop fragmented utterances
at every out-of-vocab word, so the language faculty saw bare function-word strings with NO content
anchors. The fix: decode WHOLE sentences. The recogniser surfaces content words at 64% (strong, high-recall
lattices) -- those anchor the grammar, and the language faculty fills the weak function-word slots from
their position. Same graph-native recogniser; the only change is CONTEXT.

Measured on real continuous utterances, on the FUNCTION-WORD positions specifically:
  no context  : acoustic top-1 of the function word alone (its weak lattice, no surroundings).
  with context: the language faculty reads the full sentence (content anchors present) and fills the slot.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_function_word_context [vocabN]
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

# closed-class function words — the prior-bound, acoustically-tiny slots.
FUNCTION = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be", "been", "am",
    "to", "of", "in", "on", "at", "by", "for", "with", "from", "as", "it", "its", "this",
    "that", "these", "those", "he", "she", "they", "them", "him", "her", "his", "we", "us",
    "you", "your", "i", "me", "my", "our", "do", "does", "did", "has", "have", "had", "not",
    "no", "so", "if", "then", "than", "there", "here", "what", "when", "where", "who", "how",
    "all", "out", "up", "down", "off", "into", "over", "can", "will", "would", "could",
}


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    print("=" * 98)
    print("GIVE THE FUNCTION WORDS MORE CONTEXT — content anchors let the prior fill the weak slots.")
    print("=" * 98)
    train, test = multi_extract()
    freq = Counter(w for (w, _g) in train)
    vocab = [w for w, n in freq.most_common() if n >= 8 and w.isalpha()][:N]
    wi = {w: i for i, w in enumerate(vocab)}

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
    nfun = sum(1 for w in vocab if w in FUNCTION)
    print(f"  vocab {len(vocab)} ({nfun} function words, {len(cands)} enrolled); graph-native combine-all + CMVN\n")

    def lattice(seg):
        ch = SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), 8000)
        return ranked(ch, banked, cands)[:KREC]

    # LONGER whole-sentence utterances (consecutive in-vocab, up to 18) — content words present as anchors.
    utts, cur = [], []
    for (w, g) in test:
        if w in wi:
            cur.append((w, g))
        else:
            if 6 <= len(cur):
                utts.append(cur[:18])
            cur = []
    utts = utts[:30]
    nfp = sum(1 for u in utts for (w, _g) in u if w in FUNCTION)
    print(f"  {len(utts)} whole-sentence utterances; {nfp} function-word positions\n")
    if nfp < 20:
        print("  too few function-word positions."); return

    lats, truths, top1 = [], [], []
    for u in utts:
        lat = [lattice(g) for (_w, g) in u]
        lats.append(lat); truths.append([w for (w, _g) in u]); top1.append([row[0] for row in lat])

    # CEILINGS: truth-in-lattice recall, split function vs content (what the anchors can support).
    fp_total = fp_nocontext = fp_recall = 0
    cp_total = cp_recall = 0
    for n in range(len(utts)):
        for i, w in enumerate(truths[n]):
            if w in FUNCTION:
                fp_total += 1
                fp_nocontext += int(top1[n][i] == w)
                fp_recall += int(w in lats[n][i])
            else:
                cp_total += 1
                cp_recall += int(w in lats[n][i])
    print(f"  ceilings: content-word top-{KREC} recall {cp_recall/max(cp_total,1)*100:.0f}% (the anchors); "
          f"function-word top-{KREC} recall {fp_recall/max(fp_total,1)*100:.0f}% (acoustically irrecoverable)\n")

    # WITH CONTEXT: the faculty reads the whole sentence; content words from candidates, but function words
    # filled FREELY FROM GRAMMAR (their acoustic lattice is noise -- grammar, not acoustics, decides them).
    pre = ("You are the agent's language faculty. Below are speech-recognition lattices from a children's / "
           "nature show: each numbered line is one whole utterance, each [bracketed] group is one word "
           "position with candidate words in rank order. The lattices for SHORT FUNCTION WORDS (the, a, and, "
           "is, of, to, it, in, on...) are unreliable noise -- you must supply the right function word FROM "
           "GRAMMAR even if it is not in that position's candidate list. For CONTENT words, choose from the "
           "candidates. INFER THE MEANING of the whole sentence and output the single most coherent, "
           "grammatical English word per position. Output ONLY, per utterance, a line 'N: w1 w2 ...' (one "
           "word per position, SAME count as the number of bracket groups).\n\n")
    body = [f"{n}: " + " ".join("[" + ",".join(p) + "]" for p in lat) for n, lat in enumerate(lats, 1)]
    print("  consulting the language faculty (content from candidates, function words from grammar)...", flush=True)
    ans = make_ask(timeout=360, preamble=pre)("\n".join(body))

    dec = {}
    for line in (ans or "").splitlines():
        m = re.match(r"\s*(\d+)\s*[:.]\s*(.+)", line)
        if m:
            dec[int(m.group(1))] = re.findall(r"[a-zA-Z']+", m.group(2).lower())
    fp_context = 0
    all_total = all_top1 = all_lf = 0
    for n in range(len(utts)):
        truth = truths[n]; lat = lats[n]; pred = dec.get(n + 1, top1[n])
        for i, w in enumerate(truth):
            cw = pred[i] if i < len(pred) else "<?>"
            # content words must come from the lattice (honest); function words may be grammar-filled.
            if w not in FUNCTION and cw not in lat[i]:
                cw = top1[n][i]
            all_total += 1; all_top1 += int(top1[n][i] == w); all_lf += int(cw == w)
            if w in FUNCTION:
                fp_context += int(cw == w)

    fnc0 = fp_nocontext / fp_total
    fnc1 = fp_context / fp_total
    print(f"\n  FUNCTION WORDS ({fp_total} positions):")
    print(f"    {'no context (weak lattice top-1)':<44} {fnc0*100:>5.0f}%")
    print(f"    {'WITH context (prior fills from grammar)':<44} {fnc1*100:>5.0f}%")
    print(f"  ALL WORDS ({all_total} positions):")
    print(f"    {'acoustic top-1':<44} {all_top1/all_total*100:>5.0f}%")
    print(f"    {'+ language faculty (whole-sentence)':<44} {all_lf/all_total*100:>5.0f}%")

    print("\n" + "=" * 98)
    if fnc1 > fnc0 + 0.08:
        print(f"  CONTEXT FILLS THE FUNCTION WORDS: the prior fills the acoustically-irrecoverable function-word")
        print(f"  slots {fnc0*100:.0f}% -> {fnc1*100:.0f}% from grammar. The acoustics can't separate the/a/and/is (recall")
        print(f"  {fp_recall/max(fp_total,1)*100:.0f}%); grammar can -- give the prior the surrounding sentence and the slots fall into place.")
    else:
        print(f"  function words {fnc1*100:.0f}% with context vs {fnc0*100:.0f}% without: grammar-fill is gated by the CONTENT")
        print(f"  anchors (recall {cp_recall/max(cp_total,1)*100:.0f}%) -- in connected speech at this scale the anchors are too weak to")
        print("  pin the grammar, so the prior has no reliable frame to fill the function words from. Recall is the lever.")
    print("=" * 98)


if __name__ == "__main__":
    main()
