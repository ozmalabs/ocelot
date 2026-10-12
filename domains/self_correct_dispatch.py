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
  - measuring each candidate's structural footprint and aggregating typed
    correction outcomes from the primary graph for the same target/label:
    successful adopted outcomes and unsuccessful attempts are evidence used
    by the rank Program, not an independent host choice;
    the Program's score combines that measured size delta with explicit
    prior-success and prior-failure counts;
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
import hashlib as _hashlib
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


def _candidate_digest(candidate: dict) -> str:
    payload = _json.dumps(candidate.get("rules") or {}, sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + _hashlib.sha256(payload).hexdigest()


def rank_candidates(agent, native, cands: list) -> list:
    """Re-order `cands` (`domains.self_correction._default_candidates`'s own
    output, unchanged) so the agent's OWN `self_correct_rank_<tag>` Program's
    pick -- an Argmin over measured structural cost adjusted by persisted
    utility outcomes for the same target/label -- is tried FIRST by
    `intervene_on_divergence`'s existing try-until-converges loop. Falls back to `cands`
    UNCHANGED (never a fabricated preference) when fewer than two candidates
    carry an actual rule bundle (nothing to rank) or the rank Program was
    never composed on this agent (concern not yet grounded).

    Mints one `CorrectionCandidate` node per usable candidate with its cost
    and mechanically aggregated `prior_successes`/`prior_failures`. These
    records are inputs to the agent-authored Program; the host does not choose
    a preferred label. The candidate ENUMERATION stays machinery-authored. The
    agent's
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
    outcomes: dict[tuple[str, str], list[float]] = {}
    class_outcomes: dict[str, list[float]] = {}
    for node in sub.nodes("CorrectionOutcome"):
        attrs = sub.node(node)["attrs"]
        key = (str(attrs.get("target_rule", "")), str(attrs.get("candidate_label", "")))
        stats = outcomes.setdefault(key, [0.0, 0.0])
        outcome_class = str(attrs.get("outcome_class", ""))
        class_stats = class_outcomes.setdefault(outcome_class, [0.0, 0.0]) if outcome_class else None
        if float(attrs.get("task_utility", 0.0) or 0.0) >= 1.0:
            stats[0] += 1.0
            if class_stats is not None:
                class_stats[0] += 1.0
        else:
            stats[1] += 1.0
            if class_stats is not None:
                class_stats[1] += 1.0
    for c in usable:
        cost = _candidate_cost(native, c)
        digest = _candidate_digest(c)
        target_rule = next(iter(c.get("rules", {})), "")
        prior_successes, prior_failures = outcomes.get(
            (str(target_rule), str(c.get("label", ""))), [0.0, 0.0])
        outcome_class = str(c.get("outcome_class") or "")
        if outcome_class and outcome_class in class_outcomes:
            prior_successes, prior_failures = class_outcomes[outcome_class]
        c["_self_correction_rank_trace"] = {
            "attempt_tag": tag, "structural_cost": cost,
            "candidate_digest": digest, "target_rule": target_rule,
            "outcome_class": outcome_class,
            "prior_successes": prior_successes, "prior_failures": prior_failures,
        }
        sub.add_node("CorrectionCandidate", {
            "label": c["label"], "cost": cost, "attempt_tag": tag,
            "candidate_digest": digest, "target_rule": target_rule,
            "outcome_class": outcome_class,
            "prior_successes": prior_successes, "prior_failures": prior_failures,
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
        model_after = result.get("model_final") or result.get("model_after_candidate")
        candidate_ranked = any(
            isinstance(item.get("rank_trace"), dict)
            for item in result.get("candidates_tried", [])
        )
        active_gate = any(
            isinstance(rule, dict) and rule.get("active", True)
            and str(rule.get("name", "")).startswith("self_correct_gate_")
            for rule in native.export_rules()
        )
        trace = {
            "schema": "SelfCorrectionExperienceV1",
            "source_impasse": getattr(n, "value", n),
            "target_rule": result.get("target_rule") or target,
            # Presence of the policy rule is not proof that this specific
            # correct_ready value was derived from it.
            "attempt_gate": "graph-policy-present; trigger provenance unverified" if active_gate
                            else "unverified-caller-flag",
            "candidate_order": "graph-program" if candidate_ranked else "mechanical-default",
            "candidate_generator": "host-library",
            "correct_ready": bool(at.get("correct_ready")),
            "model_before": _collapse_summary(result.get("model_before") or model_before),
            "candidates_tested": [x.get("label") for x in result.get("candidates_tried", [])],
            "candidates_tried": [
                {
                    "label": x.get("label"),
                    "candidate_digest": x.get("candidate_digest"),
                    "rank_attempt_tag": (x.get("rank_trace") or {}).get("attempt_tag"),
                    "structural_cost": (x.get("rank_trace") or {}).get("structural_cost"),
                    "prior_successes": (x.get("rank_trace") or {}).get("prior_successes", 0),
                    "prior_failures": (x.get("rank_trace") or {}).get("prior_failures", 0),
                    "inert": bool(x.get("inert")),
                    "converges": bool(x.get("converges")),
                    "selected": bool(x.get("selected")),
                    "model_after": _collapse_summary(x.get("model_after")),
                }
                for x in result.get("candidates_tried", [])
            ],
            "chosen": result.get("chosen"),
            "adopted": bool(result.get("adopted")),
            "escalated": bool(result.get("escalated")),
            "reason": result.get("reason"),
            "model_after": _collapse_summary(model_after),
        }
        outcome_records = []
        task_utility = bool(result.get("adopted") and model_after is not None
                            and bool(getattr(model_after, "converged", False)))
        for tried in result.get("candidates_tried", []):
            row = {
                "target_rule": str(result.get("target_rule") or target or ""),
                "candidate_label": str(tried.get("label") or ""),
                "outcome_class": str((tried.get("rank_trace") or {}).get("outcome_class") or ""),
                "candidate_digest": str(tried.get("candidate_digest") or ""),
                "converges_in_rehearsal": bool(tried.get("converges")),
                "selected": bool(tried.get("selected")),
                "adopted": bool(result.get("adopted") and tried.get("selected")),
                "task_utility": 1.0 if (task_utility and tried.get("selected")) else 0.0,
                "rank_attempt_tag": (tried.get("rank_trace") or {}).get("attempt_tag", ""),
            }
            outcome_node = sub.add_node("CorrectionOutcome", row)
            outcome_records.append({"node": getattr(outcome_node, "value", outcome_node), **row})
        trace["outcome_records"] = outcome_records
        native.set_attr(n, "self_correction_trace_schema", trace["schema"])
        native.set_attr(n, "self_correction_trace", _json.dumps(
            trace, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        out.append({"impasse": n, "target_rule": target, "result": result})
    return out


def _collapse_summary(model) -> Optional[dict]:
    if model is None:
        return None
    fields = ("converged", "residual", "n_fixed", "n_volatile",
              "frontier_growth_rate", "horizon", "runtime_s",
              "forward_look_ran", "imagine_steps_run", "counts_trajectory")
    summary = {name: getattr(model, name) for name in fields
               if hasattr(model, name)}
    for name in ("fixed_points", "volatile_frontier"):
        value = getattr(model, name, None)
        if isinstance(value, dict):
            summary[name] = {str(key): len(rows) if isinstance(rows, (list, tuple, set, frozenset)) else rows
                             for key, rows in value.items()}
    return summary


__all__ = ["scan_and_self_correct", "rank_candidates"]
