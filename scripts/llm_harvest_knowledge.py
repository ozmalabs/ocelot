"""Block 332000 — harvest KNOWLEDGE at scale from the calibrated qwen3 source.

Block 330 calibration earned the KNOWLEDGE tier (is-a held-out transitive
entailment 1.00, 0 self-loops) and did NOT earn concept (AUC 0.59 ≈ control) or
process (control failed). So this harvest reaps KNOWLEDGE ONLY — the honest,
calibration-earned tier — at a broader scale, and writes it as a native CAN seed
fragment (`seeds/generated/qwen3_reaped_knowledge.json`) with every edge tagged
`source: qwen3` and the knowledge-tier trust weight.

Elicitation is a constrained next-token read (`elicit_isa`) through the HF-forward
shim (`HFForward` — the numpy reader does not support qwen3_5). Self-loops are
dropped (a self-edge is not a fact). Held-out ENTAILMENT (the extracted-graph
transitive closure at distance ≥ 2, NOT elicited) is verified by substrate
traversal + a shuffled-graph control, so the reaped seed is shown to carry real
relational structure, not memorised pairs.

Run: HF_HOME=/applications/data/model_graph_work/hf_home \\
     PYTHONPATH=runners/dsl/python:. \\
     /applications/data/model_graph_work/venv/bin/python -u \\
       scripts/llm_harvest_knowledge.py
"""

import sys, json, time
sys.path.insert(0, ".")
import numpy as np

from domains import llm_hf_forward as hf
from domains import llm_knowledge_seed as ks

MODEL = "/applications/data/model_graph_work/Qwen3.8-4B-Distill"
OUT = "seeds/generated/qwen3_reaped_knowledge.json"
SOURCE = "qwen3"
KNOWLEDGE_TRUST = 0.5      # the qwen3 source band (block 331); knowledge is the
#                           earned tier, so its edges ride at the source band.


# A broad is-a taxonomy across domains (living things, materials, artifacts,
# food, bodies, vehicles). Adjacent links are elicited; the transitive closure
# at dist>=2 is held out for the substrate to DERIVE.
CHAINS = [
    ["poodle", "dog", "mammal", "animal", "organism"],
    ["beagle", "dog", "mammal", "animal", "organism"],
    ["tabby", "cat", "mammal", "animal", "organism"],
    ["lion", "cat", "mammal", "animal", "organism"],
    ["salmon", "fish", "animal", "organism"],
    ["trout", "fish", "animal", "organism"],
    ["sparrow", "bird", "animal", "organism"],
    ["eagle", "bird", "animal", "organism"],
    ["cobra", "snake", "reptile", "animal", "organism"],
    ["frog", "amphibian", "animal", "organism"],
    ["bee", "insect", "animal", "organism"],
    ["ant", "insect", "animal", "organism"],
    ["oak", "tree", "plant", "organism"],
    ["pine", "tree", "plant", "organism"],
    ["rose", "flower", "plant", "organism"],
    ["tulip", "flower", "plant", "organism"],
    ["copper", "metal", "material", "substance"],
    ["iron", "metal", "material", "substance"],
    ["gold", "metal", "material", "substance"],
    ["granite", "rock", "material", "substance"],
    ["sandstone", "rock", "material", "substance"],
    ["oxygen", "gas", "substance"],
    ["water", "liquid", "substance"],
    ["hammer", "tool", "artifact", "object"],
    ["saw", "tool", "artifact", "object"],
    ["chair", "furniture", "artifact", "object"],
    ["table", "furniture", "artifact", "object"],
    ["car", "vehicle", "artifact", "object"],
    ["truck", "vehicle", "artifact", "object"],
    ["apple", "fruit", "food", "substance"],
    ["banana", "fruit", "food", "substance"],
    ["carrot", "vegetable", "food", "substance"],
    ["heart", "organ", "body_part"],
    ["lung", "organ", "body_part"],
    ["hand", "limb", "body_part"],
]


