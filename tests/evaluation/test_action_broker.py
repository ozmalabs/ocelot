from conftest import broker, grant, raw, request


def test_p0a_is_real_default_deny_even_for_valid_fixture_request(tmp_path):
    target = broker(tmp_path, p0=True); req = request(target.manifest.run_id); cap = grant(req)
    reply = target.submit_action(raw(req), raw(cap))
    assert reply.phase == "denied" and target.state["counter"] == 0


def test_malformed_noncanonical_unknown_and_host_like_requests_never_invoke(tmp_path):
    target = broker(tmp_path)
    assert target.submit_action(b'{"schema":"ActionRequestV1"}', None).phase == "denied"
    req = request(target.manifest.run_id, method="dispatch", args={"url": "https://x"})
    assert target.submit_action(raw(req), raw(grant(req))).phase == "denied"
    assert target.state["counter"] == 0
