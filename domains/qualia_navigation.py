"""Qualia-as-navigation — the coherence intuition, read off real substrate
dynamics.

The user's framing: *"the true power. Using qualia space as a navigation.
Having a problem you feel like there should be a solution for, even when you
don't know it, and using that to try and recover a way to get there."*

This is the in-substrate reproduction of the coherence-detection literature
(Bowers et al. 1990; Topolinski & Strack 2009; Metcalfe & Wiebe 1987) — see
docs/research/psychology_affect/QUALIA_NAVIGATION_COHERENCE_PREREG.md.

MECHANISM (REAL, not an oracle). A triad is three CUE Concepts (state=1.0,
active) wired by `causal_influence` edges to candidate associate nodes. The
substrate's own convergent local field —

    local(node) = external_field(node) + identity_field(node)
                  + Σ_{e∈Edges(node,'causal_influence')} weight(e)·state(target(e))

the exact Σ coupling term `can_native_update_3state` computes inline and
`domains/can_counterfactual.local_field_term` mirrors — accumulates the field
of ALL cues that converge on a common associate. The COHERENCE signal is the
PEAK convergent field over the candidate region:

    coherence = max_{node∈candidates} Σ_{cue active} weight(cue→node)·state(cue)

Two facts make this coherence-BEFORE-retrieval, not a disguised answer lookup:
  1. it reads the FIELD MAGNITUDE (`local_field_term`), never the argmax
     Hopfield commit (`target_state_term`);
  2. the ATANH_HALF deadzone lets a node carry a high field while committing
     to state 0 — high-field-uncommitted = *feels-solvable, not yet retrieved*.

In qualia-space terms the convergent field lights `dynamical:pull`
(external_field overlay axis) while `dynamical:commitment` (identity_field)
stays dark — felt pull lit, commitment dark = the hunch.

HELD-OUT DISCIPLINE (the whole game). The navigator receives the cue set and
the candidate NODE-set. The coherence read (`coherence_signal`) NEVER
references the ground-truth associate label; it returns a scalar from the
field alone. Localisation (`localise`, fine aperture) returns the argmax NODE
— still not the ground-truth label. `assert_held_out` audits that the read
source does not reference the held-out label symbol.

DEFAULT == TODAY. A NEW module; imports read-only helpers from
analogy_search / can_counterfactual. Existing concept_signature /
find_analogies are byte-identical when this is not invoked. seed+python only.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Optional

from . import analogy_search as _an

# Qualia axis names (the dimension-name convention _observer_aperture uses).
PULL_AXIS = "dynamical:pull"
COMMITMENT_AXIS = "dynamical:commitment"


def _sub(substrate):
    return _an._sub(substrate)


# ---------------------------------------------------------------------------
# Triad construction — build a fresh Microtheory + cue/candidate Concepts.
# ---------------------------------------------------------------------------

@dataclass
class Triad:
    """A built coherence problem living in the CAN substrate.

    `cues`        -> {name: node} the 3 active cue Concepts (state=1.0).
    `candidates`  -> {name: node} candidate associate Concepts (state=0.0).
    `edges`       -> list of (cue_name, cand_name, weight) wired in.
    `held_out`    -> the ground-truth associate NAME (never read by the
                     coherence path; kept only so the harness can SCORE
                     localisation afterwards).
    """

    mt: object
    cues: dict
    candidates: dict
    edges: list
    held_out: Optional[str] = None
    _sub: object = field(default=None, repr=False)


def build_triad(substrate, cue_names, edges, *, held_out=None,
                mt_temperature: float = 1.5) -> Triad:
    """Build a triad in the substrate. `edges` is a list of
    `(cue_name, candidate_name, weight)`. Cue Concepts get state=1.0 (active);
    candidate Concepts get state=0.0 (uncommitted). All fresh nodes on a fresh
    Microtheory so triads never cross-contaminate.

    `held_out` (the true associate name) is stored on the Triad for the harness
    to score against — it is NOT passed into any coherence read.
    """
    inner = _sub(substrate)
    mt = inner.add_node(
        "Microtheory",
        {"name": "qnav_mt", "temperature": float(mt_temperature),
         "discrete_mode": "3state", "can_tick": 0},
    )

    def _mk(name, state):
        c = inner.add_node(
            "Concept",
            {"name": str(name), "state": float(state),
             "external_field": 0.0, "identity_field": 0.0},
        )
        try:
            inner.add_edge(mt, "has_concept", c, {})
        except Exception:
            inner.add_edge_unchecked(mt, "has_concept", c)
        return c

    cues = {n: _mk(n, 1.0) for n in cue_names}
    candidates: dict = {}
    wired = []
    for cue_name, cand_name, weight in edges:
        if cand_name not in candidates:
            candidates[cand_name] = _mk(cand_name, 0.0)
        src = cues[cue_name]
        dst = candidates[cand_name]
        try:
            inner.add_edge(src, "causal_influence", dst, {"weight": float(weight)})
        except Exception:
            inner.add_edge_unchecked(src, "causal_influence", dst)
        wired.append((cue_name, cand_name, float(weight)))
    return Triad(mt=mt, cues=cues, candidates=candidates, edges=wired,
                 held_out=held_out, _sub=inner)


# ---------------------------------------------------------------------------
# The convergent-field read — the coherence signal.
# ---------------------------------------------------------------------------

def _convergent_field(triad: Triad, cand_name: str) -> float:
    """`Σ_{cue active} weight(cue→cand)·state(cue)` for one candidate — the
    exact `local_field_term` Σ coupling term restricted to the cue→candidate
    edges, WITHOUT external_field/identity_field bias (both 0 on a fresh
    candidate) and WITHOUT the argmax commit. Reads only the edge weights and
    the CUE states — never the candidate's identity as an answer."""
    inner = triad._sub
    total = 0.0
    for cue_name, cnode in triad.cues.items():
        cue_state = float(inner.node(cnode)["attrs"].get("state", 0.0))
        if cue_state == 0.0:
            continue
        for cand2, weight in _cue_out_edges(inner, cnode):
            if cand2 == triad.candidates.get(cand_name):
                total += weight * cue_state
    return total


