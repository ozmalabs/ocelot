"""PILOT (calibration, PROTOCOL §1) for FACE-INVERSION / THATCHER — NOT confirmatory.
Deterministic constructions only (no RNG seed burned). Probes what the REAL sd loop does:
uniform inversion of an arrangement, a locally-flipped (Thatcher) part upright vs inverted,
and inversion-related discrimination, for CONFIGURAL vs PART-BASED patterns.
"""
from __future__ import annotations
import scripts.face_inversion_lib as L

# a canonical configural face: two "eyes" on top, one "mouth" bottom-centre.
ANCH = [(0, 0), (0, 6), (7, 3)]
FACE = L.configural(ANCH, atom=L.ATOM_L)
FACE_INV = L.rot180(FACE)                       # uniform 180 (whole)
FACE_THATCH = L.configural(ANCH, atom=L.ATOM_L, flip_idx=2)   # mouth locally flipped
FACE_THATCH_INV = L.rot180(FACE_THATCH)         # whole inverted, mouth stays locally flipped

# part-based object: three DISTINCT atoms at the SAME anchors.
ATOMS = [L.ATOM_L, L.ATOM_J, L.ATOM_T]
OBJ = L.part_based(ATOMS, ANCH)
OBJ_INV = L.rot180(OBJ)
OBJ_THATCH = L.part_based(ATOMS, ANCH, flip_idx=2)
OBJ_THATCH_INV = L.rot180(OBJ_THATCH)


def show(tag, st, cov):
    print(f"  {tag:34s} status={str(st):24s} covered_by={cov}")


def main():
    print("== CONFIGURAL (identity = arrangement) ==")
    show("upright vs {FACE}", *L.identify({"FACE": FACE}, FACE))
    show("uniform-inverted vs {FACE}", *L.identify({"FACE": FACE}, FACE_INV))
    show("thatcher-UPRIGHT vs {FACE}", *L.identify({"FACE": FACE}, FACE_THATCH))
    show("thatcher-INVERTED vs {FACE}", *L.identify({"FACE": FACE}, FACE_THATCH_INV))

    print("== PART-BASED (identity = which atoms) ==")
    show("upright vs {OBJ}", *L.identify({"OBJ": OBJ}, OBJ))
    show("uniform-inverted vs {OBJ}", *L.identify({"OBJ": OBJ}, OBJ_INV))
    show("thatcher-UPRIGHT vs {OBJ}", *L.identify({"OBJ": OBJ}, OBJ_THATCH))
    show("thatcher-INVERTED vs {OBJ}", *L.identify({"OBJ": OBJ}, OBJ_THATCH_INV))

    print("== INVERSION-RELATED DISCRIMINATION (hold FACE and its 180 twin as distinct) ==")
    show("present FACE vs {FACE,FACE_INV}", *L.identify({"FACE": FACE, "FACE_INV": FACE_INV}, FACE))
    show("present FACE_INV vs {FACE,FACE_INV}", *L.identify({"FACE": FACE, "FACE_INV": FACE_INV}, FACE_INV))
    show("present FACE vs {FACE_INV only}", *L.identify({"FACE_INV": FACE_INV}, FACE))

    print("== cross-checks ==")
    print("  FACE cells:", FACE)
    print("  FACE_INV cells:", FACE_INV)
    print("  FACE == FACE_INV ?", FACE == FACE_INV)
    print("  THATCH==FACE ?", FACE_THATCH == FACE)


if __name__ == "__main__":
    main()
