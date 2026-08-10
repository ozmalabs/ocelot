#!/usr/bin/env python3
"""DOES `TimeInfer` ON >=3 FRAMES RECOVER THE CORRESPONDENCE TWO FRAMES CANNOT?

The confirmatory measurement for `VISION_TIMEPHI_PREREG.md` (committed
ddcf65958e90 before any number). Successor to the phi rung (86000-86999).

Every arm is DETERMINISTIC except the NOISE control, whose random dot positions
draw from seeds 93000-93399 (declared; all resolved by scripts/seed_audit.py). Run from the gamma-substrate dir:

    PYTHONPATH=runners/dsl/python:. python scripts/timephi_measure.py

VERDICTS come from the AGENT'S OWN RULE (the `time_axis` / `blink_bridge` seed
writes `status`); the direct Term evaluations are DIAGNOSTIC ONLY (coord_dims,
checked) and exist to catch the phi rung's silent-refusal trap.
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
EXPECT_ENGINE = "a1d350bbd23b"

# --- stimulus configuration (PROTOCOL 13: declared residuals, inherited from
# the phi rung; construction only, never a verdict threshold) -----------------
DOT = 4              # phi rung's DOT = BLOCK
FIELD_H = 24
FIELD_W = 160        # wide enough that S=32 at N=5 stays on the lattice
RAW_N = 24           # the R-FIELD arm's square field (its verdict is width-free)
BG = 0
FG = 255
ROW = 8
DT = ["pred", "coord:r", "coord:c", "val"]

# --- the INDEPENDENT VARIABLES: iterated, never compared against -------------
S_GRID = [1, 2, 4, 6, 8, 12, 16, 20, 32]
K_GRID = [0, 1, 2, 3, 4]
P_GRID = [1, 2, 3, 4]
ISI_S = [4, 16]
# The NOISE control's ONLY randomness.  Every draw is materialised HERE, from a
# single sink bound to an explicit `range`, so `scripts/seed_audit.py` can
# RESOLVE every seed statically instead of reporting an unknown sink.  (The phi
# rung's precedent: a `--check` that passes while leaving sinks UNKNOWN has
# verified nothing, so the code is shaped to let the audit tell the truth.)
NOISE_LO = 93000
NOISE_HI = 93400
DRAWS: dict[int, list[int]] = {}

# The CODEBOOK-LIVENESS probe: a known orbit evaluated in the SAME booted
# substrate as every measured condition.  See `_codebook_live`.
PROBE_COLS = (0, 4, 8)
COORD_VIOLATIONS: list[str] = []
# Recorded, NOT gated on: the raw `coord_dims` an UNEXPLAINED result reports.
# `eval_time_infer`'s `unexplained()` constructor hardcodes it to `()`, so it is
# an OUTPUT of the verdict and cannot diagnose the codebook (PROTOCOL 1.1).
OUT_COORD_EMPTY: list[str] = []


# --------------------------------------------------------------------------- #
#  world: PIXELS.  The adapter renders a frame and converts it to cells by an
#  EXACT comparison against the frame's OWN modal luminance -- data-derived,
#  no constant.  (PROTOCOL 0: the adapter translates; it decides nothing.)
# --------------------------------------------------------------------------- #
def render(col: int | None, h: int = FIELD_H, w: int = FIELD_W) -> np.ndarray:
    """A uniform field carrying one hard-edged DOTxDOT dot at column `col`.
    `col is None` renders the blank field."""
    f = np.full((h, w), BG, dtype=np.uint8)
    if col is not None:
        f[ROW:ROW + DOT, col:col + DOT] = FG
    return f


def cells_fig(frame: np.ndarray) -> list[list]:
    """FIGURE cells: those whose luminance differs from the frame's own modal
    luminance.  A figure/ground split -- SUPPLIED STRUCTURE, declared as such."""
    vals, counts = np.unique(frame, return_counts=True)
    modal = int(vals[int(np.argmax(counts))])
    rs, cs = np.nonzero(frame != modal)
    return [["px", int(r), int(c), int(frame[r, c])] for r, c in zip(rs, cs)]


def cells_field(frame: np.ndarray) -> list[list]:
    """EVERY pixel of the bounded field.  No segmentation whatsoever."""
    h, w = frame.shape
    return [["px", r, c, int(frame[r, c])]
            for r in range(h) for c in range(w)]


def cells_bg(frame: np.ndarray) -> list[list]:
    """The frame's BACKGROUND cells (every cell at the modal luminance) -- the
    BLANK-BG encoding of a blank frame: non-empty, and a different cardinality
    from a figure frame."""
    vals, counts = np.unique(frame, return_counts=True)
    modal = int(vals[int(np.argmax(counts))])
    rs, cs = np.nonzero(frame == modal)
    return [["px", int(r), int(c), int(frame[r, c])] for r, c in zip(rs, cs)]


def seq_fig(cols) -> list[list[list]]:
    """A frame sequence in the FIGURE representation; `None` -> EMPTY frame."""
    return [([] if c is None else cells_fig(render(c))) for c in cols]


# --------------------------------------------------------------------------- #
#  substrate: the AGENT decides.  We present an Observation and read `status`.
# --------------------------------------------------------------------------- #
def _boot(seed_id: str, flag: str):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    if seed_id == "blink_bridge":
        native.load_seed_manifest(manifest_for("blink_bridge"), ag)
    s.set_attr(ag, flag, 1.0)
    s.add_node("ShapeSignature",
               {"name": "px_base", "signature": json.dumps(cells_fig(render(0))),
                "kind": "faculty", "faculty": "px_base", "dim_types": DT})
    return s, ag, native


def _codebook_live(s, term_name: str, tag: str) -> tuple:
    """THE TRAP GATE, DONE RIGHT.  Evaluate `term_name` on a KNOWN ORBIT in the
    SAME booted substrate as the measured condition and read its `coord_dims`.

    An UNEXPLAINED verdict reports `coord_dims == ()` whatever the cause -- the
    `unexplained()` constructor hardcodes it -- so reading it off the MEASURED
    call cannot tell "the codebook did not load" from "there is no orbit"
    (PROTOCOL 1.1: an absence off a guarded path is evidence of a LOOKUP, not a
    measurement).  A positive probe in the same process CAN: if the codebook were
    absent, the probe would be empty too."""
    probe = [cells_fig(render(c)) for c in PROBE_COLS]
    t = srs.Term(term_name, sequence=srs.Lit(probe),
                 codebook_type="ShapeSignature", max_b=8, field="coord_dims")
    cd = tuple(s.evaluate(t, {}) or ())
    if len(cd) == 0:
        COORD_VIOLATIONS.append(tag)
    return cd


def time_run(frames, tag: str) -> dict:
    """Present a motion sequence; the `time_axis` RULE decides.  The direct Term
    reads are DIAGNOSTIC (PROTOCOL 10.2 rule 1: positive-control the WIRING)."""
    s, ag, native = _boot("time_axis", "time_infer_enabled")
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                                   "status": "motion_seq", "key": ["timephi"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]

    def term(field):
        t = srs.Term("TimeInfer", sequence=srs.Lit(frames),
                     codebook_type="ShapeSignature", max_b=8, field=field)
        return s.evaluate(t, {})

    coord_dims = tuple(term("coord_dims") or ())
    if len(coord_dims) == 0:
        OUT_COORD_EMPTY.append(tag)
    probe_cd = _codebook_live(s, "TimeInfer", tag)
    return {"probe_coord_dims": probe_cd,
            "status": at.get("status"),
            "explained": at.get("status") == "time_inferred",
            "kind": at.get("time_kind"),
            "offset": tuple(term("offset") or ()),
            "checked": term("checked"),
            "coord_dims": coord_dims}


def blink_run(frames, tag: str) -> dict:
    s, ag, native = _boot("blink_bridge", "blink_bridge_enabled")
    s.set_attr(ag, "time_infer_enabled", 1.0)
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                                   "status": "blink_seq", "key": ["timephi"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]

    def term(field):
        t = srs.Term("BlinkBridge", sequence=srs.Lit(frames),
                     codebook_type="ShapeSignature", max_b=8, field=field)
        return s.evaluate(t, {})

    coord_dims = tuple(term("coord_dims") or ())
    if len(coord_dims) == 0:
        OUT_COORD_EMPTY.append(tag)
    probe_cd = _codebook_live(s, "BlinkBridge", tag)
    return {"probe_coord_dims": probe_cd,
            "constrained": bool(at.get("constrained")),
            "kind": at.get("bridge_kind"),
            "confidence": at.get("confidence"),
            "gap": at.get("bridge_gap"),
            "confirm": at.get("bridge_confirm"),
            "prefix": at.get("bridge_prefix"),
            "diverged_at": at.get("diverged_at"),
            "correction": at.get("correction"),
            "offset": tuple(term("offset") or ()),
            "bridged": at.get("bridged"),
            "coord_dims": coord_dims}


# ======================= THE VERDICTS (PROTOCOL 13) ======================== #
#  Every verdict below decides by EXACT EQUALITY on a logical or integer
#  quantity.  No ordering comparison against a tuned constant decides anything.
#  `tests/test_timephi_ast_migrated.py` binds these functions BY NAME as AST
#  FunctionDef nodes -- never by substring -- and asserts exactly that.
# =========================================================================== #
VERDICTS = ("v_a0_pos", "v_a0_neg", "v_a1_p0", "v_a2_p1", "v_a3_p2", "v_a4_p3",
            "v_a4n_corrected", "v_a4n_accepts_are_orbits", "v_a5_p4",
            "v_a6a_p5", "v_a6b_p6", "v_a6b_boundary", "v_a0_coord")


def v_a0_pos(pos) -> bool:
    """A0-POS: a known moving dot IS an orbit, with the TRUE offset."""
    return (pos["explained"] and pos["kind"] == "translate"
            and pos["offset"] == (0, 4))


def v_a0_neg(neg) -> bool:
    """A0-NEG: a STILL dot is refused (identity is excluded at source)."""
    return neg["status"] == "time_none"


def v_a1_p0(a1) -> bool:
    """P0: a bounded RAW PIXEL FIELD is not explained."""
    return not a1["explained"]


def v_a2_p1(a2) -> bool:
    """P1: N=2 is explained at EVERY separation -- the vacuity claim."""
    return all(a2[S]["explained"] for S in S_GRID)


def v_a3_p2(a3) -> bool:
    """P2 (H1): N>=3 is explained at EVERY separation, with the TRUE offset --
    no cutoff, i.e. NO PIXEL APERTURE."""
    return all(a3[N][S]["explained"] and a3[N][S]["offset"] == (0, S)
               for N in a3 for S in S_GRID)


def v_a4_p3(a4) -> bool:
    """P3: non-orbits (accelerating / shuffled) are refused everywhere."""
    return all(not a4[S][w]["explained"]
               for S in S_GRID for w in ("accel", "shuffle"))


def v_a4n_corrected(n_accepted) -> bool:
    """The NOISE floor on draws that are genuinely NOT orbits."""
    return n_accepted == 0


def v_a4n_accepts_are_orbits(accepted_are_orbits) -> bool:
    """Whatever the as-registered noise arm ACCEPTED must be a REAL orbit."""
    return accepted_are_orbits


def v_a5_p4(a5) -> bool:
    """P4: explained at zero ISI, refused at every ISI >= 1.  (Its evidential
    weight was declared ZERO in advance -- both nulls are forced by source
    guards; PROTOCOL 13.1 third category.)"""
    return all((v["explained"] if tag.endswith("-k0") else not v["explained"])
               for tag, v in a5.items())


def v_a6a_p5(a6) -> bool:
    """P5: the PHI TOPOLOGY (one pre-gap sample) FREEZES -- unconstrained, zero
    confidence, and a divergence on resume whose magnitude is the dot's cells
    counted twice (absent from A, present at B)."""
    return all((not v["constrained"]) and v["kind"] == "freeze"
               and float(v["confidence"]) == 0.0
               and int(v["diverged_at"]) >= 0
               and int(v["correction"]) == 2 * DOT * DOT
               for t, v in a6.items() if "-P1-" in t)


def v_a6b_p6(a6) -> bool:
    """P6: an ESTABLISHED orbit (>=2 pre-gap samples) bridges the SAME gap, with
    the TRUE offset."""
    return all(v["constrained"] and v["kind"] == "translate"
               and v["offset"] == (0, int(t.split("-S")[1].split("-")[0]))
               for t, v in a6.items() if "-P1-" not in t)


def v_a6b_boundary(a6) -> bool:
    """P6's PROVISO: the registered prediction that the bridge has a HORIZON --
    that it confirms on resume IFF the gap is within the confirming support.
    (This is the proviso that BROKE; the term.rs doc it was read from describes
    a superseded design.)"""
    return all((int(v["diverged_at"]) == -1 and int(v["correction"]) == 0)
               == (int(v["gap"]) <= int(v["confirm"]))
               for t, v in a6.items() if "-P1-" not in t)


def v_a0_coord(violations) -> bool:
    """The in-process CODEBOOK-LIVENESS probe fired on no call."""
    return len(violations) == 0


# ============================ THE ARMS ===================================== #
def main() -> int:
    R: dict = {"engine": provenance_line(), "prereg": "VISION_TIMEPHI_PREREG.md",
               "prereg_commit": "ddcf65958e90420ad03530b621bf7afc4e31d1a9"}
    print("ENGINE (from INSIDE the measuring process):", R["engine"])
    if EXPECT_ENGINE not in R["engine"]:
        print(f"ABORT: engine divergence -- expected {EXPECT_ENGINE}")
        return 2
    ok: dict = {}

    # --- A0: WIRING CONTROL.  RUN FIRST.  Nothing else is interpreted if it
    #     fails.  (The phi rung's near-miss: a mechanism whose output is "no
    #     correspondence" is indistinguishable from one that cannot express it.)
    print("\n[A0] WIRING CONTROL -- before any hypothesis arm")
    pos = time_run(seq_fig([0, 4, 8]), "A0-POS")
    neg = time_run(seq_fig([0, 0, 0]), "A0-NEG")
    ok["A0_pos"] = v_a0_pos(pos)
    ok["A0_neg"] = v_a0_neg(neg)
    R["A0"] = {"pos": pos, "neg": neg}
    print(f"  A0-POS  moving dot  -> {pos['status']} kind={pos['kind']} "
          f"offset={pos['offset']}  PASS={ok['A0_pos']}")
    print(f"  A0-NEG  still dot   -> {neg['status']}  PASS={ok['A0_neg']}")
    if not (ok["A0_pos"] and ok["A0_neg"]):
        print("  ABORT: wiring control failed; no arm is interpretable.")
        R["ABORT"] = "A0 wiring control failed"
        json.dump(R, open("results/timephi_measure.json", "w"), indent=1)
        return 3

    # --- A1: R-FIELD -- can the Term consume a BOUNDED PIXEL FIELD at all? ---
    print("\n[A1] R-FIELD: every pixel of a bounded field, NO segmentation")
    raw = [cells_field(render(c, RAW_N, RAW_N)) for c in (0, 4, 8)]
    a1 = time_run(raw, "A1-RFIELD")
    ok["A1_P0"] = v_a1_p0(a1)
    R["A1"] = {"cells_per_frame": len(raw[0]), **a1}
    print(f"  {len(raw[0])} cells/frame -> {a1['status']} checked={a1['checked']}"
          f"  P0(unexplained)={ok['A1_P0']}")

    # --- A2: VACUITY, MEASURED (N=2) -----------------------------------------
    print("\n[A2] VACUITY: N=2, every S -- predicted TRUE at all 9 (group-closed)")
    a2 = {}
    for S in S_GRID:
        r = time_run(seq_fig([0, S]), f"A2-S{S}")
        a2[S] = r
        print(f"  S={S:3d} -> {r['status']:14s} offset={r['offset']}")
    ok["A2_P1"] = v_a2_p1(a2)
    R["A2"] = {str(k): v for k, v in a2.items()}
    print(f"  => explained at all {len(S_GRID)} S: {ok['A2_P1']}")

    # --- A3: APERTURE-FREENESS at N>=3 (H1) ----------------------------------
    print("\n[A3] N in {3,5}, constant velocity, every S -- H1: NO cutoff")
    a3 = {}
    for N in (3, 5):
        row = {}
        for S in S_GRID:
            r = time_run(seq_fig([i * S for i in range(N)]), f"A3-N{N}-S{S}")
            row[S] = r
            print(f"  N={N} S={S:3d} -> {r['status']:14s} offset={r['offset']}")
        a3[N] = row
    ok["A3_P2"] = v_a3_p2(a3)
    R["A3"] = {str(N): {str(S): v for S, v in row.items()}
               for N, row in a3.items()}
    maxS = {N: max([S for S in S_GRID if a3[N][S]["explained"]], default=None)
            for N in (3, 5)}
    R["A3_max_S_with_correspondence"] = {str(k): v for k, v in maxS.items()}
    print(f"  => max S with correspondence: {maxS}  (S_GRID tops out at "
          f"{max(S_GRID)})   P2={ok['A3_P2']}")

    # --- A4: DISCRIMINATION -- what makes A3 non-vacuous ---------------------
    print("\n[A4] DISCRIMINATION: ACCEL and SHUFFLE must be REFUSED")
    a4 = {}
    for S in S_GRID:
        acc = time_run(seq_fig([0, S, 3 * S]), f"A4-ACC-S{S}")
        shu = time_run(seq_fig([S, 0, 2 * S]), f"A4-SHU-S{S}")
        a4[S] = {"accel": acc, "shuffle": shu}
        print(f"  S={S:3d} accel -> {acc['status']:14s} "
              f"shuffle -> {shu['status']}")
    ok["A4_P3"] = v_a4_p3(a4)
    R["A4"] = {str(k): v for k, v in a4.items()}
    print(f"  => refused in all {2 * len(S_GRID)} conditions: {ok['A4_P3']}")

    # --- A4n: the NOISE control.  BOTH arms reported (PROTOCOL 6/7):
    #     AS-REGISTERED (the first 100 seeds, whatever they draw) and CORRECTED
    #     (seeds whose draw is genuinely NOT an orbit).  The as-registered arm is
    #     CONTAMINATED: three uniform draws are equally spaced with probability
    #     ~1/(FIELD_W-DOT), so a real constant-velocity orbit appears by chance.
    #     Verified BEFORE the arm was touched (PROTOCOL 12.3).
    print("\n[A4n] NOISE control: independent random dot positions -- BOTH arms")
    hi = FIELD_W - DOT
    for sd in range(NOISE_LO, NOISE_HI):
        DRAWS[sd] = [int(x) for x in
                     np.random.default_rng(sd).integers(0, hi, size=3)]

    def is_orbit(cols):
        return cols[1] - cols[0] == cols[2] - cols[1]

    reg_seeds = [s2 for s2 in range(NOISE_LO, NOISE_LO + 100)]
    reg = {s2: time_run(seq_fig(DRAWS[s2]), f"A4n-{s2}")["explained"]
           for s2 in reg_seeds}
    reg_acc = [s2 for s2, v in reg.items() if v]
    reg_acc_are_orbits = all(is_orbit(DRAWS[s2]) for s2 in reg_acc)

    cor_seeds = [s2 for s2 in range(NOISE_LO + 100, NOISE_HI)
                 if not is_orbit(DRAWS[s2])][:100]
    cor = {s2: time_run(seq_fig(DRAWS[s2]), f"A4nC-{s2}")["explained"]
           for s2 in cor_seeds}
    n_cor_acc = sum(1 for v in cor.values() if v)

    ok["A4n_corrected"] = v_a4n_corrected(n_cor_acc)
    ok["A4n_registered_accepts_are_real_orbits"] = \
        v_a4n_accepts_are_orbits(reg_acc_are_orbits)
    R["A4_noise"] = {
        "registered": {"n": len(reg_seeds), "n_accepted": len(reg_acc),
                       "accepted_seeds": reg_acc,
                       "accepted_cols": {str(s2): DRAWS[s2] for s2 in reg_acc},
                       "accepted_are_genuine_orbits": reg_acc_are_orbits,
                       "analytic_expected_orbits": round(len(reg_seeds) / hi, 3)},
        "corrected": {"n": len(cor_seeds), "seed_range": [cor_seeds[0],
                                                          cor_seeds[-1]],
                      "n_accepted": n_cor_acc}}
    print(f"  AS-REGISTERED: {len(reg_acc)} accepted of {len(reg_seeds)}; "
          f"accepted draws {reg_acc} -> cols "
          f"{[DRAWS[s2] for s2 in reg_acc]}; ALL genuine orbits="
          f"{reg_acc_are_orbits}  (analytic expectation "
          f"{len(reg_seeds) / hi:.2f})")
    print(f"  CORRECTED (non-orbit draws only, seeds {cor_seeds[0]}-"
          f"{cor_seeds[-1]}): {n_cor_acc} accepted of {len(cor_seeds)}: "
          f"PASS={ok['A4n_corrected']}")

    # --- A5: THE ISI CURVE.  Evidential weight DECLARED ZERO in advance
    #     (13.1 third category: both nulls are FORCED by source guards).  Run to
    #     confirm the source reading on the real engine, and because `checked`
    #     distinguishes REFUSAL from FAILURE.
    print("\n[A5] ISI CURVE -- FORCED NULL, declared in advance; `checked` is "
          "the informative column")
    a5 = {}
    for enc in ("BLANK-EMPTY", "BLANK-BG"):
        for nf in (2, 3, 5):
            for S in ISI_S:
                for k in K_GRID:
                    cols: list = []
                    for i in range(nf):
                        if i:
                            cols += [None] * k
                        cols.append(i * S)
                    if enc == "BLANK-EMPTY":
                        frames = seq_fig(cols)
                    else:
                        frames = [(cells_bg(render(None)) if c is None
                                   else cells_fig(render(c))) for c in cols]
                    tag = f"A5-{enc}-N{nf}-S{S}-k{k}"
                    a5[tag] = time_run(frames, tag)
    ok["A5_P4"] = v_a5_p4(a5)
    R["A5"] = a5
    for enc in ("BLANK-EMPTY", "BLANK-BG"):
        for nf in (2, 3, 5):
            row = [a5[f"A5-{enc}-N{nf}-S4-k{k}"] for k in K_GRID]
            print(f"  {enc:12s} N={nf} S=4  " + "  ".join(
                f"k={k}:{'Y' if r['explained'] else 'n'}(chk={r['checked']})"
                for k, r in zip(K_GRID, row)))
    print(f"  => P4 (TRUE at k=0, FALSE at every k>=1, {len(a5)} conditions): "
          f"{ok['A5_P4']}")

    # --- A6: THE ARM THAT IS NOT FORCED -- BlinkBridge, prefix length as IV --
    print("\n[A6] BlinkBridge: PREFIX LENGTH is the IV.  P=1 IS the phi topology")
    a6 = {}
    for S in ISI_S:
        for P in P_GRID:
            for k in K_GRID[1:]:
                cols = [i * S for i in range(P)] + [None] * k + [(P + k) * S]
                tag = f"A6-S{S}-P{P}-k{k}"
                a6[tag] = blink_run(seq_fig(cols), tag)
    R["A6"] = a6
    ok["A6a_P5"] = v_a6a_p5(a6)
    ok["A6b_P6"] = v_a6b_p6(a6)
    # the registered BOUNDARY INSIDE the arm: bridging only where k <= confirm
    ok["A6b_boundary"] = v_a6b_boundary(a6)
    for S in ISI_S:
        for P in P_GRID:
            row = [a6[f"A6-S{S}-P{P}-k{k}"] for k in K_GRID[1:]]
            print(f"  S={S:2d} P={P}  " + "  ".join(
                f"k={k}:{r['kind'][:4]},conf={float(r['confidence']):.2f},"
                f"div={r['diverged_at']},corr={r['correction']}"
                for k, r in zip(K_GRID[1:], row)))
    print(f"  => P5 (P=1 freezes, correction={2 * DOT * DOT}): {ok['A6a_P5']}")
    print(f"  => P6 (P>=2 bridges with the right offset): {ok['A6b_P6']}")
    print(f"  => P6 boundary (bridges IFF gap<=confirm): {ok['A6b_boundary']}")

    # --- the trap gate: the in-process CODEBOOK-LIVENESS probe ---------------
    ok["A0_coord"] = v_a0_coord(COORD_VIOLATIONS)
    R["A0_coord_violations"] = COORD_VIOLATIONS
    R["A0_output_coord_empty"] = {
        "n": len(OUT_COORD_EMPTY),
        "note": ("`coord_dims` READ OFF THE MEASURED CALL is empty on exactly "
                 "the UNEXPLAINED conditions -- `unexplained()` hardcodes it. "
                 "It is an OUTPUT of the verdict and CANNOT diagnose the "
                 "codebook. Recorded, NOT gated on."),
        "sample": OUT_COORD_EMPTY[:8]}
    print(f"\n[A0-COORD] in-process codebook probe empty on "
          f"{len(COORD_VIOLATIONS)} call(s): PASS={ok['A0_coord']}")
    print(f"  (for contrast: the MEASURED call's own `coord_dims` is empty on "
          f"{len(OUT_COORD_EMPTY)} calls -- an output of the verdict, "
          f"inert as a codebook check)")

    R["ok"] = ok
    json.dump(R, open("results/timephi_measure.json", "w"), indent=1)
    print("\n=== SUMMARY ===")
    for k, v in ok.items():
        print(f"  {k:16s} {v}")
    print("\nwrote results/timephi_measure.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
