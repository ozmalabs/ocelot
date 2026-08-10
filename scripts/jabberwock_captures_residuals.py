"""WAVE 2c — CAPTURE-TO-SEED the 4 residual gap-builders, then they become
burnable. These builders COMPUTE structure beyond declarative Mt/concepts/rules
(built_from / depends_on concept-relations, SourceEvent nodes, cross-seed genlMt)
that the generic loader can't reproduce from the existing JSON. So we CAPTURE the
gap (the exact nodes + edges the seed boot is missing) into the seed JSON as:
  extra_nodes : [{type, name, ...attrs}]   - typed nodes beyond Mt/concepts/rules
  relations   : [{src, edge, tgt}]         - name-based edges (resolved at boot)
The loader (boot_all) materialises both, so load_all_seeds then reproduces the
builder exactly -> equivalence -> the builder can be burned (separately).

The capture is the GAP only (builder_graph - seed_boot_graph), computed by
running the builder in its native env and diffing against load_all_seeds. Writes
each seed JSON in place (creates one for a builder that had none).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_captures_residuals.py
"""
from __future__ import annotations
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import scripts.jabberwock_burns_seed_builders as B

RESIDUALS = ["function_shape", "math_foundations", "invariant_representation",
             "communication_concepts"]


def snapshot_full(s):
    """nodes: {(type,name): attrs}, edges: {(src_name,edge,tgt_name)}."""
    d = s.graph_to_dict()
    name, nodes = {}, {}
    for n in d.get("nodes", []):
        nm = (n.get("attrs") or {}).get("name")
        name[n["id"]] = nm
        if nm:
            nodes[(n.get("type"), nm)] = dict(n.get("attrs") or {})
    edges = set()
    for e in d.get("edges", []):
        sn, tn = name.get(e.get("src")), name.get(e.get("tgt"))
        if sn and tn:
            edges.add((sn, e.get("type"), tn))
    return nodes, edges


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    seed_nodes, seed_edges = snapshot_full(a.s)
    print("=" * 88)
    print("WAVE 2c — capture the 4 residual builders' computed structure to seed")
    print("=" * 88)

    blds = B.builders()
    for d in RESIDUALS:
        fns = blds.get(d)
        if not fns:
            print(f"  {d}: no install_*_seed found, skip")
            continue
        snap = B.run_builder(d, fns)
        if snap is None:
            # run_builder returns only (nodes,edges) sets; rerun for full attrs
            pass
        # full attrs run
        s = B.fresh_substrate()
        import importlib
        mod = importlib.import_module(f"domains.{d}")
        import inspect
        ok = True
        for fn_name in fns:
            fn = getattr(mod, fn_name)
            req = [pp for pp in inspect.signature(fn).parameters.values()
                   if pp.default is inspect.Parameter.empty
                   and pp.kind in (pp.POSITIONAL_ONLY, pp.POSITIONAL_OR_KEYWORD)]
            if len(req) != 1:
                ok = False
                break
            try:
                fn(s)
            except Exception as e:
                print(f"  {d}: builder raised {type(e).__name__}: {e}; skip")
                ok = False
                break
        if not ok:
            continue
        bn, be = snapshot_full(s)
        miss_n = {k: v for k, v in bn.items() if k not in seed_nodes}
        miss_e = [e for e in be if e not in seed_edges]
        # extra_nodes: the missing typed nodes (carry scalar/list attrs)
        extra_nodes = []
        for (t, nm), attrs in sorted(miss_n.items()):
            en = {"type": t, "name": nm}
            for k, v in attrs.items():
                if k != "name" and isinstance(v, (str, int, float, bool, list)):
                    en[k] = v
            extra_nodes.append(en)
        relations = [{"src": s_, "edge": et, "tgt": t_} for (s_, et, t_) in sorted(miss_e)]

        path = os.path.join(ROOT, "seeds", f"{d}.json")
        if os.path.exists(path):
            seed = json.load(open(path))
        else:                                   # builder had no JSON -> create one
            seed = {"id": d, "version": "1.0.0", "depends_on": [],
                    "description": f"captured from domains/{d}.py"}
        # merge (replace these keys with the captured gap)
        if extra_nodes:
            seed["extra_nodes"] = extra_nodes
        if relations:
            seed["relations"] = relations
        json.dump(seed, open(path, "w"), indent=1, ensure_ascii=False)
        print(f"  {d}: captured {len(extra_nodes)} extra_nodes + {len(relations)} "
              f"relations -> seeds/{d}.json")
    print("=" * 88)
    print("  Re-run the equivalence diagnostic to confirm the gaps close, then burn.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
