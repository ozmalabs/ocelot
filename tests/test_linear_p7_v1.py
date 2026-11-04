"""Allocation and self-check contract for the registered P7 runner."""
from evaluation.process_mastery.linear_p7_v1 import SEED_BLOCKS, run
from evaluation.process_mastery.analyze_linear_p7_v1 import analyze


def test_p7_development_adapters_return_real_outcomes():
    payload = run(self_check=True)
    assert payload["metadata"]["registered_draw"] is False
    assert len(payload["records"]) == 7
    assert all(row.get("status") in {"COMPLETED", "UNSUPPORTED"}
               for row in payload["records"])
    assert any(row["family"] == "qualia_tool" and
               row["profile"] == "experience-built" and
               row["outcome"] == "validated_distinction" for row in payload["records"])
    summary = analyze(payload)
    assert summary["n_records"] == 7


def test_p7_registered_seed_blocks_are_disjoint_and_frozen():
    spans = sorted((start, start + size, name) for name, (start, size) in SEED_BLOCKS.items())
    for (start, end, name), (next_start, _, next_name) in zip(spans, spans[1:]):
        assert end <= next_start, (name, next_name)
    assert SEED_BLOCKS["qualia_tool"][1] * 5 == 200
    assert SEED_BLOCKS["qualia_social"][1] * 5 == 200
