"""enigma_blind — CIPHERTEXT-ONLY (blind) recovery of the FULL Enigma.

NO CRIB. Only ciphertext + a quadgram language model (trained on a disjoint
corpus) + ground-truth (for scoring trials). This is the modern two-stage
attack (Gillogly 1995 / Weierud-Sullivan):

  STAGE A — rotor order + start positions by INDEX OF COINCIDENCE (and quadgram).
    For each rotor order x each start triple, decrypt WITHOUT the plugboard and
    score the decrypt. The plugboard is a WEAK perturbation (it swaps <=20 of 26
    letters pairwise), so the correct rotor setting still produces an
    abnormally-high IoC / quadgram peak even with the plugboard wrong. Keep the
    top-K rotor candidates.

  STAGE B — plugboard HILL-CLIMBING (Turing-free; pure n-gram optimisation).
    For each top rotor candidate, hill-climb the plugboard: start from empty,
    repeatedly try every possible single plug-pair add / swap, keep the change
    that most raises the quadgram log-likelihood, iterate to convergence.
    ESCAPE STRATEGY for local optima: MULTI-START / RANDOM-RESTART basin-hopping
    (the GNC-need the methods survey flagged) — run the climb from several
    random plug seeds and keep the global best. We measure the stall/rescue rate.

WEIGHTED ADMISSIBILITY: the quadgram log-likelihood is the SOFT excluder; the
no-fixed-point structural law is the HARD excluder (it is guaranteed by the
forward model, and we use it implicitly — a plug that maps a letter to itself is
inexpressible, the involution forbids it).

Owned pure logic. NO net / fit / gradient. The hill-climb is discrete local
search over the involution lattice scored by a fixed (frozen) n-gram model.
"""
from __future__ import annotations

import math
import random
import itertools
from typing import List, Tuple, Dict, Optional

from domains.toy_enigma import (
    Enigma, Settings, Rotor, Plugboard, REFLECTOR_B, _perm, _inv, N, A,
)

# ---------------------------------------------------------------------------
# Quadgram language model (trained on a disjoint corpus; frozen at solve time).
# log10 probabilities, add-floor smoothed. This is the standard Practical
# Cryptography quadgram-fitness measure.
# ---------------------------------------------------------------------------
class QuadgramLM:
    def __init__(self):
        self.counts: Dict[int, float] = {}   # packed quadgram key -> count
        self.total = 0.0
        self.floor = 0.0
        self.trained_chars = 0

    @staticmethod
    def _key(a: int, b: int, c: int, d: int) -> int:
        return ((a * N + b) * N + c) * N + d

    def train(self, text: str):
        s = [ord(ch) - A for ch in text.upper() if "A" <= ch <= "Z"]
        self.trained_chars += len(s)
        cnt = self.counts
        for i in range(len(s) - 3):
            k = self._key(s[i], s[i + 1], s[i + 2], s[i + 3])
            cnt[k] = cnt.get(k, 0.0) + 1.0

    def finalize(self):
        self.total = sum(self.counts.values())
        # log10 probabilities; unseen quadgram floor = log10(0.01/total)
        self.floor = math.log10(0.01 / self.total)
        for k in self.counts:
            self.counts[k] = math.log10(self.counts[k] / self.total)

    def score(self, seq: List[int]) -> float:
        """Total quadgram log10-likelihood of an index sequence (higher=better)."""
        if len(seq) < 4:
            return self.floor * max(0, len(seq) - 3)
        cnt = self.counts
        floor = self.floor
        key = self._key
        total = 0.0
        for i in range(len(seq) - 3):
            k = key(seq[i], seq[i + 1], seq[i + 2], seq[i + 3])
            v = cnt.get(k)
            total += v if v is not None else floor
        return total

    def dense_table(self):
        """A dense (26^4,) numpy float32 log10-prob table for vectorised scoring.
        table[((a*26+b)*26+c)*26+d] == score of quadgram (a,b,c,d). Exactly the
        same values as score() — just packed for numpy gather."""
        import numpy as np
        tab = np.full(N ** 4, self.floor, dtype=np.float32)
        for k, v in self.counts.items():
            tab[k] = v
        return tab


