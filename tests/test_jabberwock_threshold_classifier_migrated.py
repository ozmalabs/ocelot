"""The Jabberwock can now author the previously unreachable classifier."""
from scripts.jabberwock_build_threshold_classifier import build_artifact


def test_jabberwock_authors_general_threshold_classifier():
    artifact = build_artifact()

    assert artifact["status"] == "accepted"
    assert artifact["policy_owner"] == "rust_graph"
    assert artifact["rendered_term"] == (
        "(micros * (processed > (progress * threshold)))"
    )
    assert artifact["synthesis"]["operator_shape"] == (
        "thresholded_greater_branch"
    )
    assert artifact["synthesis"]["ops"] == [
        "Times", "Gt", "IfThenElse"
    ]
    assert artifact["synthesis"]["grounded_constants"] == [0]
    assert artifact["synthesis"]["solution_size"] == 7
    assert artifact["held_out_pass_count"] == artifact["held_out_count"] == 5
