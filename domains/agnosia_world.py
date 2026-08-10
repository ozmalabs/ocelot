"""agnosia_world — the APPERCEPTIVE / ASSOCIATIVE AGNOSIA world adapter (T9).

ARCHITECTURE (CLAUDE.md / PROTOCOL section 0). A WORLD ADAPTER and nothing else.
It does exactly the mechanical things a world adapter may:

  1. WRITE THE LESION FLAGS — blind float writes onto the `AgnosiaParams` node
     that `seeds/vision_agnosia.json` ships. This function does not read, branch
     on, or interpret any flag; the RULES that read them are the ones they
     lesion (`sd_recognize*` for `associative`, `gr_fill` for `apperceptive`).
  2. READ THE PERCEPT — the rendered form as a cell set, an exact-value read of
     the `gbel` field the `vision_ground` RULES produced (the binary/step class
     the render is bounded to; the idiom of `scripts/illusion_measure.py`). A
     pure query.
  3. HAND THE PERCEPT TO THE CONCEPT LAYER — mint ONE `Observation` whose
     `signature` is the percept's (origin-normalised) cell set and let
     `run_rules` decide. Mechanical translation of a graph read into a graph
     write, exactly as `scripts/identity_untangling_measure.py` does; the
     IDENTITY decision is entirely the `sd_*` rules'.
  4. READ THE NAME BACK — `Observation.covered_by` when the loop reached a
     recognition state. A pure query.

NO DECISIONS. There is no `if associative`, no `if apperceptive` in this file:
both ablations are FLAGS on a params node, read by the guarded rules. A
source-grep gate in `tests/test_agnosia_migrated.py` enforces it.
"""
from __future__ import annotations

import json
from typing import Any, Iterable, Optional

import numpy as np

# The dimension types of a cell-set signature: predicate + two integer
# coordinates + a value slot (the sd loop's own format, unchanged).
DIM_TYPES = ["pred", "coord:r", "coord:c", "val"]

# A recognition state is one the sd loop's own recognition rules write.
RECOGNIZED = ("recognized", "recognized_transformed")


# --------------------------------------------------------------------------- #
#  1. THE LESION FLAGS
# --------------------------------------------------------------------------- #
def set_agnosia_params(substrate, **kw: float) -> None:
    """Blind-write floats onto every `AgnosiaParams` node. Mechanical: this
    function does not read, branch on, or interpret any flag — the RULES do."""
    for p in substrate.nodes("AgnosiaParams"):
        for k, v in kw.items():
            substrate.set_attr(p, k, float(v))


# --------------------------------------------------------------------------- #
#  2. THE PERCEPT (COPY) — a pure query over the rendered field
# --------------------------------------------------------------------------- #
def normalise(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    """Origin-normalise a cell set (translation is not identity). Mechanical."""
    cs = list(cells)
    if not cs:
        return []
    mr = min(r for r, _ in cs)
    mc = min(c for _, c in cs)
    return sorted((r - mr, c - mc) for r, c in cs)


def signature(cells: Iterable[tuple[int, int]]) -> list[list[Any]]:
    """The sd loop's cell-set signature form. Mechanical translation."""
    return [["cell", r, c, "red"] for r, c in normalise(cells)]


def percept_cells(belief: np.ndarray) -> list[tuple[int, int]]:
    """The rendered percept as a cell set: the cells the field HOLDS as present.

    An EXACT-VALUE read (`|gbel - 1| <= 1e-6`) on the binary/step field the
    render is bounded to — the same read `scripts/illusion_measure.py` uses, not
    a tuned threshold. Pure query.
    """
    h, w = belief.shape
    return sorted((r, c) for r in range(h) for c in range(w)
                  if abs(float(belief[r, c]) - 1.0) <= 1e-6)


def copy_error(percept: Iterable[tuple[int, int]],
               truth: Iterable[tuple[int, int]]) -> int:
    """The COPY statistic: |percept symmetric-difference truth| in retinal
    coordinates. 0 == the form was reconstructed exactly. Measurement."""
    return len(set(percept) ^ set(truth))


# --------------------------------------------------------------------------- #
#  3 + 4. THE PERCEPT -> CONCEPT HANDOFF, AND THE NAME
# --------------------------------------------------------------------------- #
def install_codebook(substrate, objects: dict[str, list[tuple[int, int]]]) -> None:
    """Hold each object's TRUE form as a `ShapeSignature`, having first removed
    the pre-seeded symbolic signatures so only these are candidate identities
    (the isolation `identity_untangling_measure.py` uses). Mechanical setup."""
    for n in list(substrate.nodes("ShapeSignature")):
        substrate.remove_node(n)
    for name, cells in objects.items():
        substrate.add_node("ShapeSignature",
                           {"name": name, "signature": json.dumps(signature(cells)),
                            "kind": "faculty", "faculty": name, "dim_types": DIM_TYPES})


def name_percept(substrate, native, agent, cells: Iterable[tuple[int, int]]) -> dict:
    """Hand ONE percept to the concept layer and read back what it decided.

    Mints the `Observation` (mechanical write), runs the rules (the sd loop
    decides), reads `status`/`covered_by` (pure query). No branch here chooses
    an identity — `covered_by` is written only by the three `sd_recognize*`
    rules, which is exactly what the `associative` flag lesions.
    """
    cells = list(cells)
    if not cells:
        return {"status": "empty_percept", "covered_by": None}
    sig = signature(cells)
    epoch = substrate.node(agent)["attrs"].get("codebook_epoch") or 0.0
    obs = substrate.add_node("Observation",
                            {"signature": sig, "key": ["probe"], "status": "decoded",
                             "residual": sig, "decoded_epoch": epoch,
                             "dim_types": DIM_TYPES})
    substrate.add_edge(agent, "observed", obs)
    native.run_rules()
    attrs = substrate.node(obs)["attrs"]
    status = attrs.get("status")
    residual = attrs.get("residual")
    return {"status": status,
            "covered_by": attrs.get("covered_by") if status in RECOGNIZED else None,
            # §1.1 alive-controls on the CONCEPT layer, read straight off the sd
            # loop's own bookkeeping. `*_checked` == the decode/transform/dimension
            # machinery RAN; `dim_explained` == the held codebook EXPLAINED this
            # percept. Under the `associative` lesion both must still hold (the
            # percept reached the concept layer and was explained; only the
            # identity ASSIGNMENT is suppressed); under the `apperceptive` lesion
            # the machinery runs but CANNOT explain the broken form. Pure queries.
            "transform_checked": attrs.get("transform_checked"),
            "transform_explained": attrs.get("transform_explained"),
            "dim_checked": attrs.get("dim_checked"),
            "dim_explained": attrs.get("dim_explained"),
            # REPORTED, NOT USED IN ANY DECISION: `residual` is the value the
            # adapter seeded at mint time and the loop never rewrites it (it is
            # IDENTICAL in the intact and lesioned arms — a DEAD INSTRUMENT in
            # the §1.1 sense). Kept visible so the results can say so honestly.
            "residual_len": (len(residual) if residual is not None else None)}


__all__ = ["DIM_TYPES", "RECOGNIZED", "set_agnosia_params", "normalise", "signature",
           "percept_cells", "copy_error", "install_codebook", "name_percept"]
