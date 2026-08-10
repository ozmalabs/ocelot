"""Persistence demo: run twice, see the substrate's self-modifications
survive a restart.

Per user: 'wire in save/load for persistent self-modification'.

This script:
  1. Attempts to load saved substrate state from ./tmp/substrate_state.json
  2. If first run (no saved state):
       a. Bootstrap a fresh substrate
       b. Install all foundational Mts
       c. Inject RunnerObservations
       d. Run AST migration of Python detectors/corrections
       e. Run meta-handlers (detect unread + synthesise qualities)
       f. Save state
  3. If subsequent run (state loaded):
       a. Skip bootstrap — state is already present
       b. Just run the cortex assessment + derivation mechanism
       c. Show that synthesised qualities persisted + still score
  4. Print key counts for comparison

Run TWICE to see the substrate's persistent self-modification:

  $ python scripts/persist_self_modification.py    # first run: bootstrap
  $ python scripts/persist_self_modification.py    # second run: loaded

After run 1, the saved state file contains the substrate's modified
graph: synthesised qualities, FilterSpec/ActionSpec nodes, AST-migrated
detectors, gap reports. After run 2, the substrate loads that state
and the cortex's FIRST assessment already reflects the
self-modifications — no need to re-run the loop.
"""
from __future__ import annotations

import importlib
import inspect
import os
import re
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


STATE_PATH = os.path.join(
    os.environ.get("CLAUDE_JOB_DIR", "/tmp"),
    "substrate_state.json",
)
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
        "FilterSpec", "ActionSpec",
        "TheoryEnactmentGap", "UnreadObservationEvent",
        "DormantTheoryEvent", "UndeclaredEnactmentEvent",
        "HandlerSynthesisAttempt",
        "Cortex", "Sign", "Mention", "Message",
    )
    edges = (
        "has_concept", "has_rule", "in_category", "genlMt",
        "refers_to", "owns_microtheory", "assesses", "produced",
        "scored_on", "detected_smell", "for_quality", "for_smell",
        "decomposes", "best_for", "anti_pattern_for",
        "design_tag", "language_for_target", "applies_when",
        "observed_as", "applies_to", "has_gap_report",
        "implements",
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
                        "provenance": "persist",
                    })
                except Exception:
                    pass
    return s


def discover_seed_installers():
    out = []
    domains_dir = Path(__file__).resolve().parent.parent / "domains"
    for f in sorted(domains_dir.glob("*.py")):
        if f.name.startswith("__"):
            continue
        src = f.read_text()
        for match in re.finditer(r"^def (install_\w+_seed)\(",
                                  src, re.MULTILINE):
            fn_name = match.group(1)
            mod_name = f.stem
            try:
                mod = importlib.import_module(f"domains.{mod_name}")
                fn = getattr(mod, fn_name)
                sig = inspect.signature(fn)
                positional = [
                    p for p in sig.parameters.values()
                    if p.kind in (
                        inspect.Parameter.POSITIONAL_ONLY,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD)
                    and p.default is inspect.Parameter.empty
                ]
                if len(positional) == 1:
                    out.append((f"domains.{mod_name}", fn_name))
            except Exception:
                continue
    return out


def install_everything(s):
    for mod_name, fn_name in discover_seed_installers():
        try:
            mod = importlib.import_module(mod_name)
            getattr(mod, fn_name)(s)
        except Exception:
            continue


def inject_runner_observations(s):
    def add(cat, key, value, detail=""):
        try:
            s.add_node("RunnerObservation",
                       {"category": cat, "key": key,
                        "value": str(value), "detail": detail,
                        "source": "persist_demo"})
        except Exception:
            pass

    if SUBSTRATE_BINARY.exists():
        size = SUBSTRATE_BINARY.stat().st_size
        add("binary_size", "bytes", size)
        with open(SUBSTRATE_BINARY, "rb") as f:
            elf = f.read(64)
        if elf[:4] == b"\x7fELF":
            add("binary_format", "ELF", True)
            cls = elf[4]
            add("binary_word_size", "bits",
                "64" if cls == 2 else "32")
            machine = struct.unpack("<H", elf[18:20])[0]
            machine_name = {0x3E: "x86_64",
                            0xB7: "aarch64"}.get(machine, "unknown")
            add("instruction_set_architecture", "e_machine",
                machine_name)
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        block = cpuinfo.read_text().split("\n\n")[0]
        for line in block.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                k, v = k.strip(), v.strip()
                if k in ("model name", "cache size",
                         "cpu cores", "cpu MHz", "address sizes"):
                    add("cpu_property", k, v)
                if k == "flags":
                    for f in ("avx", "avx2", "avx512f", "fma",
                              "aes", "bmi2"):
                        if f in v.split():
                            add("cpu_feature_present", f, True)
    s_test = _native.Substrate()
    start = time.perf_counter()
    for i in range(1000):
        s_test.add_node("Concept", {"i": i})
    elapsed = time.perf_counter() - start
    add("operation_timing", "add_node_throughput",
        f"{1000 / elapsed:,.0f} ops/sec")


