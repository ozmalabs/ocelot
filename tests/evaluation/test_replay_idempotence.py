from conftest import broker, grant, raw, request


def test_request_nonce_and_grant_replay_leave_exactly_one_effect(tmp_path):
    target = broker(tmp_path); req = request(target.manifest.run_id); cap = grant(req)
    assert target.submit_action(raw(req), raw(cap)).phase == "accepted"
    assert target.submit_action(raw(req), raw(cap)).phase == "denied"
    assert target.state["counter"] == 2
    assert len((tmp_path / "receipts.ndjson").read_text().splitlines()) == 2
