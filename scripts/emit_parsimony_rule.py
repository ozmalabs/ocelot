"""Drive the agent's emitter to compile its OWN parsimony rule into a
fireable Rule — orchestration only.

The agent already HOLDS this rule as a concept (verified 2026-06-08):
  drive_parsimony_prune_dead = "Mts with low coverage + no recent activation
  + redundant with others are candidates for deprecation or merge."
  minimum_description_length = "... substrate analogue: substrate's parsimony drive."

This script:
  1. reads that concept's text from the substrate,
  2. extracts the trigger DIMENSIONS mechanically (the agent's named dimensions
     + a generic qualifier->comparison lexicon — no predicate invented by me),
  3. builds a declarative spec (trigger from the agent's concept; effect = mark
     for deprecation, the concept's own consequence; keep-value = the MDL/parsimony
     selector it linked),
  4. emits it via domains/rule_emitter (the mechanical compiler),
  5. VERIFIES the emitted Rule fires correctly on a synthetic graph.

The thresholds are tunables; the byte-pressure variant (resource-fit) is the
SAME template with the budget node as trigger source — deferred until a world
adapter feeds graph_bytes.
"""
from __future__ import annotations
import re, sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from substrate_rs import _native, Var, Attr, Lit, Minus, Times
from domains.rule_emitter import emit_rule_from_spec


# Generic lexicon: the agent's dimension words -> attr; qualifier -> (op, rhs).
# This reads the agent's concept; it does not invent predicates.
DIM_ATTR = {"coverage": "coverage", "activation": "activation",
            "redundant": "redundancy", "redundancy": "redundancy"}
QUALIFIER = [
    (r"low",                    ("lt",  0.2)),
    (r"no recent|no |without|not", ("lte", 0.0)),
    (r"redundant|high|>",       ("gt",  0.5)),
]


def extract_trigger_from_concept(definition: str) -> list[dict]:
    """Mechanically read the agent's concept text into trigger conjuncts."""
    text = definition.lower()
    trigger = []
    for dim_word, attr in DIM_ATTR.items():
        m = re.search(r"(\w+\s+)?" + dim_word, text)
        if not m:
            continue
        context = text[max(0, m.start() - 12): m.end()]
        op, rhs = ("eq", 0.0)
        for pat, (o, r) in QUALIFIER:
            if re.search(pat, context):
                op, rhs = o, r
                break
        cj = {"lhs": {"attr": attr, "node": "M"}, "op": op, "rhs": rhs}
        if cj not in trigger:
            trigger.append(cj)
    return trigger


def boot():
    s = _native.Substrate()
    for et in ("has_concept", "manages"):
        for a in ("Microtheory", "ParsimonyRoot"):
            for b in ("Microtheory", "ParsimonyRoot"):
                try:
                    s.add_production({"src": {"type": a, "var": "x"}, "edge_type": et,
                                      "tgt": {"type": b, "var": "y"}, "where": None,
                                      "weight": {"type": "Lit", "value": 1.0},
                                      "provenance": "o"})
                except Exception:
                    pass
    from domains.self_improvement_dynamics import install_self_improvement_dynamics_seed
    install_self_improvement_dynamics_seed(s)
    return s


def main():
    s = boot()

    # 1-2. read the agent's concept + extract its trigger.
    defn = None
    for c in s.nodes("Concept"):
        if s.node(c)["attrs"].get("name") == "drive_parsimony_prune_dead":
            defn = str(s.node(c)["attrs"].get("definition", "")); break
    print("AGENT'S CONCEPT (drive_parsimony_prune_dead):")
    print(f"  {defn}\n")
    trigger = extract_trigger_from_concept(defn)
    print("EXTRACTED TRIGGER (the agent's dimensions, mechanical qualifier->op):")
    for t in trigger:
        print(f"  {t['lhs']['attr']:11} {t['op']:4} {t['rhs']}")
    print()

    # 3. build the spec. effect = mark for deprecation (the concept's consequence).
    nat = s._native_handle() if hasattr(s, "_native_handle") else s
    prune_spec = {
        "name": "parsimony_prune_dead",
        "vars": ["root", "M"],
        "match": [["root", "manages", "M"]],
        "trigger": trigger,
        "effects": [["set_attr", "M", "deprecated", 1]],
    }

    # the MDL/parsimony selector the agent linked: keep-value = coverage*activation - redundancy.
    keep = Minus(a=Times(items=(Attr(Var("M"), "coverage"), Attr(Var("M"), "activation"))),
                 b=Attr(Var("M"), "redundancy"))
    mdl_spec_rule = {
        "name": "score_mdl_keep",
        "match": [["root", "manages", "M"]],
        "where": Lit(True).to_dict(),
        "effects": [["set_attr", "M", "mdl_keep", {"__term__": keep.to_dict()}]],
    }

    # 4. emit.
    pr_idx = emit_rule_from_spec(nat, prune_spec)
    mk_idx = nat.add_rule(mdl_spec_rule)
    print(f"EMITTED fireable Rules: parsimony_prune_dead (#{pr_idx}), "
          f"score_mdl_keep (#{mk_idx})\n")

    # 5. verify on a synthetic graph: one dead Mt, one healthy Mt.
    root = s.add_node("ParsimonyRoot", {"id": "parsimony_root"})
    dead = s.add_node("Microtheory", {"name": "dead_mt", "coverage": 0.05,
                                      "activation": 0, "redundancy": 0.95})
    healthy = s.add_node("Microtheory", {"name": "healthy_mt", "coverage": 0.8,
                                         "activation": 12, "redundancy": 0.1})
    s.add_edge(root, "manages", dead)
    s.add_edge(root, "manages", healthy)

    s.run_rules(10000)

    da, ha = s.node(dead)["attrs"], s.node(healthy)["attrs"]
    print("VERIFY (the substrate ran the emitted rules):")
    print(f"  dead_mt   : deprecated={da.get('deprecated')!r}  mdl_keep={da.get('mdl_keep')!r}")
    print(f"  healthy_mt: deprecated={ha.get('deprecated')!r}  mdl_keep={ha.get('mdl_keep')!r}")
    ok = (da.get("deprecated") == 1 and ha.get("deprecated") in (None, 0)
          and da.get("mdl_keep") is not None and ha.get("mdl_keep") is not None
          and float(ha.get("mdl_keep")) > float(da.get("mdl_keep")))
    print(f"\n  {'PASS' if ok else 'FAIL'} — dead flagged for deprecation, healthy "
          f"survives, keep-value ranks healthy > dead.")


if __name__ == "__main__":
    main()
