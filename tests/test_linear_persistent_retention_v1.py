from evaluation.process_mastery.analyze_linear_p25_v1 import analyze
from evaluation.process_mastery.linear_p25_v1 import (
    ARMS,
    CONTROL_KINDS,
    _digest,
    allocation,
    provenance,
    run_development,
)


def test_p25_allocations_are_deterministic_and_disjoint():
    development = allocation("development", streams_per_cell=2,
                              controls_per_kind=1)
    heldout = allocation("heldout")
    assert development == allocation("development", streams_per_cell=2,
                                     controls_per_kind=1)
    assert heldout == allocation("heldout")
    development_seeds = {
        seed for cell in development["stream_cells"] for seed in cell["seeds"]
    } | {seed for seeds in development["control_seeds"].values() for seed in seeds}
    heldout_seeds = {
        seed for cell in heldout["stream_cells"] for seed in cell["seeds"]
    } | {seed for seeds in heldout["control_seeds"].values() for seed in seeds}
    assert development_seeds.isdisjoint(heldout_seeds)
    assert sum(map(lambda cell: len(cell["stream_ids"]), heldout["stream_cells"])) == 1200
    assert sum(map(len, heldout["control_seeds"].values())) == 300
    assert len(_digest(heldout)) == 64


def test_p25_development_panel_preserves_paired_events_and_controls():
    payload = run_development(streams_per_cell=1, controls_per_kind=1)
    result = analyze(payload)
    assert payload["split"] == "development"
    assert payload["heldout_accessed"] is False
    assert result["analysis_status"] == "VALID", result["structural_failures"]
    assert result["row_count"] == 6 * len(ARMS)
    assert result["control_count"] == len(CONTROL_KINDS)
    assert result["primary"]["status"] == "development_only"


def test_p25_analyzer_rejects_arm_event_mismatch():
    payload = run_development(streams_per_cell=1, controls_per_kind=1)
    payload["streams"][1]["target_receipt_ids"] = ["mismatched"]
    result = analyze(payload)
    assert result["analysis_status"] == "INVALID"
    assert any(item.startswith("target_receipt_parity:")
               for item in result["structural_failures"])


def test_p25_runtime_is_attested():
    attestation = provenance()["runtime_attestation"]
    assert attestation["status"] == "ATTESTED"
    assert attestation["build_sources_match"] is True
    assert attestation["native_symbols_bound"] is True
