"""INSTRUMENT SEAMS — the two defects, and the seams that make them refusals.

`VISION_INSTRUMENT_SEAMS_PREREG.md` / `VISION_INSTRUMENT_SEAMS_RESULTS.md`.
Seed block **95000–95999** (declared, `check_claim` CLEAN, recorded in the
pre-registration per §11 rec #7).

WHAT IS BEING GATED
-------------------
**Defect 1 — a green provenance gate in a DIFFERENT PROCESS is not
provenance.** `pytest tests/test_engine_provenance_migrated.py` reported 7
PASSED in the same minute a plain script in the same tree resolved
`** WRONG ENGINE **`. Seam: `engine_provenance.assert_measuring_engine()`,
attached to `engine_preamble(strict=True)` — the call §10 rule 3 already
requires — plus an INDEPENDENT static audit (`domains/preamble_audit.py`)
for the one thing a runtime check structurally cannot see: a process that
never calls it.

**Defect 2 — a prereg records declarations, not measurements** (§11 recs
#4, #7). Seams: a GENERATED measured-occupancy record gated for freshness
(`domains/seed_record.py`), and a prereg gate requiring the `check_claim`
verdict, with an explicit committed grandfather floor.

HOW EVERY CONTROL HERE IS BUILT — read this before adding one
--------------------------------------------------------------
1. **BOTH DIRECTIONS, ALWAYS.** Fires on a real defect; green on the clean
   tree. A gate that has never been ABLE to fail has not been tested —
   three provenance gates in this arc sat green for 51 commits and then
   fired at once as FALSE ACCUSATIONS.
2. **THE PLANT MUST BE VERIFIED TO LAND.** Every positive control here
   asserts the detector is RED with the plant present *and* names where
   the plant went. The seed-claim rung's first control passed silently
   because it planted in an already-declared block; the supervisor's
   injection test passed because it planted in the wrong subtree. **If a
   control is quiet, that is a finding, not a pass.**
3. **THE DEFECT IS REAL, NEVER MOCKED.** The DIVERGED control builds an
   actual second tree with actually-different Rust source and lets the
   real fingerprint comparison reach its own verdict. Nothing in
   `engine_provenance` is monkeypatched — a diagnostic must not be
   computed by the component it checks, and neither must its control.
4. **RANDOMISED, NOT HAND-PICKED.** The plant contents are drawn from the
   declared seed block, so a control cannot pass by accident of one
   convenient example. THIS IS ALSO WHY THIS RUNG SPENDS SEEDS AT ALL: a
   static analyser draws none, and its self-audit would be vacuous.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains import engine_provenance as ep  # noqa: E402
from domains import preamble_audit as pa  # noqa: E402
from domains import seed_record as sr  # noqa: E402

# ---------------------------------------------------------------------------
# THE DECLARED SEED SUB-RANGES. §11 rec #4 applied to myself: these are the
# MEASURED ranges, not the declared block. 95020–95099 and 95120–95999 are
# to remain CLEAN.
#
# TWO SPELLINGS, DELIBERATELY. The lower control block uses plain integer
# literals; the upper uses PEP-515 UNDERSCORE literals. The supervisor's
# own pre-launch seed check was `grep "90000"`, which CANNOT SEE
# `default_rng(90_000 + seed)` — a real miss, on a real allocation. So this
# rung spends part of its block in the spelling that broke the grep, and
# `test_the_audit_sees_underscore_literals_a_grep_cannot` proves the AST
# scan reads both. A detector is worth what its blind spots cost.
# ---------------------------------------------------------------------------
_CTRL_BASE = 95000        # 95000–95019, plain literals
_CTRL_BASE_US = 95_100    # 95100–95119, underscore literals
_N_CTRL = 20


def _rng(i: int, *, underscore: bool = False):
    return (np.random.default_rng(95_100 + i) if underscore
            else np.random.default_rng(95000 + i))


def _nonce(rng) -> str:
    """A random identifier, so no control depends on one chosen example."""
    return "z" + "".join(chr(97 + int(c)) for c in rng.integers(0, 26, 8))


# ===========================================================================
# DEFECT 1a — THE RUNTIME SEAM: refuse to measure on a provably wrong engine
# ===========================================================================

def _fake_divergent_tree(tmp_path, rng) -> str:
    """A REAL tree whose Rust source really differs from this one.

    No mock. `rust_source_fingerprint` walks `runners/dsl/src/**.rs` +
    `Cargo.toml` and hashes CONTENT, so a tree containing different `.rs`
    content genuinely fingerprints differently, and
    `engine_provenance(tree=<here>)` genuinely reaches `DIVERGED` — the
    loaded engine belongs to a tree whose source is not this one's.

    It ships NO `substrate_rs` package, so `engine_preamble` will not put
    it on `sys.path` and cannot disturb the session's real engine.
    """
    tree = tmp_path / f"tree_{_nonce(rng)}"
    src = tree / "runners" / "dsl" / "src"
    src.mkdir(parents=True)
    (src / "lib.rs").write_text(
        f"// divergent by construction: {_nonce(rng)}\npub fn f() {{}}\n")
    (tree / "runners" / "dsl" / "Cargo.toml").write_text(
        f'[package]\nname = "substrate-rs"\nversion = "0.{rng.integers(1, 999)}.0"\n')
    return str(tree)


def test_a_divergent_tree_is_REFUSED_and_the_clean_tree_is_NOT(tmp_path):
    """POSITIVE CONTROL, BOTH DIRECTIONS — seeds 95000–95019.

    THE DEFECT, exactly: the tree-level gate said 7 PASSED while the
    measuring process was on the wrong engine. The seam has to refuse in
    the process, from the module that process actually imported.
    """
    # --- direction 1: it FIRES, on 20 independently randomised divergences.
    for i in range(_N_CTRL):
        rng = _rng(i)
        fake = _fake_divergent_tree(tmp_path, rng)

        # LANDING CHECK — verify the plant is what I think it is BEFORE
        # trusting the verdict. A control that fires for the wrong reason
        # is a dead instrument logged as a pass.
        assert ep.rust_source_fingerprint(fake) is not None, (
            f"plant did not land: {fake} has no fingerprintable Rust source")
        assert ep.rust_source_fingerprint(fake) != ep.rust_source_fingerprint(), (
            "plant did not land: the fake tree's Rust source is IDENTICAL to "
            "this tree's, so DIVERGED is unreachable and this control would "
            "have passed while measuring nothing")

        assert ep.engine_provenance(fake)["source_match"] == "DIVERGED"

        with pytest.raises(ep.EngineProvenanceError) as exc:
            ep.assert_measuring_engine(fake)
        assert "REFUSING TO MEASURE" in str(exc.value)
        assert "engine_build.sh" in str(exc.value), (
            "a refusal without its remedy is a wall, not a gate")

    # --- direction 2: it is GREEN on the real tree, which really is clean.
    p = ep.assert_measuring_engine()
    assert p["source_match"] in ("own", "shared"), ep.provenance_line()


def test_the_preamble_ITSELF_carries_the_refusal(tmp_path):
    """THE SEAM CHOICE, gated.

    `engine_preamble()` is the call §10 rule 3 ALREADY REQUIRES of every
    non-pytest entrypoint. Attaching the check there is why it cannot be
    skipped separately from the thing it guards: **you cannot pin the
    engine without certifying what you pinned.** If this test ever passes
    with `strict=True` on a divergent tree, the seam has come unstuck and
    the check has become optional again.
    """
    fake = _fake_divergent_tree(tmp_path, _rng(0))
    before = list(sys.path)

    with pytest.raises(ep.EngineProvenanceError):
        ep.engine_preamble(fake, strict=True)

    # strict=False must stay silent — conftest depends on it, because a
    # collection-time abort would move the ORACLE's protocol number (§9).
    ep.engine_preamble(fake, strict=False)

    assert sys.path == before, (
        "engine_preamble mutated sys.path for a tree with no substrate_rs "
        "package — the control has contaminated the session's engine")


def test_conftest_pins_strict_False_on_purpose():
    """§9 — DEFAULTS PRESERVE COMMITTED RESULTS.

    Located by AST, never by substring: the fourth selector failure in this
    arc went red on a DOCSTRING, and this very file's module docstring says
    `strict=False` twice.
    """
    import ast
    tree = ast.parse(open(os.path.join(ROOT, "conftest.py"), encoding="utf-8").read())
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id == "engine_preamble"]
    assert len(calls) == 1, f"expected one engine_preamble call, found {len(calls)}"
    kw = {k.arg: k.value for k in calls[0].keywords}
    assert "strict" in kw and kw["strict"].value is False, (
        "conftest must pass strict=False EXPLICITLY. A collection-time "
        "abort would turn the two named failures of the dedicated "
        "provenance gate into a dead suite and move the oracle's number.")


def test_provenance_line_stayed_a_PURE_REPORTER(tmp_path):
    """The reporter must NOT raise — the existing gate reads it to DESCRIBE
    a broken setup, and an instrument that refuses to describe a fault is
    not an improvement on one that describes it.

    So the refusal lives on the WRITE side (`provenance_stamp`) and on the
    PIN (`engine_preamble`), never on the READ.
    """
    fake = _fake_divergent_tree(tmp_path, _rng(1))
    line = ep.provenance_line(fake)              # must not raise
    assert "WRONG ENGINE" in line
    assert ep.engine_provenance(fake)["source_match"] == "DIVERGED"

    with pytest.raises(ep.EngineProvenanceError):
        ep.provenance_stamp(fake)
    stamp = ep.provenance_stamp()
    assert stamp["line"] == ep.provenance_line()
    assert stamp["short"] in stamp["line"]


# ===========================================================================
# DEFECT 1b — THE STATIC SEAM: the blind spot a runtime check cannot have
# ===========================================================================

_CALLS = [
    # (label, source) — every legitimate spelling of "I called it".
    ("direct", "from domains.engine_provenance import engine_preamble\n"
               "engine_preamble()\n"),
    ("alias", "from domains.engine_provenance import engine_preamble as pin\n"
              "pin()\n"),
    ("module", "from domains import engine_provenance\n"
               "engine_provenance.engine_preamble()\n"),
    ("module_alias", "from domains import engine_provenance as ep\n"
                     "ep.engine_preamble()\n"),
    ("dotted", "import domains.engine_provenance\n"
               "domains.engine_provenance.engine_preamble()\n"),
]


@pytest.mark.parametrize("label,src", _CALLS, ids=[c[0] for c in _CALLS])
def test_every_spelling_of_a_CALL_is_seen_as_a_call(label, src):
    """A DETECTOR BUILT FROM OBSERVED INSTANCES COVERS OBSERVED INSTANCES.

    Six spellings once felt like a pattern here and were a sample; the
    seventh walked through within one commit. The defence is not a longer
    list — it is resolving the BINDING, so alias/qualified/dotted forms
    are the same case and a spelling nobody has written yet still resolves.
    """
    rec = pa.audit_source(src)
    assert rec["calls_preamble"], f"{label}: a real call was not seen"
    assert rec["verdicts"] == []


def test_a_MENTION_is_not_a_call():
    """DOCSTRINGS DO NOT GATE. Neither do comments or strings."""
    src = ('"""This module explains engine_preamble() at length.\n\n'
           'Call engine_preamble() first. engine_preamble()."""\n'
           "from domains.engine_provenance import engine_preamble\n"
           "# engine_preamble()\n"
           "HELP = 'run engine_preamble() before measuring'\n")
    rec = pa.audit_source(src)
    assert not rec["calls_preamble"], (
        "a docstring / comment / string literal was read as a call — this is "
        "the substring-selector failure, for the fifth time")
    assert "imported_not_called" in rec["verdicts"]


