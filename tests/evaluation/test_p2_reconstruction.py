"""Injection seams are explicitly non-release unit scaffolding only."""
from __future__ import annotations
import pytest
from evaluation.p2.protocol import P2ProtocolError
from evaluation.p2.runner import P2Runner, P2UnitRunner
from test_p2_protocol import envelope, proposal

def test_unit_scaffold_denies_before_broker_when_reconstruction_rejects():
    calls=[]
    runner=P2UnitRunner(lambda _e,_p:{"accepted":False},lambda req:calls.append(req) or {"brokered":True})
    assert runner.score(envelope(),proposal()) == {"classification":"protocol_error","success_credit":0,"brokered":False}
    assert not calls

def test_unit_scaffold_can_exercise_broker_contract_without_release_authority():
    calls=[]; runner=P2UnitRunner(lambda _e,_p:{"accepted":True},lambda req:calls.append(req) or {"brokered":True})
    expected=proposal()["proposal_digest"]
    assert runner.score(envelope(),proposal()) == {"brokered":True}
    assert calls == [{"action_id":"a","proposal_digest":expected,"idempotency_key":expected}]

def test_release_runner_has_no_injected_reconstructor_api():
    with pytest.raises(TypeError):
        P2Runner(lambda _env, _proposal: {"accepted": True})
