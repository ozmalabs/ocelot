"""Meta-monitor — a process that sits OVER any other process and identifies
meta-issues (CLAUDE.md: the judgement is a graph-resident Rule, dials are seeded).

A first-order process works on a task (recognise digits, invent features, walk).
A META-issue is a problem with the PROCESS ITSELF, invisible from inside it — the
clearest being EFFORT WITHOUT PAYOFF: the process keeps expending work while the
thing it's meant to improve stays flat. That's the agent inventing 322 features
while recognition sits at ~13: it isn't failing, it's SPINNING — pulling a lever
that isn't connected to the outcome.

This monitor is general. Any process registers with two graph signals: an EFFORT
attr (cumulative work — features minted, ticks spent, hypotheses raised) and a
PAYOFF attr (the target — recognition, reward, coverage). Each cycle the adapter
REPORTS the two numbers; the monitor keeps a window of history (mechanical) and a
RULE makes the judgement — effort rose across the window AND payoff stayed flat ->
mint a MetaIssue + flag the process. The agent reads the flag and can stop or
redirect the process. The monitor knows nothing about speech; it knows about
processes. See [[ozma_meta_cognitive_structure]] / [[ozma_self_developmental_cortex]].
"""
from __future__ import annotations

import json
from pathlib import Path

from substrate_rs import (Attr, Lit, Var, Gt, Lte, Eq, And, Or, Abs, Minus,
                          IfThenElse)

_SEED_PATH = (Path(__file__).resolve().parent.parent /
              "seeds" / "meta_monitor.json")


def _load_seed() -> dict:
    with _SEED_PATH.open() as f:
        return json.load(f)


def _native(substrate):
    return substrate._inner if hasattr(substrate, "_inner") else substrate


def _root(substrate):
    for n in substrate.nodes("MetaMonitorRoot"):
        return n
    # Dials seeded from seeds/meta_monitor.json — not Python constants.
    return substrate.add_node("MetaMonitorRoot",
                              {"origin": "meta_monitor",
                               **_load_seed().get("meta_monitor_root", {})})


def _window(substrate) -> int:
    return int(substrate.node(_root(substrate))["attrs"].get("window", 5))


def register_process(substrate, name: str, effort_label: str = "",
                     payoff_label: str = "") -> "object":
    """Register a process for the monitor to watch. `name` identifies it;
    effort_label/payoff_label are human notes on what the two signals mean.
    Returns the Process node. Idempotent by name."""
    try:
        substrate.add_production({
            "src": {"type": "MetaMonitorRoot", "var": "a"},
            "edge_type": "watches", "tgt": {"type": "Process", "var": "b"},
            "provenance": "meta_monitor:watches"})
    except Exception:
        pass
    root = _root(substrate)
    for p in substrate.neighbours(root, "watches"):
        if substrate.node(p)["attrs"].get("name") == name:
            return p
    attrs = {
        "name": name, "origin": "meta_monitor",
        "effort_label": effort_label, "payoff_label": payoff_label,
        "effort_history": [], "payoff_history": [],
        "effort_rise": 0.0, "payoff_change": 0.0,
        "window_full": 0, "meta_eval_pending": 0, "meta_issue": "none",
        # Investigation state (do-contrast): does the effort even reach the
        # payoff? The agent MEASURES `payoff_with`/`payoff_without` its effort and
        # concludes — it does not assume.
        "investigated": 0, "payoff_with": 0.0, "payoff_without": 0.0,
        "connection_band": 1.0}
    # The intervention (how to do-contrast THIS process) is DECLARED IN THE SEED,
    # per process — not coded in Python. Flatten it onto the node for the rules
    # + the thin measurement adapter to read.
    spec = _load_seed().get("processes", {}).get(name, {})
    if "connection_band" in spec:
        attrs["connection_band"] = float(spec["connection_band"])
    iv = spec.get("intervention", {})
    if iv:
        attrs.update(
            intervention_toggle_type=iv.get("toggle_type", ""),
            intervention_toggle_attr=iv.get("toggle_attr", ""),
            intervention_with=float(iv.get("with_value", 1.0)),
            intervention_without=float(iv.get("without_value", 0.0)),
            has_intervention=1)
    else:
        attrs["has_intervention"] = 0
    p = substrate.add_node("Process", attrs)
    try:
        substrate.add_edge(root, "watches", p)
    except Exception:
        pass
    return p


