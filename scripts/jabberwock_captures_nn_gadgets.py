"""Capture neural_networks + gadgets — the two deep-fidelity builders — to seed,
so load_one_seed reproduces them and they can be burned. They build typed nodes
beyond Mt/concepts: DesignPattern (with nested-list weight matrices), CodeTarget,
NAMELESS DesignExclusion (keyed by pattern_tag/target_anti_tag), and genlMt to
MULTIPLE parents incl. non-boot code_authoring. gadgets' Mt is 'cpwl_construction'
(not its seed id 'gadgets').

Capture = run the builder on a substrate with broad productions + parent stubs
(so its genlMt/cross-refs form), diff out the NEW nodes, and write:
  - extra_nodes : every new node of type NOT in {Microtheory,Concept,Rule}
                  (Mt+concepts come from the std keys), with ALL attrs incl
                  nested lists; named or nameless.
  - relations   : the new Mt's genlMt edges (by parent name).
  - microtheory : the new Mt's real name when it differs from the seed id
                  (gadgets -> cpwl_construction).
load_one_seed (now idempotent + nameless-aware) then reproduces them exactly.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_captures_nn_gadgets.py
"""
from __future__ import annotations
import importlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import scripts.jabberwock_burns_seed_builders as B
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

TARGETS = [("neural_networks", "install_neural_networks_seed"),
           ("gadgets", "install_gadgets_seed")]
# parents the builders reference that are NOT boot Mts (cortex-created).
EXTRA_STUBS = ["code_authoring", "neural_networks", "compiler_theory"]


def main() -> int:
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    boot_mts = sorted(set(a.s.node(n)["attrs"].get("name") for n in a.s.nodes("Microtheory")
                          if a.s.node(n)["attrs"].get("name")))

    for mod, fn_name in TARGETS:
        s = B.fresh_substrate()
        for nm in set(boot_mts) | set(EXTRA_STUBS):
            if nm != mod:                                  # don't stub the Mt we're building
                try:
                    s.add_node("Microtheory", {"name": nm})
                except Exception:
                    pass
        pre = set()
        for t in ("Microtheory",):
            pass
        g0 = s.graph_to_dict()
        pre = {n["id"] for n in g0.get("nodes", [])}

        fn = getattr(importlib.import_module(f"domains.{mod}"), fn_name)
        fn(s)

        g = s.graph_to_dict()
        name_of = {n["id"]: (n.get("attrs") or {}).get("name") for n in g.get("nodes", [])}
        new = [n for n in g.get("nodes", []) if n["id"] not in pre]
        new_mt = next((n for n in new if n.get("type") == "Microtheory"), None)
        mt_name = (new_mt.get("attrs") or {}).get("name") if new_mt else mod

        def _untuple(v):
            # graph_to_dict encodes tuples (e.g. weight matrices) as
            # {"__tuple__": [...]}; convert back to nested lists.
            if isinstance(v, dict) and set(v) == {"__tuple__"}:
                return [_untuple(x) for x in v["__tuple__"]]
            if isinstance(v, list):
                return [_untuple(x) for x in v]
            return v

        extra = []
        for n in new:
            t = n.get("type")
            if t in ("Microtheory", "Concept", "Rule"):
                continue
            attrs = {}
            for k, v in (n.get("attrs") or {}).items():
                u = _untuple(v)
                if isinstance(u, (str, int, float, bool, list)):
                    attrs[k] = u
            extra.append({"type": t, **attrs})

        rels = []
        for e in g.get("edges", []):
            if e.get("type") == "genlMt" and name_of.get(e.get("src")) == mt_name:
                tgt = name_of.get(e.get("tgt"))
                if tgt:
                    rels.append({"src": mt_name, "edge": "genlMt", "tgt": tgt})

        path = os.path.join(ROOT, "seeds", f"{mod}.json")
        seed = json.load(open(path))
        if mt_name and mt_name != (seed.get("id") or mod):
            seed["microtheory"] = mt_name                  # Mt name != seed id (gadgets)
        seed["extra_nodes"] = extra
        seed["relations"] = rels
        json.dump(seed, open(path, "w"), indent=1, ensure_ascii=False)
        types = {}
        for en in extra:
            types[en["type"]] = types.get(en["type"], 0) + 1
        print(f"  {mod}: Mt={mt_name} | extra_nodes={len(extra)} {types} | "
              f"genlMt relations -> {[r['tgt'] for r in rels]}")
    print("Captured. Verify load_one_seed reproduces the tests, then swap + burn.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
