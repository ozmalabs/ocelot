"""grounding_repair — THE COMMUNICATION LOOP BECOMES A DIALOGUE. Interactive grounding + repair:
the speaker holds a BELIEF over the audience and UPDATES it from decode-failure feedback, building
common ground turn by turn (Clark & Brennan; least collaborative effort). donkey=0, earn-not-borrow,
graph-native.

THE ARC SO FAR (reuse, do NOT re-derive):
  * LISTENER          = analysis-by-synthesis (domains/analysis_by_synthesis).
  * cost-minimal SPEAKER = writer-physics effort (domains/earned_augmentation.motor_stats).
  * SPEAKER-MODELS-LISTENER = pragmatic midpoint J = ListenerRecovery - lambda*ProductionCost, a
    held Argmax-of-Plus Term over a cheap->explicit terseness spectrum (domains/pragmatic_speaker).
  * SHARED CONTEXT    = Bayesian message prior; recovery = held posterior P(true|signal,context) =
    softmax_c[Log(lik_c)+Log(prior_c)]; terseness RISES with prior peakedness (context_prior_speaker).
  * AUDIENCE MISJUDGMENT = pick terseness vs an ASSUMED peakedness p_assume; recovery scored under
    the TRUE p_true; over-estimate -> failed comms, under-estimate -> wasted effort; the one-sided
    cost asymmetry derives "be more explicit for a wide/uncertain audience" (audience_misjudgment).

THE NEW REALISM (this module). Until now the audience estimate was a FIXED (possibly wrong) guess.
Make it a DIALOGUE that builds common ground. The speaker holds a BELIEF = a distribution b over a
grid of candidate audience peakednesses p_true. Per turn, for the current referent:

  1 PRODUCE: p_assume = the belief's MAP (or expected) peakedness; the speaker picks terseness for
    THAT via the held pragmatic Term (pragmatic_speaker.choose_encoding against parametric_prior(
    p_assume)). Higher believed peakedness -> terser signal.
  2 DECODE: the audience recovers under its TRUE prior (held Bayes posterior, context_prior_speaker).
    recovery >= SUCCESS_THRESHOLD -> grounded; else FAILURE.
  3 REPAIR + UPDATE: on FAILURE the audience emits a repair signal (decode failed). The speaker does
    a HELD BAYESIAN belief update over the p_true grid given the observed outcome:
        log b'(p_true) = log b(p_true) + log P(outcome | p_assume, p_true)        (held Term)
    The OUTCOME LIKELIHOOD is the held render-compare/Bayes machinery itself: P(fail | p_assume,
    p_true) is high when p_true < p_assume (the audience had LESS shared context than assumed -> the
    chosen terse signal under-determines the message). So a FAILURE shifts mass to LOWER p_true ->
    next turn's MAP is lower -> the re-produced signal is MORE EXPLICIT. A SUCCESS shifts mass to
    p_true >= p_assume (consistent with what got through).
  4 REPEAT until success or a turn budget; then move to the NEXT referent. The UPDATED belief CARRIES
    FORWARD — common ground accumulates (later referents start terser, need fewer repairs).

WHAT IS HELD / EARNED (donkey=0):
  * terseness re-choice each turn        = the held pragmatic-speaker Argmax Term.
  * recovery under the true prior         = the held Bayes-posterior recovery Term.
  * the BELIEF UPDATE (log b + log-likelihood -> normalise) = a NEW held graph Term here, the SAME
    Log+Plus+Exp+Sum+Div+Argmax machinery context_prior_speaker uses for the posterior, applied over
    the candidate-p_true set. The MAP read-back = a held Argmax Term.
  * the outcome likelihood P(outcome | p_assume, p_true) = derived from the held Bayes recovery the
    audience would give (a sigmoid of recovery-vs-threshold), NOT a hand-tuned table.
  * likelihood (signal recognition) = held AbS render-compare + from-scratch learned head, NO
    borrowed weights. 0 LLM, 0 borrowed weights at any decision. numpy = adapter marshalling only.

THE PREDICTIONS (gated in scripts/grounding_repair_gate.py):
  1 CONVERGENCE / REPAIR: from a MISCALIBRATED (over-confident) start, belief error |MAP - p_true|
    shrinks monotonically and recovery crosses the threshold within a few turns.
  2 LEAST COLLABORATIVE EFFORT: the dialogue converges to the CALIBRATED terseness (oracle p_assume
    == p_true), not stuck over-explicit; grounding beats both a NO-FEEDBACK speaker (wrong estimate)
    and an ALWAYS-EXPLICIT speaker on the joint objective over a multi-referent dialogue.
  3 COMMON GROUND GROWS: terseness rises / repair-turns fall across referents (memory carries) vs a
    FLAT memoryless control.
  4 DISCRIMINATIVE: a SHUFFLED/uninformative repair signal does NOT drive convergence; a
    WRONG-DIRECTION update (treats failure as 'be terser') DIVERGES.
"""
from __future__ import annotations
import numpy as _np
import substrate_rs as _srs
import domains.native_fusion as _nf
import domains.pragmatic_speaker as _PS
import domains.context_prior_speaker as _CP
import domains.audience_misjudgment as _AM

