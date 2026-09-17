from conftest import broker, grant, raw, request


def test_fixture_simulator_is_deterministic_and_has_no_io_usage(tmp_path):
    left = broker(tmp_path / "left"); right = broker(tmp_path / "right")
    for target in (left, right):
        req = request(target.manifest.run_id); reply = target.submit_action(raw(req), raw(grant(req)))
        assert reply.phase == "accepted"
    assert left.state == right.state == {"counter": 2}
    receipt = (tmp_path / "left" / "receipts.ndjson").read_text()
    assert '"network_bytes":0' in receipt and '"writes":0' in receipt
