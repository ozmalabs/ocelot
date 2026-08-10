"""tests/test_exact_invariant_migrated.py — gates for the ARC5 numerics
class-C fixes (PROGRAM_SYNTHESIS_ARC5_NUMERICS_FLOATS.md c1-12, c1-14;
results/arc5_numerics_float_audit.json).

Both sites were "the spec implies a float, the problem does not" cases:

  * c1-14 (`domains/discriminative_invention.py`): the Fisher-discriminant
    test computed `std = var ** 0.5` (a genuine, generically-irrational
    square root) and persisted it, then a graph-native Rule decided band
    separability off it. `install_analyse_rule`'s decision now reads only
    `a_var`/`b_var` (never a std) through `_fisher_separates_term`, a
    sqrt-free EXACT reformulation (derived by isolating and squaring each
    square root in turn — see that function's docstring).

  * c1-12 (`domains/acoustic_resolution.py`): raw cochlear band-energy
    means were `set_attr`'d directly as Python floats, read only by
    ORDER predicates (`Gt`, in `formant_features.py`'s peak detector and
    elsewhere). `enrich_sign_bands` now persists a fixed-point Int
    (`_band_fixed_point`, scale 2**32) instead.

Both are reformulations, not redesigns: this file's job is to PROVE the
reformulation changes no decision, not merely to exercise the new code.

  (i)   Fisher verdict-identity: the REAL `analyse_confusion_band` Rule is
        run (via `install_analyse_rule` + the native rule engine, not a
        Python reimplementation of the new logic) against a battery of
        synthetic ConfusionBand cases spanning both sides of the original
        std-based threshold and near it, and its verdict is checked against
        the ORIGINAL std-based formula, reproduced independently here (the
        module no longer contains that code, so this is a real external
        reference, not an echo of the fix).

  (ii)  Ordering identity: `enrich_sign_bands`'s fixed-point representation
        is checked, over many synthetic trajectories, to preserve every
        pairwise `>` relationship among a sign's own bands relative to the
        original raw-float computation (reproduced independently here,
        the same way) — the exact property `formant_features._peak_term`
        and `dynamics_features._rise_term` depend on.

  (iii) A mechanical source check that each module's OWN decision no longer
        touches an irrational-valued quantity: `enrich_sign_bands` never
        `set_attr`s a raw float band value (only the fixed-point int), and
        `_fisher_separates_term` (the Term-tree `analyse_confusion_band`
        actually evaluates) references only a_var/b_var, never a_std/b_std,
        and builds no Div against a sum of stds.

HONEST RESIDUAL (documented, not hidden — see PROGRAM_SYNTHESIS_ARC5_SUMMARY.md):
`_stats` in discriminative_invention.py still ALSO computes and persists
`a_std`/`b_std` on ConfusionBand nodes. This is because two modules outside
this fix's file ownership for this pass — `domains/pairwise_recognition.py`
and `domains/teacher_hook.py` — read `ConfusionBand.a_std`/`b_std` directly
(with a bare `.get(key, 0.0)` fallback) for their OWN, independent
Fisher-style decisions; dropping the attr would silently zero it out under
their fallback and change THEIR verdicts — an unrelated decision this pass
must not alter without also migrating those two files (out of scope here).
So the persisted-irrational-attr elimination is complete for the module's
OWN decision (the Rule gated by test (i)/(iii) below) but the ConfusionBand
node as a whole still carries a_std/b_std for those two external readers.
`test_a_std_b_std_still_present_for_external_readers` pins this residual so
it cannot silently disappear (which would mean someone "fixed" it by
deleting the attr and quietly breaking those two files instead).
"""
from __future__ import annotations

import inspect
import math
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for _p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

pytest.importorskip("substrate_rs")
import substrate_rs as srs  # noqa: E402
import numpy as np  # noqa: E402

from domains import discriminative_invention as di  # noqa: E402
from domains import acoustic_resolution as ar  # noqa: E402


# =============================================================================
# (i) Fisher verdict-identity (discriminative_invention.py, c1-14)
# =============================================================================

