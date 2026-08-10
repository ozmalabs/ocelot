"""WIRE THE STRONG EAR IN — the graph-native SELECTIVE-ACTION faculty (the jabberwock's design, built).

The ear is PERCEPTION: it emits per utterance a Recognition {word, margin}. The DECISION (ACT on high-confidence, DEFER on
low) is GRAPH RULES, and the gate threshold theta is GRAPH DATA tuned ONLINE by the agent's own delta-rule trainer to a
TARGET COVERAGE (teacher-free: coverage = ACT-fraction read off the graph, never gold). The host does only mechanical ingest
(write Recognition + gated_by edge) and read-back (the ACT set), with ZERO if/else over margin.

Faculty (graph data):
  Gate { threshold, target_coverage, observed_coverage, frame, uframe }     # singleton parameter node
  Recognition { margin, act, deferred }  -gated_by->  Gate
  RULE act:    match [[rec,gated_by,gate]]  where Gt(rec.margin, gate.threshold)  -> set rec.act=1, rec.deferred=0
  RULE defer:  match [[rec,gated_by,gate]]  where Gt(gate.threshold, rec.margin)  -> set rec.deferred=1, rec.act=0
  RULE tune:   match [[root,has_gate,gate]] where Gt(gate.frame, gate.uframe)
               -> theta += eta*(observed_coverage - target_coverage) ; uframe=frame   (delta/LMS, the trainer it owns)

BAR (successful wiring, jabberwock): the Rules-only pass reproduces the rig — ACT-set accuracy >= 95% at ~50% coverage, the
misrecognitions concentrated in DEFER — produced entirely by graph data (theta self-tuned to ~median margin, no Python decision).

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.wire_selective_action
"""
from __future__ import annotations

import os
import pickle
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

from scripts.phase0_learned_latent import fit_pca, pca_apply
from scripts.earn_strong_ear_rescore import _l2, build_ear
from scripts.strong_ear_routing_confidence import conf_tokens
from substrate.world_adapter import WorldAdapter

CACHE = "/tmp/p0lat_cache_L6.pkl"
TOKCACHE = "/tmp/strong_ear_conf_tokens.pkl"
TARGET_COVERAGE = 0.5
ETA = 0.3
ITERS = 60


# ---- DSL term helpers (the trainer/backprop idiom) ----
def _V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": _V(n), "key": k}
def _L(v): return {"type": "Lit", "value": v}
def _Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def _Plus(*xs): return {"type": "Plus", "items": list(xs)}
def _Times(*xs): return {"type": "Times", "items": list(xs)}
def _Minus(a, b): return {"type": "Minus", "a": a, "b": b}


ACT_RULE = {
    "id": "sa_act", "name": "sa_act",
    "match": [["rec", "gated_by", "gate"]],
    "where": _Gt(A("rec", "margin"), A("gate", "threshold")),
    "effects": [["set_attr", "rec", "act", 1.0], ["set_attr", "rec", "deferred", 0.0]]}

DEFER_RULE = {
    "id": "sa_defer", "name": "sa_defer",
    "match": [["rec", "gated_by", "gate"]],
    "where": _Gt(A("gate", "threshold"), A("rec", "margin")),
    "effects": [["set_attr", "rec", "deferred", 1.0], ["set_attr", "rec", "act", 0.0]]}

TUNE_RULE = {
    "id": "sa_tune", "name": "sa_tune",
    "match": [["root", "has_gate", "gate"]],
    "where": _Gt(A("gate", "frame"), A("gate", "uframe")),
    "effects": [
        ["set_attr", "gate", "threshold", {"__term__": _Plus(
            A("gate", "threshold"),
            _Times(_L(ETA), _Minus(A("gate", "observed_coverage"), A("gate", "target_coverage"))))}],
        ["set_attr", "gate", "uframe", {"__term__": A("gate", "frame")}]]}


def ear_tokens():
    if os.path.exists(TOKCACHE):
        with open(TOKCACHE, "rb") as fh:
            return pickle.load(fh)
    with open(CACHE, "rb") as fh:
        data = pickle.load(fh)
    train, test = data["train"], data["test"]
    mu_p, V_p = fit_pca([t[4] for t in train])
    def strong_words(rows):
        return [(t[0], t[1], t[2], pca_apply(t[4], mu_p, V_p)) for t in rows]
    print("  [ear] building strong ear + computing margins on test (perception)...", flush=True)
    s_bank, s_vocab, s_vset, s_PW = build_ear(strong_words(train))
    toks = conf_tokens(strong_words(test), s_bank, s_vocab, s_vset, s_PW)  # (correct, margin, agree)
    out = [(int(c), float(m)) for (c, m, _a) in toks]
    with open(TOKCACHE, "wb") as fh:
        pickle.dump(out, fh)
    return out


