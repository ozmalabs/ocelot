from __future__ import annotations

import importlib.util

import pytest

from evaluation.research_assistant.categorical_interop import (
    SOURCE_IDS,
    OptionalDependencyUnavailable,
    run_experiment,
)


def _optional_stack_available() -> bool:
    return (importlib.util.find_spec("discopy") is not None
            and importlib.util.find_spec("substrate_rs") is not None)


@pytest.mark.skipif(not _optional_stack_available(),
                    reason="DisCoPy and substrate_rs are optional experiment dependencies")
def test_bounded_chain_and_left_identity_keep_source_ids():
    result = run_experiment()
    assert result["status"] == "completed"
    assert result["discopy"]["chain_dom"] == "X"
    assert result["discopy"]["chain_cod"] == "Z"
    assert result["discopy"]["chain_boxes"] == ["f", "g"]
    assert result["discopy"]["identity_law_equal_to_f"] is True
    assert len(result["substrate"]["composed_path"]) == 1
    assert len(result["substrate"]["identity_path_witness"]) == 1
    assert result["comparison"]["all_source_ids_preserved"] is True
    assert set(result["comparison"]["preserved_source_ids"]) == set(SOURCE_IDS.values())
    assert result["comparison"]["equivalence_claimed"] is False


def test_missing_optional_dependency_has_a_specific_result():
    # The command line wrapper converts this typed exception to a machine
    # readable skipped status; this test pins the missing-dependency contract.
    if _optional_stack_available():
        pytest.skip("optional dependencies are installed in this environment")
    with pytest.raises(OptionalDependencyUnavailable, match="optional"):
        run_experiment()
