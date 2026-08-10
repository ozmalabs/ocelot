"""Model understanding — the agent's graph-resident knowledge about the MODELS
it authors (e.g. the softmax net the code-writing cortex drafts for recognition).

Authoring a model is not the capability; UNDERSTANDING what a model IS — and
handling it accordingly — is. A model the agent authored but did not train is a
STATIC artifact. The agent must understand three things, all graph-resident here
as Concepts a model-aware cortex reads (same shape as speech_development):

  1. models do not adapt — they are frozen at authoring time (the agent authors,
     it does not train); unlike the agent's own learning, which adapts;
  2. balance the cost — using a model costs compute, and a static model can be
     systematically wrong with no in-loop path to improve, so weigh it against
     the adaptive recogniser;
  3. handle failed utterances / surprise from the model — a model's wrong or
     surprising output is a SURPRISE signal; the agent handles it via its
     surprise machinery (NOT by retraining — it doesn't — but by recording the
     limit and falling back to the adaptive core that DOES learn).

This is the missing capability behind net-authoring: the agent reaching for a
model where one fits is only safe once it knows a model is a frozen snapshot it
must keep honest against its adaptive recognition. See memory
[[ozma_agent_authors_not_trains]] / [[ozma_net_authoring_speech_bridge]].
"""
from __future__ import annotations


# (name, description, rule, indicator) — mirrors speech_development's shape so a
# model-aware cortex reads the same way the DevelopmentCortex reads its Mt.
_MODEL_CONCEPTS = [
    ("model_is_static",
     "An authored model (the softmax net the code-writing cortex drafts) is a "
     "STATIC parametric map: it computes output from input through FIXED "
     "parameters. The agent AUTHORS models; it does not TRAIN them — so a "
     "model's competence is frozen at authoring time. Unlike the agent's own "
     "graph-resident learning — signatures, predicates, invented features — "
     "which ADAPTS continuously from babble + mismatch feedback, a model does "
     "NOT adapt. A model that is wrong stays wrong.",
     "Never treat a failing model as a tuning problem to be fixed by re-running "
     "it — it cannot adapt. Re-authoring changes STRUCTURE only, never learned "
     "competence (which would need training the agent does not do). Keep the "
     "categories distinct: the adaptive recogniser is the thing that LEARNS; a "
     "model is a frozen snapshot of it (or worse, an unfitted shell).",
     "model_param_change_across_calls"),   # always 0 for an authored model
    ("model_cost_balance",
     "Using a model has a COST: compute per call, plus the structural cost that "
     "— being static — it can be SYSTEMATICALLY wrong with no in-loop path to "
     "improve. Balance that against the adaptive recogniser (the babble-trained "
     "lexicon), which costs its own compute but DOES improve over cycles. An "
     "unfitted or persistently-failing model is not worth its cost; a model is "
     "only worth keeping if its fixed competence beats the adaptive recogniser's "
     "current state by more than its per-call cost.",
     "When a model's failure rate is high AND it cannot adapt, DROP it: stop "
     "paying its per-call cost and rely on the adaptive core. Re-evaluate the "
     "balance each time the adaptive recogniser advances (it may overtake a "
     "once-useful frozen model).",
     "model_failure_rate_vs_adaptive_rate_per_call_cost"),
    ("model_failure_is_surprise",
     "A model's FAILED utterance or SURPRISING output — its prediction "
     "disagreeing with the agent's adaptive recognition, or with a known "
     "answer — is a SURPRISE signal, the same kind the surprise drive already "
     "processes. The model failing is INFORMATION about the model's limits, not "
     "noise to discard.",
     "Route a model failure/surprise into the surprise machinery. The handling "
     "is NOT to retrain (the agent does not train) but to: (a) record the "
     "model's limit, (b) fall back to the adaptive recognition for that "
     "utterance, (c) let the persistent-mismatch / feature-invention loop — "
     "which DOES adapt — carry the real learning. The model's surprise feeds the "
     "agent's ADAPTIVE core, never the frozen model.",
     "model_surprise_events_per_cycle"),
]


_MODEL_PRODUCTIONS = [
    ("Microtheory", "contains", "Concept",
     "model_understanding:mt_contains_concept"),
]


def install_model_understanding(substrate) -> dict:
    """Install the model_understanding Microtheory + its Concepts. Idempotent.
    Returns name → NodeID for the Mt and each concept."""
    for src_t, et, tgt_t, prov in _MODEL_PRODUCTIONS:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass

    mt = None
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == "model_understanding":
            mt = n
            break
    if mt is None:
        mt = substrate.add_node("Microtheory", {
            "name": "model_understanding",
            "description": (
                "What the agent knows about the MODELS it authors: they are "
                "static (do not adapt — the agent authors, it does not train), "
                "they have a cost to balance, and their failures/surprises are "
                "handled via the surprise machinery + the adaptive core, not by "
                "retraining the frozen model."),
            "origin": "model_understanding",
        })

    out = {"_mt": mt}
    for name, desc, rule, indicator in _MODEL_CONCEPTS:
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
                "origin": "model_understanding",
            })
        else:
            substrate.set_attr(cid, "description", desc)
            substrate.set_attr(cid, "rule", rule)
            substrate.set_attr(cid, "indicator", indicator)
        if cid not in substrate.neighbours(mt, "contains"):
            try:
                substrate.add_edge(mt, "contains", cid)
            except Exception:
                pass
        out[name] = cid
    return out


__all__ = ["install_model_understanding", "_MODEL_CONCEPTS"]
