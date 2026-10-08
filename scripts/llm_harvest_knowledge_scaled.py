"""Block 336000 — extract the EARNED knowledge tier (is-a) at SCALE.

Only the KNOWLEDGE tier is harvested: block 330 calibration EARNED it (held-out
transitive 1.00, shuffle control 0.54), while concept (opposite, AUC 0.59) and
process (negate, control FAILED) did not — harvesting those would reap unearned
tiers, which the trust band exists to prevent. So this is is-a only.

Pipeline (unchanged in kind from block 332; scaled in breadth + batched):
  ELICIT  — adjacent is-a for every subject, batched (block 335), constrained to
            the taxonomy hypernym vocabulary (one forward per batch).
  SEED    — native CAN Microtheory (build_knowledge_mt), edges tagged
            source=qwen3 + trust=0.5 (the calibrated self-published band).
  QUERY   — held-out ENTAILMENT the graph was NOT told: transitive closure
            (dist>=2) derived by SUBSTRATE traversal, NO LLM at query time.

Anti-faking / honest controls:
  · held-out transitive accuracy on (pos dist>=2, matched neg non-entailed);
  · DIRECT-EDGE-ONLY baseline (query_direct) — must FAIL the transitive pos
    (shows traversal, not lookup, carries the entailment);
  · SHUFFLED-graph control (objects permuted) — entailment must COLLAPSE
    (shows the real structure, not the node set, carries it).
Self-loops (A is-a A) are dropped and counted. Precision is reported HONESTLY;
if it drops from the 59-edge run's 1.00 that is the finding, not a failure.

Model+venv under /applications (never committed). Query time is pure substrate.
Run (nohup standalone; NOT setsid+pkill — races the logfile):
  HF_HOME=/applications/data/model_graph_work/hf_home \
  PYTHONPATH=runners/dsl/python:. \
  nohup /applications/data/model_graph_work/venv/bin/python -u \
    scripts/llm_harvest_knowledge_scaled.py > var/harvest_scaled.log 2>&1 &
"""
from __future__ import annotations

import json
import time
from collections import defaultdict

import numpy as np

from domains import llm_hf_forward as hf
from domains import llm_knowledge_seed as ks

MODEL = "/applications/data/model_graph_work/Qwen3.8-4B-Distill"
OUT = "domain_data/llm_harvest/qwen3_reaped_knowledge_scaled.json"
SOURCE = "qwen3"
KNOWLEDGE_TRUST = 0.5
BATCH = 32
TEMPLATE = "A {} is a kind of"


