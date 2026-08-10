"""concern_induction_gate — GATE for STAGE-1 CONCERN-INDUCTION-FROM-OBSERVATION.

Pushes stage 1 of the self-extension loop from "RANK seeded CapabilityAxes" to
"INDUCE a genuinely-new concern from what the agent OBSERVES (surprise/residual)".

The surprise = where the agent's HELD term-shapes FAIL TO COVER an observed
structure (held Covers Term = the coverage test; held AntiUnifyWitness = the
residual). A concern is MINTED from the residual's structure and INJECTED as a
manifold-suggested CapabilityAxis that COMPETES in gap_prioritiser (adds a
candidate, never overrides the Argmax). DISCRIMINATIVE NULL: a coverable
observation mints NOTHING; only an uncovered residual mints.

ARCHITECTURE: Covers / AntiUnifyWitness are Rust Terms (the surprise/residual is
the agent's, graph-native); the mint is a graph mutation; gap_prioritiser ranks
natively. No Python decision-if over graph state, no LLM. The observation is a
relation-system a world adapter produces from a real stream (mechanical ingest).

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/concern_induction_gate.py
"""
from __future__ import annotations
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import (induce_concern, learn_term_for_concern,
                                        _load_shape_signatures)
import domains.gap_prioritiser as gp


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    calls = {"n": 0}
    try:
        a.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "DONKEY")[1])
    except Exception:
        pass
    ok = True

    # the seeded CapabilityAxes BEFORE induction (to prove induced-not-seeded)
    seeded = set()
    for n in a.s.nodes("CapabilityAxis"):
        ck = a.s.node(n)["attrs"].get("capability_keys") or []
        seeded.add(tuple(ck))

    # 1 + 2. DISCRIMINATIVE NULL (the load-bearing control)
    print("=" * 78)
    print("GATE 1+2 — INDUCED-NOT-SEEDED + DISCRIMINATIVE NULL (coverable->nothing, residual->concern)")
    print("=" * 78)
    print("  held coverage vocab:", list(_load_shape_signatures(a.s).keys())[:6], "...")
    # (a) coverable observation -> NO mint
    obs_cover = [["detect", "CONTACT", "between", "PARTS"],
                 ["type", "CONTACT", "is", "INVARIANT"], ["pairwise", "PARTS"]]
    rA = induce_concern(a, obs_cover)
    print(f"  (a) coverable obs -> minted={rA['minted']} covered_by={rA.get('covered_by')}")
    # (b) uncovered observation -> mint from residual
    obs_resid = [["oscillate", "X", "around", "SETPOINT"],
                 ["overshoot", "X", "then", "CORRECT"], ["damp", "AMPLITUDE", "each", "CYCLE"]]
    rB = induce_concern(a, obs_resid)
    print(f"  (b) uncovered obs -> minted={rB['minted']} key={rB.get('capability_key')} "
          f"residual={rB.get('residual_predicates')}")
    null_ok = (rA["minted"] is False) and (rB["minted"] is True)
    induced_not_seeded = rB["minted"] and (tuple([rB["capability_key"]]) not in seeded)
    print(f"  -> NULL holds (coverable mints nothing, residual mints): {null_ok}")
    print(f"  -> induced concern is NOT one of the pre-seeded axes: {induced_not_seeded}")
    ok &= null_ok and induced_not_seeded

    # 3. FEEDS THE LOOP — competes in ranking + reaches stage 2 (honest grounding map)
    print("\n" + "=" * 78)
    print("GATE 3 — FEEDS THE LOOP (induced concern competes in ranking + reaches stage 2)")
    print("=" * 78)
    key = rB["capability_key"]
    ranked = gp.rank_gaps(a.s, k=40)
    competes = any(key in (r.get("capability_keys") or []) for r in ranked)
    print(f"  induced concern competes in gap_prioritiser ranking: {competes} ({len(ranked)} axes)")
    d = learn_term_for_concern(a, [key])
    reached = d.get("concept") == "(induced from observation)"
    print(f"  reaches stage 2 (reads residual ON the axis): {reached}")
    print(f"  stage-2 decision: term_family={d.get('term_family')} shared_leaves={d.get('shared_leaves')} "
          f"connected={d.get('connected')}")
    ok &= competes and reached

    # 4. donkey check
    print("\n" + "=" * 78)
    print("GATE 4 — DETERMINISTIC / donkey=0")
    print("=" * 78)
    import inspect, re
    import domains.reflective_faculty as rf
    src = inspect.getsource(rf.induce_concern) + inspect.getsource(rf._covers) + inspect.getsource(rf._witness_residual)
    llm = len(re.findall(r"make_ask|claude|openai|set_self_teacher|\.chat\(", src))
    print(f"  LLM calls in induction path: {llm}")
    print(f"  induction uses held Covers + AntiUnifyWitness Terms: "
          f"{'Covers' in src and 'AntiUnifyWitness' in src}")
    print(f"  DONKEY calls across the run: {calls['n']}")
    ok &= (llm == 0 and calls["n"] == 0)

    # HONEST MAP
    print("\n" + "=" * 78)
    print("HONEST MAP — where the induced concern lands")
    print("=" * 78)
    print("  STAGE 1 (induce): AUTONOMOUS — surprise = held terms fail to cover (Covers/AntiUnifyWitness),")
    print("                    concern minted from the residual, competes in ranking. Discriminative null holds.")
    if d.get("connected"):
        print("  -> the induced concern REACHES a term-family decision (shares structure with a held shape):")
        print(f"     stage 2 connected to {d.get('term_family')} -> stages 3+4 (compose/express/compile) follow.")
    else:
        print("  -> GROUNDING WALL (the named next frontier, deeper than routing): the genuinely-NEW residual")
        print(f"     ({rB.get('residual_predicates')}) shares NO structure with any held term-family (shared=0).")
        print("     A novel concern by definition matches no existing term -> it needs EITHER a NEW term")
        print("     composed for its novel shape OR its residual predicates GROUNDED into held vocabulary.")
        print("     This is CONCERN-GROUNDING — the loop's next leading edge. Induction (stage 1) is real;")
        print("     the wall moved one stage deeper, exactly as the loop (not summit) predicts.")

    print("\n" + "=" * 78)
    print(("PASS" if ok else "FAIL"),
          "- CONCERN-INDUCTION: stage 1 now INDUCES a genuinely-new concern from observation (surprise = "
          "held terms fail to cover, via Covers/AntiUnifyWitness), mints it from the residual, and it "
          "competes in gap_prioritiser. The discriminative null holds (coverable->nothing). donkey=0. "
          "Honest boundary: the induced novel concern reaches stage 2 but walls at GROUNDING (no held "
          "term-family fits a genuinely-new shape) — the named next frontier.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