def test_the_static_audit_FIRES_on_randomised_plants(tmp_path):
    """POSITIVE CONTROL — seeds 95000–95019, randomised module bodies.

    Both verdict classes: the OBSERVED defect (bound, never called) and the
    CLASS it belongs to (an entrypoint that reaches the engine without
    pinning). The second exists because a detector built only from the
    first would cover only the first.
    """
    root = tmp_path / "planted"
    (root / "scripts").mkdir(parents=True)
    expect_inc, expect_ewp = [], []

    for i in range(_N_CTRL):
        rng = _rng(i)
        n = _nonce(rng)
        pad = "\n".join(f"X_{n}_{k} = {int(rng.integers(0, 9999))}"
                        for k in range(int(rng.integers(1, 6))))

        inc = root / "scripts" / f"inc_{n}.py"
        inc.write_text("from domains import engine_provenance as ep\n"
                       f"{pad}\nprint(ep.provenance_line())\n")
        expect_inc.append(f"scripts/inc_{n}.py")

        ewp = root / "scripts" / f"ewp_{n}.py"
        ewp.write_text(f"import substrate_rs\n{pad}\n"
                       "if __name__ == '__main__':\n    print(substrate_rs)\n")
        expect_ewp.append(f"scripts/ewp_{n}.py")

        ok = root / "scripts" / f"ok_{n}.py"
        ok.write_text("from domains.engine_provenance import engine_preamble\n"
                      "engine_preamble()\nimport substrate_rs\n"
                      f"{pad}\nif __name__ == '__main__':\n    print(substrate_rs)\n")

    rep = pa.audit_tree([str(root)], base=str(root))

    # LANDING CHECK — the plants are in the subtree that was scanned, and
    # the scan actually saw all 60 files. A control that scans the wrong
    # subtree passes by finding nothing.
    assert rep["scanned"] == 3 * _N_CTRL, (
        f"the audit scanned {rep['scanned']} files, not {3 * _N_CTRL} — the "
        "plant is not where the detector looked")
    assert rep["parse_errors"] == []

    assert sorted(rep["imported_not_called"]) == sorted(expect_inc)
    assert sorted(rep["engine_without_preamble"]) == sorted(expect_ewp)
    for i in range(_N_CTRL):
        n = _nonce(_rng(i))
        assert f"scripts/ok_{n}.py" not in rep["imported_not_called"]
        assert f"scripts/ok_{n}.py" not in rep["engine_without_preamble"]


