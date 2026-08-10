#!/usr/bin/env python3
"""DOES CHECKING THE ABDUCED INTERMEDIATES MAKE INTERPOLATION REFUSABLE?

The confirmatory measurement for `VISION_GAPVERIFY_PREREG.md` (committed
5e2c34cb, addendum 1f4ca5a7, both before any number). Successor to the
gapabduce rung (97000-97999), whose deepest result was a NEGATIVE:

    THE OPERATOR HAS NO DISCRIMINATIVE POWER -- independent random endpoints
    accept at ~1/steps, because ANY TWO SAME-SHAPE FIGURES ARE RIGID
    TRANSLATES.  Its intermediates are emitted (`bridged`) and CHECKED
    AGAINST NOTHING.

This rung checks them.  In a scene with any other content, `G^t(f_before)` is a
FALSIFIABLE PREDICTION at every gap tick.

Every arm is DETERMINISTIC except the NOISE control, whose random dot positions
draw from seeds 105000-105799 (declared; materialised HERE from a single sink
bound to an explicit `range` so `scripts/seed_audit.py` can RESOLVE every one of
them statically instead of reporting an unknown sink).  Run from the
gamma-substrate dir:

    PYTHONPATH=runners/dsl/python:. python scripts/gapverify_measure.py

VERDICTS come from the AGENT'S OWN RULE (`seeds/gap_verify.json` writes
`status`/`verified`/`vviolations`); the direct Term evaluations are DIAGNOSTIC
ONLY and exist to catch the phi rung's silent-refusal trap.
"""
from __future__ import annotations
import json
import sys

import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core            # noqa: E402
from domains import reflective_faculty as rf          # noqa: E402
from substrate.seed_loader import manifest_for        # noqa: E402
import substrate_rs as srs                            # noqa: E402

# --- the engine this rung's numbers are attributed to (PROTOCOL 10.1 rule 1).
# Printed from INSIDE the measuring process and compared; divergence ABORTS.
# (A green provenance gate in a DIFFERENT process is not provenance.)
EXPECT_ENGINE = "d657468d9e1f"

# --- stimulus configuration (PROTOCOL 13: declared residuals; construction
# only, never a verdict threshold).  DOT/FIELD/BG/FG/ROW/DT are INHERITED
# UNCHANGED from the phi/timephi/gapabduce rungs. -----------------------------
DOT = 4              # phi rung's DOT = BLOCK
FIELD_H = 24
FIELD_W = 160
BG = 0
FG = 255
OCC = 128            # the occluder's luminance -- a DISTINCT SURFACE, so the
                     # graph separates figure from scene without being told
ROW = 8
DT = ["pred", "coord:r", "coord:c", "val"]

# --- THIS RUNG'S NEW configuration: the occluding bar --------------------- #
B0 = 68              # the bar's left column
BW = 20              # the bar's width
# The full passage: the dot enters flush at the bar's left edge and exits flush
# at its right, so the TOTAL displacement is fixed and only the GAP LENGTH
# varies.  Both banks have the dot DISJOINT from the bar at every k.
ENTER = B0 - DOT
EXIT = B0 + BW
PASSAGE = EXIT - ENTER          # = BW + DOT, the fixed endpoint displacement

# --- the INDEPENDENT VARIABLES: iterated, never compared against -------------
S_GRID = [1, 2, 4, 6, 8, 12, 16, 20, 32]
K_GRID = [0, 1, 2, 3, 4, 5, 6, 7]
# The tunnel axis runs past the predicted cliff DELIBERATELY: a cutoff that the
# grid cannot reach is a measure blind by construction (PROTOCOL 12.2).
T_GRID = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

# --- THE REGISTERED PREDICTIONS (prereg 9.1), stated before the run.  These
# are PREDICTIONS compared by EQUALITY, not thresholds: moving a member does not
# adjust sensitivity, it asserts a different proposition. --------------------
CLIFF_VERIFIED = (0, 1, 2, 3, 5)      # k where GapVerify verifies
CLIFF_DISAGREE = (7, 11)              # k where abduction and verification part

# The NOISE control's ONLY randomness.  Every draw is materialised HERE, from a
# single sink bound to an explicit `range`, so the seed audit can resolve it.
NOISE_LO = 105000
NOISE_HI = 105800
DRAWS: dict[int, list[int]] = {}

