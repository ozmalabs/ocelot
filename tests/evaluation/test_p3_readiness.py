from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from evaluation.p3.admission import P3ReadinessRequestV1
from evaluation.p3.receipts import P3ReceiptLog
from evaluation.p3.runner import P3R0Runner
from p3_fixtures import ready

def request(bundle, tmp_path, *, p0=None, p1=None, p2=None):
 return P3ReadinessRequestV1(bundle['p0'] if p0 is None else p0,bundle['p1'] if p1 is None else p1,bundle['p2'] if p2 is None else p2,bundle['lock'].body['native_export_digest'],bundle['lock'].body['candidate_digest'],bundle['pre'],bundle['candidate'],tmp_path/'stage')
def runner(bundle,tmp_path):
 return P3R0Runner(bundle['lock'],P3ReceiptLog(tmp_path/'receipts',bundle['lock_key']),{'p2-local':bundle['p2_key'].public_key()},{'p0-local':bundle['p0_key'].public_key()},{'p1-local':bundle['p1_key'].public_key()})
def test_absent_signed_p2_go_is_sealed_no_go(tmp_path):
 bundle=ready(tmp_path); out=runner(bundle,tmp_path).run(request(bundle,tmp_path,p2={}),proposal=bundle['proposal'])
 assert out['kind']=='denial' and out['payload']['outcome']=='no_go' and bundle['candidate'].read_bytes()!=bundle['pre'].read_bytes()
def test_all_three_signed_local_go_attestations_stage_then_rollback(tmp_path):
 bundle=ready(tmp_path); out=runner(bundle,tmp_path).run(request(bundle,tmp_path),proposal=bundle['proposal'])
 assert out['kind']=='rollback' and bundle['candidate'].read_bytes()==bundle['pre'].read_bytes()
 staged=tmp_path/'stage'/'candidate.bin'; assert staged.is_file() and staged.stat().st_mode & 0o777 == 0o444
 assert (tmp_path/'stage').stat().st_mode & 0o777 == 0o555
def test_tampered_or_untrusted_p0_p1_go_never_reaches_staging(tmp_path):
 bundle=ready(tmp_path); bad=dict(bundle['p0']); bad['decision']='stop'
 out=runner(bundle,tmp_path).run(request(bundle,tmp_path,p0=bad),proposal=bundle['proposal'])
 assert out['kind']=='denial' and not (tmp_path/'stage').exists()
