"""P8.01 acceptance names; native induction is implemented in P8.02."""
import pytest

pytestmark = pytest.mark.skip(reason="P8.02 process-induction graph rules not implemented yet")


def test_effect_learned_from_trace():
    raise NotImplementedError("P8.02 observed transition induction")


def test_unseen_object_binding():
    raise NotImplementedError("P8.02 typed object transfer")


def test_counterexample_revises_model():
    raise NotImplementedError("P8.02 counterexample handling")


def test_indistinguishable_hypotheses_retained():
    raise NotImplementedError("P8.02 hypothesis portfolio")
