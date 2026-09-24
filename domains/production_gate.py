"""Phase 6A: cognitively gated production release.

This module is deliberately small and mechanical.  Production may release a
surface only when the selected semantic frame is present, the output-null
monitor says the surface is recoverable, and the monitor created a committed
record.  The receipt makes the release auditable without turning the adapter
into a second production decision-maker.
"""
from __future__ import annotations

from typing import Any


def _native(agent):
    return getattr(agent, "inner", getattr(getattr(agent, "s", None), "_inner", None))


def legacy_readback_gate(frame: dict[str, Any], surface: str | None,
                         *, evidence_keys=None) -> dict[str, Any]:
    """Return the bounded parse-back verdict for a structural fact readback.

    The legacy relation renderer has no language-production frame to hand to
    the newer monitor.  Its deterministic round-trip contract is narrower:
    the selected relation and both selected referents must survive into the
    returned surface.  This is evidence checking, not answer selection; the
    caller has already selected the graph-held fact.
    """
    text = str(surface or "").strip().lower()
    normalized_text = text.replace("-", " ")
    keys = tuple(evidence_keys or ("event", "agent", "patient"))
    intended = [str(frame.get(key)).strip().lower()
                for key in keys if frame.get(key)]
    def _forms(token: str) -> set[str]:
        """Small structural inflection tolerance for legacy topic keys.

        A taught topic may be plural while its grounded answer uses the
        singular (``volcanoes`` -> ``volcano``). This is evidence matching,
        not a language-production shortcut: the selected topic still has to
        leave a recoverable lexical form in the surface. The relation
        renderer's exact forms remain the normal case.
        """
        forms = {token}
        if token.endswith("ies") and len(token) > 3:
            forms.add(token[:-3] + "y")
        if token.endswith("es") and len(token) > 3:
            forms.add(token[:-2])
        if token.endswith("s") and len(token) > 2:
            forms.add(token[:-1])
        return forms

    recovered = [token for token in intended
                 if token and any(
                     form in text or form.replace("-", " ") in normalized_text
                     for form in _forms(token))]
    missing = [token for token in intended if token not in recovered]
    return {
        "recoverable": bool(intended) and not missing,
        "coverage": len(recovered) / len(intended) if intended else 0.0,
        "recovered": recovered,
        "missing": missing,
        "intended": intended,
        "mode": "legacy_structural_readback",
    }


def release_if_gated(agent, frame: dict[str, Any], surface: str | None,
                     gate: dict[str, Any] | None, committed: Any = None) -> str | None:
    """Record and return a surface only when its cognitive release gate passed.

    This is not a new semantic scorer.  ``gate`` is the existing parse-back /
    output-null result, and ``committed`` is the existing committed monitor
    node.  Missing evidence yields ``None`` so the caller reaches its explicit
    error floor or bounded repair path.
    """
    text = str(surface or "").strip()
    semantic = frame if isinstance(frame, dict) else {}
    monitor = gate or {}
    recoverable = bool(monitor.get("recoverable"))
    has_goal = bool(semantic.get("event") and semantic.get("intent"))
    has_content = any(semantic.get(role) for role in
                      ("agent", "patient", "location", "recipient", "instrument"))
    reasons = []
    if not text:
        reasons.append("empty_surface")
    if text.rstrip(".!?").strip().lower() == "noted":
        reasons.append("forbidden_fallback_surface")
    if not has_goal:
        reasons.append("missing_selected_goal")
    if not has_content:
        reasons.append("missing_semantic_content")
    if not recoverable:
        reasons.append("parse_back_not_recoverable")
    if committed is None:
        reasons.append("missing_commitment")

    sub = getattr(agent, "s", agent)
    native = _native(agent)

    # Conversation-scoped idempotence: a legacy reader and its retry can
    # revisit the same selected release during one inbound event while each
    # call carries a distinct transient ``Committed`` node.  The existing
    # commitment-identity guard below cannot catch that case.  Use the already
    # established inbound Message identity only when the world adapter exposes
    # it; independent direct production calls retain the older commitment
    # identity contract.  Competing semantic events are intentionally not
    # merged because their event/mode signatures differ.
    turn_id = getattr(agent, "_last_turn_inbound", None)
    if hasattr(turn_id, "value"):
        turn_id = int(turn_id.value)
    if not reasons and turn_id is not None:
        semantic_content = sorted(str(semantic.get(role)) for role in
                                  ("agent", "patient", "location", "recipient", "instrument")
                                  if semantic.get(role))
        for existing in sub.nodes("ProductionGateReceipt"):
            existing_attrs = sub.node(existing)["attrs"]
            if (existing_attrs.get("status") == "released"
                    and existing_attrs.get("turn_message_id") == turn_id
                    and existing_attrs.get("surface") == text
                    and existing_attrs.get("semantic_event") ==
                    str(semantic.get("event"))
                    and existing_attrs.get("semantic_intent") ==
                    str(semantic.get("intent"))
                    and existing_attrs.get("semantic_content") == semantic_content
                    and existing_attrs.get("parse_back_mode") == monitor.get("mode")):
                return text

    # A production gate may be revisited while the same graph commitment is
    # still selected.  Reuse the existing released receipt rather than
    # minting a second authoritative release record.  This is an idempotence
    # guard over graph identity, not a text-based deduplication heuristic.
    if not reasons and native is not None and committed is not None:
        for existing in sub.nodes("ProductionGateReceipt"):
            existing_attrs = sub.node(existing)["attrs"]
            if (existing_attrs.get("status") == "released"
                    and existing_attrs.get("surface") == text
                    and existing_attrs.get("semantic_event") ==
                    str(semantic.get("event"))
                    and existing_attrs.get("semantic_intent") ==
                    str(semantic.get("intent"))
                    and committed in native.neighbours(existing, "releases")):
                return text

    attrs = {
        "status": "released" if not reasons else "withheld",
        "surface": text,
        "semantic_event": str(semantic.get("event")),
        "semantic_intent": str(semantic.get("intent")),
        "semantic_content": sorted(str(semantic.get(role)) for role in
                                    ("agent", "patient", "location", "recipient", "instrument")
                                    if semantic.get(role)),
        "recoverable": recoverable,
        "parse_back_mode": monitor.get("mode"),
        "coverage": monitor.get("coverage"),
        "withhold_reasons": reasons,
    }
    if turn_id is not None:
        attrs["turn_message_id"] = turn_id
    receipt = sub.add_node("ProductionGateReceipt", attrs)
    if native is not None and not reasons:
        native.add_edge_unchecked(receipt, "releases", committed)
    return text if not reasons else None


__all__ = ["legacy_readback_gate", "release_if_gated"]