def test_the_static_audit_LANDS_on_the_real_tree_not_only_on_plants():
    """THE NON-VACUITY CHECK.

    A detector proven only on synthetic input has been proven on synthetic
    input. This asserts the audit finds the SEVEN REAL FILES it found on
    the live tree — measure scripts that call `provenance_line()` to REPORT
    the engine while never calling `engine_preamble()` to PIN it, resolving
    instead through the old `sys.path.insert` convention §10.2 measured as
    broken in a worktree.

    ALL SEVEN ARE NOW REPAIRED, so `known_violations` is EMPTY and this
    check is INVERTED rather than deleted.

    The original form asserted that floor entries still reproduce AS
    VIOLATIONS. That tied the instrument's proof-of-life to the tree still
    being broken: repairing every entry turned the aliveness control red,
    and the cheapest route back to green was to leave a defect unfixed.
    **An instrument whose non-vacuity depends on an unrepaired defect is
    the failure class it was built to catch.**

    So the same seven real files are retained as a REGRESSION CORPUS under
    `repaired`, and the assertion is now that each of them PINS. It lands
    on exactly the same real tree, and it is strictly stronger: it also
    fails if any of the seven regresses to reporting-without-pinning.
    """
    repaired = pa.read_repaired()
    assert len(repaired) == 7, (
        "the repaired corpus is not the seven files verified by hand — the "
        "audit's only real-tree landing check has been emptied")
    rep = pa.audit_repo()
    still_broken = repaired & set(rep["imported_not_called"])
    assert not still_broken, (
        f"REGRESSION: {sorted(still_broken)} report provenance and no longer "
        "pin it. Call `engine_preamble()` ABOVE the first import that loads "
        "the engine — below it, the call is a no-op on resolution.")
    # NON-VACUITY, POSITIVELY. `imported_not_called` is an absence, and an
    # audit that scanned the wrong subtree satisfies an absence by finding
    # nothing. So assert the PRESENCE of the binding AND the call, per file,
    # from the AST — the same evidence the violation verdict is built from.
    for f in sorted(repaired):
        assert f.endswith(".py") and os.path.isfile(os.path.join(ROOT, f))
        one = pa.audit_file(os.path.join(ROOT, f))
        assert one["imports_preamble"], (
            f"{f} no longer binds engine_preamble — the audit is reading a "
            "file that cannot violate the rule, which is not the same as a "
            "file that obeys it. DEAD INSTRUMENT, not a clean tree.")
        assert one["calls_preamble"], f"{f} binds engine_preamble and does not call it"
    # The floor itself must stay empty: the gate binds every file now.
    assert pa.read_floor() == set(), (
        "results/preamble_audit_floor.json has regained exemptions. A floor "
        "that never shrinks is an exemption list wearing a different name.")


