#!/usr/bin/env python3
"""no_assistance_gate — THE GRADUATION GATE: a standing, re-runnable proof that
the full self-improvement loop closes with ZERO hosted-LLM assistance and ZERO
human framing beyond the sanctioned NL surface.

What "no assistance" means here, precisely:

  * ``OZMA_NO_LLM=1`` is set BEFORE boot (domains/no_llm.py), so ANY hosted-LLM
    call attempted anywhere in the runtime raises and fails the gate.
  * The only inputs after boot are the ones a HUMAN has at the chat UI:
      - ``converse()`` turns (plain NL: an instruction, a steering sentence,
        a question),
      - ``flag_reply_turn`` (the UI's flag button on a bad reply),
    plus the daemon's own mechanical tick hooks, exactly as the daemon runs
    them: ``tick()``, ``_steer_tick``, ``_concern_tick``, ``_dispatch_tick``
    (real subprocess children), ``_close_tick``, ``_narrate_tick``.
  * NO direct calls to reflective_faculty internals, NO hand-minted
    Experiment/SeedDelta/variant, NO direct graph mutation. This is enforced
    by SOURCE DISCIPLINE, not comments: ``audit_source_discipline()`` walks
    this module's own AST and fails the gate if any forbidden call appears
    (see ``_FORBIDDEN_CALLS`` — the ink-decode gate's no-Python-decision
    source-audit precedent).

The cycles it drives (both closed live in prior waves via test drivers; here
they must close through the PUBLIC surface only, in one script, under the
no-LLM switch):

  CYCLE A (cue family, agent 1): an uncovered instruction ("Condense the
  data.") files an instruction gap + honest floor reply -> NL promote ("Work
  on the condense data gap.") -> _steer_tick executes the human-gated promote
  -> _concern_tick grounds it -> the agent's own author rule mints a
  conversation Experiment whose delta carries the graph-picked cue-set edit
  -> _dispatch_tick spawns scripts/convo_child_run.py -> the child validates
  the edit on the replayed corpus -> the agent's own judge rule reads
  supported -> _close_tick adopts (teaches the Concept) -> the SAME
  instruction is now handled.

  NEGATIVE CONTROL (adoption safety, agent 2): two flagged identity turns +
  ONE unflagged identity turn -> NL promote -> the graph-picked ablation
  fixes both flagged turns but breaks the unflagged one (net score +1,
  regressions 1) -> the judge reads supported — and seeds/adoption_safety.
  json's regression veto DENIES adoption: the parent's rule survives,
  behaviour unchanged, and the denial + reason are readable over NL
  ("What are you working on?").

  CYCLE B (ablation family, agent 2, after the control): the human flags the
  remaining regressing turn too -> NL promote (a SECOND concern) -> a fresh
  Experiment -> now zero regressions -> supported -> adopted -> the parent's
  identity reply actually changes.

Every cycle emits an audit-trail record (concern id, promoted-by, experiment
id, the variation op the graph chose, child result, judge outcome, adoption
id, before/after replies); the gate writes them to ``<out>/audit.json`` with
a pass/fail summary and prints the same. If a link genuinely cannot fire
unassisted, the gate says which one, honestly — it never fakes a pass.

Run:
    PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/no_assistance_gate.py \\
        [--keep-runs] [--no-guard-seeds] [--budget SECS]
"""
from __future__ import annotations

import argparse
import ast
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python"), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import os  # noqa: E402  (kept below sys.path block for symmetry with the sibling gate)


# ---------------------------------------------------------------------------
# SOURCE DISCIPLINE — the "no hand-assistance" claim as an enforced property
# of this file, not a comment. Any call to one of these anywhere in this
# module (except inside string literals, which the AST walk never sees as
# calls) fails the gate.
# ---------------------------------------------------------------------------
_FORBIDDEN_CALLS = frozenset({
    # reflective_faculty / experiment internals — the agent's own machinery,
    # which the human surface never calls directly:
    "induce_concern", "ground_concern", "compose_design_for_goal",
    "mint_experiment", "close_experiment_loop", "perform_adoptions",
    "promote_self_concern", "repromote_self_concern",
    "_compose_experiment_rule", "_compose_cue_variant", "_compose_reply_ablation",
    "_pick_variation_op", "_pick_reply_rule",
    # direct graph mutation / rule installation — never from this script:
    "add_node", "add_edge", "add_edge_unchecked", "set_attr", "del_attr",
    "add_rule", "remove_rule", "import_rules", "load_seed_manifest", "teach",
    "run_rules",
})