def _old_fisher_decision(a_mean, b_mean, a_var, b_var, min_separation,
                         eps=1e-6) -> bool:
    """The ORIGINAL (pre-fix) std-based Fisher test — reproduced
    independently here (the module no longer contains this code at all)
    as the reference the new sqrt-free rule must match."""
    a_std = math.sqrt(a_var)
    b_std = math.sqrt(b_var)
    fisher = abs(a_mean - b_mean) / (a_std + b_std + eps)
    return fisher > min_separation


def _fresh_rule():
    """A brand-new Substrate + installed analyse rule, PER CASE (never
    shared across parametrized cases) — `apply_rule_once` fires at most one
    pending match per call, so sharing a substrate across many bands would
    make later cases starve earlier ones of firing turns, a test-harness
    bug that has nothing to do with the rule under test."""
    s = srs.Substrate()
    info = di.install_analyse_rule(s)
    s.add_production({
        "src": {"type": "DiscriminativeRoot", "var": "a"},
        "edge_type": "has_cband",
        "tgt": {"type": "ConfusionBand", "var": "b"},
        "provenance": "test_exact_invariant:has_cband"})
    return s, info["root"], info["rule_index"]


def _new_fisher_verdict(a_mean, b_mean, a_var, b_var, min_separation) -> bool:
    """Runs the REAL, production `analyse_confusion_band` Rule (via the
    native rule engine) on a synthetic ConfusionBand and returns whether it
    minted a discriminative hypothesis (`minted` flips to 1)."""
    s, root, rule_index = _fresh_rule()
    s.set_attr(root, "min_separation", float(min_separation))
    cb = s.add_node("ConfusionBand", {
        "true_word": "A", "pred_word": "B", "band": "b0", "minted": 0,
        "a_mean": float(a_mean), "a_var": float(a_var),
        "b_mean": float(b_mean), "b_var": float(b_var),
        "threshold": float((a_mean + b_mean) / 2.0),
        "high_word": "A" if a_mean >= b_mean else "B"})
    s.add_edge(root, "has_cband", cb)
    nat = s._inner if hasattr(s, "_inner") else s
    for _ in range(3):     # idempotent past the first successful fire
        nat.apply_rule_once(rule_index)
    return bool(s.node(cb)["attrs"].get("minted"))


# (a_var, b_var, min_separation) combos, each probed at a battery of
# a_mean/b_mean gaps placed relative to THAT combo's own old-formula
# boundary, on both sides and near it. frac == 1.0 (landing EXACTLY on the
# reconstructed boundary) is deliberately excluded: at an exact algebraic
# tie, the old formula (division then compare) and the new one (two
# squarings then compare) are different floating-point computation paths
# for the SAME mathematically-exact value, and can round to opposite sides
# of a strict `>` in the last bit — a universal float artifact of ANY two
# non-identical-but-equivalent implementations at a measure-zero tie, not a
# property of this reformulation specifically (confirmed by re-deriving the
# case in exact/symbolic arithmetic: the "true" answer at frac==1.0 is
# False, which is what BOTH formulas give away from the razor's edge).
_COMBOS = [
    (1.0, 1.0, 1.0), (0.01, 0.01, 1.0), (4.0, 9.0, 1.0),
    (0.0, 0.0, 1.0), (0.0, 4.0, 1.0), (2.0, 2.0, 2.5),
    (100.0, 0.5, 1.0), (1e-6, 1e-6, 1.0), (3.0, 0.02, 0.5),
    (0.5, 0.5, 3.0),
]
_FRACS = (0.0, 0.2, 0.5, 0.8, 0.9, 0.99, 0.999, 0.9999,
         1.0001, 1.001, 1.01, 1.1, 1.5, 2.0, 5.0, 10.0)


def _fisher_cases():
    cases = []
    for a_var, b_var, min_sep in _COMBOS:
        eps = 1e-6
        boundary = min_sep * (math.sqrt(a_var) + math.sqrt(b_var) + eps)
        for frac in _FRACS:
            d = boundary * frac if boundary > 0 else frac * 1e-3
            cases.append((0.0, d, a_var, b_var, min_sep))
    return cases