def test_the_preamble_gate_binds_NEW_violations_only():
    """BOTH DIRECTIONS on the gate itself.

    Green: the live tree introduces nothing beyond the floor.
    Red:   a violation absent from the floor is reported.
    """
    assert pa.new_violations() == [], (
        "a NEW §10 rule 3 violation: this file binds engine_preamble and "
        "never calls it. One line fixes it — call it. Do NOT add it to "
        "results/preamble_audit_floor.json.")

    # RED direction, with a floor that deliberately does not cover the plant.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = os.path.join(td, "t")
        os.makedirs(os.path.join(root, "scripts"))
        n = _nonce(_rng(2))
        with open(os.path.join(root, "scripts", f"v_{n}.py"), "w") as fh:
            fh.write("from domains import engine_provenance as ep\n"
                     "print(ep.provenance_line())\n")
        floor = os.path.join(td, "floor.json")
        with open(floor, "w") as fh:
            json.dump({"known_violations": []}, fh)
        rep = pa.audit_tree([root], base=root)
        assert rep["imported_not_called"] == [f"scripts/v_{n}.py"]
        assert set(rep["imported_not_called"]) - pa.read_floor(floor), (
            "the gate did not report a violation absent from its floor")


def test_the_audit_sees_underscore_literals_a_grep_cannot():
    """Seeds 95100–95119, spent in the spelling that broke a real check.

    The supervisor's pre-launch seed check was `grep "90000"`, and
    `rung7_snr_pilot.py` draws `default_rng(90_000 + seed)`. The grep saw
    nothing and the allocation was rejected by the tool that parses.
    **THE INSTRUMENT MUST READ THE LANGUAGE, NOT THE TEXT.**

    This spends 95100–95119 through underscore literals and then asserts
    the AST scan of THIS FILE recovers them — an end-to-end demonstration
    on real source, not a unit test of a helper.
    """
    for i in range(_N_CTRL):
        assert _rng(i, underscore=True).integers(0, 10) >= 0

    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from seed_audit import measured_seeds  # noqa: PLC0415

    seen = measured_seeds([os.path.abspath(__file__)])
    assert _CTRL_BASE_US in seen, (
        f"the AST scan did not see default_rng({_CTRL_BASE_US}) written as "
        "an underscore literal — the same blindness as the grep, in the tool "
        "that was supposed to be immune to it")
    assert _CTRL_BASE in seen

    # And the grep it defeats, demonstrated rather than asserted from memory.
    # LOCATED BY AST, because the obvious version of this check — a substring
    # search of this file for the digit string — MATCHED ITSELF, which is the
    # substring-selector failure happening inside the test written to warn
    # about it. (It did. That is recorded in the results doc.)
    import ast
    raw = open(os.path.abspath(__file__), encoding="utf-8").read()
    segs = [ast.get_source_segment(raw, n)
            for n in ast.walk(ast.parse(raw))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "default_rng"]
    assert any("95_100" in (s or "") for s in segs), (
        "the underscore spelling is no longer exercised at a default_rng "
        "call site — this control has stopped testing what it was built for")
    assert not any(str(_CTRL_BASE_US) in (s or "") for s in segs), (
        "a default_rng call site spells the seed WITHOUT the underscore, so "
        "a grep would find it and the control proves nothing")


