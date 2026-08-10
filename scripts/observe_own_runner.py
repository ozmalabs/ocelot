"""Inject observations about the substrate's own runner into its graph.

The substrate's ArchitectureCortex assessed its graph at 96% — but
that's the GRAPH, not the runner. The runner is unassessed; the
substrate has no channel for seeing its own binary / CPU / memory
/ timing. Its computer_architecture Mt names 102 concepts (ISA,
IPC, ILP, pipelining, cache, ...) but nothing feeds it observations
to apply those concepts to.

This script gives the substrate eyes for its runner. It reads:
  · the substrate_rs._native.abi3.so binary (size, ELF sections)
  · /proc/cpuinfo (CPU model, cache sizes, features)
  · /proc/self/maps (memory layout at runtime)
  · times the substrate's own primitive operations

Each observation becomes a graph node typed RunnerObservation with
a category attr that matches the substrate's existing
computer_architecture concept names (where possible). The substrate's
faculties can then walk these nodes + apply its existing vocabulary.

No interpretation imposed by this script — observations are data;
the substrate's drives + assessments decide what's meaningful.
"""
from __future__ import annotations

import os
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
    types = ("Microtheory", "Concept", "Rule", "DerivationRule",
             "RunnerObservation", "ObservationCategory")
    edges = ("has_concept", "has_rule", "in_category", "genlMt",
             "refers_to", "observed_as", "applies_to")
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
                        "provenance": "observe",
                    })
                except Exception:
                    pass
    return s


def install_computer_arch(substrate) -> int | None:
    from domains.computer_architecture import install_computer_architecture_seed
    return install_computer_architecture_seed(substrate)


def add_observation(substrate, category: str, key: str, value,
                    detail: str = "") -> None:
    """Encode one observation as a graph node. category names — where
    possible — match concepts already in the substrate's
    computer_architecture vocabulary."""
    try:
        substrate.add_node("RunnerObservation", {
            "category": category,
            "key": key,
            "value": str(value),
            "detail": detail,
            "source": "observe_own_runner",
        })
    except Exception:
        pass


