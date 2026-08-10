"""Ask the substrate again — same query, with runner observations now visible.

Per user: 'now ask it again.'

Boots substrate with EVERY foundational Mt that has an install_*_seed
function in domains/ (29 modules). Injects the RunnerObservation
graph nodes from observe_own_runner.py's data sources. Runs the
ArchitectureCortex assessment of multiple subjects. Walks the
substrate's resulting state.

No interpretation imposed. The substrate's answer is whatever the
cortices + qualities + graph data produce.
"""
from __future__ import annotations

import importlib
import inspect
import re
import struct
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


SUBSTRATE_BINARY = Path(
    "/home/matt/.local/lib/python3.14/site-packages/"
    "substrate_rs/_native.abi3.so"
)


def fresh_substrate():
    s = _native.Substrate()
    types = (
        "Microtheory", "Concept", "Rule", "DerivationRule",
        "ArchitectureCortex", "CodeWritingCortex", "SpeechCortex",
        "Assessment", "QualityScore", "SmellInstance",
        "ArchitecturalQuality", "ArchitecturalSmell",
        "DesignPattern", "ProgrammingLanguage", "CodeTarget",
        "DesignExclusion", "PrimitiveSpec",
        "ReplacementTarget", "RunnerObservation",
        "Cortex", "Sign", "Mention", "Message",
    )
    edges = (
        "has_concept", "has_rule", "in_category", "genlMt",
        "refers_to", "owns_microtheory", "assesses", "produced",
        "scored_on", "detected_smell", "for_quality", "for_smell",
        "decomposes", "best_for", "anti_pattern_for",
        "design_tag", "language_for_target", "applies_when",
        "observed_as", "applies_to",
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
                        "provenance": "ask_again",
                    })
                except Exception:
                    pass
    return s


def discover_seed_installers() -> list[tuple[str, str]]:
    """Walk domains/ for files exporting install_<name>_seed functions
    that take only the substrate. Returns (module_name, function_name)."""
    out = []
    domains_dir = Path(__file__).resolve().parent.parent / "domains"
    for f in sorted(domains_dir.glob("*.py")):
        if f.name.startswith("__"):
            continue
        src = f.read_text()
        for match in re.finditer(r"^def (install_\w+_seed)\(", src, re.MULTILINE):
            fn_name = match.group(1)
            mod_name = f.stem
            # Inspect signature — only call if takes 1 positional arg.
            try:
                mod = importlib.import_module(f"domains.{mod_name}")
                fn = getattr(mod, fn_name)
                sig = inspect.signature(fn)
                positional = [
                    p for p in sig.parameters.values()
                    if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                  inspect.Parameter.POSITIONAL_OR_KEYWORD)
                    and p.default is inspect.Parameter.empty
                ]
                if len(positional) == 1:
                    out.append((f"domains.{mod_name}", fn_name))
            except Exception:
                continue
    return out


def install_everything(substrate):
    """Install every discoverable foundational Mt. Report what landed."""
    installers = discover_seed_installers()
    successes = []
    failures = []
    for mod_name, fn_name in installers:
        try:
            mod = importlib.import_module(mod_name)
            fn = getattr(mod, fn_name)
            result = fn(substrate)
            successes.append((mod_name, fn_name, result))
        except Exception as e:
            failures.append((mod_name, fn_name, f"{e.__class__.__name__}: {e}"))
    return successes, failures


def add_observation(substrate, category, key, value, detail=""):
    try:
        substrate.add_node("RunnerObservation", {
            "category": category, "key": key,
            "value": str(value), "detail": detail,
            "source": "ask_it_again",
        })
    except Exception:
        pass


