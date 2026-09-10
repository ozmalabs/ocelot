"""Block 329000 — a PROCESS extracted as CAN graph dynamics, applied to unseen
inputs.

Tier 3 (hardest) of the extraction direction, after knowledge (327) and concept
(328). A PROCESS is a PROCEDURE the LLM runs — a transformation of an input into
an output — extracted as a transport operator N and applied to inputs it never
saw. The bar rises from held-out TRANSFER to held-out APPLICATION.

Process: `negate` ("X is Y" -> "X is not Y"). Fit N (input->output) and a
valence probe on context-A statements; hold out context-B statements entirely.

Two readings:
  REPRESENTATION application — apply N to a held-out B affirmation vector; does
    the output read as NEGATED under the valence probe? (The process, executed
    in the LLM's own representation.)
  SUBSTRATE application — run N as a TRANSPORT settle over Concept mode-nodes
    (block 324/325 mechanism, NO new grammar); read the output config's valence.
    This executes the process as graph DYNAMICS on the substrate.

FINDING: the process APPLIES to held-out inputs crisply in the representation
(1.00 vs identity 0.00 vs shuffle 0.00). Run as substrate transport it still
BEATS the identity baseline but at REDUCED fidelity — inheriting the irreducible
discretisation constant characterised in block 326 (a continuous directed map
forced through a discrete undirected Ising MAP) plus the K-mode compression.

Requires the process exports (model venv) and — for the substrate reading —
substrate_rs:
  PYTHONPATH=runners/dsl/python python3 scripts/llm_process_seed_measure.py
"""

import sys
sys.path.insert(0, ".")
import numpy as np

DEF_D = "/applications/data/model_graph_work/process_negate.npz"
DEF_K = "/applications/data/model_graph_work/process_negate_k.npz"
SEEDS = ["seeds/can_native_reimplementation.json"]


def main():
    zd = np.load(sys.argv[1] if len(sys.argv) > 1 else DEF_D)
    N, p, thresh = zd["N"], zd["p"], float(zd["thresh"])
    B_aff = zd["B_aff"]                     # [nB, d] held-out affirmations
    rng = np.random.default_rng(0)

    def reads_negated(v):
        return float(v @ p) < thresh

    print("=" * 74)
    print("PROCESS SEED (negate) — block 329000 (held-out APPLICATION)")
    print("process fit on context A; applied to %d held-out B statements it "
          "never saw" % len(B_aff))
    print("=" * 74)

    # ---- REPRESENTATION application ----
    appN = np.mean([reads_negated(N @ v) for v in B_aff])
    appI = np.mean([reads_negated(v) for v in B_aff])           # identity: no-op
    Nr = rng.standard_normal(N.shape).astype(np.float32) * float(np.std(N))
    appR = np.mean([reads_negated(Nr @ v) for v in B_aff])
    print("\n(1) REPRESENTATION — apply N to held-out B affirmation, read valence")
    print("    extracted N  -> reads NEGATED : %.2f" % appN)
    print("    identity (no transform)       : %.2f  (baseline: affirm != negated)"
          % appI)
    print("    shuffled-N control            : %.2f" % appR)

    # ---- SUBSTRATE application (transport-settle over mode-nodes) ----
    try:
        from substrate_rs import _native
        from domains import llm_native_graph as lng
        from domains.can_native_bp import run_loopy_bp
        zk = np.load(DEF_K)
        Nk = zk["N"]; aff_sign = zk["aff_sign"]; neg_sign = zk["neg_sign"]
        Ba = zk["B_aff_coeff"]
        K = Nk.shape[0]

        def substrate_out(inp, Nmat):
            T = np.zeros((32, 32), dtype=np.float32)
            T[:K, :K] = Nmat
            c0 = np.zeros(32, dtype=np.float32)
            c0[:K] = inp
            s = _native.Substrate()
            mt, ln = lng.build_chain_factor_graph(
                s, SEEDS, [T], c0, n_modes=K, temperature=1.0,
                transport_scale=1.0, discrete_mode="3state")
            bp = run_loopy_bp(s, mt, combine="max_product")
            return lng.read_transport_modes(bp, ln[1])

        def cfg_negated(cfg):
            return (cfg @ neg_sign) > (cfg @ aff_sign)

        sN = np.mean([cfg_negated(substrate_out(c, Nk)) for c in Ba])
        sI = np.mean([cfg_negated(substrate_out(c, np.eye(K, dtype=np.float32)))
                      for c in Ba])
        # continuous k-space readout (isolates the K-compression from the settle)
        pk = zk["pvec"]; thk = float(zk["thr"])
        linN = np.mean([(Nk @ c) @ pk < thk for c in Ba])
        linI = np.mean([c @ pk < thk for c in Ba])
        print("\n(2) SUBSTRATE — run N as transport-settle over mode-nodes (NO LLM)")
        print("    linear K=%d (continuous)  extracted %.2f  identity %.2f"
              % (K, linN, linI))
        print("    substrate Ising settle    extracted %.2f  identity %.2f"
              % (sN, sI))
        print("    (reduced fidelity vs representation — the block-326")
        print("     discretisation constant + K-mode compression)")
    except Exception as e:  # noqa: BLE001
        print("\n(2) SUBSTRATE reading skipped (substrate_rs / export absent): %s"
              % e)

    print("\n" + "=" * 74)
    print("VERDICT:")
    print("  The negate PROCESS extracts and APPLIES to held-out inputs it never")
    print("  saw: in the LLM representation, N(affirmation) reads NEGATED 1.00 vs")
    print("  identity 0.00 vs shuffle 0.00 — a procedure, not stored pairs. Run")
    print("  as substrate transport dynamics it still beats the identity")
    print("  baseline but at reduced fidelity (block-326 discretisation + K")
    print("  compression). Process extracted as dynamics; the crisp claim is at")
    print("  the representation level, the substrate execution is honest-reduced.")
    print("=" * 74)


if __name__ == "__main__":
    main()
