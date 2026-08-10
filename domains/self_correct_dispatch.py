"""self_correct_dispatch -- the mechanical host hook for TIER 5 COGNITION
(autonomous self-correction, closing `domains/self_correction.py`'s own
follow-on seam), mirroring `domains/collapse_watch.py`'s `scan_and_predict`
and `domains/imagination_dispatch.py`'s `scan_and_imagine`: it calls
`domains.self_correction.intervene_on_divergence`, an in-process Python call
a Rust rule effect cannot make itself (the SAME reason every other `scan_
and_*` hook in this codebase exists).

THE AGENT'S OWN DECISIONS (never Python here, read back only): WHETHER to
even ATTEMPT correction on a given predicted-divergence Impasse -- `seeds/
composer_self_correct_graph.json`'s `self_correct_gate_<tag>` rule (authored
via `domains.reflective_faculty.ground_concern`'s new 'self_correct'
composer, dispatched from the 'correct' RelationCue) marks `Impasse.
correct_ready`; this module never re-derives that verdict, only reads it
back -- and WHICH converging candidate to prefer -- `self_correct_rank_
<tag>`'s Argmin Program (also composer-authored) scores a mechanically-
measured candidate list and this module reorders `domains.self_correction.
_default_candidates`'s own list so the Program's pick is tried FIRST by
`intervene_on_divergence`'s existing try-until-converges loop.

WHAT IS MECHANICAL HERE (never a decision):
  - scanning for `Impasse{kind:predicted_divergence, correct_ready:true}`
    not yet attempted, and marking `self_correction_attempted` (idempotent
    bookkeeping -- the SAME "mark attempted, never re-attempt" idiom the
    inline daemon hook this module replaces already used);
  - measuring each candidate's structural footprint: the JSON-size delta
    between a candidate's variant rule(s) and the ORIGINAL active rule(s)
    they would replace -- a real, honest size measurement, not an opinion,
    handed to the agent's own rank Program as its `cost` field;
  - evaluating the agent's rank Program (`native.evaluate`, the same raw-
    dict calling convention `domains.reflective_faculty._pick_composer` /
    `_compose_structural_variant` already use for a held Term) and re-
    ordering the candidate list so its pick sits first;
  - calling `domains.self_correction.intervene_on_divergence` with that
    ordered list -- the machinery itself still performs every remaining
    mechanical sub-step (imagine, predict, denylist veto, adopt-or-propose;
    the SAFETY BOUNDARY -- `domains.reflective_faculty._rule_denylisted` --
    stays entirely inside that module, untouched by this one).

domains/self_correction.py is READ-ONLY from here (never edited): this
module only calls its existing public functions
(`intervene_on_divergence`) and two of its internal, purely-mechanical
helpers (`_default_candidates`, `_infer_growth_rule` -- the "candidate
ENUMERATION stays exactly as machinery-authored" seam that module's own
docstring names)."""
from __future__ import annotations

import json as _json
import uuid as _uuid
from typing import Any, Optional

from domains.self_correction import (
    intervene_on_divergence, _default_candidates, _infer_growth_rule,
)
from domains.collapse_model import predict_collapse


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _find_rank_program(sub) -> Optional[dict]:
    """Mechanical graph read: the agent's own `self_correct_rank_<tag>`
    Program (`seeds/composer_self_correct_graph.json`), prefix-matched by
    name since the `<tag>` suffix is per-ComposeRequest and not predictable
    here -- the SAME "search by name prefix, never assume the exact tag"
    idiom `domains.self_correction._find_variant_rule_json` (well,
    `_compose_experiment_rule`'s `_find_variant_rule_json`) documents for
    itself. Returns None (honest) if the concern was never grounded on this
    agent -- callers fall back to the machinery's own unranked default
    order, never a fabricated preference."""
    for n in sub.nodes("Program"):
        at = sub.node(n)["attrs"]
        name = at.get("name") or ""
        if name.startswith("self_correct_rank_") and at.get("program"):
            try:
                return _json.loads(at["program"])
            except Exception:
                continue
    return None


def _rule_json_by_name(native, name: str) -> Optional[dict]:
    try:
        for r in native.export_rules():
            if isinstance(r, dict) and r.get("name") == name:
                return r
    except Exception:
        pass
    return None


def _candidate_cost(native, candidate: dict) -> float:
    """Mechanical structural-footprint measurement (never an opinion): the
    JSON-size delta between each rule the candidate bundle touches and the
    ORIGINAL active rule it would replace, summed across the bundle -- a
    genuine, honest size measurement of how much the candidate edits. Used
    only to SCORE candidates for the agent's own rank Program (Argmin) to
    pick from; this function never picks one itself."""
    total = 0.0
    for rule_name, variant in (candidate.get("rules") or {}).items():
        variant_size = len(_json.dumps(variant, sort_keys=True)) if variant is not None else 0.0
        original = _rule_json_by_name(native, rule_name)
        original_size = len(_json.dumps(original, sort_keys=True)) if original is not None else 0.0
        total += abs(variant_size - original_size)
    return float(total)