# ===========================================================================
# DEFECT 2 — THE LEDGER AND PREREG SEAMS
# ===========================================================================

def test_the_measured_ledger_record_is_CURRENT():
    """§11 rec #4, structural.

    THE NUISANCE MODE IS NAMED AND IT IS A TRUE POSITIVE: if you (or a rung
    merged under you) changed which seeds this tree draws, this goes red
    until the record is regenerated. That is the point — the old prose
    discipline failed precisely at the moment of writing a ledger row, and
    this moves the requirement to a moment nobody can miss.
    """
    fresh, msg = sr.record_is_fresh()
    assert fresh, msg


def test_the_freshness_gate_FIRES_on_a_stale_record(tmp_path):
    """POSITIVE CONTROL — seeds 95000–95019, randomised perturbations.

    Perturb ONE field of a committed record and require the gate to notice.
    A freshness gate that cannot detect staleness is the purest form of the
    instrument that has never been able to fail.
    """
    live = sr.ledger_measured_report()
    assert live["blocks"], "no declared ledger blocks parsed — dead scan"

    for i in range(_N_CTRL):
        rng = _rng(i)
        stale = json.loads(sr.render(live))
        idx = int(rng.integers(0, len(stale["blocks"])))
        block = stale["blocks"][idx]
        declared = tuple(block["declared"])
        block["measured_subranges"] = [[int(rng.integers(1, 10**6))] * 2]
        block["measured_seeds"] = int(rng.integers(1, 999))

        path = tmp_path / f"rec_{i}.json"
        path.write_text(json.dumps(stale, indent=1, sort_keys=True) + "\n")

        ok, msg = sr.record_is_fresh(str(path))
        assert not ok, (
            f"perturbed block {declared} and the gate stayed GREEN — it is "
            "not reading the field it claims to gate")
        # LANDING CHECK: the message must name the block I actually broke,
        # not merely say "something differs".
        assert f"block {declared[0]}-{declared[1]}" in msg, msg
        assert "domains.seed_record --write" in msg, (
            "a stale-record failure without its one-command remedy is "
            "ceremony, and ceremony is what nobody runs")

    missing = tmp_path / "nope.json"
    ok, msg = sr.record_is_fresh(str(missing))
    assert not ok and "MISSING" in msg