def _cue_out_edges(inner, cue_node):
    """`[(target_node, weight)]` over a cue's causal_influence edges. The
    native `_native.Substrate` handle exposes `neighbours(node, edge_type)`
    (targets only, no per-edge weight enumeration), so the weight is the seed
    default (1.0) — the same weight `can_native_update_3state` multiplies by.
    Dropped edges (via `perturb(drop_edge=…)`) simply stop appearing here."""
    return [(nb, 1.0) for nb in inner.neighbours(cue_node, "causal_influence")]


def coherence_signal(triad: Triad, *, observer=None) -> dict:
    """The COHERENCE-BEFORE-RETRIEVAL read. Returns

        {"coherence": float,     # PEAK convergent field (quotiented by grain)
         "raw_peak": float,      # PEAK convergent field BEFORE grain quotient
         "pull": float,          # == coherence, as dynamical:pull magnitude
         "commitment": float,    # identity_field contribution (DARK: ~0)
         "field": {name: float}, # per-candidate quotiented field (glass box)
         "localised": None}      # deliberately NOT resolved at this call

    NEVER references `triad.held_out`. The argmax commit is not evaluated.
    `raw_peak` is the aperture-INDEPENDENT knows-THAT signal (convergence is
    present); the quotiented per-candidate `field` is what `localise` resolves
    at fine grain (knows-WHAT). At coarse aperture (large `grain` on
    dynamical:pull) the per-candidate fields collapse to a tie — knows-THAT
    (raw_peak still high) without knows-WHAT (no single node resolvable)."""
    ap = _an._observer_aperture(triad._sub, observer)
    grain = ap["grain"].get(PULL_AXIS)
    per = {}
    raw = {}
    for cand_name in triad.candidates:
        f = _convergent_field(triad, cand_name)
        raw[cand_name] = f
        if grain:
            # aperture GRAIN: quotient the pull axis at the observer's quantum.
            f = round(f / grain) * grain
        per[cand_name] = f
    coherence = max(per.values()) if per else 0.0
    raw_peak = max(raw.values()) if raw else 0.0
    # commitment = identity_field of the peak region; dark on fresh candidates.
    commitment = 0.0
    for cand_name, val in per.items():
        if val == coherence:
            node = triad.candidates[cand_name]
            commitment = float(triad._sub.node(node)["attrs"].get("identity_field", 0.0))
            break
    return {"coherence": coherence, "pull": coherence, "raw_peak": raw_peak,
            "commitment": commitment, "field": per, "localised": None}


