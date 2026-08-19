"""Regression coverage for the upgraded historical Enigma path."""

import random

from domains.toy_enigma import (
    Enigma,
    Plugboard,
    REFLECTOR_B,
    REFLECTOR_THIN_B,
    Rotor,
    Settings,
    random_settings,
)
from domains.enigma_blind import decrypt_fast, scrambler_perms, to_idx
from domains.enigma_recoverer import TrigramLM
from domains.enigma_solver import (
    EnigmaProblem,
    graph_crib_admissibility,
    solve,
)


def test_explicit_decrypt_is_reciprocal_and_filters_formatting():
    settings = Settings(("I", "II", "III"), (0, 0, 0), (1, 2, 3), "AB CD")
    plaintext = "The quick, brown fox!"
    ciphertext = settings.encrypt(plaintext)

    assert settings.decrypt(ciphertext) == "THEQUICKBROWNFOX"
    assert settings.decrypt(ciphertext) == settings.encrypt(ciphertext)


def test_ring_setting_changes_turnover_window():
    # Rotor I's raw notch is Q. With ring B, Q is reached through the window
    # at P; this is the physical alphabet-ring turnover rule.
    assert Rotor.make("I", ring=0, pos=ord("Q") - 65).at_notch()
    assert Rotor.make("I", ring=1, pos=ord("P") - 65).at_notch()
    assert not Rotor.make("I", ring=1, pos=ord("Q") - 65).at_notch()


def test_m4_roundtrip_and_stationary_greek_rotor():
    settings = Settings(
        ("BETA", "II", "IV", "I"),
        (0, 1, 2, 3),
        (0, 1, 2, 3),
        "",
        REFLECTOR_THIN_B,
        1,
    )
    machine = Enigma.build(
        list(settings.rotor_order), settings.ring, settings.start,
        settings.plug, settings.reflector, settings.stationary_rotors,
    )
    ciphertext = settings.encrypt("THEQUICKBROWNFOX")

    assert settings.decrypt(ciphertext) == "THEQUICKBROWNFOX"
    assert machine.rotors[0].pos == 0
    assert machine.stationary_rotors == 1


def test_precomputed_scrambler_matches_full_machine_for_m4():
    settings = Settings(
        ("GAMMA", "III", "IV", "II"),
        (0, 0, 0, 0),
        (2, 4, 6, 8),
        "AE BF",
        REFLECTOR_THIN_B,
        1,
    )
    ciphertext = settings.encrypt("THEQUICKBROWNFOXJUMPS")
    perms = scrambler_perms(
        settings.rotor_order, settings.ring, settings.start, len(ciphertext),
        settings.reflector, settings.stationary_rotors,
    )
    plug_map = Plugboard.from_letters(settings.plug)._map

    assert decrypt_fast(perms, plug_map, to_idx(ciphertext)) == to_idx(
        "THEQUICKBROWNFOXJUMPS"
    )


def test_historical_rotor_pool_can_sample_choose_three_of_five():
    settings = random_settings(
        random.Random(7),
        rotor_pool=("I", "II", "III", "IV", "V"),
        rotor_count=3,
    )
    assert len(settings.rotor_order) == 3
    assert len(set(settings.rotor_order)) == 3
    assert set(settings.rotor_order) <= {"I", "II", "III", "IV", "V"}


def test_solver_shaped_crib_front_door_returns_answer_and_diagnostics():
    settings = Settings(("I", "II", "III"), (0, 0, 0), (1, 2, 3), "AB")
    plaintext = "THEQUICKBROWNFOXJUMPS"
    lm = TrigramLM()
    lm.train((plaintext + "OVERTHELAZYDOG") * 30)
    result = solve(
        EnigmaProblem(
            ciphertext=settings.encrypt(plaintext), crib="THEQUICK", known_plug="AB"
        ),
        lm,
    )

    assert result["status"] == "resolved"
    assert result["answer"].rotor_order == settings.rotor_order
    assert result["answer"].start == settings.start
    assert result["diagnostics"]["evaluated"] == result["diagnostics"]["brute_force"]


def test_crib_admissibility_is_a_native_graph_cut():
    settings = Settings(("I", "II", "III"), (0, 0, 0), (1, 2, 3), "AB")
    plaintext = "THEQUICKBROWNFOX"
    ciphertext = settings.encrypt(plaintext)
    problem = EnigmaProblem(ciphertext, crib=plaintext[:8], known_plug="AB")

    def candidate(start):
        return {
            "ciphertext": ciphertext,
            "crib": plaintext[:8],
            "crib_offset": 0,
            "rotor_order": "I II III",
            "ring": "0 0 0",
            "start": " ".join(map(str, start)),
            "plugboard": "AB",
            "reflector": REFLECTOR_B,
            "search_order": ["I", "II", "III"],
            "search_start": list(start),
        }

    result = graph_crib_admissibility(
        problem,
        [candidate(settings.start), candidate((0, 0, 0))],
    )

    assert result["evaluated"] == 2
    assert result["rejected"] == 1
    assert result["survivors"][0]["search_start"] == list(settings.start)


def test_bombe_grammar_returns_a_partial_steckering_witness():
    settings = Settings(("I", "II", "III"), (0, 0, 0), (1, 2, 3), "AB")
    plaintext = "THEQUICKBROWNFOX"
    problem = EnigmaProblem(settings.encrypt(plaintext), crib=plaintext)
    candidate = {
        "ciphertext": problem.ciphertext,
        "crib": plaintext,
        "crib_offset": 0,
        "rotor_order": "I II III",
        "ring": "0 0 0",
        "start": "1 2 3",
        "reflector": REFLECTOR_B,
        "search_order": ["I", "II", "III"],
        "search_start": [1, 2, 3],
    }

    result = graph_crib_admissibility(problem, [candidate], mode="bombe")

    assert result["evaluated"] == 1
    assert isinstance(result["survivors"][0]["bombe_witness"], str)
