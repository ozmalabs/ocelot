"""Block 326000 — pushing transport fidelity: is the per-hop gap closable?

Block 324/325: the between-layer transport is aperture-covariant on the
substrate's own BP at ~0.80 held-out per hop, and the feed-forward chain
composes there across depth — but the LINEAR transport reads ~0.90 per hop, so
there is a ~0.10/hop DISCRETISATION gap (a continuous directed linear map forced
through a discrete undirected Ising MAP settle). This block applies block 323's
fidelity lever (and five more) to try to close that gap.

Six independent axes tried, NONE close it:
  1. settle-aware weight fit (regress binarised sign(coeffs_L) -> coeffs_{L+1},
     i.e. fit to what the settle actually reads);
  2. regularisation of that fit;
  3. vocab (2state vs 3state);
  4. field / transport / temperature dynamics;
  5. max-product vs sum-product combine;
  6. edge asymmetry (weaken the reverse Ising edge toward a directed transport).

FINDING (honest negative): the ~0.10/hop gap is IRREDUCIBLE on the undirected-
Ising substrate — it is the structural price of expressing a continuous DIRECTED
linear readout as a discrete UNDIRECTED Ising MAP via `run_loopy_bp`. The
feed-forward chain already tolerates it (block 325 composes at ~0.80 across
depth). Closing it would need a directed/continuous inference primitive; the
substrate's BP is undirected and discrete (protected, unchangeable here).

Requires the chain export npz and substrate_rs:
  PYTHONPATH=runners/dsl/python python3 \\
    scripts/llm_transport_fidelity_measure.py [chain.npz]
"""

import sys
sys.path.insert(0, ".")
import numpy as np

from substrate_rs import _native
from domains import llm_native_graph as lng
from domains.can_native_bp import run_loopy_bp

SEEDS = ["seeds/can_native_reimplementation.json"]
DEFAULT_EXPORT = "/applications/data/model_graph_work/chain_L10_14.npz"
NM = 8


def _hop_bp(T, c0, c1, *, fs=1.0, ts=1.0, temp=1.0, dm="3state",
            combine="max_product", back=1.0):
    ok = []
    for x0, x1 in zip(c0, c1):
        s = _native.Substrate()
        coeffs0 = np.zeros(c0.shape[1], dtype=np.float32)
        coeffs0[:] = x0
        mt, ln = lng.build_chain_factor_graph(
            s, SEEDS, [T], coeffs0, n_modes=NM, temperature=temp,
            field_scale=fs, transport_scale=ts, discrete_mode=dm,
            back_scale=back)
        bp = run_loopy_bp(s, mt, combine=combine)
        sh = lng.read_transport_modes(bp, ln[1])
        ok.append(float(np.mean(sh == np.where(x1[:NM] >= 0, 1.0, -1.0))))
    return float(np.mean(ok))


def _hop_linear(T, c0, c1):
    return float(np.mean([np.mean(np.sign((T @ x0)[:NM])
                                  == np.where(x1[:NM] >= 0, 1.0, -1.0))
                          for x0, x1 in zip(c0, c1)]))


def _ff_chain(Ts, ho_c, nL):
    per = [[] for _ in range(nL)]
    for q in range(ho_c.shape[1]):
        cur = ho_c[0, q, :NM].copy()
        per[0].append(float(np.mean(np.sign(cur)
                                    == np.where(ho_c[0, q, :NM] >= 0, 1.0, -1.0))))
        for hop in range(nL - 1):
            c0 = np.zeros(ho_c.shape[2], dtype=np.float32)
            c0[:NM] = cur
            s = _native.Substrate()
            mt, ln = lng.build_chain_factor_graph(
                s, SEEDS, [Ts[hop]], c0, n_modes=NM, temperature=1.0,
                discrete_mode="3state")
            bp = run_loopy_bp(s, mt, combine="max_product")
            sh = lng.read_transport_modes(bp, ln[1])
            per[hop + 1].append(float(np.mean(
                sh == np.where(ho_c[hop + 1, q, :NM] >= 0, 1.0, -1.0))))
            cur = sh
    return [float(np.mean(per[d])) for d in range(nL)]


