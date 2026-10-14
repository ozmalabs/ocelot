"""Criterion proposals (plan P6, 2026-10-10): the agent proposes changes to
its own reply-quality criterion; a human adopts.

MECHANICAL half of seeds/criterion_proposals.json. The criterion is data
(domains/reply_quality_criteria_v1.json); a proposal is a small edit to it in
a bounded grammar, held on a CriterionProposal node with its measurements:

  edit {"op": "cell", "inbound": ic, "reply": rc, "value": v}
       one score_table cell set to v (0..2)
  edit {"op": "cap", "inbound": ic, "reply": rc, "when": cond, "to": 0|1}
       a cap (reply_quality.assess, criteria >= 1.2.0): the pair scores at
       most `to` when cond holds -- off_topic | addressed_to_agent |
       person_turn | always

This module only enumerates edits (singles, then pairs of the best singles by
DEV agreement), applies them to a copy of the criterion, and measures:
  * Cohen's kappa and precision of the machine 0 against the labelled set,
    split by dialogue -- DEV (even dialogues) to choose, TEST (odd) to report;
  * loop success: the mean score the criterion gives the agent's own recent
    production replies -- what the self-improvement loop would see as
    progress. A proposal that raises it without raising TEST agreement is the
    Goodhart case the rules reject.
The rules decide recommended / not_recommended / goodhart_rejected; adoption
is a human decision only (decide()), applied by scripts/apply_criterion_proposal.py.
"""
from __future__ import annotations

import collections
import copy
import csv
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "evaluation/labels/reply_quality_heldout_v1.csv"
CONDITIONS = ("off_topic", "addressed_to_agent", "person_turn", "always")


def labelled_rows(path=LABELS) -> list:
    rows = []
    for r in csv.DictReader(open(path)):
        lab = (r.get("label") or "").strip()
        if lab in ("0", "1", "2"):
            rows.append({"id": r["id"], "dialogue": int(r.get("dialogue") or 0), "inbound": r["inbound"],
                         "reply": "" if r["reply"] == "(no reply)" else r["reply"], "label": int(lab)})
    return rows


def split(rows):
    """DEV = even dialogues, TEST = odd: no dialogue in both."""
    return [r for r in rows if r["dialogue"] % 2 == 0], [r for r in rows if r["dialogue"] % 2 == 1]


def kappa(pairs, classes=(0, 1, 2)):
    n = len(pairs)
    if not n:
        return None
    po = sum(1 for h, m in pairs if h == m) / n
    hc = collections.Counter(h for h, _ in pairs)
    mc = collections.Counter(m for _, m in pairs)
    pe = sum(hc[c] * mc[c] for c in classes) / (n * n)
    return round((po - pe) / (1 - pe), 4) if pe < 1 else None


def apply_edits(base: dict, edits) -> dict:
    c = copy.deepcopy(base)
    for e in edits:
        if e["op"] == "cell":
            c["score_table"][e["inbound"]][e["reply"]] = int(e["value"])
        elif e["op"] == "cap":
            c.setdefault("caps", []).append({
                "name": f"cap_{e['inbound']}_{e['reply']}_{e['when']}", "inbound_classes": [e["inbound"]],
                "reply_classes": [e["reply"]], "when": e["when"], "to": int(e["to"])})
        else:
            raise ValueError(e)
    return c


def measure(c: dict, rows, success_pairs) -> dict:
    from domains import reply_quality as rq
    dev, test = split(rows)

    def stats(rs):
        pairs = [(r["label"], rq.assess(r["inbound"], r["reply"], None, c)["score"]) for r in rs]
        m0 = [h for h, m in pairs if m == 0]
        return {"kappa": kappa(pairs), "precision0": round(sum(1 for h in m0 if h == 0) / len(m0), 4) if m0 else None,
                "n": len(pairs)}
    s = [rq.assess(i, r, None, c)["score"] for i, r in success_pairs]
    return {"dev": stats(dev), "test": stats(test),
            "loop_success": round(sum(s) / len(s), 4) if s else None}


def single_edits(base: dict) -> list:
    out = []
    table = base["score_table"]
    for ic in sorted(table):
        for rc in sorted(table[ic]):
            v = int(table[ic][rc])
            for nv in (v - 1, v + 1):
                if 0 <= nv <= 2:
                    out.append({"op": "cell", "inbound": ic, "reply": rc, "value": nv})
            if v > 0:
                for cond in CONDITIONS[:3]:
                    out.append({"op": "cap", "inbound": ic, "reply": rc, "when": cond, "to": 0})
    return out


def edit_id(edits) -> str:
    def one(e):
        if e["op"] == "cell":
            return f"cell:{e['inbound']}->{e['reply']}={e['value']}"
        return f"cap:{e['inbound']}->{e['reply']}|{e['when']}<={e['to']}"
    return "+".join(one(e) for e in edits)


def enumerate_and_measure(base: dict, rows, success_pairs, top_k=5) -> tuple:
    """(baseline measurement, [candidate measurements]) -- singles, then
    pairs of the top_k singles by DEV kappa gain (DEV only chooses)."""
    base_m = measure(base, rows, success_pairs)
    cands = []
    for e in single_edits(base):
        m = measure(apply_edits(base, [e]), rows, success_pairs)
        cands.append({"id": edit_id([e]), "edits": [e], "size": 1, **m})

    def gain(x, split_="dev"):
        return round((x[split_]["kappa"] or 0) - (base_m[split_]["kappa"] or 0), 4)
    best = sorted([x for x in cands if gain(x) > 0], key=lambda x: -gain(x))[:top_k]
    for a, b in itertools.combinations(best, 2):
        edits = a["edits"] + b["edits"]
        m = measure(apply_edits(base, edits), rows, success_pairs)
        cands.append({"id": edit_id(edits), "edits": edits, "size": 2, **m})
    for x in cands:
        x["dev_gain"], x["test_gain"] = gain(x, "dev"), gain(x, "test")
        x["success_delta"] = round((x["loop_success"] or 0) - (base_m["loop_success"] or 0), 4)
    return base_m, cands


def policy(agent):
    sub = agent.s
    for n in sub.nodes("CriterionPolicy"):
        return n, dict(sub.node(n)["attrs"])
    return None, {}


def mint(agent, cand: dict, base_m: dict, rank: int = 0):
    """A CriterionProposal under the policy, status 'measured'."""
    sub, native = agent.s, agent.inner
    pn, _ = policy(agent)
    attrs = {"candidate": cand["id"], "edits": json.dumps(cand["edits"]), "size": cand["size"],
             "criterion": "reply_quality_criteria", "dev_kappa": cand["dev"]["kappa"],
             "test_kappa": cand["test"]["kappa"], "test_precision0": cand["test"]["precision0"],
             "base_test_kappa": base_m["test"]["kappa"], "dev_gain": cand["dev_gain"],
             "test_gain": cand["test_gain"], "loop_success": cand["loop_success"],
             "success_delta": cand["success_delta"], "rank": int(rank), "status": "measured"}
    p = sub.add_node("CriterionProposal", attrs)
    if pn is not None:
        native.add_edge_unchecked(pn, "has_criterion_proposal", p)
    return p


def decide(agent, proposal, decision: str, by: str):
    """HUMAN-ONLY adoption (plan P6): record a human's approve/deny. The rules
    move the proposal on; applying an approved edit to the criterion file is
    scripts/apply_criterion_proposal.py, run by the human."""
    assert decision in ("approved", "denied"), decision
    agent.inner.set_attr(proposal, "human_decision", decision)
    agent.inner.set_attr(proposal, "decided_by", str(by))
