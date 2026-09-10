"""Block 330000 — calibrate a CURRENT model as a harvest source.

Bring up `empero-ai/Qwen3.8-4B-Distill` (Qwen3.8 distilled into the Qwen3.5-4B
hybrid `qwen3_5` architecture) through the HF-forward shim (`domains.llm_hf_
forward.HFForward`) — the numpy `NumpyQwen3` reader does NOT support this
architecture (that is Plan B, deferred), but the extraction arc only needs
next-token logits + per-layer hidden states, which the HF forward provides.

Re-run the three extraction measures — KNOWLEDGE (327 is-a held-out entailment),
CONCEPT (328 opposite held-out transfer), PROCESS (329 negate held-out
application) — with their anti-faking controls. The results are NOT a
re-derivation; they are the CALIBRATION that becomes this source's trust events
(block 331): a relation kind that survives its controls on this model earns
higher trust than one that does not.

Run: HF_HOME=/applications/data/model_graph_work/hf_home \\
     PYTHONPATH=runners/dsl/python:. \\
     /applications/data/model_graph_work/venv/bin/python -u \\
       scripts/llm_harvest_calibrate.py
"""

import sys, time
sys.path.insert(0, ".")
import numpy as np

from domains import llm_hf_forward as hf
from domains import llm_knowledge_seed as ks
from domains import llm_concept_seed as cs
from domains import llm_process_seed as ps

MODEL = "/applications/data/model_graph_work/Qwen3.8-4B-Distill"
HIDDEN_LAYER = 16          # mid-layer contextual vector (33 hidden_states, 0..32)


# ---- knowledge battery (327 taxonomy) ----
CHAINS = [
    ["poodle", "dog", "mammal", "animal", "organism"],
    ["tabby", "cat", "mammal", "animal", "organism"],
    ["salmon", "fish", "animal", "organism"],
    ["sparrow", "bird", "animal", "organism"],
    ["eagle", "bird", "animal", "organism"],
    ["oak", "tree", "plant", "organism"],
    ["pine", "tree", "plant", "organism"],
    ["rose", "flower", "plant", "organism"],
    ["copper", "metal", "material", "substance"],
    ["iron", "metal", "material", "substance"],
    ["granite", "rock", "material", "substance"],
    ["sandstone", "rock", "material", "substance"],
]
# ---- concept battery (328 antonym families) ----
A_OPP = [("hot", "cold"), ("big", "small"), ("high", "low"), ("fast", "slow"),
         ("hard", "soft"), ("heavy", "light"), ("strong", "weak"),
         ("rich", "poor"), ("happy", "sad"), ("full", "empty"),
         ("early", "late"), ("loud", "quiet")]
B_OPP = [("open", "closed"), ("wet", "dry"), ("clean", "dirty"),
         ("sharp", "dull"), ("bright", "dark"), ("young", "old"),
         ("true", "false"), ("deep", "shallow")]
# ---- process battery (329 negate) ----
A_STMT = ["The sky is blue", "Water is wet", "Fire is hot", "Ice is cold",
          "Grass is green", "The sun is bright", "Snow is white",
          "Coal is black", "Lemons are sour", "Sugar is sweet",
          "Rocks are hard", "Feathers are soft"]
B_STMT = ["The ocean is deep", "Metal is heavy", "Gold is valuable",
          "Rain is wet", "Night is dark", "Stars are distant",
          "Honey is sticky", "Wind is fast"]


def calibrate_knowledge(model, tok):
    subs, gold = [], {}
    for ch in CHAINS:
        for i in range(len(ch) - 1):
            subs.append(ch[i]); gold.setdefault(ch[i], ch[i + 1])
    subs = list(gold.keys())
    cands = sorted({o for _, o in [(s, gold[s]) for s in subs]} | set(subs))
    pairs = ks.elicit_isa(model, tok, subs, candidates=cands,
                          template="A {} is a kind of")
    extracted = [(s, o) for (s, o) in pairs if s != o]
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
    while len(neg) < len(pos) and len(nodes) > 2:
        a, b = rng.choice(nodes, 2, replace=False)
        if b not in allreach.get(a, set()) and a != b:
            neg.append((a, b))

    def reachable(s, o):
        return o in closure.get(s, {})
    tp = sum(reachable(s, o) for s, o in pos)
    tn = sum(not reachable(a, b) for a, b in neg)
    n = len(pos) + len(neg)
    return {"extracted_edges": len(extracted), "n_pos": len(pos),
            "self_loops": sum(1 for s, o in pairs if s == o),
            "transitive_acc": (tp + tn) / n if n else float("nan"),
            "tp": tp, "tn": tn}


