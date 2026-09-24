"""Boundary-only fixture adapter for the preregistered autonomous discovery demo.

This module may construct raw graph facts, load named seeds, drive a native
fixpoint, and export artifacts. It does not inspect a trajectory to select a
next concept, derive residuals, count evidence, choose recurrence, route
semantics, or mint capabilities: those decisions belong to ``ad_*``, ``mrl_*``,
``sd_*``, and ``mrs_*`` rules.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from substrate.boot_core import boot_core, load_seeds_into


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests/capability/minting/fixtures/autonomous_discovery_preregistered.json"
EDGE_TYPES = (
    "has_discovery_request", "uses_policy", "starts_at", "setpoint", "uses_observer",
    "trajectory_next", "has_semantic_relation", "has_discovery_episode",
    "has_minting_recurrence_episode", "has_episode", "has_thought_segment",
    "current_segment", "at_concept", "candidate_concept", "targets_concept",
    "selected_candidate", "has_segment_signature", "has_residual_structure",
    "reified_as_evidence", "has_residual_segment_evidence", "has_predicate_recurrence_candidate",
    "supported_by_segment", "has_mint_offer", "observed", "minted", "minted_axis",
    "has_relation_witness", "operation_request", "licenses", "licensed_by", "reachable_via",
)

# These are outputs of graph rules, never facts that this boundary adapter may author.
PROHIBITED_ADAPTER_NODE_TYPES = frozenset((
    "ThoughtSegment", "ResidualSegmentEvidence", "ResidualRelationWitness",
    "PredicateRecurrenceCandidate", "Observation", "CapabilityAxis",
))
_RAW_NODE_TYPES = frozenset((
    "DiscoveryPolicy", "Observer", "Concept", "DiscoveryRequest", "Entity",
    "SemanticRelation", "ShapeSignature",
))
_RAW_EDGE_TYPES = frozenset((
    "trajectory_next", "has_discovery_request", "uses_policy", "starts_at", "setpoint",
    "uses_observer", "has_semantic_relation",
))
_OPAQUE_ATTR_KEYS = frozenset((
    "concept_id", "display_label", "entity_id", "relation_id", "request_id", "surface_label",
))
# This is the complete, preregistered domain of labels that are not semantic relation
# fields, structural topology, or traversal policy. Fixture validation rejects a partial
# or non-bijective replacement rather than silently leaving a label unchanged.
OPAQUE_LABEL_KEYS = frozenset((
    "setpoint", "train_a", "train_b", "concept_setpoint_id", "concept_train_a_id",
    "concept_train_b_id", "request_train", "held_out_test_z", "relation_a", "relation_b",
    "setpoint_relation", "relation_a_id", "relation_b_id", "setpoint_relation_id", "item_a",
    "slot_a", "item_b", "slot_b", "test_item", "test_slot", "display_item_a",
    "display_slot_a", "display_item_b", "display_slot_b", "display_test_item",
    "display_test_slot", "positive_like_display", "precovered_structural_basis",
))


class _RaisingExternalCallback:
    """A non-functional external boundary whose calls are observable and fatal."""

    def __init__(self, audit: dict[str, Any], name: str):
        self._audit = audit
        self._name = name

    def __call__(self, *_args: Any, **_kwargs: Any) -> None:
        self._audit["callback_invocations"] += 1
        self._audit["callback_calls"].append(self._name)
        raise AssertionError(f"external {self._name} callback is prohibited in autonomous discovery")


def _has_mint_or_status_field(attrs: dict[str, Any]) -> bool:
    """Recognize output-status fields without confusing the fixed policy threshold."""
    return any(
        key == "status" or "minted" in key or key in {"mint_status", "offer_status", "mint_offer"}
        for key in attrs
    )


class _AdapterWriteGuard:
    """Instrument and constrain every public adapter mutation after seed loading."""

    def __init__(self, substrate: Any, audit: dict[str, Any]):
        self._substrate = substrate
        self._audit = audit
        self._phase = "booted"
        self._original = {
            name: getattr(substrate, name)
            for name in (
                "add_node", "add_edge", "add_edge_unchecked", "set_attr", "set_attr_many",
                "set_attr_each", "set_type", "remove_edge", "remove_node",
            )
        }

    def install(self) -> None:
        # These methods live on the Python substrate facade. Native rule effects call
        # ``_inner`` directly, so graph-native derived artifacts remain permitted.
        self._substrate.add_node = self.add_node
        self._substrate.add_edge = self.add_edge
        self._substrate.add_edge_unchecked = self.add_edge_unchecked
        self._substrate.set_attr = self.set_attr
        self._substrate.set_attr_many = self.set_attr_many
        self._substrate.set_attr_each = self.set_attr_each
        self._substrate.set_type = self.set_type
        self._substrate.remove_edge = self.remove_edge
        self._substrate.remove_node = self.remove_node

    def begin_raw_submission(self) -> None:
        if self._phase != "booted":
            self._fail("a discovery fixture may be submitted exactly once")
        self._phase = "raw"

    def finish_raw_submission(self) -> None:
        if self._phase != "raw":
            self._fail("raw submission did not complete from the raw phase")
        self._audit["raw_discovery_submissions"] += 1
        self._phase = "locked"

    def begin_held_out_submission(self) -> None:
        if self._phase != "locked":
            self._fail("held-out input may be submitted only after raw settlement")
        self._phase = "held_out"

    def finish_held_out_submission(self) -> None:
        if self._phase != "held_out":
            self._fail("held-out submission did not complete from its permitted phase")
        self._audit["held_out_submissions"] += 1
        self._phase = "locked"

    def _record(self, kind: str, detail: str) -> None:
        self._audit["permitted_adapter_writes"] += 1
        self._audit["adapter_write_events"].append({"phase": self._phase, "kind": kind, "detail": detail})

    def _fail(self, detail: str) -> None:
        self._audit["prohibited_writes"] += 1
        self._audit["prohibited_write_attempts"].append({"phase": self._phase, "detail": detail})
        raise AssertionError(f"prohibited autonomous-discovery adapter write: {detail}")

    def add_node(self, node_type: str, attrs: dict[str, Any] | None = None) -> Any:
        attrs = dict(attrs or {})
        if node_type in PROHIBITED_ADAPTER_NODE_TYPES:
            self._fail(f"adapter may not create derived node type {node_type}")
        if self._phase == "raw":
            if node_type not in _RAW_NODE_TYPES:
                self._fail(f"raw adapter node type {node_type} is not preregistered")
            if _has_mint_or_status_field(attrs) and not (
                node_type == "DiscoveryRequest" and attrs.get("status") == "pending" and set(attrs) == {"status", "request_id"}
            ):
                self._fail(f"raw adapter may not author mint/status fields on {node_type}")
        elif self._phase == "held_out":
            if node_type != "OperationRequest":
                self._fail(f"post-submission adapter node type {node_type} is not the held-out request")
            if _has_mint_or_status_field(attrs):
                self._fail("post-submission adapter may not author mint/status fields")
        else:
            self._fail(f"adapter node creation is closed during {self._phase}")
        self._record("node", node_type)
        return self._original["add_node"](node_type, attrs)

    def _add_edge(self, method: str, src: Any, edge_type: str, tgt: Any, attrs: dict[str, Any] | None = None) -> None:
        attrs = dict(attrs or {})
        allowed = _RAW_EDGE_TYPES if self._phase == "raw" else {"operation_request"} if self._phase == "held_out" else set()
        if edge_type not in allowed:
            self._fail(f"adapter edge {edge_type} is not permitted during {self._phase}")
        if _has_mint_or_status_field(attrs):
            self._fail(f"adapter edge {edge_type} carries a prohibited mint/status field")
        self._record("edge", edge_type)
        self._original[method](src, edge_type, tgt, attrs)

    def add_edge(self, src: Any, edge_type: str, tgt: Any, attrs: dict[str, Any] | None = None) -> None:
        self._add_edge("add_edge", src, edge_type, tgt, attrs)

    def add_edge_unchecked(self, src: Any, edge_type: str, tgt: Any, attrs: dict[str, Any] | None = None) -> None:
        self._add_edge("add_edge_unchecked", src, edge_type, tgt, attrs)

    def _closed_mutation(self, name: str, *_args: Any, **_kwargs: Any) -> None:
        self._fail(f"adapter {name} is never permitted after boot")

    set_attr = lambda self, *args, **kwargs: self._closed_mutation("set_attr", *args, **kwargs)
    set_attr_many = lambda self, *args, **kwargs: self._closed_mutation("set_attr_many", *args, **kwargs)
    set_attr_each = lambda self, *args, **kwargs: self._closed_mutation("set_attr_each", *args, **kwargs)
    set_type = lambda self, *args, **kwargs: self._closed_mutation("set_type", *args, **kwargs)
    remove_edge = lambda self, *args, **kwargs: self._closed_mutation("remove_edge", *args, **kwargs)
    remove_node = lambda self, *args, **kwargs: self._closed_mutation("remove_node", *args, **kwargs)


def _install_boundary_instrumentation(substrate: Any) -> None:
    if hasattr(substrate, "_autonomous_discovery_guard"):
        return
    audit: dict[str, Any] = {
        "raw_discovery_submissions": 0,
        "held_out_submissions": 0,
        "permitted_adapter_writes": 0,
        "adapter_write_events": [],
        "prohibited_writes": 0,
        "prohibited_write_attempts": [],
        "callback_invocations": 0,
        "callback_calls": [],
    }
    guard = _AdapterWriteGuard(substrate, audit)
    guard.install()
    substrate._autonomous_discovery_audit = audit
    substrate._autonomous_discovery_guard = guard
    substrate._autonomous_discovery_callbacks = {
        name: _RaisingExternalCallback(audit, name)
        for name in ("ask", "llm", "network", "tool")
    }


def adapter_audit(substrate: Any) -> dict[str, Any]:
    """Return live instrumentation data, not a reconstructed or hard-coded report."""
    return substrate._autonomous_discovery_audit


def external_callbacks(substrate: Any) -> dict[str, _RaisingExternalCallback]:
    """Return the explicit raising external-boundary stubs with shared telemetry."""
    return dict(substrate._autonomous_discovery_callbacks)


def load_fixture(path: Path = FIXTURE_PATH) -> dict[str, Any]:
    """Read the immutable preregistered raw-fixture specification."""
    fixture = json.loads(path.read_text())
    opaque = fixture.get("opaque_bijection", {})
    if set(opaque) != OPAQUE_LABEL_KEYS:
        missing = sorted(OPAQUE_LABEL_KEYS - set(opaque))
        extra = sorted(set(opaque) - OPAQUE_LABEL_KEYS)
        raise ValueError(f"opaque bijection domain mismatch; missing={missing}, extra={extra}")
    values = list(opaque.values())
    if any(not isinstance(value, str) or not value for value in values) or len(values) != len(set(values)):
        raise ValueError("opaque_bijection must map every declared opaque label to a unique non-empty string")
    return fixture


def boot_native() -> tuple[Any, Any]:
    """Boot only the explicit autonomous discovery seed closure and its boundary guard."""
    substrate, agent = boot_core(seeds=())
    load_seeds_into(substrate, agent, ["autonomous_discovery"])
    _install_boundary_instrumentation(substrate)
    return substrate, agent


def _relation(tuple_fields: dict[str, Any], *, relation_id: str, surface_label: str) -> dict[str, Any]:
    return {**tuple_fields, "relation_id": relation_id, "surface_label": surface_label}


def _label(state: dict[str, Any], key: str) -> str:
    state["opaque_label_keys_used"].add(key)
    return state["opaque_bijection"].get(key, key) if state["scrambled"] else key


def _add_raw_case(substrate: Any, agent: Any, *, case_name: str, fixture: dict[str, Any]) -> dict[str, Any]:
    """Insert only fixed raw fixture data; no derived discovery object is authored here."""
    case = fixture["cases"][case_name]
    mode = case["mode"]
    base = dict(fixture["semantic_tuple"])
    state: dict[str, Any] = {
        "mode": mode,
        "scrambled": mode == "scrambled_positive",
        "opaque_bijection": fixture["opaque_bijection"],
        "opaque_label_keys_used": set(),
    }
    name = lambda key: _label(state, key)
    policy = substrate.add_node("DiscoveryPolicy", dict(fixture["policy"]))
    observer = substrate.add_node("Observer", {"resolves": [base["dimension"]], "grain": {base["dimension"]: 1}})
    setpoint = substrate.add_node("Concept", {"concept_id": name("concept_setpoint_id"), "traversal_order": 0, "surface_label": name("setpoint")})
    train_a = substrate.add_node("Concept", {"concept_id": name("concept_train_a_id"), "traversal_order": 10, "surface_label": name("train_a")})
    train_b = substrate.add_node("Concept", {"concept_id": name("concept_train_b_id"), "traversal_order": 20, "surface_label": name("train_b")})
    substrate.add_edge(train_a, "trajectory_next", train_b)
    request = substrate.add_node("DiscoveryRequest", {"status": "pending", "request_id": name("request_train")})
    substrate.add_edge(agent, "has_discovery_request", request)
    substrate.add_edge(request, "uses_policy", policy)
    substrate.add_edge(request, "starts_at", train_a)
    substrate.add_edge(request, "setpoint", setpoint)
    substrate.add_edge(request, "uses_observer", observer)

    for entity_key, display_key in (
        ("item_a", "display_item_a"), ("slot_a", "display_slot_a"),
        ("item_b", "display_item_b"), ("slot_b", "display_slot_b"),
        ("test_item", "display_test_item"), ("test_slot", "display_test_slot"),
    ):
        substrate.add_node("Entity", {"entity_id": name(entity_key), "display_label": name(display_key)})

    first, second = dict(base), dict(base)
    if mode == "different_structure":
        second["arg2_role"] = "GROUP"
        second["quantum"] = 2
    for concept, relation, relation_id, label in (
        (train_a, first, name("relation_a_id"), name("relation_a")),
        (train_b, second, name("relation_b_id"), name("relation_b")),
    ):
        semantic = substrate.add_node("SemanticRelation", _relation(relation, relation_id=relation_id, surface_label=label))
        substrate.add_edge(concept, "has_semantic_relation", semantic)
    if mode == "precovered_setpoint":
        admitted = substrate.add_node("SemanticRelation", _relation(
            base, relation_id=name("setpoint_relation_id"), surface_label=name("setpoint_relation"),
        ))
        substrate.add_edge(setpoint, "has_semantic_relation", admitted)
    if mode == "precovered_shape":
        substrate.add_node("ShapeSignature", {
            "name": name("precovered_structural_basis"),
            "signature": [[base["dimension"], base["relation_head"], base["arg1_role"], base["arg2_role"], base["quantum"]]],
        })
    return {**state, "request": request, "policy": policy, "observer": observer, "setpoint": setpoint,
            "train_a": train_a, "train_b": train_b}


def submit_preregistered_case(substrate: Any, agent: Any, *, case_name: str,
                               fixture: dict[str, Any] | None = None) -> dict[str, Any]:
    """Submit exactly one raw discovery fixture under enforced boundary instrumentation."""
    fixture = fixture or load_fixture()
    guard = substrate._autonomous_discovery_guard
    guard.begin_raw_submission()
    try:
        state = _add_raw_case(substrate, agent, case_name=case_name, fixture=fixture)
    except Exception:
        guard._phase = "locked"
        raise
    guard.finish_raw_submission()
    state["audit"] = adapter_audit(substrate)
    state["fixture"] = fixture
    state["case_name"] = case_name
    return state


def settle_native(substrate: Any) -> None:
    """Drive the graph-native rule closure; no host-side decision is made."""
    native_steps = substrate._inner.run_rules()
    substrate._inner.add_node("NativeAutonomousDiscoveryReceipt", {
        "schema": "native_autonomous_discovery_receipt.v1",
        "cluster": "autonomous_discovery.native_settlement",
        "provenance": "native_rule_readback:autonomous_discovery",
        "native_rule": "autonomous_discovery_native_rules",
        "native_steps": int(native_steps),
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })


def submit_held_out_operation(substrate: Any, agent: Any, state: dict[str, Any]) -> Any:
    """Submit the one preregistered held-out request through the narrowly open input gate."""
    base = dict(state["fixture"]["semantic_tuple"])
    mode = state["mode"]
    if mode == "held_out_role_mismatch":
        base["arg2_role"] = "GROUP"
    elif mode == "held_out_head_mismatch":
        base["relation_head"] = "place"
    guard = substrate._autonomous_discovery_guard
    guard.begin_held_out_submission()
    try:
        request = substrate.add_node("OperationRequest", {
            "request_id": _label(state, "held_out_test_z"), "display_label": _label(state, "positive_like_display"),
            "relation_head": base["relation_head"], "arg1_role": base["arg1_role"], "arg2_role": base["arg2_role"],
        })
        substrate.add_edge(agent, "operation_request", request)
    except Exception:
        guard._phase = "locked"
        raise
    guard.finish_held_out_submission()
    return request


def graph_snapshot(substrate: Any) -> dict[str, Any]:
    """Deterministically serialize observable graph data for the preregistered artifacts."""
    inner = substrate._inner
    nodes = sorted(inner.nodes(), key=str)
    node_rows = [{"id": str(node), "type": inner.node(node)["type"], "attrs": inner.node(node).get("attrs", {})}
                 for node in nodes]
    edges = []
    for source in nodes:
        for edge_type in EDGE_TYPES:
            for target in sorted(inner.neighbours(source, edge_type), key=str):
                edges.append({"src": str(source), "type": edge_type, "tgt": str(target)})
    return {"nodes": node_rows, "edges": sorted(edges, key=lambda edge: (edge["src"], edge["type"], edge["tgt"]))}


def structural_graph_snapshot(substrate: Any) -> dict[str, Any]:
    """Project a graph to structural fields/topology, intentionally erasing opaque labels."""
    inner = substrate._inner
    nodes = list(inner.nodes())

    def signature(node: Any) -> str:
        data = inner.node(node)
        attrs = {key: value for key, value in data.get("attrs", {}).items() if key not in _OPAQUE_ATTR_KEYS}
        return json.dumps({"type": data["type"], "attrs": attrs}, sort_keys=True, default=str)

    edges = [
        {"src": signature(source), "type": edge_type, "tgt": signature(target)}
        for source in nodes for edge_type in EDGE_TYPES for target in inner.neighbours(source, edge_type)
    ]
    return {
        "nodes": sorted(signature(node) for node in nodes),
        "edges": sorted(edges, key=lambda edge: (edge["src"], edge["type"], edge["tgt"])),
    }


def rule_inventory(substrate: Any) -> dict[str, Any]:
    rules = [rule for rule in substrate._inner.export_rules() if isinstance(rule, dict)]
    names = sorted(rule.get("name") for rule in rules if rule.get("name"))
    return {"rules": names, "counts": {name: names.count(name) for name in sorted(set(names))}}


def counts(substrate: Any) -> dict[str, int]:
    return {kind: len(list(substrate.nodes(kind))) for kind in (
        "ResidualSegmentEvidence", "PredicateRecurrenceCandidate", "Observation", "CapabilityAxis",
    )}
