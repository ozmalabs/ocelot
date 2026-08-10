"""Speech development theory — graph-resident developmental knowledge.

The substrate has the apparatus: cortices, predicates, signatures,
the babble loop. What it doesn't have YET is a model of HOW that
apparatus develops. This module installs that model.

Concepts grounded here describe the developmental phenomena the
substrate is enacting:

  babbling                     — self-vocalisation trains the
                                 perception-production loop
  mismatch_signal              — disagreement between produced and
                                 perceived is the learning signal
  perceptual_narrowing         — feature space SHRINKS toward the
                                 categories actually encountered
  categorical_perception       — discrete category boundaries emerge
                                 from continuous input variation
  phase_transition             — capability appears discontinuously
                                 when configuration crosses threshold
  vocabulary_explosion         — sudden lexical acquisition once
                                 phonological categories are stable
  feature_invention            — coarse features split when bimodal
                                 distributions cross threshold

Each concept carries:
  description: textbook account of the phenomenon
  rule:        what the agent should DO when this concept applies
               (read by DevelopmentCortex to self-direct)
  indicator:   the configuration metric whose value signals this
               concept is active

Together these form the agent's model of its own development.
The DevelopmentCortex reads these concepts + the cross-cortex
state and applies the rules to adjust the substrate's own
parameters — making the system self-developmentally-aware.
"""
from __future__ import annotations


# (name, description, rule, indicator)
_DEV_CONCEPTS = [
    ("babbling",
     "Regular self-vocalisation trains the perception-production "
     "loop. Required for phonological category formation. Infants "
     "produce 1-3 babble events per minute during canonical "
     "babbling phase.",
     "If motor_coherence average < 0.5, increase babble events per "
     "cycle. If > 0.7, can decrease — the loop is converging.",
     "motor_coherence_avg"),
    ("mismatch_signal",
     "Disagreement between expected and observed (whether from "
     "teaching or self-perception) is the primary learning signal. "
     "Mismatches drive predicate retuning + feature invention.",
     "If impasses_raised per cycle > 10, learning is rich. If "
     "< 3 for many cycles, system is over-converged — challenge "
     "with novel teaching or harder distinctions.",
     "impasses_raised_recent"),
    ("perceptual_narrowing",
     "Universal-listener infants distinguish all phonemic "
     "contrasts; native-listener adults distinguish only those of "
     "their language. The feature space SHRINKS to what's "
     "actually used. Happens around 6-10 months.",
     "If a phonology concept fires on < 5% of signs across many "
     "cycles, it can be pruned. (NOT YET WIRED — pruning is a "
     "future capability.)",
     "feature_usage_distribution"),
    ("categorical_perception",
     "Continuous acoustic variation gets discretised into discrete "
     "categories. VOT, formant frequencies, etc. all show "
     "step-functions at category boundaries. Forms around 6-12 "
     "months.",
     "If exhibits_entropy rises and predicate Δ-norm stays low, "
     "categorical perception is consolidating.",
     "exhibits_entropy_trend"),
    ("phase_transition",
     "Cognitive capabilities emerge discontinuously when "
     "configuration crosses threshold. No smooth gradient up. "
     "Below: noise. Above: structured behaviour. Cannot be "
     "predicted from local metrics, only recognised post-hoc.",
     "Don't optimise for accuracy. Instead, ensure configuration "
     "metrics (motor coherence, predicate stability, feature "
     "richness) keep advancing. Phase transition will manifest "
     "when they cumulatively suffice.",
     "config_advancement_rate"),
    ("vocabulary_explosion",
     "Once phonological categories stabilise, lexical acquisition "
     "rate jumps dramatically. ~18-month-old children acquire "
     "1-10 words per day, vs 0.1/day previously.",
     "Once predicate Δ-norm has been zero for 5+ cycles AND motor "
     "coherence > 0.5, can accept much higher rate of new word "
     "teachings without overwhelming the loop.",
     "predicate_stability_duration"),
    ("feature_invention",
     "When existing features fail to discriminate observations "
     "that DO differ behaviourally, the brain forms sub-features. "
     "E.g. 'voicing' splits into 'voicing_strong'/'voicing_weak'.",
     "If sub_class_within_holder hypotheses fire repeatedly on "
     "the same feature but invention threshold isn't met, lower "
     "the invention threshold.",
     "sub_class_hypothesis_count"),
]


_DEV_PRODUCTIONS = [
    ("Microtheory", "contains", "Concept",
     "speech_development:mt_contains_concept"),
    ("DevelopmentCortex", "operates_in", "Microtheory",
     "speech_development:cortex_operates_in_mt"),
]


def install_speech_development(substrate) -> dict:
    """Install the speech_development Microtheory + its concepts.
    Idempotent. Returns name → NodeID for the Mt and concepts."""
    for src_t, et, tgt_t, prov in _DEV_PRODUCTIONS:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass

    # Find or mint the Mt.
    mt = None
    for n in substrate.nodes("Microtheory"):
        if (substrate.node(n)["attrs"].get("name")
                == "speech_development"):
            mt = n
            break
    if mt is None:
        mt = substrate.add_node("Microtheory", {
            "name": "speech_development",
            "description": (
                "Theory of how speech-cognitive capabilities "
                "emerge from sensorimotor experience. "
                "Concepts: babbling, mismatch_signal, perceptual "
                "narrowing, categorical perception, phase "
                "transitions, vocabulary explosion, feature "
                "invention. The DevelopmentCortex reads this Mt "
                "to self-direct the substrate's growth."),
            "origin": "speech_development",
        })

    out = {"_mt": mt}
    for name, desc, rule, indicator in _DEV_CONCEPTS:
        # Find existing concept by name.
        cid = None
        for c in substrate.nodes("Concept"):
            if substrate.node(c)["attrs"].get("name") == name:
                cid = c
                break
        if cid is None:
            cid = substrate.add_node("Concept", {
                "name": name,
                "description": desc,
                "rule": rule,
                "indicator": indicator,
                "origin": "speech_development",
            })
        else:
            # Refresh attrs in case of re-install.
            substrate.set_attr(cid, "description", desc)
            substrate.set_attr(cid, "rule", rule)
            substrate.set_attr(cid, "indicator", indicator)
        # Mt contains.
        if cid not in substrate.neighbours(mt, "contains"):
            try:
                substrate.add_edge(mt, "contains", cid)
            except Exception:
                pass
        out[name] = cid
    return out


__all__ = [
    "install_speech_development",
    "_DEV_CONCEPTS",
]
