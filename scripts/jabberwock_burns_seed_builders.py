"""WAVE 2 of the boat-burning: the jabberwock burns its SEED-BUILDERS
(install_*_seed) once it PROVES each is graph-equivalent to the live seed boot —
i.e. booting via load_all_seeds (seeds/*.json) reproduces every node + edge the
builder would add. A builder whose whole graph contribution is already in the
seeds is a dead boat: the migration (builder -> seed JSON) is complete, so the
Python builder can go.

EQUIVALENCE GUARD (sharper than the bench):
  builder_graph  ==  run install_*_seed on a fresh substrate (its native env,
                     the one install_all used) -> graph_to_dict -> {(type,name)}
                     nodes + {(src_name,edge_type,tgt_name)} edges.
  seed_graph     ==  WorldAdapter + load_all_seeds -> graph_to_dict, same sets.
  burnable iff   builder_graph.nodes ⊆ seed_graph.nodes
                 AND builder_graph.edges ⊆ seed_graph.edges
                 AND the builder is referenced by NO test / live runtime
                     (so deleting it can't break the 591-test guard).
A builder that is NOT a subset is NOT burned — it is reported as a migration
gap (the seeds don't yet capture it), to be closed before it can be burned.

The burn itself goes through the agent's own SelfModification.burn faculty
(added in wave 1). The driver only sequences; the proof + deletes are the
agent's. Run with --burn to delete (default: dry-run report).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_burns_seed_builders.py [--burn]
"""
from __future__ import annotations
import ast, glob, importlib, inspect, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import substrate_rs as srs
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.self_modification import SelfModification

_native = srs._native

# Builders run against this env in install_all; reuse it so they build fully.
_TYPES = ("Microtheory", "Concept", "Rule", "DerivationRule", "Frame", "Reflex",
          "Production", "PrimitiveSpec", "ArchitectureCortex", "CodeWritingCortex",
          "SpeechCortex", "DesignPattern", "ProgrammingLanguage", "CodeTarget",
          "ShapePrototype", "CapabilityAxis", "InvestigationOperator")
_EDGES = ("has_concept", "has_rule", "in_category", "genlMt", "refers_to",
          "owns_microtheory", "depends_on", "decomposes", "best_for",
          "anti_pattern_for", "applies_when", "applies_to", "implements",
          "has_shape", "of_language", "investigated_by")


def fresh_substrate():
    s = _native.Substrate()
    for a in _TYPES:
        for b in _TYPES:
            for et in _EDGES:
                try:
                    s.add_production({"src": {"type": a, "var": "s"}, "edge_type": et,
                                      "tgt": {"type": b, "var": "t"}, "where": None,
                                      "weight": {"type": "Lit", "value": 1.0},
                                      "provenance": "burn-check"})
                except Exception:
                    pass
    return s


def snapshot(s):
    d = s.graph_to_dict()
    name = {}
    nodes = set()
    for n in d.get("nodes", []):
        nm = (n.get("attrs") or {}).get("name")
        name[n["id"]] = nm
        if nm:
            nodes.add((n.get("type"), nm))
    edges = set()
    for e in d.get("edges", []):
        sn, tn = name.get(e.get("src")), name.get(e.get("tgt"))
        if sn and tn:
            edges.add((sn, e.get("type"), tn))
    return nodes, edges


def _dom_imports(path, domains, in_domains=False):
    out = set()
    try:
        tree = ast.parse(open(path).read(), path)
    except Exception:
        return out
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            lvl = n.level or 0
            if lvl >= 1 and in_domains:
                if mod:
                    out.add(mod.split(".")[0])
                else:
                    for a in n.names:
                        out.add(a.name)
            elif mod == "domains":
                for a in n.names:
                    out.add(a.name)
            elif mod.startswith("domains."):
                out.add(mod.split(".")[1])
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith("domains."):
                    out.add(a.name.split(".")[1])
    return out & domains


