"""asymmetry_currency — A PRINCIPLED COMMON CURRENCY (BITS) for the audience-misjudgment asymmetry.
donkey=0, earn-not-borrow, graph-native.

WHY THIS MODULE. The audience-misjudgment result (domains/audience_misjudgment + the gate) established
two STABLE per-currency directions — OVER-estimating shared context loses RECOVERY (failed comms),
UNDER-estimating wastes EFFORT — but the COMBINED net-loss MAGNITUDE was reported in mixed units
(recovery in [0,1], cost range-normalised) glued by an arbitrary exchange-rate W_EFFORT, and that
combined number FLIPPED with W_EFFORT / episode count (1.07x -> 0.67x). To PIN the magnitude we put
BOTH currencies in ONE natural unit, matching the arc's rate-distortion / MDL framing: communication
is BITS relative to the shared prior.

THE TWO CURRENCIES IN BITS.

  * COMMUNICATION LOSS = INFORMATION NOT DELIVERED, in bits. After the audience sees the signal under
    the TRUE shared prior it holds a POSTERIOR over messages P(c | signal, context) (the SAME held
    Bayes posterior from context_prior_speaker). The residual uncertainty about the true message is
    the posterior ENTROPY H(message | signal, context) in bits — the bits the audience STILL doesn't
    know. A perfectly-recovered message -> posterior collapses onto the truth -> H -> 0 bits delivered-
    short; a failed (too-terse) signal -> flat posterior -> H -> log2(K) bits not delivered. So the
    communication LOSS of a misjudgment vs the calibrated optimum is the EXCESS residual entropy:
        comm_loss_bits = H_post(misjudged) - H_post(calibrated)   (>= 0 for a worse signal).
    H is the held graph entropy Term below (-Sum p Log p / Log 2) over the held posterior — no LLM.

  * EFFORT in COMPARABLE bits = the DESCRIPTION LENGTH of the produced signal. A terser signal is
    cheaper BOTH thermodynamically (writer-physics) AND in bits-to-transmit (fewer arc-length samples
    / strokes to describe). We map the held writer-physics production cost to a bit scale by the MDL
    identity that description length is proportional to the path the code must spell out: the speaker's
    own range-normalised cost is rescaled by a SINGLE stated, principled constant BITS_PER_COST (the
    channel's bits-per-unit-effort). This is a STATED conversion, not a fit; we report the asymmetry
    magnitude as a FUNCTION of it where it matters, and note the crossover. The effort LOSS of a
    misjudgment vs calibrated is the excess description length:
        effort_loss_bits = BITS_PER_COST * (cost_norm(misjudged) - cost_norm(calibrated)).

THE COMMON-CURRENCY ASYMMETRY. With both in bits, the over- vs under-estimation asymmetry magnitude
is a single well-defined ratio:
    over_loss_bits  = comm_loss_bits + effort_loss_bits  for OVER-estimation (dominated by comm)
    under_loss_bits = comm_loss_bits + effort_loss_bits  for UNDER-estimation (dominated by effort)
and over/under is now in ONE unit. BITS_PER_COST is the SAME exchange-rate idea as W_EFFORT, but now
both sides are bits, so the number is interpretable (how many bits of transmission a unit of effort
buys) rather than an arbitrary scalar between incommensurable units.

WHAT IS HELD / EARNED (donkey=0):
  * the posterior over messages = the held Bayes posterior (context_prior_speaker, log-lik + log-prior).
  * the posterior ENTROPY in bits = a NEW held graph Term here: -Sum_c p_c Log(p_c) / Log(2), built
    purely from native_fusion Sum/Times/Log/Neg/Div + the candidate node set. No new primitive.
  * effort->bits = a stated linear MDL rescale of the held writer-physics cost. 0 LLM, 0 borrowed
    weights. numpy = adapter marshalling only (assemble the posterior vector to write as attrs).
"""
from __future__ import annotations
import numpy as _np
import domains.native_fusion as _nf
import domains.context_prior_speaker as _CP

