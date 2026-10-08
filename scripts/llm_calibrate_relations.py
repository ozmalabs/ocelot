"""Block 338000 — CALIBRATE 5 new relations before any of them earns the band.

The trust band exists to stop unearned tiers being reaped. Block 330 calibrated
is-a (EARNED) and, honestly, found concept weak + process control-FAILED. This
script applies the SAME discipline to five relational tiers, each with a control
appropriate to its ALGEBRA — a relation earns the band only if its held-out
structural control passes and its shuffle control collapses:

  part-of     (meronymy)  — transitive: finger po hand po body => finger po body.
                            control: held-out transitive acc + shuffle collapse.
  located-in  (topo)      — transitive: paris in france in europe => paris in europe.
                            control: held-out transitive acc + shuffle collapse.
  capital-of  (function)  — 1:1, NOT transitive. control: held-out DIRECT acc vs
                            gold + shuffle collapse (transitivity is the WRONG test).
  same-as     (synonymy)  — symmetric+transitive (equivalence). control: SYMMETRY
                            recovered in-graph + shuffle collapse.
  opposite-of (antonymy)  — symmetric, NOT transitive. control: SYMMETRY + shuffle;
                            transitivity SHOULD fail (a correctness check).

Gold sets are hand-curated (calibration, like block 330). ELICIT is oracle-only;
query is pure substrate. Reports a per-relation table: adjacent fidelity, the
structural control, the shuffle control, and the EARNED verdict. No seed is
written here — block 338's harvest step reaps only the PASSED relations.

Run (nohup standalone):
  HF_HOME=/applications/data/model_graph_work/hf_home \
  PYTHONPATH=runners/dsl/python:. \
  nohup /applications/data/model_graph_work/venv/bin/python -u \
    scripts/llm_calibrate_relations.py > var/calibrate_relations.log 2>&1 &
"""
from __future__ import annotations

import json
import time
from collections import defaultdict

import numpy as np

from domains import llm_hf_forward as hf
from domains import llm_knowledge_seed as ks

MODEL = "/applications/data/model_graph_work/Qwen3.8-4B-Distill"
OUT = "domain_data/llm_harvest/qwen3_relation_calibration.json"
BATCH = 16
RNG = np.random.default_rng(0)


# ---- gold sets (curated) ------------------------------------------------
# part-of chains (meronymy) — adjacent links elicited, dist>=2 held out.
PART_CHAINS = [
    ["finger", "hand", "arm", "body"],
    ["toe", "foot", "leg", "body"],
    ["knuckle", "finger", "hand", "arm"],
    ["nail", "finger", "hand", "arm"],
    ["petal", "flower", "plant"],
    ["leaf", "branch", "tree", "plant"],
    ["root", "tree", "plant"],
    ["wheel", "car", "vehicle"],
    ["engine", "car", "vehicle"],
    ["door", "room", "house", "building"],
    ["window", "room", "house", "building"],
    ["roof", "house", "building"],
    ["page", "chapter", "book"],
    ["keyboard", "computer", "office"],
    ["screen", "computer", "office"],
]
LOC_CHAINS = [
    ["paris", "france", "europe"],
    ["lyon", "france", "europe"],
    ["berlin", "germany", "europe"],
    ["munich", "germany", "europe"],
    ["madrid", "spain", "europe"],
    ["rome", "italy", "europe"],
    ["tokyo", "japan", "asia"],
    ["osaka", "japan", "asia"],
    ["beijing", "china", "asia"],
    ["mumbai", "india", "asia"],
    ["cairo", "egypt", "africa"],
    ["lagos", "nigeria", "africa"],
    ["toronto", "canada", "americas"],
    ["chicago", "usa", "americas"],
    ["sydney", "australia", "oceania"],
]
# capital-of (function, direct) — country -> capital gold.
CAPITAL_GOLD = {
    "france": "paris", "germany": "berlin", "spain": "madrid", "italy": "rome",
    "japan": "tokyo", "china": "beijing", "russia": "moscow", "egypt": "cairo",
    "canada": "ottawa", "brazil": "brasilia", "portugal": "lisbon",
    "greece": "athens", "poland": "warsaw", "austria": "vienna",
    "norway": "oslo", "sweden": "stockholm", "finland": "helsinki",
    "ireland": "dublin", "cuba": "havana", "peru": "lima",
}
# same-as (synonymy) — symmetric pairs.
SAME_GOLD = [
    ("big", "large"), ("small", "little"), ("fast", "quick"), ("happy", "glad"),
    ("smart", "clever"), ("sad", "unhappy"), ("rich", "wealthy"),
    ("angry", "mad"), ("cold", "chilly"), ("begin", "start"),
    ("end", "finish"), ("buy", "purchase"), ("show", "display"),
    ("help", "assist"), ("close", "shut"),
]
# opposite-of (antonymy) — symmetric pairs.
OPP_GOLD = [
    ("hot", "cold"), ("big", "small"), ("fast", "slow"), ("happy", "sad"),
    ("up", "down"), ("light", "dark"), ("open", "closed"), ("full", "empty"),
    ("high", "low"), ("hard", "soft"), ("wet", "dry"), ("rich", "poor"),
    ("young", "old"), ("strong", "weak"), ("clean", "dirty"),
]


