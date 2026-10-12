"""Block 337000 — FULL is-a reaping at SCALE (the earned tier, thousands of edges).

Block 336 proved the pipeline + controls at 213 subjects. This is the real
"full reaping" of the calibration-EARNED tier (is-a): a large subject inventory
drawn from WordNet's noun taxonomy, batched elicitation, and the SAME held-out
controls at scale. Only is-a is harvested (concept/process not earned; the other
relations are calibrated separately in block 338).

WHY WORDNET: it is itself an is-a taxonomy, so it supplies BOTH a large subject
inventory AND the true immediate hypernym of each subject — free GOLD labels to
score elicitation fidelity honestly at scale (no hand-authored gold). WordNet
lives ONLY in the /applications venv (nltk_data), never committed.

Pipeline (identical in kind to block 336):
  ELICIT  — adjacent is-a per subject, batched, constrained to the candidate
            hypernym set (the hypernyms present in the sampled cone).
  SEED    — native CAN Microtheory (build_knowledge_mt), edges source=qwen3
            trust=0.5.
  QUERY   — held-out transitive entailment (dist>=2) by SUBSTRATE traversal,
            NO LLM at query. Controls: direct-edge-only baseline (must fail the
            transitive pos) + shuffled-graph (must collapse to chance).
Fidelity vs WordNet gold reported honestly.

Run (nohup standalone; NOT setsid+pkill — races the logfile):
  HF_HOME=/applications/data/model_graph_work/hf_home \
  NLTK_DATA=/applications/data/model_graph_work/nltk_data \
  PYTHONPATH=runners/dsl/python:. \
  nohup /applications/data/model_graph_work/venv/bin/python -u \
    scripts/llm_harvest_isa_full.py > var/harvest_isa_full.log 2>&1 &
"""
from __future__ import annotations

import json
import os
import time
from collections import defaultdict

import numpy as np

from domains import llm_hf_forward as hf
from domains import llm_knowledge_seed as ks

MODEL = "/applications/data/model_graph_work/Qwen3.8-4B-Distill"
OUT = "domain_data/llm_harvest/qwen3_reaped_isa_full.json"
SOURCE = "qwen3"
KNOWLEDGE_TRUST = 0.5
BATCH = 32
TEMPLATE = "A {} is a kind of"
TARGET_SUBJECTS = 6000       # inventory size (bounded for a ~1-2hr CPU run)
SEED_RNG = 0


def _wordnet_inventory(n_target):
    """Sample up to n_target (subject, gold_hypernym) pairs from WordNet nouns.
    A subject is a single-word lemma whose synset has an immediate hypernym with
    its own single-word lemma. Returns (gold: dict subject->hypernym, cands:
    sorted candidate hypernym list). Both subject and hypernym are lowercased
    single tokens (no multiword / underscores) so the constrained read is clean."""
    nltk_dir = os.environ.get("NLTK_DATA",
                              "/applications/data/model_graph_work/nltk_data")
    import nltk
    nltk.data.path.insert(0, nltk_dir)
    from nltk.corpus import wordnet as wn

    def _lemma(syn):
        for l in syn.lemma_names():
            if l.isalpha() and l.islower() and "_" not in l:
                return l
        return None

    gold = {}
    syns = list(wn.all_synsets("n"))
    rng = np.random.default_rng(SEED_RNG)
    rng.shuffle(syns)
    for syn in syns:
        if len(gold) >= n_target:
            break
        s = _lemma(syn)
        if not s or s in gold:
            continue
        hyps = syn.hypernyms()
        if not hyps:
            continue
        h = _lemma(hyps[0])
        if not h or h == s:
            continue
        gold[s] = h
    cands = sorted(set(gold.values()) | set(gold.keys()))
    return gold, cands


