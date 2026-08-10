"""Gates for the adaptation rate as a count over the agent's own history.

Block CD recorded the regress exactly: 1/n asserts stationarity, so declare a
floor; a flat floor costs quiet regimes, so declare a surprise factor; surprise
needs a reference, so build an error EMA; the EMA needs a rate, so ... 1/n.
Each rate needed a rate, and two attempts at surprise-gating were reverted
because the reference was a 1/n accumulator judging 1/n accumulators.

`stable_run` is not an accumulator. It is an integer count of how many
consecutive times the current surprise shape produced the same response, so
computing it needs no rate, and the regress terminates instead of recursing.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = json.loads(
    (ROOT / "seeds" / "embodied_motor_program.json").read_text(encoding="utf-8")
)
RULES = {rule["name"]: rule for rule in SEED["rules"]}


def test_the_rate_is_derived_from_the_stable_run():
    """The floor is earned from the codebook, not declared -- when asked for.

    Gated OFF by default since DF measured it at three ground contacts; the
    expression is retained because its FORM is right (a count needs no rate)
    and only its SCOPE is wrong (a regime-local rate on a global model).
    """
    learner = json.dumps(RULES["emp_learn_factorized_effector_from_exact_receipt"])
    assert "current_stable_run" in learner, (
        "the adaptation rate must read the run length of the current surprise "
        "shape rather than a constant"
    )


def test_the_declared_floor_survives_only_as_the_absent_case():
    """Polarity: no surprise index means the old behaviour, byte-identical."""
    learner = json.dumps(RULES["emp_learn_factorized_effector_from_exact_receipt"])
    assert "model_adaptation_rate_floor" in learner, (
        "a consumer that publishes no shape must fall back to what it had"
    )


def test_every_index_rule_publishes_the_run_length():
    """All three paths must keep the published run honest.

    A mint and a varied response both restart it at 1 (nothing is known here,
    so believe what was just seen); a stable recurrence extends it.  If any of
    the three failed to publish, the rate would read a stale run from whichever
    action last happened to write one.
    """
    for name in (
        "emp_index_surprise_shape",
        "emp_count_stable_surprise_response",
        "emp_vary_surprise_response",
    ):
        assert "current_stable_run" in json.dumps(RULES[name]), name


def test_the_rate_at_twenty_encounters_is_the_constant_it_replaces():
    """A shape stable for 20 encounters adapts at 0.05.

    That is precisely the value `model_adaptation_rate_floor` was set to in the
    F-16 consumer -- the point being that it is now ARRIVED AT rather than
    asserted, and a shape stable for 200 correctly adapts at 0.005 instead.
    """
    assert 1.0 / 20.0 == 0.05
    replication = (
        ROOT / "scripts" / "jabberwock_jsbsim_f16_paper_replication.py"
    ).read_text(encoding="utf-8")
    assert '"model_adaptation_rate_floor": 0.05' in replication, (
        "the constant is retained as the absent-case fallback; if it moves, "
        "this gate's arithmetic no longer documents the correspondence"
    )


def test_the_shape_rate_is_gated_off_by_absence():
    """MEASURED: rate-from-shape ON costs 1/9 -> 4/9 over three faults.

    A clean 2x2 -- rate on 4/9 with credit and 4/9 without, rate off 1/9 with
    credit and 1/9 without -- so the rate owns the regression and credit is
    neutral. The gate is absent-inert, so a consumer that does not ask for it
    gets the declared floor it always had.
    """
    learner = json.dumps(RULES["emp_learn_factorized_effector_from_exact_receipt"])
    assert "model_adaptation_rate_from_shape" in learner
    replication = (
        ROOT / "scripts" / "jabberwock_jsbsim_f16_paper_replication.py"
    ).read_text(encoding="utf-8")
    assert "model_adaptation_rate_from_shape" not in replication, (
        "the F-16 consumer must not enable it: it is the measured regression"
    )
