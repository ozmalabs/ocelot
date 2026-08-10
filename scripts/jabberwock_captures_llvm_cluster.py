"""Capture the LLVM compiler cluster — 3 dep-chained path-loader builders — to
seed, so load_one_seed reproduces them and they can be burned.

  llvm_pass_compiler.install_passes_seed(s, seeds/llvm_passes.json)
      -> RuleFamily nodes
  compiler_theory_seed.install_compiler_theory_seed(s, seeds/compiler_theory.json)
      -> OptimizationConcept + Category, wired to RuleFamily by fingerprint
  optimization_pipelines_seed.install_pipelines_seed(s, seeds/optimization_pipelines.json)
      -> pipeline nodes

Run them IN ORDER on ONE fresh substrate (so compiler_theory's fingerprint
wiring resolves against passes' RuleFamily). After EACH builder, diff the NEW
nodes + NEW edges and write them into THAT builder's seed JSON as extra_nodes +
relations (edges by name; the fingerprint wiring is already resolved into
concrete instantiates relations). load_one_seed (idempotent, nameless-aware,
nested-attr) then replays them. No load_all_seeds here (avoids the capture-on-
modified-seed pollution trap); the builders set up their own grammar.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_captures_llvm_cluster.py
"""
from __future__ import annotations
import importlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import scripts.jabberwock_burns_seed_builders as B

# (module, fn, seed_id) in dependency order. seed_id == JSON stem == path.
SPECS = [
    ("llvm_pass_compiler", "install_passes_seed", "llvm_passes"),
    ("compiler_theory_seed", "install_compiler_theory_seed", "compiler_theory"),
    ("optimization_pipelines_seed", "install_pipelines_seed", "optimization_pipelines"),
]


def _untuple(v):
    if isinstance(v, dict) and set(v) == {"__tuple__"}:
        return [_untuple(x) for x in v["__tuple__"]]
    if isinstance(v, list):
        return [_untuple(x) for x in v]
    return v


def _snap(s):
    g = s.graph_to_dict()
    nodes = {n["id"]: n for n in g.get("nodes", [])}
    edges = {(e.get("src"), e.get("type"), e.get("tgt")) for e in g.get("edges", [])}
    return nodes, edges


def _init():
    s = B.fresh_substrate()
    pre_nodes, pre_edges = _snap(s)
    ref = {}            # GLOBAL node-id -> ref name (real OR synthetic), across builders
    syn = {}            # per-type synthetic counter
    return s, pre_nodes, pre_edges, ref, syn


def _refname(nid, node, ref, syn):
    if nid in ref:
        return ref[nid]
    nm = (node.get("attrs") or {}).get("name")
    if not nm:                      # NAMELESS (e.g. RewriteRule): mint a stable synthetic
        t = node.get("type") or "Node"
        syn[t] = syn.get(t, 0) + 1
        nm = f"__{t}_{syn[t]}"
    ref[nid] = nm
    return nm


def main() -> int:
    s, pre_nodes, pre_edges, ref, syn = _init()
    for mod, fn_name, seed_id in SPECS:
        path = os.path.join(ROOT, "seeds", f"{seed_id}.json")
        fn = getattr(importlib.import_module(f"domains.{mod}"), fn_name)
        fn(s, path)
        nodes, edges = _snap(s)

        new_ids = [nid for nid in nodes if nid not in pre_nodes]
        extra = []
        for nid in new_ids:
            n = nodes[nid]
            rname = _refname(nid, n, ref, syn)       # ensures a (synthetic) name exists
            attrs = {"name": rname}
            for k, v in (n.get("attrs") or {}).items():
                u = _untuple(v)
                if isinstance(u, (str, int, float, bool, list)):
                    attrs[k] = u
            attrs.setdefault("name", rname)
            extra.append({"type": n.get("type"), **attrs})

        rels, unresolved = [], 0
        for (src, et, tgt) in (edges - pre_edges):
            sn = ref.get(src) or (_refname(src, nodes[src], ref, syn) if src in nodes else None)
            tn = ref.get(tgt) or (_refname(tgt, nodes[tgt], ref, syn) if tgt in nodes else None)
            if sn and tn:
                rels.append({"src": sn, "edge": et, "tgt": tn})
            else:
                unresolved += 1

        seed = json.load(open(path))
        seed["extra_nodes"] = extra
        seed["relations"] = rels
        json.dump(seed, open(path, "w"), indent=1, ensure_ascii=False)

        types = {}
        for en in extra:
            types[en["type"]] = types.get(en["type"], 0) + 1
        print(f"  {seed_id}: extra_nodes={len(extra)} {types} | relations={len(rels)} "
              f"| unresolved_edges(nameless)={unresolved}")
        pre_nodes, pre_edges = nodes, edges
    print("Captured the LLVM cluster. Verify load_one_seed reproduces the tests, then swap + burn.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