def to_idx(text: str) -> List[int]:
    return [ord(ch) - A for ch in text.upper() if "A" <= ch <= "Z"]


# ---------------------------------------------------------------------------
# Index of coincidence — the plugboard-robust rotor discriminator.
# IoC = sum_l n_l(n_l-1) / (N_total(N_total-1)).  English ~0.066, random ~0.038.
# The plugboard preserves the letter-frequency *distribution shape* (it's a
# permutation of frequencies), so a correctly-derotored-but-plugboard-wrong
# decrypt still has a high IoC. That is why Stage A works without the plugboard.
# ---------------------------------------------------------------------------
def index_of_coincidence(seq: List[int]) -> float:
    n = len(seq)
    if n < 2:
        return 0.0
    counts = [0] * N
    for x in seq:
        counts[x] += 1
    s = sum(c * (c - 1) for c in counts)
    return s / (n * (n - 1))


# ---------------------------------------------------------------------------
# Fast decrypt WITHOUT plugboard, given a rotor scrambler. For Stage A we only
# need the rotor+reflector path; the Enigma model already does this with an
# empty plugboard, so we reuse it directly (donkey-clean: same forward model).
# ---------------------------------------------------------------------------
def decrypt_no_plug(order, ring, start, ct_idx: List[int]) -> List[int]:
    eng = Enigma.build(list(order), ring, start, "")
    out = []
    for x in ct_idx:
        out.append(eng._encrypt_char(x))
    return out


def decrypt_with_plug(order, ring, start, plug_map: List[int],
                      ct_idx: List[int]) -> List[int]:
    """Decrypt with an explicit plugboard map (list[int] involution)."""
    eng = Enigma.build(list(order), ring, start, "")
    eng.plugboard._map = plug_map
    out = []
    for x in ct_idx:
        out.append(eng._encrypt_char(x))
    return out


# ---------------------------------------------------------------------------
# FAST PATH: precompute the rotor+reflector scrambler permutation at every
# position (plugboard-free), so that decrypt under any plugboard S is just
#   p_i = S( E_i( S( c_i ) ) )
# pure array indexing. Reuses the SAME forward model (Enigma stepped, path read
# off the frozen rotor state) — donkey-clean, no new crypto.
# ---------------------------------------------------------------------------
def scrambler_perms(order, ring, start, length: int) -> List[List[int]]:
    eng = Enigma.build(list(order), ring, start, "")
    L, M, R = eng.rotors
    refl = eng.reflector
    perms = []
    for _ in range(length):
        eng._step()
        row = [0] * N
        for a in range(N):
            c = a
            c = R.encode_fwd(c); c = M.encode_fwd(c); c = L.encode_fwd(c)
            c = refl[c]
            c = L.encode_bwd(c); c = M.encode_bwd(c); c = R.encode_bwd(c)
            row[a] = c
        perms.append(row)
    return perms


def decrypt_fast(perms: List[List[int]], plug_map: List[int],
                 ct_idx: List[int]) -> List[int]:
    """Decrypt using precomputed scrambler perms + an explicit plugboard map.
    p_i = S(E_i(S(c_i)))."""
    out = [0] * len(ct_idx)
    for i, c in enumerate(ct_idx):
        out[i] = plug_map[perms[i][plug_map[c]]]
    return out


# ---------------------------------------------------------------------------
# NUMPY FAST PATH (exact-equivalent, just vectorised). Used to make the
# plugboard hill-climb's millions of scores tractable on a CPU.
# ---------------------------------------------------------------------------
def np_perms(order, ring, start, length: int):
    import numpy as np
    return np.asarray(scrambler_perms(order, ring, start, length), dtype=np.int64)


def np_score(E_np, plug_map_np, ct_np, table):
    """Decrypt p_i = S(E_i(S(c_i))) and return the quadgram log10-likelihood,
    fully vectorised. Identical value to QuadgramLM.score(decrypt_fast(...))."""
    import numpy as np
    L = ct_np.shape[0]
    s_c = plug_map_np[ct_np]                    # S(c_i)
    mid = E_np[np.arange(L), s_c]               # E_i(S(c_i))
    p = plug_map_np[mid]                         # S(E_i(S(c_i)))
    if L < 4:
        return float(table[0] * 0)
    keys = (((p[:-3] * N + p[1:-2]) * N + p[2:-1]) * N + p[3:])
    return float(table[keys].sum())


