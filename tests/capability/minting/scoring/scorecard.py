"""Unified scorecard — places the substrate next to the human baseline and (if a user
supplied one) an LLM column, on every rubric metric, with FLEX-style bootstrap CIs.

Pure assembly + formatting over numbers the runners/scorer already produced. No
substrate or model is invoked here. The LLM column is the PUBLISHED reference from
arXiv:2505.17117 unless the user pastes back a fresh run via the OFF-by-default harness.
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import metrics as M                     # noqa: E402


def build_scorecard(substrate: dict, *, human: dict = None,
                    llm: dict = None) -> dict:
    """Assemble the side-by-side scorecard.

    `substrate` carries the substrate's measured values keyed by metric:
      {"rq2_rho": float, "rq2_rho_samples": [..], "rq1_ami": float,
       "rq3_L_fine": float, "rq3_L_coarse": float, "gate_f1": float}
    `human` defaults to the ground-truth column (rho=1.0 by construction, AMI=1.0).
    `llm` defaults to the PUBLISHED reference numbers (metrics.LLM_REFERENCE).
    Returns a dict with a per-metric substrate/human/llm comparison + substrate CIs."""
    ref = M.LLM_REFERENCE
    human = human or {"rq2_rho": 1.0, "rq1_ami": 1.0}
    llm = llm or {"rq2_rho_decoder": ref["rq2_spearman_decoder_typical"],
                  "rq2_rho_bert": ref["rq2_spearman_bert"],
                  "rq1_ami": ref["rq1_ami_human_aligned"]}

    rows = []

    # RQ2 — Spearman rho (fine-grained fidelity)
    rho_ci = (M.bootstrap_ci(substrate["rq2_rho_samples"])
              if substrate.get("rq2_rho_samples") else
              {"mean": substrate.get("rq2_rho"), "lo": None, "hi": None})
    rows.append({
        "metric": "RQ2 typicality Spearman rho (higher=better)",
        "substrate": rho_ci["mean"], "substrate_ci": [rho_ci["lo"], rho_ci["hi"]],
        "human": human["rq2_rho"],
        "llm_decoder": llm["rq2_rho_decoder"], "llm_bert": llm["rq2_rho_bert"],
        "substrate_beats_llm": (rho_ci["mean"] is not None
                                and rho_ci["mean"] > llm["rq2_rho_bert"])})

    # RQ1 — category recoverability AMI
    rows.append({
        "metric": "RQ1 category recoverability AMI (higher=better)",
        "substrate": substrate.get("rq1_ami"),
        "human": human["rq1_ami"], "llm": llm["rq1_ami"],
        "note": "substrate recovery is explicit is-a structure, not emergent geometry "
                "(see T1); the LLM number is emergent — asymmetric, reported as such"})

    # RQ3 — L objective (compression-meaning); higher L = richer/less compressed
    rows.append({
        "metric": "RQ3 L objective: coarse->fine (minting raises L toward human rich)",
        "substrate_coarse": substrate.get("rq3_L_coarse"),
        "substrate_fine": substrate.get("rq3_L_fine"),
        "reading": "LLMs over-compress to LOW L; minting moves the substrate UP "
                   "(distortion/meaning preserved)"})

    # Rubric B — accommodation gate
    rows.append({
        "metric": "Gate F1 (accommodation vs gap-fill; higher=better)",
        "substrate": substrate.get("gate_f1"),
        "human": "1.0 (readiness gate by construction)",
        "note": "persistent->mint, transient/duplicate->no mint"})

    return {"columns": ["substrate", "human", "llm(published ref)"], "rows": rows}


def render(scorecard: dict) -> str:
    """A compact text rendering of the scorecard for the track output."""
    out = []
    out.append("SIDE-BY-SIDE SCORECARD (substrate vs human vs published-LLM ref)")
    out.append("=" * 78)
    for r in scorecard["rows"]:
        out.append("• " + r["metric"])
        for k, v in r.items():
            if k == "metric":
                continue
            out.append("     %-22s %s" % (k + ":", v))
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    # smoke render with placeholder substrate numbers
    demo = {"rq2_rho": 0.89, "rq2_rho_samples": [0.9, 0.888, 0.888],
            "rq1_ami": 1.0, "rq3_L_coarse": 2.57, "rq3_L_fine": 4.56,
            "gate_f1": 1.0}
    print(render(build_scorecard(demo)))