# The CODEBOOK-LIVENESS probe: a known-good abduction evaluated in the SAME
# booted substrate as every measured condition.  See `_codebook_live`.
COORD_VIOLATIONS: list[str] = []

# The abduction fields that must be IDENTICAL across the COVERED/EXPOSED pair.
ABDUCTION_FIELDS = ("vabduced", "vcloses", "voffset", "vcorrection", "vsteps")


# --------------------------------------------------------------------------- #
#  world: PIXELS.  The adapter renders a frame and converts it to cells by an
#  EXACT comparison against the frame's OWN modal luminance -- data-derived, no
#  constant.  (PROTOCOL 0: the adapter translates; it decides nothing.)
# --------------------------------------------------------------------------- #
def render(col: int | None, bar: int | None = None, size: int = DOT) -> np.ndarray:
    """A uniform field carrying an optional occluding bar at column `bar` and an
    optional hard-edged size x size dot at column `col`."""
    f = np.full((FIELD_H, FIELD_W), BG, dtype=np.uint8)
    if bar is not None:
        f[:, bar:bar + BW] = OCC
    if col is not None:
        f[ROW:ROW + size, col:col + size] = FG
    return f


def cells_fig(frame: np.ndarray) -> list[list]:
    """FIGURE cells: those whose luminance differs from the frame's own modal
    luminance.  A figure/ground split -- SUPPLIED STRUCTURE, declared as such.

    INHERITED BOUND (timephi A1, unchanged and not fixed here): the Term reuses
    `infer_translate_offset` and therefore CANNOT CONSUME A BOUNDED PIXEL FIELD
    AT ALL.  Every positive number in this rung is CONDITIONAL on this
    segmentation, which the ADAPTER supplied."""
    vals, counts = np.unique(frame, return_counts=True)
    modal = int(vals[int(np.argmax(counts))])
    rs, cs = np.nonzero(frame != modal)
    return [["px", int(r), int(c), int(frame[r, c])] for r, c in zip(rs, cs)]


def blank_seq(cols) -> list[list[list]]:
    """The CLASSIC phi encoding: no scene at all, `None` -> EMPTY frame."""
    return [([] if c is None else cells_fig(render(c))) for c in cols]


def phi_seq(col0: int, S: int, k: int) -> list[list[list]]:
    """THE PHI TOPOLOGY: ONE pre-gap sample, k blank frames, one resumed sample.
    `prefix_len == 1` is exactly the condition at which `BlinkBridge` FREEZES."""
    return blank_seq([col0] + [None] * k + [col0 + S])


def scene_seq(c1: int, c2: int, k: int, gap_bar: int | None = None,
              bar: int | None = None) -> list[list[list]]:
    """AN OCCUPIED GAP: the banks carry dot + bar; the k gap frames carry the
    scene ALONE (the figure absent, everything else observed).  `gap_bar`
    defaults to the banks' bar -- passing a different column DISPLACES the
    occluder in the gap frames ONLY, leaving both banks BYTE-IDENTICAL."""
    b = B0 if bar is None else bar
    gb = b if gap_bar is None else gap_bar
    return ([cells_fig(render(c1, b))]
            + [cells_fig(render(None, gb))] * k
            + [cells_fig(render(c2, b))])


# --------------------------------------------------------------------------- #
#  substrate: the AGENT decides.  We present an Observation and read `status`.
# --------------------------------------------------------------------------- #
def _boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    native.load_seed_manifest(manifest_for("gap_verify"), ag)
    s.set_attr(ag, "gap_verify_enabled", 1.0)
    s.add_node("ShapeSignature",
               {"name": "px_base", "signature": json.dumps(cells_fig(render(0))),
                "kind": "faculty", "faculty": "px_base", "dim_types": DT})
    return s, ag, native


