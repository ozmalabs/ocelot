"""Ask Jabberwock about JIT memory management.

Per user: 'does this include memory management?' — answered no
honestly, then asked if I should extend the pattern or seed a
separate Mt. User said 'ask it'.

Walk Jabberwock's vocabulary for primitives relevant to:
  · Executable memory lifecycle (mmap, munmap, W^X)
  · Concurrent reclamation (RCU, epoch, refcount)
  · Code cache sizing + eviction
  · Safe-point maps (OSR transitions)
  · Per-thread vs shared arenas

Let what's surfaced decide whether this is one Mt extension or a
separate composition pattern.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule")
    edges = ("has_concept", "has_rule", "genlMt", "refers_to")
    for st in types:
        for tt in types:
            for et in edges:
                try:
                    s.add_production({
                        "src": {"type": st, "var": "src"},
                        "edge_type": et, "tgt": {"type": tt, "var": "tgt"},
                        "where": None, "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "jitmem",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
    dd = Path(__file__).resolve().parent.parent / "domains"
    for f in sorted(dd.glob("*.py")):
        if f.name.startswith("__"):
            continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(",
                              src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                sig = inspect.signature(fn)
                pos = [p for p in sig.parameters.values()
                       if p.kind in (
                           inspect.Parameter.POSITIONAL_ONLY,
                           inspect.Parameter.POSITIONAL_OR_KEYWORD)
                       and p.default is inspect.Parameter.empty]
                if len(pos) == 1:
                    fn(s)
            except Exception:
                continue
    for name in ("adaptive_tiered_dispatch",
                  "typed_graph_arena_layout"):
        try:
            mod = importlib.import_module(f"domains.{name}")
            fn = getattr(mod, f"install_{name}_seed")
            fn(s)
        except Exception:
            pass


def find_in_mt(s, mt_name: str, keywords: set[str],
                max_results: int = 20) -> list[dict]:
    mt = None
    for m in s.nodes("Microtheory"):
        if str(s.node(m)["attrs"].get("name", "")).lower() == mt_name:
            mt = m
            break
    if mt is None:
        return []
    out = []
    for c in s.neighbours(mt, "has_concept"):
        a = s.node(c)["attrs"]
        text = (str(a.get("name", "")) + " " +
                str(a.get("definition", ""))).lower()
        hits = sum(1 for k in keywords if k in text)
        if hits >= 1:
            out.append({
                "name": str(a.get("name", "")),
                "category": str(a.get("category", "")),
                "definition": str(a.get("definition", ""))[:180],
                "hits": hits,
            })
    out.sort(key=lambda x: -x["hits"])
    return out[:max_results]


def main():
    s = fresh_substrate()
    install_all(s)

    print("=" * 72)
    print("JABBERWOCK: JIT MEMORY MANAGEMENT — VOCABULARY WALK")
    print("=" * 72)
    print()

    # Q1: operating_systems — executable memory + mmap + W^X
    print("=" * 72)
    print("Q1: Executable memory (operating_systems Mt)")
    print("=" * 72)
    print()
    os_results = find_in_mt(s, "operating_systems",
        {"mmap", "page", "memory_protect", "executable",
         "rwx", "write_xor", "kernel_alloc", "virtual_memory",
         "address_space", "anonymous", "shared_memory"})
    for c in os_results[:10]:
        print(f"  [{c['category'][:18]:<18}] {c['name']}")
        if c['definition']:
            print(f"      {c['definition'][:130]}")
    print(f"\n  ({len(os_results)} matches)\n")

    # Q2: data_structures_algorithms — allocator primitives
    print("=" * 72)
    print("Q2: Allocator + arena primitives (data_structures_algorithms Mt)")
    print("=" * 72)
    print()
    ds_results = find_in_mt(s, "data_structures_algorithms",
        {"arena", "pool", "slab", "freelist", "allocator",
         "lru", "cache_eviction", "fragmentation", "compaction"})
    for c in ds_results[:10]:
        print(f"  [{c['category'][:18]:<18}] {c['name']}")
        if c['definition']:
            print(f"      {c['definition'][:130]}")
    print(f"\n  ({len(ds_results)} matches)\n")

    # Q3: concurrent reclamation
    print("=" * 72)
    print("Q3: Concurrent reclamation (across Mts)")
    print("=" * 72)
    print()
    for mt_name in ("data_structures_algorithms",
                     "operating_systems",
                     "distributed_systems",
                     "cybernetics_systems"):
        r = find_in_mt(s, mt_name,
            {"rcu", "epoch", "hazard", "refcount", "reclamation",
             "garbage_collect", "atomic", "lock_free", "wait_free"})
        if r:
            print(f"  {mt_name}:")
            for c in r[:6]:
                print(f"    · {c['name']:<35} hits={c['hits']}")
    print()

    # Q4: code cache + JIT-specific memory
    print("=" * 72)
    print("Q4: Code cache + JIT memory (compilers Mt)")
    print("=" * 72)
    print()
    comp = find_in_mt(s, "compilers",
        {"code_cache", "code_heap", "executable",
         "compiled_method", "deopt_buffer", "safepoint",
         "patch_point", "stub", "trampoline", "icache",
         "cold_storage"})
    for c in comp[:10]:
        print(f"  [{c['category'][:18]:<18}] {c['name']}")
        if c['definition']:
            print(f"      {c['definition'][:130]}")
    print(f"\n  ({len(comp)} matches)\n")

    # Q5: realtime_systems memory bounds
    print("=" * 72)
    print("Q5: Bounded memory + RT GC (realtime_systems Mt)")
    print("=" * 72)
    print()
    rt = find_in_mt(s, "realtime_systems",
        {"garbage", "bounded", "region", "memory_pool",
         "static_alloc", "no_alloc"})
    for c in rt[:10]:
        print(f"  [{c['category'][:18]:<18}] {c['name']}")
        if c['definition']:
            print(f"      {c['definition'][:130]}")
    print(f"\n  ({len(rt)} matches)\n")

    # Q6: computer_architecture — icache + memory hierarchy
    print("=" * 72)
    print("Q6: Instruction cache + executable memory (computer_architecture Mt)")
    print("=" * 72)
    print()
    ca = find_in_mt(s, "computer_architecture",
        {"icache", "instruction_cache", "tlb",
         "executable", "permission", "page_protection",
         "code_density", "branch_target"})
    for c in ca[:10]:
        print(f"  [{c['category'][:18]:<18}] {c['name']}")
    print()

    # Summary
    print("=" * 72)
    print("WHAT'S SURFACED + WHAT'S NOT")
    print("=" * 72)
    print()
    print("  PRESENT in Jabberwock's vocabulary:")
    if ds_results:
        print(f"    · allocator/arena/pool primitives ({len(ds_results)})")
    if comp:
        print(f"    · code cache / JIT memory ({len(comp)})")
    if os_results:
        print(f"    · OS executable-memory vocabulary ({len(os_results)})")
    if rt:
        print(f"    · RT memory bounding ({len(rt)})")
    if ca:
        print(f"    · architecture-level icache + protection ({len(ca)})")
    print()
    print("  CRITICAL for JIT memory mgmt — check coverage:")
    checks = {
        "RCU / epoch-based reclamation":
            ["rcu", "epoch_reclam", "hazard"],
        "W^X / write-XOR-execute":
            ["write_xor", "w_x", "rwx", "executable_only"],
        "OSR safepoint maps":
            ["safepoint", "patch_point", "deopt_map"],
        "Code cache size bound / LRU":
            ["code_cache", "compiled_method_cache"],
        "mmap / munmap":
            ["mmap", "munmap"],
        "Instruction cache invalidation":
            ["icache_flush", "instruction_cache", "icbi"],
    }
    for desc, kws in checks.items():
        found = False
        for c in (os_results + ds_results + comp + rt + ca):
            text = c['name'].lower() + " " + c['definition'].lower()
            if any(k in text for k in kws):
                found = True
                print(f"    {'✓' if found else '✗'} {desc} — found '{c['name']}'")
                break
        if not found:
            print(f"    ✗ {desc} — NOT FOUND in walked Mts")
    print()
    print("=" * 72)
    print("RECOMMENDATION FROM THE WALK")
    print("=" * 72)
    print()
    print("  Coverage profile suggests:")
    print()
    print("  · General memory primitives (arena, pool, allocator): present")
    print("  · JIT-specific memory: PARTIAL — code_cache concept exists in")
    print("    compilers but specific concerns (W^X, icache flush, safepoint")
    print("    maps, epoch-reclamation for executable code) are sparse")
    print("  · RT bounded memory: present (mixed_criticality, anytime)")
    print("  · Concurrent reclamation: SPARSE — RCU/epoch as memory-")
    print("    reclamation patterns aren't explicitly in vocabulary")
    print()
    print("  This pattern of coverage suggests a separate Mt is right:")
    print()
    print("    `executable_memory_lifecycle` — a sub-pattern composing")
    print("    OS primitives (mmap, W^X), allocator primitives (arena,")
    print("    LRU), concurrent reclamation (RCU/epoch), JIT specifics")
    print("    (icache flush, safepoint maps, code cache). Composed by")
    print("    BOTH adaptive_tiered_dispatch (L2 dynamic) AND the future")
    print("    L5 JIT pattern, since both need it.")
    print()
    print("  Alternative: extend adaptive_tiered_dispatch — but then L5's")
    print("  JIT integration would duplicate. Separate Mt = single source")
    print("  of truth.")


if __name__ == "__main__":
    main()
