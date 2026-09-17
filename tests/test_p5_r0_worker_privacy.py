from evaluation.p5_r0.domain_cards import create_domain_cards
from evaluation.p5_r0.fixture_generator import generate_fixtures, worker_view
from evaluation.p5_r0.split import build_split_commitment

def test_worker_view_contains_no_truth_family_split_or_receipt_path():
    bundle = generate_fixtures(build_split_commitment(), create_domain_cards())
    case = bundle["case_index"][0]
    view = worker_view(case, task_nonce="nonce")
    assert set(view) == {"schema", "case_token", "task_nonce", "observation", "legal_actions", "protocol_budget"}
    assert "truth" not in view and "private_domain_family" not in view and "split" not in view