def _codebook_live(s, tag: str) -> tuple:
    """THE TRAP GATE, DONE RIGHT.  Evaluate the Term on a KNOWN-GOOD abduction in
    the SAME booted substrate as the measured condition and read its
    `coord_dims`.

    The timephi rung's trap gate was ITSELF INERT: it read `coord_dims` off the
    MEASURED call, but the refusal constructor hardcodes that field empty, so it
    is an OUTPUT of the verdict and cannot tell "no codebook" from "no orbit" --
    167 false accusations (PROTOCOL 1.1: an absence off a guarded path is
    evidence of a LOOKUP, not of a measurement).  A PAIRED POSITIVE PROBE in the
    same process CAN: if the codebook were absent the probe would be empty too."""
    t = srs.Term("GapVerify", sequence=srs.Lit(scene_seq(ENTER, EXIT, 2)),
                 codebook_type="ShapeSignature", max_b=8, field="coord_dims")
    cd = tuple(s.evaluate(t, {}) or ())
    if len(cd) == 0:
        COORD_VIOLATIONS.append(tag)
    return cd


def run(frames, tag: str) -> dict:
    """Present a gap sequence; the `gap_verify` RULE decides.  The direct Term
    reads are DIAGNOSTIC (PROTOCOL 10.2 rule 1: positive-control the WIRING)."""
    s, ag, native = _boot()
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                                   "status": "gap_vseq", "key": ["gapverify"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]

    def term(field):
        t = srs.Term("GapVerify", sequence=srs.Lit(frames),
                     codebook_type="ShapeSignature", max_b=8, field=field)
        return s.evaluate(t, {})

    probe_cd = _codebook_live(s, tag)
    return {"probe_coord_dims": probe_cd,
            "status": at.get("status"),
            "verified": float(at.get("verified") or 0.0) == 1.0,
            "vabduced": float(at.get("vabduced") or 0.0) == 1.0,
            "vcloses": float(at.get("vcloses") or 0.0) == 1.0,
            "vdivisible": float(at.get("vdivisible") or 0.0) == 1.0,
            "vreason": at.get("vreason"),
            "vkind": at.get("vkind"),
            "voffset": tuple(term("offset") or ()),
            "vtotal": tuple(term("total") or ()),
            "vgap": at.get("vgap"),
            "vsteps": at.get("vsteps"),
            "vprefix": at.get("vprefix"),
            "vcorrection": at.get("vcorrection"),
            "vviolations": at.get("vviolations"),
            "vticks": at.get("vticks"),
            "vpredicted": at.get("vpredicted"),
            "vcovered": at.get("vcovered"),
            "vsurfaces": at.get("vsurfaces"),
            "vhidden": at.get("vhidden")}


def run_incumbent(frames) -> dict:
    """`GapAbduce` on the same stimulus -- the INCUMBENT, evaluated on its own
    native (blank-gap) encoding.  Direct Term reads; this rung installs no
    `gap_abduce` rule and moves nothing that belongs to its predecessor."""
    s, _ag, _native = _boot()

    def term(field):
        t = srs.Term("GapAbduce", sequence=srs.Lit(frames),
                     codebook_type="ShapeSignature", max_b=8, field=field)
        return s.evaluate(t, {})
    return {"vabduced": term("explained"),
            "vcloses": term("closes"),
            "voffset": tuple(term("offset") or ()),
            "vcorrection": term("correction"),
            "vsteps": term("steps"),
            "reason": term("reason")}


# ======================= THE VERDICTS (PROTOCOL 13) ======================== #
#  Every verdict below decides by EXACT EQUALITY on a logical, integer or SET
#  quantity, or by an ordering between two MEASURED quantities.  No ordering
#  against a tuned constant decides anything.
#  `tests/test_gapverify_ast_migrated.py` binds these functions BY NAME as AST
#  FunctionDef nodes -- never by substring -- with module-level NAME BINDINGS
#  RESOLVED TO THEIR LITERALS (a name bound to a literal IS a literal).
# =========================================================================== #
VERDICTS = ("v_a0_pos", "v_a0_neg", "v_a0_coord", "v_a0_fields",
            "v_a1_equivalence", "v_a2_refusable", "v_a2_abduction_unmoved",
            "v_a3_cliff", "v_a3_disagreement", "v_a3_isi_interior",
            "v_a3_isi_falsified", "v_a4_full_search", "v_a5_blank_forced")


def v_a0_pos(pos) -> bool:
    """A0-POS WIRING: a dot crossing a bar that COVERS its whole predicted path
    is abduced AND verified, with nothing left unaccounted."""
    return (pos["vabduced"] and pos["verified"] and pos["vkind"] == "translate"
            and int(pos["vviolations"]) == 0 and int(pos["vcorrection"]) == 0
            and pos["status"] == "gap_verified")


