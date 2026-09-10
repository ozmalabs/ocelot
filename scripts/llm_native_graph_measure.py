"""Block 321000 — APERTURE-COVARIANCE measure (the native-graph test).

Is the recovered structure a NATIVE GRAPH, or still an IR at one aperture? The
test (per the user's framing that "an edge is literally a node at a different
aperture"): read the same recovered object at the MODE aperture and, refined to
the NEURON-coactivation aperture, propagate it on the SUBSTRATE'S OWN belief
propagation (`can_native_bp.run_loopy_bp`, a discrete Ising model — NOT numpy
matmul replay), then read the settled state back up. If the settled fine graph
re-expresses the coarse mode reading, the object is aperture-covariant (a native
graph, and the cognition is substrate-independent). If not, it is an IR.

RESULT: honest NEGATIVE. Reported plainly.

Requires the mode export npz (produced in the model venv by
`domains.llm_native_graph.export_mode_structure`) and substrate_rs on the path:
  PYTHONPATH=runners/dsl/python python3 scripts/llm_native_graph_measure.py \\
    [export.npz]
"""

import sys
sys.path.insert(0, ".")
import numpy as np

from substrate_rs import _native
from domains import llm_native_graph as lng
from domains.can_native_bp import run_loopy_bp

SEEDS = ["seeds/can_native_reimplementation.json"]
DEFAULT_EXPORT = "/applications/data/model_graph_work/mode_export_L12b.npz"


def _settle(field, J, fs, js):
    s = _native.Substrate()
    mt, concepts = lng.build_ising_refinement(
        s, SEEDS, field, J, temperature=1.0, field_scale=fs, j_scale=js,
        discrete_mode="3state")
    bp = run_loopy_bp(s, mt, combine="max_product")
    ss = lng.settled_state_array(bp, concepts)
    return np.array([ss[p] for p in range(len(field))]), bp["converged"]


def _covariance(modes, mean, Wc, ho_x, neuron_idx, coact_J, *, top_modes, fs,
                js, coupling, shuffle=False, rng=None):
    ags = []
    for x in ho_x:
        coeffs, coarse = lng.coarse_mode_state(modes, mean, Wc, x)
        if coupling == "mode_gram":
            nidx, field, J = lng.refine_to_neurons(modes, coeffs,
                                                   n_neurons=len(neuron_idx))
        else:  # coactivation
            field, J = lng.refine_to_neurons_coact(modes, coeffs, neuron_idx,
                                                   coact_J)
            nidx = neuron_idx
        if shuffle:
            iu = np.triu_indices_from(J, k=1)
            vals = J[iu].copy(); rng.shuffle(vals)
            Js = np.zeros_like(J); Js[iu] = vals; J = Js + Js.T
        settled, _ = _settle(field, J, fs, js)
        _, state_hat = lng.read_back_modes(modes, nidx, settled)
        order = np.argsort(-np.abs(coeffs))[:top_modes]
        ags.append(float(np.mean(coarse[order] == state_hat[order])))
    return float(np.mean(ags))


def main():
    export = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EXPORT
    z = np.load(export)
    modes, mean, Wc, ho_x = z["modes"], z["mean"], z["Wc"], z["ho_x"]
    neuron_idx, coact_J = z["neuron_idx"], z["coact_J"]
    L = int(z["layer"])
    rng = np.random.default_rng(0)
    cj = coact_J / (np.abs(coact_J).mean() + 1e-9)   # normalise to field scale

    print("=" * 74)
    print("APERTURE-COVARIANCE — block 321000 (native-graph test)")
    print("layer %d, %d held-out, N=%d neurons; chance = 0.50" %
          (L, len(ho_x), len(neuron_idx)))
    print("mode aperture  <->  neuron aperture (substrate loopy-BP settle)")
    print("=" * 74)

    # coupling structure summary
    off = coact_J[np.triu_indices_from(coact_J, k=1)]
    _, f0, Jg = lng.refine_to_neurons(modes, Wc @ ho_x[0],
                                      n_neurons=len(neuron_idx))
    goff = Jg[np.triu_indices_from(Jg, k=1)]
    print("mode-Gram   |J_off|=%.3f  (orthogonal modes -> ~no edges)" %
          np.abs(goff).mean())
    print("coactivation|J_off|=%.3f  nonzero=%.2f  (real cofiring edges)\n" %
          (np.abs(off).mean(), float(np.mean(off > 0))))

    print("%-14s %-8s %-8s %-12s %-12s" %
          ("coupling", "top_md", "fs/js", "covariance", "shuffle-J"))
    for coupling in ("mode_gram", "coactivation"):
        for top_modes in (4, 8):
            fs, js = (1.0, 1.0)
            cov = _covariance(modes, mean, Wc, ho_x, neuron_idx, cj,
                              top_modes=top_modes, fs=fs, js=js,
                              coupling=coupling)
            sh = _covariance(modes, mean, Wc, ho_x, neuron_idx, cj,
                             top_modes=top_modes, fs=fs, js=js,
                             coupling=coupling, shuffle=True, rng=rng)
            print("%-14s %-8d %-8s %-12.2f %-12.2f" %
                  (coupling, top_modes, "%.1f/%.1f" % (fs, js), cov, sh))

    print("\n" + "=" * 74)
    print("VERDICT — HONEST NEGATIVE:")
    print("  covariance ~ chance (0.5) and not above the shuffle-J control, for")
    print("  BOTH couplings. mode-Gram: orthogonal modes have ~no edges (inert).")
    print("  coactivation: dense positive coupling is a FERROMAGNET whose Ising")
    print("  settle collapses to global consensus, erasing per-neuron structure.")
    print("  The recovered structure is NOT aperture-covariant as constructed —")
    print("  the mode->Ising refinement is a DIFFERENT object sharing neuron")
    print("  support, not the same object at a finer aperture. The incidence map")
    print("  between apertures is missing. It remains an IR, not a native graph.")
    print("=" * 74)


if __name__ == "__main__":
    main()