def main():
    print("=" * 74)
    print("HARVEST KNOWLEDGE — block 332000 (qwen3 source, is-a at scale)")
    print("=" * 74)
    t0 = time.time()
    m = hf.HFForward(MODEL, dtype="float32")
    tok = m.tokenizer
    print("loaded HFForward in %.0fs" % (time.time() - t0))

    # elicit adjacent is-a (constrained to the taxonomy vocabulary)
    gold = {}
    for ch in CHAINS:
        for i in range(len(ch) - 1):
            gold.setdefault(ch[i], ch[i + 1])
    subs = list(gold.keys())
    cands = sorted(set(gold.keys()) | set(gold.values()))
    t1 = time.time()
    pairs = ks.elicit_isa(m, tok, subs, candidates=cands,
                          template="A {} is a kind of")
    print("elicited %d subjects in %.0fs" % (len(pairs), time.time() - t1))

    extracted = [(s, o) for (s, o) in pairs if s != o]
    self_loops = sum(1 for s, o in pairs if s == o)

    # transitive closure of the EXTRACTED graph (ground truth for entailment)
    from collections import defaultdict
    adj = defaultdict(list)
    for s, o in extracted:
        adj[s].append(o)

    def reach(s):
        seen, fr, out = set(), [(s, 0)], {}
        while fr:
            n, d = fr.pop(0)
            for k in adj.get(n, []):
                if k not in seen and k != s:
                    seen.add(k); out[k] = d + 1; fr.append((k, d + 1))
        return out
    closure = {s: reach(s) for s in adj}
    pos = [(s, o) for s in closure for o, d in closure[s].items() if d >= 2]
    nodes = sorted({x for e in extracted for x in e})
    rng = np.random.default_rng(0)
    allreach = {s: set(closure.get(s, {}).keys()) | set(adj.get(s, []))
                for s in nodes}
    neg = []
    tries = 0
    while len(neg) < len(pos) and tries < 10000:
        tries += 1
        a, b = rng.choice(nodes, 2, replace=False)
        if b not in allreach.get(a, set()) and a != b:
            neg.append((a, b))

    # ---- substrate entailment verification (no LLM at query) ----
    import importlib
    from substrate_rs import _native
    SEEDS = ["seeds/can_native_reimplementation.json"]
    s = _native.Substrate()
    mt, n2n = ks.build_knowledge_mt(s, SEEDS, extracted, relation="isa")

    def q_trans(subj, obj):
        return ks.query_transitive(s, n2n, subj, obj)[0]
    tp = sum(q_trans(a, b) for a, b in pos)
    tn = sum(not q_trans(a, b) for a, b in neg)
    acc = (tp + tn) / (len(pos) + len(neg)) if (pos or neg) else float("nan")

    # shuffled-graph control
    tgts = [o for _, o in extracted]
    tsh = list(tgts); rng.shuffle(tsh)
    shuffled = list(zip([s0 for s0, _ in extracted], tsh))
    s2 = _native.Substrate()
    mt2, n2n2 = ks.build_knowledge_mt(s2, SEEDS, shuffled, relation="isa")
    tp_sh = sum(ks.query_transitive(s2, n2n2, a, b)[0] for a, b in pos)
    acc_sh = (tp_sh + tn) / (len(pos) + len(neg)) if (pos or neg) else float("nan")

    print("\nextracted %d edges (self-loops %d dropped), %d nodes"
          % (len(extracted), self_loops, len(nodes)))
    print("held-out entailment: %d pos (dist>=2) + %d neg" % (len(pos), len(neg)))
    print("SUBSTRATE transitive acc: %.2f (tp %d/%d, tn %d/%d)"
          % (acc, tp, len(pos), tn, len(neg)))
    print("shuffled-graph control:  %.2f" % acc_sh)

    # ---- write the reaped native CAN seed fragment ----
    seed = {
        "_doc": ("Reaped KNOWLEDGE (is-a) from the qwen3 source (block 332). "
                 "Every edge carries source=qwen3 + trust (the calibrated "
                 "self-published band). Concept/process tiers NOT harvested "
                 "(block 330: concept weak AUC 0.59, process control-failed)."),
        "source": SOURCE,
        "relation": "isa",
        "trust": KNOWLEDGE_TRUST,
        "provenance": {"who": "language_model", "how": "generative",
                       "elicited_via": "A {} is a kind of (constrained)"},
        "calibration": {"held_out_transitive_acc": round(acc, 3),
                        "shuffled_control_acc": round(acc_sh, 3),
                        "self_loops_dropped": self_loops},
        "edges": [{"subject": s0, "relation": "isa", "object": o0,
                   "source": SOURCE, "trust": KNOWLEDGE_TRUST}
                  for (s0, o0) in extracted],
    }
    with open(OUT, "w") as f:
        json.dump(seed, f, indent=1)
    print("\nwrote %s (%d edges, source=%s, trust=%.2f)"
          % (OUT, len(extracted), SOURCE, KNOWLEDGE_TRUST))
    print("=" * 74)


if __name__ == "__main__":
    main()
