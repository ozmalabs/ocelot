"""SCALE SPLIT — the rung's own provenance self-audit.

PROTOCOL §12.3: *a provenance claim must be pinned to its DIFF, never to a
mutable tree.* That defect has been recorded SEVEN times in this arc, three of
them lying DORMANT for 51 commits because no rung added Rust — so the assertions
could never fail. `tests/test_provenance_endpoint_guard_migrated.py` now FAILS
any provenance assertion diffing a range ending at `HEAD`.

**THIS RUNG IS THE TRIGGER CONDITION THOSE DORMANT GATES WERE WAITING FOR: it
ADDS RUST.** So the claims here are the inverse of the usual instrument rung's,
and each is asserted rather than asserted-in-prose:

1. **It adds Rust, and ONLY the named files.** A `.rs` outside the declared set
   would mean the engine that produced these numbers is not the engine this
   rung documents.
2. **The Rust it adds is an INSTRUMENT, DEFAULT OFF.** This is the load-bearing
   §9 claim: every committed result must reproduce byte-identically with the
   audit unset. Checked against the SHIPPED engine, not against the source.
3. **It adds NO seed and edits NO seed**, and changes no default.
4. **It edits no other rung's files** (§11 rule 4 — rungs stay attributable).
5. **Its one edit to the shared `VISION_PROTOCOL.md` is a single appended
   ledger row with no deletions.**

BOTH ENDPOINTS ARE PINNED on every diff. Never `HEAD`, never the working tree.
"""
from __future__ import annotations

import os
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_SHA = "62fadd1a18edca2124aff57e85af4f47ae6f8b99"
RUNG_SHA = "76460d901b156bff238b2dfccfdd4f0b87e520d5"

_PREFIX = "research/experiments/gamma-substrate/"

# Exactly the paths this rung may have touched. Git reports `--name-only` paths
# from the GIT ROOT, not from the experiment dir.
ALLOWED = {
    _PREFIX + "VISION_SCALE_SPLIT_PREREG.md",
    _PREFIX + "VISION_SCALE_SPLIT_RESULTS.md",
    _PREFIX + "VISION_PROTOCOL.md",                    # the seed-ledger row only
    _PREFIX + "scripts/scale_split_measure.py",
    _PREFIX + "results/scale_split.json",
    _PREFIX + "tests/test_scale_split_provenance_migrated.py",
    # --- the Rust this rung legitimately adds ---
    _PREFIX + "runners/dsl/src/scale_audit.rs",        # the new instrument module
    _PREFIX + "runners/dsl/src/lib.rs",                # its `pub mod` declaration
    _PREFIX + "runners/dsl/src/rewrite.rs",            # counter call sites
    _PREFIX + "runners/dsl/src/substrate.rs",          # counter call sites
    _PREFIX + "runners/dsl/src/py.rs",                 # FFI counters + readout
}

