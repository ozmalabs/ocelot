from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from evaluation.p5_r0.receipts import ReceiptChain
from evaluation.p5_r0.rollback import Snapshot, rollback_receipt

def test_receipts_chain_and_exact_restore(tmp_path):
    chain = ReceiptChain(tmp_path / "receipts", Ed25519PrivateKey.generate())
    first = chain.append(run_id="r", kind="terminal", outcome="complete_correct", binding={})
    second = chain.append(run_id="r", kind="rollback", outcome="restored", binding={})
    assert second["previous_hash"] == first["receipt_hash"]
    state = {"nested": {"x": [1]}}
    snap = Snapshot(state); state["nested"]["x"].append(2)
    restored = snap.restore(state)
    assert restored == snap.digest and state == {"nested": {"x": [1]}}
    assert rollback_receipt(run_id="r", pre_snapshot=snap.digest, restored_snapshot=restored, chain_digest=chain.digest)["exact"]
