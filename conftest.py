import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# THE ENGINE MUST BE THIS TREE'S (PROTOCOL §10 + §11).
#
# `site-packages/substrate_rs.pth` is an ABSOLUTE path into the canonical
# tree, and `runners/dsl/python/substrate_rs/_native.abi3.so` is gitignored
# — so without this, EVERY WORKTREE silently imports the canonical tree's
# engine (and its whole `substrate_rs` Python package). Benign only while no
# rung adds Rust; silently wrong the moment one does.
#
# So: if THIS tree has built its own artifact, it goes FIRST on sys.path and
# wins over the `.pth`. If it has not, the `.pth` fallback still resolves —
# and `tests/test_engine_provenance_migrated.py` then requires the canonical
# tree's Rust source to be byte-identical to this tree's, failing loudly if
# it is not. A copy goes stale; a pointer cannot; but a pointer CAN point
# somewhere other than where you are standing.
from domains.engine_provenance import engine_preamble  # noqa: E402

# strict=False DELIBERATELY. `engine_preamble()` now REFUSES a DIVERGED /
# unverifiable engine in the measuring process (the seam that closes the
# "green gate in a different process" defect). Under pytest that refusal
# would abort COLLECTION, turning the two named failures of
# tests/test_engine_provenance_migrated.py into a dead suite — and moving
# the ORACLE's protocol number (§9: defaults preserve committed results).
# The dedicated gate reports; the preamble refuses; neither does the
# other's job.
engine_preamble(strict=False)

# External datasets live in a GITIGNORED repo-local dir (`data/`), not the
# machine's ephemeral /tmp tmpfs. pytest imports this rootdir conftest BEFORE
# any test module, so these setdefaults win over the per-test
# `os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")` echoes below —
# every test then reads its corpus from `data/`. Override with
# OZMA_DATASETS_DIR (e.g. a shared/mounted dataset volume).
from domains.dataset_root import dataset_dir  # noqa: E402

os.environ.setdefault("DEEPWRITING_DIR", dataset_dir("handwriting"))
os.environ.setdefault(
    "IAM_STROKES_DIR", dataset_dir("handwriting", "iam_onbd", "lineStrokes"))
os.environ.setdefault(
    "IAM_ASCII_DIR", dataset_dir("handwriting", "iam_ascii", "ascii"))
os.environ.setdefault("OMNIGLOT_DIR", dataset_dir("omniglot"))
os.environ.setdefault("PENDATA_DIR", dataset_dir("pendata"))