def main():
    print("=" * 100)
    print("WIRE THE STRONG EAR IN — graph-native selective-action faculty (decision = Rules, threshold = trained graph data)")
    print("=" * 100)
    toks = ear_tokens()
    margins = np.array([m for (_c, m) in toks])
    print(f"  {len(toks)} Recognitions; margin range [{margins.min():.3f}, {margins.max():.3f}], median {np.median(margins):.3f}")

    agent = WorldAdapter(seeds=())                                  # minimal boot — only our faculty Rules run (fast)
    gate = agent.s.add_node("Gate", {"threshold": 0.05, "target_coverage": TARGET_COVERAGE,
                                     "observed_coverage": TARGET_COVERAGE, "frame": 0.0, "uframe": 0.0})
    root = agent.s.add_node("Root", {"is_root": 1.0})
    agent.inner.add_edge_unchecked(root, "has_gate", gate)
    rec_ids = []
    for (correct, margin) in toks:
        rid = agent.s.add_node("Recognition", {"margin": float(margin), "act": 0.0, "deferred": 0.0,
                                               "scoring_correct": float(correct)})   # scoring_correct: read-back ONLY
        agent.inner.add_edge_unchecked(rid, "gated_by", gate)
        rec_ids.append((rid, correct))
    for r in (ACT_RULE, DEFER_RULE, TUNE_RULE):
        agent.inner.add_rule(r)

    # The loop: host does ONLY mechanical count + clock; ALL decisions (act/defer + theta update) are Rules.
    # (spy: no if/else over `margin` anywhere below — the host never reads margin.)
    def act_fraction():
        return float(np.mean([agent.s.node(rid)["attrs"].get("act", 0.0) for (rid, _c) in rec_ids]))

    print("\n  self-tuning the gate to target coverage via the delta-rule trainer (graph Rules only):")
    for it in range(ITERS):
        f = act_fraction()                                         # mechanical aggregate (a count, not a decision)
        agent.s.set_attr(gate, "observed_coverage", f)
        agent.s.set_attr(gate, "frame", float(it + 1))             # host clock for the once-per-iter tune guard
        agent.master_tick(); agent.tick()                          # act/defer decide + tune fires once
        if it % 12 == 0 or it == ITERS - 1:
            th = agent.s.node(gate)["attrs"]["threshold"]
            print(f"    iter {it:2d}  theta {th:.4f}  coverage {f*100:.1f}%", flush=True)

    # read back the ACT set (mechanical query) and score with the held-out gold (scoring only)
    acts = [(rid, c) for (rid, c) in rec_ids if agent.s.node(rid)["attrs"].get("act", 0.0) >= 0.5]
    defers = [(rid, c) for (rid, c) in rec_ids if agent.s.node(rid)["attrs"].get("act", 0.0) < 0.5]
    base = 100 * np.mean([c for (_r, c) in rec_ids])
    cov = 100 * len(acts) / len(rec_ids)
    act_acc = 100 * np.mean([c for (_r, c) in acts]) if acts else float("nan")
    def_acc = 100 * np.mean([c for (_r, c) in defers]) if defers else float("nan")
    theta = agent.s.node(gate)["attrs"]["threshold"]

    print("\n" + "=" * 100)
    print(f"  graph-native faculty (theta self-tuned to {theta:.4f} ~ median margin {np.median(margins):.4f}):")
    print(f"    base accuracy (act-on-all):     {base:.1f}%")
    print(f"    ACT set:    {cov:.1f}% coverage,  accuracy {act_acc:.1f}%")
    print(f"    DEFER set:  {100-cov:.1f}% coverage,  accuracy {def_acc:.1f}%   (the errors land here)")
    print("-" * 100)
    if act_acc >= 95.0 and 40 <= cov <= 60:
        print(f"  WIRED — the GRAPH decided: act/defer came from the Rules (where Gt(margin, theta)), theta was self-tuned to")
        print(f"  ~{cov:.0f}% coverage by the delta-rule trainer Rule (target {TARGET_COVERAGE*100:.0f}%, teacher-free off the ACT-fraction),")
        print(f"  and the ACT set is {act_acc:.0f}% accurate vs {base:.0f}% act-on-all — errors concentrated in DEFER ({def_acc:.0f}%).")
        print("  Zero Python decision: the host only ingested margins + counted coverage. The strong ear is wired as a faculty.")
    else:
        print(f"  PARTIAL — coverage {cov:.0f}% / ACT acc {act_acc:.1f}% (bar: >=95% @ 40-60% cov). The faculty runs graph-native but")
        print("  the numbers miss the bar; check theta convergence / margin scale.")
    print("=" * 100)


if __name__ == "__main__":
    main()
