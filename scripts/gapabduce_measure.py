#!/usr/bin/env python3
"""DOES AN ENDPOINT-ABDUCED GENERATOR CLOSE THE PHI TOPOLOGY -- AND DOES IT BUY
THE HUMAN ISI CURVE?

The confirmatory measurement for `VISION_GAPABDUCE_PREREG.md` (committed
8a5fd11c before any number). Successor to the timephi rung (93000-93999), which
named this operator as the one thing the substrate lacks:

    solve G^(k+1)(f_before) = f_after for G -- a DIVISIBILITY TEST, NO THRESHOLD

Every arm is DETERMINISTIC except the NOISE control, whose random dot positions
draw from seeds 97000-97899 (declared; materialised HERE from a single sink bound
to an explicit `range` so `scripts/seed_audit.py` can RESOLVE every one of them
statically instead of reporting an unknown sink). Run from the gamma-substrate
dir:

    PYTHONPATH=runners/dsl/python:. python scripts/gapabduce_measure.py

VERDICTS come from the AGENT'S OWN RULE (`seeds/gap_abduce.json` writes
`status`/`abduced`/`closes`); the direct Term evaluations are DIAGNOSTIC ONLY and
exist to catch the phi rung's silent-refusal trap.
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
# (A green provenance gate in a DIFFERENT process is not provenance -- measured
# 2026-07-19: 7 PASSED in the same minute a script resolved the wrong engine.)
EXPECT_ENGINE = "9931e144d19b"

# --- stimulus configuration (PROTOCOL 13: declared residuals, inherited from
# the phi/timephi rungs; construction only, never a verdict threshold) ---------
DOT = 4              # phi rung's DOT = BLOCK
FIELD_H = 24
FIELD_W = 160
BG = 0
FG = 255
ROW = 8
DT = ["pred", "coord:r", "coord:c", "val"]

# --- the INDEPENDENT VARIABLES: iterated, never compared against -------------
S_GRID = [1, 2, 4, 6, 8, 12, 16, 20, 32]
# K_GRID is extended past the predecessor's 0..4 DELIBERATELY: an interior
# optimum must be given room to appear.  Truncating at 4 would make the
# discriminator unable to find the thing it exists to look for -- PROTOCOL 12.2's
# blind-by-construction defect, in the time domain.
K_GRID = [0, 1, 2, 3, 4, 5, 6, 7]

# The NOISE control's ONLY randomness.  Every draw is materialised HERE, from a
# single sink bound to an explicit `range`, so the seed audit can resolve it.
NOISE_LO = 97000
NOISE_HI = 97900
DRAWS: dict[int, list[int]] = {}

# The CODEBOOK-LIVENESS probe: a known-good abduction evaluated in the SAME
# booted substrate as every measured condition.  See `_codebook_live`.
PROBE_COLS = (0, None, 4)
COORD_VIOLATIONS: list[str] = []


# --------------------------------------------------------------------------- #
#  world: PIXELS.  The adapter renders a frame and converts it to cells by an
#  EXACT comparison against the frame's OWN modal luminance -- data-derived, no
#  constant.  (PROTOCOL 0: the adapter translates; it decides nothing.)
# --------------------------------------------------------------------------- #
def render(col: int | None, size: int = DOT) -> np.ndarray:
    """A uniform field carrying one hard-edged size x size dot at column `col`.
    `col is None` renders the blank field."""
    f = np.full((FIELD_H, FIELD_W), BG, dtype=np.uint8)
    if col is not None:
        f[ROW:ROW + size, col:col + size] = FG
    return f


def cells_fig(frame: np.ndarray) -> list[list]:
    """FIGURE cells: those whose luminance differs from the frame's own modal
    luminance.  A figure/ground split -- SUPPLIED STRUCTURE, declared as such.

    INHERITED BOUND (timephi A1, unchanged and not fixed here): `TimeInfer` --
    and therefore `GapAbduce`, which reuses the same `infer_translate_offset` --
    CANNOT CONSUME A BOUNDED PIXEL FIELD AT ALL.  Every positive number in this
    rung is CONDITIONAL on this segmentation, which the ADAPTER supplied."""
    vals, counts = np.unique(frame, return_counts=True)
    modal = int(vals[int(np.argmax(counts))])
    rs, cs = np.nonzero(frame != modal)
    return [["px", int(r), int(c), int(frame[r, c])] for r, c in zip(rs, cs)]


def seq(cols, size: int = DOT) -> list[list[list]]:
    """A frame sequence in the FIGURE representation; `None` -> EMPTY frame."""
    return [([] if c is None else cells_fig(render(c, size))) for c in cols]


def phi_seq(col0: int, S: int, k: int, size: int = DOT) -> list[list[list]]:
    """THE PHI TOPOLOGY: ONE pre-gap sample, k blank frames, one resumed sample.
    `prefix_len == 1` is exactly the condition at which `BlinkBridge` FREEZES."""
    return seq([col0] + [None] * k + [col0 + S], size)


# --------------------------------------------------------------------------- #
#  substrate: the AGENT decides.  We present an Observation and read `status`.
# --------------------------------------------------------------------------- #
def _boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    native.load_seed_manifest(manifest_for("gap_abduce"), ag)
    s.set_attr(ag, "gap_abduce_enabled", 1.0)
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
    t = srs.Term("GapAbduce", sequence=srs.Lit(seq(PROBE_COLS)),
                 codebook_type="ShapeSignature", max_b=8, field="coord_dims")
    cd = tuple(s.evaluate(t, {}) or ())
    if len(cd) == 0:
        COORD_VIOLATIONS.append(tag)
    return cd


def run(frames, tag: str) -> dict:
    """Present a gap sequence; the `gap_abduce` RULE decides.  The direct Term
    reads are DIAGNOSTIC (PROTOCOL 10.2 rule 1: positive-control the WIRING)."""
    s, ag, native = _boot()
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                                   "status": "gap_seq", "key": ["gapabduce"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]

    def term(field):
        t = srs.Term("GapAbduce", sequence=srs.Lit(frames),
                     codebook_type="ShapeSignature", max_b=8, field=field)
        return s.evaluate(t, {})

    probe_cd = _codebook_live(s, tag)
    return {"probe_coord_dims": probe_cd,
            "status": at.get("status"),
            "abduced": float(at.get("abduced") or 0.0) == 1.0,
            "closes": float(at.get("closes") or 0.0) == 1.0,
            "divisible": float(at.get("divisible") or 0.0) == 1.0,
            "reason": at.get("abduce_reason"),
            "kind": at.get("abduce_kind"),
            "offset": tuple(term("offset") or ()),
            "total": tuple(term("total") or ()),
            "gap": at.get("abduce_gap"),
            "steps": at.get("abduce_steps"),
            "prefix": at.get("abduce_prefix"),
            "correction": at.get("abduce_correction"),
            "checked": term("checked")}


# ======================= THE VERDICTS (PROTOCOL 13) ======================== #
#  Every verdict below decides by EXACT EQUALITY on a logical or integer
#  quantity.  No ordering comparison against a tuned constant decides anything.
#  `tests/test_gapabduce_ast_migrated.py` binds these functions BY NAME as AST
#  FunctionDef nodes -- never by substring -- and asserts exactly that, with
#  module-level NAME BINDINGS RESOLVED TO THEIR LITERALS (the PROTOCOL 13 hole
#  named this week: a name bound to a literal IS a literal).
# =========================================================================== #
VERDICTS = ("v_a0_pos", "v_a0_neg", "v_a0_coord", "v_a1_p2", "v_a2_p3",
            "v_a2_p4", "v_a3_p5_interior", "v_a3_p5_falsified", "v_a4_p6_null")


def v_a0_pos(pos) -> bool:
    """A0-POS WIRING: a dot displaced 4 across a gap of 1 (2 divides 4) is
    abduced, closes exactly, and reports the HALVED offset."""
    return (pos["abduced"] and pos["closes"] and pos["kind"] == "translate"
            and pos["offset"] == (0, 2) and int(pos["correction"]) == 0)


def v_a0_neg(neg) -> bool:
    """A0-NEG WIRING: a STATIONARY dot across the same gap is REFUSED as the
    identity -- the reader DISCRIMINATES rather than accepting everything."""
    return (not neg["abduced"]) and neg["reason"] == "identity"


def v_a0_coord(violations) -> bool:
    """The in-process CODEBOOK-LIVENESS probe fired on no call."""
    return len(violations) == 0


def v_a1_p2(a1) -> bool:
    """P2 -- THE CAPABILITY, and the arm that is NOT forced by the ISI
    arithmetic.  At prefix_len == 1 (THE PHI TOPOLOGY, where `BlinkBridge`
    freezes with correction 32) a divisible displacement CLOSES the gap
    exactly, with the abduced per-step offset."""
    return all(v["abduced"] and v["closes"] and int(v["prefix"]) == 1
               and int(v["correction"]) == 0
               and v["offset"] == (0, S // (k + 1))
               for (S, k), v in a1.items())


def v_a2_p3(matrix) -> bool:
    """P3 -- THE DIVISIBILITY COMB: the gap closes EXACTLY IFF (k+1) divides S.
    An exact-equality biconditional over the whole grid, no exception admitted
    in either direction."""
    return all(v["abduced"] == (S % (k + 1) == 0)
               for (S, k), v in matrix.items())


def v_a2_p4(matrix) -> bool:
    """P4 -- LINEAR RESCUE: no non-divisible cell is rescued by a steps-th root
    in the integer 2x2 linear class."""
    return all(v["kind"] != "linear" for v in matrix.values())


def v_a3_p5_interior(R) -> bool:
    """THE REGISTERED DISCRIMINATOR, CONFIRMING BRANCH: an interior optimum
    requires the argmax to sit at k >= 1 AND to STRICTLY EXCEED R(0).

    NON-MONOTONICITY IS NOT AN INTERIOR OPTIMUM.  The divisor comb is jagged by
    construction (R(2) < R(3)), so a rung that registered only 'is it monotone?'
    would score this comb as CONFIRMING and publish the opposite of the truth.
    The maximum's LOCATION is the discriminator; the jaggedness is arithmetic.

    `kstar != 0` states the registered `k* >= 1` EXACTLY (K_GRID starts at 0),
    without an ORDERING against a non-zero literal.  Tightened against myself
    after the run and BEFORE the write-up: the proposition and the outcome are
    identical, and the re-run is asserted byte-identical.  PROTOCOL 1.1 permits
    making a measure stricter against yourself; 5 forbids only loosening one to
    rescue a failure."""
    kstar = min(K_GRID, key=lambda k: (-R[k], k))
    return kstar != 0 and R[kstar] > R[0]


def v_a3_p5_falsified(R) -> bool:
    """THE REGISTERED DISCRIMINATOR, FALSIFYING BRANCH: R(0) is a global
    maximum, so there is no interior optimum and the operator does NOT buy the
    human curve's shape."""
    return all(R[0] >= R[k] for k in K_GRID)