def report(substrate, name: str, effort: float, payoff: float) -> None:
    """Adapter: record this cycle's effort + payoff for `name`, keep a window of
    history, and compute the across-window deltas (mechanical) the rule judges.
    Sets meta_eval_pending so the agent's rule will re-evaluate."""
    p = register_process(substrate, name)
    w = _window(substrate)
    a = substrate.node(p)["attrs"]
    eh = (list(a.get("effort_history", [])) + [float(effort)])[-w:]
    ph = (list(a.get("payoff_history", [])) + [float(payoff)])[-w:]
    substrate.set_attr(p, "effort_history", eh)
    substrate.set_attr(p, "payoff_history", ph)
    substrate.set_attr(p, "payoff_current", float(payoff))
    if len(eh) >= w:
        substrate.set_attr(p, "effort_rise", float(eh[-1] - eh[0]))
        substrate.set_attr(p, "payoff_change", float(ph[-1] - ph[0]))
        substrate.set_attr(p, "window_full", 1)
    else:
        substrate.set_attr(p, "window_full", 0)
    substrate.set_attr(p, "meta_eval_pending", 1)


def install_meta_issue_rule(substrate) -> dict:
    """Install the monitor's judgement as a Rule over each watched Process: once a
    full window is in, EFFORT rose past `effort_min_rise` AND |PAYOFF change| stayed
    within `payoff_flat_band` -> the process is spinning; set meta_issue. The
    thresholds are read from the MetaMonitorRoot (seeded). Returns
    {'root','rule_index'}."""
    nat = _native(substrate)
    root = _root(substrate)
    P, R = Var("P"), Var("R")
    spinning_now = And(items=(
        Gt(a=Attr(P, "effort_rise"), b=Attr(R, "effort_min_rise")),
        Lte(a=Abs(Attr(P, "payoff_change")), b=Attr(R, "payoff_flat_band"))))
    improved = Gt(a=Attr(P, "payoff_change"), b=Attr(R, "payoff_improve_band"))
    mi = Attr(P, "meta_issue")
    # A verdict the investigation already reached — PRESERVE it (don't re-derive).
    concluded = Or(items=(Eq(a=mi, b=Lit("disconnected_lever")),
                          Eq(a=mi, b=Lit("lever_helps")),
                          Eq(a=mi, b=Lit("lever_harms"))))
    still_spinning = Or(items=(spinning_now,
                              Eq(a=mi, b=Lit("effort_without_payoff"))))
    # LATCH only — NO assumption of cause. The cause is the SEPARATE investigation
    # rule's job (do-contrast). This rule keeps the initial spinning flag up
    # (until payoff improves) and preserves whatever verdict the investigation
    # reached.
    issue_next = IfThenElse(
        improved, Lit("none"),
        IfThenElse(concluded, mi,
                   IfThenElse(still_spinning, Lit("effort_without_payoff"),
                              Lit("none"))))
    rule = {
        "name": "detect_meta_issue",
        "match": [["R", "watches", "P"]],
        "where": And(items=(Eq(a=Attr(P, "meta_eval_pending"), b=Lit(1)),
                            Eq(a=Attr(P, "window_full"), b=Lit(1)))).to_dict(),
        "effects": [
            ["set_attr", "P", "meta_issue", {"__term__": issue_next.to_dict()}],
            ["set_attr", "P", "meta_eval_pending", 0],
        ],
    }
    return {"root": root, "rule_index": nat.add_rule(rule)}


