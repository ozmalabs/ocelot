"""P7 acceptance names frozen by COGNITION_QUALIA_ACQUISITION_CONTRACT.md.

The graph-rule producer is introduced in P7.03. Keep these explicit pending
cases skipped until that seed and its graph fixtures exist; do not count them
as passing mechanism tests before activation.
"""
import pytest


pytestmark = pytest.mark.skip(reason="P7.03 acquisition rules not implemented yet")


def test_no_target_axis_in_inputs():
    raise NotImplementedError("implemented with P7.03 graph fixture")


def test_finer_grain_cannot_fake_missing_dimension():
    raise NotImplementedError("implemented with P7.03 graph fixture")


def test_acquired_axis_has_episode_witnesses():
    raise NotImplementedError("implemented with P7.03 graph fixture")


def test_negative_evidence_can_revise():
    raise NotImplementedError("implemented with P7.03 graph fixture")
