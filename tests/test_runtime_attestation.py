import json
from types import SimpleNamespace

import pytest

from evaluation.process_mastery.runtime_attestation import attest, assert_freeze_matches


def _fixture(tmp_path, native_bytes=b"native-one", receipt=True):
    wrapper = tmp_path / "__init__.py"
    wrapper.write_text("# wrapper\n")
    extension = tmp_path / "_native.abi3.so"
    extension.write_bytes(native_bytes)
    node_id, substrate = object(), object()
    native = SimpleNamespace(__file__=str(extension), NodeID=node_id, Substrate=substrate)
    package = SimpleNamespace(__file__=str(wrapper), _native=native,
                              NodeID=node_id, Substrate=substrate)
    build = tmp_path / "_native.build.json" if receipt else None
    if build:
        build.write_text(json.dumps({"source_fingerprint": "source-abc"}))
    return package, build


def test_hashes_loaded_extension_not_wrapper(tmp_path):
    package, build = _fixture(tmp_path)
    result = attest(package=package, build_receipt=build)
    assert result["wrapper_sha256"] != result["loaded_extension_sha256"]
    assert result["native_symbols_bound"] is True


def test_native_change_breaks_freeze(tmp_path):
    package, build = _fixture(tmp_path)
    frozen = attest(package=package, build_receipt=build)
    package._native.__file__ and open(package._native.__file__, "wb").write(b"native-two")
    changed = attest(package=package, build_receipt=build)
    with pytest.raises(RuntimeError, match="loaded_extension_sha256"):
        assert_freeze_matches(changed, frozen)


def test_same_wrapper_different_native_rejected(tmp_path):
    package, build = _fixture(tmp_path)
    frozen = attest(package=package, build_receipt=build)
    second_path = tmp_path / "other.abi3.so"
    second_path.write_bytes(b"different")
    package._native.__file__ = str(second_path)
    changed = attest(package=package, build_receipt=build)
    assert changed["wrapper_sha256"] == frozen["wrapper_sha256"]
    with pytest.raises(RuntimeError, match="loaded_extension_sha256"):
        assert_freeze_matches(changed, frozen)


def test_missing_build_receipt_unknown(tmp_path):
    package, _ = _fixture(tmp_path, receipt=False)
    result = attest(package=package)
    assert result["status"] == "UNKNOWN"
    assert result["build_receipt_sha256"] is None
    assert "build_receipt_unknown" in result["issues"]


def test_source_receipt_mismatch_rejected(tmp_path):
    package, build = _fixture(tmp_path)
    build.write_text(json.dumps({"source_fingerprint": "source-abc",
                                 "files": {"missing/source.rs": "bad"}}))
    result = attest(package=package, build_receipt=build)
    assert result["build_sources_match"] is False
    assert "build_source_mismatch" in result["issues"]
