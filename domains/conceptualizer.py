"""conceptualizer — PHASE 1 + PHASE 2: FORMATION-OF-INTENT and the SELF-MONITOR (Levelt's
conceptualizer -> formulator -> MONITOR; Searle's illocutionary force + perlocutionary effect;
Grice/Relevance: meaning IS the recoverable intention; Clark: audience design over common
ground). Per CLAUDE.md, this module is a WORLD-ADAPTER-SHAPED host layer -- it marshals graph
inputs in, ticks, and reads graph outputs back out. It contains NO decision over graph state:
which FORCE / perlocutionary GOAL a communicative intent carries, which concepts are FOCUS vs
GROUND, and whether a formulated utterance is RECOVERABLE (commit) or must be REVISED, are all
read back from graph data the jabberwock's own composer-authored rules computed
(`domains.reflective_faculty._compose_conceptualize_rule`, dispatched through
`induce_concern`/`ground_concern` exactly like `_compose_communicate_rule` --
`seeds/conceptualizer.json` documents which composer tier this occupies and why).

THE PHASE-1 PIPELINE (one `run_rules` fixpoint each step, mirrors `domains.audience_production_
dispatch`'s already-approved "pending request" idiom):

  1. `mint_communicative_goal` -- mechanical graph write: a communicative Goal{kind, force_kind,
     content} -for_audience-> an Interlocutor, -wants_force-> the ONE held ForceCodebookHub
     (seeds/conceptualizer.json; always the SAME target node, never chosen per-instance).
  2. `form_intent_<tag>` (jabberwock-authored rule, fired by the next `run_rules`) JOINS the
     hub's ForceTemplate children via an Eq-test on `force_kind==kind` -- the RULE ENGINE
     picks the template, not Python -- and mints a `CommunicativeIntent{force,
     perlocutionary_goal, informative_content}`.
  3. `request_message_shape_<tag>` (same authored batch) mints a
     `MessageShapeRequest{status:'requested'}` once the intent exists.
  4. `scan_and_conceptualize` (this module, mechanical, safe to call every tick) finds pending
     `MessageShapeRequest` nodes and calls `domains.audience_driven_production.audience_model`
     + `residual_vs_audience` + `select_utterance` VERBATIM (reused, never reimplemented --
     read-only per the build brief) to mint a `MessageShape{focus, ground, residual_frac}` (=
     the residual split) and to FORMULATE the utterance (audience-tailored: terse when
     grounded, explicit when not) onto that same node. This function makes NO decision about
     WHAT is focus vs ground vs how terse to be -- that discipline lives entirely inside the
     already-approved `audience_driven_production` functions it calls; it only performs the
     graph I/O `add_rule`/rule effects cannot perform (an in-process Python call chain), the
     SAME justification `audience_production_dispatch.scan_and_speak_to_audience` documents
     for itself.

THE PHASE-2 PIPELINE (the SELF-MONITOR -- Levelt's internal loop, "imagine the utterance's
reception and reground before committing"):

  5. `request_monitor_<tag>` (jabberwock-authored, same composer batch) fires once a
     MessageShape exists: mints a `MonitorRequest{status:'requested'}` -for_shape-> the shape,
     -for_intent-> the intent. Same pending-request idiom as step 3, one level up.
  6. `scan_and_monitor` (this module, mechanical, safe every tick) IMAGINES RECEPTION: decodes
     the formulated utterance back into concepts via `domains.language.comprehend` -- the
     agent's OWN comprehension running on its OWN production, the textbook Levelt-monitor shape
     (the production system listening to itself) -- and unions that with a FRESHLY regrounded
     audience credit: `audience_driven_production.audience_model` + `residual_vs_audience`
     called AGAIN, against the Interlocutor node's CURRENT attrs (not the snapshot the shape was
     formulated from). This is the "reground before committing" step: if the world/caller has
     since revised what this audience is credited to know (or was simply wrong), the fresh call
     sees it; the frozen MessageShape does not. VERIFIES the CommunicativeIntent's full
     `informative_content` is recoverable (Grice's success criterion) and writes a
     `Verdict{recoverable, perlocutionary_goal, missing}` -- keyed on the GOAL (carrying
     `perlocutionary_goal` onto the verdict), not a bare cost/score. This function decides
     nothing about what happens with the verdict -- that is `commit_if_recoverable_<tag>` /
     `revise_if_not_recoverable_<tag>`'s Eq-join, entirely in the rule engine.
  7. `commit_if_recoverable_<tag>` mints a `Committed{utterance, terseness, grounded_used}` node
     -- THE COMMITMENT GATE: nothing is cleared to emit until this fires.
     `revise_if_not_recoverable_<tag>` mints a FRESH `MessageShapeRequest` for the SAME intent
     when the verdict says NOT recoverable; `scan_and_conceptualize` reprocesses it against the
     now-current (possibly regrounded) audience state, `request_monitor_<tag>` re-fires on the
     new MessageShape, and the loop closes as ordinary rule-fixpoint chaining -- no Python
     iteration, no Python decision.

`read_intent` / `read_committed` are pure mechanical read-backs (no decision) for scripts/tests
to print the formed CommunicativeIntent / MessageShape / Committed utterance. `run_pipeline`
pumps the whole thing (tick -> scan_and_conceptualize -> tick -> scan_and_monitor) a FIXED
number of rounds -- a mechanical repetition, never a decision over graph content (each scan is
a no-op once its pending-request queue is empty) -- the PHASE-3 (converse-wiring) entry point.
"""
from __future__ import annotations

