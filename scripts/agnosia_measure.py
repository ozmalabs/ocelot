#!/usr/bin/env python3
"""APPERCEPTIVE / ASSOCIATIVE AGNOSIA (FRONTIER T9) — confirmatory measurement.

Pre-registration: `VISION_AGNOSIA_PREREG.md` (committed BEFORE this run, §3).
Failure-mode gate #1 of `VISION_VENTRAL_GROUNDING.md` — the FORM<->RECOGNITION
seam. The classic double dissociation:

  * ASSOCIATIVE — ablate the IDENTITY layer (`AgnosiaParams.associative` guards
    the three `sd_recognize*` rules, the sole writers of `covered_by`): the
    percept still FORMS (the COPY survives) but is not NAMED.
  * APPERCEPTIVE — ablate percept COMPLETION (`AgnosiaParams.apperceptive`
    guards `gr_fill`): the form cannot be built, so COPY fails and naming
    necessarily fails with it.

Two ablations hitting DIFFERENT stages, with the COPY test discriminating, is
what proves the seam is real rather than one blob.

Both render engines and the whole identity ladder are REUSED UNCHANGED (NO new
Rust). Every confirmatory arm is DETERMINISTIC except the noise FLOOR, which
draws 100 seeds 48000-48099 (declared in the prereg). Run from the
gamma-substrate dir:

    PYTHONPATH=runners/dsl/python:. python scripts/agnosia_measure.py

NO Python decides a percept or an identity: the percept (`gbel`) is produced by
the `vision_ground` RULES, the identity (`covered_by`) by the `shape_decode_loop`
RULES. This runner only CONSTRUCTS stimuli, WRITES FLAGS, and READS percepts and
names back (mechanical I/O, §0), then COMPUTES metrics over them (measurement,
not decision).
"""
from __future__ import annotations

import json
import os
import random
import time

import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains import ground_world as gw  # noqa: E402
from domains import agnosia_world as aw  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

# =========================================================================== #
#  STIMULI — stroke-composed forms on a 20x20 retina
# =========================================================================== #
H = W = 20
OCC_RADIUS = 1.0        # a 5-cell no-data disc; 3 of its cells fall ON the form


def hbar(r, c0, c1):
    return [(r, c) for c in range(c0, c1 + 1)]


def vbar(c, r0, r1):
    return [(r, c) for r in range(r0, r1 + 1)]


OBJ = {
    "T": sorted(set(hbar(3, 4, 14) + vbar(9, 3, 16))),
    "L": sorted(set(vbar(4, 3, 16) + hbar(16, 4, 14))),
    "I": sorted(set(vbar(9, 3, 16))),
    "H": sorted(set(vbar(4, 3, 16) + vbar(14, 3, 16) + hbar(9, 5, 13))),
    "U": sorted(set(vbar(4, 3, 16) + vbar(14, 3, 16) + hbar(16, 5, 13))),
    "E": sorted(set(vbar(4, 3, 16) + hbar(3, 5, 13) + hbar(9, 5, 13) + hbar(16, 5, 13))),
}
# Occluder centres: mid-segment, away from every stroke end and junction.
OCC = {"T": (12, 9), "L": (9, 4), "I": (9, 9), "H": (6, 4), "U": (6, 14), "E": (12, 4)}

NAMES = list(OBJ)
FLOOR_SEEDS = range(48000, 48100)       # the ONLY seeds this rung consumes


