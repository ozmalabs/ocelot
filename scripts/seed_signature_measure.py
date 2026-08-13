#!/usr/bin/env python3
"""scripts/seed_signature_measure.py — the AR2 measurement, per
docs/research/engine_substrate/SEED_PICK_STRUCTURAL_FALLBACK_PREREG.md.

Boots a full agent, mints `SeedSummary.where_signature_json` via
`domains.seed_signature.ensure_seed_signature`, mechanically FILTERS the raw
discovery candidates (`seed_signature_discover_probes_results.json`'s class_a/
class_b samples, and a fresh full scan) down to GENUINE, UNAMBIGUOUS probes —
a Class A probe word must (1) be absent from EVERY skippable seed's
`keywords_text` (so the primary Argmax genuinely abstains, not merely
abstains for the target seed while some OTHER seed accidentally wins), (2) be
present in the TARGET seed's own `where_signature_json`, and (3) be absent
from every OTHER skippable seed's `where_signature_json` (so the structural
fallback picks the target UNAMBIGUOUSLY, not via an insertion-order tie) — a
Class B probe word must be present in the target seed's own `keywords_text`
with nonzero overlap already (the primary genuinely does not abstain).

Then evaluates THREE Term variants directly via `native.evaluate` (no rule
dispatch, no `_compose_experiment_rule` call) on the REAL held graph:
  (1) primary-only  -- byte-identical to production's CURRENT (unwired) Term
  (2) structural-only -- the new signal in isolation
  (3) combined (primary, fallback-on-abstain) -- the WIRED Term this rung
      installs into `_compose_experiment_rule`

This validates the design BEFORE the production edit, exactly
`rule_signature_wiring_check.py`'s own precedent for A1/A2.
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble(strict=False)

from substrate.boot_core import boot_core  # noqa: E402
from substrate.boot_all import load_all_seeds  # noqa: E402
from domains import seed_signature as ssig  # noqa: E402


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


# ---------------------------------------------------------------------------
# Term builders -- EXACT mirror of the shapes registered in the PREREG's AR1/
# AR3 and (after the production edit) installed verbatim in
# `reflective_faculty._compose_experiment_rule`'s `vary` branch.
# ---------------------------------------------------------------------------
V = lambda n: {"type": "Var", "name": n}
L = lambda v: {"type": "Lit", "value": v}
Attr = lambda nd, k: {"type": "Attr", "node": nd, "key": k}
Eq = lambda a, b: {"type": "Eq", "a": a, "b": b}
Gt = lambda a, b: {"type": "Gt", "a": a, "b": b}
Gte = lambda a, b: {"type": "Gte", "a": a, "b": b}
Ite = lambda c, t, o: {"type": "IfThenElse", "cond": c, "then": t, "other": o}
Filter = lambda src, var, pred: {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
Argmax = lambda src, var, val, default: {"type": "Argmax", "source": src, "var_name": var,
                                          "value": val, "default": default}
NodesOfType = lambda t: {"type": "NodesOfType", "node_type": t}
Sum = lambda src, var, val: {"type": "Sum", "source": src, "var_name": var, "value": val}
StrIdx = lambda h, n: {"type": "StringIndexOf", "haystack": h, "needle": n}
LetT = lambda nm, val, body: {"type": "Let", "name": nm, "value": val, "body": body}


def _primary_pick_expr(words_list):
    words = L(words_list)
    overlap = lambda node_t: Sum(words, "w",
        Ite(Gte(StrIdx(Attr(node_t, "keywords_text"), V("w")), L(0)), L(1), L(0)))
    candidates = Filter(NodesOfType("SeedSummary"), "s", Eq(Attr(V("s"), "skippable"), L(1.0)))
    best = Argmax(candidates, "s", overlap(V("s")), None)
    return LetT("best", best,
        Ite(Eq(V("best"), L(None)), L(""),
            Ite(Gt(overlap(V("best")), L(0.0)), Attr(V("best"), "seed_id"), L(""))))


def _structural_pick_expr(words_list):
    words = L(words_list)
    struct_overlap = lambda node_t: Sum(words, "w",
        Ite(Gte(StrIdx(Attr(node_t, "where_signature_json"), V("w")), L(0)), L(1), L(0)))
    candidates = Filter(NodesOfType("SeedSummary"), "s", Eq(Attr(V("s"), "skippable"), L(1.0)))
    struct_best = Argmax(candidates, "s2", struct_overlap(V("s2")), None)
    return LetT("sbest", struct_best,
        Ite(Eq(V("sbest"), L(None)), L(""),
            Ite(Gt(struct_overlap(V("sbest")), L(0.0)), Attr(V("sbest"), "seed_id"), L(""))))


def _combined_pick_expr(words_list):
    """THE WIRED SHAPE -- exactly what this rung installs into
    `_compose_experiment_rule`'s `skip_id_expr`."""
    words = L(words_list)
    overlap = lambda node_t: Sum(words, "w",
        Ite(Gte(StrIdx(Attr(node_t, "keywords_text"), V("w")), L(0)), L(1), L(0)))
    struct_overlap = lambda node_t: Sum(words, "w",
        Ite(Gte(StrIdx(Attr(node_t, "where_signature_json"), V("w")), L(0)), L(1), L(0)))
    candidates = Filter(NodesOfType("SeedSummary"), "s", Eq(Attr(V("s"), "skippable"), L(1.0)))
    best = Argmax(candidates, "s", overlap(V("s")), None)
    struct_best = Argmax(candidates, "s2", struct_overlap(V("s2")), None)
    struct_skip_id_expr = LetT("sbest", struct_best,
        Ite(Eq(V("sbest"), L(None)), L(""),
            Ite(Gt(struct_overlap(V("sbest")), L(0.0)), Attr(V("sbest"), "seed_id"), L(""))))
    return LetT("best", best,
        Ite(Eq(V("best"), L(None)), struct_skip_id_expr,
            Ite(Gt(overlap(V("best")), L(0.0)), Attr(V("best"), "seed_id"), struct_skip_id_expr)))


