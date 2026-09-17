"""Finite, local-only construction and verification of the P2 evaluator image."""
from __future__ import annotations
import re
import shutil
import subprocess
from pathlib import Path
from .podman import PodmanPolicyUnavailable

_DIGEST=re.compile(r"^sha256:[0-9a-f]{64}$")
def build_or_fail_closed(*, podman: str, containerfile: Path, context: Path, tag: str, expected_digest: str) -> str:
    """Build only from the supplied finite context with pulls disabled, then pin digest."""
    if not _DIGEST.fullmatch(expected_digest): raise PodmanPolicyUnavailable("p2 evaluator image digest")
    exe=shutil.which(podman) if "/" not in podman else podman
    if not exe or not Path(exe).is_file(): raise PodmanPolicyUnavailable("podman unavailable")
    for path in (containerfile,context):
        if Path(path).is_symlink() or not Path(path).exists(): raise PodmanPolicyUnavailable("finite evaluator context")
    try:
        built=subprocess.run([exe,"build","--pull=never","--network=none","-f",str(containerfile),"-t",tag,str(context)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=120,check=False,close_fds=True)
        if built.returncode: raise PodmanPolicyUnavailable("local evaluator image build failed")
        inspected=subprocess.run([exe,"image","inspect","--format","{{.Digest}}",tag],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=10,check=False,close_fds=True)
    except OSError as exc: raise PodmanPolicyUnavailable("local evaluator image unavailable") from exc
    digest=inspected.stdout.decode().strip()
    if inspected.returncode or digest != expected_digest: raise PodmanPolicyUnavailable("evaluator image digest mismatch")
    return digest