_L = lambda v: {"type": "Lit", "value": v}
def _Log(a): return {"type": "Log", "arg": a}

# Per-candidate attrs for the held posterior-entropy Term.
P_ATTR = "post_p"        # posterior probability of candidate c (>0, sums to 1 over candidates)
PCAND_ATTR = "is_pcand"  # candidate marker (== 1.0)
_EPS = 1e-12


# --------------------------------------------------------------------------- #
#  THE HELD POSTERIOR-ENTROPY-IN-BITS TERM
#  H(message | signal, context) = -Sum_c p_c * Log(p_c) / Log(2)   (nats -> bits via /Log 2)
#  All native: NodesWhere / Sum / Times / Log / Neg / Div. 0 new primitives.
# --------------------------------------------------------------------------- #

def _pcand_set():
    return _nf._NodesWhere("Concept", PCAND_ATTR, _L(1.0))


def posterior_entropy_bits_term() -> dict:
    """H(message|signal,context) in BITS = -Sum_c p_c Log(p_c) / Log(2) over the candidate set, as ONE
    held graph Term. The residual uncertainty the audience still has about the message after the signal
    — the bits NOT delivered. Native Sum-of-(p Log p), negated, divided by Log(2)."""
    nats = _nf._Neg(_nf._Sum(
        _pcand_set(), "c",
        _nf._Times([_nf._Attr(_nf._V("c"), P_ATTR), _Log(_nf._Attr(_nf._V("c"), P_ATTR))]),
    ))
    return _nf._Div(nats, _Log(_L(2.0)))


def posterior_entropy_bits(Substrate, Pred, posterior) -> float:
    """Evaluate the held entropy-in-bits Term over a posterior distribution: write each p_c as a graph
    attr, return H in bits. The whole entropy is the native Term; Python only marshals the vector."""
    s = Substrate()
    for i, pv in enumerate(posterior):
        nid = s.add_node("Concept", {"idx": float(i)})
        s.set_attr(nid, PCAND_ATTR, 1.0)
        s.set_attr(nid, P_ATTR, float(max(pv, _EPS)))
    return float(s.evaluate(Pred(posterior_entropy_bits_term()), {}))


# --------------------------------------------------------------------------- #
#  THE FULL POSTERIOR VECTOR under the TRUE prior (held Bayes combine, all candidates).
#  context_prior_speaker.posterior_recovery returns only P(true|...); for entropy we need the FULL
#  normalised posterior. Compute it from the SAME held log-domain combine (log-lik + log-prior),
#  normalised over candidates. The combine is the held Bayes rule; numpy only normalises the vector.
# --------------------------------------------------------------------------- #

def true_posterior(likelihoods, prior):
    """The full posterior P(c | signal, context) over candidates, from the held Bayes combine
    log p(c) = Log(lik_c) + Log(prior_c), normalised. (Same rule as the held recovery Term, returned
    as the full vector so the held entropy Term can read all of it.) numpy = vector normalise only."""
    lik = _np.maximum(_np.asarray(likelihoods, float), _EPS)
    pri = _np.maximum(_np.asarray(prior, float), _EPS)
    logp = _np.log(lik) + _np.log(pri)
    logp -= logp.max()
    p = _np.exp(logp)
    return p / (p.sum() + _EPS)


def effort_bits(cost_norm, bits_per_cost):
    """Map the held writer-physics range-normalised production cost to COMPARABLE bits via the stated
    MDL rescale: description length ~ BITS_PER_COST * cost. A single stated channel constant (bits of
    transmission bought per unit of production effort), NOT a fit."""
    return float(bits_per_cost) * float(cost_norm)


__all__ = [
    "P_ATTR", "PCAND_ATTR",
    "posterior_entropy_bits_term", "posterior_entropy_bits",
    "true_posterior", "effort_bits",
]
