from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest
from evaluation.p5_r0.domain_cards import create_domain_cards, validate_domain_card, public_card
from evaluation.p5_r0.protocol import P5R0Error

def test_domain_cards_are_signed_and_public_projection_hides_family():
    cards = create_domain_cards(Ed25519PrivateKey.generate())
    assert [c["card_id"] for c in cards] == ["card-01", "card-02"]
    assert all(public_card(c)["domain_token"].startswith("opaque-") for c in cards)
    assert "private_domain_family" not in public_card(cards[0])

def test_domain_card_tamper_fails_closed():
    card = create_domain_cards()[0]
    card["modality"] = "embodied_sensorimotor"
    with pytest.raises(P5R0Error): validate_domain_card(card)