def v_a4_p6_null(n_accepted) -> bool:
    """The NON-TRANSLATE arm: endpoints that are not rigid translates of one
    another are refused.  DECLARED FORCED in advance (PROTOCOL 13.1): the
    cardinality check refuses at source, so this arm could not have produced a
    positive and carries NO evidential weight.  It is run to confirm the source
    reading against the REAL ENGINE -- the thing a doc comment failed at this
    week."""
    return n_accepted == 0


# ============================ THE ARMS ===================================== #
def main() -> int:
    R: dict = {"engine": provenance_line(), "prereg": "VISION_GAPABDUCE_PREREG.md",
               "prereg_commit": "8a5fd11c"}
    print("ENGINE (from INSIDE the measuring process):", R["engine"])
    if EXPECT_ENGINE not in R["engine"]:
        print(f"ABORT: engine divergence -- expected {EXPECT_ENGINE}")
        return 2
    ok: dict = {}

    # --- A0: WIRING CONTROL.  RUN FIRST.  Nothing else is interpreted if it
    #     fails.  (The phi rung nearly published a perfect fake null off
    #     silently-refused `has_region` edges: a mechanism whose output is "no
    #     correspondence" is indistinguishable from one that cannot express it.)
    print("\n[A0] WIRING CONTROL -- before any hypothesis arm")
    pos = run(phi_seq(0, 4, 1), "A0-POS")
    neg = run(seq([0, None, 0]), "A0-NEG")
    ok["A0_pos"] = v_a0_pos(pos)
    ok["A0_neg"] = v_a0_neg(neg)
    R["A0"] = {"pos": pos, "neg": neg}
    print(f"  A0-POS  dot +4 across gap 1 -> abduced={pos['abduced']} "
          f"closes={pos['closes']} offset={pos['offset']} "
          f"corr={pos['correction']}  PASS={ok['A0_pos']}")
    print(f"  A0-NEG  stationary dot      -> abduced={neg['abduced']} "
          f"reason={neg['reason']}  PASS={ok['A0_neg']}")
    if not (ok["A0_pos"] and ok["A0_neg"]):
        print("  ABORT: wiring control failed; no arm is interpretable.")
        R["ABORT"] = "A0 wiring control failed"
        json.dump(R, open("results/gapabduce_measure.json", "w"), indent=1)
        return 3

    # --- A1: THE CAPABILITY (P2) -- does the PHI TOPOLOGY now close? ---------
    #     Every (S,k) on the grid for which (k+1) divides S, at prefix_len == 1.
    print("\n[A1] P2 THE CAPABILITY: prefix_len==1 (THE PHI TOPOLOGY), divisible")
    a1 = {}
    for S in S_GRID:
        for k in K_GRID:
            if S % (k + 1) == 0:
                a1[(S, k)] = run(phi_seq(0, S, k), f"A1-S{S}-k{k}")
    ok["A1_P2"] = v_a1_p2(a1)
    R["A1"] = {f"S{S}-k{k}": v for (S, k), v in a1.items()}
    for S in S_GRID:
        row = [(k, a1[(S, k)]) for k in K_GRID if (S, k) in a1]
        print(f"  S={S:3d}  " + "  ".join(
            f"k={k}:off={v['offset']},corr={v['correction']}" for k, v in row))
    print(f"  => P2 (closes at prefix_len 1, correction 0, {len(a1)} conditions;"
          f" BlinkBridge reported correction 32 here): {ok['A1_P2']}")

    # --- A2: THE FULL S x k MATRIX (P3 comb, P4 linear rescue) --------------
    print("\n[A2] P3/P4: the full grid -- closes IFF (k+1) divides S?")
    matrix = {}
    for S in S_GRID:
        for k in K_GRID:
            matrix[(S, k)] = a1[(S, k)] if (S, k) in a1 \
                else run(phi_seq(0, S, k), f"A2-S{S}-k{k}")
    ok["A2_P3"] = v_a2_p3(matrix)
    ok["A2_P4"] = v_a2_p4(matrix)
    R["A2"] = {f"S{S}-k{k}": v for (S, k), v in matrix.items()}
    print("      k=" + "".join(f"{k:>4d}" for k in K_GRID))
    for S in S_GRID:
        print(f"  S={S:3d} " + "".join(
            f"{'  Y ' if matrix[(S, k)]['abduced'] else '  . '}" for k in K_GRID))
    n_lin = sum(1 for v in matrix.values() if v["kind"] == "linear")
    print(f"  => P3 (closes IFF divisible, {len(matrix)} cells): {ok['A2_P3']}")
    print(f"  => P4 (no linear rescue): {ok['A2_P4']}  (linear cells: {n_lin})")

    # --- A3: THE ISI CURVE and THE REGISTERED DISCRIMINATOR (P5) ------------
    print("\n[A3] P5 THE ISI CURVE -- the registered discriminator")
    Rk = {k: sum(1 for S in S_GRID if matrix[(S, k)]["abduced"]) / len(S_GRID)
          for k in K_GRID}
    ok["A3_P5_interior_optimum"] = v_a3_p5_interior(Rk)
    ok["A3_P5_falsified"] = v_a3_p5_falsified(Rk)
    kstar = min(K_GRID, key=lambda k: (-Rk[k], k))
    ties = [k for k in K_GRID if k >= 1 and Rk[k] == Rk[0]]
    verdict = ("INTERIOR OPTIMUM" if ok["A3_P5_interior_optimum"]
               else ("AMBIGUOUS (tie)" if ties else "FALSIFIED"))
    R["A3_ISI_curve"] = {str(k): Rk[k] for k in K_GRID}
    R["A3_kstar"] = kstar
    R["A3_ties_with_k0"] = ties
    R["A3_verdict"] = verdict
    for k in K_GRID:
        print(f"  k={k}  steps={k+1}  R(k)={Rk[k]:.3f}  "
              + "#" * int(round(Rk[k] * 40)))
    print(f"  => argmax k* = {kstar}   R(0) = {Rk[0]:.3f}   "
          f"R(k*) = {Rk[kstar]:.3f}")
    print(f"  => REGISTERED VERDICT: {verdict}")

    # --- A4: THE NOISE ARMS, with the ANALYTIC EXPECTATION COMPUTED FIRST ---
    #     The predecessor's noise control was NOT a noise control: three uniform
    #     draws are equally spaced ~1/156 of the time, so a "spurious" accept was
    #     the mechanism being CORRECT.  The same trap is present here in a MUCH
    #     larger form, and it is computed in advance rather than discovered.
    print("\n[A4] P6 NOISE: independent random endpoints -- the analytic "
          "expectation is computed BEFORE the arm is read")
    hi = FIELD_W - DOT
    for sd in range(NOISE_LO, NOISE_HI):
        DRAWS[sd] = [int(x) for x in
                     np.random.default_rng(sd).integers(0, hi, size=2)]

    # EXACT analytic expectation over the uniform pair on this grid: accept iff
    # the difference is divisible by `steps` AND non-zero.  A FORMULA, computed
    # from the grid -- not a remembered approximation.
    def analytic(steps: int) -> float:
        diffs = np.subtract.outer(np.arange(hi), np.arange(hi)).ravel()
        return float(np.mean((diffs % steps == 0) & (diffs != 0)))

    noise = {}
    for k in K_GRID:
        sds = list(range(NOISE_LO + 100 * k, NOISE_LO + 100 * (k + 1)))
        acc = sum(1 for sd in sds
                  if run(seq([DRAWS[sd][0]] + [None] * k + [DRAWS[sd][1]]),
                         f"A4-k{k}-{sd}")["abduced"])
        exp = analytic(k + 1)
        noise[k] = {"n": len(sds), "seeds": [sds[0], sds[-1]],
                    "accepted": acc, "rate": acc / len(sds),
                    "analytic_expected_rate": round(exp, 4),
                    "analytic_expected_count": round(exp * len(sds), 1)}
        print(f"  k={k} steps={k+1}: accepted {acc:3d}/100 (rate "
              f"{acc/len(sds):.3f})   ANALYTIC EXPECTATION {exp:.3f} "
              f"({exp*len(sds):.1f}/100)")

    # The genuinely-null arm: endpoints that are NOT rigid translates (a dot of
    # a DIFFERENT SIZE).  DECLARED FORCED in advance -- the cardinality check
    # refuses at source, so it carries no evidential weight; it is run to
    # confirm the source reading on the REAL ENGINE.
    nt_seeds = list(range(NOISE_LO + 800, NOISE_LO + 900))
    nt_acc = sum(1 for sd in nt_seeds
                 if run([cells_fig(render(DRAWS[sd][0], DOT)), [],
                         cells_fig(render(DRAWS[sd][1], DOT + 1))],
                        f"A4NT-{sd}")["abduced"])
    ok["A4_P6_nontranslate_null"] = v_a4_p6_null(nt_acc)
    R["A4_noise"] = {str(k): v for k, v in noise.items()}
    R["A4_nontranslate"] = {"n": len(nt_seeds),
                            "seeds": [nt_seeds[0], nt_seeds[-1]],
                            "accepted": nt_acc,
                            "forced": True,
                            "note": ("DECLARED FORCED (PROTOCOL 13.1): "
                                     "infer_translate_offset refuses unequal "
                                     "cardinality at source. No evidential "
                                     "weight; run to confirm the source "
                                     "reading against the real engine.")}
    print(f"  NON-TRANSLATE (different dot size, FORCED null): "
          f"{nt_acc}/100 accepted  PASS={ok['A4_P6_nontranslate_null']}")

    # --- the trap gate: the in-process CODEBOOK-LIVENESS probe --------------
    ok["A0_coord"] = v_a0_coord(COORD_VIOLATIONS)
    R["A0_coord_violations"] = COORD_VIOLATIONS
    print(f"\n[A0-COORD] in-process codebook probe empty on "
          f"{len(COORD_VIOLATIONS)} call(s): PASS={ok['A0_coord']}")

    R["ok"] = ok
    json.dump(R, open("results/gapabduce_measure.json", "w"), indent=1)
    print("\n=== SUMMARY ===")
    for k2, v in ok.items():
        print(f"  {k2:28s} {v}")
    print(f"  {'ISI VERDICT':28s} {verdict}")
    print("\nwrote results/gapabduce_measure.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