def rank_candidates(agent, native, cands: list) -> list:
    """Re-order `cands` (`domains.self_correction._default_candidates`'s own
    output, unchanged) so the agent's OWN `self_correct_rank_<tag>` Program's
    pick -- an Argmin over each USABLE candidate's mechanically-measured
    structural-footprint cost -- is tried FIRST by `intervene_on_divergence`'s
    existing try-until-converges loop, so that when >= 2 candidates would
    converge, the cheaper/less-invasive one is adopted. Falls back to `cands`
    UNCHANGED (never a fabricated preference) when fewer than two candidates
    carry an actual rule bundle (nothing to rank) or the rank Program was
    never composed on this agent (concern not yet grounded).

    Mints one EPHEMERAL `CorrectionCandidate{label, cost, attempt_tag}` node
    per usable candidate (mechanical -- the candidate ENUMERATION and its
    cost MEASUREMENT stay exactly as machinery/host-authored) so the agent's
    rank Program can genuinely Argmin over real graph nodes: `Attr(Var(x),
    key)` only resolves through an actual NodeID, verified empirically to
    silently misbehave (order-dependent tie-breaking, not a real value
    comparison) when `x` is bound to a plain python dict instead -- the same
    reason every other held Argmax/Argmin in this codebase (`_pick_composer`,
    `_compose_structural_variant`) picks over `NodesOfType(...)`, never a
    bare env-supplied list. These audit nodes are left in the graph (a
    record of what was considered and why, the same "honest record" idiom
    `domains.self_correction._mint_proposal` already keeps), scoped by a
    fresh `attempt_tag` per call so concurrent/repeated attempts never
    collide."""
    sub, _n = _resolve(agent)
    usable = [c for c in cands if c.get("rules")]
    if len(usable) < 2:
        return cands
    rank_term = _find_rank_program(sub)
    if rank_term is None:
        return cands
    tag = _uuid.uuid4().hex[:12]
    for c in usable:
        sub.add_node("CorrectionCandidate", {
            "label": c["label"], "cost": _candidate_cost(native, c), "attempt_tag": tag,
        })
    try:
        picked = native.evaluate(rank_term, {"tag": tag})
    except Exception:
        return cands
    picked_label = sub.node(picked)["attrs"].get("label") if picked is not None and sub.has_node(picked) else None
    if picked_label is None:
        return cands
    return ([c for c in cands if c.get("label") == picked_label] +
            [c for c in cands if c.get("label") != picked_label])


def scan_and_self_correct(agent) -> list:
    """The mechanical host hook: find every `Impasse{kind:predicted_
    divergence}` the agent's OWN `self_correct_gate_<tag>` rule has marked
    `correct_ready` (never every unresolved one -- that was the prior
    "try every one" scaffold this hook replaces in `scripts/
    jabberwock_daemon.py`), mark it `self_correction_attempted` (idempotent),
    rank the candidate space via the agent's OWN rank Program, and call
    `domains.self_correction.intervene_on_divergence`. A predicted-divergence
    Impasse the gate rule never marked (below its own priority threshold) is
    silently skipped here -- the agent chose not to spend correction effort
    on it; this hook makes no such judgement itself.

    Returns a list of `{"impasse": NodeID, "target_rule": name_or_None,
    "result": intervene_on_divergence's own return dict}` for every Impasse
    actually attempted this call."""
    sub, native = _resolve(agent)
    out: list = []
    for n in list(sub.nodes("Impasse")):
        if not sub.has_node(n):
            continue
        at = sub.node(n)["attrs"]
        if at.get("kind") != "predicted_divergence":
            continue
        if at.get("self_correction_attempted"):
            continue
        if not at.get("correct_ready"):
            continue
        native.set_attr(n, "self_correction_attempted", True)

        model_before = predict_collapse(agent)
        target = _infer_growth_rule(native, model_before)
        kwargs: dict[str, Any] = {"model_before": model_before}
        if target is not None:
            kwargs["target_rule"] = target
            cands = _default_candidates(native, target)
            kwargs["candidates"] = rank_candidates(agent, native, cands)
        result = intervene_on_divergence(agent, **kwargs)
        out.append({"impasse": n, "target_rule": target, "result": result})
    return out


__all__ = ["scan_and_self_correct", "rank_candidates"]