_L = lambda v: {"type": "Lit", "value": v}

# Per-candidate (p_true grid) graph attrs for the held belief-update Term.
BELIEF_ATTR = "log_belief"   # current log belief b(p_true) for this candidate (un-normalised ok)
LOGLIK_ATTR = "log_lik"      # log P(observed outcome | p_assume, this candidate p_true)
CAND_ATTR = "is_pt"          # candidate-p_true marker (== 1.0)
PEAK_ATTR = "pt_peak"        # the candidate's p_true peakedness value (read back at the MAP)
_EPS = 1e-12


def _Log(a):  return {"type": "Log", "arg": a}
def _Exp(a):  return {"type": "Exp", "arg": a}


# --------------------------------------------------------------------------- #
#  THE HELD BAYESIAN BELIEF-UPDATE TERM over the candidate-p_true set.
#    log b'(p) = log b(p) + log P(outcome | p_assume, p)        (additive log-domain combine)
#    b'(p)     = exp(log b'(p)) / Sum_q exp(log b'(q))          (Exp / Sum / Div, all native)
#  The MAP read-back = Argmax over candidates of the (un-normalised) log posterior. Same Log+Plus+
#  Exp+Sum+Div+Argmax machinery context_prior_speaker.posterior_recovery_term uses — reused, no new
#  primitive. Python only marshals the prior log-belief + per-candidate outcome log-likelihood.
# --------------------------------------------------------------------------- #

def _cand_set():
    return _nf._NodesWhere("Concept", CAND_ATTR, _L(1.0))


def _logpost(var_name: str) -> dict:
    """log b'(p) = log b(p) + log P(outcome | p_assume, p) — the held additive Bayes combine over
    the p_true grid (prior belief x outcome likelihood, log-domain). Identical shape to the message
    posterior's Log(lik)+Log(prior); here the 'prior' is the carried belief and the 'likelihood' is
    the held outcome likelihood."""
    return _nf._Plus([
        _nf._Attr(_nf._V(var_name), BELIEF_ATTR),   # log b(p) (carried belief = common ground so far)
        _nf._Attr(_nf._V(var_name), LOGLIK_ATTR),   # log P(outcome | p_assume, p) (held feedback)
    ])


def _posterior_prob(var_name: str) -> dict:
    """Normalised posterior belief b'(p) = exp(logpost(p)) / Sum_q exp(logpost(q)) for the candidate
    bound to var_name — a held Div of Exp(logpost) by the native Sum of Exp(logpost) over the set."""
    den = _nf._Sum(_cand_set(), "_q", _Exp(_logpost("_q")))
    return _nf._Div(_Exp(_logpost(var_name)), den)


def map_term() -> dict:
    """The held belief MAP: Argmax over the p_true grid of the (un-normalised) log posterior — the
    most-believed audience peakedness after the update. (Argmax is monotone under the shared
    normaliser, so the un-normalised logpost suffices; same Argmax-of-score shape as the speaker.)"""
    return _nf._Argmax(_cand_set(), "w", _logpost("w"))


# --------------------------------------------------------------------------- #
#  WORLD-ADAPTER GLUE — feed the carried log-belief + per-candidate outcome log-likelihood,
#  evaluate the held update Term, read back the new (normalised) belief + its MAP. NO decision here.
# --------------------------------------------------------------------------- #

def _build(Substrate, grid, log_belief, log_lik):
    s = Substrate()
    nodes = []
    for i, pk in enumerate(grid):
        nid = s.add_node("Concept", {"idx": float(i)})
        s.set_attr(nid, CAND_ATTR, 1.0)
        s.set_attr(nid, PEAK_ATTR, float(pk))
        s.set_attr(nid, BELIEF_ATTR, float(log_belief[i]))
        s.set_attr(nid, LOGLIK_ATTR, float(log_lik[i]))
        nodes.append(nid)
    return s, nodes


