"""FACE-INVERSION / THATCHER (T10) — the migrated gate. VISION_FACE_INVERSION_PREREG.md
(committed e407429f, BEFORE the confirmatory run, §3).

A VALIDATION gate that PINS a clean diagnosed NEGATIVE (PROTOCOL §7): the substrate's
composition (arrangement, driven through the real sd loop) is reference-frame-INVARIANT,
NOT holistic-configural in the human way. It ADDS NO seed and NO Rust — it MEASURES the
existing shape-decode loop. Every recognition decision is in seeds/shape_decode_loop.json;
the test only builds cell-arrangement stimuli and reads status/covered_by back.

Locked facts (engine 7d5f50c18673, gen_infer OFF):
  * uniform inversion -> recognised as OWN identity (no cost): configural 4/4, part 4/4;
  * Thatcher (local part flip) -> unrecognised in BOTH orientations (no frame-gating): 0
    frame-gated of 12 configural cases;
  * inversion-related pairs COLLAPSE (a pattern and its 180-twin -> one identity): 4/4;
  * arms ALIVE (upright & inverted recognised, Thatcher unrecognised) + noise 0/100.
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.face_inversion_lib as L  # noqa: E402 (does engine_preamble on import)

FACE_ANCHORS = {
    "A": [(0, 0), (0, 6), (7, 3)],
    "B": [(0, 0), (0, 8), (5, 4)],
    "C": [(0, 2), (0, 7), (8, 0)],
    "D": [(1, 0), (0, 5), (6, 6)],
}
CFG = {k: L.configural(v, atom=L.ATOM_L) for k, v in FACE_ANCHORS.items()}

PB_ANCH = [(0, 0), (0, 6), (7, 3)]
PB_ATOMSETS = {
    "P": [L.ATOM_L, L.ATOM_J, L.ATOM_S], "Q": [L.ATOM_J, L.ATOM_S, L.ATOM_T],
    "R": [L.ATOM_S, L.ATOM_T, L.ATOM_L], "S": [L.ATOM_T, L.ATOM_L, L.ATOM_J],
}
PB = {k: L.part_based(v, PB_ANCH) for k, v in PB_ATOMSETS.items()}


def _own(codebook, views):
    return sum(L.identify(codebook, c)[1] == k for k, c in views.items())


# ---- ARM 1: INVERSION COST (headline DIFFERENTIAL) -> NEGATIVE -----------------------
def test_ARM1_uniform_inversion_has_NO_cost_for_either_representation():
    inv_c = _own(CFG, {k: L.rot180(c) for k, c in CFG.items()})
    inv_p = _own(PB, {k: L.rot180(c) for k, c in PB.items()})
    assert inv_c == len(CFG)      # 4/4 inverted configural faces recognised as OWN identity
    assert inv_p == len(PB)       # 4/4 inverted part objects recognised as OWN identity
    cost_config = 1 - inv_c / len(CFG)
    cost_part = 1 - inv_p / len(PB)
    # the differential is the effect; here it is ZERO -> NO disproportionate inversion cost.
    assert cost_config == 0.0 and cost_part == 0.0
    assert (cost_config - cost_part) == 0.0


# ---- ARM 2: THATCHER -> NO frame-gating (NEGATIVE) ----------------------------------
def test_ARM2_thatcher_no_frame_gating_detected_in_both_orientations():
    gated = both_unrec = cases = 0
    for k, anch in FACE_ANCHORS.items():
        for fi in range(3):
            up = L.configural(anch, atom=L.ATOM_L, flip_idx=fi)
            _, cu = L.identify(CFG, up)
            _, ci = L.identify(CFG, L.rot180(up))
            ru, ri = int(cu == k), int(ci == k)
            gated += (ru != ri)
            both_unrec += (ru == 0 and ri == 0)
            cases += 1
    assert cases == 12
    assert gated == 0            # NO configural Thatcher case is frame-gated
    assert both_unrec == 12      # the local anomaly is detected (unrecognised) in BOTH frames


# ---- ARM 3: REFERENCE-FRAME -> orbit-collapse (frame-invariant, not human upright bias) -
def test_ARM3_inversion_related_pairs_collapse():
    collapsed = 0
    for k, c in CFG.items():
        cb = {k: c, k + "_inv": L.rot180(c)}
        _, c1 = L.identify(cb, c)
        _, c2 = L.identify(cb, L.rot180(c))
        collapsed += (c1 == c2 and c1 is not None)
    assert collapsed == len(CFG)   # 4/4: a configural pattern and its 180-twin are ONE identity


def test_ARM3_part_based_nonrotation_related_stay_discriminable():
    for a, b in (("P", "Q"), ("R", "S")):
        cb = {a: PB[a], b: PB[b]}
        assert L.identify(cb, PB[a])[1] == a
        assert L.identify(cb, PB[b])[1] == b
        assert L.identify(cb, L.rot180(PB[a]))[1] == a   # inverted still own identity


# ---- ARM 4: FLOOR / §1.1 (arms ALIVE + noise) ---------------------------------------
def test_ARM4_arms_alive():
    # ALIVE: upright recognised, inverted recognised (covered_by not a constant None),
    # Thatcher unrecognised -> BOTH recognition states reached.
    assert _own(CFG, CFG) == len(CFG)
    assert _own(CFG, {k: L.rot180(c) for k, c in CFG.items()}) == len(CFG)
    _, tcov = L.identify(CFG, L.configural(FACE_ANCHORS["A"], atom=L.ATOM_L, flip_idx=0))
    assert tcov is None


def test_ARM4_noise_floor_no_force_maps():
    force = 0
    for i in range(100):
        rng = random.Random(49000 + i)
        cells = set()
        while len(cells) < 9:
            cells.add((rng.randint(0, 9), rng.randint(0, 9)))
        if L.identify(CFG, list(cells))[1] is not None:
            force += 1
    assert force == 0            # the recogniser is not a universal container (seeds 49000-49099)


# ---- §9: this gate ADDS NO seed -----------------------------------------------------
def test_no_face_inversion_seed_is_added():
    # The gate is read-only on the substrate: there is no vision_face_inversion seed/flag.
    seeds_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "seeds")
    assert not os.path.exists(os.path.join(seeds_dir, "vision_face_inversion.json"))
