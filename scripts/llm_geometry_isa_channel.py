"""DIRECTION 2 — read is-a structure from REPRESENTATION GEOMETRY (hidden states)
instead of eliciting it via templated Q&A.

Continuous with the mechanism-recovery arc (blocks 318-329): the hypothesis is
that the is-a (hypernymy) structure is already LINEARLY present in the qwen3_5
residual stream, and that reading the geometry beats the lossy single-token
generation read. Baseline to beat (block 337, scripts/llm_harvest_isa_full.py):
templated constrained-argmax elicitation gets 0.272 VALID is-a edges on
open-vocab WordNet nouns (validity = object is ANY-level WordNet ancestor of the
subject).

THE QUESTION: does the hidden-state geometry SEPARATE true is-a pairs from false
ones better than templated Q&A, and does it PICK the true parent more often than
argmax on the SAME held-out subjects?

METHOD (all additive; no protected file touched, no .so rebuilt):
  1. Inventory: reuse the _wordnet_inventory pattern (SEED_RNG=0) for a bounded
     set of (child, immediate_parent) gold pairs. Split train / held-out by
     SUBJECT (no leakage of a subject across splits).
  2. Representation: one HF forward per distinct word via hidden_all_layers ->
     last-token hidden state at every layer (0=embeddings .. 32=post-block).
     Words may be multi-token; hidden_at/hidden_all_layers return the LAST-token
     state by design (documented choice). Subjects AND candidate parents are
     embedded identically so their geometry is comparable.
  3. Readers fit on TRAIN, scored on HELD-OUT, per layer:
       (a) OFFSET direction  delta = mean(parent - child); pred = child + delta,
           retrieve nearest candidate by cosine.
       (b) AFFINE map W (ridge) child -> parent; pred = W child, retrieve
           nearest.
       (c) LINEAR PROBE (logistic) on pair features [child, parent, parent-child]
           classifying true vs false pair -> separability AUC.
     Retrieval accuracy = does the reader rank a VALID ancestor top-1 among all
     candidate parents (matches the baseline's validity definition). Also report
     exact-immediate-parent top-1.
  4. CONTROLS (must collapse to chance, exactly like the elicitation controls):
       - RANDOM-direction control: replace delta with a random gaussian vector.
       - SHUFFLED-pairs control: permute parent labels in TRAIN before fitting.
  5. HEAD-TO-HEAD: run the templated constrained-argmax elicitation
     (llm_knowledge_seed.elicit_isa_batch) on the IDENTICAL held-out subjects
     with the IDENTICAL candidate set, and compare valid-ancestor rate side by
     side with the geometry reader.

HONEST FRAMING: the prior concept-probe attempt (block 328) got weak antonym AUC
0.59 and a control FAILED, so a probe "working" is proven ONLY against the
random+shuffle controls. If geometry does NOT beat elicitation, that is a real
negative result and is reported as such.

Run (nohup STANDALONE):
  HF_HOME=/applications/data/model_graph_work/hf_home \
  NLTK_DATA=/applications/data/model_graph_work/nltk_data \
  PYTHONPATH=runners/dsl/python:. \
  nohup /applications/data/model_graph_work/venv/bin/python -u \
    scripts/llm_geometry_isa_channel.py > var/agent2_channel.log 2>&1 &
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
SEED_RNG = 0
TARGET_PAIRS = 1200          # bounded inventory (train+held-out), ~1200 forwards
HELDOUT_FRAC = 0.35          # fraction of subjects held out
TEMPLATE = "A {} is a kind of"   # identical to the elicitation baseline
RIDGE = 10.0
OUT_JSON = "var/agent2_channel_metrics.json"


# ---------------------------------------------------------------------------
# Inventory (reuse block-337 pattern). Also keep the FULL ancestor cone per
# subject so validity == "object is ANY-level WordNet ancestor" (baseline defn).
# ---------------------------------------------------------------------------
def _wordnet_inventory(n_target):
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

    gold = {}            # subject -> immediate parent lemma
    subj_syn = {}        # subject -> its synset (for the ancestor cone)
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
        subj_syn[s] = syn
    cands = sorted(set(gold.values()) | set(gold.keys()))

    # full ancestor cone (ANY level) per subject, as lemma strings
    cone = {}
    for s, syn in subj_syn.items():
        anc = set()
        for path in syn.hypernym_paths():
            for a in path:
                if a == syn:
                    continue
                for l in a.lemma_names():
                    if l.isalpha() and l.islower() and "_" not in l:
                        anc.add(l)
        cone[s] = anc
    return gold, cands, cone


# ---------------------------------------------------------------------------
# Representation: last-token hidden state at every layer, one forward per word.
# ---------------------------------------------------------------------------
def embed_words(model, tokenizer, words, template):
    """Returns H[word] = np.ndarray [n_layers+1, d] (last-token hidden state at
    each layer for `template.format(word)`). One HF forward per distinct word."""
    H = {}
    t0 = time.time()
    for i, w in enumerate(words):
        ids = tokenizer(template.format(w), return_tensors="pt")["input_ids"][0].tolist()
        layers = model.hidden_all_layers(ids)      # list [d] over layers
        H[w] = np.stack(layers).astype(np.float32)  # [L, d]
        if (i + 1) % 200 == 0:
            print("  embedded %d/%d words (%.0fs)" % (i + 1, len(words),
                                                      time.time() - t0),
                  flush=True)
    return H


def _l2(x):
    n = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / (n + 1e-9)


# ---------------------------------------------------------------------------
# Readers (fit on TRAIN, all per-layer).
# ---------------------------------------------------------------------------
def fit_offset(child_mat, parent_mat):
    """delta = mean(parent - child)."""
    return (parent_mat - child_mat).mean(axis=0)


def fit_affine(child_mat, parent_mat, ridge):
    """Ridge: child -> parent. Returns W [d,d]."""
    X, Y = child_mat, parent_mat
    d = X.shape[1]
    A = X.T @ X + ridge * np.eye(d, dtype=np.float32)
    return np.linalg.solve(A, X.T @ Y).T.astype(np.float32)


def retrieve_topk(pred_vecs, cand_words, cand_mat, subjects, valid_fn,
                  exact_parents, topk=5):
    """For each subject's predicted vector, rank candidate parents by cosine;
    report valid@1 (any-ancestor) and exact@1 (immediate parent). A candidate
    equal to the subject itself is excluded."""
    P = _l2(pred_vecs)                  # [N, d]
    C = _l2(cand_mat)                   # [M, d]
    sims = P @ C.T                      # [N, M]
    cand_index = {w: j for j, w in enumerate(cand_words)}
    valid1 = exact1 = 0
    for i, s in enumerate(subjects):
        row = sims[i].copy()
        if s in cand_index:
            row[cand_index[s]] = -2.0   # exclude self
        order = np.argsort(-row)
        top1 = cand_words[order[0]]
        if valid_fn(s, top1):
            valid1 += 1
        if top1 == exact_parents.get(s):
            exact1 += 1
    n = len(subjects)
    return valid1 / n, exact1 / n


def pair_auc(child_mat_tr, parent_mat_tr, child_mat_te, parent_mat_te,
             neg_parent_mat_te, rng):
    """Logistic probe on [child, parent, parent-child] classifying true vs false
    pair; AUC on held-out (true pairs vs child-with-random-wrong-parent)."""
    def feats(c, p):
        return np.concatenate([c, p, p - c], axis=1)
    # build train negatives by shuffling parents
    perm = rng.permutation(len(parent_mat_tr))
    Xpos = feats(child_mat_tr, parent_mat_tr)
    Xneg = feats(child_mat_tr, parent_mat_tr[perm])
    Xtr = np.concatenate([Xpos, Xneg], 0)
    ytr = np.concatenate([np.ones(len(Xpos)), np.zeros(len(Xneg))])
    # standardize + logistic (numpy, ridge-regularized IRLS-free grad)
    mu = Xtr.mean(0); sd = Xtr.std(0) + 1e-6
    Xtr = (Xtr - mu) / sd
    w = np.zeros(Xtr.shape[1], dtype=np.float32); b = 0.0
    lr, lam = 0.5, 1e-3
    for _ in range(400):
        z = Xtr @ w + b
        p = 1.0 / (1.0 + np.exp(-z))
        g = p - ytr
        w -= lr * (Xtr.T @ g / len(ytr) + lam * w)
        b -= lr * g.mean()
    # held-out scoring
    Xte_pos = (feats(child_mat_te, parent_mat_te) - mu) / sd
    Xte_neg = (feats(child_mat_te, neg_parent_mat_te) - mu) / sd
    sp = Xte_pos @ w + b
    sn = Xte_neg @ w + b
    return _auc(sp, sn)


def _auc(pos_scores, neg_scores):
    """AUC = P(pos > neg) via rank statistic."""
    y = np.concatenate([np.ones(len(pos_scores)), np.zeros(len(neg_scores))])
    s = np.concatenate([pos_scores, neg_scores])
    order = np.argsort(s)
    ranks = np.empty(len(s)); ranks[order] = np.arange(1, len(s) + 1)
    n_pos = len(pos_scores); n_neg = len(neg_scores)
    auc = (ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
    return float(auc)


def main() -> int:
    print("=" * 74)
    print("GEOMETRY CHANNEL for is-a — DIRECTION 2 (qwen3_5 hidden states)")
    print("=" * 74)
    t_inv = time.time()
    gold, cands, cone = _wordnet_inventory(TARGET_PAIRS)
    subs = list(gold.keys())
    print("WordNet inventory: %d (child,parent) pairs, %d candidate parents (%.0fs)"
          % (len(subs), len(cands), time.time() - t_inv), flush=True)

    def valid_fn(subject, obj):
        # baseline validity: obj is ANY-level ancestor of subject
        return obj in cone.get(subject, set())

    # split by subject
    rng = np.random.default_rng(SEED_RNG)
    order = rng.permutation(len(subs))
    n_te = int(len(subs) * HELDOUT_FRAC)
    te_subs = [subs[i] for i in order[:n_te]]
    tr_subs = [subs[i] for i in order[n_te:]]
    print("split: %d train subjects, %d held-out subjects" % (len(tr_subs), len(te_subs)),
          flush=True)

    # candidate parent set for retrieval = all gold parents (open-vocab-ish),
    # matching the baseline's constrained candidate pool spirit.
    cand_parents = sorted(set(gold.values()))
    print("retrieval candidate parents: %d" % len(cand_parents), flush=True)

    # ---- load model, embed all distinct words once ----------------------
    t0 = time.time()
    m = hf.HFForward(MODEL, dtype="float32")
    tok = m.tokenizer
    print("loaded HFForward in %.0fs; n_layers=%d" % (time.time() - t0, m.n_layers),
          flush=True)

    words = sorted(set(subs) | set(cand_parents))
    print("embedding %d distinct words (one forward each)..." % len(words), flush=True)
    t1 = time.time()
    H = embed_words(m, tok, words, TEMPLATE)
    n_layers = next(iter(H.values())).shape[0]
    print("embedded %d words across %d layers in %.0fs"
          % (len(words), n_layers, time.time() - t1), flush=True)

    # ---- head-to-head: templated elicitation on held-out subjects -------
    t2 = time.time()
    el_pairs = ks.elicit_isa_batch(m, tok, te_subs, candidates=cand_parents,
                                   template=TEMPLATE, batch_size=32)
    el_valid = sum(1 for s, o in el_pairs if valid_fn(s, o)) / len(el_pairs)
    el_exact = sum(1 for s, o in el_pairs if gold.get(s) == o) / len(el_pairs)
    print("ELICITATION baseline on held-out: valid@1=%.3f exact@1=%.3f  (%.0fs)"
          % (el_valid, el_exact, time.time() - t2), flush=True)

    # ---- STEERING probe: "ask the LLM to generate weights" --------------
    # The Q&A channel already emits a full softmax over the candidate parents.
    # Read that as a model-generated CONFIDENCE per (subject, argmax-object) and
    # test whether the elicitation is separable / calibrated by it: does keeping
    # only high-confidence picks raise validity, and does confidence rank valid
    # picks above invalid ones (AUC)? This is a cheap in-channel check of the
    # "let the LLM generate weights" idea, kept alongside (not instead of) the
    # geometry direction this agent owns.
    cand_first_ids = {}
    for w in cand_parents:
        ids = tok(" " + w, add_special_tokens=False)["input_ids"]
        if ids:
            cand_first_ids.setdefault(ids[0], w)
    tid_list = list(cand_first_ids.keys())
    el_conf = []          # model softmax prob of the chosen candidate
    el_isvalid = []
    seqs = [tok(TEMPLATE.format(s), return_tensors="pt")["input_ids"][0].tolist()
            for s in te_subs]
    for i in range(0, len(seqs), 32):
        chunk = seqs[i:i + 32]
        logits = m.forward_logits_batch(chunk)          # [b, vocab]
        sub_logits = logits[:, tid_list]                 # restrict to candidates
        sub_logits = sub_logits - sub_logits.max(1, keepdims=True)
        probs = np.exp(sub_logits); probs /= probs.sum(1, keepdims=True)
        for r, s in zip(probs, te_subs[i:i + 32]):
            j = int(np.argmax(r))
            obj = cand_first_ids[tid_list[j]]
            el_conf.append(float(r[j]))
            el_isvalid.append(1 if valid_fn(s, obj) else 0)
    el_conf = np.array(el_conf); el_isvalid = np.array(el_isvalid)
    conf_auc = _auc(el_conf[el_isvalid == 1], el_conf[el_isvalid == 0]) \
        if el_isvalid.sum() and (1 - el_isvalid).sum() else float("nan")
    # validity among the top-half most-confident picks
    med = np.median(el_conf)
    hi = el_isvalid[el_conf >= med]
    hiconf_valid = float(hi.mean()) if len(hi) else float("nan")
    print("STEERING (LLM-generated weights) confidence-AUC=%.3f; "
          "valid@1 among top-half confident=%.3f (vs all=%.3f)"
          % (conf_auc, hiconf_valid, el_valid), flush=True)

    # ---- precompute per-layer matrices ----------------------------------
    def mat(word_list, layer):
        return np.stack([H[w][layer] for w in word_list]).astype(np.float32)

    # held-out negatives for AUC: each held-out child paired with a random
    # WRONG parent (not in its ancestor cone)
    cp_arr = np.array(cand_parents, dtype=object)
    neg_parent_word = {}
    for s in te_subs:
        while True:
            cand = str(rng.choice(cp_arr))
            if cand not in cone.get(s, set()) and cand != s:
                neg_parent_word[s] = cand
                break

    results = {"layers": [], "meta": {
        "n_train": len(tr_subs), "n_heldout": len(te_subs),
        "n_cand_parents": len(cand_parents), "template": TEMPLATE,
        "elicitation_valid_at1": round(el_valid, 4),
        "elicitation_exact_at1": round(el_exact, 4),
        "steering_confidence_auc": round(conf_auc, 4),
        "steering_hiconf_valid_at1": round(hiconf_valid, 4),
        "baseline_block337_valid": 0.272,
    }}

    print("\nLAYER SWEEP (valid@1 = obj is ANY-level ancestor, matches baseline)")
    print("%-5s | %-19s | %-19s | %-8s | %-8s | %-8s"
          % ("layer", "offset valid/exact", "affine valid/exact", "probeAUC",
             "randOff", "shufOff"))
    print("-" * 90)

    best = {"valid": -1.0}
    for L in range(n_layers):
        cm_tr = mat(tr_subs, L); pm_tr = mat([gold[s] for s in tr_subs], L)
        cm_te = mat(te_subs, L)
        cand_mat = mat(cand_parents, L)
        pm_te = mat([gold[s] for s in te_subs], L)
        npm_te = mat([neg_parent_word[s] for s in te_subs], L)

        # (a) offset
        delta = fit_offset(cm_tr, pm_tr)
        off_valid, off_exact = retrieve_topk(cm_te + delta, cand_parents,
                                             cand_mat, te_subs, valid_fn, gold)
        # (b) affine
        W = fit_affine(cm_tr, pm_tr, RIDGE)
        aff_valid, aff_exact = retrieve_topk(cm_te @ W.T, cand_parents,
                                             cand_mat, te_subs, valid_fn, gold)
        # (c) probe AUC
        auc = pair_auc(cm_tr, pm_tr, cm_te, pm_te, npm_te,
                       np.random.default_rng(SEED_RNG + 1))

        # CONTROL: random direction (same norm as delta)
        rdir = rng.standard_normal(delta.shape).astype(np.float32)
        rdir = rdir / (np.linalg.norm(rdir) + 1e-9) * np.linalg.norm(delta)
        rand_valid, _ = retrieve_topk(cm_te + rdir, cand_parents, cand_mat,
                                      te_subs, valid_fn, gold)
        # CONTROL: shuffled-pairs offset (permute train parents)
        perm = rng.permutation(len(pm_tr))
        delta_sh = fit_offset(cm_tr, pm_tr[perm])
        shuf_valid, _ = retrieve_topk(cm_te + delta_sh, cand_parents, cand_mat,
                                      te_subs, valid_fn, gold)

        row = {"layer": L,
               "offset_valid": round(off_valid, 4), "offset_exact": round(off_exact, 4),
               "affine_valid": round(aff_valid, 4), "affine_exact": round(aff_exact, 4),
               "probe_auc": round(auc, 4),
               "rand_ctrl_valid": round(rand_valid, 4),
               "shuf_ctrl_valid": round(shuf_valid, 4)}
        results["layers"].append(row)
        print("%-5d | %6.3f / %6.3f     | %6.3f / %6.3f     | %6.3f   | %6.3f   | %6.3f"
              % (L, off_valid, off_exact, aff_valid, aff_exact, auc,
                 rand_valid, shuf_valid), flush=True)

        best_layer_valid = max(off_valid, aff_valid)
        if best_layer_valid > best["valid"]:
            best = {"valid": best_layer_valid, "layer": L,
                    "offset_valid": off_valid, "affine_valid": aff_valid,
                    "probe_auc": auc, "rand_ctrl": rand_valid,
                    "shuf_ctrl": shuf_valid,
                    "reader": "affine" if aff_valid >= off_valid else "offset"}

    results["best"] = best

    print("\n" + "=" * 74)
    print("HEAD-TO-HEAD on identical held-out subjects (validity = ANY ancestor)")
    print("  elicitation (templated argmax) valid@1 : %.3f" % el_valid)
    print("  geometry best-layer (L%d, %s) valid@1  : %.3f"
          % (best["layer"], best["reader"], best["valid"]))
    print("  block-337 open-vocab baseline          : 0.272")
    print("  random-direction control (L%d)         : %.3f" % (best["layer"], best["rand_ctrl"]))
    print("  shuffled-pairs control (L%d)           : %.3f" % (best["layer"], best["shuf_ctrl"]))
    print("  probe separability AUC (L%d)           : %.3f" % (best["layer"], best["probe_auc"]))
    delta_vs_elicit = best["valid"] - el_valid
    verdict = ("GEOMETRY BEATS ELICITATION" if delta_vs_elicit > 0.02
               else "GEOMETRY DOES NOT BEAT ELICITATION (negative result)")
    print("  VERDICT: %s (Δ=%.3f vs elicitation)" % (verdict, delta_vs_elicit))
    print("=" * 74)
    results["meta"]["verdict"] = verdict
    results["meta"]["geometry_best_valid"] = round(best["valid"], 4)
    results["meta"]["delta_vs_elicitation"] = round(delta_vs_elicit, 4)

    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=1)
    print("wrote %s" % OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
