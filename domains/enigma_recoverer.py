"""enigma_recoverer — structure-recoverer (analysis-by-synthesis + weighted
admissibility) that reverse-engineers a toy Enigma's settings from ciphertext.

THE AGENT'S COGNITION (owned, no net/fit/gradient). Two levels:

LEVEL 1 — rotor order + start positions (small/zero plugboard).
  ANALYSIS-BY-SYNTHESIS: for each candidate (order, start), DECRYPT the
  ciphertext (synthesise the plaintext under that hypothesis) and SCORE by
  WEIGHTED ADMISSIBILITY = soft excluders INTERSECTED (not one dot-product):
      - ngram   : letter-trigram log-likelihood of the decrypt (English structure)
      - crib    : the known-plaintext snippet appears at the known offset
      - sanity  : no-fixed-point already guaranteed by the model (kept as a check)
  Excluders are combined by INTERSECTION (sum of log-excluders = log of product),
  and a candidate ABSTAINS (floor) if any HARD excluder (the crib) fails. The
  argmax-admissibility over the feasible set = recovered settings.

LEVEL 2 — plugboard (Turing's Bombe trick).
  The crib gives a MENU: positions where plaintext letter p enciphers to
  ciphertext letter c. We pick a candidate plug for one letter and PROPAGATE the
  no-self-map + plugboard-involution constraints through the menu's LOOPS. A
  contradiction (a letter forced to map to itself, or to two different letters)
  rejects the ENTIRE rotor hypothesis for that whole plug-class IN BULK — without
  enumerating the 1e14 plugboards. This bulk contradiction-carving IS weighted
  admissibility with HARD excluders (intersection of constraints carving the
  inadmissible). We show the pruning factor vs brute force.
"""
from __future__ import annotations

import math
import itertools
from collections import defaultdict
from typing import List, Tuple, Dict, Optional

from domains.toy_enigma import Enigma, Settings, encrypt, N, A, REFLECTOR_B


# ---------------------------------------------------------------------------
# Language model: letter-trigram counts from a TRAIN corpus (world, train-only).
# ---------------------------------------------------------------------------
class TrigramLM:
    def __init__(self, k: float = 0.1):
        self.k = k
        self.tri = defaultdict(float)
        self.bi = defaultdict(float)
        self.V = N
        self.trained_chars = 0

    def train(self, text: str):
        s = [ord(ch) - A for ch in text.upper() if "A" <= ch <= "Z"]
        self.trained_chars += len(s)
        for i in range(len(s)):
            if i >= 2:
                self.tri[(s[i - 2], s[i - 1], s[i])] += 1.0
                self.bi[(s[i - 2], s[i - 1])] += 1.0

    def logprob(self, seq: List[int]) -> float:
        """Add-k smoothed trigram log-likelihood, per-character normalised."""
        if len(seq) < 3:
            return 0.0
        lp = 0.0
        k = self.k
        for i in range(2, len(seq)):
            num = self.tri[(seq[i - 2], seq[i - 1], seq[i])] + k
            den = self.bi[(seq[i - 2], seq[i - 1])] + k * self.V
            lp += math.log(num / den)
        return lp / (len(seq) - 2)


def to_idx(text: str) -> List[int]:
    return [ord(ch) - A for ch in text.upper() if "A" <= ch <= "Z"]


# ---------------------------------------------------------------------------
# WEIGHTED ADMISSIBILITY: soft excluders intersected, abstain-at-floor.
# Each excluder returns a value in (-inf, 0]; 0 = fully admissible on that axis,
# -inf = inadmissible (abstain). Intersection = sum (log of the product). This is
# the same shape as domains/weighted_admissibility (product of soft excluders),
# carrying the no-self-map / crib as HARD excluders that floor the score.
# ---------------------------------------------------------------------------
FLOOR = -1e9


def admissibility(decrypt_idx: List[int], lm: TrigramLM,
                  crib: str, crib_offset: int,
                  ngram_weight: float = 1.0) -> float:
    # HARD excluder: crib must appear at the known offset (else abstain at floor)
    crib_idx = to_idx(crib)
    seg = decrypt_idx[crib_offset:crib_offset + len(crib_idx)]
    if seg != crib_idx:
        return FLOOR
    # SOFT excluder: n-gram structure of the whole decrypt
    return ngram_weight * lm.logprob(decrypt_idx)


