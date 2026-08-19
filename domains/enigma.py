"""Public Enigma API.

``toy_enigma`` is retained as the compatibility module used by the original
research scripts. New callers should import from here: the implementation now
supports the historical I–V rotor pool, ring-aware turnover, explicit
decryption, and M4-style Beta/Gamma machines.
"""

from domains.toy_enigma import (  # noqa: F401
    A,
    N,
    Enigma,
    Plugboard,
    Rotor,
    Settings,
    REFLECTOR_A,
    REFLECTOR_B,
    REFLECTOR_C,
    REFLECTOR_THIN_B,
    REFLECTOR_THIN_C,
    REFLECTORS,
    ROTOR_WIRINGS,
    decrypt,
    encrypt,
    random_settings,
)

__all__ = [
    "A", "N", "Enigma", "Plugboard", "Rotor", "Settings",
    "REFLECTOR_A", "REFLECTOR_B", "REFLECTOR_C", "REFLECTOR_THIN_B",
    "REFLECTOR_THIN_C", "REFLECTORS", "ROTOR_WIRINGS", "decrypt",
    "encrypt", "random_settings",
]
