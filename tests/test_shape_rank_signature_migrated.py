"""Native exposure checks for the P4 finite-difference signature Term."""
from substrate_rs import _native


def _term():
    return {
        "type": "ShapeRankSignature",
        "samples": {"type": "Var", "name": "samples"},
        "order": {"type": "Var", "name": "order"},
        "width": {"type": "Lit", "value": 8},
    }


def test_native_shape_rank_signature_matches_legacy_fixtures():
    substrate = _native.Substrate()
    samples = [0, 1, 5, 14]
    expected = (
        (0, 1, 2, 3, 0, 0, 0, 0),
        (0, 1, 2, 0, 0, 0, 0, 0),
        (0, 1, 0, 0, 0, 0, 0, 0),
        (2, 0, 0, 0, 0, 0, 0, 0),
    )
    for order, signature in enumerate(expected):
        assert substrate.evaluate(_term(), {"samples": samples, "order": order}) == signature


def test_native_shape_rank_signature_rejects_invalid_and_nonfinite_inputs():
    substrate = _native.Substrate()
    assert substrate.evaluate(_term(), {"samples": [0.0, float("nan")], "order": 0}) is None
    assert substrate.evaluate(_term(), {"samples": [1, 2], "order": 3}) is None
    assert substrate.evaluate(_term(), {"samples": [1] * 65, "order": 0}) is None


def test_native_shape_rank_signature_is_pure():
    substrate = _native.Substrate()
    before = substrate.nodes()
    substrate.evaluate(_term(), {"samples": [0, 1, 5, 14], "order": 2})
    assert substrate.nodes() == before
