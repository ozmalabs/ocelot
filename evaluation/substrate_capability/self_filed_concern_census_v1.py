#!/usr/bin/env python3
"""Tranche 5: census of the agent's OWN filed concerns on a natural corpus.

No deployed daemon history exists on this host (~/.jabberwock absent), so the
census uses concerns the agent files ITSELF (gap_awareness et al.) while
conversing through persona_chat_20 (User 1's turns). For each SelfConcern:
kind, content, the pipeline promotion would choose, and the variation
families its promoted relations make applicable (each pick refuted in turn),
at the current 12-word cue window AND the old 4-word window.
"""
import json, sys, time, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
OUT = ROOT / "evaluation/reports/self_filed_concern_census_v1_20261007.json"


def families(a, jd, rf, kind, content, window):
    from domains.variation_credit_lab import VariationLab
    stop = {"your", "the", "a", "an", "of", "to", "my", "me", "it", "this", "that", "for", "and", "on", "in",
            "with", "you", "yourself", "at"}
    words = [w.lower().strip(".,;:!?'\"") for w in str(content).split()]
    words = [w for w in words if len(w) > 2 and w not in stop]
    old = jd._PROMOTE_CUE_WORDS; jd._PROMOTE_CUE_WORDS = window
    try:
        rels, pipe = jd._promote_relations_for_concern(kind, words, (words[0].upper() if words else "SELF")[:24])
    finally:
        jd._PROMOTE_CUE_WORDS = old
    if pipe != "experiment":
        return pipe, []
    preds = [r[0] for r in rels]
    heads = sorted({r[0] for r in rf._residual_relations(a, preds)} | set(preds))
    lab = VariationLab(True); k = lab.concern(kind); seq = []
    for _ in range(8):
        op = lab.pick(k, heads)
        if op is None: break
        seq.append(op); lab.trial(k, op, "refuted")
    return pipe, seq


def main():
    if OUT.exists(): raise SystemExit("refusing to overwrite")
    import jabberwock_daemon as jd
    import domains.reflective_faculty as rf
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    t0 = time.time()
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    dialogues = json.load(open(ROOT / "data/corpus/persona_chat_20.json"))
    turns = 0
    for dlg in dialogues:
        for spk, text in dlg["turns"]:
            if spk != "User 1": continue
            try:
                a.converse(text, speech_act="question" if text.strip().endswith("?") else "statement")
            except Exception:  # noqa: BLE001
                pass
            turns += 1
    rows = []
    for sc in a.s.nodes("SelfConcern"):
        at = a.s.node(sc)["attrs"]
        kind = str(at.get("kind") or "self_improvement"); content = at.get("content") or at.get("predicate") or ""
        p12, f12 = families(a, jd, rf, kind, content, 12)
        p4, f4 = families(a, jd, rf, kind, content, 4)
        rows.append({"kind": kind, "content": str(content)[:120], "pipeline": p12, "families_12": f12, "families_4": f4})
    by_kind = collections.Counter(r["kind"] for r in rows)
    exp_rows = [r for r in rows if r["pipeline"] == "experiment"]
    summ = {"turns": turns, "concerns": len(rows), "by_kind": dict(by_kind), "experiment_pipeline": len(exp_rows),
            "multi_family_12": sum(len(r["families_12"]) >= 2 for r in exp_rows),
            "multi_family_4": sum(len(r["families_4"]) >= 2 for r in exp_rows),
            "family_counts_12": dict(collections.Counter(f for r in exp_rows for f in r["families_12"])),
            "elapsed_s": time.time() - t0}
    OUT.write_text(json.dumps({"schema": "SelfFiledConcernCensusV1", "summary": summ, "rows": rows}, indent=1, sort_keys=True) + "\n")
    print(json.dumps(summ, indent=1))

main()