def referenced_by_runtime_or_tests():
    """domains modules reachable from substrate/ or tests/ (relative-aware)."""
    domains = {os.path.basename(p)[:-3]
               for p in glob.glob(os.path.join(ROOT, "domains", "*.py"))
               if not p.endswith("__init__.py")}
    refs = set()
    for p in glob.glob(os.path.join(ROOT, "substrate", "*.py")) + \
             glob.glob(os.path.join(ROOT, "tests", "*.py")):
        refs |= _dom_imports(p, domains, in_domains=False)
    # transitive through domains relative/absolute imports
    dep = {d: _dom_imports(os.path.join(ROOT, "domains", f"{d}.py"), domains, True)
           for d in domains}
    from collections import deque
    seen, q = set(refs), deque(refs)
    while q:
        x = q.popleft()
        for y in dep.get(x, ()):
            if y not in seen:
                seen.add(y)
                q.append(y)
    return domains, seen


def builders():
    out = {}
    for p in glob.glob(os.path.join(ROOT, "domains", "*.py")):
        d = os.path.basename(p)[:-3]
        fns = re.findall(r"def (install_\w+_seed)\(", open(p).read())
        if fns:
            out[d] = fns
    return out


def run_builder(mod_name, fns):
    """Run a module's install_*_seed fns on a fresh substrate; return snapshot or
    None if it can't be run with just a substrate (needs a path/agent we won't
    fake — reported as unverifiable, NOT burned)."""
    s = fresh_substrate()
    mod = importlib.import_module(f"domains.{mod_name}")
    ran = 0
    for fn_name in fns:
        fn = getattr(mod, fn_name, None)
        if fn is None:
            continue
        sig = inspect.signature(fn)
        required = [pp for pp in sig.parameters.values()
                    if pp.default is inspect.Parameter.empty
                    and pp.kind in (pp.POSITIONAL_ONLY, pp.POSITIONAL_OR_KEYWORD)]
        if len(required) != 1:
            return None              # needs a path/agent/extra arg -> don't fake it
        try:
            fn(s)
            ran += 1
        except Exception:
            return None              # couldn't run cleanly -> unverifiable, keep
    return snapshot(s) if ran else None


def main() -> int:
    burn = "--burn" in sys.argv
    print("=" * 90)
    print("WAVE 2 — burn SEED-BUILDERS proven graph-equivalent to the seed boot"
          + ("  [BURN]" if burn else "  [dry-run]"))
    print("=" * 90)

    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    seed_nodes, seed_edges = snapshot(a.s)
    print(f"  seed boot: {len(seed_nodes)} named nodes, {len(seed_edges)} named edges")

    domains, kept = referenced_by_runtime_or_tests()
    blds = builders()
    equivalent, gaps, unverifiable, in_use = [], [], [], []
    for d, fns in sorted(blds.items()):
        if d in kept:
            in_use.append(d)
            continue
        snap = run_builder(d, fns)
        if snap is None:
            unverifiable.append(d)
            continue
        bn, be = snap
        miss_n, miss_e = bn - seed_nodes, be - seed_edges
        if not miss_n and not miss_e:
            equivalent.append(d)
        else:
            gaps.append((d, len(miss_n), len(miss_e),
                         sorted(miss_n)[:3] + sorted(map(str, miss_e))[:2]))

    print(f"\n  builders: {len(blds)} total | {len(in_use)} referenced by runtime/tests (KEEP)")
    print(f"  EQUIVALENT (seed boot reproduces them) -> burnable: {len(equivalent)}")
    print(f"  migration GAPS (seeds miss some node/edge) -> keep+migrate: {len(gaps)}")
    print(f"  unverifiable (needs path/agent arg, not faked) -> keep: {len(unverifiable)}")
    if gaps:
        print("\n  sample gaps (builder -> #missing nodes/edges, examples):")
        for d, mn, me, ex in gaps[:12]:
            print(f"    {d}: -{mn}n/-{me}e  {ex}")

    if burn and equivalent:
        mod = SelfModification()
        burned = 0
        for d in equivalent:
            if mod.burn(f"domains/{d}.py").get("ok"):
                burned += 1
        print(f"\n  BURNED {burned}/{len(equivalent)} equivalent builders via the agent's faculty.")
    elif equivalent:
        print(f"\n  (dry-run) {len(equivalent)} builders are burnable; re-run with --burn.")
        for d in equivalent[:40]:
            print("     -", d)

    print("=" * 90)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