# Structural row-field / Term-scaffolding words that appear in EVERY seed's
# signature blob regardless of content (row-shape vocabulary, not literal
# content) -- excluded from probe candidacy so a probe genuinely names
# something specific to ONE seed's rules, not JSON syntax.
_GENERIC_STOPWORDS = {
    "items", "value", "source", "false", "true", "status", "pending",
    "edge_type", "any_type", "type", "node", "attr", "path", "field",
    "var_name", "predicate", "default", "cond", "then", "other", "arg",
}


def _find_unambiguous_probes(ag, n_class_a=6, n_class_b=4):
    seeds = {}
    for n in ag.s.nodes("SeedSummary"):
        at = ag.s.node(n)["attrs"]
        if at.get("skippable") != 1.0:
            continue
        sid = at.get("seed_id")
        seeds[sid] = {
            "kw": (at.get("keywords_text") or "").lower(),
            "sig": at.get("where_signature_json") or "",
        }

    import re
    word_re = re.compile(r"[a-z][a-z_]{5,}")

    class_a, class_b = [], []
    for sid, d in seeds.items():
        if len(class_a) >= n_class_a and len(class_b) >= n_class_b:
            break
        sig_words = set(word_re.findall(d["sig"].lower())) - _GENERIC_STOPWORDS
        for w in sig_words:
            if len(class_a) >= n_class_a:
                break
            if w in d["kw"]:
                continue
            # must be absent from EVERY other seed's keywords_text (primary
            # genuinely abstains system-wide) and present ONLY in this
            # seed's structural signature (unambiguous structural winner)
            if any(w in other["kw"] for osid, other in seeds.items()):
                continue
            others_with_sig_hit = [osid for osid, other in seeds.items()
                                    if osid != sid and w in other["sig"]]
            if others_with_sig_hit:
                continue
            class_a.append({"seed_id": sid, "word": w})
        # Class B: a word already in this seed's OWN keywords_text
        kw_words = set(word_re.findall(d["kw"])) - _GENERIC_STOPWORDS
        for w in kw_words:
            if len(class_b) >= n_class_b:
                break
            if w in d["kw"]:
                class_b.append({"seed_id": sid, "word": w})
                break  # one per seed is enough signal

    return class_a[:n_class_a], class_b[:n_class_b]


def main():
    t0 = time.time()
    print("Booting full agent (load_all_seeds) ...", flush=True)
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    rep = load_all_seeds(ag)
    print(f"  loaded {rep['loaded']}/{rep['total']} in {time.time()-t0:.1f}s", flush=True)

    t1 = time.time()
    n_touched = ssig.ensure_seed_signature(s)
    print(f"ensure_seed_signature: minted {n_touched} new attrs in {time.time()-t1:.1f}s", flush=True)

    print("\nSearching for unambiguous Class A / Class B probes ...", flush=True)
    class_a, class_b = _find_unambiguous_probes(ag)
    print(f"Found {len(class_a)} Class A, {len(class_b)} Class B unambiguous probes", flush=True)

    results = {"class_a": [], "class_b": []}
    for probe in class_a:
        words = [probe["word"]]
        primary = ag.inner.evaluate(_primary_pick_expr(words), {})
        structural = ag.inner.evaluate(_structural_pick_expr(words), {})
        combined = ag.inner.evaluate(_combined_pick_expr(words), {})
        row = {
            "seed_id": probe["seed_id"], "word": probe["word"],
            "primary_pick": primary, "structural_pick": structural,
            "combined_pick": combined,
            "primary_abstained": primary in ("", None),
            "structural_correct": structural == probe["seed_id"],
            "combined_correct": combined == probe["seed_id"],
        }
        results["class_a"].append(row)
        print(f"  Class A [{probe['seed_id']!r} <- {probe['word']!r}]: "
              f"primary={primary!r} structural={structural!r} combined={combined!r}", flush=True)

    for probe in class_b:
        words = [probe["word"]]
        primary = ag.inner.evaluate(_primary_pick_expr(words), {})
        combined = ag.inner.evaluate(_combined_pick_expr(words), {})
        row = {
            "seed_id": probe["seed_id"], "word": probe["word"],
            "primary_pick": primary, "combined_pick": combined,
            "primary_nonabstain": primary not in ("", None),
            "combined_matches_primary": combined == primary,
        }
        results["class_b"].append(row)
        print(f"  Class B [{probe['seed_id']!r} <- {probe['word']!r}]: "
              f"primary={primary!r} combined={combined!r}", flush=True)

    n_a_pass = sum(1 for r in results["class_a"] if r["primary_abstained"] and r["structural_correct"] and r["combined_correct"])
    n_b_pass = sum(1 for r in results["class_b"] if r["primary_nonabstain"] and r["combined_matches_primary"])
    print(f"\nClass A: {n_a_pass}/{len(class_a)} pass (primary abstains, structural+combined correct)", flush=True)
    print(f"Class B: {n_b_pass}/{len(class_b)} pass (primary non-abstain, combined unchanged)", flush=True)

    out_path = os.path.join(ROOT, "scripts", "seed_signature_measure_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nWritten to {out_path}")
    print(f"Total wall time: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
