from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest
from evaluation.p3.attestations import local_attestation_digest
from evaluation.p3.lock import ARTIFACT_NAMES, make_release_lock, validate_lock
from evaluation.p3.protocol import P3ProtocolError
from p3_fixtures import digest, local_go

def test_lock_is_complete_signed_and_binds_all_local_go_artifacts():
 key=Ed25519PrivateKey.generate(); p0=local_go('p0',key,digest('1')); p1=local_go('p1',key,digest('2')); p2=local_go('p2',key,digest('3'))
 lock=make_release_lock(signing_key=key,key_id='e',p0_go_digest=local_attestation_digest(p0),p1_go_digest=local_attestation_digest(p1),p2_go_digest=local_attestation_digest(p2),artifacts={n:digest(format((i % 9) + 1,'x')) for i,n in enumerate(ARTIFACT_NAMES)},candidate_digest=digest('4'),pre_snapshot_digest=digest('5'),native_export_digest=digest('6'))
 assert validate_lock(lock,{'e':key.public_key()}).digest==lock['content_hash']
 lock['thresholds']['wall_seconds']=1
 with pytest.raises(P3ProtocolError): validate_lock(lock,{'e':key.public_key()})

def test_lock_rejects_missing_p0_or_p1_bindings():
 key=Ed25519PrivateKey.generate(); p=local_go('p2',key,digest('3'))
 raw=make_release_lock(signing_key=key,key_id='e',p0_go_digest=digest('1'),p1_go_digest=digest('2'),p2_go_digest=local_attestation_digest(p),artifacts={n:digest(format((i % 9) + 1,'x')) for i,n in enumerate(ARTIFACT_NAMES)},candidate_digest=digest('4'),pre_snapshot_digest=digest('5'),native_export_digest=digest('6'))
 del raw['p0_go_digest']
 with pytest.raises(P3ProtocolError): validate_lock(raw,{'e':key.public_key()})
