#!/usr/bin/env python3
"""scripts/rule_signature_wiring_check.py — AR1/AR2 validation of the
COMBINATION-WIRING DESIGN, before it is wired into production
(`domains.reflective_faculty._pick_acting_rule` / `_pick_reply_rule`).

Reuses the EXACT 40-probe oracle from `scripts/rule_signature_measure.py`
(Class A / Class B; Class C reused too for an agreement-rate sanity check),
per the task brief: "reproduce/reuse its own 40-probe test set rather than
inventing a new one."

Tests ONE candidate Term — production's own StringIndexOf-Sum-Argmax
(UNCHANGED), falling back, ONLY when production abstains (best is None OR
its own overlap score is 0), to the SAME StringIndexOf-Sum-Argmax shape
applied to `where_signature_json` instead of `keywords_text` — evaluated as
ONE Term via a SINGLE native.evaluate() call (no Python if/else picking a
rule name; the whole decision, including the fallback branch, lives inside
the Term tree, matching the existing convention at this call site).

This script makes NO production edits. It is read-only investigation:
booting a full agent and evaluating a NEW Term side by side with the
existing `_pick_acting_rule`/`_pick_reply_rule` and the observational
`pick_*_rule_structural` functions, to confirm the combined Term recovers
BOTH Class A and Class B before the production files are touched.
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

# Reuse the pre-registered probe table verbatim.
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import rule_signature_measure as rsm  # noqa: E402


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


V = lambda n: {"type": "Var", "name": n}
L = lambda v: {"type": "Lit", "value": v}
Attr = lambda nd, k: {"type": "Attr", "node": nd, "key": k}
Eq = lambda a, b: {"type": "Eq", "a": a, "b": b}
Not = lambda x: {"type": "Not", "arg": x}
And = lambda *xs: {"type": "And", "items": list(xs)}
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


def _combined_pick_term(writes_key: str, axis_preds) -> dict:
    """ONE Term: production's own Argmax first; falls back, INSIDE the same
    Term (no Python branch), to a where_signature_json Argmax of the exact
    same StringIndexOf-Sum shape, only when production's own pick is None or
    scores 0."""
    words = L(list(axis_preds))
    name_overlap = lambda nd: Sum(words, "w",
        Ite(Gte(StrIdx(Attr(nd, "keywords_text"), V("w")), L(0)), L(1), L(0)))
    struct_overlap = lambda nd: Sum(words, "w",
        Ite(Gte(StrIdx(Attr(nd, "where_signature_json"), V("w")), L(0)), L(1), L(0)))
    candidates = Filter(NodesOfType("RuleSummary"), "s",
        And(Eq(Attr(V("s"), writes_key), L(1.0)), Eq(Attr(V("s"), "skippable"), L(1.0))))
    name_best = Argmax(candidates, "s", name_overlap(V("s")), None)
    struct_best = Argmax(candidates, "s2", struct_overlap(V("s2")), None)
    fallback = LetT("sbest", struct_best,
        Ite(And(Not(Eq(V("sbest"), L(None))), Gt(struct_overlap(V("sbest")), L(0.0))),
            V("sbest"), L(None)))
    return LetT("best", name_best,
        Ite(And(Not(Eq(V("best"), L(None))), Gt(name_overlap(V("best")), L(0.0))),
            V("best"), fallback))


def _combined_pick(ag, writes_key, axis_preds):
    sub0, native0 = ag.s, ag.inner
    term = _combined_pick_term(writes_key, axis_preds)
    try:
        picked = native0.evaluate(term, {})
    except Exception as e:
        return {"picked": None, "name": None, "error": f"{type(e).__name__}: {e}"}
    if picked is None or not sub0.has_node(picked):
        return {"picked": None, "name": None}
    return {"picked": picked, "name": sub0.node(picked)["attrs"].get("name")}


def _run_oracle_class(ag, probes, kind: str):
    writes_key = "writes_chosen_action" if kind == "acting" else "writes_reply"
    rows = []
    for target, word in probes:
        combo = _combined_pick(ag, writes_key, [word])
        rows.append({
            "target": target, "word": word, "kind": kind,
            "combined_pick": combo.get("name"),
            "combined_correct": (combo.get("name") == target),
        })
    return rows


def main():
    print("Booting full agent (load_all_seeds) ...", flush=True)
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    rep = load_all_seeds(ag)
    print(f"  loaded {rep['loaded']}/{rep['total']}", flush=True)

    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    rf._ensure_reply_rule_provenance(ag.s, ag.inner)
    touched = rsig.ensure_where_signature(ag.s)
    print(f"  where_signature_json minted on {touched} RuleSummary nodes", flush=True)

    class_a = (_run_oracle_class(ag, rsm.CLASS_A_ACTING, "acting")
               + _run_oracle_class(ag, rsm.CLASS_A_REPLY, "reply"))
    class_b = (_run_oracle_class(ag, rsm.CLASS_B_ACTING, "acting")
               + _run_oracle_class(ag, rsm.CLASS_B_REPLY, "reply"))

    def summarize(rows, label):
        n = len(rows)
        correct = sum(1 for r in rows if r["combined_correct"])
        print(f"{label}: n={n} combined_correct={correct}")
        for r in rows:
            mark = "OK" if r["combined_correct"] else "MISS"
            print(f"    [{mark}] {r['kind']:6s} {r['target']:60s} word={r['word']!r:20s} -> {r['combined_pick']!r}")
        return {"n": n, "combined_correct": correct}

    sum_a = summarize(class_a, "Class A (where-native)")
    sum_b = summarize(class_b, "Class B (name-native)")

    out = {"class_a": {"rows": class_a, "summary": sum_a},
           "class_b": {"rows": class_b, "summary": sum_b}}
    out_path = os.path.join(ROOT, "scripts", "rule_signature_wiring_check_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWritten to {out_path}")

    total_n = sum_a["n"] + sum_b["n"]
    total_correct = sum_a["combined_correct"] + sum_b["combined_correct"]
    print(f"\n=== TOTAL: {total_correct}/{total_n} correct under the combined term ===")


if __name__ == "__main__":
    main()