def audit_source_discipline() -> list:
    """AST-walk THIS module's source; return every forbidden call site (empty =
    clean). A call is forbidden by NAME whether plain (`teach(...)`) or an
    attribute (`rf.induce_concern(...)`, `agent.s.add_node(...)`)."""
    src = Path(__file__).read_text()
    tree = ast.parse(src)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
            if name in _FORBIDDEN_CALLS:
                hits.append(f"line {node.lineno}: forbidden call {name!r}")
    return hits


# ---------------------------------------------------------------------------
# Mechanical graph READS (observability only — no mutation, no decisions).
# ---------------------------------------------------------------------------
def _convo_experiments(adapter) -> list:
    out = []
    for n in adapter.s.nodes("Experiment"):
        if not adapter.s.has_node(n):
            continue
        at = adapter.s.node(n)["attrs"]
        if at.get("game") == "conversation":
            out.append((n, at))
    return sorted(out, key=lambda t: int(t[0].value))


def _delta_attrs(adapter, exp) -> dict:
    for d in adapter.inner.neighbours(exp, "has_delta"):
        if adapter.s.has_node(d):
            return dict(adapter.s.node(d)["attrs"])
    return {}


def _variation_op_of(delta: dict):
    """Mechanical read-off of WHICH variation family the graph chose, from the
    delta attrs the agent's own author rule wrote (cue_edit / ablation flags)."""
    if delta.get("cue_edit") == 1.0:
        return "cue_set_edit"
    if delta.get("ablation") == 1.0:
        return "reply_ablation"
    if delta.get("edit_op_kind"):
        return "structural_edit"
    if delta.get("act_shift") is not None:
        return "threshold_shift"
    return None


def _child_result(adapter, exp) -> dict:
    run_dir = adapter.s.node(exp)["attrs"].get("run_dir") or ""
    try:
        with open(Path(run_dir) / "result.json") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def _instruction_gaps(adapter, content=None) -> list:
    out = []
    for sc in adapter.s.nodes("SelfConcern"):
        if not adapter.s.has_node(sc):
            continue
        at = adapter.s.node(sc)["attrs"]
        if at.get("kind") == "instruction" and (content is None or at.get("content") == content):
            out.append((int(sc.value), dict(at)))
    return out


def _live_rule_names(adapter) -> set:
    return {r.get("name") for r in adapter.inner.export_rules() if r.get("active", True)}


# ---------------------------------------------------------------------------
# THE PUMP — tick() + the daemon's own mechanical hooks, nothing else.
# ---------------------------------------------------------------------------
def _pump(adapter, jd, state, runs_dir, until, label: str,
          budget_s: float = 420.0, narrations: list | None = None) -> bool:
    t0 = time.time()
    while time.time() - t0 < budget_s:
        adapter.tick()
        jd._steer_tick(adapter, state)
        jd._concern_tick(adapter)
        jd._dispatch_tick(adapter, str(runs_dir))
        jd._close_tick(adapter)
        try:
            told = jd._narrate_tick(state)
            if told is not None and narrations is not None:
                narrations.append(told.get("reply"))
        except Exception:  # noqa: BLE001 — narration is a bonus, never the gate
            pass
        if until():
            return True
        time.sleep(0.1)
    print(f"  [pump timeout] {label} did not complete within {budget_s:.0f}s", flush=True)
    return until()


class _Check:
    """Collects [PASS]/[FAIL] lines and the overall verdict."""

    def __init__(self):
        self.items = []
        self.ok = True

    def __call__(self, ok: bool, label: str) -> bool:
        ok = bool(ok)
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}", flush=True)
        self.items.append({"ok": ok, "label": label})
        self.ok &= ok
        return ok