def v_a0_neg(neg) -> bool:
    """A0-NEG WIRING: a STATIONARY dot behind the same bar is REFUSED as the
    identity -- the reader DISCRIMINATES rather than accepting everything."""
    return (not neg["vabduced"]) and neg["vreason"] == "identity"


def v_a0_coord(violations) -> bool:
    """The in-process CODEBOOK-LIVENESS probe fired on no call."""
    return len(violations) == 0


def v_a0_fields(ref) -> bool:
    """`refused()` calls `finish()`, WHICH SELECTS THE FIELD -- so a value
    restored on a refusal AFTER the Dict is built silently does nothing on every
    call that asks for it.  That cost the predecessor 42 wrong `total` fields and
    was caught by a MECHANISM TEST, not by inspection.

    So: every field this rung reads off a REFUSAL is asserted here to carry its
    measured value rather than a constructor's default.  On a refusal that
    happened AFTER the full check (`unverified`), the tick and cell counters must
    be non-degenerate and the arithmetic must close."""
    return (ref["vreason"] == "unverified"
            and int(ref["vticks"]) == int(ref["vgap"])
            and int(ref["vpredicted"]) != 0
            and int(ref["vviolations"]) == int(ref["vpredicted"]) - int(ref["vcovered"]))


def v_a1_equivalence(pairs) -> bool:
    """P1 -- EQUIVALENCE.  On the CLASSIC blank-gap grid, `GapVerify`'s
    ABDUCTION is identical to `GapAbduce`'s, cell for cell.  The surface-set
    split GENERALISES the incumbent's empty-run split and must REDUCE to it: an
    empty frame's key set is the empty set, a strict subset of any non-empty
    set.  This is different code and it can disagree."""
    return all(mine[f] == theirs[f] for mine, theirs in pairs.values()
               for f in ABDUCTION_FIELDS)


def v_a2_refusable(pair) -> bool:
    """P2 -- THE HEADLINE, AND IT IS NOT FORCED.  Two stimuli with BYTE-IDENTICAL
    banks, differing ONLY in what the gap frames show, must receive DIFFERENT
    verdicts: the covered path verifies with nothing unaccounted, the exposed
    path is refused with a measured violation count.

    A NULL HERE KILLS THE RUNG -- if the check cannot separate these, it is
    decorative (PROTOCOL 13.2) and no other number here means anything."""
    cov, exp = pair["covered"], pair["exposed"]
    return (cov["verified"] and int(cov["vviolations"]) == 0
            and (not exp["verified"]) and int(exp["vviolations"]) != 0
            and exp["vreason"] == "unverified")


def v_a2_abduction_unmoved(pair) -> bool:
    """P2's OTHER HALF, and the sharper one: across that same pair the
    ABDUCTION must be IDENTICAL.  This is PROTOCOL 1's fifth clause pointed at
    the mechanism -- it moves the verification attributes WHILE PROVABLY MOVING
    NOTHING ELSE, so the separation cannot be some other quantity in disguise."""
    cov, exp = pair["covered"], pair["exposed"]
    return all(cov[f] == exp[f] for f in ABDUCTION_FIELDS)


def v_a3_cliff(tunnel) -> bool:
    """P3 -- THE TUNNEL CLIFF, PREDICTED TO THE EXACT INTEGER BEFORE THE RUN.

    On a fixed full passage the arithmetic admits every k whose steps divide the
    displacement; the GEOMETRY admits only those where the object moves at least
    its own width per step, i.e. k <= BW/DOT.  `CLIFF_VERIFIED` is that
    prediction, registered in the pre-registration's addendum.

    It is compared by SET EQUALITY, not by an ordering: moving a member does not
    adjust sensitivity, it asserts a different proposition.  A cliff anywhere
    else falsifies my model of my own mechanism."""
    got = tuple(sorted(k for k, v in tunnel.items() if v["verified"]))
    return got == tuple(sorted(CLIFF_VERIFIED))