def belief_update(Substrate, Pred, grid, log_belief, log_lik):
    """ONE held Bayesian belief update over the p_true grid: posterior log-belief and its MAP via the
    held Terms. Returns (new_log_belief, new_belief_prob, map_peak, map_idx). The combine
    (log b + log-lik -> normalise -> MAP) is native; Python only marshals in/out."""
    s, nodes = _build(Substrate, grid, log_belief, log_lik)
    probs = [float(s.evaluate(Pred(_posterior_prob("c")), {"c": nid})) for nid in nodes]
    # un-normalised log posterior is what the MAP Argmax reads; recover it for carry-forward, then
    # re-centre (subtract max) for numerical safety so it stays an honest carried log-belief.
    new_logb = _np.array([log_belief[i] + log_lik[i] for i in range(len(grid))], float)
    new_logb = new_logb - new_logb.max()
    pick = s.evaluate(Pred(map_term()), {})
    midx = int(round(s.node(pick)["attrs"]["idx"]))
    return new_logb.tolist(), probs, float(grid[midx]), midx


def belief_map(Substrate, Pred, grid, log_belief):
    """The MAP of a belief with NO new evidence (zero log-likelihood) — used to read the speaker's
    current assumed-peakedness before producing a signal. Held Argmax Term."""
    _, _, mp, mi = belief_update(Substrate, Pred, grid, log_belief, [0.0] * len(grid))
    return mp, mi


def belief_expected(grid, log_belief):
    """The belief's EXPECTED peakedness E_b[p] (a softer estimate than the MAP). Plain read-back of
    the normalised belief; the gate uses the MAP for the produced signal but reports this too."""
    lb = _np.asarray(log_belief, float)
    w = _np.exp(lb - lb.max()); w = w / (w.sum() + _EPS)
    return float(_np.dot(w, grid))


# --------------------------------------------------------------------------- #
#  THE OUTCOME LIKELIHOOD  P(observed outcome | p_assume, candidate p_true)  — HELD, not tabulated.
#  The audience would recover the message with the held Bayes recovery r(p_assume, p_true) (the
#  speaker is too terse when p_true < p_assume). Model the observed binary outcome as a Bernoulli
#  whose success prob is a steep sigmoid of (recovery - threshold): success likely iff recovery clears
#  the threshold. So:
#     P(success | p_assume, p) = sigmoid(beta * (r(p_assume, p) - thr))
#     P(failure | p_assume, p) = 1 - that.
#  r(p_assume, p) is the SAME held render-compare/Bayes recovery the audience uses (precomputed per
#  cell by the gate). This makes the feedback GENUINE: a failure is only informative because it
#  reflects the real held recovery surface. numpy = sigmoid marshalling only.
# --------------------------------------------------------------------------- #

def outcome_loglik(recoveries_over_grid, observed_success: bool, thr: float, beta: float = 25.0):
    """log P(observed outcome | p_assume, p_true) for every candidate p_true on the grid, from the
    held recovery r(p_assume, p_true) the audience would give at the speaker's CURRENT p_assume.
    `recoveries_over_grid[k]` = held Bayes recovery if the true peakedness were grid[k] (signal fixed
    at the chosen terseness). observed_success = did THIS turn's real decode (under the actual p_true)
    succeed. Returns a log-likelihood vector over the grid. Genuine feedback: the shape comes from the
    held recovery surface, so an UNINFORMATIVE/shuffled outcome carries no consistent gradient."""
    r = _np.asarray(recoveries_over_grid, float)
    p_succ = 1.0 / (1.0 + _np.exp(-beta * (r - thr)))
    p_succ = _np.clip(p_succ, _EPS, 1.0 - _EPS)
    p = p_succ if observed_success else (1.0 - p_succ)
    return _np.log(p).tolist()


def outcome_loglik_wrongdir(recoveries_over_grid, observed_success: bool, thr: float,
                            beta: float = 25.0):
    """DISCRIMINATIVE control: the WRONG-DIRECTION update — treat the outcome with the likelihood
    INVERTED (a failure is read as evidence for HIGH recovery = 'be terser'). Swaps success/failure
    in the Bernoulli. The held update machinery is identical; only the (wrong) likelihood differs, so
    the belief should DIVERGE (move AWAY from p_true) — proving the real update uses the signal
    correctly."""
    return outcome_loglik(recoveries_over_grid, not observed_success, thr, beta)


__all__ = [
    "BELIEF_ATTR", "LOGLIK_ATTR", "CAND_ATTR", "PEAK_ATTR",
    "map_term", "belief_update", "belief_map", "belief_expected",
    "outcome_loglik", "outcome_loglik_wrongdir",
]