def set_process_controls(substrate, name: str, root_node) -> None:
    """Link a watched Process to the root it CONTROLS, so the response rule can
    pause that root when the process is flagged. The root's rules gate on its
    `paused` attr (set it to 0 if absent)."""
    try:
        substrate.add_production({
            "src": {"type": "Process", "var": "a"},
            "edge_type": "controls",
            "tgt": {"type": substrate.node(root_node)["type"], "var": "b"},
            "provenance": "meta_monitor:controls"})
    except Exception:
        pass
    p = register_process(substrate, name)
    if "paused" not in substrate.node(root_node)["attrs"]:
        substrate.set_attr(root_node, "paused", 0)
    if root_node not in substrate.neighbours(p, "controls"):
        try:
            substrate.add_edge(p, "controls", root_node)
        except Exception:
            pass


def install_meta_response_rule(substrate) -> dict:
    """The agent's RESPONSE: for each Process that controls a root, set that
    root's `paused` flag to 1 when the process is flagged effort-without-payoff,
    else 0. The controlled process's rules gate on `paused` — so the agent stops
    spinning a lever that isn't moving the outcome, and resumes if it starts to.
    Returns {'rule_index'}."""
    nat = _native(substrate)
    P = Var("P")
    mi = Attr(P, "meta_issue")
    # Pause the process when spinning, when its effort is HARMFUL, or when the
    # lever is disconnected — but NOT when the lever HELPS (then the effort is
    # good; the agent should keep + use it, not pause it).
    flagged = Or(items=(Eq(a=mi, b=Lit("effort_without_payoff")),
                        Eq(a=mi, b=Lit("disconnected_lever")),
                        Eq(a=mi, b=Lit("lever_harms"))))
    paused_next = IfThenElse(flagged, Lit(1), Lit(0))
    rule = {
        "name": "respond_to_meta_issue",
        "match": [["P", "controls", "Root"]],
        "where": Lit(True).to_dict(),
        "effects": [["set_attr", "Root", "paused",
                     {"__term__": paused_next.to_dict()}]],
    }
    return {"rule_index": nat.add_rule(rule)}


def agent_check_meta(substrate, rule_index: int, respond_index: int | None = None,
                     max_iters: int = 100) -> list:
    """Fire the judgement rule over every watched process whose window just
    updated, then (if `respond_index` given) the response rule so the agent acts
    on any flag. Returns the processes currently flagged."""
    nat = _native(substrate)
    root = _root(substrate)
    for _ in range(max_iters):
        pending = [p for p in substrate.neighbours(root, "watches")
                   if substrate.node(p)["attrs"].get("meta_eval_pending") == 1]
        if not pending:
            break
        nat.apply_rule_once(rule_index)
    if respond_index is not None:
        for _ in range(max(1, len(list(substrate.neighbours(root, "watches"))))):
            nat.apply_rule_once(respond_index)
    return get_meta_issues(substrate)


def record_intervention(substrate, name: str, payoff_with: float,
                        payoff_without: float) -> None:
    """Record the agent's DO-CONTRAST: the payoff measured WITH its effort's
    output active vs WITHOUT it. This is the agent investigating — actively
    intervening on its own process to see whether the effort reaches the payoff —
    not assuming. The investigation rule reads these to conclude."""
    p = register_process(substrate, name)
    substrate.set_attr(p, "payoff_with", float(payoff_with))
    substrate.set_attr(p, "payoff_without", float(payoff_without))
    substrate.set_attr(p, "investigated", 1)


