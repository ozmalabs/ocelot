"""colour_bound_world — a world adapter for COLOUR IDENTITY'S REFUSAL BOUND
(VISION_COLOUR_BOUND_PREREG.md).

Mechanical I/O ONLY (CLAUDE.md / PROTOCOL §0). It composes the committed
`colour_identity_world` adapter (scene/region construction and readback are
UNCHANGED and re-used verbatim, so the stimuli are the landed rung's own) and adds
exactly two things, both mechanical:

  * `set_flags` — a BLIND WRITE of the `bound` flag (and the pre-existing `identity`
    / `achromatopsia` flags) onto every ColourIdentityParams node. No read, no
    branch, no default-picking.
  * `refusals` / `refused_dists` — RAW readback of the `ci_refused` /
    `ci_refused_dist` attributes the `ci_refuse` RULE writes.

It makes NO percept decision. Whether an observation is admitted or refused is
decided ENTIRELY by the seed rules `ci_assign` / `ci_refuse` via the packing-radius
bound; this file never computes a distance, never compares one to a bound, and never
inspects a category. There is no `if` anywhere in it — the module is AST-scanned by
`tests/test_colour_bound_migrated.py::test_no_python_decision_in_the_adapter`, which
rejects any `If`/`IfExp`/`Compare`/`BoolOp` node.

The runner (`scripts/colour_bound_measure.py`) computes the packing-radius predicate
INDEPENDENTLY, in Python, for arm BOUNDARY_EXACT — that is a MEASUREMENT of the
graph's decision, deliberately kept out of this adapter and out of the agent's path.
"""
from __future__ import annotations

from domains import colour_identity_world as ciw

# Scene construction + readback are the LANDED rung's own, re-used verbatim so that
# every stimulus in this rung is byte-for-byte the stimulus colour identity measured.
add_field = ciw.add_field
add_region = ciw.add_region
tick = ciw.tick
n_categories = ciw.n_categories
categories = ciw.categories
cell_attr = ciw.cell_attr
region_attr = ciw.region_attr
read_attr = ciw.read_attr
signs = ciw.signs
scene_epoch = ciw.scene_epoch


def set_flags(s, *, identity: float = 0.0, achromatopsia: float = 0.0,
              bound: float = 0.0) -> None:
    """Blind-write all three flags on every ColourIdentityParams node.

    No read, no branch. `bound` is the refusal bound added by this rung; it ships at
    0.0 (OFF) in the seed and every caller that does not name it gets the committed
    behaviour (§9).
    """
    for p in s.nodes("ColourIdentityParams"):
        s.set_attr(p, "identity", float(identity))
        s.set_attr(p, "achromatopsia", float(achromatopsia))
        s.set_attr(p, "bound", float(bound))


# --- readouts (pure mechanical queries, no decision) ---------------------------
def refusals(s, handle: dict) -> list[float]:
    """Per-cell `ci_refused` (1.0 iff the ci_refuse RULE fired), in cell order."""
    return [float(s.node(n)["attrs"].get("ci_refused", 0.0))
            for n in handle["region_ids"]]


def refused_dists(s, handle: dict) -> list[float]:
    """Per-cell `ci_refused_dist` (the residual to the rejected nearest quantum)."""
    return [float(s.node(n)["attrs"].get("ci_refused_dist", -1.0))
            for n in handle["region_ids"]]


def probe_readout(s, nid: int) -> dict:
    """Every attribute this rung reads off ONE probe region. Raw values only."""
    a = s.node(nid)["attrs"]
    return {
        "crg": float(a.get("crg", 0.0)),
        "cby": float(a.get("cby", 0.0)),
        "sign_rg": float(a.get("sign_rg", 0.0)),
        "sign_by": float(a.get("sign_by", 0.0)),
        "sign_dist": float(a.get("sign_dist", -1.0)),
        "ci_refused": float(a.get("ci_refused", 0.0)),
        "ci_refused_dist": float(a.get("ci_refused_dist", -1.0)),
        "assigned_epoch": float(a.get("assigned_epoch", -1.0)),
    }