# ---------------------------------------------------------------------------
# LEVEL 1: recover rotor order + start positions (plugboard small/zero).
# ANALYSIS-BY-SYNTHESIS: decrypt under each hypothesis, score admissibility.
# ---------------------------------------------------------------------------
def recover_level1(ciphertext: str, crib: str, crib_offset: int, lm: TrigramLM,
                   rotor_pool=("I", "II", "III"), ring=(0, 0, 0),
                   known_plug: str = "", topk: int = 3,
                   reflector=REFLECTOR_B, rotor_count: int = 3,
                   stationary_rotors=None,
                   verbose: bool = False):
    """Returns (best_settings, score, n_evaluated, brute_force_size, ranked).
    The feasible set = all rotor orders x all 26^3 start positions."""
    best = None
    best_score = -float("inf")
    ranked = []
    n_eval = 0
    orders = list(itertools.permutations(rotor_pool, rotor_count))
    if len(ring) != rotor_count:
        raise ValueError("ring must contain one setting per searched rotor")
    if stationary_rotors is None and rotor_count == 4:
        stationary_rotors = 1
    if rotor_count == 4 and stationary_rotors == 1:
        orders = [order for order in orders if order[0] in {"BETA", "GAMMA"}]
    brute = len(orders) * (N ** rotor_count)
    for order in orders:
        for start in itertools.product(range(N), repeat=rotor_count):
            eng = Enigma.build(list(order), tuple(ring), start, known_plug,
                               reflector, stationary_rotors)
            dec = eng.decrypt(ciphertext)
            dec_idx = to_idx(dec)
            n_eval += 1
            sc = admissibility(dec_idx, lm, crib, crib_offset)
            if sc <= FLOOR:
                continue
            ranked.append((sc, order, start))
            if sc > best_score:
                best_score = sc
                best = Settings(order, tuple(ring), start, known_plug, reflector,
                                stationary_rotors)
    ranked.sort(key=lambda x: -x[0])
    return best, best_score, n_eval, brute, ranked[:topk]


# ---------------------------------------------------------------------------
# LEVEL 2: the BOMBE — plugboard recovery via constraint propagation.
#
# Setup: we have the CRIB (plaintext) aligned to ciphertext over a window. For a
# CANDIDATE rotor hypothesis (order, start, ring), the Enigma WITHOUT plugboard
# defines, at each position i, a permutation E_i (the rotor+reflector scrambler).
# WITH plugboard S (an involution), the full encipherment of a letter at pos i is:
#       c_i = S( E_i( S( p_i ) ) )
# The Bombe fixes an ASSUMPTION for ONE letter's plug partner and propagates the
# implied plug pairs through the crib's letters. A contradiction (a letter forced
# to be plugged to two different partners, or to itself) FALSIFIES the assumption.
# If ALL 26 assumptions for the chosen letter contradict, the rotor hypothesis is
# rejected WHOLESALE (plugboard-independent) — the bulk prune.
#
# This implements the Bombe's logic directly: a self-consistent steckering of the
# crib letters under hypothesis (order,start) either exists (=> candidate +
# recovered plug) or every branch contradicts (=> reject all ~1e14 plugboards for
# that rotor hypothesis at once). Constraint INTERSECTION carving the inadmissible
# = weighted admissibility with hard excluders.
# ---------------------------------------------------------------------------
def _scrambler_perms(order, ring, start, ciphertext_len,
                     reflector=REFLECTOR_B, stationary_rotors=None):
    """E_i for each position i: the rotor+reflector permutation WITHOUT plugboard.
    A single Enigma (empty plugboard) is stepped once per position; at each
    position the FULL 26-letter scrambler permutation is read off in one pass by
    enciphering all 26 letters at the FROZEN rotor state (the model steps once per
    encrypt, so we snapshot the rotor positions and apply the path directly)."""
    eng = Enigma.build(list(order), tuple(ring), tuple(start), "", reflector,
                       stationary_rotors)
    perms = []
    for i in range(ciphertext_len):
        eng._step()  # advance odometer to position i (1-indexed like encrypt)
        row = [0] * N
        for a in range(N):
            row[a] = eng._scramble(a)
        perms.append(row)
    return perms


