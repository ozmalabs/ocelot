from evaluation.p5_r0.baselines import exact_memorizer, label_blind_random
from evaluation.p5_r0.permutations import label_permutation, inverse_normalize, altered_semantics
from evaluation.p5_r0.domain_cards import create_domain_cards
from evaluation.p5_r0.fixture_generator import generate_fixtures
from evaluation.p5_r0.split import build_split_commitment

def test_baselines_are_provenance_bound_and_unseen_memorizer_abstains():
    bundle = generate_fixtures(build_split_commitment(), create_domain_cards())
    train = {r["case_digest"] for r in bundle["case_index"] if r["split"] == "train"}
    held = next(r for r in bundle["case_index"] if r["split"] == "held_out")
    assert exact_memorizer(train, held["case_digest"])["action"] == "abstain"
    assert label_blind_random(2, ["a", "b"])["action"] == "a"

def test_semantics_preserving_permutation_normalizes_and_alteration_changes_commitment():
    perm = label_permutation(["a", "b", "c"])
    assert inverse_normalize(perm["mapping"]["a"], perm) == "a"
    case = next(iter(generate_fixtures(build_split_commitment(), create_domain_cards())["case_index"]))
    assert altered_semantics(case)["case_digest"] != case["case_digest"]
