import pytest

from evaluation.process_mastery.cumulative_checkpoint_panel import (
    run_component_knockouts,
)


def test_component_ablation_follows_actual_path_and_preserves_source():
    graph = {"nodes": [
        {"id": "distinction", "attrs": {"p27_component": "learned_distinctions",
                                             "value": "rotate"}},
        {"id": "prior", "attrs": {"p27_component": "shared_transfer_priors",
                                      "value": "identity"}},
    ], "edges": []}
    result = run_component_knockouts(graph=graph,
        world={"world_id": "dev", "split": "development"},
        native_predictor=lambda state, _world: tuple(sorted(
            n["attrs"]["value"] for n in state["nodes"])) )
    assert result["status"] == "COMPLETED"
    assert result["source_graph_unchanged"]
    assert result["outcomes"]["learned_distinctions"]["prediction_changed"]
    assert result["outcomes"]["shared_transfer_priors"]["prediction_changed"]
    assert not result["actionable"]
    assert len(graph["nodes"]) == 2


def test_component_knockout_reports_absent_causal_paths():
    graph = {"nodes": [{"id": "base", "attrs": {"value": "fixed"}}], "edges": []}
    result = run_component_knockouts(graph=graph,
        world={"world_id": "dev", "split": "development"},
        native_predictor=lambda state, _world: len(state["nodes"]))
    assert all(row["status"] == "no_effect_observed"
               for row in result["outcomes"].values())
    assert all(row["removed_nodes"] == 0 for row in result["outcomes"].values())


def test_knockouts_do_not_run_on_sealed_validation_or_heldout():
    for split in ("validation", "heldout"):
        with pytest.raises(ValueError, match="development-only"):
            run_component_knockouts(graph={"nodes": [], "edges": []},
                world={"world_id": "sealed", "split": split},
                native_predictor=lambda _state, _world: None)


def test_no_scoring_feedback_into_training():
    calls = []
    graph = {"nodes": [], "edges": []}
    run_component_knockouts(graph=graph,
        world={"world_id": "dev", "split": "development"},
        native_predictor=lambda state, world: calls.append((state, world)) or "choice")
    assert len(calls) == 5
    assert all(call[0] is not graph for call in calls)
    assert len(graph["nodes"]) == 0


def test_component_names_are_explicit_and_unknown_names_fail_closed():
    with pytest.raises(ValueError, match="unknown causal component"):
        from evaluation.process_mastery.cumulative_checkpoint_panel import ablate_component
        ablate_component({"nodes": []}, "unregistered_component")