from typing import Any, Optional

import domains.audience_driven_production as adp
import domains.audience as aud
import domains.language as lang

_SEED_ID = "conceptualizer"
_GOAL_TYPE = "Goal"
_INTERLOCUTOR_TYPE = "Interlocutor"
_INTENT_TYPE = "CommunicativeIntent"
_SHAPE_REQUEST_TYPE = "MessageShapeRequest"
_SHAPE_TYPE = "MessageShape"
_MONITOR_REQUEST_TYPE = "MonitorRequest"
_VERDICT_TYPE = "Verdict"
_COMMITTED_TYPE = "Committed"


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        for n in sub.nodes("Agent"):
            if not sub.node(n)["attrs"].get("is_class"):
                ag_node = n
                break
    return sub, native, ag_node


def _add_edge_unchecked(native, src, edge_type, tgt, attrs=None) -> None:
    try:
        native.add_edge_unchecked(src, edge_type, tgt, attrs or {})
    except TypeError:
        native.add_edge_unchecked(src, edge_type, tgt)


# --------------------------------------------------------------------------- #
#  0. seed bring-up — mechanical, idempotent (SAME guard idiom as
#     reflective_faculty._ensure_seed_chain / substrate.boot_core.load_seeds_into).
# --------------------------------------------------------------------------- #

def ensure_conceptualizer_seed(agent) -> bool:
    """Idempotently load `seeds/conceptualizer.json` (the ForceCodebook + the RelationCue/
    ComposerCue dispatch vocabulary the composer needs to ground a 'form intent, shape it for
    the audience' concern) onto `agent`, guarded by a graph-resident `Seed{id:'conceptualizer'}`
    node so a second call is a no-op. Mechanical seed I/O; installs no Rule and decides
    nothing."""
    sub, native, ag_node = _resolve(agent)
    # already present as live graph content (e.g. boot_all.load_all_seeds installs the
    # conceptualizer manifest by globbing seeds/ WITHOUT minting a Seed marker node) —
    # short-circuit so a second install never duplicates the ForceCodebookHub. Same
    # for/return guard idiom as `_force_hub`; no decision.
    for _hub in sub.nodes("ForceCodebookHub"):
        return True
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == _SEED_ID:
            return True
    from substrate.seed_loader import manifest_for
    native.load_seed_manifest(manifest_for(_SEED_ID), ag_node)
    sub.add_node("Seed", {"id": _SEED_ID, "version": "1.0.0"})
    return True


def _force_hub(sub):
    for n in sub.nodes("ForceCodebookHub"):
        return n
    return None


# --------------------------------------------------------------------------- #
#  1. mint a communicative Goal — the world/caller's decision of WHAT to say to
#     WHOM (force_kind + content + interlocutor); this function only writes it.
# --------------------------------------------------------------------------- #