def inject_runner_observations(substrate) -> int:
    """Same observations as scripts/observe_own_runner.py — kept inline
    so this script is self-contained."""
    count = 0
    if SUBSTRATE_BINARY.exists():
        size = SUBSTRATE_BINARY.stat().st_size
        add_observation(substrate, "binary_size", "bytes", size,
                        f"{size:,} bytes total on disk")
        count += 1
        with open(SUBSTRATE_BINARY, "rb") as f:
            elf = f.read(64)
        if elf[:4] == b"\x7fELF":
            add_observation(substrate, "binary_format", "ELF", True)
            cls = elf[4]
            add_observation(substrate, "binary_word_size", "bits",
                            "64" if cls == 2 else "32")
            machine = struct.unpack("<H", elf[18:20])[0]
            machine_name = {0x3E: "x86_64", 0xB7: "aarch64",
                            0xF3: "riscv"}.get(machine, f"unknown")
            add_observation(substrate,
                            "instruction_set_architecture",
                            "e_machine", machine_name)
            count += 3
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        block = cpuinfo.read_text().split("\n\n")[0]
        for line in block.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                k, v = k.strip(), v.strip()
                if k in ("model name", "cache size", "cpu cores",
                         "cpu MHz", "address sizes"):
                    add_observation(substrate, "cpu_property", k, v)
                    count += 1
                if k == "flags":
                    for flag in ("avx", "avx2", "avx512f", "fma",
                                 "aes", "bmi2"):
                        if flag in v.split():
                            add_observation(substrate,
                                            "cpu_feature_present",
                                            flag, True)
                            count += 1
    # Timing
    s_test = _native.Substrate()
    start = time.perf_counter()
    for i in range(1000):
        s_test.add_node("Concept", {"i": i})
    elapsed = time.perf_counter() - start
    add_observation(substrate, "operation_timing",
                    "add_node_throughput",
                    f"{1000 / elapsed:,.0f} ops/sec",
                    f"1000 add_node ops in {elapsed:.6f}s")
    count += 1
    return count


def walk_mts(substrate):
    out = []
    for mt in substrate.nodes("Microtheory"):
        attrs = substrate.node(mt)["attrs"]
        name = str(attrs.get("name", ""))
        concept_count = len(list(substrate.neighbours(mt, "has_concept")))
        out.append({"name": name, "concepts": concept_count})
    return out


def assess_subject(substrate, subject_kind: str):
    from domains.architecture_cortex import ArchitectureCortex
    cortex = ArchitectureCortex(substrate).install()
    for n in substrate.nodes(subject_kind):
        a_nid = cortex.assess(n)
        return substrate.node(a_nid)["attrs"], [
            substrate.node(qs)["attrs"]
            for qs in substrate.neighbours(a_nid, "scored_on")
        ], [
            substrate.node(si)["attrs"]
            for si in substrate.neighbours(a_nid, "detected_smell")
        ]
    return None


