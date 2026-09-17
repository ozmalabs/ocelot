from __future__ import annotations
from evaluation.p2.protocol import validate_proposal
from test_p2_protocol import envelope, proposal

def test_basis_point_distribution_is_complete_for_every_legal_action():
    p=validate_proposal(proposal(),envelope())
    assert all(sum(record["outcome_basis_points"].values()) == 10_000 for record in p["predictions"])
def test_tie_set_is_explicit_and_not_collapsed_to_input_order():
    p=proposal(); p["selection"]["native_tie_set"]=["b","a"]
    from evaluation.p0a.canonical import object_hash
    p["proposal_digest"]=object_hash({k:v for k,v in p.items() if k != "proposal_digest"})
    assert set(validate_proposal(p,envelope())["selection"]["native_tie_set"]) == {"a","b"}
