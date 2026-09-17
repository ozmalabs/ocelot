from evaluation.p5_r0.rollback import Snapshot

def test_snapshot_restore_is_exact_after_nested_mutation():
    state = {"graph": {"nodes": [{"value": 1}]}, "codebook": {"token": "opaque"}}
    snapshot = Snapshot(state)
    state["graph"]["nodes"][0]["value"] = 99
    state["codebook"]["token"] = "changed"
    assert snapshot.restore(state) == snapshot.digest
    assert state == {"graph": {"nodes": [{"value": 1}]}, "codebook": {"token": "opaque"}}
