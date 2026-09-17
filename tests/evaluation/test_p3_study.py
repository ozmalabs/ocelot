from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import time
import pytest
from evaluation.p3.study import DISTRIBUTIONS, TaskReleaseLedger, materialize_study, bootstrap_ci, sign_permutation_pvalues, holm, classify
from evaluation.p3.protocol import P3ProtocolError


def test_exact_locked_sequential_materialization():
 key=Ed25519PrivateKey.generate(); lock='sha256:'+'a'*64
 manifest,public,private=materialize_study(seed=b'x'*32,signing_key=key,key_id='task',lock_digest=lock,run_id='r',expires_at=int(time.time())+60)
 assert manifest['distribution_count']==12 and len(public)==12 and len(private)==360
 assert all(len(public[d])==30 for d in DISTRIBUTIONS)
 assert public[DISTRIBUTIONS[0]][0]['sequence']==0
 assert public[DISTRIBUTIONS[-1]][-1]['sequence']==359
 ledger=TaskReleaseLedger({'task':key.public_key()},lock,'r')
 assert ledger.consume(public[DISTRIBUTIONS[0]][0])['sequence']==0
 with pytest.raises(P3ProtocolError): ledger.consume(public[DISTRIBUTIONS[0]][0])


def test_statistics_boundary_and_holm_are_deterministic():
 values=[5000]*30; assert bootstrap_ci(values,seed=7,resamples=20)==(5000,5000)
 assert sign_permutation_pvalues(values,seed=7,permutations=20)[0] <= 1_000_000
 assert holm([10]*12)==[120]*12
 assert classify(5000,(1,6000),50000,100000,complete=True)=='improve'
 assert classify(5000,(1,6000),1,1,complete=False)=='inconclusive'
