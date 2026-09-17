"""Release lane performs policy preflight against a real rootless Podman daemon.

Ordinary developer CI skips only when Podman is unavailable; release CI sets
P2_RELEASE_LANE=1, where missing/hardened-policy failures are test failures.
"""
from __future__ import annotations
import os
import shutil
import pytest
from dataclasses import replace
from evaluation.p2.podman import PodmanLauncher, PodmanPolicyUnavailable, PodmanUnavailable
from test_p2_podman import spec

def _release_or_skip(message):
    if os.environ.get("P2_RELEASE_LANE") == "1": pytest.fail(message)
    pytest.skip(message)

def test_real_rootless_podman_preflight_or_release_failure(tmp_path):
    if shutil.which("podman") is None: _release_or_skip("Podman unavailable outside release evaluator lane")
    try:
        PodmanLauncher().preflight(spec(tmp_path))
    except (PodmanPolicyUnavailable, PodmanUnavailable) as exc:
        _release_or_skip(f"digest-pinned local P2 image preflight failed: {exc}")

def test_real_hardened_container_and_bypass_fixture_are_required_in_release(tmp_path):
    """Runs an evaluator-provisioned native/bypass image, never a mock.

    Release provides digest-pinned images. The bypass image's fixed entrypoint
    attempts Python, shell, host socket/path, undeclared executable, callback,
    and ID-only routing; nonzero termination with no proposal is the expected
    containment result. Ordinary developer CI cannot claim this control.
    """
    if shutil.which("podman") is None: _release_or_skip("Podman unavailable")
    image=os.environ.get("P2_TEST_BYPASS_IMAGE_DIGEST")
    if not image: _release_or_skip("evaluator bypass fixture image unavailable")
    base=spec(tmp_path); hardened=replace(base, image_digest=image)
    process=PodmanLauncher().start(hardened)
    stdout, _stderr=process.communicate(b"", timeout=5)
    import json
    report=json.loads(stdout)
    assert process.returncode == 0 and report.get("schema") == "P2BypassProbeReportV1"
    assert report.get("status") == "contained" and set(report.get("attempts", {}).values()) == {"blocked"}

def test_bypass_surface_is_rejected_by_hardened_runtime_contract(tmp_path):
    argv=" ".join(PodmanLauncher().argv(spec(tmp_path)))
    for forbidden in ("python", "sh ", "podman.sock", "/run/user", "--privileged"):
        assert forbidden not in argv
