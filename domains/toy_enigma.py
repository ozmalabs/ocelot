"""toy_enigma — a 3-rotor Enigma forward model (owned pure logic, no net/fit).

THE FORWARD MODEL (donkey-clean): given SETTINGS + plaintext -> ciphertext.
Exact, deterministic, owned Python. This is the "f(params) -> signal" plug-in
for the solve-for-N machine (memory ozma_solve_for_n_is_general_not_speech):
the structure-recoverer inverts THIS to pull the settings out of ciphertext.

CONFIG (3-rotor Enigma, 26-letter alphabet A..Z):
  - 3 ROTORS, each a fixed permutation of the alphabet with one NOTCH position
    (historical Enigma I rotors I / II / III + reflector B, wirings below).
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
ROTOR_WIRINGS: Dict[str, Tuple[str, str]] = {
    "I":   ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
    "II":  ("AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
    "III": ("BDFHJLCPRTXVZNYEIWGAKMUSQO", "V"),
    "IV":  ("ESOVPZJAYQUIRHXLNFTGKDCMWB", "J"),
    "V":   ("VZBRGITYUPSDNHLXAWMJQOFECK", "Z"),
}
REFLECTOR_B = "YRUHQSLDPXNGOKMIEBFZCWVJAT"


@dataclass
class Rotor:
    name: str
    forward: List[int]      # wiring as permutation (right->left through rotor)
    backward: List[int]     # inverse wiring (left->right return path)
    notch: int              # notch letter index
    ring: int = 0           # ringstellung 0..25
    pos: int = 0            # current rotation 0..25

    @classmethod
    def make(cls, name: str, ring: int = 0, pos: int = 0) -> "Rotor":
        wiring, notch = ROTOR_WIRINGS[name]
        fwd = _perm(wiring)
        return cls(name, fwd, _inv(fwd), ord(notch) - A, ring, pos)

    def at_notch(self) -> bool:
        return self.pos == self.notch

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
            assert a not in seen and b not in seen, "plugboard must be disjoint"
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
            pairs.append((ord(tok[0]) - A, ord(tok[1]) - A))
        return cls(tuple(pairs))


@dataclass
class Enigma:
    rotors: List[Rotor]            # [left, middle, right]
    reflector: List[int]
    plugboard: Plugboard

    @classmethod
    def build(cls, rotor_order: List[str], ring: Tuple[int, int, int],
              start: Tuple[int, int, int], plug: str = "",
              reflector: str = REFLECTOR_B) -> "Enigma":
        rotors = [Rotor.make(rotor_order[i], ring[i], start[i]) for i in range(3)]
        return cls(rotors, _perm(reflector), Plugboard.from_letters(plug))

    def _step(self):
        # right rotor always steps; double-step anomaly on middle rotor
        L, M, R = self.rotors
        if M.at_notch():
            M.step()
            L.step()
        elif R.at_notch():
            M.step()
        R.step()

    def _encrypt_char(self, c: int) -> int:
        self._step()
        L, M, R = self.rotors
        c = self.plugboard.swap(c)
        c = R.encode_fwd(c); c = M.encode_fwd(c); c = L.encode_fwd(c)
        c = self.reflector[c]
        c = L.encode_bwd(c); c = M.encode_bwd(c); c = R.encode_bwd(c)
        c = self.plugboard.swap(c)
        return c

    def encrypt(self, text: str) -> str:
        out = []
        for ch in text.upper():
            if not ("A" <= ch <= "Z"):
                continue
            out.append(chr(self._encrypt_char(ord(ch) - A) + A))
        return "".join(out)


def encrypt(rotor_order, ring, start, plug, plaintext, reflector=REFLECTOR_B) -> str:
    """One-shot forward model: settings + plaintext -> ciphertext."""
    return Enigma.build(rotor_order, ring, start, plug, reflector).encrypt(plaintext)


# ---- Settings container + random sampler for ground-truth trials -----------
@dataclass
class Settings:
    rotor_order: Tuple[str, str, str]
    ring: Tuple[int, int, int]
    start: Tuple[int, int, int]
    plug: str = ""

    def encrypt(self, text: str) -> str:
        return encrypt(list(self.rotor_order), self.ring, self.start, self.plug, text)

    def __str__(self):
        return (f"order={'/'.join(self.rotor_order)} ring={self.ring} "
                f"start={self.start} plug='{self.plug}'")


def random_settings(rng: random.Random, n_plugs: int = 0,
                    rotor_pool=("I", "II", "III"),
                    ring_zero: bool = True) -> Settings:
    order = tuple(rng.sample(list(rotor_pool), 3))
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
    return Settings(order, ring, start, " ".join(pairs))


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
