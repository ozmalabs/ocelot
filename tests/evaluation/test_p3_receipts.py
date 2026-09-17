from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest
from evaluation.p0a.canonical import object_hash
from evaluation.p3.protocol import P3ProtocolError
from evaluation.p3.receipts import P3ReceiptLog, receipt_payload


def test_append_only_receipt_chain_survives_restart(tmp_path):
 key=Ed25519PrivateKey.generate(); log=P3ReceiptLog(tmp_path,key); first=log.append('impasse',{'reason':'closed'})
 restarted=P3ReceiptLog(tmp_path,key); assert restarted.sequence==1 and restarted.previous==first['receipt_hash']


def test_terminal_envelope_evidence_is_structural_and_signed_by_the_receipt_chain(tmp_path):
 key=Ed25519PrivateKey.generate(); log=P3ReceiptLog(tmp_path,key)
 digest=lambda char: 'sha256:'+char*64
 bindings={name:digest(char) for name,char in zip(('p0_go_digest','p1_go_digest','p2_go_digest','native_export_digest','candidate_digest','pre_snapshot_digest'),'abcdef')}
 terminal={'schema':'P3EnvelopeTerminalEvidenceV1','lock_digest':digest('a'),'run_id':'r','task_digest':digest('b'),'sequence':2,'reason':'P3ExecutionFailure'}
 terminal['evidence_digest']=object_hash(terminal)
 payload=receipt_payload(lock_digest=digest('a'),proposal_digest=None,outcome='no_go',reason='evaluator_task_envelope_rejected',control_digests={'worker':digest('c')},release_bindings=bindings)
 payload['terminal_evidence']=terminal
 receipt=log.append('terminal',payload)
 assert receipt['kind']=='terminal'
 malformed=dict(payload); malformed['terminal_evidence']=dict(terminal, sequence='two')
 with pytest.raises(P3ProtocolError): log.append('terminal',malformed)
 P3ReceiptLog(tmp_path,key)
