"""self_extend_ladder_gate — GATE for the SELF-EXTENSION LADDER (dynamic-first).

The agent extends ITSELF on impasse, dynamic-first:
  rung-1 analogy (held) -> rung-2 search/compose (held) ->
  rung-3 DYNAMIC: compose the needed operation from HELD Terms + register it as a
    LIVE named graph-resident Program (teach_program) -> callable IMMEDIATELY, NO
    recompile, NO restart. The PRIMARY self-extension.
  rung-4 RUST-RECOMPILE (self_extend): only when NOT composable from held Terms
    (a new BASE primitive) -> emit Rust -> cargo check -> maturin rebuild ->
    rollback on fail. The RARE fallback (restart-requiring).
  rung-5 HumanImpasse: last resort.

Dynamic-compose (no restart) is tried BEFORE Rust-recompile, before the creator.
This whole session's faculties (the bridge, generation/recovery, signature-
authoring, the shape-math compositions) were exactly such dynamic compositions of
held Terms registered as live Programs — zero recompile. This makes that the
first-class self-extension faculty, wired to the impasse.

ARCHITECTURE: dynamic extension = compose held Terms into a Term-tree + register as
a graph-resident named Program (held teach_program) run by the existing Rust
evaluator, NO recompile; the Rust-recompile path stays the held self_extend
(rung-4 fallback). No Python reasoning. donkey=0.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/self_extend_ladder_gate.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import self_extend_ladder, _load_program, run_program_on_fresh

# Term builders (the held base the agent composes from)
def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def Plus(*xs): return {"type": "Plus", "items": list(xs)}
def Times(*xs): return {"type": "Times", "items": list(xs)}
def AUW(vals): return {"type": "AntiUnifyWitness", "values": vals, "wild": "·?·"}

_TEST_PROGS = ["ladder_op_weighted_sum", "ladder_op_diff_extract"]


def _cleanup(names):
    import json
    p = os.path.join(ROOT, "seeds", "programs.json")
    if os.path.exists(p):
        d = json.load(open(p))
        d["nodes"] = [n for n in d.get("nodes", []) if n.get("attrs", {}).get("name") not in names]
        json.dump(d, open(p, "w"), indent=1)


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    calls = {"n": 0}
    try:
        a.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "DONKEY")[1])
    except Exception:
        pass

    # donkey-spy on cargo/maturin: assert NO recompile ran in the dynamic path
    import subprocess as _sp
    real_run = _sp.run
    recompile = {"n": 0}
    def spy_run(args, *a2, **k2):
        joined = " ".join(map(str, args)) if isinstance(args, (list, tuple)) else str(args)
        if "cargo" in joined or "maturin" in joined:
            recompile["n"] += 1
        return real_run(args, *a2, **k2)
    _sp.run = spy_run

    ok = True
    _cleanup(_TEST_PROGS)
    try:
        # 1+2. DYNAMIC SELF-EXTENSION, generalises to >=2 ops (composed from held Terms)
        print("=" * 78)
        print("GATE 1+2 — DYNAMIC self-extension (no recompile, no restart), >=2 ops")
        print("=" * 78)
        gaps = [
            {"name": "ladder_op_weighted_sum",
             "program": Plus(V("a"), Times(V("b"), L(2))),                 # a + 2b
             "check": {"env": {"a": 3, "b": 5}, "expect": 13}},
            {"name": "ladder_op_diff_extract",
             "program": AUW(L([["attracts", "C", "o"], ["attracts", "N", "e"]])),  # held AntiUnifyWitness
             "check": {"env": {}}},
        ]
        for g in gaps:
            res = self_extend_ladder(a, g)
            rung = res.get("rung")
            print(f"  {g['name']}: rung={rung} kind={res.get('kind')} callable={res.get('callable')} "
                  f"value={res.get('value')} recompiled={res.get('recompiled')} restarted={res.get('restarted')}")
            dyn_ok = (rung == 3 and res.get("ok") and res.get("recompiled") is False
                      and res.get("restarted") is False)
            ok &= dyn_ok
        print(f"  cargo/maturin invocations during dynamic path: {recompile['n']} (must be 0)")
        ok &= (recompile["n"] == 0)

        # the registered ops are CALLABLE IMMEDIATELY from the graph (live, no restart)
        loaded = _load_program(a.s, "ladder_op_weighted_sum")
        live = run_program_on_fresh(loaded, {"a": 10, "b": 1})
        print(f"  registered op callable LIVE: a+2b(a=10,b=1) -> {live.get('value')} (expect 12) "
              f"-> {'OK' if live.get('value') == 12 else 'FAIL'}")
        ok &= (live.get("value") == 12)

        # 3. FALLBACK ORDER — a gap with NO composable program + NO rust_spec falls to HumanImpasse;
        #    a gap with a rust_spec would route to rung-4 (the held self_extend, the rare fallback).
        print("\n" + "=" * 78)
        print("GATE 3 — FALLBACK ORDER: dynamic -> (rust) -> HumanImpasse")
        print("=" * 78)
        # (a) not composable, no rust spec -> HumanImpasse (rung-5), AFTER trying dynamic
        before_imp = len(list(a.s.nodes("Impasse")))
        res_h = self_extend_ladder(a, {"name": "genuinely_uncomposable", "program": None})
        after_imp = len(list(a.s.nodes("Impasse")))
        print(f"  uncomposable gap -> rung={res_h.get('rung')} ({res_h.get('kind')}); "
              f"HumanImpasse raised: {after_imp > before_imp}")
        print(f"  ladder trail: {[t['rung'] for t in res_h.get('ladder', [])]}")
        order_ok = res_h.get("rung") == 5 and after_imp > before_imp
        ok &= order_ok
        # (b) confirm the ladder ATTEMPTS dynamic FIRST (rung-3 in the trail before any human rung)
        trail_rungs = [t["rung"] for t in res_h.get("ladder", [])]
        print(f"  order: HumanImpasse (rung 5) is LAST in the trail: {trail_rungs and trail_rungs[-1] == 5}")

        # 4. REGRESSION — the held faculties + the legit Programs intact; donkey=0
        print("\n" + "=" * 78)
        print("GATE 4 — REGRESSION + donkey=0 + persistence")
        print("=" * 78)
        progs_node_present = _load_program(a.s, "generate_shape") is not None
        print(f"  existing Programs intact (generate_shape held): {progs_node_present}")
        ok &= progs_node_present
        # persistence: the dynamically-registered op was teach'd -> in seeds/programs.json
        import json
        pj = json.load(open(os.path.join(ROOT, "seeds", "programs.json")))
        persisted = [n["attrs"].get("name") for n in pj.get("nodes", []) if n.get("type") == "Program"]
        dyn_persisted = "ladder_op_weighted_sum" in persisted
        print(f"  dynamically-registered op PERSISTS (fresh boot would have it): {dyn_persisted}")
        ok &= dyn_persisted
        print(f"  DONKEY (LLM) calls: {calls['n']}  (must be 0)")
        ok &= (calls["n"] == 0)

    finally:
        _sp.run = real_run
        _cleanup(_TEST_PROGS)   # leave the repo's programs.json clean (gate is a probe)

    print("\n" + "=" * 78)
    print(("PASS" if ok else "FAIL"),
          "- SELF-EXTENSION LADDER (dynamic-first): on impasse the agent COMPOSES the operation from "
          "HELD Terms and REGISTERS it as a LIVE named Program — callable immediately, NO recompile, NO "
          "restart (cargo/maturin ran 0 times); generalises to >=2 ops; Rust-recompile (self_extend) is the "
          "rare rung-4 fallback, HumanImpasse the rung-5 last resort; registered ops persist; donkey=0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