# ---------------------------------------------------------------------------
# STAGE B: plugboard hill-climbing with multi-start escape (GNC / basin-hopping).
# ---------------------------------------------------------------------------
def _apply_pair(plug_map: List[int], a: int, b: int) -> List[int]:
    """Return a fresh involution map with pair (a,b) added, removing any prior
    plugs on a or b (so the result stays a valid involution)."""
    m = list(plug_map)
    # unplug a's current partner and b's current partner
    pa, pb = m[a], m[b]
    m[pa] = pa
    m[pb] = pb
    m[a] = b
    m[b] = a
    return m


def _pairs_of(plug_map: List[int]) -> List[Tuple[int, int]]:
    pairs = []
    for x in range(N):
        y = plug_map[x]
        if y != x and x < y:
            pairs.append((x, y))
    return pairs


def hill_climb_np(E_np, ct_np, table, max_pairs=10, init_map=None):
    """NUMPY hill-climb (exact-equivalent of hill_climb_plugboard, vectorised
    scorer). Returns (best_map_list, best_score, n_evals)."""
    import numpy as np
    cur = list(init_map) if init_map is not None else list(range(N))
    cur_np = np.asarray(cur, dtype=np.int64)
    cur_score = np_score(E_np, cur_np, ct_np, table)
    n_evals = 1
    improved = True
    iters = 0
    # Safety bound: a strictly-improving climb over the <=10-pair involution
    # lattice converges in well under this many steps; the cap only fires on the
    # rare pathological near-flat ridge (the heavy tail noted in the report),
    # preventing a single trial from running unboundedly long.
    while improved and iters < 60:
        iters += 1
        improved = False
        best_map = None
        best_score = cur_score
        for a in range(N):
            for b in range(a + 1, N):
                if cur[a] == b:
                    continue
                cand = _apply_pair(cur, a, b)
                if len(_pairs_of(cand)) > max_pairs:
                    continue
                sc = np_score(E_np, np.asarray(cand, dtype=np.int64), ct_np, table)
                n_evals += 1
                if sc > best_score:
                    best_score = sc
                    best_map = cand
        for (a, b) in _pairs_of(cur):
            cand = list(cur)
            cand[a] = a
            cand[b] = b
            sc = np_score(E_np, np.asarray(cand, dtype=np.int64), ct_np, table)
            n_evals += 1
            if sc > best_score:
                best_score = sc
                best_map = cand
        if best_map is not None:
            cur = best_map
            cur_score = best_score
            improved = True
    return cur, cur_score, n_evals


def stage_b_np(E_np, ct_np, table, max_pairs=10, n_starts=5, rng=None):
    """Multi-start (basin-hopping) plugboard climb, numpy. Returns
    (best_map, best_score, total_evals, rescues, empty_score)."""
    import numpy as np
    if rng is None:
        rng = random.Random(0)
    best_map, best_score, ev = hill_climb_np(E_np, ct_np, table, max_pairs,
                                             init_map=None)
    total_ev = ev
    empty_score = best_score
    rescues = 0
    for s in range(1, n_starts):
        seed = _random_plug_map(rng, n_pairs=rng.randint(3, max_pairs))
        m, sc, ev = hill_climb_np(E_np, ct_np, table, max_pairs, init_map=seed)
        total_ev += ev
        if sc > best_score + 1e-9:
            best_score = sc
            best_map = m
            if sc > empty_score + 1e-9:
                rescues += 1
    return best_map, best_score, total_ev, rescues, empty_score