def test_a_perturbed_DUPLICATE_declared_range_is_still_named(tmp_path):
    """REGRESSION — the bug this rung's own control found in this rung.

    The §11 ledger repeats declared ranges on purpose ("0–13 (again)";
    1900–1999 appears twice). Keying the diff by `(lo, hi)` silently kept
    only the LAST row, so perturbing any earlier duplicate produced a
    correct STALE verdict with an EMPTY explanation. The top-level
    comparison still fired — which is exactly why this was nearly invisible.
    **Only the landing check ("name the block I broke") caught it.** A gate
    that cannot say what it caught is one nobody can act on.
    """
    live = sr.ledger_measured_report()
    dup = [tuple(b["declared"]) for b in live["blocks"]]
    repeated = {k for k in dup if dup.count(k) > 1}
    if not repeated:
        pytest.skip("the ledger no longer repeats a declared range")

    target = sorted(repeated)[0]
    first = next(i for i, b in enumerate(live["blocks"])
                 if tuple(b["declared"]) == target)
    stale = json.loads(sr.render(live))
    stale["blocks"][first]["measured_seeds"] = 424242

    path = tmp_path / "dup.json"
    path.write_text(json.dumps(stale, indent=1, sort_keys=True) + "\n")
    ok, msg = sr.record_is_fresh(str(path))
    assert not ok
    assert f"block {target[0]}-{target[1]}" in msg, msg


def test_the_record_is_DETERMINISTIC():
    """A record that varied run to run could not be gated for freshness,
    so every ordering in it is sorted and no timestamp is stored."""
    a = sr.render(sr.ledger_measured_report())
    b = sr.render(sr.ledger_measured_report())
    assert a == b


def test_the_record_PRICES_ITS_OWN_SILENCE():
    """A CHECK THAT PASSES WITH UNKNOWN SINKS HAS VERIFIED NOTHING.

    The record must carry the unresolved-sink count so a reader prices the
    silence instead of over-trusting a clean-looking artifact.
    """
    rec = sr.read_record()
    assert rec is not None
    assert rec["unresolved_sinks"] > 0, (
        "seed_audit reports ZERO unresolved sinks — it has 7 declared blind "
        "spots and hundreds of unresolvable sites, so zero means the "
        "counter died, not that the tree became transparent")
    assert "NEVER" in rec["_README"]


def test_every_new_prereg_records_its_check_claim_output():
    """§11 rec #7, structural — and THIS RUNG IS INSIDE IT.

    I generated the grandfather floor from `os.listdir` AFTER writing my own
    pre-registration, so my document landed in the exempt set and this gate
    was green on me for the reason that it never looked at me. Same shape as
    the seed-claim rung's silently-passing control and the supervisor's
    wrong-subtree injection. Corrected: `_GATE_AUTHOR_PREREG` is excluded
    from the floor, so this rung must satisfy its own gate.
    """
    floor = sr.read_prereg_floor()
    assert sr._GATE_AUTHOR_PREREG not in floor, (
        "the rung that installed this gate grandfathered itself — a gate "
        "that exempts its author has not been tested")
    assert sr._GATE_AUTHOR_PREREG in sr.prereg_files(), (
        "the gate author's pre-registration is missing from the tree")

    missing = sr.preregs_missing_claim()
    assert missing == [], (
        "these pre-registrations declare a seed block but record no "
        f"check_claim verdict: {missing}\n"
        "  Run:  python3 scripts/seed_claim.py <lo> <hi>\n"
        "  and paste the output into the pre-registration (§11 rec #7). "
        "Do NOT add the file to results/prereg_claim_floor.json.")