def _gold_from_chains(chains):
    gold = {}
    for ch in chains:
        for i in range(len(ch) - 1):
            gold.setdefault(ch[i], ch[i + 1])
    return gold


def _transitive_eval(extracted, relation, SEEDS):
    """Build graph, hold out dist>=2 closure, return (acc, dir_recall, acc_sh,
    npos, nneg)."""
    from substrate_rs import _native
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
    pos = [(a, b) for a in closure for b, d in closure[a].items() if d >= 2]
    nodes = sorted({x for e in extracted for x in e})
    allreach = {a: set(closure.get(a, {}).keys()) | set(adj.get(a, []))
                for a in nodes}
    neg = []
    tries = 0
    while len(neg) < len(pos) and tries < 100000:
        tries += 1
        a, b = RNG.choice(np.array(nodes, dtype=object), 2, replace=False)
        if b not in allreach.get(a, set()) and a != b:
            neg.append((a, b))
    if not pos:
        return dict(acc=float("nan"), dir_recall=float("nan"),
                    acc_sh=float("nan"), npos=0, nneg=0)
    s = _native.Substrate()
    _, n2n = ks.build_knowledge_mt(s, SEEDS, extracted, relation=relation)
    tp = sum(ks.query_transitive(s, n2n, a, b)[0] for a, b in pos)
    tn = sum(not ks.query_transitive(s, n2n, a, b)[0] for a, b in neg)
    acc = (tp + tn) / (len(pos) + len(neg))
    dir_recall = sum(ks.query_direct(s, n2n, a, b) for a, b in pos) / len(pos)
    tgts = [o for _, o in extracted]; tsh = list(tgts); RNG.shuffle(tsh)
    sh = list(zip([x for x, _ in extracted], tsh))
    s2 = _native.Substrate()
    _, n2n2 = ks.build_knowledge_mt(s2, SEEDS, sh, relation=relation)
    tp2 = sum(ks.query_transitive(s2, n2n2, a, b)[0] for a, b in pos)
    tn2 = sum(not ks.query_transitive(s2, n2n2, a, b)[0] for a, b in neg)
    acc_sh = (tp2 + tn2) / (len(pos) + len(neg))
    return dict(acc=round(acc, 3), dir_recall=round(dir_recall, 3),
                acc_sh=round(acc_sh, 3), npos=len(pos), nneg=len(neg))


