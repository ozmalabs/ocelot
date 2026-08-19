"""Configurable historical Enigma model (owned pure logic, no net/fit).

THE FORWARD MODEL (donkey-clean): given SETTINGS + plaintext -> ciphertext.
Exact, deterministic, owned Python. This is the "f(params) -> signal" plug-in
for the solve-for-N machine (memory ozma_solve_for_n_is_general_not_speech):
the structure-recoverer inverts THIS to pull the settings out of ciphertext.

CONFIG (the original 3-rotor API remains the default):
  - 3 moving rotors, or a 4-rotor M4-style machine with a stationary Greek
    rotor on the left. Historical Wehrmacht rotors I–V and naval Greek rotors
    Beta/Gamma are included.
  - REFLECTOR: an involution with NO fixed point => guarantees no letter ever
    maps to itself (the structural weakness Turing's Bombe exploited).
  - ROTOR STEPPING: odometer with notch + the historical double-step anomaly.
  - PLUGBOARD (Steckerbrett): an involution (a set of disjoint swap pairs).
    Start small (0-3 pairs) to keep recovery tractable.

SETTINGS (the "N" to recover):
  - rotor_order : a permutation (left, middle, right) chosen from {I,II,III}
                  (3! = 6 orders if using all three; we draw 3 of the available).
  - ring        : ringstellung, 3 letters (Ringstellung) 0..25 each
  - start       : Grundstellung, 3 letters (start positions) 0..25 each
  - plug        : plugboard pairs (involution)

SEARCH-SPACE SIZES (stated explicitly):
  - rotor_order over 3 distinct rotors: 3! = 6
  - start positions: 26^3 = 17_576
  - ring positions: 26^3 = 17_576   (but ring is partially redundant with start;
                    only the relative ring-start offset of the FAST rotor matters
                    for a single short message before stepping — see notes)
  - plugboard with p pairs from 26 letters:
        p=0 -> 1
        p=1 -> C(26,2) = 325
        p=2 -> 325 * C(24,2) / 2 = 44_850
        p=3 -> 325*276*231/6 = 3_453_450
        p=10 (historical) -> 150_738_274_937_250 (~1.5e14)
  - FULL key space (order x start x ring x p=10) ~ 6 * 17576^2 * 1.5e14 ~ 2.8e26.

The Bombe trick: recover ROTOR settings WITHOUT enumerating the plugboard
(plugboard-independent constraint propagation), reducing the 1e26 wall to the
~1e5-1e6 rotor-only search. That is the convergence claim we test.

Encryption is SYMMETRIC: decrypt(c) = encrypt(c) under identical settings
(because the reflector makes the whole transform an involution at each position).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional

A = ord("A")
N = 26


def _perm(s: str) -> List[int]:
    return [ord(ch) - A for ch in s]


def _inv(perm: List[int]) -> List[int]:
    inv = [0] * len(perm)
    for i, p in enumerate(perm):
        inv[p] = i
    return inv


# Historical Enigma I rotor wirings + notch (the letter at which the rotor to its
# LEFT steps). Reflector B. These are the real wirings (public, declassified).
ROTOR_WIRINGS: Dict[str, Tuple[str, Optional[str]]] = {
    "I":   ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
    "II":  ("AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
    "III": ("BDFHJLCPRTXVZNYEIWGAKMUSQO", "V"),
    "IV":  ("ESOVPZJAYQUIRHXLNFTGKDCMWB", "J"),
    "V":   ("VZBRGITYUPSDNHLXAWMJQOFECK", "Z"),
    "BETA":  ("LEYJVCNIXWPBQMDRTAKZGFUHOS", None),
    "GAMMA": ("FSOKANUERHMBTIYCWLQPZXVGJD", None),
}
REFLECTOR_B = "YRUHQSLDPXNGOKMIEBFZCWVJAT"
REFLECTOR_A = "EJMZALYXVBWFCRQUONTSPIKHGD"
REFLECTOR_C = "FVPJIAOYEDRZXWGCTKUQSBNMHL"
REFLECTOR_THIN_B = "ENKQAUYWJICOPBLMDXZVFTHRGS"
REFLECTOR_THIN_C = "RDOBJNTKVEHMLFCWZAXGYIPSUQ"
REFLECTORS: Dict[str, str] = {
    "A": REFLECTOR_A, "B": REFLECTOR_B, "C": REFLECTOR_C,
    "THIN_B": REFLECTOR_THIN_B, "THIN_C": REFLECTOR_THIN_C,
}


@dataclass
class Rotor:
    name: str
    forward: List[int]      # wiring as permutation (right->left through rotor)
    backward: List[int]     # inverse wiring (left->right return path)
    notch: Optional[int]    # notch letter index; None for Greek rotors
    ring: int = 0           # ringstellung 0..25
    pos: int = 0            # current rotation 0..25

    @classmethod
    def make(cls, name: str, ring: int = 0, pos: int = 0) -> "Rotor":
        wiring, notch = ROTOR_WIRINGS[name]
        if not 0 <= ring < N or not 0 <= pos < N:
            raise ValueError("ring and position must be in 0..25")
        fwd = _perm(wiring)
        return cls(name, fwd, _inv(fwd),
                   None if notch is None else ord(notch) - A, ring, pos)

    def at_notch(self) -> bool:
        # The notch is mounted on the alphabet ring, so its window letter
        # changes with Ringstellung. The old model was correct only at AAA.
        return self.notch is not None and self.pos == (self.notch - self.ring) % N

    def step(self):
        self.pos = (self.pos + 1) % N

    def encode_fwd(self, c: int) -> int:
        # offset by (pos - ring), pass through wiring, undo offset
        shift = (self.pos - self.ring) % N
        c = (c + shift) % N
        c = self.forward[c]
        return (c - shift) % N

    def encode_bwd(self, c: int) -> int:
        shift = (self.pos - self.ring) % N
        c = (c + shift) % N
        c = self.backward[c]
        return (c - shift) % N


@dataclass
class Plugboard:
    """An involution: a set of disjoint swap pairs. Identity for unplugged letters."""
    pairs: Tuple[Tuple[int, int], ...] = ()
    _map: List[int] = field(default_factory=lambda: list(range(N)))

    def __post_init__(self):
        m = list(range(N))
        seen = set()
        for a, b in self.pairs:
            if not (0 <= a < N and 0 <= b < N) or a == b:
                raise ValueError("plugboard pairs must contain two distinct A-Z letters")
            if a in seen or b in seen:
                raise ValueError("plugboard pairs must be disjoint")
            seen.add(a); seen.add(b)
            m[a], m[b] = b, a
        self._map = m

    def swap(self, c: int) -> int:
        return self._map[c]

    @classmethod
    def from_letters(cls, spec: str) -> "Plugboard":
        # spec like "AB CD EF"
        pairs = []
        for tok in spec.split():
            if len(tok) != 2 or not tok.isalpha() or not tok.isascii():
                raise ValueError(f"invalid plugboard pair: {tok!r}")
            tok = tok.upper()
            pairs.append((ord(tok[0]) - A, ord(tok[1]) - A))
        return cls(tuple(pairs))


@dataclass
class Enigma:
    rotors: List[Rotor]            # left-to-right; M4 has a stationary Greek rotor first
    reflector: List[int]
    plugboard: Plugboard
    stationary_rotors: int = 0

    @classmethod
    def build(cls, rotor_order: List[str], ring: Tuple[int, ...],
              start: Tuple[int, ...], plug: str = "",
              reflector: str = REFLECTOR_B,
              stationary_rotors: Optional[int] = None) -> "Enigma":
        if len(rotor_order) < 3:
            raise ValueError("at least three rotors are required")
        if len(rotor_order) != len(ring) or len(ring) != len(start):
            raise ValueError("rotor_order, ring, and start must have equal lengths")
        rotor_order = [name.upper() for name in rotor_order]
        if stationary_rotors is None:
            stationary_rotors = (
                1 if len(rotor_order) == 4 and rotor_order[0] in {"BETA", "GAMMA"}
                else 0
            )
        if stationary_rotors < 0 or stationary_rotors > len(rotor_order) - 3:
            raise ValueError("stationary_rotors must leave exactly three moving rotors")
        if stationary_rotors and rotor_order[0] not in {"BETA", "GAMMA"}:
            raise ValueError("an M4 stationary rotor must be BETA or GAMMA")
        unknown = [name for name in rotor_order if name not in ROTOR_WIRINGS]
        if unknown:
            raise ValueError(f"unknown rotor(s): {unknown}")
        if len(set(rotor_order[stationary_rotors:])) != len(rotor_order) - stationary_rotors:
            raise ValueError("moving rotors must be distinct")
        rotors = [Rotor.make(rotor_order[i], ring[i], start[i])
                  for i in range(len(rotor_order))]
        reflector = REFLECTORS.get(reflector.upper(), reflector)
        if len(reflector) != N or set(reflector) != set("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            raise ValueError("reflector must be a permutation of A-Z")
        refl = _perm(reflector)
        if any(refl[refl[i]] != i or refl[i] == i for i in range(N)):
            raise ValueError("reflector must be an involution without fixed points")
        return cls(rotors, refl, Plugboard.from_letters(plug), stationary_rotors)

    def _step(self):
        # The three rightmost rotors are the moving stack. This is the normal
        # machine and the M4, whose left Greek rotor is stationary.
        slow, middle, fast = self.rotors[-3:]
        if middle.at_notch():
            middle.step()
            slow.step()
        elif fast.at_notch():
            middle.step()
        fast.step()

    def _scramble(self, c: int) -> int:
        """Apply the rotor/reflector path at the current frozen state."""
        for rotor in reversed(self.rotors):
            c = rotor.encode_fwd(c)
        c = self.reflector[c]
        for rotor in self.rotors:
            c = rotor.encode_bwd(c)
        return c

    def _encrypt_char(self, c: int) -> int:
        self._step()
        c = self.plugboard.swap(c)
        c = self._scramble(c)
        c = self.plugboard.swap(c)
        return c

    def encrypt(self, text: str) -> str:
        out = []
        for ch in text.upper():
            if not ("A" <= ch <= "Z"):
                continue
            out.append(chr(self._encrypt_char(ord(ch) - A) + A))
        return "".join(out)

    def decrypt(self, text: str) -> str:
        """Decrypt text with the same settings (Enigma is reciprocal)."""
        return self.encrypt(text)


def encrypt(rotor_order, ring, start, plug, plaintext, reflector=REFLECTOR_B,
            stationary_rotors: Optional[int] = None) -> str:
    """One-shot forward model: settings + plaintext -> ciphertext."""
    return Enigma.build(rotor_order, tuple(ring), tuple(start), plug, reflector,
                        stationary_rotors).encrypt(plaintext)


def decrypt(rotor_order, ring, start, plug, ciphertext, reflector=REFLECTOR_B,
            stationary_rotors: Optional[int] = None) -> str:
    """One-shot decryption API; explicit even though the machine is reciprocal."""
    return encrypt(rotor_order, ring, start, plug, ciphertext, reflector,
                   stationary_rotors)


# ---- Settings container + random sampler for ground-truth trials -----------
@dataclass
class Settings:
    rotor_order: Tuple[str, ...]
    ring: Tuple[int, ...]
    start: Tuple[int, ...]
    plug: str = ""
    reflector: str = REFLECTOR_B
    stationary_rotors: Optional[int] = None

    def encrypt(self, text: str) -> str:
        return encrypt(list(self.rotor_order), self.ring, self.start, self.plug, text,
                       self.reflector, self.stationary_rotors)

    def decrypt(self, text: str) -> str:
        return self.encrypt(text)

    def __str__(self):
        return (f"order={'/'.join(self.rotor_order)} ring={self.ring} "
                f"start={self.start} plug='{self.plug}'")


def random_settings(rng: random.Random, n_plugs: int = 0,
                    rotor_pool=("I", "II", "III"),
                    ring_zero: bool = True, rotor_count: int = 3,
                    reflector: str = REFLECTOR_B) -> Settings:
    if rotor_count < 3 or len(rotor_pool) < rotor_count:
        raise ValueError("rotor_pool must contain at least rotor_count rotors")
    order = tuple(rng.sample(list(rotor_pool), rotor_count))
    # Ring: historically often AAA; keeping ring at 0 removes the ring/start
    # redundancy so "recover the start positions" is well-posed for a short msg.
    if ring_zero:
        ring = (0, 0, 0)
    else:
        ring = (rng.randrange(N), rng.randrange(N), rng.randrange(N))
    start = (rng.randrange(N), rng.randrange(N), rng.randrange(N))
    # plugboard: n_plugs disjoint random pairs
    letters = list(range(N))
    rng.shuffle(letters)
    pairs = []
    for i in range(n_plugs):
        a, b = letters[2 * i], letters[2 * i + 1]
        pairs.append(chr(a + A) + chr(b + A))
    stationary = 1 if rotor_count == 4 and order[0] in {"BETA", "GAMMA"} else None
    return Settings(order, ring, start, " ".join(pairs), reflector, stationary)


if __name__ == "__main__":
    # self-test: symmetry + no-fixed-point
    rng = random.Random(0)
    s = random_settings(rng, n_plugs=3, ring_zero=False)
    pt = "THEQUICKBROWNFOXJUMPSOVERTHELAZYDOG"
    ct = s.encrypt(pt)
    # decrypt = encrypt with same settings
    s2 = Settings(s.rotor_order, s.ring, s.start, s.plug)
    rt = s2.encrypt(ct)
    print("settings:", s)
    print("plain :", pt)
    print("cipher:", ct)
    print("roundtrip ok:", rt == pt)
    print("no fixed point:", all(a != b for a, b in zip(pt, ct)))
