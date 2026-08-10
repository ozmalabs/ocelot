"""LIVE DEMONSTRATION — a SELF-TRAINING reflex net on a REAL task.

Run: PYTHONPATH=. python scripts/reflex_selftrain_reader_task.py

Not the toy x². The task is a genuine comprehension decision: reproduce
the REAL deep reader's `(kind, focus)` speech-act verdict (statement vs
question, and the wh-focus reason/place/thing/manner/time/selection) from
real sentence features. The reflex net learns it purely by COLLAPSE and
SURPRISE — `net_collapse_step` (predict → surprise = target − prediction
→ collapse the weights toward it), from a ZERO readout, on the reader's
OWN labels. No external optimizer, no gradient library, no batch solve.

Then: held-out accuracy (did it learn the reader's decision?) and speed
(the net serves the decision in µs vs the reader's ms) — the reflex cache
self-trained on the real task.
"""
from __future__ import annotations

import time

import numpy as np

from substrate_rs import _native
from substrate.world_adapter import WorldAdapter
from domains import comprehend_text as ct

_CUES = ["why", "where", "what", "how", "when", "which", "who",
         "is", "are", "do", "does", "did", "can", "the", "a"]


def _features(text):
    """A real, extractable sentence feature vector (structural cues), the
    net's input. Mechanical tokenization — the smallest graph token."""
    t = text.lower()
    words = [w.strip(".,?!;:'\"") for w in t.split()]
    first = words[0] if words else ""
    feats = [1.0 if "?" in text else 0.0]
    feats += [1.0 if first == c else 0.0 for c in _CUES]      # first-word cue
    feats += [1.0 if c in words else 0.0 for c in _CUES]      # anywhere cue
    feats.append(min(len(words), 12) / 12.0)                  # length
    return feats


def _verdict(wa, text):
    c = ct.comprehend_text(wa, text)
    return f"{c.kind}:{c.focus}"


def _build_net(s, in_dim, out_dim, hidden=200, seed=1):
    rng = np.random.default_rng(seed)
    asm = s.add_node("NetworkAssemblage", {"input_dim": in_dim, "output_dim": out_dim})
    sid = s.add_node("AssemblageStep", {"order": 0, "dim_behavior": "transform"})
    s.add_edge(asm, "has_step", sid, {})
    w = {"W1": (rng.standard_normal((hidden, in_dim)) * 1.2).tolist(),
         "b1": (rng.standard_normal(hidden) * 0.3).tolist(),
         "W2": [[0.0] * hidden for _ in range(out_dim)],       # ZERO readout
         "b2": [0.0] * out_dim}
    for role, dat in w.items():
        wt = s.add_node("WeightTensor", {"role": role, "data": dat})
        s.add_edge(sid, "has_weight", wt, {})
    return asm


def _fresh():
    s = _native.Substrate()
    for a in ("NetworkAssemblage", "AssemblageStep", "WeightTensor"):
        for b in ("NetworkAssemblage", "AssemblageStep", "WeightTensor"):
            for et in ("has_step", "has_weight"):
                s.add_production({"src": {"type": a, "var": "s"}, "edge_type": et,
                                  "tgt": {"type": b, "var": "t"}, "where": None,
                                  "weight": {"type": "Lit", "value": 1.0}, "provenance": "d"})
    return s


def _nid(x):
    return x.value if hasattr(x, "value") else int(x)


def _corpus():
    statements = [
        "The moon orbits the earth.", "A cat sat on the mat.",
        "Rain falls from the clouds.", "Saturn has many rings.",
        "The dog chased the ball.", "Water boils at a hundred degrees.",
        "Birds fly south in winter.", "The sun rises in the east.",
        "Glass breaks when it is dropped.", "Trees lose their leaves in autumn.",
        "The river flows to the sea.", "Ice melts in the heat.",
    ]
    questions = [
        "Why did the dog bark?", "Where are you going?", "What is the capital?",
        "How does a bird fly?", "When does the store open?", "Which road is faster?",
        "Why is the sky blue?", "Where did she leave the keys?",
        "What causes the tides?", "How do plants grow?", "When will it rain?",
        "Which book is better?", "Why does ice float?", "Where is the station?",
        "What time is it?", "How far is the moon?",
    ]
    return statements, questions