def bootstrap(s):
    """Full pipeline: install seeds, observations, migrate, meta-handle."""
    install_everything(s)
    inject_runner_observations(s)
    from domains.code_writing_cortex import CodeWritingCortex
    CodeWritingCortex(s).install()
    from domains.python_migration import (
        run_ast_migration, run_correction_migration,
    )
    run_ast_migration(s)
    run_correction_migration(s)
    from domains.meta_handlers import (
        install_meta_handler_graph_specs, run_meta_handlers,
    )
    install_meta_handler_graph_specs(s)
    run_meta_handlers(s)
    # Tag substrate components with the neuroscience concepts they
    # implement — graph-resident answers to 'what neural mechanism
    # does this part of me embody?'
    from domains.neuroscience_tagging import tag_all_substrate_components
    tag_summary = tag_all_substrate_components(s)
    print(f"  Neuroscience tags applied:")
    for k, v in tag_summary.items():
        print(f"    {k}: {v}")
    # Sample queries — direct graph traversal answers.
    from domains.neuroscience_tagging import (
        what_does_this_implement,
    )
    print(f"  Sample queries (graph-resident answers):")
    for fs in s.nodes("FilterSpec"):
        name = str(s.node(fs)["attrs"].get("name", ""))
        if "anticipation" in name.lower():
            answers = what_does_this_implement(s, fs)
            print(f"    '{name}' implements: {', '.join(answers)}")
            break
    for fs in s.nodes("FilterSpec"):
        name = str(s.node(fs)["attrs"].get("name", ""))
        if "frustration" in name.lower():
            answers = what_does_this_implement(s, fs)
            print(f"    '{name}' implements: {', '.join(answers)}")
            break
    for mt in s.nodes("Microtheory"):
        name = str(s.node(mt)["attrs"].get("name", ""))
        if name == "self_improvement_dynamics":
            answers = what_does_this_implement(s, mt)
            print(f"    Mt '{name}' implements: {', '.join(answers)}")
            break
    for mt in s.nodes("Microtheory"):
        name = str(s.node(mt)["attrs"].get("name", ""))
        if name == "causal_attitude_networks":
            answers = what_does_this_implement(s, mt)
            print(f"    Mt '{name}' implements: {', '.join(answers)}")
            break


def report_state(s, run_label: str):
    from domains.architecture_cortex import ArchitectureCortex
    from domains.derivation_mechanism import run_derivation
    from domains.self_persistence import summary_after_load

    counts = summary_after_load(s)
    print(f"  Graph node counts (by type):")
    for k, v in counts.items():
        if v > 0:
            print(f"    {k:<32} {v}")
    print()

    cortex = ArchitectureCortex(s).install()
    subject = None
    for n in s.nodes("CodeWritingCortex"):
        subject = n
        break
    if subject is not None:
        a_nid = cortex.assess(subject)
        a = s.node(a_nid)["attrs"]
        print(f"  Cortex assessment ({run_label}):")
        print(f"    Overall: {a['total_score']}/{a['max_total_score']}"
              f"  ({a['overall_pct']}%)")
        print(f"    Qualities scored: {a['n_qualities']}  "
              f"Smells: {a['smell_count']}")
        # Distinguish synthesised vs original.
        original = {"separation_of_concerns", "abstraction_layering",
                    "introspectability", "data_drivenness",
                    "compositional_reuse"}
        for qs in s.neighbours(a_nid, "scored_on"):
            attrs = s.node(qs)["attrs"]
            name = str(attrs.get("quality_name", ""))
            if name in original:
                continue
            print(f"      synthesised: {name:<48} "
                  f"{attrs['score']}/{attrs['max_score']}")
    print()

    deriv = run_derivation(s)
    print(f"  Derivation mechanism:")
    print(f"    Mts walked:      {deriv['n_mts_walked']}")
    print(f"    Dormant Mts:     {deriv['n_dormant_mts']}")
    print(f"    FilterSpec:      {deriv['n_filter_specs']}")
    print(f"    ActionSpec:      {deriv['n_action_specs']}")
    print(f"    Qualities:       {deriv['n_qualities']}")


def main():
    from domains.self_persistence import (
        load_state, save_state, state_exists,
    )

    print("=" * 72)
    print("PERSISTENT SELF-MODIFICATION DEMO")
    print(f"State file: {STATE_PATH}")
    print(f"State exists: {state_exists(STATE_PATH)}")
    print("=" * 72)
    print()

    s = fresh_substrate()
    loaded = load_state(s, STATE_PATH)

    if not loaded:
        print(">>> NO SAVED STATE FOUND — bootstrapping from scratch")
        print()
        bootstrap(s)
        print()
        print("--- AFTER BOOTSTRAP ---")
        report_state(s, "fresh bootstrap")
        print()
        save_info = save_state(s, STATE_PATH)
        print(f"--- SAVED STATE ---")
        print(f"  Path:        {save_info['path']}")
        print(f"  Size:        {save_info['size_bytes']:,} bytes")
        print(f"  Nodes:       {save_info['n_nodes']:,}")
        print(f"  Edges:       {save_info['n_edges']:,}")
        print(f"  Productions: {save_info['n_productions']:,}")
        print()
        print(">>> RUN AGAIN to see the saved state load + persist.")
    else:
        print(">>> LOADED SAVED STATE — substrate's self-modifications"
              " survived restart")
        print()
        print("--- AFTER LOAD ---")
        report_state(s, "from saved state")
        print()
        # Run the meta-handlers ONE MORE TIME. They should be idempotent:
        # detect_unread_observations should find 0 new categories
        # (the synthesised qualities already cover them).
        from domains.meta_handlers import run_meta_handlers
        mh = run_meta_handlers(s)
        print("  Meta-handlers re-run on loaded state:")
        for k, v in mh.items():
            print(f"    {k}: {v}")
        print()
        print("  Expected: unread_observations_detected = 0")
        print("  (because the previously-synthesised qualities are")
        print("   still in the loaded graph + still cover those")
        print("   categories)")
        print()
        # Re-save (state is now slightly extended).
        save_state(s, STATE_PATH)


if __name__ == "__main__":
    main()
