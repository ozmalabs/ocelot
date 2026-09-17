from __future__ import annotations
import copy
import pytest
from evaluation.p0a.canonical import canonical_bytes, object_hash, sha256
from evaluation.p2.protocol import P2ProtocolError, validate_envelope, validate_proposal
from p2_fixtures import signed

def envelope():
    return signed({"schema":"P2ObservationEnvelopeV1","run_id":"run","episode_id":"episode","step":0,"observation_atoms":["o0","o1"],"legal_action_ids":["a","b"],"goal_atoms":["g"],"cost_bounds":{"maximum_intervention":9},"budget":{"cpu_ms":2000,"wall_ms":3000,"memory_bytes":536870912,"pids":32,"stdout_bytes":65536,"network_bytes":0,"horizon":1,"branching":1,"nodes_per_action":8},"training_bundle":{"schema":"public"},"signature":"fixture"})
def prediction(action):
    return {"action_id":action,"source_belief_digest":"sha256:"+"a"*64,"transition_witness_digests":["sha256:"+"b"*64],"trajectory_export":{"nodes":[{"kind":"PredictionTrajectory"}]},"outcome_basis_points":{"o0":7500,"o1":2500},"predicted_goal_atoms":["g"],"intervention_cost":1,"manifold":{"support":True,"resolved":True,"loss":0,"information_loss":0,"earliest_decisive_tick":1},"goal_probability_bp":8000,"confidence_bp":8000,"uncertainty_bp":2000,"terminal_status":"predicted"}
def proposal(env=None):
    env=env or envelope(); sealed=sha256(canonical_bytes(env)); out={"schema":"P2NativePlanProposalV1","run_id":"run","episode_id":"episode","envelope_digest":sealed,"verified_input_digest":sealed,"predictions":[prediction("a"),prediction("b")],"selection":{"selected_action_id":"a","classification":"selected","selection_path":"P2BoundedFutureManifoldV1","feasible_action_ids":["a","b"],"minimal_action_ids":["a","b"],"native_tie_set":["a","b"]}}
    out["proposal_digest"]=object_hash(out); return out

def test_accepts_complete_bounded_all_action_proposal():
    env=envelope(); assert validate_proposal(proposal(env), env)["selection"]["selected_action_id"] == "a"
@pytest.mark.parametrize("mutate", [lambda p: p["predictions"].pop(), lambda p: p["predictions"][1].__setitem__("action_id","a"), lambda p: p["predictions"][0]["outcome_basis_points"].__setitem__("o0", 1)])
def test_rejects_incomplete_duplicate_or_nonprobabilistic_predictions(mutate):
    env=envelope(); p=proposal(env); mutate(p); p["proposal_digest"]=object_hash({k:v for k,v in p.items() if k != "proposal_digest"})
    with pytest.raises(P2ProtocolError): validate_proposal(p,env)
def test_rejects_hidden_authority_in_public_bundle():
    env=envelope(); env["training_bundle"]["hidden_state"]="no" 
    with pytest.raises(P2ProtocolError): validate_envelope(env)
