"""Wire the actionable win into the agent's NATIVE recogniser: recognise FSDD on
RELATIONAL features. The recognition is the agent's held machinery — acquire_sign
(cluster), ground_sign (label), match_sign (recognise), denoted_concepts (read the
grounded digit). The ONLY thing this shell supplies is the world-adapter plumbing:
held cochlea features (substrate_rs.speech._audio) optionally passed through the held
relational transform (Substrate.shape_signature). No decision lives here — the agent
clusters, grounds, and matches; we feed features and read its verdict.

A/B: identical native pipeline, transform = identity (raw cochlear) vs relational
(shape_signature rank, centred for the cosine match). Cross-speaker held-out. The
earlier numpy control (L2 on per-digit class-means) found relational beats raw; this
TESTS that end-to-end through the agent's own acquire/ground/match. RESULT: it does
NOT survive — raw beats relational (george -8%, theo -20.5%, threshold-swept + centred).
The relational "win" was an artifact of the L2-on-class-means proxy; the agent's real
cosine-clustering recogniser prefers raw cochlear. Wiring through the agent's actual
machinery refuted the proxy — exactly why you wire it through the agent.

Run: python scripts/fsdd_relational_recognize.py [test_speaker] [n_per] [threshold]
"""
from __future__ import annotations
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from substrate_rs import Substrate
import substrate_rs.speech as sp
from substrate_rs.speech import _audio
from scripts.speech_analysis_by_synthesis import load_wav, feat, DATA, FN, N_BANDS


def run(test_spk, n_per, thresh, relational):
    files = []
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < n_per:
            files.append((os.path.join(DATA, fn), int(m.group(1)), m.group(2)))

    s = Substrate()
    _audio.seed_audio_grammar(s)
    sp.seed_speech_grammar(s)           # register AcousticLexicon / AcousticSign in Γ
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)
    lex = sp.open_lexicon(s, name="fsdd", match_threshold=thresh)
    # digit Concepts the agent grounds signs to.
    concept = {d: s.add_node("Concept", {"name": f"digit_{d}"}) for d in range(10)}

    def transform(f):
        v = f.flatten().astype(np.float32)
        if relational:                      # held relational rank — the cross-speaker lever
            v = np.asarray(s.shape_signature([float(x) for x in v]), np.float32)
            v = v - v.mean()                # centre so the native COSINE match == rank
                                            # correlation (cosine on uncentred ranks saturates)
        return v

    # vote bookkeeping: which digit a sign was grounded to, how often (world-adapter
    # counting; the SIGN identity + grounding are the agent's).
    votes: dict = {}

    train = [f for f in files if f[2] != test_spk]
    test = [f for f in files if f[2] == test_spk]

    # TRAIN: the agent acquires a sign per utterance (merging similar) + grounds it.
    for path, digit, _spk in train:
        samples, fs = load_wav(path)
        v = transform(feat(s, bank, samples, fs))
        sign, _is_new = sp.acquire_sign(s, lex, v, threshold=thresh)
        sp.ground_sign(s, sign, concept[digit])
        votes.setdefault(sign, {}).__setitem__(
            digit, votes.get(sign, {}).get(digit, 0) + 1)

    # RECOGNISE: the agent matches; we read the matched sign's majority-grounded digit.
    correct = matched = 0
    for path, digit, _spk in test:
        samples, fs = load_wav(path)
        v = transform(feat(s, bank, samples, fs))
        sign, _dist = sp.match_sign(s, lex, v, threshold=thresh)
        if sign is None or sign not in votes:
            continue                        # agent declines (no admissible match)
        matched += 1
        pred = max(votes[sign], key=votes[sign].get)
        correct += (pred == digit)
    n = len(test)
    n_signs = len(sp.lexicon_signs(s, lex))
    return correct, n, matched, n_signs


def main():
    test_spk = sys.argv[1] if len(sys.argv) > 1 else "george"
    n_per = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    print("=" * 78)
    print(f"FSDD recognition through the AGENT'S NATIVE recogniser (acquire/ground/match)")
    print(f"  held-out speaker={test_spk}  {n_per}/digit/speaker  (threshold swept per rep)")
    print("=" * 78)
    # cosine saturates on rank vectors, so each representation needs its own
    # match_threshold band — sweep both, report each rep's best overall accuracy.
    grids = {
        False: [0.55, 0.65, 0.72, 0.78, 0.85],          # raw cochlear
        True:  [0.30, 0.50, 0.65, 0.78, 0.88],          # centred relational (correlation)
    }
    best = {}
    for relational in (False, True):
        tag = "RELATIONAL" if relational else "raw cochlear"
        print(f"\n  {tag}:")
        bestacc = -1.0
        for th in grids[relational]:
            c, n, m, ns = run(test_spk, n_per, th, relational)
            print(f"    thr={th:<5} {c}/{n} = {c/n:5.1%}   (matched {m}/{n}; {ns} signs)")
            if c / n > bestacc:
                bestacc = c / n
        best[relational] = bestacc
    print("=" * 78)
    print(f"  BEST overall accuracy — raw {best[False]:.1%}  vs  RELATIONAL "
          f"{best[True]:.1%}   (delta {best[True]-best[False]:+.1%})")
    print("=" * 78)


if __name__ == "__main__":
    main()
