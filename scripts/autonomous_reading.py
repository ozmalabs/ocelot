"""AUTONOMOUS READING INVESTIGATION (graph-native) — the agent drives its own reading frontiers.

Wires the reading faculties into the agent's existing investigation loop (gap_prioritiser). Each reading
capability is banked as a MeasuredCapability (its current value + a target); the agent's native score
Term ranks the open gaps by shortfall x payoff and PICKS a frontier; the graph names the Operator that
investigates it (investigated_by edge); the loop dispatches the matching reading runner, MEASURES the
capability, banks the result, and marks the frontier investigated so the next pick moves on. The DECISION
(which reading frontier next) is the graph's Term; the host only dispatches the runner the graph names
and writes the number back — exactly the role it plays in the speech loop.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.autonomous_reading [iters]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs
from domains import gap_prioritiser as gp
from domains.investigation_operators import wire_operators, operator_for_axis
from domains.reading_runners import RUNNERS

SEP = "=" * 92

# The reading faculties as graph DATA (Operator nodes): name, the runner that measures it, the capability
# keywords it investigates, its metric + target. The agent's self-knowledge, not a Python branch.
READING_OPS = [
    {"name": "grapheme_recognition", "runner": "grapheme",
     "keywords": ["grapheme", "one-shot", "handwriting", "omniglot", "shape recognition", "symbol"],
     "metric": "recognition_accuracy", "target": 0.85},
    {"name": "word_lexicon", "runner": "word",
     "keywords": ["word", "lexicon", "whole-word", "spelling", "vocabulary"],
     "metric": "word_accuracy", "target": 0.95},
    {"name": "viterbi_lm", "runner": "viterbi",
     "keywords": ["viterbi", "language model", "sequence", "lattice", "bigram", "decode"],
     "metric": "letter_accuracy", "target": 0.90},
    {"name": "cross_modal", "runner": "cross_modal",
     "keywords": ["cross-modal", "phoneme", "reading aloud", "grapheme-phoneme", "speech"],
     "metric": "read_aloud_accuracy", "target": 0.90},
]

# The reading capabilities the agent currently holds, with a measured value below their target (room to
# investigate). Banked as MeasuredCapability nodes; the synthesis Rule re-opens each as a gap.
SEED_CAPS = [
    (["grapheme one-shot handwriting recognition"], 0.40, 0.85, "recognition_accuracy"),
    (["whole-word lexicon spelling vocabulary decode"], 0.50, 0.95, "word_accuracy"),
    (["viterbi sequence language model lattice decode"], 0.42, 0.90, "letter_accuracy"),
    (["cross-modal grapheme-phoneme reading aloud speech"], 0.55, 0.90, "read_aloud_accuracy"),
]


def main():
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    print(SEP)
    print("AUTONOMOUS READING INVESTIGATION (graph-native): the agent ranks its reading frontiers by its own")
    print("score Term, picks one, dispatches the runner the GRAPH names, measures, banks, and re-ranks.")
    print(SEP)

    s = srs.Substrate()
    s.add_production({"src": {"type": "CapabilityAxis", "var": "a"}, "edge_type": "investigated_by",
                      "tgt": {"type": "Operator", "var": "b"}, "provenance": "autonomous_reading"})
    for spec in READING_OPS:                                       # mint the reading faculties as Operator nodes
        s.add_node("Operator", {"name": spec["name"], "runner": spec["runner"], "metric": spec["metric"],
                                "target": float(spec["target"]), "keywords": list(spec["keywords"])})
    for keys, measured, target, metric in SEED_CAPS:               # bank the current reading capabilities
        gp.record_measured_capability(s, keys, measured=measured, target=target, metric=metric, fresh=False)

    print(f"\n  {len(READING_OPS)} reading faculties, {len(SEED_CAPS)} capabilities banked. Running {iters} self-"
          f"selected investigations:\n", flush=True)
    investigated = []
    for it in range(iters):
        for ax in list(s.nodes("CapabilityAxis")):                 # recompute the gap set from the LIVE measurements
            s.remove_node(ax)                                      # (met capabilities mint no axis -> they close)
        for mc in s.nodes(gp.MEASURED_TYPE):
            s.set_attr(mc, "synth_pending", 1)
        gp.synthesise_builtinsufficient_gaps(s)                    # re-open below-target capabilities as gaps
        picked = gp.pick_frontier(s)                               # the agent's PICK (native score Term)
        if picked is None:
            print(f"  iter {it+1}: no open reading frontier — every target met."); break
        wire_operators(s)                                          # graph names the operator per axis
        op = operator_for_axis(s, picked["axis_id"])
        if op is None or op.get("runner") not in RUNNERS:
            print(f"  iter {it+1}: picked {picked['capability_keys']} but no runner wired."); break
        runner = RUNNERS[op["runner"]]
        sf = picked.get("shortfall", picked["score"] / 1e9)
        measured = runner(s, picked, op)                           # dispatch: MEASURE the chosen faculty
        gp.record_measured_capability(s, picked["capability_keys"], measured=measured,
                                      target=float(op["target"]), metric=op["metric"], fresh=False)
        investigated.append((op["name"], measured))
        met = "MET (closes)" if measured >= float(op["target"]) else "still short"
        print(f"  iter {it+1}:  PICKED '{op['name']}'  (target {op['target']})  -> dispatched runner '{op['runner']}'"
              f"  -> measured {op['metric']} = {measured:.3f}  [{met}]", flush=True)

    distinct = len({n for n, _ in investigated})
    print(f"\n  {SEP[:88]}")
    print(f"  {len(investigated)} investigations, {distinct} DISTINCT reading frontiers self-selected and measured")
    print(f"  end-to-end — no per-experiment script written by hand. The pick is the agent's native score Term;")
    print(f"  the dispatch is the graph's investigated_by edge; the host only ran the runner the graph named.")
    print(f"  Reading is now wired into the autonomous investigation loop, beside speech.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
