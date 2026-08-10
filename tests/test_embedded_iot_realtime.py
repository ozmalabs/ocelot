"""embedded_iot_realtime Mt + 8 decomposition packs."""
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


def test_eiot_installs_with_genlmt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "embedded_iot_realtime")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "embedded_iot_realtime"
    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "compiler_theory" in parents


def test_eiot_carries_rt_foundation():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "embedded_iot_realtime")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("hard_realtime", "soft_realtime", "firm_realtime",
                     "determinism", "worst_case_execution_time",
                     "jitter", "latency_RT"):
        assert required in names


def test_eiot_carries_rtos():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "embedded_iot_realtime")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("FreeRTOS", "Zephyr", "VxWorks", "QNX",
                     "PREEMPT_RT"):
        assert required in names


def test_eiot_carries_rt_scheduling():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "embedded_iot_realtime")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("rate_monotonic_scheduling",
                     "earliest_deadline_first", "deadline_monotonic",
                     "schedulability_analysis",
                     "priority_inheritance_RT",
                     "priority_ceiling_protocol",
                     "rate_monotonic_utilisation_bound"):
        assert required in names


def test_eiot_carries_microcontrollers():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "embedded_iot_realtime")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("ARM_Cortex_M", "RISC_V_embedded", "ESP32",
                     "STM32", "AVR_8_bit", "RP2040"):
        assert required in names


def test_eiot_carries_peripherals():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "embedded_iot_realtime")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("GPIO", "I2C", "SPI", "UART", "ADC_resolution",
                     "DAC", "PWM"):
        assert required in names


def test_eiot_carries_iot_protocols():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "embedded_iot_realtime")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("MQTT_pubsub", "MQTT_QoS_levels", "CoAP",
                     "LwM2M", "BLE_GATT", "Zigbee", "Thread",
                     "Matter", "6LoWPAN", "LoRaWAN",
                     "NB_IoT_LTE_M", "Sigfox"):
        assert required in names


def test_eiot_carries_rt_communication():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "embedded_iot_realtime")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("CAN_bus", "LIN_bus", "FlexRay",
                     "Time_Sensitive_Networking_TSN", "EtherCAT",
                     "PROFINET", "OPC_UA", "DDS_data_distribution"):
        assert required in names


def test_eiot_carries_robotics():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "embedded_iot_realtime")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("ROS2", "micro_ROS", "ROS2_QoS_profiles",
                     "URDF_robot_description"):
        assert required in names


def test_eiot_carries_sensors_actuators_fusion():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "embedded_iot_realtime")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("IMU", "LIDAR", "time_of_flight_sensor",
                     "rotary_encoder", "event_camera", "BLDC_motor",
                     "servo_motor", "stepper_motor", "Kalman_filter",
                     "complementary_filter", "particle_filter"):
        assert required in names


def test_eiot_carries_embedded_ml_safety():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "embedded_iot_realtime")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("TinyML", "TFLite_Micro", "ML_quantization_embedded",
                     "DO_178C_avionics", "ISO_26262_automotive",
                     "IEC_61508", "ASIL_levels", "MISRA_C",
                     "formal_verification_embedded",
                     "triple_modular_redundancy", "lockstep_CPUs",
                     "watchdog_kick_pattern", "fail_safe_design"):
        assert required in names


def test_eiot_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "embedded_iot_realtime")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_eiot_decomposition_packs_load():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    load_one_seed(s, "embedded_iot_realtime")
    ids = install_all_concept_expansions(s)
    for required in ("rtos_internals_decomposition",
                     "wcet_schedulability_decomposition",
                     "cortex_m_decomposition",
                     "iot_protocols_deep_decomposition",
                     "ros2_dds_decomposition",
                     "sensor_fusion_decomposition",
                     "embedded_ml_tinyml_decomposition",
                     "safety_critical_embedded_decomposition",
                     "embedded_communication_decomposition"):
        assert required in ids, f"eIoT pack {required!r} not loaded"


def test_total_eiot_concept_count():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "embedded_iot_realtime")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 195, f"only {n_concepts} concepts"
    assert n_rules >= 55, f"only {n_rules} rules"
