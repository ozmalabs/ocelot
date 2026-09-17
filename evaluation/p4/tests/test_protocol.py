from evaluation.p0a.canonical import object_hash
from evaluation.p4.protocol import P4ProtocolError,validate_envelope,validate_proposal
import pytest
def test_closed_envelope_rejects_label_leak():
 v={"schema":"P4R0TaskEnvelopeV1","run_id":"r","sequence":1,"fixture_id":"opaque","logical_time":1,"observation":{"hidden_rule":1},"parent_receipt":None};v["envelope_digest"]=object_hash(v)
 with pytest.raises(P4ProtocolError):validate_envelope(v)
def test_closed_proposal_and_digest():
 v={"schema":"GraphActionProposalV1","proposal_id":"p","run_id":"r","sequence":1,"kind":"inspect","causal_parent_receipt_hash":None,"reservation":{"actions":1,"risk":1,"transactions":1},"graph_digest":"sha256:"+"0"*64};v["proposal_digest"]=object_hash(v);assert validate_proposal(v)==v
