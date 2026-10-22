"""P9.01 frozen invention acceptance names; later tasks implement them."""
import pytest

pytestmark = pytest.mark.skip(reason="P9.02/P9.04 process invention assertions not implemented yet")


def test_compose_order():
    raise NotImplementedError("P9.02 exact composition acceptance")


def test_noninvertible_no_inverse():
    raise NotImplementedError("P9.04 noninvertible effect acceptance")


def test_repair_not_exact_inverse():
    raise NotImplementedError("P9.04 separate repair contract")


def test_finite_probe_collision_not_law():
    raise NotImplementedError("P9.02 incomplete fingerprint collision")