def mint_communicative_goal(agent, force_kind: str, content, interlocutor: dict,
                             **extra_attrs) -> Any:
    """Mint an `Interlocutor{id, observed, known_concepts}` node (mechanical snapshot of
    `interlocutor`, the SAME shape `audience_production_dispatch.mint_produce_for_audience_
    request` uses) + a communicative `Goal{kind:'communicate', force_kind, content}` +
    `g -for_audience-> interlocutor_node` + `g -wants_force-> hub` (the ONE held
    ForceCodebookHub — always the same target, mechanical, no choice). The DECISION of WHICH
    force applies happens later, in the rule engine (`form_intent_<tag>`'s Eq-join), not
    here. Returns the Goal node id."""
    ensure_conceptualizer_seed(agent)
    sub, native, ag_node = _resolve(agent)
    aid = interlocutor.get("id", "interlocutor")
    interlocutor_node = sub.add_node(_INTERLOCUTOR_TYPE, {
        "id": aid,
        "observed": bool(interlocutor.get("observed", False)),
        "known_concepts": [str(c) for c in interlocutor.get("known_concepts", [])],
    })
    attrs = {"kind": "communicate", "force_kind": str(force_kind),
             "content": sorted({str(c) for c in content})}
    attrs.update(extra_attrs)
    g = sub.add_node(_GOAL_TYPE, attrs)
    _add_edge_unchecked(native, g, "for_audience", interlocutor_node)
    hub = _force_hub(sub)
    if hub is not None:
        _add_edge_unchecked(native, g, "wants_force", hub)
    if ag_node is not None:
        _add_edge_unchecked(native, ag_node, "has_goal", g)
    return g


# --------------------------------------------------------------------------- #
#  2. scan_and_conceptualize — the mechanical host hook for form_message_shape +
#     formulate (an in-process Python call chain a Rust rule effect cannot make).
# --------------------------------------------------------------------------- #

def _read_node_attrs(sub, node) -> dict:
    return dict(sub.node(node)["attrs"]) if node is not None else {}


def _mint_ungrounded_placeholder(sub, aid: str):
    """Honest `grounded:false` SystemModel placeholder — the SAME node type/attr vocabulary
    the grounded case uses (mirrors `audience_production_dispatch._mint_ungrounded_
    placeholder`, kept local so this module never imports that module's private helper)."""
    return sub.add_node("SystemModel", {
        "target_kind": "foreign_snapshot", "target_id": f"audience:{aid}",
        "converged": False, "residual": 1.0, "grounded": False,
        "method": ("conceptualizer: no observation of this interlocutor — audience_model() "
                   "intentionally builds no SystemModel for an unobserved audience."),
    })


def scan_and_conceptualize(agent, lexicon: list[dict], **select_kwargs) -> list[dict]:
    """For every pending `MessageShapeRequest{status:'requested'}`: resolve its
    CommunicativeIntent (`req -for_intent-> intent`, wired by `request_message_shape_<tag>`)
    and the intent's audience (`intent -for_audience-> aud`), call
    `audience_driven_production.audience_model` + `residual_vs_audience` (mints the
    `MessageShape{focus, ground, residual_frac}` — `focus`/`ground` are `residual_vs_
    audience`'s `new`/`known`, VERBATIM) + `select_utterance` (the audience-designed
    formulation) and write the results onto the MessageShape node, then mark the request
    'shaped'. Mechanical scan, safe every tick — a re-scan never re-shapes a request already
    marked 'shaped'. Returns the per-request results produced THIS call."""
    sub, native, ag_node = _resolve(agent)
    results: list[dict] = []
    for req in list(sub.nodes(_SHAPE_REQUEST_TYPE)):
        at = sub.node(req)["attrs"]
        if at.get("status") != "requested":
            continue
        intent = None
        for nb in native.neighbours(req, "for_intent"):
            intent = nb
            break
        if intent is None:
            continue
        iat = _read_node_attrs(sub, intent)
        meaning = set(iat.get("informative_content") or [])

        aud_node = None
        for nb in native.neighbours(intent, "for_audience"):
            aud_node = nb
            break
        aat = _read_node_attrs(sub, aud_node)
        interlocutor = {"id": aat.get("id", "interlocutor"),
                         "observed": bool(aat.get("observed", False)),
                         "known_concepts": list(aat.get("known_concepts") or [])}

        bundle = adp.audience_model(agent, interlocutor)
        residual = adp.residual_vs_audience(agent, meaning, bundle)
        res = adp.select_utterance(agent, meaning, bundle, lexicon, **select_kwargs)

        if bundle["system_model"] is not None:
            sm_node = bundle["system_model"].model_node
        else:
            sm_node = _mint_ungrounded_placeholder(sub, interlocutor["id"])

        shape = sub.add_node(_SHAPE_TYPE, {
            "focus": list(residual["new"]), "ground": list(residual["known"]),
            "residual_frac": residual["residual_frac"],
            "utterance": res["utterance"], "terseness": res["terseness"],
            "grounded_used": res["grounded_used"],
        })
        _add_edge_unchecked(native, req, "has_shape", shape)
        _add_edge_unchecked(native, intent, "has_shape", shape)
        _add_edge_unchecked(native, req, "has_audience_model", sm_node)
        native.set_attr(req, "status", "shaped")

        results.append({"request": req, "intent": intent, "shape": shape,
                         "system_model": sm_node, "result": res, "residual": residual,
                         "interlocutor": interlocutor})
    return results


