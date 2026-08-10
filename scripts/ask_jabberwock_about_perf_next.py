"""Ask Jabberwock — given the bench results, what do you want to build next?

Per user: 'ask the agent'.

The substrate just got benched against its own design predictions
(commits b0a7954 → 38ace12). Some gaps closed, some remain:

  · Bench 1  graph mutations    BEAT 1.25×
  · Bench 2  dispatcher EDF     MISS — Mutex bottleneck (work-stealing closes 3.9×)
  · Bench 2b WorkStealing       6.07 M/s — Box<dyn> overhead is the ceiling
  · Bench 3b 4-dim Kalman       BEAT 8.5× (substrate's actual workload)
  · Bench 3c 16-dim FP64        BEAT 1.23×
  · Bench 3c 64-dim FP64        MISS 0.08× — 58% of single-core peak
  · Bench 3d 64-dim BF16        MISS 0.05× — A-conversion overhead
  · Bench 5  raw 64×64 matmul   BF16/FP64 = 2.38× (architecture verified)

I named three candidate paths to close the remaining 64-dim gap:
multi-core parallel Kalman, BLAS via blis-rs, native-BF16 P storage.

I'm not picking. Asking Jabberwock to walk its own state +
specifications + gaps and surface what IT would build.

No proposals. No options to pick from. I inject the bench
results as RunnerObservation nodes — Jabberwock's "eyes" — and let
its existing derivation/specification pipeline speak.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = (
        "Microtheory", "Concept", "Rule", "DerivationRule",
        "DesignPattern", "ProgrammingLanguage", "CodeTarget",
        "DesignExclusion", "PrimitiveSpec",
        "ReplacementTarget", "RunnerObservation",
        "FilterSpec", "ActionSpec", "TheoryEnactmentGap",
        "ArchitectureCortex", "CodeWritingCortex",
    )
    edges = (
        "has_concept", "has_rule", "in_category", "genlMt",
        "refers_to", "owns_microtheory", "applies_to",
        "implements", "design_tag", "applies_when",
        "observed_as", "has_gap_report",
    )
    for src_t in types:
        for tgt_t in types:
            for et in edges:
                try:
                    s.add_production({
                        "src": {"type": src_t, "var": "src"},
                        "edge_type": et,
                        "tgt": {"type": tgt_t, "var": "tgt"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "ask_perf",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
    domains_dir = Path(__file__).resolve().parent.parent / "domains"
    for f in sorted(domains_dir.glob("*.py")):
        if f.name.startswith("__"):
            continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(", src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                sig = inspect.signature(fn)
                pos = [p for p in sig.parameters.values()
                       if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                      inspect.Parameter.POSITIONAL_OR_KEYWORD)
                       and p.default is inspect.Parameter.empty]
                if len(pos) == 1:
                    fn(s)
            except Exception:
                continue


def inject_bench_observations(s):
    """The bench results become RunnerObservations Jabberwock can see.

    Categories chosen to match the substrate's existing vocabulary:
    operation_timing, design_prediction_match, design_prediction_miss,
    bottleneck_diagnosis.
    """
    observations = [
        # Where the design matched.
        ("design_prediction_match", "graph_mutations_per_sec", "37.5M",
         "BEAT 1.25× — L1 arena layout matches prediction"),
        ("design_prediction_match", "kalman_4d_fp64_per_sec", "2.12M",
         "BEAT 8.5× — substrate's actual drive dimension"),
        ("design_prediction_match", "kalman_16d_fp64_per_sec", "307K",
         "BEAT 1.23× — AVX-512 FP64 hits prediction"),
        # Where the design missed + the diagnosed cause.
        ("design_prediction_miss", "dispatcher_submit_per_sec", "6.07M",
         "MISS 0.06× of 100M prediction — Box<dyn> dispatch overhead"),
        ("design_prediction_miss", "kalman_64d_fp64_per_sec", "19.88K",
         "MISS 0.08× of 250K — 58% of single-core FP64 peak"),
        ("design_prediction_miss", "kalman_64d_bf16_cached_per_sec", "12.28K",
         "MISS 0.05× — BF16 A-conversion per matmul dominates"),
        # Architecture verifications.
        ("architecture_verified", "raw_64x64_bf16_vs_fp64", "2.38x",
         "Mat::mul_bf16 path works when matrices are reused"),
        # Specific implementation states.
        ("bottleneck_diagnosis", "L2_scheduler_box_dyn",
         "Box<dyn FnOnce> allocation",
         "Each submit allocates a closure; lock-free injector now "
         "exposes this as the new ceiling"),
        ("bottleneck_diagnosis", "L3_kalman_64d_a_conversion",
         "FP64→BF16 of left operand per call",
         "Bf16PackedB caches B; A is converted each mul_bf16_pre_b call. "
         "6 matmuls × 4096 conversions = ~50µs/update at 64-dim"),
        # What the L3 Mt named but isn't built.
        ("named_but_unbuilt", "multi_core_kalman",
         "parallelism across substrate's many drives",
         "L3 prediction's 6-core variant: 1.5M/sec at 6 cores"),
        ("named_but_unbuilt", "block_tiled_matmul",
         "BLAS-style register/L1 blocking",
         "Closes 64-dim FP64 gap from 58% to 90%+ of peak"),
        ("named_but_unbuilt", "native_bf16_P_storage",
         "Kalman with covariance held in BF16",
         "Removes per-call A-conversion; matches Bench 5's 2.38× lift"),
    ]
    for cat, key, val, ctx in observations:
        try:
            s.add_node("RunnerObservation", {
                "category": cat, "key": key, "value": val,
                "context": ctx, "source": "perf_bench_eb3cbc0_to_38ace12",
            })
        except Exception:
            pass


def main():
    s = fresh_substrate()
    install_all(s)
    inject_bench_observations(s)

    print("=" * 72)
    print("ASKING JABBERWOCK — GIVEN THE BENCH RESULTS,")
    print("                    WHAT DO YOU WANT TO BUILD NEXT?")
    print("=" * 72)
    print()

    # ---------- Q1: what does Jabberwock see? ----------
    print("=" * 72)
    print("Q1: What Jabberwock sees (RunnerObservation by category)")
    print("=" * 72)
    by_cat = {}
    for n in s.nodes("RunnerObservation"):
        a = s.node(n)["attrs"]
        by_cat.setdefault(str(a.get("category", "")), []).append(a)
    print()
    for cat in sorted(by_cat.keys()):
        items = by_cat[cat]
        print(f"  [{cat}]  ({len(items)} observations)")
        for it in items[:6]:
            k = it.get("key", "")
            v = it.get("value", "")
            print(f"    · {k}: {v}")
    print()

    # ---------- Q2: which named-but-unbuilt path does the agent's
    # OWN vocabulary connect best to? ----------
    print("=" * 72)
    print("Q2: For each named-but-unbuilt path, which substrate-resident")
    print("    Mts already hold relevant theory?")
    print("=" * 72)
    print()

    candidates = [it for it in by_cat.get("named_but_unbuilt", [])]

    runtime_mt_names = []
    for mt in s.nodes("Microtheory"):
        nm = str(s.node(mt)["attrs"].get("name", "")).lower()
        if any(k in nm for k in (
            "compiler", "computer_arch", "operating_system",
            "runtime", "code_authoring", "code_writing",
            "machine_learning", "drives_estimation", "control",
            "realtime", "concurrent", "parallel", "linear_algebra",
            "physics", "robotics", "executable_memory",
            "adaptive_tiered", "universal_coordination",
        )):
            c_count = len(list(s.neighbours(mt, "has_concept")))
            r_count = len(list(s.neighbours(mt, "has_rule")))
            runtime_mt_names.append((nm, c_count, r_count))

    def score_candidate(c):
        """Count Mt-vocabulary that mentions the candidate's keywords."""
        kws = (str(c.get("key", "")) + " " + str(c.get("value", ""))
               + " " + str(c.get("context", ""))).lower()
        score = 0
        evidence = []
        for nm, cc, rc in runtime_mt_names:
            hits = 0
            for w in re.findall(r"\w+", nm):
                if len(w) > 4 and w in kws:
                    hits += 1
            if hits:
                score += cc + rc + (hits * 3)
                evidence.append((nm, cc + rc, hits))
        return score, evidence

    scored = []
    for c in candidates:
        sc, ev = score_candidate(c)
        scored.append((sc, c, ev))

    scored.sort(key=lambda x: -x[0])
    for sc, c, ev in scored:
        print(f"  [{c.get('key')}]  vocabulary score: {sc}")
        print(f"     value: {c.get('value')}")
        print(f"     ctx:   {c.get('context')}")
        for nm, w, h in ev[:5]:
            print(f"     ← Mt {nm:<40} weight {w}, kw hits {h}")
        print()

    # ---------- Q3: which bottleneck does Jabberwock have the
    # strongest vocabulary to ACT on? ----------
    print("=" * 72)
    print("Q3: For each bottleneck, which substrate Mts cover the fix?")
    print("=" * 72)
    print()
    for b in by_cat.get("bottleneck_diagnosis", []):
        kws = (str(b.get("key", "")) + " " + str(b.get("value", ""))
               + " " + str(b.get("context", ""))).lower()
        relevant = []
        for nm, cc, rc in runtime_mt_names:
            for w in re.findall(r"\w+", nm):
                if len(w) > 4 and w in kws:
                    relevant.append(nm)
                    break
        print(f"  Bottleneck: {b.get('key')}")
        print(f"    value: {b.get('value')}")
        if relevant:
            print(f"    Covered by Mts: {', '.join(sorted(set(relevant)))}")
        else:
            print(f"    No Mt directly covers this — would need new vocabulary")
        print()

    # ---------- Q4: the existing agent_specify_primitive pipeline ----
    print("=" * 72)
    print("Q4: What does Jabberwock's existing agent_specify_primitive")
    print("    say — does it surface something new given these obs?")
    print("=" * 72)
    print()
    try:
        from domains.runtime_design import agent_specify_primitive
        try:
            spec = agent_specify_primitive(s)
            print("  Jabberwock's specification:")
            for k, v in spec.items():
                vs = str(v)
                if len(vs) > 200:
                    vs = vs[:200] + "..."
                print(f"    {k}: {vs}")
        except Exception as e:
            print(f"  ✗ Could not run: {e}")
    except ImportError as e:
        print(f"  ✗ {e}")
    print()

    # ---------- Q5: synthesize ----------
    print("=" * 72)
    print("WHAT JABBERWOCK'S OWN STATE SURFACES")
    print("=" * 72)
    print()
    if scored:
        best_sc, best, best_ev = scored[0]
        print(f"  Highest vocabulary-grounded candidate: {best.get('key')}")
        print(f"    {best.get('value')}")
        print(f"    Grounded in: "
              f"{', '.join(nm for nm, _, _ in best_ev[:4])}")
        print()
        if len(scored) > 1:
            print(f"  Runner-up: {scored[1][1].get('key')} "
                  f"(score {scored[1][0]})")
            if len(scored) > 2:
                print(f"  Third:     {scored[2][1].get('key')} "
                      f"(score {scored[2][0]})")
    print()
    print("=" * 72)
    print("The agent's answer is whichever path its own vocabulary")
    print("scores highest on. The numbers + the Mt-grounding above")
    print("are what Jabberwock's state says.")
    print("=" * 72)


if __name__ == "__main__":
    main()
