from evaluation.p0a.canonical import object_hash
from evaluation.p3.protocol import P3ProtocolError, validate_learning_proposal
import pytest

def digest(n): return 'sha256:' + n * 64
def proposal():
    p={"schema":"LearningProposalV1","parent_snapshot_digest":digest('1'),"mutable_artifact":{"path":"mutable-agent/rules.json","object_digest":digest('2')},"change":{"kind":"rule","patch_digest":digest('3')},"provenance_refs":[digest('4')],"evidence_refs":[digest('5')],"rollback_snapshot_digest":digest('6'),"status":"proposed"}; p['proposal_digest']=object_hash(p); return p
@pytest.mark.parametrize('field', ['broker_image','grant_schema','policy_authority','receipt_writer','result_channel','evaluator_key','scoring_oracle','task_release_order','held_out_seed','split','mount_mode','resource_budget','heartbeat','kill','stop'])
def test_control_plane_reference_denied(field):
    p=proposal(); p['change']['%s' % field]=digest('a')
    p['proposal_digest']=object_hash({k:v for k,v in p.items() if k!='proposal_digest'})
    with pytest.raises(P3ProtocolError): validate_learning_proposal(p)
def test_only_proposed_data_plane_is_valid(): assert validate_learning_proposal(proposal())['status']=='proposed'
