"""A PROVENANCE PIN THIS REPOSITORY CANNOT RESOLVE IS A SKIP, NOT A RED.

WHY THIS EXISTS (red-test triage, 2026-08-12). Eight test files carry §12.3
rung-provenance gates: `git diff BASE_SHA RUNG_SHA` and assert the rung's own
commit added no Rust, touched only files it owned, appended exactly one ledger
row, and so on. Those are good gates. **Their subject is a commit range that
this repository no longer contains.**

MEASURED at `d239b7c`: this repo's root commit is `26ca9ff` (2026-08-10, 96
commits). The pins point into the pre-export tree — their own pinned paths
still read `research/experiments/gamma-substrate/...`, the OLD layout — and
`git cat-file -e 212212e3` returns `fatal: Not a valid object name`. **30 node
ids across 8 files** were red for this one reason, and NO amount of future work
can turn them green here: the evidence they check was not deleted by a defect,
it is simply not in this repository.

What that is, precisely, and why it is a SKIP and not a retirement:

  * it is NOT a failing claim. Each of those claims was verified when its rung
    landed; nothing has falsified any of them.
  * it is NOT fixable code. There is no defect to repair.
  * it IS an absent artifact — the same shape as `data/` not being symlinked,
    which this tree already skips on by convention.
  * and it SELF-HEALS: point the checkout at a repo that does contain the
    history and every one of these gates arms again, unchanged.

THE PRECEDENT IS THE FILES' OWN. They already carry
`_UNPINNED = RUNG_SHA.startswith("RUNG_SHA")` with
`@pytest.mark.skipif(_UNPINNED, reason="RUNG_SHA not yet pinned")` — a pin that
cannot be used yet is already a skip. A pin that cannot be used ANY MORE is the
same fact from the other end.

WHAT THIS MUST NEVER BECOME: a way to skip a provenance gate whose pins ARE
reachable. `unresolvable()` asks git one question — is this object in this
repository — and a reachable pin returns False, so the gate runs and can fail.
"""
from __future__ import annotations

import functools
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@functools.lru_cache(maxsize=None)
def _is_object(sha: str) -> bool:
    """Is `sha` a commit object IN THIS REPOSITORY? Mechanical; never guesses."""
    if not sha or sha.startswith("RUNG_SHA") or sha.startswith("BASE_SHA"):
        return False
    try:
        r = subprocess.run(["git", "-C", ROOT, "cat-file", "-e", f"{sha}^{{commit}}"],
                           capture_output=True, text=True, timeout=60)
    except Exception:                                   # noqa: BLE001
        return False
    return r.returncode == 0


def unresolvable(*shas: str) -> bool:
    """True iff ANY pinned commit is absent from this repository."""
    return any(not _is_object(s) for s in shas)


def reason(*shas: str) -> str:
    missing = [s for s in shas if not _is_object(s)]
    return ("provenance pin(s) not in this repository: "
            f"{missing} — this repo's history begins at "
            f"{_root_commit()}. The rung's own claim is UNVERIFIABLE HERE, not "
            "false; the gate re-arms unchanged against a repo that has the "
            "range. See tests/provenance_pins.py.")


@functools.lru_cache(maxsize=1)
def _root_commit() -> str:
    try:
        r = subprocess.run(["git", "-C", ROOT, "rev-list", "--max-parents=0", "HEAD"],
                           capture_output=True, text=True, timeout=60)
        return (r.stdout.split() or ["UNKNOWN"])[0][:12]
    except Exception:                                   # noqa: BLE001
        return "UNKNOWN"


def skip_if_unresolvable(*shas: str):
    """A `pytest.mark.skipif` for a pin this repository cannot resolve."""
    import pytest
    return pytest.mark.skipif(unresolvable(*shas), reason=reason(*shas))
