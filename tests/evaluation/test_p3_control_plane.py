"""Real candidate mutation attempts must die before staging or evaluator execution."""
import pytest
from evaluation.p0a.canonical import canonical_bytes
from evaluation.p3.admission import P3ReadinessRequestV1
from evaluation.p3.receipts import P3ReceiptLog
from evaluation.p3.runner import P3R0Runner
from p3_fixtures import mutable_candidate, ready

def _request(bundle, tmp_path):
 return P3ReadinessRequestV1(bundle['p0'],bundle['p1'],bundle['p2'],bundle['lock'].body['native_export_digest'],bundle['lock'].body['candidate_digest'],bundle['pre'],bundle['candidate'],tmp_path/'stage')
def _runner(bundle,tmp_path):
 return P3R0Runner(bundle['lock'],P3ReceiptLog(tmp_path/'receipts',bundle['lock_key']),{'p2-local':bundle['p2_key'].public_key()},{'p0-local':bundle['p0_key'].public_key()},{'p1-local':bundle['p1_key'].public_key()})
@pytest.mark.parametrize('artifact', ['broker_image','grant_schema','policy_authority_image','p3_schemas','native_evaluator','benchmark_grammar','resource_limits','kill_supervisor_policy'])
def test_direct_and_transitive_control_mutation_is_denied_before_staging(tmp_path,artifact):
 # This is a real candidate payload under the lock's own digest, not an unknown proposal field.
 from evaluation.p3.lock import ARTIFACT_NAMES
 from p3_fixtures import digest
 locked_digest=digest(f"{(ARTIFACT_NAMES.index(artifact) % 9) + 1:x}")
 raw=mutable_candidate({'mutation': {'transitive': [{'artifact_digest': locked_digest}, {'target': artifact}]}})
 bundle=ready(tmp_path,candidate_bytes=raw)
 out=_runner(bundle,tmp_path).run(_request(bundle,tmp_path),proposal=bundle['proposal'])
 assert out['kind']=='denial' and not (tmp_path/'stage').exists() and bundle['lock'].artifacts[artifact] == locked_digest

def test_locked_malicious_candidate_payload_is_denied_after_byte_binding_before_stage(tmp_path):
 raw=mutable_candidate({'nested': {'policy': {'stop': 'attempt'}}})
 bundle=ready(tmp_path,candidate_bytes=raw)
 out=_runner(bundle,tmp_path).run(_request(bundle,tmp_path),proposal=bundle['proposal'])
 assert out['kind']=='denial' and out['payload']['reason']=='preflight:P3ProtocolError'
 assert not (tmp_path/'stage').exists() and bundle['candidate'].read_bytes()==raw