def investigate(substrate, name: str, measure_payoff) -> tuple | None:
    """The agent investigates a flagged process by DO-CONTRAST, driven entirely by
    the intervention DECLARED IN THE SEED (no per-process Python): toggle the named
    graph attr to its with/without values and measure the payoff each way.
    `measure_payoff()` is the only world-I/O — a thin callable the caller passes
    (e.g. 'recognition accuracy'). Records the result for the conclusion rule.
    Returns (payoff_with, payoff_without) or None if the process declares no
    intervention."""
    p = register_process(substrate, name)
    a = substrate.node(p)["attrs"]
    if not a.get("has_intervention"):
        return None
    ttype = a.get("intervention_toggle_type")
    tattr = a.get("intervention_toggle_attr")
    node = next((n for n in substrate.nodes(ttype)), None)
    if node is None:
        node = substrate.add_node(ttype, {"origin": "meta_monitor"})
    substrate.set_attr(node, tattr, float(a.get("intervention_with", 1.0)))
    with_val = float(measure_payoff())
    substrate.set_attr(node, tattr, float(a.get("intervention_without", 0.0)))
    without_val = float(measure_payoff())
    record_intervention(substrate, name, with_val, without_val)
    return (with_val, without_val)


def install_investigation_rule(substrate) -> dict:
    """The agent's CONCLUSION from its do-contrast, as a Rule: if toggling the
    process's output barely moves the payoff (|with - without| <= connection_band)
    the effort does NOT reach the payoff -> `disconnected_lever` (the lever is the
    wrong one — look elsewhere). Otherwise the effort DOES matter, so the flag
    stays `effort_without_payoff` (a connected-but-hard problem). Decided from
    MEASUREMENT, not assumption. Returns {'rule_index'}."""
    nat = _native(substrate)
    P = Var("P")
    band = Attr(P, "connection_band")
    signed = Minus(a=Attr(P, "payoff_with"), b=Attr(P, "payoff_without"))
    disconnected = Lte(a=Abs(signed), b=band)     # toggling barely moves payoff
    helps = Gt(a=signed, b=band)                  # using the effort raises payoff
    # Three-way verdict from the MEASURED direction, never assumed:
    #   |delta| small      -> disconnected_lever (effort can't reach payoff)
    #   with >> without    -> lever_helps (the effort works; the fix is to USE it)
    #   with << without    -> lever_harms (the effort is COUNTERPRODUCTIVE; stop)
    issue_next = IfThenElse(
        disconnected, Lit("disconnected_lever"),
        IfThenElse(helps, Lit("lever_helps"), Lit("lever_harms")))
    rule = {
        "name": "investigate_connection",
        "match": [["R", "watches", "P"]],
        "where": Eq(a=Attr(P, "investigated"), b=Lit(1)).to_dict(),
        "effects": [
            ["set_attr", "P", "meta_issue", {"__term__": issue_next.to_dict()}],
            ["set_attr", "P", "investigated", 0],
        ],
    }
    return {"rule_index": nat.add_rule(rule)}


def agent_conclude_investigation(substrate, rule_index: int,
                                 max_iters: int = 100) -> list:
    """Fire the investigation rule over every process whose do-contrast just
    landed. Returns the current meta-issues."""
    nat = _native(substrate)
    root = _root(substrate)
    for _ in range(max_iters):
        pend = [p for p in substrate.neighbours(root, "watches")
                if substrate.node(p)["attrs"].get("investigated") == 1]
        if not pend:
            break
        nat.apply_rule_once(rule_index)
    return get_meta_issues(substrate)


def get_meta_issues(substrate) -> list:
    """Processes the monitor currently flags, as {name, issue, effort_rise,
    payoff_change} — what the agent reads to decide to stop/redirect a process."""
    out = []
    for p in substrate.neighbours(_root(substrate), "watches"):
        a = substrate.node(p)["attrs"]
        if a.get("meta_issue") not in (None, "", "none"):
            out.append({"name": a.get("name"), "issue": a.get("meta_issue"),
                        "effort_rise": a.get("effort_rise"),
                        "payoff_change": a.get("payoff_change")})
    return out


__all__ = ["register_process", "report", "install_meta_issue_rule",
           "set_process_controls", "install_meta_response_rule",
           "agent_check_meta", "get_meta_issues",
           "record_intervention", "investigate", "install_investigation_rule",
           "agent_conclude_investigation"]