# The ONLY .rs files this rung may touch. Anything else means the engine that
# produced the numbers differs from the one documented.
ALLOWED_RUST = {
    _PREFIX + "runners/dsl/src/scale_audit.rs",
    _PREFIX + "runners/dsl/src/lib.rs",
    _PREFIX + "runners/dsl/src/rewrite.rs",
    _PREFIX + "runners/dsl/src/substrate.rs",
    _PREFIX + "runners/dsl/src/py.rs",
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


def test_the_rust_it_adds_is_exactly_the_declared_set():
    """Claim 1. This rung ADDS Rust — so the gate is not 'no .rs' but 'only
    these .rs'. A stray engine edit would silently change the object every
    other rung measures."""
    rust = {p for p in _changed(BASE_SHA, RUNG_SHA)
            if p.endswith((".rs", "Cargo.toml", "Cargo.lock"))}
    stray = sorted(rust - ALLOWED_RUST)
    assert stray == [], f"this rung touched undeclared Rust: {stray}"
    assert _PREFIX + "runners/dsl/src/scale_audit.rs" in rust, (
        "the instrument module is absent from the diff — this gate would be "
        "vacuously green, which is the failure mode it exists to prevent")


def test_the_audit_is_DEFAULT_OFF_in_the_shipped_engine():
    """Claim 2, and the load-bearing one (PROTOCOL §9: defaults preserve
    committed results).

    Asserted against the SHIPPED BINARY rather than against the source, because
    what protects every other rung's numbers is the engine that actually loads —
    the two-binary hazard (§10) is precisely a case where source and artifact
    disagreed and both agents reported green."""
    import sys
    sys.path.insert(0, REPO)
    from domains.engine_provenance import engine_preamble
    engine_preamble()
    from substrate_rs import _native

    assert hasattr(_native.Substrate, "scale_audit_enabled"), (
        "the shipped engine has no scale-audit readout — the numbers in "
        "VISION_SCALE_SPLIT_RESULTS.md were not produced by this binary")
    if os.environ.get("OZMA_SCALE_AUDIT"):
        pytest.skip("OZMA_SCALE_AUDIT is set in this environment")
    assert _native.Substrate.scale_audit_enabled() is False, (
        "the scale audit is ON by default — every committed result would be "
        "measured through an instrumented engine (§9 violation)")


def test_the_disabled_instrument_counts_NOTHING():
    """Claim 2's teeth. 'Default off' is only worth asserting if 'off' really
    means no counter moves. A counter that ticked while disabled would be a
    silent behaviour change in every rung that runs after this one."""
    import sys
    sys.path.insert(0, REPO)
    from domains.engine_provenance import engine_preamble
    engine_preamble()
    from substrate_rs import _native
    if os.environ.get("OZMA_SCALE_AUDIT"):
        pytest.skip("OZMA_SCALE_AUDIT is set in this environment")

    import domains.seed_registry  # noqa: F401
    from substrate.boot_core import boot_core, load_seeds_into
    from domains.wave_world import WaveWorld

    _native.Substrate.scale_audit_set_enabled(False)
    _native.Substrate.scale_audit_reset()
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    w = WaveWorld(s, h=12, w=12, seed=0)
    for i in range(6):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
    moved = {k: v for k, v in _native.Substrate.scale_audit_snapshot() if v}
    assert moved == {}, f"counters moved while the audit was OFF: {moved}"


def test_this_rung_adds_and_edits_NO_seed():
    """Claim 3. An instrument that edited a seed would be measuring something
    other than the committed agent."""
    seeds = [p for p in _changed(BASE_SHA, RUNG_SHA) if "/seeds/" in p]
    assert seeds == [], f"this rung claims to touch no seed, but touched: {seeds}"


def test_this_rung_touches_only_its_own_files():
    """Claim 4 (§11 rule 4)."""
    foreign = sorted(set(_changed(BASE_SHA, RUNG_SHA)) - ALLOWED)
    assert foreign == [], f"this rung touched files it does not own: {foreign}"


def test_the_protocol_edit_is_the_ledger_entry_ONLY():
    """Claim 5. The diff must ADD lines and REMOVE none — §11 rule 1 resolves
    ledger conflicts by keeping BOTH sides, which only works if nobody deletes.

    The `:/` magic pathspec is load-bearing: git reports `--name-only` paths
    from the GIT ROOT but resolves a PATHSPEC relative to CWD, and this suite
    runs from the experiment dir. The video-probe rung's version of this test
    failed with 'got 0' for exactly that reason."""
    d = _git("diff", "--unified=0", BASE_SHA, RUNG_SHA, "--",
             ":/" + _PREFIX + "VISION_PROTOCOL.md")
    removed = [ln for ln in d.splitlines()
               if ln.startswith("-") and not ln.startswith("---")]
    added = [ln for ln in d.splitlines()
             if ln.startswith("+") and not ln.startswith("+++")]
    assert removed == [], f"the ledger edit deleted lines: {removed}"
    assert len(added) == 1, f"expected ONE appended ledger row, got {len(added)}"
    assert "61000" in added[0], "the appended row is not this rung's seed block"


def test_commits_after_the_rung_tip_add_ONLY_this_test():
    """The endpoint pinning is only honest if nothing substantive hides after
    RUNG_SHA. Pinned RUNG_SHA..TAIL_SHA, BOTH FIXED — resolving this against
    `HEAD` is the exact defect that turned three dormant gates red at once and
    made them accuse rungs whose claims were true."""
    TAIL_SHA = "4e20b4a02053b0ff9852773c2e02dc512d6041a4"
    if TAIL_SHA.startswith("__") or TAIL_SHA == RUNG_SHA:
        return
    tail = set(_changed(RUNG_SHA, TAIL_SHA))
    allowed_tail = {_PREFIX + "tests/test_scale_split_provenance_migrated.py"}
    assert tail <= allowed_tail, (
        f"commits after the rung tip changed more than this test: "
        f"{sorted(tail - allowed_tail)}")