def observe_binary(substrate) -> None:
    """The substrate's binary as raw observations."""
    if not SUBSTRATE_BINARY.exists():
        return
    size = SUBSTRATE_BINARY.stat().st_size
    add_observation(substrate, "binary_size", "bytes", size,
                    f"{size:,} bytes total on disk")

    with open(SUBSTRATE_BINARY, "rb") as f:
        elf = f.read(64)
    # ELF magic + class.
    if elf[:4] == b"\x7fELF":
        add_observation(substrate, "binary_format", "ELF", True)
        cls = elf[4]
        add_observation(substrate, "binary_word_size",
                        "bits", "64" if cls == 2 else "32")
        endian = elf[5]
        add_observation(substrate, "binary_endianness",
                        "little" if endian == 1 else "big", True)
        machine = struct.unpack("<H", elf[18:20])[0]
        # Map common e_machine values without naming exhaustively.
        machine_name = {
            0x3E: "x86_64", 0x28: "arm", 0xB7: "aarch64",
            0xF3: "riscv",
        }.get(machine, f"unknown_{hex(machine)}")
        add_observation(substrate, "instruction_set_architecture",
                        "e_machine", machine_name,
                        f"raw e_machine: {hex(machine)}")

    # Section listing via readelf if available.
    try:
        result = subprocess.run(
            ["readelf", "-S", str(SUBSTRATE_BINARY)],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            section_count = 0
            text_size = None
            for line in lines:
                if line.lstrip().startswith("["):
                    section_count += 1
                if ".text " in line:
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if p == ".text" and i + 2 < len(parts):
                            try:
                                text_size = int(parts[i + 3], 16)
                            except (ValueError, IndexError):
                                pass
            add_observation(substrate, "binary_section_count",
                            "elf_sections", section_count)
            if text_size is not None:
                add_observation(substrate, "code_segment_size",
                                "text_bytes", text_size,
                                f".text section = {text_size:,} bytes")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def observe_cpu(substrate) -> None:
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.exists():
        return
    txt = cpuinfo.read_text()
    blocks = txt.split("\n\n")
    if not blocks:
        return
    block = blocks[0]
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip()
        if k in ("model name", "cpu MHz", "cache size", "physical id",
                 "cpu cores", "siblings", "cpu family", "model",
                 "stepping", "microcode", "bogomips", "address sizes"):
            add_observation(substrate, "cpu_property", k, v)
        if k == "flags":
            flags = v.split()
            add_observation(substrate, "cpu_features", "flag_count",
                            len(flags),
                            f"e.g. {' '.join(flags[:8])}")
            # Highlight a few the substrate's compilers Mt would know.
            for flag in ("avx", "avx2", "avx512f", "sse4_2",
                         "aes", "fma", "f16c", "popcnt", "bmi2"):
                if flag in flags:
                    add_observation(substrate,
                                    "cpu_feature_present",
                                    flag, True)


def observe_memory_layout(substrate) -> None:
    maps = Path("/proc/self/maps")
    if not maps.exists():
        return
    lines = maps.read_text().splitlines()
    add_observation(substrate, "memory_layout",
                    "mapping_count", len(lines))
    so_mappings = [l for l in lines if "_native" in l and ".so" in l]
    if so_mappings:
        for m in so_mappings[:3]:
            add_observation(substrate, "memory_mapping",
                            "substrate_so", m.strip())


def observe_timing(substrate) -> None:
    """Time some substrate operations on the freshly-built substrate."""
    s_test = _native.Substrate()
    # Cost of producing a node.
    start = time.perf_counter()
    for i in range(1000):
        s_test.add_node("Concept", {"i": i})
    elapsed = time.perf_counter() - start
    add_observation(substrate, "operation_timing",
                    "add_node_1000x_seconds",
                    f"{elapsed:.6f}",
                    f"{1000 / elapsed:,.0f} nodes/sec")
    # Cost of attr read.
    nid = s_test.add_node("Concept", {"k": "v"})
    start = time.perf_counter()
    for i in range(10000):
        _ = s_test.node(nid)["attrs"]
    elapsed = time.perf_counter() - start
    add_observation(substrate, "operation_timing",
                    "attr_read_10000x_seconds",
                    f"{elapsed:.6f}",
                    f"{10000 / elapsed:,.0f} reads/sec")


def main():
    s = fresh_substrate()
    print("=" * 72)
    print("GIVING THE SUBSTRATE EYES FOR ITS OWN RUNNER")
    print("=" * 72)
    print()
    # Install the vocabulary needed to reason about observations.
    print("Installing computer_architecture Mt (102 concepts ready for")
    print("the substrate to apply to observations)...")
    install_computer_arch(s)
    print()
    print("Injecting observations as RunnerObservation graph nodes:")
    print()
    observe_binary(s)
    observe_cpu(s)
    observe_memory_layout(s)
    observe_timing(s)

    # Show what the substrate now sees.
    obs = list(s.nodes("RunnerObservation"))
    print(f"  → {len(obs)} observations injected")
    print()
    # Group by category for the substrate's view of itself.
    by_category: dict[str, list] = {}
    for n in obs:
        attrs = s.node(n)["attrs"]
        cat = str(attrs.get("category", ""))
        by_category.setdefault(cat, []).append(attrs)
    for cat, entries in sorted(by_category.items()):
        print(f"  [{cat}] ({len(entries)})")
        for e in entries[:6]:
            detail = f" — {e['detail']}" if e.get("detail") else ""
            print(f"    {e.get('key', ''):<24} {e.get('value', '')}{detail}")
        if len(entries) > 6:
            print(f"    ... ({len(entries) - 6} more)")
    print()
    print("=" * 72)
    print("WHAT THIS GIVES THE SUBSTRATE")
    print("=" * 72)
    print()
    print(f"  · {len(obs)} graph-resident observations of its own runner")
    print("  · Each observation typed RunnerObservation with a category")
    print("    that the substrate's computer_architecture Mt can apply")
    print("    its vocabulary to (instruction_set_architecture,")
    print("    cpu_feature_present, code_segment_size, etc.)")
    print("  · No interpretation imposed — the substrate's existing")
    print("    drives + cortices decide what's meaningful")
    print()
    print("The substrate now has eyes for its runner. Whether it")
    print("notices inadequacy + decides to design a new one is its own")
    print("decision, not mine.")


if __name__ == "__main__":
    main()
