"""network_protocols Mt + 9 decomposition packs."""
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


def test_network_protocols_installs_with_genlmt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "network_protocols")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "network_protocols"
    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "compiler_theory" in parents


def test_network_protocols_carries_foundation():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "network_protocols")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("layered_model", "OSI_seven_layer",
                     "TCP_IP_four_layer", "encapsulation",
                     "MTU_maximum_transmission_unit",
                     "MSS_maximum_segment_size",
                     "packet", "frame", "middlebox"):
        assert required in names, f"missing foundation {required!r}"


def test_network_protocols_carries_transport():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "network_protocols")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("TCP", "UDP", "QUIC", "SCTP",
                     "TCP_three_way_handshake",
                     "TCP_congestion_control",
                     "TCP_slow_start", "TCP_fast_retransmit",
                     "TCP_selective_ack", "TCP_window_scaling",
                     "head_of_line_blocking"):
        assert required in names


def test_network_protocols_carries_security():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "network_protocols")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("TLS_1_3", "TLS_handshake", "X509_certificate",
                     "certificate_transparency", "HTTPS",
                     "DDoS", "BGP_hijacking", "RPKI"):
        assert required in names


def test_network_protocols_carries_application_protocols():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "network_protocols")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("HTTP_1_1", "HTTP_2", "HTTP_3",
                     "HPACK_header_compression",
                     "QPACK_header_compression",
                     "DNS", "WebSocket", "gRPC",
                     "Protocol_Buffers", "MQTT", "AMQP",
                     "Kafka_protocol", "WebRTC",
                     "STUN_NAT_traversal", "TURN_relay",
                     "CoAP"):
        assert required in names


def test_network_protocols_carries_routing():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "network_protocols")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("IP_routing", "BGP", "OSPF", "IS_IS",
                     "NAT", "NAT64"):
        assert required in names


def test_network_protocols_carries_datacenter_networking():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "network_protocols")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("load_balancer_L4", "load_balancer_L7",
                     "anycast", "ECMP", "VXLAN", "RDMA", "RoCE",
                     "InfiniBand", "DPDK", "XDP", "service_mesh",
                     "CDN"):
        assert required in names


def test_network_protocols_carries_performance():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "network_protocols")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("BBR_congestion_control", "CUBIC_congestion_control",
                     "bufferbloat", "TSO_GSO_offload",
                     "GRO_receive_offload", "RSS",
                     "MPTCP"):
        assert required in names


def test_network_protocols_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "network_protocols")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_network_decomposition_packs_load():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    load_one_seed(s, "network_protocols")
    ids = install_all_concept_expansions(s)
    for required in ("tcp_congestion_control_decomposition",
                     "tls_handshake_decomposition",
                     "http2_decomposition",
                     "quic_decomposition",
                     "bgp_routing_decomposition",
                     "dns_resolution_decomposition",
                     "linux_network_stack_decomposition",
                     "rdma_decomposition",
                     "service_mesh_decomposition"):
        assert required in ids, f"net pack {required!r} not loaded"


def test_network_pack_sub_mechanisms_mount():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "network_protocols")
    install_all_concept_expansions(s)
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    # TCP CC pack
    for n in ("congestion_window", "AIMD_additive_increase_multiplicative_decrease",
              "slow_start_phase", "AIMD_additive_increase_multiplicative_decrease",
              "fast_recovery", "BBR_bandwidth_estimation",
              "BBR_RTT_estimation", "ECN_explicit_congestion_notification"):
        assert n in names
    # TLS pack
    for n in ("client_hello_message", "key_share_extension",
              "ECDHE_key_exchange", "HKDF_key_derivation",
              "certificate_chain", "finished_message",
              "PSK_session_resumption", "zero_RTT_early_data",
              "AEAD_cipher"):
        assert n in names
    # HTTP/2 pack
    for n in ("binary_framing_layer", "stream_concept", "frame_types",
              "HPACK_static_table", "HPACK_dynamic_table",
              "stream_prioritisation", "flow_control_window",
              "HOL_blocking_at_TCP_level"):
        assert n in names
    # QUIC pack
    for n in ("QUIC_over_UDP", "connection_ID", "stream_frames",
              "per_stream_reliability",
              "packet_number_independent_of_data",
              "connection_migration", "path_validation",
              "amplification_limit"):
        assert n in names
    # BGP pack
    for n in ("autonomous_system", "BGP_session", "UPDATE_message",
              "AS_PATH_attribute", "NEXT_HOP_attribute", "LOCAL_PREF",
              "BGP_best_path_selection", "iBGP_full_mesh",
              "route_reflector", "RPKI_validation"):
        assert n in names
    # DNS pack
    for n in ("stub_resolver", "recursive_resolver", "root_servers",
              "TLD_servers", "authoritative_server",
              "TTL_caching_lifetime", "DNSSEC_signatures",
              "EDNS0_extension", "DoH_DNS_over_HTTPS"):
        assert n in names
    # Linux stack pack
    for n in ("NAPI_poll", "GRO_coalescing", "sk_buff",
              "netfilter_hooks", "qdisc_queueing_discipline",
              "io_uring_async_io", "XDP_eXpress_Data_Path",
              "eBPF_kernel_programming"):
        assert n in names
    # RDMA pack
    for n in ("verbs_API", "queue_pair", "memory_region_registration",
              "RDMA_write_operation", "RDMA_read_operation",
              "RDMA_atomic_operations", "completion_queue",
              "DCQCN_congestion_control", "PFC_priority_flow_control"):
        assert n in names
    # Service mesh pack
    for n in ("sidecar_proxy", "control_plane", "xDS_protocol",
              "mTLS_between_services", "service_identity",
              "circuit_breaker", "retry_with_budget",
              "outlier_detection", "distributed_tracing_injection",
              "ambient_mode_layer4_proxy"):
        assert n in names


def test_total_network_concept_count():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "network_protocols")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 180, f"only {n_concepts} concepts"
    assert n_rules >= 55, f"only {n_rules} rules"