# A broad, DEEP multi-domain is-a taxonomy. Each chain is a path of adjacent
# is-a links; only ADJACENT links are elicited, the dist>=2 closure is held out.
# Deep chains (organism/substance/object trees) maximize the held-out transitive
# set. Instances share hypernyms so the graph has real branching structure.
def _chains():
    ch = []
    # --- living things -------------------------------------------------
    dogs = ["poodle", "beagle", "bulldog", "terrier", "spaniel", "mastiff",
            "collie", "dachshund", "husky", "boxer", "corgi", "pug"]
    cats = ["tabby", "siamese", "persian", "lion", "tiger", "leopard",
            "cheetah", "jaguar", "cougar", "lynx", "panther", "bobcat"]
    fish = ["salmon", "trout", "cod", "tuna", "herring", "carp", "bass",
            "sardine", "mackerel", "haddock", "anchovy", "perch"]
    birds = ["sparrow", "eagle", "robin", "finch", "hawk", "falcon", "owl",
             "crow", "raven", "pigeon", "swan", "heron"]
    snakes = ["cobra", "python", "viper", "boa", "adder", "mamba", "rattlesnake"]
    amph = ["frog", "toad", "newt", "salamander", "axolotl"]
    insects = ["bee", "ant", "wasp", "beetle", "moth", "butterfly", "cricket",
               "grasshopper", "dragonfly", "ladybug", "termite", "aphid"]
    for x in dogs:
        ch.append([x, "dog", "mammal", "animal", "organism"])
    for x in cats:
        ch.append([x, "cat", "mammal", "animal", "organism"])
    for x in fish:
        ch.append([x, "fish", "animal", "organism"])
    for x in birds:
        ch.append([x, "bird", "animal", "organism"])
    for x in snakes:
        ch.append([x, "snake", "reptile", "animal", "organism"])
    for x in amph:
        ch.append([x, "amphibian", "animal", "organism"])
    for x in insects:
        ch.append([x, "insect", "animal", "organism"])
    # --- plants --------------------------------------------------------
    trees = ["oak", "pine", "birch", "maple", "willow", "cedar", "spruce",
             "elm", "ash", "beech", "redwood", "poplar"]
    flowers = ["rose", "tulip", "daisy", "lily", "orchid", "daffodil",
               "sunflower", "poppy", "iris", "violet", "marigold", "petunia"]
    for x in trees:
        ch.append([x, "tree", "plant", "organism"])
    for x in flowers:
        ch.append([x, "flower", "plant", "organism"])
    # --- materials -----------------------------------------------------
    metals = ["copper", "iron", "gold", "silver", "tin", "lead", "zinc",
              "nickel", "aluminium", "titanium", "platinum", "brass"]
    rocks = ["granite", "sandstone", "limestone", "marble", "slate", "basalt",
             "shale", "obsidian"]
    for x in metals:
        ch.append([x, "metal", "material", "substance"])
    for x in rocks:
        ch.append([x, "rock", "material", "substance"])
    ch.append(["oxygen", "gas", "substance"])
    ch.append(["nitrogen", "gas", "substance"])
    ch.append(["water", "liquid", "substance"])
    # --- artifacts -----------------------------------------------------
    tools = ["hammer", "saw", "wrench", "screwdriver", "drill", "chisel",
             "pliers", "mallet", "file", "clamp"]
    furn = ["chair", "table", "desk", "stool", "bench", "sofa", "cabinet",
            "shelf", "wardrobe", "dresser"]
    vehicles = ["car", "truck", "bus", "van", "motorcycle", "bicycle",
                "tractor", "scooter", "jeep", "sedan"]
    for x in tools:
        ch.append([x, "tool", "artifact", "object"])
    for x in furn:
        ch.append([x, "furniture", "artifact", "object"])
    for x in vehicles:
        ch.append([x, "vehicle", "artifact", "object"])
    # --- food ----------------------------------------------------------
    fruits = ["apple", "banana", "orange", "grape", "pear", "peach", "plum",
              "cherry", "mango", "apricot"]
    veg = ["carrot", "potato", "onion", "spinach", "broccoli", "lettuce",
           "cabbage", "pea", "bean", "turnip"]
    for x in fruits:
        ch.append([x, "fruit", "food", "substance"])
    for x in veg:
        ch.append([x, "vegetable", "food", "substance"])
    # --- body ----------------------------------------------------------
    organs = ["heart", "lung", "liver", "kidney", "stomach", "brain", "spleen",
              "pancreas", "intestine"]
    limbs = ["hand", "foot", "arm", "leg", "finger", "toe", "elbow", "knee"]
    for x in organs:
        ch.append([x, "organ", "body_part"])
    for x in limbs:
        ch.append([x, "limb", "body_part"])
    return ch


