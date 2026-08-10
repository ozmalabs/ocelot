"""Reflex-net builder — the mechanical graph construction that mints the
PRIMAL LAYER over an already-constructed net.

This is a world-adapter/seed BUILDER: it only EMITS graph data (ReflexNet
node + edges + TunableParameter knobs). No decisions, no agent state — the
DECISIONS (serve within basin, judge faster-and-regression-free, adopt)
all live in seeds/reflex_net.json's Rules and the existing rule spine.

The design (see REFLEX_NET_DESIGN.md):

  * A reflex net wraps a `NetworkAssemblage` (evaluated by the native
    `NetForward` Term) as a cheap default path.
  * It is minted OFF (`enabled == 0`) — the layer is optional; a
    judge/adopt or human decision flips it on.
  * Its basin gate (`basin_threshold`) and `enabled` flag are
    `TunableParameter`s, so widening/narrowing/disabling is a zero-code
    graph edit.

Because the generic `reflex_net_serve` Rule matches ANY
`ReflexQuery -for_net-> ReflexNet -net_assemblage-> NetworkAssemblage`,
minting a reflex net is pure data — no per-net rule authoring. Adopt =
flip `enabled`; ablate = `remove_rule` the serve rule or disable the
node; both reuse the substrate's existing spine.
"""
from __future__ import annotations


# The knobs every reflex net carries, discoverable via `has_tunable`.
_KNOBS = (
    ("enabled", 0.0, 1.0, 1.0, "serve from this reflex net (0=off, the default)"),
    ("basin_threshold", 0.0, 1.0e9, 0.05,
     "serve only when the caller's residual is below this (basin membership)"),
)


def mint_reflex_net(substrate, assemblage_nid, *, name,
                    basin_threshold, enabled=0.0):
    """Mint a ReflexNet wrapping `assemblage_nid`, OFF by default.

    Idempotent on `name`: re-minting returns the existing node. Returns
    the ReflexNet node id. Mechanical graph emission only.
    """
    s = substrate
    for existing in s.nodes("ReflexNet"):
        if s.node(existing)["attrs"].get("name") == name:
            return existing

    rn = s.add_node("ReflexNet", {
        "name": name,
        "enabled": float(enabled),
        "basin_threshold": float(basin_threshold),
    })
    s.add_edge(rn, "net_assemblage", assemblage_nid, {})
    for attr, lo, hi, step, desc in _KNOBS:
        tp = s.add_node("TunableParameter", {
            "attr_name": attr, "min": float(lo), "max": float(hi),
            "step": float(step), "description": f"reflex-net {name}: {desc}",
        })
        s.add_edge(rn, "has_tunable", tp, {})
    return rn


def mint_reflex_query(substrate, reflex_net_nid, input_vec, residual):
    """Mint a pending ReflexQuery against `reflex_net_nid`. The caller
    supplies the grounded `residual` (the decode residual / quantum
    membership) — the basin gate is EXTERNAL to the net. Mechanical only.
    """
    s = substrate
    q = s.add_node("ReflexQuery", {
        "status": "pending",
        "residual": float(residual),
        "input_vec": [float(v) for v in input_vec],
    })
    s.add_edge(q, "for_net", reflex_net_nid, {})
    return q
