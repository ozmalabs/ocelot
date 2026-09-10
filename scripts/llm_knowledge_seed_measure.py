"""Block 327000 — knowledge extracted as a native CAN seed answers held-out
ENTAILMENT by substrate operations only.

The LLM's relational knowledge (adjacent is-a links) was elicited offline and
written to a seed json. Here we build a native CAN Microtheory from the
EXTRACTED edges and answer held-out entailment queries — transitive-closure
pairs at distance >= 2 that were NOT elicited — using ONLY the substrate (graph
traversal). No LLM at query time.

The anti-faking bar: the seed must DERIVE these entailments (they are not stored
edges), and it must do so BECAUSE of the graph structure. Two controls:
  DIRECT-EDGE baseline — answer only from stored edges; must FAIL the >=2-hop
    entailments (they are not stored), proving traversal adds real inference.
  SHUFFLED-GRAPH control — permute the edge targets; entailment must COLLAPSE,
    proving the real relational structure (not the node set) carries it.

Requires the seed json (model venv: `know_elicit`) and substrate_rs:
  PYTHONPATH=runners/dsl/python python3 \\
    scripts/llm_knowledge_seed_measure.py [seed.json]
"""

import sys
import json
sys.path.insert(0, ".")
import numpy as np

from substrate_rs import _native
from domains import llm_knowledge_seed as ks

SEEDS = ["seeds/can_native_reimplementation.json"]
DEFAULT_SEED = "/applications/data/model_graph_work/knowledge_seed.json"


def _accuracy(substrate, n2n, pos, neg, query):
    """query(subj, obj) -> bool. Accuracy = (positives answered yes + negatives
    answered no) / total."""
    tp = sum(1 for s, o, *_ in pos if query(substrate, n2n, s, o))
    tn = sum(1 for a, b in neg if not query(substrate, n2n, a, b))
    total = len(pos) + len(neg)
    return (tp + tn) / total, tp, tn


def _query_transitive(substrate, n2n, s, o):
    reach, _ = ks.query_transitive(substrate, n2n, s, o)
    return reach


def main():
    seed_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SEED
    d = json.load(open(seed_path))
    extracted = [tuple(e) for e in d["extracted"]]
    pos = d["entail_pos"]
    neg = [tuple(x) for x in d["entail_neg"]]
    rng = np.random.default_rng(0)

    print("=" * 74)
    print("KNOWLEDGE SEED — block 327000 (substrate-only entailment)")
    print("%d extracted edges; held-out: %d entailment positives (dist>=2, NOT"
          % (len(extracted), len(pos)))
    print(" elicited) + %d negatives; chance = 0.50; NO LLM at query time"
          % len(neg))
    print("=" * 74)

    # real seed
    s = _native.Substrate()
    mt, n2n = ks.build_knowledge_mt(s, SEEDS, extracted, relation="isa")

    acc_t, tp_t, tn_t = _accuracy(s, n2n, pos, neg, _query_transitive)
    acc_d, tp_d, tn_d = _accuracy(s, n2n, pos, neg, ks.query_direct)

    # shuffled-graph control: same nodes, permuted edge targets
    names = list(n2n.keys())
    srcs = [e[0] for e in extracted]
    tgts = [e[1] for e in extracted]
    tgts_sh = list(tgts)
    rng.shuffle(tgts_sh)
    shuffled = list(zip(srcs, tgts_sh))
    s2 = _native.Substrate()
    mt2, n2n2 = ks.build_knowledge_mt(s2, SEEDS, shuffled, relation="isa")
    acc_sh, tp_sh, tn_sh = _accuracy(s2, n2n2, pos, neg, _query_transitive)

    print("\n%-28s %-10s %-8s %-8s" % ("query mode", "accuracy", "pos-yes", "neg-no"))
    print("  %-26s %-10.2f %-8s %-8s" %
          ("SUBSTRATE transitive", acc_t, "%d/%d" % (tp_t, len(pos)),
           "%d/%d" % (tn_t, len(neg))))
    print("  %-26s %-10.2f %-8s %-8s" %
          ("direct-edge baseline", acc_d, "%d/%d" % (tp_d, len(pos)),
           "%d/%d" % (tn_d, len(neg))))
    print("  %-26s %-10.2f %-8s %-8s" %
          ("shuffled-graph control", acc_sh, "%d/%d" % (tp_sh, len(pos)),
           "%d/%d" % (tn_sh, len(neg))))

    print("\n" + "=" * 74)
    print("VERDICT:")
    print("  If SUBSTRATE transitive >> direct-edge (which cannot answer the")
    print("  >=2-hop entailments — they are not stored) AND >> shuffled-graph,")
    print("  the extracted knowledge is a WORKING graph seed: the substrate")
    print("  DERIVES entailment it was never told, by its own graph operations,")
    print("  with no LLM in the loop. That is knowledge extracted for the")
    print("  substrate's own cognition, not a lookup table in a graph costume.")
    print("=" * 74)


if __name__ == "__main__":
    main()
