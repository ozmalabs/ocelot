from conftest import broker, grant, raw, request


def test_absent_expired_quota_and_revoked_grants_deny(tmp_path):
    target = broker(tmp_path); req = request(target.manifest.run_id)
    assert target.submit_action(raw(req), None).phase == "denied"
    assert target.submit_action(raw(req), raw(grant(req, expires=0))).phase == "denied"
    assert target.submit_action(raw(req), raw(grant(req, uses=2))).phase == "denied"
    assert target.submit_action(raw(req), raw(grant(req, revocation=1))).phase == "denied"
    assert target.state["counter"] == 0


def test_signed_grant_cannot_be_substituted_for_another_valid_request_arguments(tmp_path):
    target = broker(tmp_path)
    authorized = request(target.manifest.run_id, args={"steps": 2})
    substituted = request(target.manifest.run_id, request_id="123e4567-e89b-42d3-a456-426614174009",
                          nonce="B" * 43, args={"steps": 3})
    signed_for_authorized = grant(authorized)
    reply = target.submit_action(raw(substituted), raw(signed_for_authorized))
    assert reply.phase == "denied"
    assert target.state["counter"] == 0