# --------------------------------------------------------------------------- #
#  3. scan_and_monitor — PHASE 2's mechanical host hook: IMAGINE RECEPTION,
#     write a Verdict; the RULE ENGINE (commit_if_recoverable_<tag> /
#     revise_if_not_recoverable_<tag>) decides what happens next.
# --------------------------------------------------------------------------- #

def _decode_utterance(utterance: str, lexicon: list[dict]) -> set:
    """IMAGINE RECEPTION, literally: run the agent's OWN comprehension
    (`domains.language.comprehend`) over its OWN produced utterance -- the same lexicon
    `language.produce` rendered it with -- and extract the concepts it decodes to via
    `audience._concepts` (the SAME extractor `residual_vs_audience` already reuses, never a
    new one). This is comprehend(produce(m)) run for real, not bookkeeping: what the
    utterance's WORDS actually make recoverable, independent of what the speaker intended.
    `language.comprehend("", ...)` is already safe (returns `[]`) — no empty-string guard
    needed."""
    decoded: set = set()
    for item in lang.comprehend(utterance, lexicon):
        decoded |= aud._concepts(item)
    return decoded


def scan_and_monitor(agent, lexicon: list[dict]) -> list[dict]:
    """For every pending `MonitorRequest{status:'requested'}` (minted by the jabberwock-authored
    `request_monitor_<tag>` once a MessageShape exists): IMAGINE RECEPTION (`_decode_utterance`
    on the formulated `MessageShape.utterance`) union a FRESHLY REGROUNDED audience credit --
    `audience_driven_production.audience_model` + `residual_vs_audience` called AGAIN against
    the Interlocutor node's CURRENT attrs (not the snapshot `scan_and_conceptualize` formulated
    from; this is the "reground before committing" step -- a stale or corrected belief about
    what the audience knows is caught here, not before). VERIFY: does the recovered set cover
    the CommunicativeIntent's full `informative_content` (Grice's success criterion)? Writes a
    `Verdict{recoverable, perlocutionary_goal, missing, decoded, credited_now}` -- carrying the
    intent's `perlocutionary_goal` (the GOAL the verdict is keyed on, not a bare cost/score) --
    that `commit_if_recoverable_<tag>` / `revise_if_not_recoverable_<tag>` Eq-test on. This
    function decides nothing about commit vs revise; it only computes the boolean the rule
    engine branches on, the SAME justification tier `scan_and_conceptualize` already
    establishes for itself. Mechanical scan, safe every tick."""
    sub, native, ag_node = _resolve(agent)
    results: list[dict] = []
    for req in list(sub.nodes(_MONITOR_REQUEST_TYPE)):
        at = sub.node(req)["attrs"]
        if at.get("status") != "requested":
            continue
        shape = None
        for nb in native.neighbours(req, "for_shape"):
            shape = nb
            break
        intent = None
        for nb in native.neighbours(req, "for_intent"):
            intent = nb
            break
        sat = _read_node_attrs(sub, shape)
        iat = _read_node_attrs(sub, intent)
        content = set(iat.get("informative_content") or [])

        decoded = _decode_utterance(sat.get("utterance") or "", lexicon)

        aud_node = None
        for nb in native.neighbours(intent, "for_audience"):
            aud_node = nb
            break
        aat = _read_node_attrs(sub, aud_node)
        interlocutor = {"id": aat.get("id", "interlocutor"),
                         "observed": bool(aat.get("observed", False)),
                         "known_concepts": list(aat.get("known_concepts") or [])}
        fresh_bundle = adp.audience_model(agent, interlocutor)
        fresh_residual = adp.residual_vs_audience(agent, content, fresh_bundle)
        credited_now = set(fresh_residual["known"])

        recovered = decoded | credited_now
        missing = sorted(content - recovered)
        recoverable = not missing

        verdict = sub.add_node(_VERDICT_TYPE, {
            "recoverable": recoverable, "perlocutionary_goal": iat.get("perlocutionary_goal"),
            "missing": missing, "decoded": sorted(decoded), "credited_now": sorted(credited_now),
        })
        _add_edge_unchecked(native, req, "has_verdict", verdict)
        native.set_attr(req, "status", "monitored")

        results.append({"request": req, "shape": shape, "intent": intent, "verdict": verdict,
                         "recoverable": recoverable, "missing": missing,
                         "perlocutionary_goal": iat.get("perlocutionary_goal")})
    return results


