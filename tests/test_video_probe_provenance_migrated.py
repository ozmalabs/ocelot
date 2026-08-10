"""VIDEO PROBE — the rung's own provenance self-audit.

PROTOCOL §12.3: *a provenance claim must be pinned to its DIFF, never to a
mutable tree.* Both of rung 8B's self-restraint gates rotted the day they were
written because they diffed the LIVE TREE against a hardcoded sha, so they tested
"has anyone done any work since" rather than the claim they were making. This
defect has now occurred three times in this arc.

So every assertion below pins **BOTH ENDPOINTS** — `git diff BASE_SHA RUNG_SHA` —
and never `HEAD`, never the working tree.

THE CLAIMS THIS RUNG MAKES ABOUT ITSELF, and which are checked here:

1. **It adds NO Rust.** The engine it measured on is a `shared` build whose Rust
   source is byte-identical to the canonical tree (§10.1 rule 4). That is only a
   valid provenance if this rung touched no `.rs`.
2. **It adds NO seed and edits NO seed.** It is an instrument (§0/§9): every
   number it reports was produced by the committed seeds, unmodified.
3. **It edits NO other rung's files.** Rungs stay attributable (§11 rule 4).
4. **It changes no default.** Implied by 2, and checked directly against the
   whole `seeds/` tree.

The RUNG_SHA below is the rung's last SUBSTANTIVE commit. Commits after it on this
branch add only this test file, which is asserted explicitly rather than assumed —
otherwise this gate would have the very mutable-endpoint defect it exists to
prevent.
"""
from __future__ import annotations

import os
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_SHA = "328065b62a31cf1daeb601557f21a0d331a2aed2"
RUNG_SHA = "fcb15723faddc35df2b7383ae041d8e899d5209b"

# Exactly the paths this rung is allowed to have touched, relative to the repo
# root's parent (git reports paths from the git root, not the experiment dir).
_PREFIX = "research/experiments/gamma-substrate/"
ALLOWED = {
    _PREFIX + "VISION_VIDEO_PROBE_PREREG.md",
    _PREFIX + "VISION_VIDEO_PROBE_RESULTS.md",
    _PREFIX + "VISION_PROTOCOL.md",                     # the seed-ledger entry only
    _PREFIX + "scripts/video_probe_measure.py",
    _PREFIX + "scripts/video_probe_diagnose.py",
    _PREFIX + "scripts/video_probe_explore_seam.py",
    _PREFIX + "results/video_probe.json",
    _PREFIX + "results/video_probe_diagnose.json",
    _PREFIX + "results/video_probe_seam_explore.json",
    _PREFIX + "tests/test_video_probe_provenance_migrated.py",
}


def _git(*args) -> str:
    return subprocess.run(("git",) + args, cwd=REPO, capture_output=True,
                          text=True, check=True).stdout


def _have(sha: str) -> bool:
    try:
        subprocess.run(("git", "cat-file", "-e", sha + "^{commit}"), cwd=REPO,
                       capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def _changed(a: str, b: str) -> list[str]:
    return [ln for ln in _git("diff", "--name-only", a, b).splitlines() if ln]


pytestmark = pytest.mark.skipif(
    RUNG_SHA.startswith("__") or not _have(BASE_SHA) or not _have(RUNG_SHA),
    reason="rung commits not present in this clone (skips only where unpinnable)")


def test_this_rung_adds_NO_rust():
    """Claim 1. The measured engine is a SHARED build justified by byte-identical
    Rust source; a single .rs in this diff would invalidate every number."""
    rust = [p for p in _changed(BASE_SHA, RUNG_SHA)
            if p.endswith((".rs", "Cargo.toml", "Cargo.lock"))]
    assert rust == [], f"this rung claims to add no Rust, but touched: {rust}"


def test_this_rung_adds_and_edits_NO_seed():
    """Claim 2 + 4. An instrument that edited a seed would be measuring something
    other than the committed agent."""
    seeds = [p for p in _changed(BASE_SHA, RUNG_SHA) if "/seeds/" in p]
    assert seeds == [], f"this rung claims to touch no seed, but touched: {seeds}"


def test_this_rung_touches_only_its_own_files():
    """Claim 3. Rungs stay attributable (§11 rule 4): no other rung's
    pre-registration, results, adapter or test may appear in this diff."""
    foreign = sorted(set(_changed(BASE_SHA, RUNG_SHA)) - ALLOWED)
    assert foreign == [], f"this rung touched files it does not own: {foreign}"


def test_the_protocol_edit_is_the_ledger_entry_ONLY():
    """The one shared file in the diff is VISION_PROTOCOL.md, and the rung claims
    its edit there is a single appended seed-ledger row. Checked, not asserted:
    the diff must ADD lines and REMOVE none (§11 rule 1 resolves ledger conflicts
    by keeping BOTH sides, which only works if nobody deletes)."""
    # NOTE: git reports --name-only paths from the GIT ROOT but resolves a
    # PATHSPEC relative to CWD, and this runs with cwd=<experiment dir>. The
    # `:/` magic prefix makes the pathspec root-relative so both ends agree.
    # (Caught by this very test failing with "got 0" — a gate that has only
    # ever passed is not a gate that has been tested, §12.3.)
    d = _git("diff", "--unified=0", BASE_SHA, RUNG_SHA, "--",
             ":/" + _PREFIX + "VISION_PROTOCOL.md")
    removed = [ln for ln in d.splitlines()
               if ln.startswith("-") and not ln.startswith("---")]
    added = [ln for ln in d.splitlines()
             if ln.startswith("+") and not ln.startswith("+++")]
    assert removed == [], f"the ledger edit deleted lines: {removed}"
    assert len(added) == 1, f"expected ONE appended ledger row, got {len(added)}"
    assert "54000" in added[0], "the appended row is not this rung's seed block"


def test_commits_after_the_rung_tip_add_ONLY_this_test():
    """The endpoint-pinning is only honest if nothing substantive hides after
    RUNG_SHA. This asserts the tail of the branch explicitly rather than
    trusting it — the mutable-endpoint defect (§12.3) in its last hiding place.

    SUPERVISOR REPAIR (2026-07-19), and this one is the sharpest instance in the
    arc: the test above reintroduced the very defect it names. It resolved the
    tail against `HEAD`, so the moment ANY later rung merged, "the tail of this
    rung" silently became "every commit anyone has landed since" — and the INK ×
    VENTRAL merge duly turned it red, accusing the video probe of adding Rust it
    never wrote. Naming a defect in a docstring is not the same as being gated
    against it; §12.3 is now the sixth recorded occurrence across this arc
    (colour-bound, colour-bound-k1, lighting-L4, lighting-L3b, margin, here),
    plus the Troxler cut that caught itself within the hour.

    The tail is now pinned to its true extent: RUNG_SHA..TAIL_SHA, both fixed."""
    TAIL_SHA = "50ed2937d642a121b871448811030b13f8f44f86"   # this rung's own final commit
    if TAIL_SHA == RUNG_SHA:
        return
    tail = set(_changed(RUNG_SHA, TAIL_SHA))
    allowed_tail = {_PREFIX + "tests/test_video_probe_provenance_migrated.py"}
    assert tail <= allowed_tail, (
        f"commits after the rung tip changed more than this test: {sorted(tail - allowed_tail)}")
