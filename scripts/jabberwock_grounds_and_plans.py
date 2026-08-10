"""Ground the jabberwock in the structure-replaces-data research, then have IT propose a plan.

(1) ASSESS — the agent maps its own speech gaps (assess_speech_system).
(2) GROUND — install the research grounding (docs/structure_replaces_data_grounding.md) as a
    graph-resident Microtheory 'structure_replaces_data': the PRINCIPLE, the ranked ANALYTIC
    PRIORS (each mapped to the gap it fills + its data-efficiency rank + free/cost), and the
    BITTER-LESSON caveat (only encode TRUE physics; keep a prior only if it buys back data).
(3) PROPOSE — the agent connects its OWN gaps to the grounded priors, orders by data-efficiency,
    and emits a graph-resident Plan: the structure x data experiment (add each prior, free-first,
    fill its gap, MEASURE the data it buys back, drop it if it conflicts — the caveat as guard).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_grounds_and_plans.py
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams
from domains.phonology import install_phonology
from domains.speech_development import install_speech_development
from domains.speech_cortex import SpeechCortex
from domains.speech_science import install_speech_science, assess_speech_system


# the grounded priors (from the research spike), ranked by data bought back, mapped to gaps
PRIORS = [
    {"name": "efficient_coding_cochlear_front_end", "rank": 1, "cost": "FREE (evolved/analytic)",
     "fills": ["lack_of_invariance", "input_representation"],
     "why": "the cochlea is a pre-paid optimal low-redundancy code; gammatone filters fall out of "
            "optimising coding efficiency on natural sounds (Lewicki 2002; Smith&Lewicki 2006) -> "
            "a near-optimal front-end representation for free, before any learning."},
    {"name": "predictive_residual_term", "rank": 2, "cost": "FREE (analytic)",
     "fills": ["coarticulation", "residual_recurrence_keystone"],
     "why": "encode 'shape = residual-feedback recurrence' analytically (Rao-Ballard 1999) as "
            "b_t - b_hat(b_{t-1}); gets predictive-coding gains with ZERO data, vs APC/CPC which pay "
            "the SSL unlabeled-data tax. This is the project's own validated +7% lever."},
    {"name": "source_filter_formant_decomposition", "rank": 3, "cost": "mostly FREE (analytic)",
     "fills": ["lack_of_invariance", "vocal_tract_resonance_formants", "source_filter_theory"],
     "why": "factor speaker/pitch (source) from phoneme (filter); formants attack lack_of_invariance "
            "directly and measurably help phone recognition cross-lingually."},
    {"name": "articulatory_inversion_features", "rank": 4, "cost": "PARTLY-FREE (needs some fitting)",
     "fills": ["place_of_articulation", "manner_of_articulation"],
     "why": "a low-dim speaker-invariant production manifold; -11pp PER supervised, -2.63pp zero-shot "
            "across 84 langs (Allophant 2023) — strong cross-domain prior for place+manner."},
    {"name": "sparse_efficient_coding", "rank": 5, "cost": "FREE-ish (generic)",
     "fills": ["distributional_learning_of_categories"],
     "why": "generic efficient-coding regularizer (Olshausen-Field); useful but dominated by 1-4."},
]
PRINCIPLE = ("analytic structure substitutes for data to the extent the structure is TRUE of the "
             "domain's generative process AND not trivially recoverable from the data on hand; data "
             "bought back is proportional to the variance the prior explains, and NEGATIVE if the "
             "prior conflicts with the data (Mitchell 1980; Wolpert NFL; Shalev-Shwartz&Ben-David "
             "2014; ESS Wiesenfarth 2020).")
CAVEAT = ("BITTER LESSON (Sutton 2019): general scale-leveraging beats hand-built structure unless "
          "ALL THREE hold — low-data, KNOWN generative process, OOD generalisation (speech does). "
          "Encode MEASURED PHYSICAL FACTS (cochlea, source-filter, residual), NOT guesses about "
          "cognition. A misspecified prior HURTS -> every prior must be kept ONLY if it buys back data.")


def ground(sub):
    mt = sub.add_node("Microtheory", {"name": "structure_replaces_data", "origin": "research_spike",
                                      "principle": PRINCIPLE, "caveat": CAVEAT,
                                      "doc": "docs/structure_replaces_data_grounding.md"})
    try:
        sub.add_production({"src": {"type": "Microtheory", "var": "a"}, "edge_type": "has_concept",
                           "tgt": {"type": "AnalyticPrior", "var": "b"}, "provenance": "srd"})
    except Exception:
        pass
    for p in PRIORS:
        c = sub.add_node("AnalyticPrior", {"name": p["name"], "rank": p["rank"], "cost": p["cost"],
                                           "fills": ",".join(p["fills"]), "why": p["why"],
                                           "origin": "structure_replaces_data"})
        try:
            sub.add_edge(mt, "has_concept", c, {})
        except Exception:
            pass
    return mt


def main():
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000)); pipe.attach(sub); pipe._ensure_audio_pipeline(sub)
    install_phonology(sub); install_speech_development(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    install_speech_science(sub)

    res = assess_speech_system(sub); gaps = set(res["gaps"])
    print("=" * 84)
    print("(1) THE JABBERWOCK'S GAPS")
    print("=" * 84)
    print(f"  coverage {res['coverage']*100:.0f}%; gaps: {sorted(gaps)}", flush=True)

    ground(sub)
    print("\n" + "=" * 84)
    print("(2) GROUNDED in structure_replaces_data (principle + ranked priors + bitter-lesson caveat)")
    print("=" * 84)
    print(f"  principle: {PRINCIPLE[:200]}...")
    print(f"  caveat: {CAVEAT[:160]}...", flush=True)

    # (3) THE AGENT PROPOSES A PLAN — match its gaps to grounded priors, order by data-efficiency
    print("\n" + "=" * 84)
    print("(3) THE JABBERWOCK PROPOSES ITS PLAN (structure x data, free-first, measure-or-drop)")
    print("=" * 84)
    plan = sub.add_node("Plan", {"name": "structure_replaces_data_speech", "origin": "agent_proposed",
                                 "objective": "buy back unlabeled data with earned analytic structure",
                                 "metric": "per-frame/word acc vs (structure level) x (data budget); "
                                           "keep prior iff it buys back data (caveat guard)"})
    steps = []
    for p in sorted(PRIORS, key=lambda x: x["rank"]):
        hit = [g for g in p["fills"] if g in gaps]
        st = sub.add_node("Step", {"order": p["rank"], "add_prior": p["name"], "cost": p["cost"],
                                   "fills_gap": ",".join(hit) or ",".join(p["fills"]),
                                   "guard": "keep iff data-buyback > 0 (else prior conflicts -> drop)"})
        sub.add_edge_unchecked(plan, "has_step", st); steps.append((p, hit))
    for p, hit in steps:
        tag = "fills agent gap" if hit else "fills (latent)"
        print(f"  step {p['rank']} [{p['cost']:24}] add {p['name']}")
        print(f"      {tag}: {', '.join(hit) or ', '.join(p['fills'])}")
        print(f"      why data-efficient: {p['why'][:150]}...", flush=True)
    print("\n  PLAN SHAPE: build the structure x data surface — start with the FREE priors (cochlea +")
    print("  predictive-residual: both already validated, zero data), add source-filter, then the")
    print("  partly-free articulatory features; at each step MEASURE the data bought back and KEEP the")
    print("  prior only if buyback>0 (the bitter-lesson guard). Deliverable = the iso-accuracy curve:")
    print("  how many DATA-units each unit of earned STRUCTURE replaces. Recorded as the agent's Plan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