def hill_climb_plugboard(perms, ct_idx: List[int], lm: QuadgramLM,
                         max_pairs: int = 10, init_map: Optional[List[int]] = None):
    """Single hill-climb from `init_map` (empty if None) using precomputed
    scrambler perms. At each step, evaluate EVERY candidate single-pair change
    (add a new pair over two free letters, OR re-pair to improve) and apply the
    best-improving one; also consider removing a pair (escape over-plugging).
    Converge when no change helps or max_pairs reached.
    Returns (best_map, best_score, n_evals)."""
    cur = list(init_map) if init_map is not None else list(range(N))
    cur_score = lm.score(decrypt_fast(perms, cur, ct_idx))
    n_evals = 1
    improved = True
    while improved:
        improved = False
        best_map = None
        best_score = cur_score
        for a in range(N):
            for b in range(a + 1, N):
                if cur[a] == b:
                    continue  # already this pair
                cand = _apply_pair(cur, a, b)
                if len(_pairs_of(cand)) > max_pairs:
                    continue
                sc = lm.score(decrypt_fast(perms, cand, ct_idx))
                n_evals += 1
                if sc > best_score:
                    best_score = sc
                    best_map = cand
        for (a, b) in _pairs_of(cur):
            cand = list(cur)
            cand[a] = a
            cand[b] = b
            sc = lm.score(decrypt_fast(perms, cand, ct_idx))
            n_evals += 1
            if sc > best_score:
                best_score = sc
                best_map = cand
        if best_map is not None:
            cur = best_map
            cur_score = best_score
            improved = True
    return cur, cur_score, n_evals


def _random_plug_map(rng: random.Random, n_pairs: int) -> List[int]:
    letters = list(range(N))
    rng.shuffle(letters)
    m = list(range(N))
    for i in range(n_pairs):
        a, b = letters[2 * i], letters[2 * i + 1]
        m[a] = b
        m[b] = a
    return m


def stage_b(perms, ct_idx: List[int], lm: QuadgramLM,
            max_pairs: int = 10, n_starts: int = 6, rng: Optional[random.Random] = None):
    """Multi-start plugboard hill-climbing (basin-hopping escape) on precomputed
    scrambler perms. Start 0 = empty plugboard; starts 1..n-1 = random plug seeds.
    Returns (best_map, best_score, total_evals, n_restarts_that_beat_empty,
             empty_start_score).
    The 'rescue count' = how many random restarts beat the empty-start basin —
    the measured local-optima escape rate."""
    if rng is None:
        rng = random.Random(0)
    best_map, best_score, ev = hill_climb_plugboard(
        perms, ct_idx, lm, max_pairs, init_map=None)
    total_ev = ev
    empty_score = best_score
    rescues = 0
    for s in range(1, n_starts):
        seed = _random_plug_map(rng, n_pairs=rng.randint(3, max_pairs))
        m, sc, ev = hill_climb_plugboard(
            perms, ct_idx, lm, max_pairs, init_map=seed)
        total_ev += ev
        if sc > best_score + 1e-9:
            best_score = sc
            best_map = m
            if sc > empty_score + 1e-9:
                rescues += 1
    return best_map, best_score, total_ev, rescues, empty_score