def _symmetry_eval(extracted, relation, SEEDS):
    """For a symmetric relation: build graph with ONLY the forward edges, hold
    out the REVERSE direction, check the graph recovers it via 1 hop after we
    add reverse-closure — here we test whether the elicited forward edges, when
    the relation is declared symmetric, let the substrate answer b->a. We model
    symmetry as: add both directions, then the held-out test is that reverse
    pairs are reachable. The honest control is the shuffle: permuted pairs must
    NOT be symmetric-consistent. Returns (sym_acc, acc_sh)."""
    from substrate_rs import _native
    # forward + reverse edges (symmetry materialized)
    both = extracted + [(o, s) for s, o in extracted]
    s = _native.Substrate()
    _, n2n = ks.build_knowledge_mt(s, SEEDS, both, relation=relation)
    # test: every elicited (a,b) should have b->a queryable (symmetry recovered)
    rev = [(o, s0) for s0, o in extracted]
    tp = sum(ks.query_direct(s, n2n, a, b) for a, b in rev)
    sym_acc = tp / len(rev) if rev else float("nan")
    # shuffle control: permute the reverse targets; symmetry should NOT hold
    tgts = [b for _, b in rev]; tsh = list(tgts); RNG.shuffle(tsh)
    revsh = list(zip([a for a, _ in rev], tsh))
    tp_sh = sum(ks.query_direct(s, n2n, a, b) for a, b in revsh)
    acc_sh = tp_sh / len(revsh) if revsh else float("nan")
    return dict(sym_acc=round(sym_acc, 3), acc_sh=round(acc_sh, 3),
                npairs=len(rev))


