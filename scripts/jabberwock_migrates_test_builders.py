"""Migrate the TEST-COUPLED (in_use) seed-builders so they become burnable.

Wave-3 failed because the builders HARDCODE structure (esp. genlMt parents) in
Python, absent from the seed JSON, so load_one_seed didn't reproduce what the
tests assert. Fix: run each builder WITH productions + all-Mt stubs (so its
hardcoded genlMt/cross-refs actually form), DIFF against load_one_seed on the
same substrate, and CAPTURE the gap (extra_nodes + relations) into the seed JSON.
After that load_one_seed reproduces the builder exactly -> the install_X_seed(s)
call sites can be swapped to load_one_seed(s, "X") transparently -> burn.

Phase 1 (this script, default): capture each migratable in-use builder's gap +
VERIFY builder == load_one_seed on a stub substrate. Reports swappable count.
--apply also writes the captures (always needed before the swap/burn step).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_migrates_test_builders.py [--apply]
"""
from __future__ import annotations
import glob, importlib, inspect, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import scripts.jabberwock_burns_seed_builders as B
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds, load_one_seed
from domains.self_migration import Migrator

MT_NAMES = []


def stub_sub(target):
    s = B.fresh_substrate()
    for nm in MT_NAMES:
        if nm != target:
            s.add_node("Microtheory", {"name": nm})
    return s


def snap(s):
    d = s.graph_to_dict(); nm = {}; nodes = {}
    for n in d.get("nodes", []):
        x = (n.get("attrs") or {}).get("name"); nm[n["id"]] = x
        if x:
            nodes[(n.get("type"), x)] = dict(n.get("attrs") or {})
    edges = set()
    for e in d.get("edges", []):
        a, b = nm.get(e.get("src")), nm.get(e.get("tgt"))
        if a and b:
            edges.add((a, e.get("type"), b))
    return nodes, edges


def run_builder(mod, fns, target):
    s = stub_sub(target)
    m = importlib.import_module(f"domains.{mod}")
    for fn in fns:
        f = getattr(m, fn, None)
        if f is None:
            continue
        req = [p for p in inspect.signature(f).parameters.values()
               if p.default is inspect.Parameter.empty
               and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        if len(req) != 1:
            return None
        try:
            f(s)
        except Exception:
            return None
    return snap(s)


def capture(mod, miss_n, miss_e):
    extra = []
    for (t, nm), attrs in sorted(miss_n.items()):
        en = {"type": t, "name": nm}
        for k, v in attrs.items():
            if k != "name" and isinstance(v, (str, int, float, bool, list)):
                en[k] = v
        extra.append(en)
    rels = [{"src": s_, "edge": et, "tgt": t_} for (s_, et, t_) in sorted(miss_e)]
    path = os.path.join(ROOT, "seeds", f"{mod}.json")
    seed = json.load(open(path)) if os.path.exists(path) else {
        "id": mod, "version": "1.0.0", "depends_on": [], "description": f"captured from domains/{mod}.py"}
    if extra:
        seed.setdefault("extra_nodes", [])
        have = {(e["type"], e["name"]) for e in seed["extra_nodes"]}
        seed["extra_nodes"] += [e for e in extra if (e["type"], e["name"]) not in have]
    if rels:
        seed.setdefault("relations", [])
        have = {(r["src"], r["edge"], r["tgt"]) for r in seed["relations"]}
        seed["relations"] += [r for r in rels if (r["src"], r["edge"], r["tgt"]) not in have]
    json.dump(seed, open(path, "w"), indent=1, ensure_ascii=False)


def main() -> int:
    apply = "--apply" in sys.argv
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    global MT_NAMES
    MT_NAMES = sorted(set(a.s.node(n)["attrs"].get("name") for n in a.s.nodes("Microtheory")
                          if a.s.node(n)["attrs"].get("name")))
    mig = Migrator()
    domains, kept = mig._referenced(roots_only=True)
    blds = B.builders()
    # in-use builders that are SINGLE-fn + never called with custom args (swappable)
    files = [os.path.join(ROOT, "domains", "code_writing_cortex.py")] + glob.glob(os.path.join(ROOT, "tests", "*.py"))
    candidates = []
    for d, fns in sorted(blds.items()):
        if d not in kept or len(fns) != 1:
            continue
        if not os.path.exists(os.path.join(ROOT, "seeds", f"{d}.json")):
            continue                      # not an Mt-from-seed builder (e.g. a helper)
        fn = fns[0]
        multiarg = any(re.search(re.escape(fn) + r"\(\s*[^,()]+,\s*", open(p).read()) for p in files if os.path.exists(p))
        if multiarg:
            continue
        candidates.append((d, fn))

    print("=" * 80)
    print(f"MIGRATE TEST-COUPLED BUILDERS — {len(candidates)} single-arg in-use candidates"
          + ("  [APPLY capture]" if apply else "  [dry-run]"))
    print("=" * 80)
    swappable, failed = [], []
    for d, fn in candidates:
        snap_b = run_builder(d, [fn], d)
        if snap_b is None:
            failed.append((d, "builder unrunnable"))
            continue
        bn, be = snap_b
        s2 = stub_sub(d); load_one_seed(s2, d); ln, le = snap(s2)
        miss_n = {k: v for k, v in bn.items() if k not in ln}
        miss_e = [e for e in be if e not in le]
        if apply and (miss_n or miss_e):
            capture(d, miss_n, miss_e)
            s3 = stub_sub(d); load_one_seed(s3, d); ln, le = snap(s3)
            miss_n = {k: v for k, v in bn.items() if k not in ln}
            miss_e = [e for e in be if e not in le]
        if not miss_n and not miss_e:
            swappable.append(d)
        else:
            failed.append((d, f"-{len(miss_n)}n/-{len(miss_e)}e {sorted(miss_n)[:2]}{sorted(map(str,miss_e))[:2]}"))
    print(f"  swappable (builder == load_one_seed{' after capture' if apply else ''}): {len(swappable)}/{len(candidates)}")
    for d in swappable:
        print("   ok ", d)
    if failed:
        print(f"  NOT swappable: {len(failed)}")
        for d, why in failed:
            print("   --", d, why)
    print("=" * 80)
    if apply:
        print("  captures written. Next: swap call sites (migrate_builders_to_load_one_seed.py --apply),")
        print("  run the builder tests + bench, then burn via the agent's faculty.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
