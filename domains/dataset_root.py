"""Where external datasets live — a single, repo-local, GITIGNORED location.

Large external corpora (DeepWriting / IAM handwriting, UNIPEN + QuickDraw pen data,
Omniglot strokes) are NOT committed; they are provisioned into `<repo>/data/` (which
`.gitignore` already excludes) rather than the machine's ephemeral `/tmp` (which is a
size-capped tmpfs — filling it broke the test run, and a reboot wipes it). Override
the root with `OZMA_DATASETS_DIR` for a shared/mounted dataset volume.

This is a pure path helper (no agent logic, no I/O) — the world adapters and the test
conftest read their default dataset directories from here so there is ONE definition."""
from __future__ import annotations

import os

# <repo> == the gamma-substrate experiment root (this file is at domains/).
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def datasets_root() -> str:
    """The gitignored dataset root: `$OZMA_DATASETS_DIR` or `<repo>/data`."""
    return os.environ.get("OZMA_DATASETS_DIR", os.path.join(_REPO, "data"))


def dataset_dir(*parts: str) -> str:
    """A dataset directory under the root, e.g. `dataset_dir('handwriting')`."""
    return os.path.join(datasets_root(), *parts)
