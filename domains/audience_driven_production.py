"""audience_driven_production — the COMMUNICATION LOOP'S THIRD PIECE, GROUNDED. donkey=0,
earn-not-borrow, graph-native.

THE ARC SO FAR (reuse, do not re-derive):
  * pragmatic_speaker: J(rung) = ListenerRecovery(rung) - lambda*ProductionCost(rung), a held
    Argmax-of-Plus Term over a cheap->explicit spectrum (`choose_encoding`). The speaker-models-
    listener midpoint.
  * audience.py: a Scene/Party/Concept participation-framework graph + `knows`/`novelty` — theory-
    of-mind reads over a party's believed-knowledge set.
  * communicate.py: objective-driven utterance choice over conveyed-concept content.
  * system_model.model_system(agent, target={"kind":"foreign_snapshot", "graph": ...}): the NEW
    general grounded model of an ARBITRARY OTHER system, anchored via SensorAnchor + the installed
    `ReachableFrom(node, "grounded_in")` Term (domains/grounding_reach.py) — "I observed them," never
    "this is true on the target's own terms".

WHAT WAS MISSING (the creator's framing, memory ozma_two_model_communication): the pragmatic_speaker
arc's "audience model" was always a HAND-SET prior (parametric_prior / neighbour_prior — a knob the
Python adapter chose). This module GROUNDS it: the audience model consumed by the speaker's midpoint
choice is now a `system_model.model_system` result over the interlocutor's OBSERVED knowledge, so
"terse to a rich shared model" only fires when that model is a real observation, never a guess.

THE CONTRACT:
  * `audience_model(agent, interlocutor)` -> a bundle {grounded, id, known, system_model, graph,
    party, scene}. `interlocutor = {"id": str, "observed": bool, "known_concepts": [str, ...]}`.
    When `observed` is True, builds an `audience.py`-shaped Scene/Party/Concept graph carrying the
    OBSERVED known-concepts, snapshots it, and calls `system_model.model_system` with a
    `foreign_snapshot` target -> a `SensorAnchor`-grounded `SystemModel` (mechanical, verbatim
    reuse of the existing foreign-snapshot grounding path). When `observed` is False (a wide/unknown
    audience the agent never actually watched), NO system model is built at all -- the bundle carries
    `grounded=False`, `known=frozenset()`. This is the epistemic discipline: an unobserved audience
    contributes NOTHING to the shared-model credit, on purpose.

  * `residual_vs_audience(agent, meaning, audience)` -> {new, known, residual_frac}. The meaning's
    concepts (reuses `audience._concepts`, the SAME extractor `audience.novelty` is built on) split
    into `known` (the audience is credited with these ONLY when `audience['grounded']` is True --
    reuses `audience.knows` against the audience's OWN observed graph) vs `new` (the residual --
    what the signal must actually carry). Ungrounded audiences get residual == the FULL meaning:
    there is no observed basis to omit anything.

  * `select_utterance(agent, meaning, audience, lexicon, candidates=None, lam=0.35, n_rungs=5)` ->
    {utterance, terseness, grounded_used, ...}. UNGROUNDED audience -> hard fallback to the explicit
    rendering (no spectrum, no argmax -- the discipline is unconditional, not a soft preference).
    GROUNDED audience -> builds a cheap->explicit spectrum (rung 0 = fully explicit -- residual PLUS
    every already-known concept restated; last rung = fully terse -- residual only, known concepts
    dropped since the audience is credited with already having them) and picks the joint optimum via
    the SAME held Argmax-of-Plus Term `pragmatic_speaker.choose_encoding` runs for the handwriting
    arc (reused VERBATIM, no reimplementation -- `Substrate`/`Pred` are the same
    `substrate_rs.Substrate` / `many_settings_recognizer._Pred` wrapper every other module in this
    arc (audience_misjudgment, context_prior_speaker's callers, grounding_repair) already reuses).
    Every rung is actually RENDERED via `domains.language.produce` (the real per-concept leaf-
    production path, module untouched) so the selection yields a genuine utterance string, not a
    bare score.

WHAT IS NEW, THIN GLUE (own to this module, not a re-derivation of anything upstream):
  * the concept-set spectrum builder (`_spectrum`) — interpolates between "all known concepts
    restated" (rung 0) and "known concepts dropped" (last rung), by DROPPING known concepts in a
    fixed deterministic order as terseness rises. A direct textual analogue of
    `pragmatic_speaker.simplify_strokes`' "drop the least-salient marks" for STROKES, but there is
    no stroke geometry in text, so this module supplies its own (documented) knob.
  * `_render` — joins `language.produce` calls over the conveyed concept set (word count = the
    production-cost proxy; pragmatic_speaker's cost is pen-travel + jerk, which has no text analogue,
    so word count is this module's own honest stand-in, exactly flagged as adapter glue).
  * `_concepts_of` — a one-line dispatch so `meaning` may be given either as a flat concept
    collection (the shape `communicate.py`'s `choose()` already uses) or a nested meaning Term-tree
    (the shape `audience._concepts` / `language.produce` already parse); both paths land on
    `audience._concepts` (reused, not reimplemented) for the tree case.

numpy USAGE (flagged): adapter math only -- linspace over the spectrum, min-max cost normalisation
(reuses `domains.audience_misjudgment._norm_range` verbatim, the SAME helper `outcome()` already
range-normalises production cost with). The DECISION (which rung wins) is the held Argmax-of-Plus
Term evaluated in Rust via `pragmatic_speaker.choose_encoding`; this module never picks a rung in
Python once the audience is grounded -- it only marshals rungs in and reads the winner back out.

FOR THE FOLLOW-ON (an agent-authored produce-for-audience RULE): this module intentionally stops at
"Python glue that calls the held Terms" -- exactly at the same altitude as pragmatic_speaker.py /
audience_misjudgment.py / grounding_repair.py, which the arc has always left as Python callable
machinery for a scripted gate. A follow-on that wants the JABBERWOCK to make this call as an
authored Rule (not a scripted Python call) should treat `audience_model` + `residual_vs_audience` +
`select_utterance` the way `ground_concern`'s composer treats `pragmatic_speaker.choose_encoding`
today: as the machinery a graph-resident Rule invokes via a Term/effect, not something to
re-implement. The natural seam is `select_utterance`'s two branches (ungrounded-fallback vs
grounded-argmax) -- an authored rule should read `SystemModel.grounded` off the graph directly
(the attr `system_model.model_system` already writes) and branch the SAME way, rather than calling
back into this Python function.
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as _np
from substrate_rs import Substrate

import domains.audience as aud
import domains.system_model as sysm
import domains.pragmatic_speaker as PS
import domains.many_settings_recognizer as MS
from domains import language as lang
from domains.audience_misjudgment import _norm_range   # reused verbatim (range-normalise cost)

Pred = MS._Pred          # the SAME evaluable-Term wrapper every choose_encoding caller reuses.

DEFAULT_LAMBDA = 0.35     # production-vs-decoding trade weight (fixed; same order as the arc's
#                           established LAMBDA constants -- 0.3 (grounding_repair_gate/referential_
#                           communication), 0.4 (pragmatic_speaker_gate/context_prior_gate)).
DEFAULT_N_RUNGS = 5


# --------------------------------------------------------------------------- #
#  1. audience_model — a GROUNDED SystemModel of an OBSERVED interlocutor.
# --------------------------------------------------------------------------- #

def audience_model(agent, interlocutor: dict) -> dict:
    """Ground (or refuse to ground) a model of `interlocutor`.

    `interlocutor`: {"id": str, "observed": bool, "known_concepts": [str, ...]}.
      - "observed" True  -> the agent actually watched/heard this party (has real signal about what
        it knows). Builds an `audience.py` Scene/Party/Concept graph carrying the observed
        known-concepts, snapshots it (`graph_to_dict`), and calls `system_model.model_system` with a
        `foreign_snapshot` target -- the SAME mechanical path `tests/test_system_model.py` proves is
        SensorAnchor-grounded (verbatim reuse, this module adds no new grounding logic).
      - "observed" False (or omitted) -> a wide/unknown audience the agent never actually watched.
        NO system model is built (there is nothing to ground); the bundle is the honest
        `{"grounded": False, "known": frozenset()}` null.

    Returns {"grounded": bool, "id": str, "known": frozenset[str], "system_model":
    SystemModelResult|None, "graph": native Substrate|None, "party": NodeID|None, "scene":
    NodeID|None}. `graph`/`party` are the SOURCE audience-knowledge graph (kept live, not just the
    foreign snapshot copy `model_system` ingests) so `residual_vs_audience` can run the real
    `audience.knows` theory-of-mind read against it.
    """
    aid = interlocutor.get("id", "interlocutor")
    if not interlocutor.get("observed"):
        return {"grounded": False, "id": aid, "known": frozenset(), "system_model": None,
                "graph": None, "party": None, "scene": None}

    known = [str(c) for c in interlocutor.get("known_concepts", [])]
    g = aud.new_graph()
    scene = aud.make_scene(g)
    party = aud.add_party(g, scene, aid, known)
    graph_dict = g.graph_to_dict()

    sysres = sysm.model_system(
        agent, target={"kind": "foreign_snapshot", "graph": graph_dict, "id": f"audience:{aid}"},
        horizon=2, imagine_steps=2)

    grounded = bool(sysres.grounded)
    return {
        "grounded": grounded, "id": aid,
        "known": frozenset(known) if grounded else frozenset(),
        "system_model": sysres, "graph": g, "party": party, "scene": scene,
    }


# --------------------------------------------------------------------------- #
#  2. residual_vs_audience — the meaning-minus-what-the-audience-already-predicts split.
# --------------------------------------------------------------------------- #

def _concepts_of(meaning) -> set:
    """Accept `meaning` either as a flat concept collection (communicate.py's `content: frozenset`
    shape) or a nested meaning Term-tree (audience.py's / language.py's shape) -- one dispatch,
    landing on the REAL `audience._concepts` extractor for the tree case (reused, not
    reimplemented)."""
    if isinstance(meaning, (set, frozenset, list, tuple)):
        return set(meaning)
    return set(aud._concepts(meaning))


def residual_vs_audience(agent, meaning, audience: dict) -> dict:
    """What `meaning` contains that `audience` does NOT already predict.

    Returns {"new": [...], "known": [...], "residual_frac": float}. `known` is populated ONLY when
    `audience['grounded']` is True, via `audience.knows` against the audience's own observed graph
    (the SAME theory-of-mind read `audience.novelty` already performs) -- the shared model shrinks
    the signal to its residual exactly when that model is a real observation. An ungrounded audience
    contributes nothing: `new` degrades to the WHOLE meaning, `residual_frac` == 1.0 (there is no
    observed basis to presume anything is already known)."""
    concepts = _concepts_of(meaning)
    if not audience.get("grounded") or audience.get("graph") is None:
        return {"new": sorted(concepts), "known": [], "residual_frac": 1.0 if concepts else 0.0}
    g, party = audience["graph"], audience["party"]
    known = {c for c in concepts if aud.knows(g, party, c)}
    new = concepts - known
    residual_frac = (len(new) / len(concepts)) if concepts else 0.0
    return {"new": sorted(new), "known": sorted(known), "residual_frac": residual_frac}


# --------------------------------------------------------------------------- #
#  3. select_utterance — the audience-tailored midpoint, actually produced.
# --------------------------------------------------------------------------- #

def _render(concepts, lexicon: list[dict]) -> str:
    """Render a concept set to a surface string via the REAL `language.produce` leaf-concept path
    (one call per concept, joined) -- mechanical glue, no new production logic. Deterministic order
    (sorted) so the same concept set always renders the same text."""
    if not concepts:
        return ""
    return " ".join(lang.produce(c, lexicon) for c in sorted(concepts))


def _spectrum(residual_new: set, credited_known: set, n_rungs: int):
    """The cheap->explicit spectrum: n_rungs terseness rungs, t in [0,1]. t=0 (explicit) conveys the
    residual PLUS every credited-known concept restated; t=1 (terse) conveys the residual only,
    dropping known concepts as terseness rises (in a fixed, deterministic order) since the audience
    is credited with already having them. Returns [(terseness, conveyed_set), ...]. The textual
    analogue of `pragmatic_speaker.simplify_strokes`'s detail-dropping knob -- this module's own,
    documented in the module docstring."""
    known_sorted = sorted(credited_known)
    n_known = len(known_sorted)
    ts = _np.linspace(0.0, 1.0, max(2, n_rungs))
    rungs = []
    for t in ts:
        keep_n = int(round((1.0 - float(t)) * n_known))
        conveyed = set(residual_new) | set(known_sorted[:keep_n])
        rungs.append((float(t), conveyed))
    return rungs


def select_utterance(agent, meaning, audience: dict, lexicon: list[dict], *,
                      candidates: Optional[list] = None, lam: float = DEFAULT_LAMBDA,
                      n_rungs: int = DEFAULT_N_RUNGS) -> dict:
    """Choose the utterance conveying `meaning`'s residual at the audience-tailored joint optimum,
    and actually produce it (`language.produce`, real string out).

    THE GROUNDING DISCIPLINE (load-bearing): if `audience['grounded']` is False (the agent never
    observed this interlocutor -- an unknown/wide audience being guessed at), this function does
    NOT run the pragmatic spectrum/argmax at all. It falls back, unconditionally, to the fully
    explicit rendering of `meaning`'s whole concept set. Tersening against an ungrounded guess would
    be exactly the curse-of-knowledge failure `audience_misjudgment.py`'s over-estimation case
    already showed collapses recovery -- here the discipline is stronger: don't even attempt the
    trade when there is no observation to trade against.

    If grounded, builds a cheap->explicit spectrum (`_spectrum`, or the caller's own
    `candidates=[(terseness, concept_set), ...]`), renders + scores each rung (recovery = the
    fraction of the FULL meaning recoverable from conveyed-concepts UNION credited-known-concepts;
    cost = rendered word count, range-normalised via `audience_misjudgment._norm_range`), and picks
    the joint optimum via the held `pragmatic_speaker.choose_encoding` Argmax-of-Plus Term (reused
    verbatim -- the SAME Term the handwriting arc's speaker uses, pointed at text rungs instead of
    stroke rungs).

    Returns {"utterance": str, "terseness": float, "grounded_used": bool, "conveyed": [...],
    "residual": {...}, "recovery": float|None, "cost": float|None, "rungs": [...] (grounded only)}.
    """
    all_concepts = _concepts_of(meaning)
    residual = residual_vs_audience(agent, meaning, audience)
    grounded_used = bool(audience.get("grounded"))

    if not grounded_used:
        utterance = _render(all_concepts, lexicon)
        return {
            "utterance": utterance, "terseness": 0.0, "grounded_used": False,
            "conveyed": sorted(all_concepts), "residual": residual,
            "recovery": None, "cost": None, "rungs": None,
            "reason": "ungrounded audience model -- explicit fallback (no observation to tailor to)",
        }

    credited_known = set(audience.get("known") or ())
    if candidates is None:
        rungs = _spectrum(set(residual["new"]), credited_known, n_rungs)
    else:
        rungs = [(float(t), set(c)) for t, c in candidates]

    ts = [t for t, _ in rungs]
    rendered, recs, costs = [], [], []
    for _, conveyed in rungs:
        text = _render(conveyed, lexicon)
        rendered.append(text)
        recovered = (conveyed | credited_known) & all_concepts
        recs.append((len(recovered) / len(all_concepts)) if all_concepts else 1.0)
        costs.append(float(len(text.split())) if text else 0.0)

    cost_n = _norm_range(costs).tolist()
    _, idx = PS.choose_encoding(Substrate, Pred, ts, recs, cost_n, lam)

    return {
        "utterance": rendered[idx], "terseness": ts[idx], "grounded_used": True,
        "conveyed": sorted(rungs[idx][1]), "residual": residual,
        "recovery": recs[idx], "cost": cost_n[idx],
        "rungs": list(zip(ts, rendered, recs, cost_n)),
    }


__all__ = [
    "DEFAULT_LAMBDA", "DEFAULT_N_RUNGS",
    "audience_model", "residual_vs_audience", "select_utterance",
]
