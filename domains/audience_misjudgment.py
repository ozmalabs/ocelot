"""audience_misjudgment — THE AUDIENCE-PRIOR MISJUDGMENT PENALTY (the "wider audience" half of the
communication loop). donkey=0, earn-not-borrow, graph-native.

THE ARC SO FAR (do not re-derive; reuse, don't duplicate):
  * LISTENER = analysis-by-synthesis (domains/analysis_by_synthesis).
  * cost-minimal SPEAKER = writer-physics effort (domains/earned_augmentation.motor_stats).
  * SPEAKER-MODELS-LISTENER = the pragmatic midpoint J = ListenerRecovery - lambda*ProductionCost,
    a held Argmax-of-Plus Term over a cheap->explicit spectrum (domains/pragmatic_speaker).
  * SHARED CONTEXT = a Bayesian message prior; recovery = held-Term posterior
    P(true | signal, context) = softmax_c[Log(lik_c)+Log(prior_c)]; chosen terseness RISES with
    prior peakedness (domains/context_prior_speaker).

THE NEW REALISM (this module). Until now the speaker knew the TRUE message prior. Make it realistic:
the speaker has only a BELIEF about the audience's prior and picks terseness for its ASSUMED
peakedness; recovery is then evaluated under the audience's TRUE prior. MISJUDGMENT = the mismatch.

  * TRUE audience prior   = parametric_prior at p_true  (reuse context_prior_speaker).
  * ASSUMED prior         = parametric_prior at p_assume (same construction, assumed peakedness).
  * the SPEAKER picks terseness = the held pragmatic-midpoint argmax computed AGAINST the ASSUMED
    prior (it optimizes for what it THINKS the audience knows) — pragmatic_speaker.choose_encoding
    on recoveries computed under the ASSUMED prior.
  * the OUTCOME = actual recovery (held Bayes posterior under the TRUE prior) + actual production
    cost of the chosen signal. MISJUDGMENT LOSS = the joint-objective shortfall vs the CALIBRATED
    (p_assume == p_true) optimum.

THE PREDICTIONS (the heart):
  1 OVER-ESTIMATION (p_assume > p_true): speaker assumes MORE shared context than the audience has,
    is TOO TERSE -> recovery COLLAPSES (curse-of-knowledge). Steep penalty.
  2 UNDER-ESTIMATION (p_assume < p_true): assumes LESS, is OVER-EXPLICIT -> recovery fine but
    production effort WASTED. Mild penalty (wasted bits, not failed comms).
  3 ASYMMETRY: over-estimation loss >> under-estimation loss. Therefore under UNCERTAINTY about the
    audience (a DISTRIBUTION over p_true = a "wide audience"), the robust speaker should BIAS toward
    UNDER-estimating shared context = be MORE EXPLICIT. The optimal assumed-peakedness under audience
    uncertainty is SHIFTED BELOW the mean true peakedness — "select a midpoint for a wider audience"
    EMERGES from the asymmetric penalty, not stipulated.

WHAT IS HELD / EARNED (donkey=0):
  * the per-(p_assume) terseness choice = the held pragmatic-speaker Term (pragmatic_speaker.choose_term).
  * the actual recovery under the true prior = the held Bayes-posterior Term (context_prior_speaker).
  * the LOSS and the ROBUST argmax under audience uncertainty = NEW held graph Terms here (Argmax /
    Sum / Plus / Times / Minus over candidate p_assume of expected J across the audience distribution).
  * 0 LLM, 0 borrowed weights at any decision. numpy = adapter marshalling only.
"""
from __future__ import annotations
import numpy as _np
import substrate_rs as _srs
import domains.native_fusion as _nf
import domains.pragmatic_speaker as _PS
import domains.context_prior_speaker as _CP

_L = lambda v: {"type": "Lit", "value": v}

# Per-(p_assume) candidate graph attrs for the robust-argmax Term.
ASSUME_ATTR = "is_assume"   # candidate assumed-peakedness marker (== 1.0)
EJ_ATTR = "exp_joint"       # expected joint objective of this p_assume across the audience dist
PEAK_ATTR = "assume_peak"   # the candidate's assumed peakedness (read back at the argmax)


