"""bigville_can_integration_demo -- the live two-resident CAN-belief-network
demonstration for BIGVILLE_CAN_INTEGRATION_PREREG.md sec6.

Picks the two REAL bigville_cast100.json residents with the lowest and
highest ``resolution_bins`` trait (mechanical, tie-broken by index -- fixed
before the population is drawn), builds each an independent, individually-
parameterized CAN belief network (``worlds.bigville_can_beliefs``), applies
the SAME scenario evidence to both, relaxes + audits each with the real
``can_ops`` PyO3 surface, and runs a small multi-start sweep to read off a
basin count. Prints a JSON result block to stdout (redirected to a results
file by the caller) -- WORLD-ADAPTER / MEASUREMENT script only, no agent
decision logic: every branch here is fixed analysis code operating on
already-computed numbers, not a rule engine over live agent graph state.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate_rs import _native                                    # noqa: E402
from worlds.bigville_can_beliefs import (                           # noqa: E402
    install_productions, build_resident_can_mt, apply_scenario_evidence,
    TOPIC_NAMES,
)

RES_GAIN = 1.0
BETA = 1.5
N_RESTARTS = 20
CLUSTER_TOL = 0.3


def pick_demo_residents(cast: list) -> tuple:
    lo = min(cast, key=lambda r: (r["params"]["resolution_bins"], r["index"]))
    hi = max(cast, key=lambda r: (r["params"]["resolution_bins"], -r["index"]))
    return lo, hi


def multi_start_basin_count(s, mt, concept_ids, rng, n=N_RESTARTS, tol=CLUSTER_TOL):
    """Reseed each Concept's `state` to an i.i.d. {-1,+1} choice, relax, and
    cluster the converged marginals (L2 < tol merges) -- the exact
    multi-start protocol CAN_BELIEF_QUANTIZATION_PREREG.md sec2.2
    registered. mt_mean_field_marginal is a pure read (can_ops.rs's own doc
    comment), so repeated calls after re-seeding state are safe."""
    clusters = []  # list of vectors (in concept_ids order)
    frustrations = []
    energies = []
    for _ in range(n):
        for cid in concept_ids:
            s.set_attr(cid, "state", float(rng.choice([-1.0, 1.0])))
        marg = s.mt_mean_field_marginal(mt)
        vec = np.array([round(marg.get(cid.value, 0.0), 1) for cid in concept_ids])
        frustrations.append(s.mt_frustration_given_state(mt, marg))
        energies.append(s.mt_energy(mt, marg))
        matched = False
        for c in clusters:
            if np.linalg.norm(vec - c) < tol:
                matched = True
                break
        if not matched:
            clusters.append(vec)
    return {
        "basin_count": len(clusters),
        "mean_frustration": float(np.mean(frustrations)),
        "mean_energy": float(np.mean(energies)),
    }


def run_one(s, resident, res_gain=RES_GAIN, beta=BETA):
    built = build_resident_can_mt(s, resident, res_gain=res_gain, beta=beta)
    apply_scenario_evidence(s, built["concepts"])
    s.mt_relax_to_marginal(built["mt_node"])
    audit = s.mt_audit_basin(built["mt_node"])
    concept_ids = [built["concepts"][t] for t in TOPIC_NAMES]
    rng = np.random.default_rng(resident["index"] + 90000)
    sweep = multi_start_basin_count(s, built["mt_node"], concept_ids, rng)
    rounding_err = float(np.mean([abs(e["true_j"] - e["quantized_j"]) for e in built["edges"]]))
    return {
        "resident": {
            "index": resident["index"], "name": resident["name"],
            "role": resident["role"],
            "resolution_bins": resident["params"]["resolution_bins"],
            "arousal": resident["params"]["arousal"],
        },
        "effective_bins": built["effective_bins"],
        "edges": built["edges"],
        "mean_abs_rounding_error": rounding_err,
        "single_relax_audit": {
            "concept_count": audit["concept_count"],
            "coupling_count": audit["coupling_count"],
            "energy": audit["energy"],
            "coverage": audit["coverage"],
            "frustration": audit["frustration"],
            "marginal": {t: round(audit["marginal"].get(built["concepts"][t].value, 0.0), 4)
                         for t in TOPIC_NAMES},
        },
        "multi_start_sweep": sweep,
    }


def main():
    cast_path = os.path.join(_ROOT, "seeds", "bigville_cast100.json")
    cast = json.load(open(cast_path))["residents"]
    lo, hi = pick_demo_residents(cast)

    s = _native.Substrate()
    install_productions(s)

    result = {
        "res_gain_demo_choice": RES_GAIN, "beta": BETA, "n_restarts": N_RESTARTS,
        "low_resolution": run_one(s, lo),
        "high_resolution": run_one(s, hi),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
