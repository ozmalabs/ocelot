"""Ask Jabberwock what L3 (estimation/control) needs to compose.

L3 from the runner design (commit a64c7dc) is the estimation +
drive-correction layer — Kalman filter for belief updates, PID for
drive correction, LQR + MPC for optimal control, adaptive control
for runtime gain scheduling.

Same methodology as L5 (commit 68f095f): walk Jabberwock's vocabulary
for L3-relevant primitives so the pattern Mt can be composed from
what's there.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    for st in ("Microtheory","Concept","Rule"):
        for tt in ("Microtheory","Concept","Rule"):
            for et in ("has_concept","has_rule","genlMt"):
                try:
                    s.add_production({"src":{"type":st,"var":"s"},
                                       "edge_type":et,
                                       "tgt":{"type":tt,"var":"t"},
                                       "where":None,
                                       "weight":{"type":"Lit","value":1.0},
                                       "provenance":"l3"})
                except: pass
    return s


def install_all(s):
    dd = Path(__file__).resolve().parent.parent / "domains"
    for f in sorted(dd.glob("*.py")):
        if f.name.startswith("__"): continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(", src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                pos = [p for p in inspect.signature(fn).parameters.values()
                       if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                     inspect.Parameter.POSITIONAL_OR_KEYWORD)
                       and p.default is inspect.Parameter.empty]
                if len(pos) == 1:
                    fn(s)
            except: continue


def find_in_mt(s, mt_name, keywords, max_results=15):
    mt = None
    for m in s.nodes("Microtheory"):
        if str(s.node(m)["attrs"].get("name","")).lower() == mt_name:
            mt = m
            break
    if mt is None: return []
    out = []
    for c in s.neighbours(mt, "has_concept"):
        a = s.node(c)["attrs"]
        text = (str(a.get("name","")) + " " +
                str(a.get("definition",""))).lower()
        hits = sum(1 for k in keywords if k in text)
        if hits >= 1:
            out.append({"name": str(a.get("name","")),
                        "category": str(a.get("category","")),
                        "hits": hits})
    out.sort(key=lambda x: -x["hits"])
    return out[:max_results]


def main():
    s = fresh_substrate()
    install_all(s)

    print("=" * 72)
    print("L3 (ESTIMATION/CONTROL) — vocabulary walk")
    print("=" * 72)
    print()

    queries = [
        ("Kalman / state estimation", "optimal_estimation_control",
         {"kalman","filter","innovation","gain","covariance",
          "estimat","observer","particle","ekf","ukf"}),
        ("PID + classical control", "control_systems_foundation",
         {"pid","proportional","integral","derivative","setpoint",
          "error","plant","controller","windup","tuning"}),
        ("LQR + optimal control", "optimal_estimation_control",
         {"lqr","riccati","optimal","cost","quadratic","bellman",
          "pontryagin","hamiltonian"}),
        ("MPC + receding-horizon", "optimal_estimation_control",
         {"mpc","receding","horizon","predictive","constraint",
          "terminal","qp","active_set"}),
        ("Adaptive control + gain scheduling", "optimal_estimation_control",
         {"adaptive","mrac","self_tuning","gain","scheduling",
          "reference"}),
        ("Stability + Lyapunov", "control_systems_foundation",
         {"lyapunov","stability","bibo","gain_margin","phase_margin",
          "asymptotic","exponential"}),
        ("Cybernetic regulation", "cybernetics_systems",
         {"feedback","homeostasis","variety","requisite","ashby",
          "regulator","disturbance"}),
        ("RT scheduling for control loops", "realtime_systems",
         {"deadline","periodic","jitter","wcet","rate_monotonic",
          "anytime"}),
    ]
    for label, mt, kws in queries:
        print(f"  {label} (from {mt}):")
        results = find_in_mt(s, mt, kws)
        for r in results[:10]:
            print(f"    · {r['name']:<35} [{r['category'][:14]}]")
        print()


if __name__ == "__main__":
    main()