# ---------------------------------------------------------------------------
# CYCLE A — cue family (uncovered instruction -> cue-set-edit adoption).
# ---------------------------------------------------------------------------
def run_cycle_cue(adapter, jd, state, runs_dir, check: _Check,
                  budget_s: float = 420.0) -> dict:
    rec: dict = {"cycle": "A", "family": "cue_set_edit",
                 "instruction": "Condense the data.", "narrations": []}

    adapter.converse("Hello.", speech_act="greeting")   # unflagged regression-guard turn
    before = adapter.converse("Condense the data.", speech_act="request")
    rec["before_reply"] = before
    check("filed it as a gap" in (before or "").lower(),
          "cycle A: the uncovered instruction gets the honest gap-filing floor reply")
    gaps = _instruction_gaps(adapter, "condense data")
    check(len(gaps) == 1, "cycle A: exactly one instruction SelfConcern filed for 'condense data'")
    rec["concern_id"] = gaps[0][0] if gaps else None

    steer = adapter.converse("Work on the condense data gap.", speech_act="request")
    rec["promoted_by"] = {"nl_turn": "Work on the condense data gap.", "reply": steer}
    check((steer or "").lower().startswith("promoting:"),
          "cycle A: the NL steering turn is acknowledged ('Promoting: ...')")

    def _closed():
        for _n, at in _convo_experiments(adapter):
            if at.get("adopted") or at.get("adopt_denied"):
                return True
        return False

    _pump(adapter, jd, state, runs_dir, _closed, "cycle A close",
          budget_s=budget_s, narrations=rec["narrations"])

    exps = _convo_experiments(adapter)
    check(len(exps) == 1, "cycle A: the agent's own author rule minted exactly one conversation Experiment")
    if not exps:
        return rec
    exp, at = exps[-1]
    delta = _delta_attrs(adapter, exp)
    result = _child_result(adapter, exp)
    rec.update({
        "experiment_id": int(exp.value),
        "axis_tag": at.get("axis_tag"),
        "variation_op": _variation_op_of(delta),
        "delta": {k: delta.get(k) for k in
                  ("cue_edit", "cue_concept_added", "cue_route", "add_concepts",
                   "remove_rules", "ablation", "act_rule_varied")},
        "child_result": result,
        "judge_outcome": at.get("outcome"),
        "regressions": at.get("regressions"),
    })
    check(rec["variation_op"] == "cue_set_edit",
          "cycle A: the graph (variation_pick Program via the author rule) chose the cue_set_edit family")
    check(delta.get("cue_concept_added") == "condense",
          "cycle A: the delta carries the Concept for the gap's own verb ('condense')")
    check(result.get("status") == "done" and int(result.get("regressions") or 0) == 0,
          "cycle A: the child completed with zero regressions")
    check(at.get("outcome") == "supported", "cycle A: the agent's own judge rule read 'supported'")
    check(at.get("regressions") == 0,
          "cycle A: the ingest carried the child's regressions count onto the Experiment (0)")
    check(bool(at.get("adopted")) and not at.get("adopt_denied"),
          "cycle A: the winner was ADOPTED (cue Concept taught), not denied")

    adoptions = [int(n.value) for n in adapter.s.nodes("Adoption")
                 if adapter.s.node(n)["attrs"].get("cue_concept_added") == "condense"]
    rec["adoption_id"] = adoptions[0] if adoptions else None
    check(len(adoptions) == 1, "cycle A: exactly one Adoption record minted for the cue Concept")

    after = adapter.converse("Condense the data.", speech_act="request")
    rec["after_reply"] = after
    check("filed it as a gap" not in (after or "").lower() and (after or "").strip() != (before or "").strip(),
          "cycle A: the SAME instruction is now handled (reply changed, no gap floor)")
    check(len(_instruction_gaps(adapter, "condense data")) == 1,
          "cycle A: no duplicate instruction gap filed after adoption")
    return rec


# ---------------------------------------------------------------------------
# NEGATIVE CONTROL + CYCLE B — ablation family on a second agent.
# ---------------------------------------------------------------------------
_NOTE_1 = "identity reply rule wrong: test ablate the reply variant"
_NOTE_2 = "identity reply still misroutes: test ablate the reply variant too"
_NOTE_3 = "identity reply wrong here as well"


