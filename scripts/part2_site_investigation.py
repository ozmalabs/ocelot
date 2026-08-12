#!/usr/bin/env python3
"""scripts/part2_site_investigation.py — AR3 investigation for the four
remaining `keywords_text`-family sites this rung's PREREG names but does not
assume a fix for: `reflective_faculty.py` A3 (`:4183`, SeedSummary seed-skip
pick), A4 (`_EDIT_OPS`, EditOp Argmax), A5 (`_compose_knob_variant`,
ApertureBudget attr Argmax), and A6 (`_compose_rule_literal_variant`,
where-literal-candidate Argmax) — per
`docs/research/engine_substrate/RULE_SIGNATURE_PRODUCTION_WIRING_PREREG.md`
AR3. Read-only: mints no new node types, calls no production write path,
only reads real held state after a full boot and compares candidate scoring
functions offline.

Nothing here is agent decision logic — it is investigation tooling, the
same class as `scripts/rule_signature_measure.py`.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble(strict=False)

from substrate.boot_core import boot_core  # noqa: E402
from substrate.boot_all import load_all_seeds  # noqa: E402
import domains.reflective_faculty as rf  # noqa: E402
import domains.rule_signature as rsig  # noqa: E402


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


# ---------------------------------------------------------------------------
# A6 — _compose_rule_literal_variant's (rule, where-literal) Argmax.
# Compare _collect_vocab_tokens-based overlap vs rule_signature-substring
# overlap, over the REAL writes_where_literal population, on a battery of
# real content-word probes drawn from actual comparison subtrees found in
# this population (never invented).
# ---------------------------------------------------------------------------

def _a6_population(ag):
    rf._ensure_where_literal_rule_provenance(ag.s, ag.inner)
    pop = []
    import json as _json
    for n in ag.s.nodes("RuleSummary"):
        at = ag.s.node(n)["attrs"]
        if at.get("writes_where_literal") != 1.0 or at.get("skippable") != 1.0:
            continue
        try:
            rule_json = _json.loads(at.get("rule_json") or "{}")
        except Exception:
            continue
        cands = rf._find_where_lits(rule_json.get("where"))
        for i, cand in enumerate(cands):
            pop.append({"rule": at.get("name"), "idx": i, "cand": cand})
    return pop


def _a6_vocab_score(cand, words):
    vocab = rf._collect_vocab_tokens(cand)
    return sum(1 for w in words if w in vocab)


def _a6_sig_score(cand, words):
    sig = rsig.rule_signature(cand)
    matched = [row for row in sig if any(w in repr(row) for w in words)]
    return len(matched)


def investigate_a6(ag):
    pop = _a6_population(ag)
    print(f"A6: real (rule, where-literal) candidate pairs: {len(pop)}", flush=True)
    # Build probes from the REAL vocabulary discovered in this population
    # (never invented): every distinct 2-word vocab pair drawn from a single
    # candidate's own _collect_vocab_tokens is a natural "this candidate is
    # genuinely named" probe under the existing >=2-word guard.
    probes = []
    seen_targets = set()
    for row in pop:
        vocab = sorted(rf._collect_vocab_tokens(row["cand"]))
        if len(vocab) >= 2 and row["rule"] not in seen_targets:
            probes.append({"target_rule": row["rule"], "target_idx": row["idx"], "words": vocab[:3]})
            seen_targets.add(row["rule"])
    print(f"A6: probes constructed from real candidate vocab: {len(probes)}", flush=True)

    disagreements = []
    same_pick = 0
    for p in probes:
        words = p["words"]
        vocab_best = None   # (score, rule, idx)
        sig_best = None
        for row in pop:
            vs = _a6_vocab_score(row["cand"], words)
            if vs >= 2 and (vocab_best is None or vs > vocab_best[0]):
                vocab_best = (vs, row["rule"], row["idx"])
            ss = _a6_sig_score(row["cand"], words)
            if ss >= 2 and (sig_best is None or ss > sig_best[0]):
                sig_best = (ss, row["rule"], row["idx"])
        vpick = (vocab_best[1], vocab_best[2]) if vocab_best else None
        spick = (sig_best[1], sig_best[2]) if sig_best else None
        if vpick == spick:
            same_pick += 1
        else:
            disagreements.append({"words": words, "target": (p["target_rule"], p["target_idx"]),
                                   "vocab_pick": vpick, "sig_pick": spick})
    print(f"A6: {same_pick}/{len(probes)} probes pick the SAME (rule, literal) under both scorers", flush=True)
    for d in disagreements[:10]:
        print(f"  DISAGREE words={d['words']} target={d['target']} vocab={d['vocab_pick']} sig={d['sig_pick']}", flush=True)
    return {"n_pairs": len(pop), "n_probes": len(probes), "same_pick": same_pick,
            "disagreements": disagreements}


# ---------------------------------------------------------------------------
# A4 — EditOp Argmax. Measure real collision risk among the 4 hand-authored
# keywords_text blurbs against realistic axis_preds probes (reused from the
# rule_signature_measure.py oracle's own residual-predicate vocabulary,
# since EditOp is scored against exactly that vocabulary in production).
# ---------------------------------------------------------------------------

def investigate_a4(ag):
    rf._ensure_edit_ops(ag.s)
    ops = []
    for n in ag.s.nodes("EditOp"):
        at = ag.s.node(n)["attrs"]
        ops.append((at.get("kind"), at.get("keywords_text", "")))
    print(f"A4: EditOp population: {len(ops)} — {[o[0] for o in ops]}", flush=True)
    # cross-blurb word overlap (collision risk BEFORE any concern is even
    # considered — do the 4 hand-written blurbs share vocabulary with each
    # other at all?)
    blurb_words = {kind: set(txt.split()) for kind, txt in ops}
    collisions = []
    kinds = list(blurb_words)
    for i in range(len(kinds)):
        for j in range(i + 1, len(kinds)):
            shared = blurb_words[kinds[i]] & blurb_words[kinds[j]]
            if shared:
                collisions.append((kinds[i], kinds[j], sorted(shared)))
    print(f"A4: cross-blurb word collisions among the 4 ops: {collisions}", flush=True)
    return {"ops": ops, "cross_blurb_collisions": collisions}


# ---------------------------------------------------------------------------
# A5 — _compose_knob_variant's ApertureBudget attr Argmax. Measure the real
# attr-key collision structure (families sharing a '_'-split word) on the
# REAL held ApertureBudget rows.
# ---------------------------------------------------------------------------

def investigate_a5(ag):
    rows = []
    for n in ag.s.nodes("ApertureBudget"):
        at = ag.s.node(n)["attrs"]
        rows.append((at.get("register"), sorted(k for k, v in at.items()
                     if isinstance(v, (int, float)) and not isinstance(v, bool))))
    print(f"A5: ApertureBudget rows (register, numeric attr count): "
          f"{[(r, len(k)) for r, k in rows]}", flush=True)
    if not rows:
        return {"rows": [], "collision_families": {}}
    _reg, keys = rows[0]
    from collections import defaultdict
    families = defaultdict(list)
    for k in keys:
        parts = [p for p in k.split("_") if p]
        for p in parts:
            families[p].append(k)
    collide = {w: ks for w, ks in families.items() if len(set(ks)) >= 2}
    print(f"A5: '_'-split word families with >=2 distinct attr keys "
          f"(ambiguous under the existing >=2-word guard IF the concern "
          f"also names a second, non-discriminating word shared by all of "
          f"them): {collide}", flush=True)
    return {"register_keys": keys, "collision_families": {w: ks for w, ks in collide.items()}}


# ---------------------------------------------------------------------------
# A3 — the seed-skip pick (a Term embedded live in
# `_compose_experiment_rule`, over SeedSummary.keywords_text). Measure the
# real population size and whether ANY structural signature is even
# plausible for a SEED (a manifest of many rules), as opposed to ONE rule.
# ---------------------------------------------------------------------------

def investigate_a3(ag):
    n_seeds = 0
    n_skippable = 0
    sample = []
    for n in ag.s.nodes("SeedSummary"):
        at = ag.s.node(n)["attrs"]
        n_seeds += 1
        if at.get("skippable") == 1.0:
            n_skippable += 1
        if len(sample) < 3:
            sample.append({"seed_id": at.get("seed_id"),
                            "keywords_text_len": len(at.get("keywords_text") or "")})
    print(f"A3: SeedSummary population: {n_seeds} total, {n_skippable} skippable "
          f"(non-frozen, real Argmax candidates)", flush=True)
    print(f"A3: sample keywords_text lengths: {sample}", flush=True)
    return {"n_seeds": n_seeds, "n_skippable": n_skippable, "sample": sample}


def main():
    print("Booting full agent (load_all_seeds) ...", flush=True)
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    rep = load_all_seeds(ag)
    print(f"  loaded {rep['loaded']}/{rep['total']}", flush=True)

    out = {}
    print("\n=== A6 investigation ===", flush=True)
    out["a6"] = investigate_a6(ag)
    print("\n=== A4 investigation ===", flush=True)
    out["a4"] = investigate_a4(ag)
    print("\n=== A5 investigation ===", flush=True)
    out["a5"] = investigate_a5(ag)
    print("\n=== A3 investigation ===", flush=True)
    out["a3"] = investigate_a3(ag)

    out_path = os.path.join(ROOT, "scripts", "part2_site_investigation_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nWritten to {out_path}")


if __name__ == "__main__":
    main()
