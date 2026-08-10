"""BATCH-APPLY THE DRIVE RULES — the durable gate.

Pre-registration: `VISION_BATCH_APPLY_PREREG.md` (committed 767f0850).
Results: `VISION_BATCH_APPLY_RESULTS.md`.

WHAT THIS GUARDS. The claim is that batching the five `vision_change` drive
rules is EXACT — it removes work without moving any verdict. That claim has
two halves and a silent-failure mode, and this file gates all three:

  1. CORRECTNESS — the per-cell state the drive phase produces must be
     BITWISE identical with the flag on and off. Compared by exact `repr`,
     never rounded and never toleranced: a tolerance on this gate would be
     metric surgery (PROTOCOL §5) on the one check that matters.
  2. THE EFFECT — the number of Python->Rust drive entries must collapse to
     the floor band and STOP GROWING WITH N. Without this half, a silent
     regression to `apply_rule_once` would still pass check 1 (it is the
     path check 1 compares against!) and the rung's result would evaporate
     with nothing going red.
  3. THE WIRING — `apply_rule_batch` must exist on the native substrate, the
     adapter must actually call it, and the seed must actually set the flag.
     `VISION_BATCH_APPLY_PREREG.md` §2 records that this rung's predecessor
     recommended setting the seed flag ALONE, which would have been inert:
     `apply_rule_once` never reads `batch`. An inert intervention that reports
     a plausible null is this arc's most-repeated failure (eleven inert
     instruments), so the wiring is asserted rather than assumed.

Cargo cannot link this crate for `cargo test` (`extension-module` is set
unconditionally — pre-existing), so the Rust-level checks live here, against
the SHIPPED engine. That is the stronger place for them anyway: it tests the
binary that actually produces the numbers.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "seeds", "vision_change.json")

pytest.importorskip("substrate_rs")

import domains.seed_registry  # noqa: F401,E402
import domains.wave_world as wave_world  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains.lateral_world import add_lateral_retina, set_lat_params  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from substrate_rs import _native  # noqa: E402

# Every attribute the drive phase can touch, plus the downstream wave
# attributes that would reveal drift ESCAPING the phase. Fixed here so the
# comparison cannot later be narrowed to whatever happens to match (§5).
CELL_ATTRS = (
    "driven", "dstep_med", "dstep_on", "dstep_off", "dstep_sus",
    "lum_ref", "ref_n", "ref_step",
    "lum_raw", "lum_prev", "lum_seen",
    "state", "activated_at", "last_burst",
)

GRID = 12
TICKS = 8


def _frames(g, n=6, seed=11):
    """A smooth drifting field — the same construction the measurement uses.
    Fresh per-tick noise would be maximally non-sparse BY CONSTRUCTION."""
    rng = np.random.default_rng(seed)
    base = rng.random((g + n + 2, g + n + 2)).astype(np.float32)
    for _ in range(6):
        base = (base + np.roll(base, 1, 0) + np.roll(base, -1, 0)
                + np.roll(base, 1, 1) + np.roll(base, -1, 1)) / 5.0
    return [np.ascontiguousarray(base[i:i + g, i:i + g]) for i in range(n)]


def _strip_batch(tmp_path) -> str:
    """A seed copy with `batch` stripped from every rule. The control arm
    varies the graph DATA; it does not take a different code path."""
    with open(SEED) as fh:
        seed = json.load(fh)
    for r in seed.get("rules", []):
        r.pop("batch", None)
    p = os.path.join(str(tmp_path), "vision_change_nobatch.json")
    with open(p, "w") as fh:
        json.dump(seed, fh)
    return p


def _run(g=GRID, ticks=TICKS):
    """Boot the assembled eye and drive it. Returns (state record, drive-entry
    count) — the correctness witness and the effect witness together."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_lateral"])
    world = WaveWorld(s, h=g, w=g, seed=0, fovea_radius=0)
    add_lateral_retina(world)
    s.set_attr(s.nodes("WaveParams")[0], "propagate", 1.0)
    for cp in s.nodes("ChangeParams"):
        s.set_attr(cp, "change", 1.0)
        s.set_attr(cp, "sustain", 1.0)
    set_lat_params(world, lateral=1.0)

    frames = _frames(g)
    _native.Substrate.scale_audit_reset()
    _native.Substrate.scale_audit_set_enabled(True)
    for i in range(ticks):
        world.step(ignite_k=1 if i % 5 == 0 else 0, frame=frames[i % len(frames)])
    _native.Substrate.scale_audit_set_enabled(False)
    calls = dict(_native.Substrate.scale_audit_snapshot())["epochs_apply_once"]

    rec = []
    for key in sorted(world.cells):
        at = s.node(world.cells[key])["attrs"]
        rec.append((key, tuple(repr(at.get(a)) for a in CELL_ATTRS)))
    return rec, calls


@pytest.fixture
def arms(tmp_path, monkeypatch):
    """The two arms, run in one process against one binary, so the difference
    cannot be confounded by which engine produced it."""
    on_rec, on_calls = _run()
    monkeypatch.setattr(wave_world, "_CHANGE_SEED", _strip_batch(tmp_path))
    off_rec, off_calls = _run()
    return (on_rec, on_calls), (off_rec, off_calls)


# --- 3. THE WIRING -----------------------------------------------------------