def main() -> int:
    print("=" * 74)
    print("HARVEST is-a @ FULL SCALE — block 337000 (qwen3, earned tier)")
    print("=" * 74)
    t_inv = time.time()
    gold, cands = _wordnet_inventory(TARGET_SUBJECTS)
    subs = list(gold.keys())
    print("WordNet inventory: %d subjects, %d candidate hypernyms (%.0fs)"
          % (len(subs), len(cands), time.time() - t_inv))

    t0 = time.time()
    m = hf.HFForward(MODEL, dtype="float32")
    tok = m.tokenizer
    print("loaded HFForward in %.0fs" % (time.time() - t0))

    # ---- ELICIT (batched) — the compute-bound phase --------------------
    t1 = time.time()
    pairs = ks.elicit_isa_batch(m, tok, subs, candidates=cands,
                                template=TEMPLATE, batch_size=BATCH)
    el_dt = time.time() - t1
    print("elicited %d subjects in %.0fs (%.0f edges/hr) [batched bs=%d]"
          % (len(pairs), el_dt, len(pairs) / el_dt * 3600, BATCH))

    extracted = [(s, o) for (s, o) in pairs if s != o]
    self_loops = sum(1 for s, o in pairs if s == o)
    correct_adj = sum(1 for s, o in pairs if gold.get(s) == o)
    print("adjacent elicitation vs WordNet gold: %d/%d (%.3f); self-loops %d"
          % (correct_adj, len(pairs), correct_adj / len(pairs), self_loops))

    # ---- held-out transitive closure of the EXTRACTED graph ------------
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
    rng = np.random.default_rng(SEED_RNG)
    allreach = {s: set(closure.get(s, {}).keys()) | set(adj.get(s, []))
                for s in nodes}
    # cap the held-out eval set so verification is quick even at scale
    if len(pos) > 2000:
        idx = rng.choice(len(pos), 2000, replace=False)
        pos = [pos[i] for i in idx]
    neg = []
    tries = 0
    nodes_arr = np.array(nodes, dtype=object)
    while len(neg) < len(pos) and tries < 500000:
        tries += 1
        a, b = rng.choice(nodes_arr, 2, replace=False)
        if b not in allreach.get(a, set()) and a != b:
            neg.append((a, b))

    # ---- substrate entailment verification (NO LLM at query) -----------
    from substrate_rs import _native
    SEEDS = ["seeds/can_native_reimplementation.json"]
    s = _native.Substrate()
    mt, n2n = ks.build_knowledge_mt(s, SEEDS, extracted, relation="isa")

    tp = sum(ks.query_transitive(s, n2n, a, b)[0] for a, b in pos)
    tn = sum(not ks.query_transitive(s, n2n, a, b)[0] for a, b in neg)
    acc = (tp + tn) / (len(pos) + len(neg)) if (pos or neg) else float("nan")
    tp_dir = sum(ks.query_direct(s, n2n, a, b) for a, b in pos)
    dir_recall = tp_dir / len(pos) if pos else float("nan")

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
    print("held-out entailment: %d pos (dist>=2, capped) + %d neg"
          % (len(pos), len(neg)))
    print("SUBSTRATE transitive acc:   %.3f (tp %d/%d, tn %d/%d)"
          % (acc, tp, len(pos), tn, len(neg)))
    print("direct-edge-only baseline:  %.3f pos-recall (must ~0)" % dir_recall)
    print("shuffled-graph control:     %.3f (must collapse)" % acc_sh)

    seed = {
        "_doc": ("FULL is-a reaping from qwen3 at scale (block 337). Earned tier "
                 "only. Subjects sampled from WordNet nouns (which also supply "
                 "the gold hypernym for honest fidelity scoring). Every edge "
                 "source=qwen3 trust=0.5; held-out transitive entailment DERIVED "
                 "by substrate traversal, no LLM at query."),
        "source": SOURCE, "relation": "isa", "trust": KNOWLEDGE_TRUST,
        "provenance": {"who": "language_model", "how": "generative",
                       "model": "empero-ai/Qwen3.8-4B-Distill",
                       "inventory": "wordnet-noun-sample",
                       "elicited_via": TEMPLATE + " (constrained, batched)"},
        "calibration": {
            "n_edges": len(extracted), "n_nodes": len(nodes),
            "n_subjects": len(subs), "self_loops_dropped": self_loops,
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