def calibrate_concept(hf_model, tok):
    words = sorted({w for p in A_OPP + B_OPP for w in p})
    vecs = ps.statement_vectors_hf(hf_model, tok,
                                   ["The word %s means" % w for w in words],
                                   layer=HIDDEN_LAYER)
    vecs = {w: vecs["The word %s means" % w] for w in words}
    W = cs.fit_opposite_operator(vecs, A_OPP, ridge=1.0)
    Bw = sorted({w for p in B_OPP for w in p})
    goldset = set()
    for a, b in B_OPP:
        goldset.add((a, b)); goldset.add((b, a))
    rng = np.random.default_rng(0)

    def align(Wm, a, b):
        p = Wm @ vecs[a]; p = p / (np.linalg.norm(p) + 1e-9)
        v = vecs[b] / (np.linalg.norm(vecs[b]) + 1e-9)
        return float(p @ v)

    def auc(Wm):
        pos = np.array([align(Wm, a, b) for a, b in B_OPP])
        neg = []
        for _ in range(300):
            a, b = rng.choice(Bw, 2, replace=False)
            if (a, b) not in goldset:
                neg.append(align(Wm, a, b))
        neg = np.array(neg)
        return float(np.mean([(p > neg).mean() for p in pos]))
    Wr = rng.standard_normal(W.shape).astype(np.float32) * float(np.std(W))
    return {"transfer_auc": auc(W), "random_W_auc": auc(Wr)}


def calibrate_process(hf_model, tok):
    def neg(s):
        return s.replace(" is ", " is not ", 1)
    allstmt = []
    for s in A_STMT + B_STMT:
        allstmt.append(s); allstmt.append(neg(s))
    vecs = ps.statement_vectors_hf(hf_model, tok, allstmt, layer=HIDDEN_LAYER)
    N = ps.fit_process_operator(vecs, [(s, neg(s)) for s in A_STMT], ridge=1.0)
    p, thresh = ps.fit_valence_probe(vecs, A_STMT, [neg(s) for s in A_STMT])
    rng = np.random.default_rng(0)
    Nr = rng.standard_normal(N.shape).astype(np.float32) * float(np.std(N))
    appN = np.mean([ps.reads_negated(N @ vecs[s], p, thresh) for s in B_STMT])
    appI = np.mean([ps.reads_negated(vecs[s], p, thresh) for s in B_STMT])
    appR = np.mean([ps.reads_negated(Nr @ vecs[s], p, thresh) for s in B_STMT])
    return {"apply_extracted": float(appN), "apply_identity": float(appI),
            "apply_shuffled": float(appR)}


def main():
    print("=" * 74)
    print("HARVEST CALIBRATION — block 330000")
    print("model: empero-ai/Qwen3.8-4B-Distill (qwen3_5 hybrid, HF forward)")
    print("=" * 74)
    t0 = time.time()
    m = hf.HFForward(MODEL, dtype="float32")
    tok = m.tokenizer
    print("loaded HFForward in %.0fs; n_layers=%d" % (time.time() - t0, m.n_layers))

    print("\n[knowledge] is-a held-out transitive entailment (327 battery)")
    k = calibrate_knowledge(m, tok)
    print("  extracted edges %d (self-loops %d), held-out pos %d"
          % (k["extracted_edges"], k["self_loops"], k["n_pos"]))
    print("  SUBSTRATE transitive accuracy: %.2f (tp %d / tn %d)"
          % (k["transitive_acc"], k["tp"], k["tn"]))

    print("\n[concept] opposite-of held-out transfer (328 battery)")
    c = calibrate_concept(m, tok)
    print("  transfer AUC: %.2f  (random-W control %.2f; chance 0.50)"
          % (c["transfer_auc"], c["random_W_auc"]))

    print("\n[process] negate held-out application (329 battery)")
    pr = calibrate_process(m, tok)
    print("  apply extracted %.2f | identity %.2f | shuffled %.2f"
          % (pr["apply_extracted"], pr["apply_identity"], pr["apply_shuffled"]))

    print("\n" + "=" * 74)
    print("CALIBRATION TABLE (feeds block-331 trust events):")
    print("  knowledge (is-a)   : transitive %.2f, self-loops %d/%d elicited"
          % (k["transitive_acc"], k["self_loops"],
             k["extracted_edges"] + k["self_loops"]))
    print("  concept (opposite) : transfer AUC %.2f vs control %.2f"
          % (c["transfer_auc"], c["random_W_auc"]))
    print("  process (negate)   : apply %.2f vs identity %.2f vs shuffle %.2f"
          % (pr["apply_extracted"], pr["apply_identity"], pr["apply_shuffled"]))
    print("=" * 74)


if __name__ == "__main__":
    main()
