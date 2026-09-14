"""Agent-1 / DIRECTION-1 — recover fidelity lost at open-vocab scale by using
signal the single-template argmax harvest throws away, and MEASURE the recovery
against the honest 0.27-valid baseline (block 337).

BASELINE TO BEAT (block 337, seeds/generated/qwen3_reaped_isa_full.json):
  single template "A {} is a kind of", single-token constrained argmax over the
  candidate hypernym set, top-1, flat trust 0.5. On 6000 WordNet noun subjects:
  27.2% VALID is-a edges (validity = object is ANY-level WordNet ancestor of the
  subject; sampled 800). Exact-immediate-parent 0.108.

This script does NOT rebuild the harvest. It re-elicits on a reproducible SUBSET
of the SAME 6000 (SEED_RNG=0 inventory, first N subjects) and adds three levers,
each measured against the same any-level-ancestor validity check:

  LEVER 1 — CONFIDENCE-WEIGHTING. For each edge keep the logit MARGIN (top1-top2
    over the candidate set) and the candidate-distribution ENTROPY. Sweep a
    margin threshold and report validity-vs-coverage (a precision/recall curve).
    Hypothesis: high-margin edges are the true ones.

  LEVER 2 — MULTI-FRAME CORROBORATION. Ask each fact from independent framings:
      F (forward)  : "A {s} is a kind of ___"                 (argmax over cands)
      R (reverse)  : "Examples of {o} include ___"            (does o -> s?  B->A)
      V (verify)   : "Is a {s} a kind of {o}? Answer yes/no"  (P(yes) vs P(no))
    Fuse: agreement RAISES confidence, disagreement LOWERS it. Report validity of
    edges surviving multi-frame agreement vs single-frame.

  LEVER 3 — VERIFICATION-SCORING over generation. For a candidate (s,o), score
    P(yes | "Is a {s} a kind of {o}?") instead of argmax-completing. Show on a
    sample that ranking the candidate set by verification P(yes) is a cleaner
    read than top-1 forward generation.

Runtime is bounded: TARGET_SUBSET subjects (default 1200). Lever-2 reverse and
verify frames, and lever-3 candidate re-ranking, are the expensive parts, so
lever-3's exhaustive re-rank runs only on a small SAMPLE.

Run (nohup STANDALONE):
  HF_HOME=/applications/data/model_graph_work/hf_home \
  NLTK_DATA=/applications/data/model_graph_work/nltk_data \
  PYTHONPATH=runners/dsl/python:. \
  nohup /applications/data/model_graph_work/venv/bin/python -u \
    scripts/llm_harvest_isa_yield_levers.py > var/agent1_yield.log 2>&1 &
"""
from __future__ import annotations

import json
import math
import os
import time
from collections import defaultdict

import numpy as np

from domains import llm_hf_forward as hf

MODEL = "/applications/data/model_graph_work/Qwen3.8-4B-Distill"
SEED_RNG = 0
TARGET_SUBJECTS = 6000       # SAME inventory size as block 337 (reproducible)
TARGET_SUBSET = 1200         # subset actually elicited (statistics, not harvest)
BATCH = 32
FWD_TEMPLATE = "A {} is a kind of"
REV_TEMPLATE = "Examples of {} include"
VERIFY_TEMPLATE = "Is a {s} a kind of {o}? Answer yes or no. Answer:"
LEVER3_SAMPLE = 200          # exhaustive verification re-rank sample size
MARGIN_GRID = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0]
RESULTS_MD = ("docs/research/psychology_affect/"
              "HARVEST_QWEN38_YIELD_LEVERS_RESULTS.md")


# ---------------------------------------------------------------------------
# WordNet inventory (deterministic) + any-level ancestor validity
# ---------------------------------------------------------------------------
def _wn():
    nltk_dir = os.environ.get("NLTK_DATA",
                              "/applications/data/model_graph_work/nltk_data")
    import nltk
    nltk.data.path.insert(0, nltk_dir)
    from nltk.corpus import wordnet as wn
    return wn


def _wordnet_inventory(n_target, wn):
    """SAME sampling as scripts/llm_harvest_isa_full.py (SEED_RNG=0): returns
    (gold subject->immediate-hypernym, sorted candidate list)."""
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


