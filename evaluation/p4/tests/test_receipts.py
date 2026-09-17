from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from evaluation.p4.receipts import P4ReceiptLog,payload
D="sha256:"+"1"*64
def test_receipt_chain_is_contiguous_signed_and_complete(tmp_path):
 log=P4ReceiptLog(tmp_path,Ed25519PrivateKey.generate());p=payload(run_id="r",lock_digest=D,fixture_digest=D,snapshot_digest=D,outcome="no_go",reason="test",resources={})
 a=log.append("task_release",p);b=log.append("result",p);assert b["previous_hash"]==a["receipt_hash"];P4ReceiptLog(tmp_path,log.public_key).reload()
