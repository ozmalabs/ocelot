from evaluation.p5_r0.domain_cards import create_domain_cards
from evaluation.p5_r0.split import build_split_commitment, build_case_index, build_taxonomy, validate_taxonomy

def test_exact_factorized_case_index_is_disjoint_and_held_out_is_combinatorial():
    cards = create_domain_cards(); split = build_split_commitment(); rows = build_case_index(split, cards)
    assert len(rows) == 48
    assert len({r["case_digest"] for r in rows}) == 48
    assert len({r["source_commitment"] for r in rows}) == 48
    assert {r["combination_id"] for r in rows if r["split"] == "held_out"} == {"H01", "H02"}
    assert validate_taxonomy(build_taxonomy())["taxonomy_digest"]