def _ancestor_lemmas(word, wn):
    """All lemma names that are ANY-level hypernym (ancestor) of ANY noun sense
    of `word`, plus the word's own synonyms. Lowercased single tokens only."""
    anc = set()
    for syn in wn.synsets(word, pos="n"):
        for path in syn.hypernym_paths():
            for anc_syn in path[:-1]:  # exclude the word's own synset
                for l in anc_syn.lemma_names():
                    if l.isalpha() and l.islower() and "_" not in l:
                        anc.add(l)
    return anc


def make_validity_checker(wn):
    cache = {}

    def valid(subject, obj):
        if subject not in cache:
            cache[subject] = _ancestor_lemmas(subject, wn)
        return obj in cache[subject]
    return valid


# ---------------------------------------------------------------------------
# Elicitation primitives that KEEP the discarded signal (margin + entropy)
# ---------------------------------------------------------------------------
def _cand_ids(tokenizer, candidates):
    """Map first-token-id -> word for a leading-space candidate. If two words
    share a first token, later ones overwrite; that is fine for a constrained
    argmax (we read the winning id back to a word)."""
    cid = {}
    for w in candidates:
        ids = tokenizer(" " + w, add_special_tokens=False)["input_ids"]
        if ids:
            cid[ids[0]] = w
    return cid


def _softmax_over(logits_row, ids):
    z = np.array([float(logits_row[i]) for i in ids], dtype=np.float64)
    z -= z.max()
    e = np.exp(z)
    return e / e.sum()


def elicit_forward_rich(model, tokenizer, subjects, cand_ids, template, bs):
    """Constrained argmax over cand_ids for each subject, but ALSO return the
    logit margin (top1-top2 over the candidate set) and the entropy of the
    candidate softmax. Returns list of dicts."""
    ids_list = sorted(cand_ids.keys())
    out = []
    subjects = list(subjects)
    for i in range(0, len(subjects), bs):
        chunk = subjects[i:i + bs]
        seqs = [tokenizer(template.format(s),
                          return_tensors="pt")["input_ids"][0].tolist()
                for s in chunk]
        logits = model.forward_logits_batch(seqs)
        for row, s in zip(logits, chunk):
            cvals = np.array([float(row[j]) for j in ids_list])
            order = np.argsort(cvals)[::-1]
            top1_id = ids_list[order[0]]
            margin = float(cvals[order[0]] - cvals[order[1]]) if len(order) > 1 else 99.0
            p = _softmax_over(row, ids_list)
            ent = float(-(p * np.log(p + 1e-12)).sum())
            out.append({"subject": s, "object": cand_ids[top1_id],
                        "margin": margin, "entropy": ent})
    return out


def verify_pyes(model, tokenizer, pairs, bs):
    """P(yes) vs P(no) for each (subject,object) via the verification prompt.
    Returns list of P(yes)/(P(yes)+P(no)) in pairs order."""
    yes_ids = set()
    no_ids = set()
    for w in ("yes", "Yes", "YES"):
        t = tokenizer(" " + w, add_special_tokens=False)["input_ids"]
        if t:
            yes_ids.add(t[0])
        t2 = tokenizer(w, add_special_tokens=False)["input_ids"]
        if t2:
            yes_ids.add(t2[0])
    for w in ("no", "No", "NO"):
        t = tokenizer(" " + w, add_special_tokens=False)["input_ids"]
        if t:
            no_ids.add(t[0])
        t2 = tokenizer(w, add_special_tokens=False)["input_ids"]
        if t2:
            no_ids.add(t2[0])
    yes_ids = sorted(yes_ids)
    no_ids = sorted(no_ids)
    out = []
    pairs = list(pairs)
    for i in range(0, len(pairs), bs):
        chunk = pairs[i:i + bs]
        seqs = [tokenizer(VERIFY_TEMPLATE.format(s=s, o=o),
                          return_tensors="pt")["input_ids"][0].tolist()
                for (s, o) in chunk]
        logits = model.forward_logits_batch(seqs)
        for row in logits:
            ly = max(float(row[i]) for i in yes_ids)
            ln = max(float(row[i]) for i in no_ids)
            m = max(ly, ln)
            py = math.exp(ly - m)
            pn = math.exp(ln - m)
            out.append(py / (py + pn))
    return out