def bombe_test(order, ring, start, crib: str, ciphertext: str, crib_offset: int,
               reflector=REFLECTOR_B, stationary_rotors=None):
    """Try to find a self-consistent plugboard (steckering) for the crib under the
    rotor hypothesis. Returns (ok, recovered_plug_pairs, branches_tried,
    branches_contradicted). ok=False => reject this rotor hypothesis for ALL
    plugboards (the bulk prune)."""
    p = to_idx(crib)
    c = to_idx(ciphertext)[crib_offset:crib_offset + len(p)]
    if len(c) < len(p):
        return False, None, 0, 0
    # scrambler perms at the crib positions
    perms_all = _scrambler_perms(order, ring, start, crib_offset + len(p),
                                 reflector, stationary_rotors)
    E = perms_all[crib_offset:crib_offset + len(p)]

    # Choose the most-connected letter in the crib as the Bombe's test letter.
    freq = defaultdict(int)
    for x in p:
        freq[x] += 1
    test_letter = max(freq, key=freq.get)

    branches = 0
    contradicted = 0
    # Assume test_letter steckers to `partner` (partner==test_letter => self-steckered).
    for partner in range(N):
        branches += 1
        stecker = {}   # letter -> partner (the plug map being built); involution

        def setp(x, y) -> bool:
            # set stecker[x]=y and stecker[y]=x; reject on contradiction
            if x in stecker:
                if stecker[x] != y:
                    return False
            if y in stecker:
                if stecker[y] != x:
                    return False
            stecker[x] = y
            stecker[y] = x
            return True

        ok = setp(test_letter, partner)
        # Propagate through every crib constraint: c_i = S(E_i(S(p_i))).
        # We do BFS closure: each known stecker value lets us deduce more.
        changed = ok
        while ok and changed:
            changed = False
            for i in range(len(p)):
                pi, ci = p[i], c[i]
                # if S(p_i) is known, then S(c_i) = E_i(S(p_i)) is forced
                if pi in stecker:
                    mid = E[i][stecker[pi]]
                    if ci in stecker:
                        if stecker[ci] != mid:
                            ok = False; break
                    else:
                        if not setp(ci, mid):
                            ok = False; break
                        changed = True
                # symmetric: if S(c_i) known, S(p_i) = E_i^{-1}(S(c_i)) forced
                if ci in stecker:
                    # invert E_i
                    inv = E[i].index(stecker[ci])
                    if pi in stecker:
                        if stecker[pi] != inv:
                            ok = False; break
                    else:
                        if not setp(pi, inv):
                            ok = False; break
                        changed = True
            if not ok:
                break
        if not ok:
            contradicted += 1
            continue
        # Self-consistent steckering found. Validate no-self-map of reflector is
        # respected automatically. Extract plug pairs (only genuine swaps).
        pairs = []
        seen = set()
        for x, y in stecker.items():
            if x != y and x not in seen:
                pairs.append((min(x, y), max(x, y)))
                seen.add(x); seen.add(y)
        plug = " ".join(chr(a + A) + chr(b + A) for a, b in sorted(pairs))
        return True, plug, branches, contradicted
    return False, None, branches, contradicted


def complete_plugboard(order, ring, start, ciphertext: str, lm: "TrigramLM",
                       partial_plug: str, max_extra_pairs: int = 6,
                       reflector=REFLECTOR_B):
    """Once the Bombe has fixed the ROTORS (single survivor) + the crib-forced
    plug pairs, finish the plugboard by WEIGHTED ADMISSIBILITY: greedily add the
    plug pair that most raises the n-gram admissibility of the FULL decrypt, until
    no addition helps. This is the historical 'complete the Steckerbrett by hand
    once the rotors are known' step — here the same soft excluder (n-gram
    intersection) drives it. Returns the completed plug string."""
    fixed_pairs = [tuple(sorted((ord(t[0]) - A, ord(t[1]) - A)))
                   for t in partial_plug.split()]
    used = set()
    for a, b in fixed_pairs:
        used.add(a); used.add(b)

    def score(pairs):
        plug = " ".join(chr(a + A) + chr(b + A) for a, b in pairs)
        dec = Settings(tuple(order), tuple(ring), tuple(start), plug,
                       reflector).encrypt(ciphertext)
        return lm.logprob(to_idx(dec))

    cur = list(fixed_pairs)
    base = score(cur)
    for _ in range(max_extra_pairs):
        best_gain = 1e-9
        best_pair = None
        free = [x for x in range(N) if x not in used]
        for i in range(len(free)):
            for j in range(i + 1, len(free)):
                a, b = free[i], free[j]
                sc = score(cur + [(a, b)])
                if sc - base > best_gain:
                    best_gain = sc - base
                    best_pair = (a, b)
                    best_base = sc
        if best_pair is None:
            break
        cur.append(best_pair)
        used.add(best_pair[0]); used.add(best_pair[1])
        base = best_base
    cur.sort()
    return " ".join(chr(a + A) + chr(b + A) for a, b in cur)


# Settings import for complete_plugboard (kept here to avoid a cycle at top)
from domains.toy_enigma import Settings  # noqa: E402