def _hr(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


def main():
    _hr("BOOT the real reader + label a corpus with ITS OWN verdicts")
    wa = WorldAdapter()
    statements, questions = _corpus()
    data = []
    for txt in statements + questions:
        data.append((txt, _features(txt), _verdict(wa, txt)))
    classes = sorted({v for _, _, v in data})
    cidx = {c: i for i, c in enumerate(classes)}
    print(f"  {len(data)} sentences; the reader's verdict classes: {classes}")

    rng = np.random.default_rng(0)
    idx = rng.permutation(len(data))
    split = int(0.7 * len(data))
    train = [data[i] for i in idx[:split]]
    test = [data[i] for i in idx[split:]]
    in_dim = len(data[0][1])
    out_dim = len(classes)

    _hr("SELF-TRAIN a reflex net (zero readout) by COLLAPSE + SURPRISE")
    s = _fresh()
    asm = _build_net(s, in_dim, out_dim)
    nid = _nid(asm)

    def onehot(v):
        y = [0.0] * out_dim
        y[cidx[v]] = 1.0
        return y

    def accuracy(rows):
        ok = 0
        for _, f, v in rows:
            pred = int(np.argmax(s.net_forward(nid, f)))
            ok += (pred == cidx[v])
        return ok / len(rows)

    print(f"  {'epoch':>5}  {'mean surprise':>14}  {'train acc':>10}  {'held-out acc':>12}")
    for epoch in range(400):
        eta = 0.5 / (1.0 + 0.02 * epoch)
        order = list(train)
        rng.shuffle(order)
        sur = [s.net_collapse_step(nid, f, onehot(v), eta) for _, f, v in order]
        if epoch in (0, 4, 19, 49, 99, 199, 399):
            print(f"  {epoch:>5}  {np.mean(sur):>14.5f}  {accuracy(train):>10.2%}  "
                  f"{accuracy(test):>12.2%}")

    _hr("SPEED: the self-trained net vs the real reader, per sentence")
    def _t(fn, it):
        for _ in range(50):
            fn()
        t = time.perf_counter()
        for _ in range(it):
            fn()
        return (time.perf_counter() - t) / it
    sample = test[0][0]
    fsample = _features(sample)
    t_net = _t(lambda: s.net_forward(nid, fsample), 3000)
    t_read = _t(lambda: ct.comprehend_text(wa, sample), 300)

    _hr("VERDICT")
    print(f"  A reflex net with a ZERO readout trained ITSELF — by surprise-"
          f"driven collapse, on the")
    print(f"  reader's own {out_dim}-way (kind, focus) verdicts — to "
          f"{accuracy(test):.0%} held-out accuracy on a REAL")
    print(f"  comprehension decision. No external optimizer, no gradients, no "
          f"batch solve.")
    print(f"  It serves the decision in {t_net*1e6:.1f} µs vs the reader's "
          f"{t_read*1e3:.2f} ms  ({t_read/t_net:,.0f}x faster).")
    print(f"\n  (Honest: small corpus ({len(test)} held-out); the (kind,focus) "
          f"verdict is cue-driven, so it's a")
    print(f"   learnable regularity — exactly what a reflex cache is for. "
          f"comprehend_text is the CHEAP")
    print(f"   parse path; the net caches its NUMERIC (kind,focus) decision — "
          f"the expensive symbolic")
    print(f"   full-turn reply needs a different representation, per the "
          f"reader-cache demo.)")

    import os
    out = os.path.join(os.path.dirname(__file__), "..", "results",
                       "reflex_selftrain_reader_verdict.log")
    with open(out, "w") as f:
        f.write(f"task: reproduce the real reader's (kind,focus) verdict, {out_dim} classes\n"
                f"self_trained_heldout_acc: {accuracy(test):.3f}\n"
                f"train_acc: {accuracy(train):.3f}\n"
                f"mechanism: net_collapse_step (surprise-driven collapse), zero-readout, no external optimizer\n"
                f"speed: net={t_net*1e6:.1f}us reader={t_read*1e3:.2f}ms speedup={t_read/t_net:.0f}x\n")
    print(f"\n  saved -> {out}")


if __name__ == "__main__":
    main()