# --------------------------------------------------------------------------- #
#  CALIBRATED / MISJUDGED OUTCOME for one (target, p_assume, p_true).
#  All decisions are held Terms; this is world-adapter glue around them.
# --------------------------------------------------------------------------- #

def _norm_range(x):
    x = _np.asarray(x, float)
    lo, hi = x.min(), x.max()
    return (x - lo) / (hi - lo + 1e-9)


def outcome(Substrate, Pred, liks, costs, ts, nbr, p_assume, p_true, true_idx, lam,
            n_cand=20):
    """The realistic speaker for ONE target: pick terseness against the ASSUMED prior (held
    pragmatic-speaker Term), then evaluate recovery + cost under the TRUE prior.

      assumed prior  = parametric_prior(p_assume) ; true prior = parametric_prior(p_true).
      speaker recoveries-for-choice = held Bayes posterior under the ASSUMED prior, per rung.
      chosen rung    = held choose_encoding (Argmax of recovery_assumed - lambda*cost_norm).
      ACTUAL recovery = held Bayes posterior of the CHOSEN rung's likelihood under the TRUE prior.
      ACTUAL cost     = the chosen rung's held writer-physics production cost.

    Returns (chosen_terseness, actual_recovery, actual_cost_norm, chosen_idx). cost is range-
    normalised over THIS target's rungs (same as the speaker uses) so J is comparable across
    p_assume for this target."""
    pri_assume = _CP.parametric_prior(n_cand, true_idx, p_assume, neighbour_idx=nbr)
    pri_true = _CP.parametric_prior(n_cand, true_idx, p_true, neighbour_idx=nbr)
    cn = _norm_range(costs)
    # recoveries the speaker BELIEVES it will get (under the assumed prior) — held Term per rung.
    recs_assumed = [_CP.posterior_recovery(Substrate, Pred, lik, pri_assume, true_idx)
                    for lik in liks]
    _, idx = _PS.choose_encoding(Substrate, Pred, ts, recs_assumed, cn, lam)
    # ACTUAL recovery under the TRUE prior at the chosen rung — held Bayes Term.
    actual_rec = _CP.posterior_recovery(Substrate, Pred, liks[idx], pri_true, true_idx)
    return float(ts[idx]), float(actual_rec), float(cn[idx]), int(idx)


def joint(actual_rec, actual_cost_norm, lam):
    """The realised joint objective J = recovery_under_true_prior - lambda*cost_norm. (A plain
    scalar read-back of the held outcome; the per-p_assume argmax over these is the held Term below.)"""
    return float(actual_rec) - float(lam) * float(actual_cost_norm)


# --------------------------------------------------------------------------- #
#  THE TWO CURRENCIES OF MISJUDGMENT (the creator's framing, made explicit).
#  A misjudgment costs in TWO distinct currencies:
#    * recovery SHORTFALL — the message did not get through (FAILED COMMUNICATION). This is what
#      OVER-estimation (too terse for the real audience) incurs.
#    * cost EXCESS        — effort spent that the audience did not need (WASTED EFFORT). This is what
#      UNDER-estimation (over-explicit) incurs.
#  These are NOT the same currency: a failed message must be repaired/repeated (catastrophic), wasted
#  bits are merely inefficient. The asymmetry weight w_comm > w_effort encodes "failed comms is worse
#  than wasted effort". The objective is then J_asym = w_comm*recovery - w_effort*cost — a held Term.
# --------------------------------------------------------------------------- #

def joint_asym(actual_rec, actual_cost_norm, w_comm, w_effort):
    """The two-currency objective J = w_comm*recovery - w_effort*cost. w_comm > w_effort makes a unit
    of failed communication cost more than a unit of wasted effort — the creator's asymmetry. (Scalar
    read-back; the held expected-J argmax below operates on these per-cell values.)"""
    return float(w_comm) * float(actual_rec) - float(w_effort) * float(actual_cost_norm)