def run_pipeline(agent, lexicon: list[dict], *, rounds: int = 4, tick_budget: int = 2000,
                  **select_kwargs) -> None:
    """PHASE-3 ENTRY POINT: run the full conceptualizer fixpoint -- form intent -> shape ->
    formulate -> monitor -> commit (looping through revise/re-monitor as needed) -- from one
    call. Pumps `tick -> scan_and_conceptualize -> tick -> scan_and_monitor` a FIXED number of
    `rounds` (mechanical repetition, never a decision over graph content: each scan is a no-op
    once its own pending-request queue is empty, the SAME idempotency every scan in this module
    already relies on). Call `mint_communicative_goal` first, then this, then `read_committed`
    for the utterance cleared to emit -- nothing earlier in the pipeline is safe to emit."""
    sub, native, ag_node = _resolve(agent)
    for _ in range(rounds):
        native.run_rules(tick_budget)
        scan_and_conceptualize(agent, lexicon, **select_kwargs)
        native.run_rules(tick_budget)
        scan_and_monitor(agent, lexicon)
    native.run_rules(tick_budget)


# --------------------------------------------------------------------------- #
#  3.5 PHASE-3 reply bridge — the marshal-only entry the LIVE converse path calls.
#      No decision: it drives the composer (the jabberwock authoring its OWN rules)
#      once, wires the goal, pumps the pipeline, and reads the gate back out.
# --------------------------------------------------------------------------- #

# the FOUR clauses the phase-1/phase-2 tests induce (mirrors
# tests/test_conceptualizer_monitor.py's ALL_CLAUSES) — driving `induce_concern` with
# them makes the jabberwock AUTHOR all five conceptualizer rules via its own composer.
_FORM_CLAUSE = ["form", "INTENT", "before", "UTTERANCE"]
_SHAPE_CLAUSE = ["shape", "MESSAGE", "by", "RESIDUAL"]
_MONITOR_CLAUSE = ["monitor", "UTTERANCE", "before", "COMMIT"]
_COMMIT_CLAUSE = ["commit", "UTTERANCE", "if", "RECOVERABLE"]
_RULES_READY_TYPE = "ConceptualizerRulesReady"


def ensure_conceptualizer_rules(agent, *, tag: str = "conceptualizer_live") -> bool:
    """Idempotently drive `induce_concern`->`ground_concern` ONCE so the jabberwock AUTHORS the
    five conceptualizer rules (form_intent / request_message_shape / request_monitor /
    commit_if_recoverable / revise_if_not_recoverable), guarded by a graph-resident
    `ConceptualizerRulesReady` node so a second call is a no-op (the SAME for/return guard idiom
    as `ensure_conceptualizer_seed`/`_force_hub`). This DECIDES nothing -- it drives the composer
    (the jabberwock authoring its OWN rules from a framed concern, the admissible 'build the
    faculty' motion `scripts/arc_self_report.build_describe_faculty` already uses) and records
    that it ran. Reflective_faculty is imported lazily to avoid an import cycle."""
    ensure_conceptualizer_seed(agent)
    sub, native, ag_node = _resolve(agent)
    for _n in sub.nodes(_RULES_READY_TYPE):
        return True
    import domains.reflective_faculty as _rf
    ind = _rf.induce_concern(
        agent, [_FORM_CLAUSE, _SHAPE_CLAUSE, _MONITOR_CLAUSE, _COMMIT_CLAUSE], name_hint=tag)
    _rf.ground_concern(agent, [ind.get("capability_key")])
    sub.add_node(_RULES_READY_TYPE, {"tag": tag})
    return True