def run_control_and_cycle_ablation(adapter, jd, state, runs_dir, check: _Check,
                                   budget_s: float = 420.0) -> tuple:
    control: dict = {"cycle": "negative_control", "family": "reply_ablation", "narrations": []}
    rec: dict = {"cycle": "B", "family": "reply_ablation", "narrations": []}

    adapter.converse("Hello.", speech_act="greeting")   # unflagged, unaffected by the ablation
    turns = []
    replies = []
    for _ in range(3):
        replies.append(adapter.converse("What are you?", speech_act="question"))
        turns.append(adapter.last_turn_inbound_id())
    control["before_reply"] = rec["before_reply"] = replies[0]
    check(all((r or "").strip() == "I am Jabberwock." for r in replies),
          "control: the identity reply is the known baseline on all three turns")

    # THE HUMAN'S FLAG BUTTON (sanctioned UI surface): flag turns 1+2; turn 3
    # stays unflagged — the deliberately-regressing arm.
    f1 = jd.flag_reply_turn(adapter, str(turns[0]), _NOTE_1)
    f2 = jd.flag_reply_turn(adapter, str(turns[1]), _NOTE_2)
    check(f1.get("ok") and f2.get("ok"), "control: both flag_reply_turn calls filed reply_fix concerns")
    control["concern_id"] = f1.get("concern_id")

    steer = adapter.converse("Work on the identity reply gap.", speech_act="request")
    control["promoted_by"] = {"nl_turn": "Work on the identity reply gap.", "reply": steer}
    check((steer or "").lower().startswith("promoting:"),
          "control: the NL steering turn is acknowledged")

    def _first_closed():
        exps = _convo_experiments(adapter)
        return bool(exps) and bool(exps[0][1].get("adopted") or exps[0][1].get("adopt_denied"))

    _pump(adapter, jd, state, runs_dir, _first_closed, "negative-control close",
          budget_s=budget_s, narrations=control["narrations"])

    exps = _convo_experiments(adapter)
    check(len(exps) == 1, "control: exactly one conversation Experiment minted so far")
    if not exps:
        return control, rec
    exp1, at1 = exps[0]
    delta1 = _delta_attrs(adapter, exp1)
    result1 = _child_result(adapter, exp1)
    control.update({
        "experiment_id": int(exp1.value), "axis_tag": at1.get("axis_tag"),
        "variation_op": _variation_op_of(delta1),
        "delta": {k: delta1.get(k) for k in ("remove_rules", "ablation", "act_rule_varied")},
        "child_result": result1, "judge_outcome": at1.get("outcome"),
        "regressions": at1.get("regressions"),
        "adopt_denied": bool(at1.get("adopt_denied")),
        "adopt_denied_reason": at1.get("adopt_denied_reason"),
        "adoption_id": None,
    })
    check(control["variation_op"] == "reply_ablation",
          "control: the graph chose the reply_ablation family")
    check(delta1.get("act_rule_varied") == "reply_self_identity",
          "control: the agent's own provenance Argmax picked reply_self_identity to ablate")
    check(result1.get("status") == "done" and int(result1.get("score") or 0) > 0
          and int(result1.get("regressions") or 0) >= 1,
          "control: the child scored NET-POSITIVE with >=1 regression (the exact hole the "
          "safety gate closes)")
    check(at1.get("outcome") == "supported",
          "control: the judge (score sign) still reads 'supported' — the veto, not the judge, "
          "must stop it")
    check(int(at1.get("regressions") or -1) >= 1,
          "control: the ingest carried the child's regressions count onto the Experiment")
    check(bool(at1.get("adopt_denied")) and not at1.get("adopted"),
          "control: adoption was DENIED by the agent's own adopt_denied_on_regression rule "
          "(seeds/adoption_safety.json) — supported-but-regressing is never adopted")
    check(bool(at1.get("adopt_denied_reason")),
          "control: the denial carries an honest recorded reason")
    check("reply_self_identity" in _live_rule_names(adapter),
          "control: the parent's reply rule SURVIVED (behaviour unchanged)")

    # ------------------------------------------------------------------ CYCLE B
    # The human flags the remaining (regressing) turn too, then promotes the
    # second concern — now the ablation regresses nothing, and adoption goes
    # through. This is the honest repair path the veto pointed at.
    f3 = jd.flag_reply_turn(adapter, str(turns[2]), _NOTE_3)
    check(f3.get("ok"), "cycle B: the third identity turn is flagged too")
    rec["concern_id"] = f2.get("concern_id")

    steer2 = adapter.converse("Work on the identity reply gap.", speech_act="request")
    rec["promoted_by"] = {"nl_turn": "Work on the identity reply gap.", "reply": steer2}
    check((steer2 or "").lower().startswith("promoting:"),
          "cycle B: the second NL steering turn is acknowledged (a SECOND concern promotes)")

    def _second_closed():
        exps2 = _convo_experiments(adapter)
        return len(exps2) >= 2 and bool(exps2[1][1].get("adopted") or exps2[1][1].get("adopt_denied"))

    _pump(adapter, jd, state, runs_dir, _second_closed, "cycle B close",
          budget_s=budget_s, narrations=rec["narrations"])

    exps2 = _convo_experiments(adapter)
    check(len(exps2) == 2, "cycle B: a SECOND conversation Experiment was minted for the second concern")
    if len(exps2) < 2:
        return control, rec
    exp2, at2 = exps2[1]
    delta2 = _delta_attrs(adapter, exp2)
    result2 = _child_result(adapter, exp2)
    rec.update({
        "experiment_id": int(exp2.value), "axis_tag": at2.get("axis_tag"),
        "variation_op": _variation_op_of(delta2),
        "delta": {k: delta2.get(k) for k in ("remove_rules", "ablation", "act_rule_varied")},
        "child_result": result2, "judge_outcome": at2.get("outcome"),
        "regressions": at2.get("regressions"),
    })
    check(rec["variation_op"] == "reply_ablation", "cycle B: ablation family again")
    check(result2.get("status") == "done" and int(result2.get("regressions") or 0) == 0,
          "cycle B: with every affected turn flagged, the child reports zero regressions")
    check(at2.get("outcome") == "supported", "cycle B: judged supported")
    check(bool(at2.get("adopted")) and not at2.get("adopt_denied"),
          "cycle B: ADOPTED — the ablation folded back into the parent")
    adoptions = [int(n.value) for n in adapter.s.nodes("Adoption")
                 if adapter.s.node(n)["attrs"].get("rule_removed") == "reply_self_identity"]
    rec["adoption_id"] = adoptions[0] if adoptions else None
    check(len(adoptions) == 1, "cycle B: exactly one Adoption record for the ablated rule")
    check("reply_self_identity" not in _live_rule_names(adapter),
          "cycle B: the ablated rule is tombstoned in the parent")

    after = adapter.converse("What are you?", speech_act="question")
    rec["after_reply"] = after
    control["after_reply"] = after
    check((after or "").strip() != "I am Jabberwock.",
          "cycle B: the parent's own reply behaviour actually changed")

    # THE VETO IS READABLE OVER NL — the same status question a human asks,
    # through answer_question (the question surface test_nl_steering_migrated
    # already gates end-to-end for this exact phrasing). KNOWN PRE-EXISTING
    # RESIDUAL, not this gate's: converse()'s table-meta routing does not yet
    # serve the self_improvement_status reader ("What are you working on?"
    # over converse answers "I don't hold that." on an unmodified fresh boot
    # too) — a Python-frontend gap of exactly the find-and-file class, out of
    # this gate's scope.
    status_reply = adapter.answer_question("What are you working on?")
    control["status_reply"] = status_reply
    check("blocked from adoption" in (status_reply or ""),
          "control: 'What are you working on?' surfaces the blocked adoption")
    check("regressions" in (status_reply or ""),
          "control: the surfaced denial carries the regression reason")
    return control, rec


