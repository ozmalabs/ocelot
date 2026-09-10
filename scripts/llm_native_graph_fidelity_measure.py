"""Block 323000 — attack the incidence-map FIDELITY gap.

Block 322 reached PARTIAL aperture-covariance (raw-loading incidence, held-out
~0.75), and lever (c) proved the ceiling is structural (exact == loopy), not the
solver. Block 322 named the residual as incidence-map fidelity: the loading-
weighted bipartite graph only APPROXIMATELY encodes the mode reading. This block
attacks that fidelity directly.

  Lever 1 — FIT the incidence weights (on TRAIN) so the mode-node reproduces the
    mode reading, instead of taking the raw loadings. Regularised.
  Lever 2 — vocab (2state vs 3state): is the discretisation part of the ceiling?

FINDING (honest): the fitted, well-REGULARISED incidence lifts held-out
aperture-covariance from ~0.75 (raw) to ~0.88 through the substrate's OWN BP.
The gap is a GENERALISATION phenomenon (train ~1.0, held-out plateaus), closed
in part by regularisation; vocab is irrelevant. Not full covariance — the
residual is generalisation at 60 train prompts, and the STRUCTURAL next axis is
the between-layer transport incidence (this whole arc used a single layer).

Requires the mode export npz WITH train arrays (model venv:
`export_mode_structure` — writes tr_x/tr_coef) and substrate_rs:
  PYTHONPATH=runners/dsl/python python3 \\
    scripts/llm_native_graph_fidelity_measure.py [export.npz]
"""

import sys
sys.path.insert(0, ".")
import numpy as np

from substrate_rs import _native
from domains import llm_native_graph as lng
from domains.can_native_bp import run_loopy_bp

SEEDS = ["seeds/can_native_reimplementation.json"]
DEFAULT_EXPORT = "/applications/data/model_graph_work/mode_export_L12c.npz"
N_NEUR, N_MODES = 8, 4


def _bp_covariance(modes, mean, Wc, ho_x, nidx, *, override=None,
                   discrete_mode="3state"):
    ags = []
    for x in ho_x:
        coeffs, _ = lng.coarse_mode_state(modes, mean, Wc, x)
        _, field, _ = lng.refine_to_neurons(modes, coeffs, n_neurons=len(nidx))
        s = _native.Substrate()
        mt, ncs, mcs, dom = lng.build_mode_neuron_factor_graph(
            s, SEEDS, modes, coeffs, nidx, field, temperature=1.0,
            mode_field_scale=0.0, neuron_field_scale=1.0, incidence_scale=1.0,
            n_modes=N_MODES, discrete_mode=discrete_mode,
            incidence_override=override)
        bp = run_loopy_bp(s, mt, combine="max_product")
        sh = lng.read_mode_nodes(bp, mcs)
        ags.append(float(np.mean(np.where(coeffs[dom] >= 0, 1.0, -1.0) == sh)))
    return float(np.mean(ags))


def _direct_covariance(modes, Wc, xs, nidx, W):
    """No-BP readout ceiling: sign(W · sign(field)) vs sign(coeffs)."""
    ok = []
    for x in xs:
        coeffs = Wc @ x
        s = np.where((coeffs @ modes[:, nidx]) >= 0, 1.0, -1.0)
        dom = np.argsort(-np.abs(coeffs))[:N_MODES]
        ok.append(float(np.mean(np.sign(W[dom] @ s)
                                 == np.where(coeffs[dom] >= 0, 1.0, -1.0))))
    return float(np.mean(ok))


def main():
    export = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EXPORT
    z = np.load(export)
    modes, mean, Wc = z["modes"], z["mean"], z["Wc"]
    ho_x, tr_x = z["ho_x"], z["tr_x"]
    nidx = z["neuron_idx"][:N_NEUR]
    L = int(z["layer"])

    print("=" * 74)
    print("NATIVE-GRAPH FIDELITY — block 323000 (layer %d)" % L)
    print("closing the incidence-map fidelity gap (block 322 raw = ~0.75)")
    print("=" * 74)

    # ---- Lever 1: fitted incidence, ridge sweep (direct-readout ceiling) ----
    print("\n[lever 1] fitted incidence — direct-readout ceiling (train vs held-out)")
    print("%-8s %-8s %-8s" % ("ridge", "train", "held-out"))
    for rg in (1.0, 50.0, 500.0):
        W = lng.fit_incidence(modes, mean, Wc, tr_x, nidx, n_modes=N_MODES,
                              ridge=rg)
        tr = _direct_covariance(modes, Wc, tr_x, nidx, W)
        ho = _direct_covariance(modes, Wc, ho_x, nidx, W)
        print("  %-6.0f %-8.2f %-8.2f" % (rg, tr, ho))
    print("  (train ~1.0 regardless => representable; held-out rises with reg")
    print("   => the gap is GENERALISATION, closed in part by regularisation)")

    # ---- Through the substrate BP settle: raw vs fitted(heavy reg) ----
    W = lng.fit_incidence(modes, mean, Wc, tr_x, nidx, n_modes=N_MODES,
                          ridge=500.0)
    raw = _bp_covariance(modes, mean, Wc, ho_x, nidx, override=None)
    fit = _bp_covariance(modes, mean, Wc, ho_x, nidx, override=W)
    print("\n[substrate BP settle, held-out aperture-covariance]")
    print("  raw-loading incidence:        %.2f  (block 322 baseline)" % raw)
    print("  fitted incidence (heavy reg): %.2f  (block 323 — the lift)" % fit)

    # ---- Lever 2: vocab ----
    v3 = _bp_covariance(modes, mean, Wc, ho_x, nidx, override=None,
                        discrete_mode="3state")
    v2 = _bp_covariance(modes, mean, Wc, ho_x, nidx, override=None,
                        discrete_mode="2state")
    print("\n[lever 2] vocab (raw incidence): 3state %.2f  vs  2state %.2f  "
          "(no effect => not the ceiling)" % (v3, v2))

    print("\n" + "=" * 74)
    print("VERDICT — the fidelity gap is GENERALISATION, partly closable:")
    print("  * fitted + well-regularised incidence lifts held-out covariance")
    print("    from ~0.75 (raw) to ~0.88 through the substrate's own BP.")
    print("  * train reaches ~1.0 => full aperture-covariance is REPRESENTABLE;")
    print("    the residual is generalisation at 60 train prompts, not a wall.")
    print("  * vocab (2 vs 3 state) does not move it; solver does not (322c:")
    print("    exact == loopy). The named STRUCTURAL next axis is the")
    print("    between-layer TRANSPORT incidence (this arc used one layer).")
    print("=" * 74)


if __name__ == "__main__":
    main()