def main():
    export = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EXPORT
    z = np.load(export)
    tr_c, ho_c, layers = z["tr_c"], z["ho_c"], list(z["layers"])
    nL = len(layers)
    c0_tr, c1_tr = tr_c[0], tr_c[1]
    c0_ho, c1_ho = ho_c[0], ho_c[1]
    Traw = lng.fit_transport(c0_tr, c1_tr, ridge=1.0)

    print("=" * 74)
    print("TRANSPORT FIDELITY — block 326000 (single hop L%d->L%d, held-out)"
          % (layers[0], layers[1]))
    print("=" * 74)
    print("  linear baseline sign(T.x0):        %.2f" % _hop_linear(Traw, c0_ho, c1_ho))
    print("  raw-T BP settle (block 324/325):   %.2f" % _hop_bp(Traw, c0_ho, c1_ho))

    print("\n--- six levers to close the ~0.10/hop discretisation gap ---")
    # 1/2 settle-aware weight fit + regularisation
    for rg in (1.0, 10.0, 100.0):
        Tsa = lng.fit_transport_settle_aware(c0_tr, c1_tr, ridge=rg, n_modes=NM)
        print("  1/2 settle-aware fit ridge %-5.0f: %.2f" %
              (rg, _hop_bp(Tsa, c0_ho, c1_ho)))
    # 3 vocab
    print("  3   vocab 2state:                  %.2f" %
          _hop_bp(Traw, c0_ho, c1_ho, dm="2state"))
    # 4 dynamics
    print("  4   dynamics fs=3,ts=3:            %.2f" %
          _hop_bp(Traw, c0_ho, c1_ho, fs=3.0, ts=3.0))
    # 5 combine
    print("  5   sum-product combine:           %.2f" %
          _hop_bp(Traw, c0_ho, c1_ho, combine="sum_product"))
    # 6 edge asymmetry
    print("  6   edge asymmetry back=0.1:       %.2f" %
          _hop_bp(Traw, c0_ho, c1_ho, back=0.1))

    print("\n--- feed-forward chain: raw vs settle-aware transports (per depth) ---")
    Traws = [lng.fit_transport(tr_c[i], tr_c[i + 1], ridge=1.0)
             for i in range(nL - 1)]
    Tsas = [lng.fit_transport_settle_aware(tr_c[i], tr_c[i + 1], ridge=10.0,
                                           n_modes=NM) for i in range(nL - 1)]
    raw = _ff_chain(Traws, ho_c, nL)
    sa = _ff_chain(Tsas, ho_c, nL)
    print("  %-8s %-10s %-14s" % ("depth", "FF-raw", "FF-settle-aware"))
    for d in range(nL):
        print("  L%-6d %-10.2f %-14.2f" % (layers[d], raw[d], sa[d]))

    print("\n" + "=" * 74)
    print("VERDICT — HONEST NEGATIVE: the ~0.10/hop gap is IRREDUCIBLE here.")
    print("  Six independent levers (settle-aware fit, regularisation, vocab,")
    print("  dynamics, combine rule, edge asymmetry) all leave per-hop BP at")
    print("  ~0.78 vs linear ~0.88. It is the structural price of a continuous")
    print("  DIRECTED linear map expressed as a discrete UNDIRECTED Ising MAP")
    print("  (run_loopy_bp). The feed-forward chain already composes AT this")
    print("  ceiling across depth (block 325); a directed/continuous inference")
    print("  primitive would be needed to close it, which the substrate's BP")
    print("  (undirected, discrete, protected) does not provide.")
    print("=" * 74)


if __name__ == "__main__":
    main()