# =========================================================================== #
#  ONE GRAPH — render seed + identity seed, both live
# =========================================================================== #
def build(name, *, associative=0.0, apperceptive=0.0, interp=0.0, ground=1.0,
          frame=None, occ=None):
    """Boot ONE substrate carrying BOTH stages, lay out the occluder, write the
    lesion flags, present the stimulus, and let the render rules run."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_ground", "vision_agnosia"])
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    aw.install_codebook(s, OBJ)
    wd = WaveWorld(s, h=H, w=W, seed=0)
    anat = gw.add_grounded_field(wd, blind_center=occ or OCC[name],
                                 blind_radius=OCC_RADIUS)
    gw.set_ground_params(wd, ground=ground, interp=interp)
    aw.set_agnosia_params(s, associative=associative, apperceptive=apperceptive)
    if frame is None:
        frame = np.zeros((H, W))
        for (r, c) in OBJ[name]:
            frame[r, c] = 1.0
    gw.present(wd, anat, frame)
    return dict(s=s, ag=ag, native=native, wd=wd, anat=anat)


def probe(name, **kw):
    """One object through BOTH stages; returns the COPY and NAME readouts."""
    g = build(name, **kw)
    belief = gw.belief_field(g["wd"], g["anat"])
    percept = aw.percept_cells(belief)
    truth = OBJ[name]
    occ_on_form = sorted(set(g["anat"]["blind"]) & set(truth))
    filled = gw.filled(g["wd"], g["anat"])
    named = aw.name_percept(g["s"], g["native"], g["ag"], percept)
    symd = aw.copy_error(percept, truth)
    return dict(
        object=name,
        n_percept=len(percept),
        n_truth=len(truth),
        symdiff=symd,
        copy_ok=bool(symd == 0),
        percept=percept,
        occ_on_form=occ_on_form,
        occ_rendered=sorted(set(occ_on_form) & set(percept)),
        n_filled_occluded=int(sum(1 for (r, c) in g["anat"]["blind"]
                                  if float(filled[r, c]) > 0.5)),
        status=named["status"],
        residual_len=named["residual_len"],
        transform_checked=named["transform_checked"],
        dim_checked=named["dim_checked"],
        dim_explained=bool(named["dim_explained"] is True or named["dim_explained"] == 1),
        covered_by=named["covered_by"],
        name_ok=bool(named["covered_by"] == name),
    )


# =========================================================================== #
#  ARMS
# =========================================================================== #
def arm(tag, **kw):
    rows = [probe(n, **kw) for n in NAMES]
    return dict(
        tag=tag,
        n=len(rows),
        n_copy_ok=sum(r["copy_ok"] for r in rows),
        n_name_ok=sum(r["name_ok"] for r in rows),
        n_named_anything=sum(r["covered_by"] is not None for r in rows),
        n_percept_nonempty=sum(r["n_percept"] > 0 for r in rows),
        symdiffs=[r["symdiff"] for r in rows],
        statuses=sorted({r["status"] for r in rows}),
        residual_lens=[r["residual_len"] for r in rows],
        n_transform_checked=sum(1 for r in rows if r["transform_checked"] == 1),
        n_dim_checked=sum(1 for r in rows if r["dim_checked"] == 1),
        n_dim_explained=sum(1 for r in rows if r["dim_explained"]),
        covered=[r["covered_by"] for r in rows],
        rows=rows,
    )


def floor_arm(tag, **kw):
    """G FLOOR — random binary stimuli must name NOTHING, in every arm."""
    named, empties = 0, 0
    for sd in FLOOR_SEEDS:
        rng = random.Random(sd)
        frame = np.zeros((H, W))
        for r in range(H):
            for c in range(W):
                if rng.random() < 0.25:
                    frame[r, c] = 1.0
        g = build("T", frame=frame, **kw)
        percept = aw.percept_cells(gw.belief_field(g["wd"], g["anat"]))
        if not percept:
            empties += 1
        out = aw.name_percept(g["s"], g["native"], g["ag"], percept)
        if out["covered_by"] is not None:
            named += 1
    return dict(tag=tag, n=len(list(FLOOR_SEEDS)), n_named=named,
                n_empty_percept=empties,
                seeds=[min(FLOOR_SEEDS), max(FLOOR_SEEDS)])


def main():
    t0 = time.time()
    prov = provenance_line()
    print(prov)

    A = arm("A_INTACT")
    B = arm("B_ASSOCIATIVE", associative=1.0)
    C = arm("C_APPERCEPTIVE", apperceptive=1.0)
    C2 = arm("C2_APPERCEPTIVE_INTERP", interp=1.0)

    # D — the DOUBLE DISSOCIATION: two ablations, different stages, COPY discriminates.
    D = dict(
        copy_survives_associative=bool(B["n_copy_ok"] == B["n"]),
        copy_fails_apperceptive=bool(C["n_copy_ok"] == 0),
        naming_fails_both=bool(B["n_named_anything"] == 0 and C["n_named_anything"] == 0),
        naming_intact=bool(A["n_name_ok"] == A["n"]),
        copy_intact=bool(A["n_copy_ok"] == A["n"]),
    )
    D["double_dissociation"] = bool(all(D.values()))

    # E — COPY-ALIVE: the associative copy is a REAL reconstruction, byte-identical to intact.
    per_obj = []
    for a_row, b_row in zip(A["rows"], B["rows"]):
        per_obj.append(dict(
            object=a_row["object"],
            percept_identical=bool(a_row["percept"] == b_row["percept"]),
            n_occ_on_form=len(b_row["occ_on_form"]),
            n_occ_rendered=len(b_row["occ_rendered"]),
            rendered_all_occluded=bool(b_row["occ_rendered"] == b_row["occ_on_form"]),
        ))
    E = dict(rows=per_obj,
             all_percepts_identical=bool(all(r["percept_identical"] for r in per_obj)),
             all_occluded_rendered=bool(all(r["rendered_all_occluded"] for r in per_obj)),
             min_occ_on_form=min(r["n_occ_on_form"] for r in per_obj))
    E["copy_alive"] = bool(E["all_percepts_identical"] and E["all_occluded_rendered"]
                           and E["min_occ_on_form"] > 0)

    # F — LESION-ALIVE, EXACTLY as pre-registered: arm C's percept is non-empty
    # (the render machinery ran; it is the COMPLETION that is destroyed) AND the
    # recognition layer still ran on it (status reaches a terminal sd state).
    F = dict(
        apperceptive_percept_nonempty=bool(C["n_percept_nonempty"] == C["n"]),
        apperceptive_recognition_ran=bool(all(st != "empty_percept" for st in C["statuses"])),
        apperceptive_statuses=C["statuses"],
        apperceptive_symdiffs=C["symdiffs"],
    )
    F["lesions_alive"] = bool(F["apperceptive_percept_nonempty"]
                              and F["apperceptive_recognition_ran"])

    # F2 — NOT PRE-REGISTERED. A characterisation added after the run to diagnose
    # the concept layer's liveness under each lesion, read off the sd loop's own
    # bookkeeping. NO decision rule depends on it. It replaces a first attempt
    # (`residual_len`) that was a DEAD INSTRUMENT: `residual` is the value the
    # adapter seeds at mint time and the loop never rewrites it, so it reads
    # IDENTICALLY (24/24/14/37/37/41) in the INTACT and lesioned arms and could
    # not distinguish anything. Reported in full, including that admission.
    F2 = dict(
        intact=dict(n_transform_checked=A["n_transform_checked"],
                    n_dim_checked=A["n_dim_checked"],
                    n_dim_explained=A["n_dim_explained"]),
        associative=dict(n_transform_checked=B["n_transform_checked"],
                         n_dim_checked=B["n_dim_checked"],
                         n_dim_explained=B["n_dim_explained"]),
        apperceptive=dict(n_transform_checked=C["n_transform_checked"],
                          n_dim_checked=C["n_dim_checked"],
                          n_dim_explained=C["n_dim_explained"]),
        residual_lens_dead_instrument=dict(intact=A["residual_lens"],
                                           associative=B["residual_lens"],
                                           apperceptive=C["residual_lens"]),
    )
    F2["concept_layer_ran_and_explained_under_associative"] = bool(
        B["n_dim_checked"] == B["n"] and B["n_dim_explained"] == B["n"]
        and B["n_dim_explained"] == A["n_dim_explained"])
    F2["concept_layer_ran_but_could_not_explain_under_apperceptive"] = bool(
        C["n_dim_checked"] == C["n"] and C["n_dim_explained"] == 0)

    # G — FLOOR, in every arm.
    G = dict(intact=floor_arm("floor_intact"),
             associative=floor_arm("floor_associative", associative=1.0),
             apperceptive=floor_arm("floor_apperceptive", apperceptive=1.0))
    G["all_zero"] = bool(all(G[k]["n_named"] == 0 for k in ("intact", "associative", "apperceptive")))

    # H — FLAG LOAD-BEARING (§13.2): max|on - off| on each claimed target.
    Hh = dict(
        associative_moves_name=int(abs(A["n_name_ok"] - B["n_name_ok"])),
        associative_moves_copy=int(abs(A["n_copy_ok"] - B["n_copy_ok"])),
        apperceptive_moves_copy=int(abs(A["n_copy_ok"] - C["n_copy_ok"])),
        apperceptive_moves_name=int(abs(A["n_name_ok"] - C["n_name_ok"])),
    )
    Hh["load_bearing"] = bool(Hh["associative_moves_name"] > 0
                              and Hh["associative_moves_copy"] == 0
                              and Hh["apperceptive_moves_copy"] > 0)

    # X — OFF-DAY (§9): both flags at default must reproduce the intact arm.
    X = arm("X_OFFDAY_DEFAULTS")
    X_ok = bool(X["n_copy_ok"] == X["n"] and X["n_name_ok"] == X["n"]
                and [r["percept"] for r in X["rows"]] == [r["percept"] for r in A["rows"]])

    verdict = dict(
        A_intact=bool(A["n_copy_ok"] == A["n"] and A["n_name_ok"] == A["n"]),
        B_associative=bool(B["n_copy_ok"] == B["n"] and B["n_named_anything"] == 0),
        C_apperceptive=bool(C["n_copy_ok"] == 0 and C["n_named_anything"] == 0),
        C2_apperceptive_interp=bool(C2["n_copy_ok"] == 0 and C2["n_named_anything"] == 0),
        D_double_dissociation=D["double_dissociation"],
        E_copy_alive=E["copy_alive"],
        F_lesions_alive=F["lesions_alive"],
        G_floor=G["all_zero"],
        H_load_bearing=Hh["load_bearing"],
        X_offday=X_ok,
    )
    verdict["ALL_PASS"] = bool(all(verdict.values()))

    out = dict(
        rung="AGNOSIA_T9",
        provenance=prov,
        prereg="VISION_AGNOSIA_PREREG.md",
        seeds_consumed=[min(FLOOR_SEEDS), max(FLOOR_SEEDS)],
        objects=NAMES,
        occluder_radius=OCC_RADIUS,
        arms=dict(A_INTACT=A, B_ASSOCIATIVE=B, C_APPERCEPTIVE=C,
                  C2_APPERCEPTIVE_INTERP=C2, X_OFFDAY=X),
        D_double_dissociation=D,
        E_copy_alive=E,
        F_lesions_alive=F,
        F2_concept_layer_characterisation=F2,
        G_floor=G,
        H_load_bearing=Hh,
        verdict=verdict,
        seconds=round(time.time() - t0, 1),
    )
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(here, "results", "agnosia_measure.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    for k, v in verdict.items():
        print(f"  {k:26s} {v}")
    print("wrote", path, f"({out['seconds']}s)")
    return out


if __name__ == "__main__":
    main()
