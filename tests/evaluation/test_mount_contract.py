import pytest
from evaluation.p0a.canonical import ProtocolError
from evaluation.p0a.mounts import LocalMountContract


def test_content_addressed_mount_contract_rejects_agent_paths(tmp_path):
    mounts = LocalMountContract(tmp_path, "sha256:" + "d" * 64)
    digest = mounts.stage(b"sealed")
    assert mounts.resolve_input(digest).read_bytes() == b"sealed"
    with pytest.raises(ProtocolError): mounts.resolve_input("../seed.json")
    with pytest.raises(ProtocolError): mounts.reject_agent_path("/tmp/result")
    assert mounts.local_approximation is True