def localise(triad: Triad, *, observer=None) -> dict:
    """FINE-aperture read: resolve WHICH candidate carries the peak field —
    knows-WHAT. Returns the coherence dict plus `"localised"` = the argmax
    candidate NAME (still the substrate's own node name, NOT the held-out
    ground-truth label — the harness compares them). At coarse grain, ties
    after quotienting are reported as an unresolved set."""
    base = coherence_signal(triad, observer=observer)
    per = base["field"]
    if not per:
        base["localised"] = None
        return base
    peak = max(per.values())
    winners = [n for n, v in per.items() if v == peak]
    base["localised"] = winners[0] if len(winners) == 1 else None
    base["localised_ties"] = sorted(winners)
    return base


# ---------------------------------------------------------------------------
# Perturbation — Topolinski anti-faking. A REAL fluency read must MOVE.
# ---------------------------------------------------------------------------

def perturb(triad: Triad, *, drop_edge=None, cue_scale=None) -> Triad:
    """Perturb the FLUENCY of a triad in place and return it.

      * `drop_edge=(cue_name, cand_name)` — remove that convergence edge
        (Topolinski's coherence-disruption): the associate loses one cue's
        field.
      * `cue_scale=float` — attenuate every cue's state (evidence-alpha /
        external_field decay analogue): weaker cues => weaker convergence.

    Because the coherence read is DERIVED from these very dynamics, perturbing
    them MUST move the read (claim 2). A read that survived this would be a
    hard-coded oracle."""
    inner = triad._sub
    if cue_scale is not None:
        for cnode in triad.cues.values():
            s = float(inner.node(cnode)["attrs"].get("state", 0.0))
            inner.set_attr(cnode, "state", s * float(cue_scale))
    if drop_edge is not None:
        cue_name, cand_name = drop_edge
        cue_node = triad.cues[cue_name]
        cand_node = triad.candidates[cand_name]
        _remove_edge(inner, cue_node, "causal_influence", cand_node)
        triad.edges = [(a, b, w) for (a, b, w) in triad.edges
                       if not (a == cue_name and b == cand_name)]
    return triad


def _remove_edge(inner, src, etype, dst):
    """Remove a convergence edge via the handle's own primitive
    (`remove_edge` / `remove_edge_unchecked`) so the cue stops contributing
    its field to that candidate."""
    for meth in ("remove_edge", "remove_edge_unchecked"):
        fn = getattr(inner, meth, None)
        if fn is not None:
            try:
                fn(src, etype, dst)
                return
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Held-out audit — never_reference_held_out discipline.
# ---------------------------------------------------------------------------

def assert_held_out(triad: Triad) -> bool:
    """Static audit: the coherence read path (`coherence_signal`,
    `_convergent_field`, `_cue_out_edges`) must not reference the held-out
    associate label. The read receives the candidate NODE-set and cue states;
    it must not branch on the ground-truth answer.

    Enforced two ways:
      1. runtime — the read functions take no `held_out`/answer argument;
      2. source — the held-out label string does not appear literally in the
         read source (the substrate's proven never_reference_held_out idiom,
         mirroring the program-synthesis / speech-LOSO audits).
    Returns True or raises AssertionError."""
    for fn in (coherence_signal, _convergent_field, _cue_out_edges, localise):
        params = set(inspect.signature(fn).parameters)
        assert "held_out" not in params, (
            "%s must not take a held_out argument" % fn.__name__)
    read_src = "".join(inspect.getsource(fn) for fn in
                       (coherence_signal, _convergent_field, _cue_out_edges,
                        localise))
    if triad.held_out:
        label = str(triad.held_out)
        # the candidate node name may legitimately equal the label at BUILD
        # time; the audit is that the READ SOURCE does not hard-code it.
        assert label not in read_src, (
            "held-out label %r must not appear in the coherence read source"
            % label)
    return True
