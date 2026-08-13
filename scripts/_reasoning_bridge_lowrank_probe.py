"""One-off investigation script (tools/*-class, not agent runtime) for
docs/research/engine_substrate/REASONING_FACILITY_BRIDGE_PREREG.md /
_RESULTS.md candidate 2b: does a REAL, POPULATED `causal_influence` network
exhibit true low-rank (shared-generator) coupling structure, as
CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md Sec6.4/Sec7 item 4 asked but could
not test (no populated network existed at the time)?

Builds every real resident in seeds/bigville_cast100.json's own per-resident
CAN network via the UNMODIFIED worlds/bigville_can_beliefs.build_resident_
can_mt, stacks the 5 real structural-edge weights (both the pre-quantization
`true_j` continuous coupling and the actual `quantized_j` CAN uses) into an
N_residents x 5 matrix, and reports the singular-value spectrum -- the
direct empirical answer to "how many shared latent generators explain this
population's coupling variance" (Sec6.4's own definition: `J_ij = Sum_mu
w_mu . f_mu(i) . f_mu(j)` for a SMALL set of mu).

Pure investigation: reads seeds/bigville_cast100.json, calls
build_resident_can_mt/true_edge_j/quantize_j (all unmodified), no seed/
domain file is edited by this script.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np                                                      # noqa: E402
from substrate_rs import _native                                        # noqa: E402
from worlds.bigville_can_beliefs import (                               # noqa: E402
    install_productions, build_resident_can_mt, STRUCTURAL_EDGES,
    true_edge_j, effective_resolution_bins, quantize_j,
)

_CAST_PATH = os.path.join(_ROOT, "seeds", "bigville_cast100.json")


def _cast():
    return json.load(open(_CAST_PATH))["residents"]


def _spectrum(mat: np.ndarray) -> dict:
    """Center columns (population mean per edge), SVD, report the fraction
    of variance the top-k singular values explain -- the standard
    factor-analysis reading of "how many shared generators does this
    population's coupling variation need."""
    centered = mat - mat.mean(axis=0, keepdims=True)
    # degenerate (zero-variance) columns would blow up a correlation-based
    # method; SVD on the centered matrix directly handles them (a
    # zero-variance column contributes zero singular value mass, honestly).
    u, s, vt = np.linalg.svd(centered, full_matrices=False)
    total = float((s ** 2).sum())
    if total <= 0:
        return {"singular_values": s.tolist(), "explained_variance_ratio": [],
                "cum_explained": [], "rank_at_95pct": 0, "rank_at_99pct": 0}
    var_ratio = (s ** 2) / total
    cum = np.cumsum(var_ratio)
    rank95 = int(np.searchsorted(cum, 0.95) + 1)
    rank99 = int(np.searchsorted(cum, 0.99) + 1)
    return {"singular_values": [round(float(x), 6) for x in s],
            "explained_variance_ratio": [round(float(x), 6) for x in var_ratio],
            "cum_explained": [round(float(x), 6) for x in cum],
            "rank_at_95pct": rank95, "rank_at_99pct": rank99}


def main():
    cast = _cast()
    n = len(cast)
    edge_labels = ["%s-%s" % (a, b) for a, b, _bj, _nk in STRUCTURAL_EDGES]
    nuance_keys = sorted({nk for _a, _b, _bj, nk in STRUCTURAL_EDGES})

    true_mat = np.zeros((n, len(STRUCTURAL_EDGES)))
    quant_mat = np.zeros((n, len(STRUCTURAL_EDGES)))
    for i, resident in enumerate(cast):
        p = resident["params"]
        eff_bins = effective_resolution_bins(p["resolution_bins"], p["arousal"])
        for j, (a, b, base_j, nuance_key) in enumerate(STRUCTURAL_EDGES):
            tj = true_edge_j(p, base_j, nuance_key)
            true_mat[i, j] = tj
            quant_mat[i, j] = quantize_j(tj, eff_bins)

    print("=== Candidate 2b: low-rank/shared-generator test on N=%d real "
          "Bigville residents' causal_influence coupling ===" % n)
    print("edges:", edge_labels)
    print("distinct nuance_key generators driving ALL edge variation:",
          nuance_keys, "(count=%d)" % len(nuance_keys))
    print()
    for name, mat in (("true_j (pre-quantization, continuous)", true_mat),
                       ("quantized_j (actual CAN causal_influence weight)", quant_mat)):
        spec = _spectrum(mat)
        print("--- %s ---" % name)
        print("singular values:          ", spec["singular_values"])
        print("explained variance ratio: ", spec["explained_variance_ratio"])
        print("cumulative explained:     ", spec["cum_explained"])
        print("rank needed for 95%% var:   %d / %d edges"
              % (spec["rank_at_95pct"], len(STRUCTURAL_EDGES)))
        print("rank needed for 99%% var:   %d / %d edges"
              % (spec["rank_at_99pct"], len(STRUCTURAL_EDGES)))
        print()

    # Also verify the CAN network is really built from these exact numbers,
    # on the real substrate, for one resident -- a sanity cross-check that
    # this script's own true_edge_j/quantize_j readout matches what
    # build_resident_can_mt actually writes onto a real graph.
    s = _native.Substrate()
    install_productions(s)
    built = build_resident_can_mt(s, cast[0])
    print("sanity cross-check (resident 0, %r): built['edges'][0] = %r"
          % (cast[0]["name"], built["edges"][0]))


if __name__ == "__main__":
    main()