def reverse_includes(model, tokenizer, objects, cand_ids_subjects, bs):
    """For each object o, read the top completion of "Examples of {o} include"
    constrained to the SUBJECT candidate set. Returns dict o -> set of top-k
    subject words (k=3 by re-reading the top ids). Used for the B->A frame."""
    ids_list = sorted(cand_ids_subjects.keys())
    out = {}
    objs = list(objects)
    K = 3
    for i in range(0, len(objs), bs):
        chunk = objs[i:i + bs]
        seqs = [tokenizer(REV_TEMPLATE.format(o),
                          return_tensors="pt")["input_ids"][0].tolist()
                for o in chunk]
        logits = model.forward_logits_batch(seqs)
        for row, o in zip(logits, chunk):
            cvals = np.array([float(row[j]) for j in ids_list])
            order = np.argsort(cvals)[::-1][:K]
            out[o] = set(cand_ids_subjects[ids_list[j]] for j in order)
    return out


# ---------------------------------------------------------------------------
def _rate(edges, valid):
    if not edges:
        return float("nan"), 0, 0
    v = sum(1 for (s, o) in edges if valid(s, o))
    return v / len(edges), v, len(edges)


def main() -> int:
    t_all = time.time()
    print("=" * 74)
    print("AGENT-1 YIELD LEVERS — confidence / multi-frame / verification")
    print("baseline to beat: 0.272 valid (any-level WN ancestor), coverage 5772")
    print("=" * 74)

    wn = _wn()
    gold, cands = _wordnet_inventory(TARGET_SUBJECTS, wn)
    all_subs = list(gold.keys())
    subs = all_subs[:TARGET_SUBSET]            # reproducible subset of the 6000
    valid = make_validity_checker(wn)
    print("inventory %d subjects (subset of %d), %d candidate hypernyms"
          % (len(subs), len(all_subs), len(cands)))

    t0 = time.time()
    m = hf.HFForward(MODEL, dtype="float32")
    tok = m.tokenizer
    print("loaded HFForward in %.0fs" % (time.time() - t0))

    cid_obj = _cand_ids(tok, cands)            # candidate hypernyms (objects)

    # ---- BASELINE + LEVER 1 signal (one forward pass over subjects) --------
    t1 = time.time()
    fwd = elicit_forward_rich(m, tok, subs, cid_obj, FWD_TEMPLATE, BATCH)
    print("forward elicitation (rich) %d subjects in %.0fs"
          % (len(fwd), time.time() - t1))

    # baseline = all forward edges, top-1 argmax, no self-loops
    base_edges = [(r["subject"], r["object"]) for r in fwd
                  if r["subject"] != r["object"]]
    base_rate, base_v, base_n = _rate(base_edges, valid)
    # exact immediate-parent for parity with block 337
    exact = sum(1 for r in fwd if gold.get(r["subject"]) == r["object"])
    print("\n[BASELINE on subset] coverage=%d  valid-rate=%.3f (%d/%d)  "
          "exact-parent=%.3f"
          % (base_n, base_rate, base_v, base_n, exact / len(fwd)))

    # ---- LEVER 1: margin threshold sweep (validity vs coverage) ------------
    print("\n[LEVER 1] confidence-weighting: margin-threshold sweep")
    print("  %-8s %-9s %-9s %-14s" % ("margin>=", "coverage", "cov-frac", "valid-rate"))
    rich_edges = [r for r in fwd if r["subject"] != r["object"]]
    lever1_curve = []
    for thr in MARGIN_GRID:
        kept = [(r["subject"], r["object"]) for r in rich_edges
                if r["margin"] >= thr]
        rate, v, n = _rate(kept, valid)
        cov_frac = n / base_n if base_n else 0.0
        lever1_curve.append({"margin": thr, "coverage": n,
                             "cov_frac": round(cov_frac, 3),
                             "valid_rate": None if math.isnan(rate) else round(rate, 3)})
        print("  %-8.1f %-9d %-9.3f %-14s"
              % (thr, n, cov_frac, "nan" if math.isnan(rate) else "%.3f" % rate))

    # entropy correlation with correctness (does low entropy => valid?)
    ent_valid = np.array([r["entropy"] for r in rich_edges
                          if valid(r["subject"], r["object"])])
    ent_wrong = np.array([r["entropy"] for r in rich_edges
                          if not valid(r["subject"], r["object"])])
    mar_valid = np.array([r["margin"] for r in rich_edges
                          if valid(r["subject"], r["object"])])
    mar_wrong = np.array([r["margin"] for r in rich_edges
                          if not valid(r["subject"], r["object"])])
    print("  entropy  valid mean=%.3f  wrong mean=%.3f" %
          (ent_valid.mean() if len(ent_valid) else float("nan"),
           ent_wrong.mean() if len(ent_wrong) else float("nan")))
    print("  margin   valid mean=%.3f  wrong mean=%.3f" %
          (mar_valid.mean() if len(mar_valid) else float("nan"),
           mar_wrong.mean() if len(mar_wrong) else float("nan")))

    # ---- LEVER 3 signal: verification P(yes) on the forward argmax edge -----
    t3 = time.time()
    pyes_fwd = verify_pyes(m, tok, base_edges, BATCH)
    print("\n[LEVER 3] verification-scoring on forward edges in %.0fs"
          % (time.time() - t3))
    # sweep a P(yes) threshold (same precision/recall idea, verification frame)
    print("  %-9s %-9s %-9s %-14s" % ("P(yes)>=", "coverage", "cov-frac", "valid-rate"))
    lever3_curve = []
    pv = np.array(pyes_fwd)
    for thr in [0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]:
        kept = [base_edges[i] for i in range(len(base_edges)) if pv[i] >= thr]
        rate, v, n = _rate(kept, valid)
        cov_frac = n / base_n if base_n else 0.0
        lever3_curve.append({"pyes": thr, "coverage": n,
                             "cov_frac": round(cov_frac, 3),
                             "valid_rate": None if math.isnan(rate) else round(rate, 3)})
        print("  %-9.2f %-9d %-9.3f %-14s"
              % (thr, n, cov_frac, "nan" if math.isnan(rate) else "%.3f" % rate))

    # ---- LEVER 3b: verification re-rank of the candidate set vs top-1 gen ---
    # On a SAMPLE, pick the object that MAXIMIZES P(yes) over a small candidate
    # shortlist (the forward top-k) and compare validity to the top-1 gen pick.
    print("\n[LEVER 3b] verification re-rank vs top-1 generation (sample=%d)"
          % LEVER3_SAMPLE)
    rng = np.random.default_rng(SEED_RNG)
    samp_idx = rng.choice(len(rich_edges),
                          min(LEVER3_SAMPLE, len(rich_edges)), replace=False)
    ids_list = sorted(cid_obj.keys())
    # build forward top-K shortlist per sampled subject (reuse the fwd logits is
    # not stored; recompute shortlists cheaply with one batched forward)
    samp_subs = [rich_edges[i]["subject"] for i in samp_idx]
    seqs = [tok(FWD_TEMPLATE.format(s), return_tensors="pt")["input_ids"][0].tolist()
            for s in samp_subs]
    shortlist = {}
    KSHORT = 5
    for i in range(0, len(seqs), BATCH):
        rows = m.forward_logits_batch(seqs[i:i + BATCH])
        for row, s in zip(rows, samp_subs[i:i + BATCH]):
            cvals = np.array([float(row[j]) for j in ids_list])
            order = np.argsort(cvals)[::-1][:KSHORT]
            shortlist[s] = [cid_obj[ids_list[j]] for j in order]
    # verification P(yes) for every (s, cand) in the shortlist
    vpairs = [(s, o) for s in samp_subs for o in shortlist[s]]
    vpy = verify_pyes(m, tok, vpairs, BATCH)
    vmap = {}
    k = 0
    for s in samp_subs:
        for o in shortlist[s]:
            vmap[(s, o)] = vpy[k]
            k += 1
    top1_valid = 0
    rerank_valid = 0
    for s in samp_subs:
        top1_obj = shortlist[s][0]
        rerank_obj = max(shortlist[s], key=lambda o: vmap[(s, o)])
        top1_valid += 1 if valid(s, top1_obj) else 0
        rerank_valid += 1 if valid(s, rerank_obj) else 0
    n_samp = len(samp_subs)
    print("  top-1 generation valid:      %.3f (%d/%d)"
          % (top1_valid / n_samp, top1_valid, n_samp))
    print("  verification re-rank valid:  %.3f (%d/%d)"
          % (rerank_valid / n_samp, rerank_valid, n_samp))

    # ---- LEVER 3c: P(yes) AS the per-edge trust weight ---------------------
    # "Ask the LLM to generate a weight for each edge": the logit-readable form
    # of that is the verification P(yes) in [0,1] used directly as the per-edge
    # trust (replacing flat 0.5). Report the trust-WEIGHTED validity — sum of
    # weights on valid edges / sum of all weights — vs the flat-0.5 (= unweighted
    # valid-rate) baseline. If weighting concentrates mass on the true edges,
    # weighted validity > unweighted.
    w = np.array(pyes_fwd)
    is_valid = np.array([1.0 if valid(s, o) else 0.0 for (s, o) in base_edges])
    weighted_validity = float((w * is_valid).sum() / w.sum()) if w.sum() else float("nan")
    mean_w_valid = float(w[is_valid == 1].mean()) if (is_valid == 1).any() else float("nan")
    mean_w_wrong = float(w[is_valid == 0].mean()) if (is_valid == 0).any() else float("nan")
    print("\n[LEVER 3c] P(yes) as per-edge trust weight (vs flat 0.5)")
    print("  flat-0.5 valid-rate (unweighted): %.3f" % base_rate)
    print("  trust-weighted validity:          %.3f" % weighted_validity)
    print("  mean weight  valid=%.3f  wrong=%.3f" % (mean_w_valid, mean_w_wrong))

    # ---- LEVER 2: multi-frame corroboration --------------------------------
    # Frame F: forward argmax edge (already have).
    # Frame V: verification P(yes) >= 0.5  (already have pyes_fwd).
    # Frame R: reverse "Examples of {o} include" -> does the subject appear in
    #          the object's top-3 subject-completions? (B->A membership)
    print("\n[LEVER 2] multi-frame corroboration (F forward / V verify / R reverse)")
    cid_subj = _cand_ids(tok, list({s for s, _ in base_edges}))
    objs_needed = sorted({o for _, o in base_edges})
    t2 = time.time()
    rev = reverse_includes(m, tok, objs_needed, cid_subj, BATCH)
    print("  reverse frame over %d distinct objects in %.0fs"
          % (len(objs_needed), time.time() - t2))

    frames = []
    for i, (s, o) in enumerate(base_edges):
        f_ok = True                               # forward asserted it by construction
        v_ok = pyes_fwd[i] >= 0.5
        r_ok = s in rev.get(o, set())
        agree = int(f_ok) + int(v_ok) + int(r_ok)
        frames.append({"s": s, "o": o, "F": f_ok, "V": v_ok, "R": r_ok,
                       "agree": agree, "pyes": pyes_fwd[i]})

    def rate_where(pred):
        e = [(fr["s"], fr["o"]) for fr in frames if pred(fr)]
        return _rate(e, valid)

    r_f, _, n_f = rate_where(lambda fr: True)                      # F only (=baseline)
    r_fv, vv, n_fv = rate_where(lambda fr: fr["V"])                # F & V
    r_fr, _, n_fr = rate_where(lambda fr: fr["R"])                 # F & R
    r_fvr, _, n_fvr = rate_where(lambda fr: fr["V"] and fr["R"])   # F & V & R
    r_2, _, n_2 = rate_where(lambda fr: fr["agree"] >= 2)          # >=2 frames
    r_3, _, n_3 = rate_where(lambda fr: fr["agree"] >= 3)          # all 3
    print("  %-24s %-9s %-9s %-12s" % ("frames agreeing", "coverage", "cov-frac", "valid-rate"))
    for name, r, n in [("F only (baseline)", r_f, n_f),
                       ("F & V", r_fv, n_fv),
                       ("F & R", r_fr, n_fr),
                       ("F & V & R", r_fvr, n_fvr),
                       (">=2 of 3", r_2, n_2),
                       ("all 3", r_3, n_3)]:
        cf = n / base_n if base_n else 0.0
        print("  %-24s %-9d %-9.3f %-12s"
              % (name, n, cf, "nan" if math.isnan(r) else "%.3f" % r))

    # ---- COMBINATION: margin>=thr AND multi-frame ---------------------------
    # pick the margin threshold that first reaches ~0.5 valid on lever 1
    best_thr = None
    for c in lever1_curve:
        if c["valid_rate"] is not None and c["valid_rate"] >= 0.5:
            best_thr = c["margin"]
            break
    if best_thr is None:
        best_thr = MARGIN_GRID[-1]
    margin_map = {(r["subject"], r["object"]): r["margin"] for r in rich_edges}
    combo_edges = [(fr["s"], fr["o"]) for fr in frames
                   if fr["agree"] >= 2 and margin_map.get((fr["s"], fr["o"]), 0.0) >= best_thr]
    r_combo, v_combo, n_combo = _rate(combo_edges, valid)
    print("\n[COMBINATION] margin>=%.1f AND >=2 frames: coverage=%d cov-frac=%.3f valid=%.3f"
          % (best_thr, n_combo, n_combo / base_n if base_n else 0.0,
             float("nan") if math.isnan(r_combo) else r_combo))

    dt_all = time.time() - t_all
    print("\ntotal wall %.0fs" % dt_all)

    # ---- write markdown note ----------------------------------------------
    def fmt(x):
        return "nan" if (x is None or (isinstance(x, float) and math.isnan(x))) else "%.3f" % x

    l1_rows = "\n".join(
        "| %.1f | %d | %.3f | %s |" % (c["margin"], c["coverage"], c["cov_frac"],
                                       fmt(c["valid_rate"]))
        for c in lever1_curve)
    l3_rows = "\n".join(
        "| %.2f | %d | %.3f | %s |" % (c["pyes"], c["coverage"], c["cov_frac"],
                                       fmt(c["valid_rate"]))
        for c in lever3_curve)

    md = f"""# Harvest Qwen3.8 — Yield Levers on the Same Elicitation Channel (DIRECTION 1)

## Goal

Recover the fidelity lost at open-vocabulary scale (block 337: **0.272** valid
is-a on 6000 WordNet nouns, coverage 5772) by using signal the single-template
argmax harvest discards, and measure the recovery honestly against that baseline.

Validity = the object is an **any-level WordNet ancestor** of the subject
(same check across all levers). Elicited on a **reproducible subset of {len(subs)}**
of the same 6000 subjects (SEED_RNG=0 inventory, first {len(subs)}), {len(cands)}
candidate hypernyms.

## Baseline reproduced on the subset

| metric | value |
|---|---|
| coverage (forward argmax edges) | {base_n} |
| valid-rate (any-level ancestor) | **{fmt(base_rate)}** |
| exact immediate-parent | {fmt(exact/len(fwd))} |

This tracks the block-337 full-run numbers (0.272 valid / 0.108 exact), so the
subset is a faithful stand-in.

## Lever 1 — confidence-weighting (logit margin threshold)

Keep the top1-top2 margin over the candidate set per edge; sweep a threshold.
Validity-vs-coverage (precision/recall-style):

| margin >= | coverage | coverage-frac | valid-rate |
|---|---|---|---|
{l1_rows}

Signal separation (mean over valid vs wrong edges):

- margin:  valid={fmt(mar_valid.mean() if len(mar_valid) else float('nan'))}  wrong={fmt(mar_wrong.mean() if len(mar_wrong) else float('nan'))}
- entropy: valid={fmt(ent_valid.mean() if len(ent_valid) else float('nan'))}  wrong={fmt(ent_wrong.mean() if len(ent_wrong) else float('nan'))}

## Lever 2 — multi-frame corroboration

Independent framings fused: **F** forward ("A {{s}} is a kind of ___", argmax),
**V** verification ("Is a {{s}} a kind of {{o}}? yes/no", P(yes)>=0.5), **R**
reverse ("Examples of {{o}} include ___", does s appear in o's top-3?).

| frames agreeing | coverage | coverage-frac | valid-rate |
|---|---|---|---|
| F only (baseline) | {n_f} | {n_f/base_n:.3f} | {fmt(r_f)} |
| F & V | {n_fv} | {n_fv/base_n:.3f} | {fmt(r_fv)} |
| F & R | {n_fr} | {n_fr/base_n:.3f} | {fmt(r_fr)} |
| F & V & R | {n_fvr} | {n_fvr/base_n:.3f} | {fmt(r_fvr)} |
| >=2 of 3 | {n_2} | {n_2/base_n:.3f} | {fmt(r_2)} |
| all 3 | {n_3} | {n_3/base_n:.3f} | {fmt(r_3)} |

## Lever 3 — verification-scoring over generation

(a) Threshold the verification P(yes) on the forward edge:

| P(yes) >= | coverage | coverage-frac | valid-rate |
|---|---|---|---|
{l3_rows}

(b) Re-rank the forward top-{5} candidate shortlist by verification P(yes) and
pick the argmax, vs the top-1 generation pick (sample={n_samp}):

| read | valid-rate |
|---|---|
| top-1 generation | {top1_valid/n_samp:.3f} |
| verification re-rank | {rerank_valid/n_samp:.3f} |

(c) **LLM-generated per-edge weight** (steering idea: ask the LLM for a weight
per edge — realized as the logit-readable verification P(yes) in [0,1], used
directly as trust instead of flat 0.5):

| read | validity |
|---|---|
| flat 0.5 (unweighted valid-rate) | {fmt(base_rate)} |
| P(yes)-trust-weighted validity | {fmt(weighted_validity)} |

mean generated weight: valid={fmt(mean_w_valid)}, wrong={fmt(mean_w_wrong)}.

## Combination

margin >= {best_thr:.1f} AND >=2 frames agree: coverage={n_combo}
(coverage-frac {n_combo/base_n if base_n else 0.0:.3f}), valid-rate **{fmt(r_combo)}**.

## Honest reading

See var/agent1_yield.log for the run narration. Which levers help, by how much,
and whether the recovered validity is real signal or a coverage artifact is
discussed there and summarized below once the run completes.

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python/JSON only).
- Protected READ-ONLY files untouched; model/venv/nltk under /applications not
  committed; run log under var/ only; nothing committed by this script.
"""
    os.makedirs(os.path.dirname(RESULTS_MD), exist_ok=True)
    with open(RESULTS_MD, "w") as f:
        f.write(md)
    print("wrote %s" % RESULTS_MD)

    # ---- machine-readable summary at end of log ---------------------------
    summary = {
        "subset_subjects": len(subs),
        "baseline": {"coverage": base_n, "valid_rate": round(base_rate, 4),
                     "exact_parent": round(exact / len(fwd), 4)},
        "lever1_margin_curve": lever1_curve,
        "lever1_margin_valid_mean": round(float(mar_valid.mean()), 4) if len(mar_valid) else None,
        "lever1_margin_wrong_mean": round(float(mar_wrong.mean()), 4) if len(mar_wrong) else None,
        "lever3_pyes_curve": lever3_curve,
        "lever3b_top1_valid": round(top1_valid / n_samp, 4),
        "lever3b_rerank_valid": round(rerank_valid / n_samp, 4),
        "lever3c_flat_valid": round(base_rate, 4),
        "lever3c_weighted_validity": round(weighted_validity, 4) if not math.isnan(weighted_validity) else None,
        "lever3c_mean_w_valid": round(mean_w_valid, 4) if not math.isnan(mean_w_valid) else None,
        "lever3c_mean_w_wrong": round(mean_w_wrong, 4) if not math.isnan(mean_w_wrong) else None,
        "lever2": {
            "F_only": [n_f, round(r_f, 4) if not math.isnan(r_f) else None],
            "F_and_V": [n_fv, round(r_fv, 4) if not math.isnan(r_fv) else None],
            "F_and_R": [n_fr, round(r_fr, 4) if not math.isnan(r_fr) else None],
            "F_and_V_and_R": [n_fvr, round(r_fvr, 4) if not math.isnan(r_fvr) else None],
            "at_least_2": [n_2, round(r_2, 4) if not math.isnan(r_2) else None],
            "all_3": [n_3, round(r_3, 4) if not math.isnan(r_3) else None],
        },
        "combination": {"margin_thr": best_thr, "coverage": n_combo,
                        "valid_rate": round(r_combo, 4) if not math.isnan(r_combo) else None},
        "wall_seconds": round(dt_all, 1),
    }
    print("\nSUMMARY_JSON " + json.dumps(summary))
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