def test_the_prereg_gate_FIRES_and_a_MENTION_does_not_satisfy_it(tmp_path):
    """POSITIVE CONTROL — seeds 95100–95119, randomised documents.

    Three arms, because the failure I most expect is the middle one:
      * no claim at all           -> REPORTED
      * the WORDS but no verdict  -> REPORTED (a mention is not a record)
      * the tool's actual output  -> silent
    """
    root = tmp_path / "preregs"
    root.mkdir()
    floor = tmp_path / "floor.json"
    floor.write_text(json.dumps({"grandfathered": []}))

    expect_missing = []
    for i in range(_N_CTRL):
        rng = _rng(i, underscore=True)
        n = _nonce(rng)
        lo = int(rng.integers(1000, 900000))
        hi = lo + int(rng.integers(1, 999))

        bare = root / f"VISION_{n.upper()}_A_PREREG.md"
        bare.write_text(f"# {n}\n\nSeed block {lo}-{hi}. Hypothesis: none.\n")
        expect_missing.append(bare.name)

        talky = root / f"VISION_{n.upper()}_B_PREREG.md"
        talky.write_text(
            f"# {n}\n\nI ran check_claim on {lo}-{hi} and seed_claim.py said "
            "it was fine. Seed claim: clean.\n")
        expect_missing.append(talky.name)

        good = root / f"VISION_{n.upper()}_C_PREREG.md"
        good.write_text(
            f"# {n}\n\n```\nSEED CLAIM {lo}-{hi}: CLEAN -- no collision "
            "DETECTED.\n  Scope: 798 files with seed sinks; 482 UNRESOLVED "
            "sink sites tree-wide.\n```\n")

        # LANDING CHECK on the parser itself, per document.
        assert sr._claim_verdicts(good.read_text()) == [(lo, hi)]
        assert sr._claim_verdicts(talky.read_text()) == []

    missing = sr.preregs_missing_claim(str(root), floor_path=str(floor))

    assert len(missing) == 2 * _N_CTRL, (
        f"expected {2 * _N_CTRL} reported documents, got {len(missing)} — "
        "the plant is not where the gate looked")
    assert sorted(missing) == sorted(expect_missing)

    # Green direction: grandfathering silences it, and only it.
    all_floor = tmp_path / "all.json"
    all_floor.write_text(json.dumps({"grandfathered": sorted(
        p for p in os.listdir(root))}))
    assert sr.preregs_missing_claim(str(root), floor_path=str(all_floor)) == []


def test_my_own_footprint_is_what_i_declared():
    """§11 rec #4 APPLIED TO MYSELF — the non-vacuous self-audit.

    The seed-accounting rung audited its own footprint and found it had THE
    SAME SHAPE AS THE DEFECT IT WAS AUDITING (two scattered sub-ranges at
    10% fill). So: measure mine, against what §0.3 of my pre-registration
    declared IN ADVANCE, and report the MEASURED sub-ranges rather than the
    declared block.
    """
    mine = sr.measured_subranges([os.path.relpath(os.path.abspath(__file__), ROOT)])
    assert mine == [[95000, 95019], [95100, 95119]], (
        f"measured footprint {mine} is not the declared "
        "[[95000, 95019], [95100, 95119]] — either I spent seeds I did not "
        "declare, or the scan cannot see the ones I did")

    total = sum(hi - lo + 1 for lo, hi in mine)
    assert total == 40, total
    # The declared BLOCK is 1000 wide; I measure 40. Fill 0.04 — which is
    # WORSE than the ledger's 0.100 median and is recorded, not hidden.
    # That is exactly the over-declaration rec #4 exists to expose, and it
    # is mine.