_FISHER_CASES = _fisher_cases()


@pytest.mark.parametrize("a_mean,b_mean,a_var,b_var,min_sep", _FISHER_CASES)
def test_fisher_verdict_identical_to_reference(a_mean, b_mean, a_var, b_var,
                                                min_sep):
    new = _new_fisher_verdict(a_mean, b_mean, a_var, b_var, min_sep)
    old = _old_fisher_decision(a_mean, b_mean, a_var, b_var, min_sep)
    assert new == old, (
        f"verdict diverged: a_mean={a_mean} b_mean={b_mean} a_var={a_var} "
        f"b_var={b_var} min_sep={min_sep} -> new={new} old={old}")


def test_fisher_battery_spans_both_verdicts():
    """Sanity: the battery above must contain BOTH True and False old-formula
    verdicts, else the identity test above would be checking nothing on one
    side of the threshold."""
    verdicts = {_old_fisher_decision(a, b, av, bv, m)
                for a, b, av, bv, m in _FISHER_CASES}
    assert verdicts == {True, False}


def test_a_std_b_std_still_present_for_external_readers():
    """Pins the documented residual: ConfusionBand still carries a_std/b_std
    (computed the same way as before) so pairwise_recognition.py /
    teacher_hook.py keep working unmodified. If this starts failing because
    the attrs were removed, those two files' `.get(key, 0.0)` fallback will
    silently zero out their own Fisher checks -- fix THAT (migrate them to
    a_var/b_var with the sqrt-free test) before removing this attr, don't
    just delete this test."""
    m, var, std = di._stats([1.0, 2.0, 3.0, 4.0])
    assert std == var ** 0.5 and std > 0
    root_cfg_path = ROOT / "seeds" / "discriminative_invention.json"
    assert root_cfg_path.exists()
    src = inspect.getsource(di.compute_confusion_band_stats)
    assert '"a_std":' in src and '"b_std":' in src
    assert '"a_var":' in src and '"b_var":' in src


# =============================================================================
# (ii) Ordering identity (acoustic_resolution.py, c1-12)
# =============================================================================

def _old_bands(patches, n: int, normalize: bool) -> list:
    """Reproduces the PRE-fix arithmetic of `enrich_sign_bands`'s inner loop
    exactly (raw float, no fixed-point scaling) — the module no longer
    computes this; it is an independent reference here."""
    vals = [float(g.mean())
            for g in np.array_split(np.asarray(patches, dtype=float), n)]
    if normalize and len(vals) > 1:
        m = sum(vals) / len(vals)
        vals = [v - m for v in vals]
    return vals


def _synthetic_trajectory(rng, lo=0.0, hi=5.0) -> list:
    """A random-but-deterministic 800-value (32 frames x 25 patches)
    cochlear trajectory: 25 patch base energies repeated over 32 frames with
    small per-frame jitter, including near-tied neighbouring patches (to
    stress rounding right where an order flip would be most likely)."""
    base = [rng.uniform(lo, hi) for _ in range(25)]
    # force a few neighbouring patches to be nearly tied
    for k in (3, 10, 17):
        base[k + 1] = base[k] + rng.uniform(-1e-4, 1e-4)
    traj = []
    for _f in range(32):
        for b in base:
            traj.append(b + rng.uniform(-1e-3, 1e-3))
    return traj


def _check_orders_match(substrate, sign, patches, resolutions, normalize):
    for n in resolutions:
        old_vals = _old_bands(list(patches), n, normalize)
        new_vals = [substrate.node(sign)["attrs"][f"band{n}_{i}"]
                    for i in range(n)]
        assert all(isinstance(v, int) for v in new_vals), (
            f"expected persisted band{n}_i to be an exact int, got {new_vals}")
        for i in range(n):
            for j in range(n):
                old_order = old_vals[i] > old_vals[j]
                new_order = new_vals[i] > new_vals[j]
                assert old_order == new_order, (
                    f"order flipped at n={n} i={i} j={j}: "
                    f"old={old_vals[i]!r} vs {old_vals[j]!r}; "
                    f"new={new_vals[i]!r} vs {new_vals[j]!r}")