# --------------------------------------------------------------------------- #
#  THE ROBUST-ARGMAX-UNDER-AUDIENCE-UNCERTAINTY TERM (held graph Term).
#  Wide audience = a DISTRIBUTION over p_true (weights a_k on grid p_true_k). For each candidate
#  p_assume we have already computed (held) the realised J(p_assume, p_true_k). The expected joint
#  objective is E_k[ J ] = Sum_k a_k * J(p_assume, p_true_k); the ROBUST p_assume = Argmax over the
#  p_assume candidates of that expectation. Both the expectation (Sum of Times) and the Argmax are
#  native Terms — Python only marshals the precomputed per-cell J as attrs.
# --------------------------------------------------------------------------- #

def _assume_set():
    return _nf._NodesWhere("Concept", ASSUME_ATTR, _L(1.0))


def _expected_joint_score(var_name: str, n_true: int) -> dict:
    """E_k[J] = Sum_k weight_k * J_k for the p_assume candidate bound to `var_name`, as a held Plus
    of Times over the audience grid: the grid weights and the per-true-prior realised J are graph
    attrs (w0,j0,w1,j1,...) on the candidate node. A native sum-of-products (expectation) Term."""
    return _nf._Plus([
        _nf._Times([_nf._Attr(_nf._V(var_name), f"w{k}"), _nf._Attr(_nf._V(var_name), f"j{k}")])
        for k in range(n_true)
    ])


def robust_argmax_term(n_true: int) -> dict:
    """robust = Argmax over candidate p_assume of its expected joint objective across the audience
    distribution — the WHOLE 'pick the assumed-peakedness that maximises expected J over the wide
    audience' as ONE held graph Term (Argmax over the candidate set of the held expectation
    sum-of-products). Same Argmax-of-score shape the pragmatic speaker uses; no per-node manual
    evaluation, no env-bound node — fully self-contained over the candidate set."""
    return _nf._Argmax(_assume_set(), "a", _expected_joint_score("a", n_true))


def robust_assume(Substrate, Pred, assume_peaks, J_matrix, audience_weights):
    """Pick the ROBUST assumed-peakedness under a wide-audience distribution, via ONE held Term.

      assume_peaks    : grid of candidate p_assume values.
      J_matrix[a][k]  : realised joint objective if the speaker ASSUMES assume_peaks[a] and the TRUE
                        prior is true_grid[k] (precomputed via outcome()/joint(), averaged over
                        targets). Each entry is itself the output of the held outcome+Bayes Terms.
      audience_weights[k] : the wide-audience distribution over true_grid (sums to 1).

    Builds one Concept per p_assume carrying the audience weights + that row of J as attrs, then
    argmaxes the held expected-J Term over the candidate set. Returns
    (robust_peak, robust_idx, expected_J_per_assume)."""
    n_true = len(audience_weights)
    s = Substrate()
    nodes = []
    for a, pa in enumerate(assume_peaks):
        nid = s.add_node("Concept", {"idx": float(a)})
        s.set_attr(nid, ASSUME_ATTR, 1.0)
        s.set_attr(nid, PEAK_ATTR, float(pa))
        for k in range(n_true):
            s.set_attr(nid, f"w{k}", float(audience_weights[k]))
            s.set_attr(nid, f"j{k}", float(J_matrix[a][k]))
        nodes.append(nid)
    pick = s.evaluate(Pred(robust_argmax_term(n_true)), {})
    ridx = int(round(s.node(pick)["attrs"]["idx"]))
    # expected J per candidate for reporting (the same held expectation, read per candidate).
    ej = [float(sum(audience_weights[k] * J_matrix[a][k] for k in range(n_true)))
          for a in range(len(assume_peaks))]
    return float(assume_peaks[ridx]), ridx, ej


__all__ = [
    "ASSUME_ATTR", "EJ_ATTR", "PEAK_ATTR",
    "outcome", "joint", "joint_asym",
    "robust_argmax_term", "robust_assume", "_norm_range",
]
