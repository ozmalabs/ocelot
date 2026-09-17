from evaluation.p3.admission import reject_and_rollback
from evaluation.p3.receipts import P3ReceiptLog
from p3_fixtures import ready

def test_rejection_restores_exact_preproposal_bytes(tmp_path):
 bundle=ready(tmp_path); bundle['candidate'].write_bytes(b'harm')
 record=reject_and_rollback(candidate=bundle['candidate'],pre_snapshot=bundle['pre'],receipt_log=P3ReceiptLog(tmp_path/'r',bundle['lock_key']),lock=bundle['lock'],proposal_digest=None,reason='inconclusive')
 assert bundle['candidate'].read_bytes()==bundle['pre'].read_bytes() and record['kind']=='rollback'
def test_rollback_rejects_symlink_target(tmp_path):
 bundle=ready(tmp_path); target=tmp_path/'target'; target.write_bytes(b'control'); bundle['candidate'].unlink(); bundle['candidate'].symlink_to(target)
 import pytest
 from evaluation.p3.protocol import P3ProtocolError
 with pytest.raises(P3ProtocolError): reject_and_rollback(candidate=bundle['candidate'],pre_snapshot=bundle['pre'],receipt_log=P3ReceiptLog(tmp_path/'r',bundle['lock_key']),lock=bundle['lock'],proposal_digest=None,reason='bad')
 assert target.read_bytes()==b'control'



def test_rollback_failure_is_signed_terminal_impasse_not_a_swallowed_denial(tmp_path):
 from evaluation.p3.admission import terminal_rollback_impasse
 bundle=ready(tmp_path); target=tmp_path/'target'; target.write_bytes(b'control'); bundle['candidate'].unlink(); bundle['candidate'].symlink_to(target)
 log=P3ReceiptLog(tmp_path/'impasse',bundle['lock_key'])
 record=terminal_rollback_impasse(candidate=bundle['candidate'],pre_snapshot=bundle['pre'],receipt_log=log,lock=bundle['lock'],proposal_digest=bundle['proposal']['proposal_digest'],cause=RuntimeError('restore failed'))
 assert record['kind']=='impasse' and record['payload']['terminal_evidence']['schema']=='P3RollbackImpasseEvidenceV1'
 assert record['payload']['terminal_evidence']['observed_candidate_digest'] is None and log.sequence==1