# ---------------------------------------------------------------------------
# Full blind recovery: Stage A -> Stage B over top rotor candidates.
# ---------------------------------------------------------------------------
def recover_blind(ciphertext: str, lm: QuadgramLM, rotor_pool=("I", "II", "III"),
                  ring=(0, 0, 0), topk_ioc: int = 300, sharpen_pairs: int = 3,
                  topk_rotor: int = 3, max_pairs: int = 10, n_starts: int = 6,
                  rng: Optional[random.Random] = None):
    """Blind ciphertext-only recovery — the full two-stage attack.

    STAGE A (rotor order + start positions):
      A1. IoC prune: decrypt plugboard-free at every (order, start), keep the
          top-`topk_ioc` by index of coincidence (a ~0.5%% prune of 105_456).
      A2. Quadgram sharpen: on each survivor run a CHEAP `sharpen_pairs`-plug
          hill-climb; this re-ranks so the true rotor setting rises to the top
          (the plugboard, once partially recovered, makes the quadgram peak
          unambiguous). Keep the top-`topk_rotor`.
    STAGE B (plugboard): full multi-start hill-climb (up to `max_pairs`) on the
      top rotor candidates; best quadgram wins. Returns results + diagnostics.
    """
    import numpy as np
    if rng is None:
        rng = random.Random(12345)
    ct_idx = to_idx(ciphertext)
    L = len(ct_idx)
    ct_np = np.asarray(ct_idx, dtype=np.int64)
    table = lm.dense_table()
    orders = list(itertools.permutations(rotor_pool))
    brute = len(orders) * (N ** 3)

    # --- A1: coarse prune. The full 10-pair plugboard scrambles 20/26 letters,
    # so NEITHER IoC NOR the no-plug n-gram alone reliably ranks the true rotor
    # at moderate lengths (measured). We therefore take the UNION of the top-K by
    # IoC and the top-K by no-plug quadgram — broadening coverage so the true
    # setting survives the prune more often. ---
    ioc_rows = []
    a_eval = 0
    for order in orders:
        for s0 in range(N):
            for s1 in range(N):
                for s2 in range(N):
                    start = (s0, s1, s2)
                    dec = decrypt_no_plug(order, ring, start, ct_idx)
                    ioc_rows.append((index_of_coincidence(dec), lm.score(dec),
                                     order, start))
                    a_eval += 1
    by_ioc = sorted(ioc_rows, key=lambda x: -x[0])[:topk_ioc]
    by_q = sorted(ioc_rows, key=lambda x: -x[1])[:topk_ioc]
    seen = set()
    survivors = []
    for ioc, q, order, start in by_ioc + by_q:
        key = (order, start)
        if key in seen:
            continue
        seen.add(key)
        survivors.append((ioc, order, start))

    # --- A2: cheap quadgram sharpen on survivors (numpy fast path) ---
    sharpened = []
    sharpen_evals = 0
    for ioc, order, start in survivors:
        E_np = np_perms(order, ring, start, L)
        m, sc, ev = hill_climb_np(E_np, ct_np, table, max_pairs=sharpen_pairs)
        sharpen_evals += ev
        sharpened.append((sc, ioc, order, start))
    sharpened.sort(key=lambda x: -x[0])
    cands = sharpened[:topk_rotor]

    # --- Stage B: full plugboard climb on the top rotor candidates (numpy) ---
    best = None
    best_score = -float("inf")
    total_b_eval = 0
    total_rescues = 0
    stalls = 0
    for (q, ioc, order, start) in cands:
        E_np = np_perms(order, ring, start, L)
        bmap, bscore, b_eval, rescues, empty_score = stage_b_np(
            E_np, ct_np, table, max_pairs=max_pairs, n_starts=n_starts, rng=rng)
        total_b_eval += b_eval
        total_rescues += rescues
        if rescues > 0:
            stalls += 1
        if bscore > best_score:
            best_score = bscore
            best = dict(order=order, start=start, ring=ring,
                        plug_map=bmap, score=bscore, ioc=ioc)
    pairs = _pairs_of(best["plug_map"])
    plug_str = " ".join(chr(a + A) + chr(b + A) for a, b in pairs)
    best["plug_str"] = plug_str
    best["pairs"] = pairs
    return dict(best=best, stage_a_candidates=cands, stage_a_evals=a_eval,
                sharpen_evals=sharpen_evals, stage_b_evals=total_b_eval,
                brute_force=brute, total_rescues=total_rescues, stalls=stalls,
                n_rotor_cands=len(cands))


# ---------------------------------------------------------------------------
# Scoring a recovery against ground truth.
# ---------------------------------------------------------------------------
def plug_pairs_set(plug_str: str):
    s = set()
    for tok in plug_str.split():
        a, b = ord(tok[0]) - A, ord(tok[1]) - A
        s.add((min(a, b), max(a, b)))
    return s


def grade(truth: Settings, best: dict):
    """Return (rotor_ok, start_ok, plug_recall, plug_precision, full_ok)."""
    rotor_ok = tuple(best["order"]) == tuple(truth.rotor_order)
    start_ok = tuple(best["start"]) == tuple(truth.start)
    truth_pairs = plug_pairs_set(truth.plug)
    rec_pairs = set(best["pairs"])
    if truth_pairs:
        recall = len(truth_pairs & rec_pairs) / len(truth_pairs)
    else:
        recall = 1.0 if not rec_pairs else 0.0
    if rec_pairs:
        precision = len(truth_pairs & rec_pairs) / len(rec_pairs)
    else:
        precision = 1.0 if not truth_pairs else 0.0
    full_ok = rotor_ok and start_ok and (truth_pairs == rec_pairs)
    return rotor_ok, start_ok, recall, precision, full_ok
