"""The agent proposes the reflex-net Rust affordance it needs.

Per the self-extension architecture (`domains/self_extend_rust.py`,
`domains/proposal_install.py`): the agent AUTHORS a `RustExtensionSpec`
(a name + semantics-kind + why-new/residual prose — the DECISION that a
primitive is needed), and a gated pipeline builds/installs it. The agent
can only *parameterize* existing codegen templates; genuinely novel
engine logic (like this one, whose evaluator lives in `shape_decode.rs`)
falls OUTSIDE rung-4's additive write surface — `ALLOWED_INSTALL_FILES`
is `{term.rs, jsonio.rs, reflect.rs, py.rs, shape.rs}`, and this touches
`shape_decode.rs` — so it is the documented human-authored engine-change
pattern (the join-index precedent), authored under the creator's
directive and gated, NOT slipped through the auto-installer.

This builder mints the agent's own graph record of that decision: the
`RustExtensionSpec` naming the residual its language could not express
(per-net basin scoping of a decode) + an `ExtensionProposal` marking the
honest install boundary. Mechanical graph emission only — the DECISION
(the residual, why it's new) is the agent's; the writer is host I/O.
"""
from __future__ import annotations

_SPEC_NAME = "shapedecode_codebook_scope"


def agent_propose_codebook_scope(substrate, *, installed=True, ts=None):
    """Mint the agent's RustExtensionSpec + ExtensionProposal for the
    `codebook_scope` affordance. Idempotent on the spec name. Returns
    (spec_id, proposal_id)."""
    sub = getattr(substrate, "s", substrate)

    # The agent's spec: the residual its held DSL could not express.
    spec_attrs = {
        "name": _SPEC_NAME,
        "semantics_kind": "codebook_scoping",
        "purpose": "Restrict a ShapeDecode to a per-net subset of the shared "
                   "codebook so two reflex nets can hold DIFFERENT symbolic basins.",
        "why_new": "ShapeDecode's codebook is selected by node TYPE (all "
                   "ShapeSignatures) and its `exclude` filters by name; neither "
                   "expresses 'decode against ONLY this net's basin_parts'. No "
                   "finite Term-tree over the held DSL scopes the codebook per net.",
        "motivating_residual": "reflex_ground_residual could only ground a "
                               "reflex query against the WHOLE quantum codebook; a "
                               "per-net basin (this net serves domain X, that one "
                               "domain Y) was inexpressible — the exhausted trail "
                               "named a new ShapeDecode parameter.",
        "compiled": bool(installed),
        "stage": "human_built_engine_change",
        "errors": "",
        "origin": "agent_runtime_design",
    }
    existing = None
    for n in sub.nodes("RustExtensionSpec"):
        if sub.node(n)["attrs"].get("name") == _SPEC_NAME:
            existing = n
            break
    if existing is not None and sub.has_node(existing):
        for k, v in spec_attrs.items():
            sub.set_attr(existing, k, v)
        spec_id = existing
    else:
        spec_id = sub.add_node("RustExtensionSpec", spec_attrs)

    # The honest install boundary: this is an engine change (shape_decode.rs)
    # OUTSIDE rung-4's ALLOWED_INSTALL_FILES, authored by the human/coding-agent
    # under directive and gated — not auto-installed. live_tree_untouched is
    # False precisely because the affordance IS now in the live runtime.
    prop_attrs = {
        "of": _SPEC_NAME,
        "status": "installed" if installed else "requested",
        "requires_restart": True,
        "installed": bool(installed),
        "live_tree_untouched": not installed,
        "install_surface": "engine_change_outside_rung4_allowed_files",
        "touches": "runners/dsl/src/shape_decode.rs (apply_scope) + term/jsonio/reflect",
        "gated_by": "human directive (join-index precedent)",
        "ts": ts,
    }
    prop_id = sub.add_node("ExtensionProposal", prop_attrs)
    inner = getattr(substrate, "inner", sub)
    try:
        inner.add_edge_unchecked(prop_id, "validates", spec_id)
    except Exception:
        sub.add_edge(prop_id, "validates", spec_id, {})
    return spec_id, prop_id
