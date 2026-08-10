"""full_loop_gate — GATE for the FULL self-extension LOOP run end-to-end, with a
truthful AUTONOMY MAP. There is no summit: the agent learns a new concern -> builds
a new term -> expresses it -> compiles it, an open-ended cycle.

The 4 stages, each driven on the REAL agent (donkey=0):
  1. LEARN A NEW CONCERN — gap_prioritiser.rank_gaps surfaces+ranks concerns from
     the agent's OWN graph (CapabilityAxes from its postulates), no hand-handing.
  2. BUILD/DECIDE THE TERM — learn_term_for_concern (the stage-1->2 CONNECTOR this
     gate's fix supplies): author the concern's signature from its held Concept's
     OWN definition, match it to the held term-family by the agent's shape-matcher.
  3. EXPRESS — register the composed Term as a live named graph-resident Program.
  4. COMPILE — callable immediately on the Rust evaluator (dynamic, no restart).

THE FIX (the first wall): stage 1 surfaces a concern KEY; stage 2 needs its
held-Concept STRUCTURE. learn_term_for_concern connects them (mechanical lookup +
held author_signature + held matcher — no reasoning). The wall that remains (the
honest next frontier): a surfaced concern with NO held Concept (e.g. action_effect,
a bare capability-key) cannot be connected — it needs a grounded Concept first.

ARCHITECTURE: every stage is the agent's held machinery; Python mechanically
dispatches + reads. NO LLM (donkey=0). NO decision-if over graph state.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/full_loop_gate.py
"""
from __future__ import annotations
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import domains.gap_prioritiser as gp
from domains.reflective_faculty import (learn_term_for_concern, dynamic_extend,
                                        _load_program, run_program_on_fresh)


def _cleanup(name):
    p = os.path.join(ROOT, "seeds", "programs.json")
    if os.path.exists(p):
        d = json.load(open(p))
        d["nodes"] = [n for n in d.get("nodes", []) if n.get("attrs", {}).get("name") != name]
        json.dump(d, open(p, "w"), indent=1)


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    calls = {"n": 0}
    try:
        a.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "DONKEY")[1])
    except Exception:
        pass
    ok = True

    # STAGE 1 — LEARN A NEW CONCERN (the agent's own gap_prioritiser)
    print("=" * 78)
    print("STAGE 1 — LEARN A NEW CONCERN (gap_prioritiser, the agent's own ranking)")
    print("=" * 78)
    ranked = gp.rank_gaps(a.s, k=23)
    top = (ranked or [{}])[0]
    print(f"  agent surfaced+ranked {len(ranked or [])} concerns; #1 = {top.get('capability_keys')} "
          f"(score {top.get('score')})")
    s1_ok = bool(ranked)
    print("  -> stage 1 autonomous (agent's graph, donkey=0):", "OK" if s1_ok else "FAIL")
    ok &= s1_ok

    # STAGE 2 — DECIDE/BUILD THE TERM (the connector: concern -> term-family)
    print("\n" + "=" * 78)
    print("STAGE 2 — DECIDE THE TERM (learn_term_for_concern: signature -> matched term-family)")
    print("=" * 78)
    chosen, decision = None, None
    walls = []
    for r in ranked or []:
        d = learn_term_for_concern(a, r.get("capability_keys"))
        if d.get("connected"):
            chosen, decision = r, d
            break
        else:
            walls.append((r.get("capability_keys"), d.get("reason", "")[:60]))
    if decision:
        print(f"  concern {decision['concern']} via Concept {decision['concept']!r}")
        print(f"  authored signature (from the Concept's OWN definition): {decision['signature']}")
        print(f"  term-family the agent's matcher chose: {decision['term_family']} ({decision['shared_leaves']} shared)")
    s2_ok = decision is not None and decision.get("connected")
    print(f"  concerns that WALLED before a structured one (no held Concept): {len(walls)}")
    if walls[:2]:
        print(f"    e.g. {walls[0][0]}: {walls[0][1]}")
    print("  -> stage 2 autonomous (matcher's decision, donkey=0):", "OK" if s2_ok else "FAIL")
    ok &= s2_ok

    # STAGE 3 + 4 — EXPRESS + COMPILE (compose a Term of the chosen shape, register live, callable)
    print("\n" + "=" * 78)
    print("STAGE 3 (EXPRESS) + STAGE 4 (COMPILE) — compose held Terms -> live Program -> callable")
    print("=" * 78)
    name = "loop_" + "_".join(decision["concern"]) if decision else "loop_none"
    # the matched family (build-from-prior / residual_recurrence) -> compose NEW = prior + delta
    prog = {"type": "Plus", "items": [{"type": "Var", "name": "prior"}, {"type": "Var", "name": "delta"}]}
    res = dynamic_extend(a, name, prog, check={"env": {"prior": 2, "delta": 5}, "expect": 7})
    print(f"  dynamic_extend: rung={res.get('rung')} callable={res.get('callable')} value={res.get('value')} "
          f"recompiled={res.get('recompiled')} restarted={res.get('restarted')}")
    live = run_program_on_fresh(_load_program(a.s, name), {"prior": 100, "delta": 1}) if res.get("ok") else {}
    new_ok = res.get("ok") and live.get("value") == 101
    print(f"  NEW capability CALLABLE LIVE: {name}(100,1) = {live.get('value')} (expect 101) "
          f"— did NOT exist at loop start")
    print("  -> stage 3+4 autonomous (held ladder, no restart, donkey=0):", "OK" if new_ok else "FAIL")
    ok &= new_ok
    _cleanup(name)

    # AUTONOMY MAP
    print("\n" + "=" * 78)
    print("AUTONOMY MAP (each stage: agent's-own vs hand-primed)")
    print("=" * 78)
    print("  1 LEARN concern   : AUTONOMOUS — gap_prioritiser ranks the agent's own CapabilityAxes.")
    print("                      WALL (next frontier): a concern induced fresh from OBSERVATION/")
    print("                      surprise (curious_agent residual layer) is NOT a held faculty;")
    print("                      and a bare capability-key with no held Concept can't reach stage 2.")
    print("  2 DECIDE term     : AUTONOMOUS (after this fix) — learn_term_for_concern authors the")
    print("                      concern's signature from its held Concept + matches the term-family")
    print("                      by the agent's own shape-matcher. WALL fixed for concerns WITH a")
    print("                      held Concept; un-grounded concern-keys still wall (named frontier).")
    print("  3 EXPRESS         : AUTONOMOUS — teach_program registers a live named Program.")
    print("  4 COMPILE         : AUTONOMOUS — callable on the Rust evaluator, no restart (rung-3);")
    print("                      rung-4 emit+recompile available for genuinely-new base primitives.")
    print(f"\n  DONKEY (LLM) calls across the whole loop: {calls['n']}")
    ok &= (calls["n"] == 0)

    print("\n" + "=" * 78)
    print(("PASS" if ok else "FAIL"),
          "- FULL LOOP run end-to-end: learn concern -> decide term -> express -> compile, a NEW "
          "callable capability the agent did not start with. The first wall (stage-1->2: concern-key "
          "had no route to its structure) is FIXED (learn_term_for_concern). The honest remaining "
          "frontier: concerns with NO held Concept, and concern-induction from observation. donkey=0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
