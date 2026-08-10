"""distributed_systems Mt + 8 decomposition packs."""
from __future__ import annotations

import pytest
from substrate_rs import _native


_NODE_TYPES = (
    "Microtheory", "Concept", "Rule",
    "DesignPattern", "ProgrammingLanguage", "CodeTarget",
    "DesignExclusion", "LanguageExclusion", "LanguageScoringConfig",
    "CodeWritingCortex", "CodeAuthoringRoot", "Reflex",
    "ReplacementTarget", "CodeDraft", "ValidationResult",
    "CodeInstallation",
)
_EDGE_TYPES = (
    "genlMt", "has_concept", "has_rule", "owns_microtheory",
    "owns_root", "has_reflex", "current_target", "has_draft",
    "validated_by", "installed_as", "authored_in", "uses_pattern",
    "subClassOf", "in_category", "decomposes",
)


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et, "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    s.add_node("Microtheory", {"name": "compiler_theory"})
    return s


def test_ds_installs_with_genlmt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "distributed_systems")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "distributed_systems"
    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "compiler_theory" in parents


def test_ds_carries_architecture():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "distributed_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("monolith_vs_microservices",
                     "fallacies_of_distributed_computing",
                     "service_mesh", "sidecar_pattern", "API_gateway",
                     "BFF_backend_for_frontend"):
        assert required in names


def test_ds_carries_resilience():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "distributed_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("circuit_breaker", "bulkhead_pattern",
                     "retry_with_backoff", "jitter",
                     "timeout_propagation", "fail_fast_principle",
                     "graceful_degradation"):
        assert required in names


def test_ds_carries_consistency_patterns():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "distributed_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("saga_pattern", "saga_choreography",
                     "saga_orchestration", "event_sourcing", "CQRS",
                     "two_phase_commit_2PC", "TCC_try_confirm_cancel",
                     "idempotency_distributed",
                     "exactly_once_semantics",
                     "at_most_once_delivery",
                     "at_least_once_delivery"):
        assert required in names


def test_ds_carries_logical_time():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "distributed_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("lamport_timestamp", "vector_clock",
                     "hybrid_logical_clock", "NTP_clock_sync",
                     "TrueTime_Spanner"):
        assert required in names


def test_ds_carries_failure_detection():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "distributed_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("heartbeat_failure_detection", "gossip_protocol",
                     "phi_accrual_failure_detector", "SWIM_protocol"):
        assert required in names


def test_ds_carries_service_communication():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "distributed_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("service_discovery", "load_balancer_L4",
                     "load_balancer_L7", "sticky_session",
                     "liveness_probe", "readiness_probe",
                     "graceful_shutdown", "rate_limiting_token_bucket",
                     "rate_limiting_leaky_bucket",
                     "distributed_rate_limiting", "backpressure",
                     "distributed_locking_Redlock"):
        assert required in names


def test_ds_carries_observability():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "distributed_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("distributed_tracing", "trace_context_propagation",
                     "structured_logging", "metrics_prometheus_style",
                     "three_pillars_observability"):
        assert required in names


def test_ds_carries_SRE():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "distributed_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("SLO", "SLA", "SLI", "error_budget",
                     "RED_method", "USE_method", "chaos_engineering",
                     "canary_deployment", "blue_green_deployment",
                     "feature_flag", "blameless_postmortem"):
        assert required in names


def test_ds_carries_scaling_messaging():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "distributed_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("distributed_cache_pattern", "cache_aside_pattern",
                     "write_through_cache", "write_behind_cache",
                     "CDN_edge_caching", "geo_replication",
                     "multi_region_failover", "anycast_routing",
                     "horizontal_vs_vertical_scaling", "stateless_design",
                     "messaging_queue_pattern", "pub_sub_pattern",
                     "dead_letter_queue"):
        assert required in names


def test_ds_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "distributed_systems")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_ds_decomposition_packs_load():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    load_one_seed(s, "distributed_systems")
    ids = install_all_concept_expansions(s)
    for required in ("service_mesh_internals_decomposition",
                     "distributed_tracing_decomposition",
                     "resilience_patterns_decomposition",
                     "saga_event_sourcing_decomposition",
                     "logical_time_decomposition",
                     "failure_detection_decomposition",
                     "distributed_transactions_decomposition",
                     "sre_observability_decomposition",
                     "messaging_patterns_decomposition"):
        assert required in ids, f"DS pack {required!r} not loaded"


def test_total_ds_concept_count():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "distributed_systems")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 175, f"only {n_concepts} concepts"
    assert n_rules >= 55, f"only {n_rules} rules"