def v_a3_disagreement(tunnel) -> bool:
    """P3's PAIRED FORM: the k at which ABDUCTION and VERIFICATION part company
    -- where the arithmetic is fine but the object could not have been hidden.
    Registered in advance as `CLIFF_DISAGREE`."""
    got = tuple(sorted(k for k, v in tunnel.items()
                       if v["vabduced"] != v["verified"]))
    return got == tuple(sorted(CLIFF_DISAGREE))


def v_a3_isi_interior(R) -> bool:
    """THE REGISTERED ISI DISCRIMINATOR, CONFIRMING BRANCH: an interior optimum
    requires the argmax to sit away from zero AND to STRICTLY EXCEED R(0).

    NON-MONOTONICITY IS NOT AN INTERIOR OPTIMUM.  The predecessor's curve was a
    jagged divisor comb, and a rung that had registered only 'is it monotone?'
    would have scored it as CONFIRMING and published the opposite of the truth.
    THE MAXIMUM'S LOCATION IS THE DISCRIMINATOR; the jaggedness is arithmetic.

    Declared UNREACHABLE in advance (prereg 4/P4): verification is a MONOTONE
    FILTER -- it can only remove acceptances -- and R(0) is doubly forced (every
    integer divides by 1; at gap 0 there are NO intermediates, so the check is
    vacuous).  A filter cannot raise anything, so this branch cannot fire."""
    kstar = min(T_GRID, key=lambda k: (-R[k], k))
    return kstar != 0 and R[kstar] > R[0]


def v_a3_isi_falsified(R) -> bool:
    """THE FALSIFYING BRANCH: R(0) is a global maximum, so there is no interior
    optimum.  Reported alongside the TIE set -- a PLATEAU (R(0) tied with some
    k) reads AMBIGUOUS, and that distinction was registered in advance
    precisely so it could not be reinterpreted afterwards."""
    return all(R[0] >= R[k] for k in T_GRID)


def v_a4_full_search(rows) -> bool:
    """A REFUSAL MUST BE A FAILURE AFTER A FULL CHECK, NOT A REFUSAL AT A GUARD.

    Every `unverified` verdict in the noise arm must have checked every gap tick
    and compared a non-zero number of cells.  A refusal with nothing predicted
    would be a guard wearing a measurement's clothes -- a PROTOCOL 13 negative,
    and it would be reported as one."""
    return all(int(r["vticks"]) == int(r["vgap"]) and int(r["vpredicted"]) != 0
               for r in rows if r["vreason"] == "unverified")


def v_a5_blank_forced(blank) -> bool:
    """P6 -- BLANK-GAP STRICTNESS.  DECLARED FORCED in advance (PROTOCOL 13.1):
    on a genuinely blank gap NOTHING is observed, so every predicted cell is
    unaccounted and the verdict could not have been anything else.  It carries
    NO evidential weight and is run only to confirm the source reading against
    the REAL ENGINE -- the thing a doc comment failed at four times this week.

    It is also a SCOPE STATEMENT: under strict accountability the substrate is
    MORE REFUSING THAN A HUMAN on classic phi."""
    return all((not v["verified"]) and int(v["vviolations"]) == int(v["vpredicted"])
               and int(v["vpredicted"]) != 0 for v in blank.values())


# ===================== THE ANALYTIC EXPECTATIONS =========================== #
#  Computed by EXHAUSTIVE ENUMERATION over the sampling grid, INSIDE the runner,
#  BEFORE the arm is read.  A FORMULA, never a remembered approximation: the
#  timephi rung's "noise" control was not one (three uniform draws are equally
#  spaced ~1/156 of the time, so a "spurious" accept was the mechanism being
#  CORRECT), and the gapabduce rung fixed that by registering the formula.
#  These are NOT verdicts and are not scanned as such -- they are the
#  expectation each measured cell is reported against.
# =========================================================================== #
def _disjoint(c: int) -> bool:
    """The dot at column `c` does not touch the bar.  When it does, it OCCLUDES
    the bar, the bar's own cell count differs between the two banks, and the
    per-surface rigidity test refuses `not_rigid` -- a condition the registered
    formula (prereg 4/P5) OMITTED.  Reported, not hidden (prereg 9.3)."""
    return (c + DOT <= B0) or (c >= B0 + BW)