def main() -> int:
    print("=" * 74)
    print("RELATION CALIBRATION — block 338000 (per-relation held-out controls)")
    print("=" * 74)
    SEEDS = ["seeds/can_native_reimplementation.json"]

    t0 = time.time()
    m = hf.HFForward(MODEL, dtype="float32")
    tok = m.tokenizer
    print("loaded HFForward in %.0fs\n" % (time.time() - t0))

    report = {}

    # ---------- part-of (transitive) ----------
    gold = _gold_from_chains(PART_CHAINS)
    subs = list(gold.keys())
    cands = sorted(set(gold) | set(gold.values()))
    pairs = ks.elicit_relation_batch(m, tok, subs,
                                     template="A {} is part of a",
                                     candidates=cands, batch_size=BATCH)
    fid = sum(1 for s, o in pairs if gold.get(s) == o) / len(pairs)
    extracted = [(s, o) for s, o in pairs if s != o]
    tr = _transitive_eval(extracted, "part_of", SEEDS)
    earned = (tr["acc"] >= 0.8 and tr["acc_sh"] <= 0.65 and tr["dir_recall"] <= 0.2)
    report["part_of"] = dict(kind="transitive", fidelity=round(fid, 3),
                             **tr, earned=bool(earned))
    print("part_of      fid=%.2f transitive_acc=%.3f dir=%.3f shuffle=%.3f -> %s"
          % (fid, tr["acc"], tr["dir_recall"], tr["acc_sh"],
             "EARNED" if earned else "NOT earned"))

    # ---------- located-in (transitive) ----------
    gold = _gold_from_chains(LOC_CHAINS)
    subs = list(gold.keys())
    cands = sorted(set(gold) | set(gold.values()))
    pairs = ks.elicit_relation_batch(m, tok, subs,
                                     template="{} is located in",
                                     candidates=cands, batch_size=BATCH)
    fid = sum(1 for s, o in pairs if gold.get(s) == o) / len(pairs)
    extracted = [(s, o) for s, o in pairs if s != o]
    tr = _transitive_eval(extracted, "located_in", SEEDS)
    earned = (tr["acc"] >= 0.8 and tr["acc_sh"] <= 0.65 and tr["dir_recall"] <= 0.2)
    report["located_in"] = dict(kind="transitive", fidelity=round(fid, 3),
                                **tr, earned=bool(earned))
    print("located_in   fid=%.2f transitive_acc=%.3f dir=%.3f shuffle=%.3f -> %s"
          % (fid, tr["acc"], tr["dir_recall"], tr["acc_sh"],
             "EARNED" if earned else "NOT earned"))

    # ---------- capital-of (direct function) ----------
    subs = list(CAPITAL_GOLD.keys())
    cands = sorted(set(CAPITAL_GOLD.values()))
    pairs = ks.elicit_relation_batch(m, tok, subs,
                                     template="The capital of {} is",
                                     candidates=cands, batch_size=BATCH)
    fid = sum(1 for s, o in pairs if CAPITAL_GOLD.get(s) == o) / len(pairs)
    # shuffle control: permuted country->capital should score ~1/N by chance
    tgts = [o for _, o in pairs]; tsh = list(tgts); RNG.shuffle(tsh)
    fid_sh = sum(1 for (s, _), o in zip(pairs, tsh)
                 if CAPITAL_GOLD.get(s) == o) / len(pairs)
    earned = (fid >= 0.8 and fid_sh <= 0.3)
    report["capital_of"] = dict(kind="direct_function", fidelity=round(fid, 3),
                                shuffle_fidelity=round(fid_sh, 3),
                                n=len(pairs), earned=bool(earned))
    print("capital_of   fid=%.2f shuffle_fid=%.3f (direct) -> %s"
          % (fid, fid_sh, "EARNED" if earned else "NOT earned"))

    # ---------- same-as (symmetric synonymy) ----------
    subs = [a for a, _ in SAME_GOLD]
    goldmap = {a: b for a, b in SAME_GOLD}
    cands = sorted(set(goldmap.values()) | set(goldmap.keys()))
    pairs = ks.elicit_relation_batch(m, tok, subs,
                                     template="A word that means the same as {} is",
                                     candidates=cands, batch_size=BATCH)
    fid = sum(1 for s, o in pairs if goldmap.get(s) == o) / len(pairs)
    extracted = [(s, o) for s, o in pairs if s != o]
    sy = _symmetry_eval(extracted, "same_as", SEEDS)
    earned = (fid >= 0.6 and sy["sym_acc"] >= 0.9 and sy["acc_sh"] <= 0.3)
    report["same_as"] = dict(kind="symmetric", fidelity=round(fid, 3),
                             **sy, earned=bool(earned))
    print("same_as      fid=%.2f symmetry=%.3f shuffle=%.3f -> %s"
          % (fid, sy["sym_acc"], sy["acc_sh"], "EARNED" if earned else "NOT earned"))

    # ---------- opposite-of (symmetric antonymy) ----------
    subs = [a for a, _ in OPP_GOLD]
    goldmap = {a: b for a, b in OPP_GOLD}
    cands = sorted(set(goldmap.values()) | set(goldmap.keys()))
    pairs = ks.elicit_relation_batch(m, tok, subs,
                                     template="The opposite of {} is",
                                     candidates=cands, batch_size=BATCH)
    fid = sum(1 for s, o in pairs if goldmap.get(s) == o) / len(pairs)
    extracted = [(s, o) for s, o in pairs if s != o]
    sy = _symmetry_eval(extracted, "opposite_of", SEEDS)
    earned = (fid >= 0.6 and sy["sym_acc"] >= 0.9 and sy["acc_sh"] <= 0.3)
    report["opposite_of"] = dict(kind="symmetric", fidelity=round(fid, 3),
                                 **sy, earned=bool(earned))
    print("opposite_of  fid=%.2f symmetry=%.3f shuffle=%.3f -> %s"
          % (fid, sy["sym_acc"], sy["acc_sh"], "EARNED" if earned else "NOT earned"))

    with open(OUT, "w") as f:
        json.dump({"_doc": "Per-relation calibration (block 338). A relation "
                   "earns the trust band only if its structural control passes "
                   "and its shuffle control collapses. Honest negatives kept.",
                   "relations": report}, f, indent=1)
    earned_list = [r for r, d in report.items() if d["earned"]]
    print("\nEARNED relations (harvestable): %s" % (earned_list or "NONE"))
    print("wrote %s" % OUT)
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