def test_native_exposes_apply_rule_batch():
    """Without this method the seed flag is INERT: `apply_rule_once` never
    reads `batch` (`substrate.rs`), so the flag alone changes nothing."""
    assert hasattr(_native.Substrate, "apply_rule_batch"), (
        "engine predates apply_rule_batch — rebuild via scripts/engine_build.sh")


def test_drive_phase_dispatches_to_the_batch_entry():
    with open(os.path.join(ROOT, "domains", "wave_world.py")) as fh:
        body = fh.read()
    assert "nat.apply_rule_batch(idx)" in body, (
        "_drive_phase no longer calls apply_rule_batch — the intervention is "
        "silently reverted and every count in VISION_BATCH_APPLY_RESULTS.md "
        "would be unreproducible")


def test_all_five_drive_rules_carry_the_batch_flag():
    with open(SEED) as fh:
        seed = json.load(fh)
    flags = {r["name"]: bool(r.get("batch", False)) for r in seed["rules"]}
    assert len(flags) == 5, flags
    assert all(flags.values()), flags


# --- 1. CORRECTNESS ----------------------------------------------------------

def test_batch_and_serial_produce_bitwise_identical_state(arms):
    """THE GATE. Batching reorders binding application within a pass; the
    fixpoint is only order-independent for CONFLUENT rules. The prereg argued
    confluence from the rule bodies (no retraction; self-narrowing only;
    binding-disjoint write-sets; the one non-local read is of an attribute no
    rule writes). This measures it."""
    (on_rec, _), (off_rec, _) = arms
    assert len(on_rec) == len(off_rec)
    diffs = []
    for (k1, v1), (k2, v2) in zip(on_rec, off_rec):
        assert k1 == k2
        if v1 != v2:
            diffs.append((k1, [(a, x, y) for a, x, y in zip(CELL_ATTRS, v1, v2)
                               if x != y]))
    assert not diffs, (
        f"{len(diffs)} cell(s) differ between batch and serial application. "
        f"This is NOT a batching bug to tune around — it means the run_rules "
        f"fixpoint is ORDER-DEPENDENT on this path, which bears on the async "
        f"collapse plan. First 3: {diffs[:3]}")


def test_the_accumulator_rule_is_exact(arms):
    """`ch_adapt_ref` is the read-modify-write accumulator
    (`lum_ref += (lum_raw - lum_ref)/max(ref_n,1)`; `ref_n += 1`) — the rule
    the prereg named as the one that would break FIRST and in the LAST DECIMAL
    if the cell<->binding bijection ever failed. Asserted separately from the
    bulk comparison so a failure names the mechanism instead of a cell count."""
    (on_rec, _), (off_rec, _) = arms
    i_ref, i_n = CELL_ATTRS.index("lum_ref"), CELL_ATTRS.index("ref_n")
    for (k, v1), (_, v2) in zip(on_rec, off_rec):
        assert v1[i_ref] == v2[i_ref], (k, v1[i_ref], v2[i_ref])
        assert v1[i_n] == v2[i_n], (k, v1[i_n], v2[i_n])


# --- 2. THE EFFECT -----------------------------------------------------------

def test_drive_entries_collapse_to_the_floor_band(arms):
    """The floor FALLS OUT (PROTOCOL §13) and its band was registered BEFORE
    measurement: retaining `while ...: pass` costs one extra EMPTY quiescence
    pass per rule that fired, so the floor is between `n_rules * ticks` and
    `2 * n_rules * ticks`. Neither bound is chosen — `n_rules` is read from the
    seed file and `ticks` from the schedule."""
    (_, on_calls), (_, off_calls) = arms
    with open(SEED) as fh:
        n_rules = len(json.load(fh)["rules"])
    lo, hi = n_rules * TICKS, 2 * n_rules * TICKS
    assert lo <= on_calls <= hi, (on_calls, lo, hi)
    assert on_calls < off_calls, (on_calls, off_calls)


def test_drive_entries_do_not_grow_with_the_field(monkeypatch, tmp_path):
    """THE SCALING CLAIM, not just the point value. The wall was the PRODUCT of
    (entries proportional to N) x (a scan proportional to N). This asserts the
    first factor is now CONSTANT — quadrupling the cell count must not move the
    entry count at all. A regression to `apply_rule_once` would still pass the
    bitwise gate above (it IS that gate's reference arm) and would only be
    caught here."""
    _, small = _run(g=8)
    _, large = _run(g=16)
    assert small == large, (
        f"drive entries grew {small} -> {large} when cells went 64 -> 256; "
        "the per-binding re-derivation is back")


def test_a_rule_without_the_flag_still_goes_one_binding_at_a_time(tmp_path,
                                                                 monkeypatch):
    """THE DELEGATION PATH. `apply_rule_batch` must be `apply_rule_once`
    verbatim for a rule that does NOT set `batch` — that is what makes the §9
    "defaults preserve committed results" claim structural rather than tested,
    and it is why the dispatch was NOT put inside `apply_rule_once` (two
    `vision_settle` rules already set the flag and are driven by other
    callers)."""
    monkeypatch.setattr(wave_world, "_CHANGE_SEED", _strip_batch(tmp_path))
    _, small = _run(g=8)
    _, large = _run(g=16)
    assert large > small, (
        "an unflagged rule must still re-derive per binding; if this is now "
        "constant, apply_rule_batch is batching rules that never opted in")
