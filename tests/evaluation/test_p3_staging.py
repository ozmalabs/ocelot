"""The P3 artifact closure is explicit, finite, and lock-bound."""
import hashlib
import pytest

from evaluation.p3.lock import ARTIFACT_NAMES, P3ReleaseLockV1
from evaluation.p3.protocol import P3ProtocolError
from evaluation.p3.staging import write_staging_index, validate_staging_index
from p3_fixtures import digest


def test_full_artifact_closure_requires_every_locked_staged_file(tmp_path):
 root=tmp_path/'closure'; root.mkdir(); artifacts={}; supplied={}
 image={'broker_image','policy_authority_image','receipt_writer_image','native_worker','native_evaluator_image'}
 for name in ARTIFACT_NAMES:
  if name in image:
   artifacts[name]=digest('a'); supplied[name]=artifacts[name]
  else:
   path=root/name; path.write_bytes(name.encode()); artifacts[name]='sha256:'+hashlib.sha256(name.encode()).hexdigest(); supplied[name]=path
 lock=P3ReleaseLockV1({'content_hash':digest('b'),'artifacts':artifacts})
 index=write_staging_index(root=root,lock=lock,artifacts=supplied)
 assert validate_staging_index(index,root=root,lock=lock)['entries'][0]['name']==ARTIFACT_NAMES[0]
 supplied.pop('p3_schemas')
 with pytest.raises(P3ProtocolError): write_staging_index(root=root,lock=lock,artifacts=supplied)