def _covered(c1: int, d: int, steps: int) -> bool:
    """Every intermediate lies wholly behind the bar."""
    v = d // steps
    return all(B0 <= c1 + t * v and c1 + t * v + DOT <= B0 + BW
               for t in range(1, steps))


def analytic(steps: int, *, verify: bool, rigid: bool) -> float:
    """The exact rate over the uniform pair on this grid.

    `verify=False, rigid=False` is the REGISTERED formula verbatim (the
    incumbent's divisibility alone).  `rigid=True` adds the bank-rigidity
    condition the registered formula omitted; `verify=True` adds coverage."""
    hi = FIELD_W - DOT
    n = 0
    hits = 0
    for c1 in range(hi):
        for c2 in range(hi):
            n += 1
            d = c2 - c1
            if d == 0 or d % steps != 0:
                continue
            if rigid and not (_disjoint(c1) and _disjoint(c2)):
                continue
            if verify and not _covered(c1, d, steps):
                continue
            hits += 1
    return hits / n


# ============================ THE ARMS ===================================== #
def main() -> int:
    R: dict = {"engine": provenance_line(), "prereg": "VISION_GAPVERIFY_PREREG.md",
               "prereg_commit": "5e2c34cb", "prereg_addendum": "1f4ca5a7"}
    print("ENGINE (from INSIDE the measuring process):", R["engine"])
    if EXPECT_ENGINE not in R["engine"]:
        print(f"ABORT: engine divergence -- expected {EXPECT_ENGINE}")
        return 2
    ok: dict = {}

    # --- A0: WIRING CONTROL.  RUN FIRST.  Nothing else is interpreted if it
    #     fails.  (The phi rung nearly published a perfect fake null off
    #     silently-refused `has_region` edges.)
    print("\n[A0] WIRING CONTROL -- before any hypothesis arm")
    pos = run(scene_seq(ENTER, EXIT, 2), "A0-POS")
    neg = run(scene_seq(ENTER, ENTER, 2), "A0-NEG")
    ref = run(scene_seq(ENTER, EXIT, 2, gap_bar=B0 - 40), "A0-FIELDS")
    ok["A0_pos"] = v_a0_pos(pos)
    ok["A0_neg"] = v_a0_neg(neg)
    ok["A0_fields"] = v_a0_fields(ref)
    R["A0"] = {"pos": pos, "neg": neg, "refusal": ref}
    print(f"  A0-POS  covered passage -> abduced={pos['vabduced']} "
          f"verified={pos['verified']} viol={pos['vviolations']} "
          f"pred={pos['vpredicted']} status={pos['status']}  PASS={ok['A0_pos']}")
    print(f"  A0-NEG  stationary dot  -> abduced={neg['vabduced']} "
          f"reason={neg['vreason']}  PASS={ok['A0_neg']}")
    print(f"  A0-FIELDS refusal reads -> reason={ref['vreason']} "
          f"ticks={ref['vticks']} pred={ref['vpredicted']} "
          f"cov={ref['vcovered']} viol={ref['vviolations']}  "
          f"PASS={ok['A0_fields']}")
    if not (ok["A0_pos"] and ok["A0_neg"] and ok["A0_fields"]):
        print("  ABORT: wiring control failed; no arm is interpretable.")
        R["ABORT"] = "A0 wiring control failed"
        json.dump(R, open("results/gapverify_measure.json", "w"), indent=1)
        return 3

    # --- A1: EQUIVALENCE on the CLASSIC blank-gap grid (P1) -----------------
    print("\n[A1] P1 EQUIVALENCE: the abduction is unchanged on the blank grid")
    pairs = {}
    for S in S_GRID:
        for k in K_GRID:
            frames = phi_seq(0, S, k)
            pairs[(S, k)] = (run(frames, f"A1-S{S}-k{k}"), run_incumbent(frames))
    ok["A1_equivalence"] = v_a1_equivalence(pairs)
    n_diff = sum(1 for m, t in pairs.values()
                 if any(m[f] != t[f] for f in ABDUCTION_FIELDS))
    R["A1"] = {f"S{S}-k{k}": {"mine": m, "incumbent": t}
               for (S, k), (m, t) in pairs.items()}
    R["A1_cells"] = len(pairs)
    R["A1_disagreeing_cells"] = n_diff
    print(f"  {len(pairs)} cells, abduction fields {ABDUCTION_FIELDS}")
    print(f"  disagreeing cells: {n_diff}   PASS={ok['A1_equivalence']}")

    # --- A2: THE PAIRED CONTRAST (P2) -- the headline ----------------------
    print("\n[A2] P2 THE PAIRED CONTRAST: identical banks, different gap content")
    pair = {"covered": run(scene_seq(ENTER, EXIT, 2), "A2-COVERED"),
            "exposed": run(scene_seq(ENTER, EXIT, 2, gap_bar=B0 - 40), "A2-EXPOSED")}
    ok["A2_refusable"] = v_a2_refusable(pair)
    ok["A2_abduction_unmoved"] = v_a2_abduction_unmoved(pair)
    # PROTOCOL 1 clause 5: the mechanism must MOVE something downstream.
    vacuity = {f: abs(float(pair["covered"][f] or 0) - float(pair["exposed"][f] or 0))
               for f in ("vviolations", "vcovered")}
    vacuity["verified"] = float(pair["covered"]["verified"] != pair["exposed"]["verified"])
    R["A2"] = pair
    R["A2_vacuity_D"] = vacuity
    for nm, v in pair.items():
        print(f"  {nm:8s} abduced={v['vabduced']} offset={v['voffset']} "
              f"corr={v['vcorrection']} | verified={v['verified']} "
              f"viol={v['vviolations']} cov={v['vcovered']}/{v['vpredicted']}")
    print(f"  => P2 REFUSABLE: {ok['A2_refusable']}   "
          f"abduction unmoved: {ok['A2_abduction_unmoved']}")
    print(f"  => vacuity D (max|on-off|): {vacuity}")

    # --- A3: THE TUNNEL CLIFF (P3) and THE ISI DISCRIMINATOR ---------------
    print("\n[A3] P3 THE TUNNEL CLIFF -- fixed passage, gap length varies")
    tunnel = {}
    for k in T_GRID:
        tunnel[k] = run(scene_seq(ENTER, EXIT, k), f"A3-k{k}")
    ok["A3_cliff"] = v_a3_cliff(tunnel)
    ok["A3_disagreement"] = v_a3_disagreement(tunnel)
    R["A3"] = {str(k): v for k, v in tunnel.items()}
    for k in T_GRID:
        v = tunnel[k]
        print(f"  k={k:2d} steps={str(v['vsteps']):>3s} off={str(v['voffset']):>8s} "
              f"abduced={str(v['vabduced']):5s} verified={str(v['verified']):5s} "
              f"viol={str(v['vviolations']):>4s}/{str(v['vpredicted']):<4s} "
              f"reason={v['vreason']}")
    got_v = tuple(sorted(k for k, v in tunnel.items() if v["verified"]))
    got_a = tuple(sorted(k for k, v in tunnel.items() if v["vabduced"]))
    print(f"  ABDUCTION admits   k = {got_a}")
    print(f"  VERIFICATION admits k = {got_v}   (registered {tuple(CLIFF_VERIFIED)})")
    print(f"  => P3 CLIFF: {ok['A3_cliff']}   DISAGREEMENT: {ok['A3_disagreement']}")

    Rk = {k: (1.0 if tunnel[k]["verified"] else 0.0) for k in T_GRID}
    ok["A3_isi_interior_optimum"] = v_a3_isi_interior(Rk)
    ok["A3_isi_falsified"] = v_a3_isi_falsified(Rk)
    kstar = min(T_GRID, key=lambda k: (-Rk[k], k))
    ties = [k for k in T_GRID if k != 0 and Rk[k] == Rk[0]]
    verdict = ("INTERIOR OPTIMUM" if ok["A3_isi_interior_optimum"]
               else ("AMBIGUOUS (tie)" if ties else "FALSIFIED"))
    R["A3_ISI_curve"] = {str(k): Rk[k] for k in T_GRID}
    R["A3_kstar"] = kstar
    R["A3_ties_with_k0"] = ties
    R["A3_verdict"] = verdict
    print(f"  => ISI argmax k* = {kstar}  ties with k0: {ties}")
    print(f"  => REGISTERED ISI VERDICT: {verdict}")

    # --- A4: THE NOISE ARM (P5) -- ANALYTIC EXPECTATIONS COMPUTED FIRST ----
    print("\n[A4] P5 NOISE: independent random endpoints against a FIXED scene")
    hi = FIELD_W - DOT
    for sd in range(NOISE_LO, NOISE_HI):
        DRAWS[sd] = [int(x) for x in
                     np.random.default_rng(sd).integers(0, hi, size=2)]
    expectations = {k: {
        "registered_abduced": round(analytic(k + 1, verify=False, rigid=False), 4),
        "exact_abduced": round(analytic(k + 1, verify=False, rigid=True), 4),
        "exact_verified": round(analytic(k + 1, verify=True, rigid=True), 4),
    } for k in K_GRID}
    print("  ANALYTIC EXPECTATIONS (computed before any arm is read):")
    for k in K_GRID:
        e = expectations[k]
        print(f"    k={k} steps={k+1}: registered_abduced={e['registered_abduced']:.4f} "
              f"exact_abduced={e['exact_abduced']:.4f} "
              f"exact_verified={e['exact_verified']:.4f}")

    noise = {}
    all_rows = []
    for k in K_GRID:
        sds = list(range(NOISE_LO + 100 * k, NOISE_LO + 100 * (k + 1)))
        rows = [run(scene_seq(DRAWS[sd][0], DRAWS[sd][1], k), f"A4-k{k}-{sd}")
                for sd in sds]
        all_rows.extend(rows)
        n_abd = sum(1 for r in rows if r["vabduced"])
        n_ver = sum(1 for r in rows if r["verified"])
        reasons: dict = {}
        for r in rows:
            reasons[r["vreason"]] = reasons.get(r["vreason"], 0) + 1
        e = expectations[k]
        noise[k] = {"n": len(rows), "seeds": [sds[0], sds[-1]],
                    "abduced": n_abd, "verified": n_ver,
                    "abduced_rate": n_abd / len(rows),
                    "verified_rate": n_ver / len(rows),
                    "conditional_verified_given_abduced":
                        (n_ver / n_abd) if n_abd else None,
                    "reasons": reasons, **e}
        print(f"  k={k} steps={k+1}: abduced {n_abd:3d}/100 (exp "
              f"{e['exact_abduced']*100:5.1f}) | verified {n_ver:3d}/100 (exp "
              f"{e['exact_verified']*100:5.1f}) | P(ver|abd)="
              f"{(n_ver/n_abd) if n_abd else float('nan'):.3f}  {reasons}")
    ok["A4_full_search"] = v_a4_full_search(all_rows)
    R["A4_noise"] = {str(k): v for k, v in noise.items()}
    print(f"  => every refusal is a FAILURE AFTER A FULL CHECK: "
          f"{ok['A4_full_search']}")

    # --- A5: BLANK-GAP STRICTNESS (P6, FORCED) -----------------------------
    print("\n[A5] P6 BLANK-GAP STRICTNESS (DECLARED FORCED, zero weight)")
    blank = {}
    for k in K_GRID:
        if k != 0:
            blank[k] = run(phi_seq(0, PASSAGE, k), f"A5-k{k}")
    ok["A5_blank_forced"] = v_a5_blank_forced(blank)
    R["A5"] = {str(k): v for k, v in blank.items()}
    for k, v in blank.items():
        print(f"  k={k} abduced={v['vabduced']} verified={v['verified']} "
              f"viol={v['vviolations']}/{v['vpredicted']} reason={v['vreason']}")
    print(f"  => forced null confirmed on the real engine: "
          f"{ok['A5_blank_forced']}")

    # --- the trap gate: the in-process CODEBOOK-LIVENESS probe --------------
    ok["A0_coord"] = v_a0_coord(COORD_VIOLATIONS)
    R["A0_coord_violations"] = COORD_VIOLATIONS
    print(f"\n[A0-COORD] in-process codebook probe empty on "
          f"{len(COORD_VIOLATIONS)} call(s): PASS={ok['A0_coord']}")

    R["ok"] = ok
    json.dump(R, open("results/gapverify_measure.json", "w"), indent=1)
    print("\n=== SUMMARY ===")
    for k2, v in ok.items():
        print(f"  {k2:28s} {v}")
    print(f"  {'ISI VERDICT':28s} {verdict}")
    print("\nwrote results/gapverify_measure.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