def test_band_ordering_is_byte_identical_to_raw_float():
    import random
    rng = random.Random(20260801)
    s = srs.Substrate()
    for _trial in range(40):
        traj = _synthetic_trajectory(rng)
        sign = s.add_node("AcousticSign", {"trajectory": traj})
        n_added = ar.enrich_sign_bands(s, resolution=12, signs=[sign])
        assert n_added == 1
        patches = ar._patch_energies(traj)
        _check_orders_match(s, sign, patches, (3, 6, 12), normalize=False)


def test_band_ordering_is_byte_identical_to_raw_float_when_normalized():
    """Same gate, with the agent's per-sign baseline-subtraction hypothesis
    switched on (`set_normalization`) — negative values, the branch untested
    above."""
    import random
    rng = random.Random(7)
    s = srs.Substrate()
    ar.set_normalization(s, True)
    for _trial in range(40):
        traj = _synthetic_trajectory(rng, lo=-2.0, hi=5.0)
        sign = s.add_node("AcousticSign", {"trajectory": traj})
        n_added = ar.enrich_sign_bands(s, resolution=12, signs=[sign])
        assert n_added == 1
        patches = ar._patch_energies(traj)
        _check_orders_match(s, sign, patches, (3, 6, 12), normalize=True)


# =============================================================================
# (iii) mechanical source / attr checks
# =============================================================================

def test_acoustic_resolution_never_persists_the_raw_float_band_value():
    """c1-12's exact defect line -- `substrate.set_attr(sign, f"band{n}_{i}",
    v)` with `v` the raw numpy-mean float -- must be gone; every persisted
    band value must go through the fixed-point conversion."""
    src = inspect.getsource(ar.enrich_sign_bands)
    assert 'substrate.set_attr(sign, f"band{n}_{i}", v)' not in src
    assert 'substrate.set_attr(sign, f"band{n}_{i}", _band_fixed_point(v))' in src


def test_band_fixed_point_returns_an_exact_int():
    for v in (0.0, -0.0, 1.5, -3.25, 1e-9, -1e-9, 123.456):
        q = ar._band_fixed_point(v)
        assert isinstance(q, int)
        # round-trips to within one fixed-point unit of the original value.
        assert abs(q / ar._BAND_FIXED_POINT_SCALE - v) < 1.0 / ar._BAND_FIXED_POINT_SCALE


def test_fisher_separates_term_never_references_std():
    """The graph-resident DECISION (`analyse_confusion_band`, built from
    `_fisher_separates_term`) must never reference a_std/b_std or build a
    Div against a sum of stds -- it decides from a_var/b_var only, via the
    sqrt-free reformulation."""
    src = inspect.getsource(di._fisher_separates_term)
    assert "a_std" not in src and "b_std" not in src
    assert '"a_var"' in src and '"b_var"' in src
    # the RULE built from it must not carry the old formula's literal shape.
    install_src = inspect.getsource(di.install_analyse_rule)
    assert "a_std" not in install_src and "b_std" not in install_src
    assert "fisher = Div(" not in install_src


def test_stats_no_longer_computes_std_for_the_rules_own_decision():
    """`_stats` still returns a std (documented residual, for
    pairwise_recognition.py/teacher_hook.py -- see module docstring), but
    the RULE's OWN inputs (a_var/b_var) are what `compute_confusion_band_stats`
    feeds it, and `_fisher_separates_term` -- what the rule actually
    evaluates -- takes no std argument at all."""
    sig = inspect.signature(di._fisher_separates_term)
    assert list(sig.parameters) == ["CB", "R"]
    m, var, std = di._stats([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert var == pytest.approx(4.0)
    assert std == pytest.approx(2.0)
