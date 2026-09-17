"""P3 worker/evaluator envelope, containment, and evidence tests."""
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import hashlib
import json
import time
import pytest

from evaluation.p0a.canonical import canonical_bytes, object_hash, sign
from evaluation.p3.execution import P3ExecutionFailure, P3PodmanSpec, P3WorkerClient, validate_pair_evidence
from evaluation.p3.protocol import P3ProtocolError
from evaluation.p3.study import TaskReleaseLedger, materialize_study
from p3_fixtures import digest


class FakeLauncher:
 def __init__(self, worker_reply): self.worker_reply=worker_reply; self.requests=[]
 def exchange(self, spec, request):
  self.requests.append((spec.entrypoint,request))
  if spec.entrypoint=='/runtime/p3_probe':
   return canonical_bytes({'schema':'P3WorkerAdversarialProbeReportV1','status':'contained','attempts':{
    'direct_control_plane_mutation':'blocked','transitive_control_plane_mutation':'blocked','host_io':'blocked','replay_order':'blocked','rollback_restore':'blocked'}}),0
  return canonical_bytes(self.worker_reply),0


def _spec(tmp_path):
 root=tmp_path/'closure'; root.mkdir(); agent=root/'agent'; agent.mkdir(); worker=agent/'worker'; worker.write_bytes(b'bin'); worker.chmod(0o500); (agent/'candidate.bin').write_bytes(b'candidate')
 input_root=root/'input'; input_root.mkdir(); work=root/'work'; work.mkdir(); seccomp=root/'seccomp'; seccomp.write_bytes(b'policy')
 return P3PodmanSpec(digest('a'),worker,agent,input_root,seccomp,'sha256:'+hashlib.sha256(b'policy').hexdigest(),work,root)


def _envelope(key):
 lock=digest('a'); _manifest, package, _private=materialize_study(seed=b'x'*32, signing_key=key, key_id='eval-task', lock_digest=lock, run_id='r', expires_at=int(time.time())+60)
 return lock, package['shift-toy-a-struct-1'][0]


def test_worker_authenticates_one_canonical_task_and_runs_all_container_probes(tmp_path):
 key=Ed25519PrivateKey.generate(); lock, envelope=_envelope(key); candidate='sha256:'+hashlib.sha256(b'candidate').hexdigest()
 reply={'schema':'P3WorkerOutputV1','task_digest':envelope['task_digest'],'candidate_digest':candidate,'candidate_evidence':{'bounded':'evidence'}}
 reply['worker_output_digest']=object_hash(reply)
 launcher=FakeLauncher(reply); client=P3WorkerClient(_spec(tmp_path), task_release_keys={'eval-task':key.public_key()}, launcher=launcher)
 client.bind_task_release(lock_digest=lock, run_id='r')
 assert client.adversarial_probe(lock_digest=lock)['status']=='contained'
 assert client.execute_next(envelope,candidate_digest=candidate)==reply
 request=json.loads(launcher.requests[-1][1])
 assert request=={'schema':'P3WorkerRequestV1','sealed_task_digest':envelope['task_digest']}
 with pytest.raises(P3ExecutionFailure): client.execute_next(envelope,candidate_digest=candidate)


def test_task_ledger_rejects_forgery_wrong_order_replay_and_expiry():
 key=Ed25519PrivateKey.generate(); lock, first=_envelope(key)
 _manifest, package, _private=materialize_study(seed=b'y'*32, signing_key=key, key_id='eval-task', lock_digest=lock, run_id='r', expires_at=int(time.time())+60)
 second=package['shift-toy-a-struct-1'][1]
 ledger=TaskReleaseLedger({'eval-task':key.public_key()},lock,'r')
 with pytest.raises(P3ProtocolError): ledger.consume(second)
 forged=dict(first); forged['nonce']=digest('b')
 with pytest.raises(P3ProtocolError): ledger.consume(forged)
 assert ledger.consume(first)['sequence']==0
 with pytest.raises(P3ProtocolError): ledger.consume(first)
 expired=dict(first); expired['expires_at']=0
 with pytest.raises(P3ProtocolError): TaskReleaseLedger({'eval-task':key.public_key()},lock,'r').consume(expired)


def _evidence(key, envelope, *, candidate=digest('c'), pre=digest('d')):
 arms={name:{'score':60000,'status':'ok'} for name in ('governed','frozen','reset_memory','no_consolidation')}
 ledger={name:{'cpu_count':1,'memory_bytes':4*1024**3,'wall_seconds':60,'graph_transactions':10000,'network_bytes':0} for name in arms}
 value={'schema':'P3PairEvidenceV1','key_id':'evaluator','lock_digest':digest('a'),'task_digest':envelope['task_digest'],'pair_id':envelope['pair_id'],'sequence':envelope['sequence'],'candidate_digest':candidate,'pre_snapshot_digest':pre,'post_snapshot_digest':digest('e'),'arms':arms,'safety_ok':True,'resource_ledger':ledger,'retention_delta':0,'transfer_delta':6000,'worker_output_digest':digest('f'),'receipt_hashes':{'worker':digest('1'),'evaluator':digest('2')}}
 value['evidence_digest']=object_hash(value); value['signature']=sign(value,key,'evidence_digest'); return value


def test_pair_evidence_is_canonical_signed_and_bound_to_exact_task_candidate_and_snapshots():
 key=Ed25519PrivateKey.generate(); envelope={'pair_id':'p','sequence':0,'task_digest':digest('b')}; evidence=_evidence(key,envelope)
 assert validate_pair_evidence(evidence,public_key=key.public_key(),lock_digest=digest('a'),envelope=envelope,candidate_digest=digest('c'),pre_snapshot_digest=digest('d'))==evidence
 forged=dict(evidence); forged['sequence']=1
 with pytest.raises(P3ProtocolError): validate_pair_evidence(forged,public_key=key.public_key(),lock_digest=digest('a'),envelope=envelope,candidate_digest=digest('c'),pre_snapshot_digest=digest('d'))