def conceptualize_reply(agent, force_kind, content, interlocutor: dict, lexicon: list[dict], *,
                        rounds: int = 4, **select_kwargs) -> dict:
    """PHASE-3 reply entry: ensure the rules are authored, mint a communicative Goal
    (`force_kind` + `content` + `interlocutor` -- the caller's WHAT-to-say / to-WHOM, the SAME
    decision `mint_communicative_goal` documents as the world's), run the full
    form->shape->monitor->commit pipeline, and read the formed CommunicativeIntent + the
    monitor-cleared Committed utterance back. Returns {"goal", "intent", "committed"}. Every
    DECISION inside (which force, which focus/ground, whether recoverable) is the jabberwock's own
    composer-authored rules', never Python's; `committed["committed"]` is None until the monitor
    clears the gate."""
    ensure_conceptualizer_rules(agent)
    g = mint_communicative_goal(agent, force_kind, content, interlocutor)
    run_pipeline(agent, lexicon, rounds=rounds, **select_kwargs)
    return {"goal": g, "intent": read_intent(agent, g), "committed": read_committed(agent, g)}


# --------------------------------------------------------------------------- #
#  4. read-back — pure mechanical query, no decision.
# --------------------------------------------------------------------------- #

def read_intent(agent, goal_node) -> dict:
    """Read the CommunicativeIntent (+ its MessageShape, if formed) formed from
    `goal_node` back into a plain dict for scripts/tests to inspect/print. Pure graph read."""
    sub, native, ag_node = _resolve(agent)
    intent_node = None
    for nb in native.neighbours(goal_node, "forms_intent"):
        intent_node = nb
        break
    if intent_node is None:
        return {"goal": goal_node, "intent": None}
    iat = _read_node_attrs(sub, intent_node)
    shape_node = None
    for nb in native.neighbours(intent_node, "has_shape"):
        shape_node = nb
        break
    sat = _read_node_attrs(sub, shape_node) if shape_node is not None else {}
    return {
        "goal": goal_node, "intent": intent_node,
        "force": iat.get("force"), "perlocutionary_goal": iat.get("perlocutionary_goal"),
        "informative_content": list(iat.get("informative_content") or []),
        "shape": shape_node,
        "focus": list(sat.get("focus") or []), "ground": list(sat.get("ground") or []),
        "residual_frac": sat.get("residual_frac"),
        "utterance": sat.get("utterance"), "terseness": sat.get("terseness"),
        "grounded_used": sat.get("grounded_used"),
    }


def read_committed(agent, goal_node) -> dict:
    """Read the `Committed` node (if the monitor has cleared one) formed from `goal_node`'s
    CommunicativeIntent back into a plain dict -- THE COMMIT-GATE READ: `committed`/`utterance`
    are `None` until `commit_if_recoverable_<tag>` has actually fired (an un-monitored, or
    still-not-recoverable, intent has no `Committed` node to find). Pure graph read, no
    decision -- this is the PHASE-3 read-off point for what may actually be emitted."""
    sub, native, ag_node = _resolve(agent)
    intent_node = None
    for nb in native.neighbours(goal_node, "forms_intent"):
        intent_node = nb
        break
    if intent_node is None:
        return {"goal": goal_node, "intent": None, "committed": None, "utterance": None}
    committed_node = None
    for nb in native.neighbours(intent_node, "has_committed"):
        committed_node = nb
        break
    cat = _read_node_attrs(sub, committed_node) if committed_node is not None else {}
    return {
        "goal": goal_node, "intent": intent_node, "committed": committed_node,
        "utterance": cat.get("utterance"), "terseness": cat.get("terseness"),
        "grounded_used": cat.get("grounded_used"),
    }


__all__ = [
    "ensure_conceptualizer_seed", "ensure_conceptualizer_rules", "conceptualize_reply",
    "mint_communicative_goal",
    "scan_and_conceptualize", "scan_and_monitor", "run_pipeline",
    "read_intent", "read_committed",
]
