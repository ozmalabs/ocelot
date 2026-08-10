"""Capability profiler — measure the capability graph from the agent's OWN activity,
instead of hand-wiring it.

The capstone of the capability-graph arc. A capability is a rule the agent runs; its
`composes_on` edges are the agent's own DATAFLOW — rule B composes_on rule A when B
reads an attr A writes (B consumes what A produces). That structure is derived from
the rules themselves (a mechanical walk, the same read/write logic the Rust engine's
`derive_access` uses), and which rules actually fired (and how hard) is read from the
engine's own `rule_costs()` after a real `run_rules`. Feed that measured graph to the
existing `cap_leverage_propagate` rule and leverage falls out — the rule everything
routes through scores highest, with nobody hand-wiring it.

Mechanical host I/O only: walk rule JSON, read the engine's cost counters, mint the
graph. No decision is taken here — leverage is computed by the graph's own rules.
"""
from __future__ import annotations

from domains.capability_graph import add_capability, compose

# Efficiency-proficiency scale: cost-per-firing (µs) at which own_prof falls to ~0.5.
# A cheap, fast (well-optimised) capability reads as high proficiency — the JIT's own
# notion of mastery. This is EFFICIENCY proficiency, not correctness (which would need a
# per-rule success oracle the cost counters don't carry).
_PROF_SCALE = 50.0

# Control-flow flags written/read by almost every rule as a firing guard — they are
# not data the rules pass to each other, so counting them as dataflow manufactures
# false edges. Excluded from the composition derivation (documented, not silent).
_CONTROL_KEYS = {"status", "stage"}


def build_type_map(productions):
    """edge_type -> (src_type, tgt_type), from a seed's declared productions. Lets the
    profiler resolve each rule variable's node type, so read/write keys can be qualified
    by (node_type, key) and coincidental same-name attrs on different types don't collide."""
    tm = {}
    for p in productions:
        et = p.get("edge_type")
        if et:
            tm.setdefault(et, (p.get("src", {}).get("type"), p.get("tgt", {}).get("type")))
    return tm


def _var_types(rule, type_map):
    """Bind each rule variable to its node type via the match edges + add_node effects."""
    vt = {}
    for m in rule.get("match", []):
        if isinstance(m, list) and len(m) >= 3 and m[1] in type_map:
            src_t, tgt_t = type_map[m[1]]
            vt.setdefault(m[0], src_t)
            vt.setdefault(m[2], tgt_t)
    for eff in rule.get("effects", []):
        if isinstance(eff, list) and eff and eff[0] in ("add_node", "add_node_if_absent") and len(eff) > 2:
            vt[eff[1]] = eff[2]
    return vt


def _node_type(n, vt):
    if isinstance(n, dict):
        if n.get("type") == "Var":
            return vt.get(n.get("name"), "?")
        if n.get("type") == "Pick" and isinstance(n.get("source"), dict) \
                and n["source"].get("type") == "NodesOfType":
            return n["source"].get("node_type", "?")
    return "?"


def _attr_reads(node, acc, vt=None):
    """Attr keys read anywhere in a term subtree. Qualified by (node_type, key) when a
    var->type map is supplied, else the bare key."""
    if isinstance(node, dict):
        if node.get("type") == "Attr" and "key" in node:
            acc.add((_node_type(node.get("node"), vt), node["key"]) if vt is not None else node["key"])
        for v in node.values():
            _attr_reads(v, acc, vt)
    elif isinstance(node, list):
        for v in node:
            _attr_reads(v, acc, vt)


def rule_access(rule, type_map=None):
    """(reads, writes) sets for a rule, from its own JSON — the producer/consumer accounting
    the engine does in `derive_access`, over the wire form. With `type_map`, keys are
    qualified by (node_type, key) so coincidental same-name attrs on different node types
    don't collide (and the control-key exclusion is unnecessary — types resolve it)."""
    vt = _var_types(rule, type_map) if type_map is not None else None
    reads, writes = set(), set()
    _attr_reads(rule.get("where"), reads, vt)
    for eff in rule.get("effects", []):
        if not isinstance(eff, list):
            continue
        op = eff[0]
        if op == "set_attr":                      # ["set_attr", var, key, value]
            writes.add((vt.get(eff[1], "?"), eff[2]) if vt is not None else eff[2])
            _attr_reads(eff[3], reads, vt)        # the value term may read other attrs
        elif op in ("add_node", "add_node_if_absent"):  # [op, var, type, {attrs}]
            if len(eff) > 3 and isinstance(eff[3], dict):
                for k in eff[3]:
                    writes.add((eff[2], k) if vt is not None else k)
                _attr_reads(eff[3], reads, vt)
    if vt is not None:                            # types resolve collisions; no key exclusion needed
        return reads, writes
    return reads - _CONTROL_KEYS, writes - _CONTROL_KEYS


def profile(observed, rules_by_name, cap_substrate, root, *, min_fires=1, type_map=None):
    """Build a MEASURED capability graph in `cap_substrate` from a workload that already
    ran on `observed`.

    - which rules fired (and how hard) := observed.rule_costs() (the engine's own counters)
    - composes_on := derived dataflow (B composes_on A iff reads(B) ∩ writes(A))

    Returns {rule_name: capability_node}. Leverage/genericity are then the graph's job.
    """
    cost = {name: (us, prog) for (name, us, _proc, prog) in observed.rule_costs() if prog >= min_fires}
    access = {n: rule_access(rules_by_name[n], type_map) for n in cost if n in rules_by_name}

    caps = {}
    for name, (us, prog) in cost.items():
        if name not in access:
            continue
        # own_prof is MEASURED as efficiency: cheaper per firing => more mastered/optimised.
        us_per_fire = us / max(prog, 1)
        own_prof = 1.0 / (1.0 + us_per_fire / _PROF_SCALE)
        # own_value carries measured activity: a rule that fires more is a hotter base.
        cap = add_capability(cap_substrate, root, name, own_prof, own_value=1.0 + float(prog))
        cap_substrate.set_attr(cap, "hotness", float(prog))   # measured fire count
        cap_substrate.set_attr(cap, "cost", float(us))        # measured time footprint
        caps[name] = cap

    # B composes_on A  <=>  B genuinely CONSUMES output A produces: B reads a key A writes
    # that B does NOT itself write. Requiring "not written by B" excludes shared-accumulator
    # keys (both rules write them — mutual state, not producer/consumer), which would
    # otherwise form cycles; the result is a DAG, so multiplicative eff_cap composes cleanly.
    for b, (rb, wb) in access.items():
        for a, (ra, wa) in access.items():
            if a == b or b not in caps or a not in caps:
                continue
            if (rb & wa) - wb:                       # a key A writes, B reads, B doesn't write
                compose(cap_substrate, caps[b], caps[a])
    return caps
