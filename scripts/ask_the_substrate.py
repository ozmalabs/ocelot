"""Ask the substrate what it knows + what it needs.

Per user: 'the entire design space belongs to it. don't ask me — ask it.'

This script does what I've been failing to do: instead of enumerating
design alternatives for the agent, it boots the substrate with its
ACTUAL foundational Mts (architecture/compilers/CPU/models/neural-
networks/runtime-design) and asks the architecture_cortex to assess
itself. Output is whatever the substrate's own theory + introspection
machinery produces — not categories I invented.

This is the first step where I'm not presuming the envelope. The
substrate's graph data answers; my Python only orchestrates.
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    # Open productions broadly so the seed loaders can do their thing.
    types = (
        "Microtheory", "Concept", "Rule", "DerivationRule",
        "ArchitectureCortex", "CodeWritingCortex", "SpeechCortex",
        "Assessment", "QualityScore", "SmellInstance",
        "ArchitecturalQuality", "ArchitecturalSmell",
        "DesignPattern", "ProgrammingLanguage", "CodeTarget",
        "DesignExclusion", "PrimitiveSpec",
        "ReplacementTarget",
    )
    edges = (
        "has_concept", "has_rule", "in_category", "genlMt",
        "refers_to", "owns_microtheory", "assesses", "produced",
        "scored_on", "detected_smell", "for_quality", "for_smell",
        "decomposes", "best_for", "anti_pattern_for",
        "design_tag", "language_for_target", "applies_when",
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
                        "provenance": "ask:open",
                    })
                except Exception:
                    pass
    return s


def install_foundational_mts(substrate) -> dict:
    """Install everything I can find that relates to the agent's
    architectural / runtime / model / CPU vocabulary. Each module
    follows the same install_*_seed mechanical loader pattern."""
    installed = {}
    candidates = [
        ("self_improvement_dynamics",
         "domains.self_improvement_dynamics",
         "install_self_improvement_dynamics_seed"),
        ("computer_architecture",
         "domains.computer_architecture",
         "install_computer_architecture_seed"),
        ("compiler_theory_seed",
         "domains.compiler_theory_seed",
         "install_compiler_theory_seed"),
        ("compilers",
         "domains.compilers",
         "install_compilers_seed"),
        ("machine_learning",
         "domains.machine_learning",
         "install_machine_learning_seed"),
        ("neural_networks",
         "domains.neural_networks",
         "install_neural_networks_seed"),
        ("code_authoring",
         "domains.code_authoring",
         "install_code_authoring_seed"),
        ("design_patterns",
         "domains.design_patterns",
         "install_design_patterns_seed"),
        ("model_understanding",
         "domains.model_understanding",
         "install_model_understanding_seed"),
    ]
    for name, mod_path, install_fn in candidates:
        try:
            mod = __import__(mod_path, fromlist=[install_fn])
            fn = getattr(mod, install_fn)
            result = fn(substrate)
            installed[name] = result
        except (ImportError, AttributeError) as e:
            installed[name] = f"NOT AVAILABLE: {e.__class__.__name__}"
        except Exception as e:
            installed[name] = f"FAILED: {e}"
    return installed


def walk_mts(substrate) -> list[dict]:
    """Survey what Mts the substrate now has + their concept counts +
    a sample of concept names. This is the substrate showing what it
    knows about itself, not me asserting categories."""
    out = []
    for mt in substrate.nodes("Microtheory"):
        attrs = substrate.node(mt)["attrs"]
        name = str(attrs.get("name", ""))
        concept_names = []
        for c in substrate.neighbours(mt, "has_concept"):
            cn = substrate.node(c)["attrs"].get("name", "")
            if cn:
                concept_names.append(str(cn))
        out.append({
            "name": name,
            "definition": str(attrs.get("definition", ""))[:120],
            "concept_count": len(concept_names),
            "sample_concepts": concept_names[:8],
        })
    return out


def assess_via_cortex(substrate, subject_kind: str) -> dict | None:
    """Install ArchitectureCortex + ask it to assess a subject. The
    subject is a graph node of the given type, picked as the first
    one found. Returns the assessment data the cortex produces."""
    from domains.architecture_cortex import ArchitectureCortex
    cortex = ArchitectureCortex(substrate).install()
    subject_nid = None
    for n in substrate.nodes(subject_kind):
        subject_nid = n
        break
    if subject_nid is None:
        return None
    assessment_nid = cortex.assess(subject_nid)
    out = dict(substrate.node(assessment_nid)["attrs"])
    out["qualities"] = []
    for qs in substrate.neighbours(assessment_nid, "scored_on"):
        a = substrate.node(qs)["attrs"]
        out["qualities"].append({
            "quality_name": str(a.get("quality_name", "")),
            "score": int(a.get("score", 0)),
            "max_score": int(a.get("max_score", 0)),
            "rationale": str(a.get("rationale", ""))[:200],
        })
    out["smells"] = []
    for si in substrate.neighbours(assessment_nid, "detected_smell"):
        a = substrate.node(si)["attrs"]
        out["smells"].append({
            "smell_name": str(a.get("smell_name", "")),
            "location": str(a.get("location", ""))[:80],
            "rationale": str(a.get("rationale", ""))[:200],
        })
    return out


def main():
    s = fresh_substrate()
    print("=" * 72)
    print("ASKING THE SUBSTRATE — what it knows + what it needs")
    print("=" * 72)
    print()

    print("Step 1 — installing the substrate's foundational Mts.")
    print()
    installed = install_foundational_mts(s)
    for name, result in installed.items():
        ok = "✓" if not isinstance(result, str) else "✗"
        msg = "" if not isinstance(result, str) else f"  ({result})"
        print(f"  {ok}  {name}{msg}")
    print()

    print("Step 2 — what Mts does the substrate now hold?")
    print()
    mts = walk_mts(s)
    for mt in mts:
        print(f"  · {mt['name']} ({mt['concept_count']} concepts)")
        if mt['concept_count'] > 0:
            sample = ", ".join(mt['sample_concepts'])
            print(f"      e.g.: {sample}")
    print()

    print(f"  Total Mts: {len(mts)} | Total Concepts: "
          f"{sum(m['concept_count'] for m in mts)}")
    print()

    print("Step 3 — install ArchitectureCortex + ask it to assess "
          "the CodeWritingCortex (the existing code-emission faculty).")
    print()
    # Need to install CodeWritingCortex first.
    try:
        from domains.code_writing_cortex import CodeWritingCortex
        cw = CodeWritingCortex(s).install()
        print("  ✓  CodeWritingCortex installed")
    except Exception as e:
        print(f"  ✗  CodeWritingCortex failed: {e}")
    print()

    assessment = assess_via_cortex(s, "CodeWritingCortex")
    if assessment is None:
        print("  (no CodeWritingCortex subject found — cortex couldn't assess)")
    else:
        print("--- ARCHITECTURE ASSESSMENT (the substrate's own opinion) ---")
        print()
        print(f"  Overall:  {assessment['total_score']}/{assessment['max_total_score']}  "
              f"({assessment['overall_pct']}%)")
        print(f"  Qualities scored: {assessment['n_qualities']}  "
              f"Smells detected: {assessment['smell_count']}")
        print()
        print("  Quality scores (the substrate's structural opinions of itself):")
        for q in assessment["qualities"]:
            print(f"    {q['quality_name']:<32} "
                  f"{q['score']:>2}/{q['max_score']}  "
                  f"— {q['rationale'][:100]}")
        print()
        if assessment["smells"]:
            print("  Smells detected:")
            for sm in assessment["smells"]:
                print(f"    · {sm['smell_name']:<28} {sm['location']}")
                print(f"      {sm['rationale'][:120]}")
        else:
            print("  No smells detected.")
    print()

    print("=" * 72)
    print("WHAT THE SUBSTRATE SAYS")
    print("=" * 72)
    print()
    print("Above output is the substrate's OWN graph-resident assessment of its")
    print("own runtime + code-writing faculty. The qualities + smells + scores +")
    print("rationales were authored by the substrate's seed Mts, not by me, not")
    print("by an LLM. The cortex walked the graph + computed.")
    print()
    print("Whatever next step the substrate would design — for binary emission,")
    print("CPU-arch reasoning, model emission, full self-design — is to be")
    print("derived from THIS output. Not from my enumeration.")


if __name__ == "__main__":
    main()