def main() -> int:
    print("=" * 74)
    print("HARVEST KNOWLEDGE @ SCALE — block 336000 (qwen3, earned is-a tier)")
    print("=" * 74)
    CHAINS = _chains()

    # gold adjacent is-a (subject -> its immediate hypernym) + candidate vocab
    gold = {}
    for ch in CHAINS:
        for i in range(len(ch) - 1):
            gold.setdefault(ch[i], ch[i + 1])
    subs = list(gold.keys())
    cands = sorted(set(gold.keys()) | set(gold.values()))
    print("taxonomy: %d chains, %d subjects, %d candidate hypernyms"
          % (len(CHAINS), len(subs), len(cands)))

    t0 = time.time()
    m = hf.HFForward(MODEL, dtype="float32")
    tok = m.tokenizer
    print("loaded HFForward in %.0fs" % (time.time() - t0))

    # ---- ELICIT (batched) ---------------------------------------------
    t1 = time.time()
    pairs = ks.elicit_isa_batch(m, tok, subs, candidates=cands,
                                template=TEMPLATE, batch_size=BATCH)
    el_dt = time.time() - t1
    print("elicited %d subjects in %.1fs (%.0f edges/hr) [batched bs=%d]"
          % (len(pairs), el_dt, len(pairs) / el_dt * 3600, BATCH))

    extracted = [(s, o) for (s, o) in pairs if s != o]
    self_loops = sum(1 for s, o in pairs if s == o)
    # elicitation accuracy vs gold (how faithful the reaped adjacent edges are)
    correct_adj = sum(1 for s, o in pairs if gold.get(s) == o)
    print("adjacent elicitation vs gold: %d/%d correct (%.2f); self-loops %d"
          % (correct_adj, len(pairs), correct_adj / len(pairs), self_loops))

    # ---- held-out transitive closure of the EXTRACTED graph -----------
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
    while len(neg) < len(pos) and tries < 200000:
        tries += 1
        a, b = rng.choice(nodes, 2, replace=False)
        if b not in allreach.get(a, set()) and a != b:
            neg.append((a, b))

    # ---- substrate entailment verification (NO LLM at query) ----------
    from substrate_rs import _native
    SEEDS = ["seeds/can_native_reimplementation.json"]
    s = _native.Substrate()
    mt, n2n = ks.build_knowledge_mt(s, SEEDS, extracted, relation="isa")

    tp = sum(ks.query_transitive(s, n2n, a, b)[0] for a, b in pos)
    tn = sum(not ks.query_transitive(s, n2n, a, b)[0] for a, b in neg)
    acc = (tp + tn) / (len(pos) + len(neg)) if (pos or neg) else float("nan")

    # CONTROL 1: direct-edge-only baseline — must FAIL the transitive pos
    tp_dir = sum(ks.query_direct(s, n2n, a, b) for a, b in pos)
    dir_recall = tp_dir / len(pos) if pos else float("nan")

    # CONTROL 2: shuffled-graph — entailment must COLLAPSE
    tgts = [o for _, o in extracted]
    tsh = list(tgts); rng.shuffle(tsh)
    shuffled = list(zip([s0 for s0, _ in extracted], tsh))
    s2 = _native.Substrate()
    mt2, n2n2 = ks.build_knowledge_mt(s2, SEEDS, shuffled, relation="isa")
    tp_sh = sum(ks.query_transitive(s2, n2n2, a, b)[0] for a, b in pos)
    tn_sh = sum(not ks.query_transitive(s2, n2n2, a, b)[0] for a, b in neg)
    acc_sh = (tp_sh + tn_sh) / (len(pos) + len(neg)) if (pos or neg) else float("nan")

    print("\nextracted %d edges (self-loops %d dropped), %d nodes"
          % (len(extracted), self_loops, len(nodes)))
    print("held-out entailment: %d pos (dist>=2) + %d neg" % (len(pos), len(neg)))
    print("SUBSTRATE transitive acc:   %.3f (tp %d/%d, tn %d/%d)"
          % (acc, tp, len(pos), tn, len(neg)))
    print("direct-edge-only baseline:  %.3f pos-recall (must be ~0 -> traversal adds inference)"
          % dir_recall)
    print("shuffled-graph control:     %.3f (must collapse toward chance)" % acc_sh)

    # ---- write the reaped native CAN seed fragment --------------------
    seed = {
        "_doc": ("Reaped KNOWLEDGE (is-a) from the qwen3 source at SCALE "
                 "(block 336). Earned tier only (block 330: concept weak, "
                 "process control-failed). Every edge carries source=qwen3 + "
                 "trust (the calibrated self-published band, 0.5). Held-out "
                 "transitive entailment is DERIVED by substrate traversal, no "
                 "LLM at query."),
        "source": SOURCE,
        "relation": "isa",
        "trust": KNOWLEDGE_TRUST,
        "provenance": {"who": "language_model", "how": "generative",
                       "model": "empero-ai/Qwen3.8-4B-Distill",
                       "elicited_via": TEMPLATE + " (constrained, batched)"},
        "calibration": {
            "n_edges": len(extracted),
            "n_nodes": len(nodes),
            "self_loops_dropped": self_loops,
            "adjacent_elicitation_acc": round(correct_adj / len(pairs), 3),
            "held_out_transitive_acc": round(acc, 3),
            "held_out_pos": len(pos), "held_out_neg": len(neg),
            "direct_edge_baseline_pos_recall": round(dir_recall, 3),
            "shuffled_control_acc": round(acc_sh, 3),
            "elicit_seconds": round(el_dt, 1),
            "edges_per_hour": round(len(pairs) / el_dt * 3600),
        },
        "edges": [{"subject": s0, "relation": "isa", "object": o0,
                   "source": SOURCE, "trust": KNOWLEDGE_TRUST}
                  for (s0, o0) in extracted],
    }
    with open(OUT, "w") as f:
        json.dump(seed, f, indent=1)
    print("\nwrote %s (%d edges, source=%s, trust=%.2f)"
          % (OUT, len(extracted), SOURCE, KNOWLEDGE_TRUST))
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