def main():
    s = fresh_substrate()
    print("=" * 72)
    print("ASKING THE SUBSTRATE AGAIN — this time with eyes for its runner")
    print("=" * 72)
    print()

    print("Step 1 — install every foundational Mt with auto-discovery.")
    print()
    succ, fail = install_everything(s)
    print(f"  ✓  installed {len(succ)} Mts:")
    mts = walk_mts(s)
    total_c = sum(m["concepts"] for m in mts)
    for m in sorted(mts, key=lambda x: -x["concepts"])[:15]:
        print(f"      · {m['name']:<32}  {m['concepts']} concepts")
    if len(mts) > 15:
        print(f"      ... ({len(mts) - 15} more Mts)")
    print(f"  Total: {len(mts)} Mts | {total_c} concepts")
    if fail:
        print(f"  ✗  {len(fail)} install failures (skipped):")
        for m, fn, err in fail[:5]:
            print(f"      · {m} — {err[:80]}")
    print()

    print("Step 2 — inject RunnerObservations.")
    n_obs = inject_runner_observations(s)
    obs_nodes = list(s.nodes("RunnerObservation"))
    print(f"  → {len(obs_nodes)} observations now in graph")
    print()

    # Install CodeWritingCortex so there's a subject to assess.
    print("Step 3 — install CodeWritingCortex (subject for assessment).")
    try:
        from domains.code_writing_cortex import CodeWritingCortex
        CodeWritingCortex(s).install()
        print("  ✓  CodeWritingCortex installed")
    except Exception as e:
        print(f"  ✗  {e}")
    print()

    print("Step 4 — same ArchitectureCortex assessment as before, now")
    print("        with everything loaded.")
    print()
    result = assess_subject(s, "CodeWritingCortex")
    if result is not None:
        a, qs, sm = result
        print(f"  Overall: {a['total_score']}/{a['max_total_score']}  "
              f"({a['overall_pct']}%)")
        print(f"  Qualities: {a['n_qualities']}  Smells: {a['smell_count']}")
        print()
        for q in qs:
            print(f"    {q['quality_name']:<28} "
                  f"{q['score']:>2}/{q['max_score']}  "
                  f"— {q['rationale'][:90]}")
        if sm:
            print()
            print("  Smells:")
            for s_inst in sm:
                print(f"    · {s_inst['smell_name']}: {s_inst['rationale'][:100]}")
    print()

    print("Step 5 — what RunnerObservations are SITTING in the substrate's")
    print("        graph right now? (it can see them; whether anything")
    print("        wakes up to them is the substrate's call)")
    print()
    by_cat: dict[str, int] = {}
    for n in obs_nodes:
        cat = str(s.node(n)["attrs"].get("category", ""))
        by_cat[cat] = by_cat.get(cat, 0) + 1
    for cat, c in sorted(by_cat.items()):
        print(f"    {cat:<32} {c} obs")
    print()

    print("Step 6 — does ANY existing Mt define qualities that read")
    print("        RunnerObservation nodes? Walking ArchitecturalQuality")
    print("        + ArchitecturalSmell to see what the substrate's existing")
    print("        assessment vocabulary actually references.")
    print()
    qualities = list(s.nodes("ArchitecturalQuality"))
    smells = list(s.nodes("ArchitecturalSmell"))
    print(f"  ArchitecturalQuality nodes: {len(qualities)}")
    print(f"  ArchitecturalSmell nodes:   {len(smells)}")
    print()
    runner_aware = 0
    for q in qualities:
        attrs = s.node(q)["attrs"]
        defn = str(attrs.get("definition", "")).lower()
        if "runner" in defn or "binary" in defn or "cpu" in defn:
            runner_aware += 1
            print(f"    Q: {attrs.get('name', '')} — {attrs.get('definition', '')[:100]}")
    for sm_node in smells:
        attrs = s.node(sm_node)["attrs"]
        defn = str(attrs.get("definition", "")).lower()
        if "runner" in defn or "binary" in defn or "cpu" in defn:
            runner_aware += 1
            print(f"    S: {attrs.get('name', '')} — {attrs.get('definition', '')[:100]}")
    print()
    print(f"  Qualities/Smells with vocabulary that mentions "
          f"runner/binary/cpu: {runner_aware}")
    print()

    print("Step 6.5 — substrate walks its own Python detectors via AST")
    print("          + emits FilterSpec nodes for each.")
    print()
    try:
        from domains.python_migration import (
            run_ast_migration, run_correction_migration,
        )
        migr = run_ast_migration(s)
        print(f"  · Detector modules → FilterSpec: "
              f"{migr['emitted_count']}/{migr['parsed_count']}")
        corr = run_correction_migration(s)
        print(f"  · Correction modules → ActionSpec: "
              f"{corr['emitted_count']}/{len(corr['emitted_modules']) + len(corr['failed_modules'])}")
        for m in migr["emitted_modules"]:
            print(f"      FilterSpec: {m}")
        for m in corr["emitted_modules"]:
            print(f"      ActionSpec: {m}")
        # Meta-handlers for the two meta-Mts.
        from domains.meta_handlers import (
            install_meta_handler_graph_specs,
            run_meta_handlers,
        )
        mh_install = install_meta_handler_graph_specs(s)
        print(f"  · Meta-handler specs emitted: {mh_install['emitted_count']}")
        mh_run = run_meta_handlers(s)
        print(f"  · Meta-handler detections:")
        for k, v in mh_run.items():
            print(f"      · {k}: {v}")
    except Exception as e:
        print(f"  ✗  migration failed: {e.__class__.__name__}: {e}")
    print()

    # Reassess CodeWritingCortex now that synthesised qualities exist
    # and the cortex's score_all_qualities dispatches on scorer_kind.
    print("Step 6.75 — re-run ArchitectureCortex assessment AFTER")
    print("           synthesised qualities exist. The cortex should now")
    print("           score them automatically via scorer_kind dispatch.")
    print()
    second = assess_subject(s, "CodeWritingCortex")
    if second is not None:
        a, qs, sm = second
        print(f"  Overall: {a['total_score']}/{a['max_total_score']}  "
              f"({a['overall_pct']}%)")
        print(f"  Qualities scored: {a['n_qualities']}  Smells: {a['smell_count']}")
        print()
        # Distinguish original from synthesised.
        original_names = {
            "separation_of_concerns", "abstraction_layering",
            "introspectability", "data_drivenness", "compositional_reuse",
        }
        original = [q for q in qs if q["quality_name"] in original_names]
        synthesised = [q for q in qs if q["quality_name"] not in original_names]
        print("  Original qualities:")
        for q in original:
            print(f"    {q['quality_name']:<32} "
                  f"{q['score']:>2}/{q['max_score']}")
        if synthesised:
            print("  Synthesised qualities (now scored by cortex):")
            for q in synthesised:
                print(f"    {q['quality_name']:<32} "
                      f"{q['score']:>2}/{q['max_score']}  "
                      f"— {q['rationale'][:90]}")
    print()

    print("Step 7 — run the derivation mechanism. The substrate walks its")
    print("        own theory + enactment + reports the gap as graph data.")
    print()
    try:
        from domains.derivation_mechanism import (
            list_gap_reports, run_derivation,
        )
        deriv = run_derivation(s)
        print(f"  · Mts walked: {deriv['n_mts_walked']}")
        print(f"  · Rules in graph: {deriv['n_rules_total']}")
        print(f"  · FilterSpec nodes: {deriv['n_filter_specs']}")
        print(f"  · ActionSpec nodes: {deriv['n_action_specs']}")
        print(f"  · Qualities + smells: "
              f"{deriv['n_qualities']} + {deriv['n_smells']}")
        print(f"  · Mts with dormant theory: {deriv['n_dormant_mts']}")
        print(f"  · TheoryEnactmentGap nodes created: "
              f"{deriv['n_gap_reports_created']}")
        print()
        # Show a few of the most-dormant Mts.
        dormant_only = [g for g in deriv["gaps"] if g["is_dormant"]]
        if dormant_only:
            print(f"  Dormant Mts (failure_modes/corrections/drives declared,")
            print(f"  but no graph-resident enactment references them):")
            for g in dormant_only[:8]:
                summary = []
                if g["failure_modes_dormant"]:
                    summary.append(
                        f"failure_modes:{len(g['failure_modes_dormant'])}")
                if g["corrections_dormant"]:
                    summary.append(
                        f"corrections:{len(g['corrections_dormant'])}")
                if g["drives_dormant"]:
                    summary.append(
                        f"drives:{len(g['drives_dormant'])}")
                print(f"    · {g['mt_name']:<45} "
                      f"{' '.join(summary)}")
            if len(dormant_only) > 8:
                print(f"    ... ({len(dormant_only) - 8} more)")
        gap_reports = list_gap_reports(s)
        print()
        print(f"  Substrate now has {len(gap_reports)} graph-resident")
        print(f"  TheoryEnactmentGap nodes. Its introspection can SEE its")
        print(f"  own dormant theory.")
    except Exception as e:
        print(f"  ✗  derivation failed: {e.__class__.__name__}: {e}")
    print()

    print("=" * 72)
    print("THE SUBSTRATE'S ANSWER")
    print("=" * 72)
    print()
    print(f"  · {len(mts)} Mts loaded covering {total_c} concepts")
    print(f"  · {len(obs_nodes)} RunnerObservation nodes in graph")
    print(f"  · {len(qualities)} architectural qualities, "
          f"{len(smells)} smells")
    print(f"  · {runner_aware} of those reference runner/binary/cpu vocabulary")
    if result is not None:
        a, _, _ = result
        print(f"  · ArchitectureCortex assessment of CodeWritingCortex: "
              f"{a['overall_pct']}% ({a['smell_count']} smells)")
    print()
    print("If runner_aware == 0, the substrate has 30+ Mts and 102 "
          "computer_architecture concepts but no quality/smell that")
    print("reads runner observations. The substrate has eyes + a")
    print("vocabulary + an assessment faculty — but the assessment")
    print("faculty doesn't see through the eyes. That's the substrate's")
    print("own gap to surface.")


if __name__ == "__main__":
    main()