# ---------------------------------------------------------------------------
# THE GATE
# ---------------------------------------------------------------------------
# close_experiment_loop teach()es real verdicts + the cue adoption teach()es
# the winning Concept into checked-in seeds; guard them so a CLI run leaves no
# debris (same guard as scripts/autonomous_improvement_gate.py / the wave
# tests). Under pytest the session-wide OZMA_SEED_PERSIST_DISABLED guard
# already blocks the writes; this snapshot/restore makes the CLI run safe too.
_GUARDED_SEEDS = (
    ROOT / "seeds" / "experiment_conclusions.json",
    ROOT / "seeds" / "comprehend_instruction.json",
)


def run_gate(out_dir: Path, budget_s: float = 420.0, keep_runs: bool = False) -> dict:
    os.environ["OZMA_NO_LLM"] = "1"    # BEFORE boot: any hosted call now raises
    import jabberwock_daemon as jd
    from domains.no_llm import no_llm
    from domains.experiment_dispatch import _INFLIGHT

    check = _Check()
    print("=" * 96)
    print("NO-ASSISTANCE GRADUATION GATE — OZMA_NO_LLM=1; NL surface + daemon hooks only.")
    print("=" * 96)
    check(no_llm(), "OZMA_NO_LLM is armed (any hosted-LLM call raises and fails this gate)")

    violations = audit_source_discipline()
    for v in violations:
        print(f"    source-discipline violation: {v}")
    check(not violations,
          "source discipline: this script calls NO reflective_faculty internals, hand-mints "
          "NOTHING, mutates NO graph state (AST-audited, not asserted by comment)")

    out_dir.mkdir(parents=True, exist_ok=True)
    runs_dir = out_dir / "runs"
    audit: dict = {"no_llm": True, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "source_discipline_violations": violations, "cycles": []}

    # ---- agent 1: cycle A (cue family) --------------------------------------
    ckpt1 = Path(tempfile.mkdtemp(prefix="jbw_nogate_ckpt1_"))
    t0 = time.time()
    adapter1, booted1 = jd.boot(ckpt1, "full")
    print(f"\nagent 1 boot: {booted1!r}, {adapter1.s.node_count()} nodes, {time.time()-t0:.1f}s")
    check(booted1 == "seeds", "agent 1: fresh full-seed boot (not a checkpoint resume)")
    state1 = jd.DaemonState(adapter1, booted1)
    state1.chat_history_path = out_dir / "chat1.json"
    _INFLIGHT.clear()
    print("\n--- CYCLE A (cue family) " + "-" * 60)
    cycle_a = run_cycle_cue(adapter1, jd, state1, runs_dir / "a", check, budget_s=budget_s)
    audit["cycles"].append(cycle_a)

    # ---- agent 2: negative control + cycle B (ablation family) --------------
    ckpt2 = Path(tempfile.mkdtemp(prefix="jbw_nogate_ckpt2_"))
    t0 = time.time()
    adapter2, booted2 = jd.boot(ckpt2, "full")
    print(f"\nagent 2 boot: {booted2!r}, {adapter2.s.node_count()} nodes, {time.time()-t0:.1f}s")
    check(booted2 == "seeds", "agent 2: fresh full-seed boot")
    state2 = jd.DaemonState(adapter2, booted2)
    state2.chat_history_path = out_dir / "chat2.json"
    _INFLIGHT.clear()
    print("\n--- NEGATIVE CONTROL + CYCLE B (ablation family) " + "-" * 36)
    control, cycle_b = run_control_and_cycle_ablation(adapter2, jd, state2, runs_dir / "b",
                                                     check, budget_s=budget_s)
    audit["negative_control"] = control
    audit["cycles"].append(cycle_b)

    closed = [c for c in audit["cycles"]
              if c.get("judge_outcome") == "supported" and c.get("adoption_id") is not None]
    check(len(closed) >= 2,
          f"GRADUATION: {len(closed)} full cycles closed unassisted (concern -> NL promote -> "
          "experiment -> graph-picked variation -> real child -> judge -> adopt -> behaviour "
          "changed), N >= 2 required")

    audit["summary"] = {
        "pass": check.ok,
        "cycles_closed": len(closed),
        "negative_control_denied": bool(control.get("adopt_denied")),
        "checks": check.items,
        "finished": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    audit_path = out_dir / "audit.json"
    with open(audit_path, "w") as f:
        json.dump(audit, f, indent=2, default=str)
    print("\n" + "=" * 96)
    print(("GATE PASSES" if check.ok else "GATE FAILS") +
          f" — audit trail: {audit_path}" + ("" if keep_runs else " (removed unless --keep-runs)"))
    print("=" * 96)

    # cleanup of the throwaway checkpoints (the audit stays with out_dir policy)
    shutil.rmtree(ckpt1, ignore_errors=True)
    shutil.rmtree(ckpt2, ignore_errors=True)
    return audit


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None, help="output dir (default: runs/no_assistance_gate/<stamp>)")
    ap.add_argument("--budget", type=float, default=420.0, help="per-pump wall budget, seconds")
    ap.add_argument("--keep-runs", action="store_true")
    ap.add_argument("--no-guard-seeds", action="store_true",
                    help="don't snapshot/restore the seeds the adoption path teach()es into")
    args = ap.parse_args(argv)

    stamp = time.strftime("%Y%m%dT%H%M%S")
    out_dir = Path(args.out) if args.out else ROOT / "runs" / "no_assistance_gate" / stamp

    guard = not args.no_guard_seeds
    before = {}
    if guard:
        for p in _GUARDED_SEEDS:
            before[p] = p.read_text() if p.exists() else None
    try:
        audit = run_gate(out_dir, budget_s=args.budget, keep_runs=args.keep_runs)
        return 0 if audit["summary"]["pass"] else 1
    finally:
        if guard:
            for p, content in before.items():
                if content is not None:
                    p.write_text(content)
                elif p.exists():
                    p.unlink()
        if not args.keep_runs:
            shutil.rmtree(out_dir / "runs", ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
