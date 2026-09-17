"""P3 E1 has no in-process executor escape hatch."""
import inspect

from evaluation.p3.admission import P3ReadinessRequestV1
from evaluation.p3.receipts import P3ReceiptLog
from evaluation.p3.runner import P3R0Runner
from p3_fixtures import ready


def test_local_runner_has_no_executor_callback_and_still_rolls_back(tmp_path):
 bundle=ready(tmp_path)
 runner=P3R0Runner(bundle['lock'],P3ReceiptLog(tmp_path/'receipts',bundle['lock_key']),{'p2-local':bundle['p2_key'].public_key()},{'p0-local':bundle['p0_key'].public_key()},{'p1-local':bundle['p1_key'].public_key()})
 request=P3ReadinessRequestV1(bundle['p0'],bundle['p1'],bundle['p2'],bundle['lock'].body['native_export_digest'],bundle['lock'].body['candidate_digest'],bundle['pre'],bundle['candidate'],tmp_path/'stage')
 assert 'executor' not in inspect.signature(runner.run_e1_local_test).parameters
 out=runner.run(request,proposal=bundle['proposal'])
 assert out['kind']=='rollback' and bundle['candidate'].read_bytes()==bundle['pre'].read_bytes()
