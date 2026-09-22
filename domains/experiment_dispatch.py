"""experiment_dispatch — the experiment-dispatch MECHANISM (host I/O only, CLAUDE.md).

The DECISION to run an experiment is the agent's: it mints an ``Experiment`` node
(``status="requested"``) via its own rules when it wants to test a hypothesis
about its own seeds/rules. This module does not decide that, does not decide
WHAT to try, and does not interpret results — it only:

  1. **sees** a requested ``Experiment`` node,
  2. **snapshots** the parent agent's current mind (``WorldAdapter.save``),
  3. **spawns** ``scripts/arc_child_run.py`` as a detached child process to play
     the episode out-of-process (so the parent's own tick loop is never blocked
     by an experiment run), and
  4. **ingests** the finished child's ``result.json`` / ``trace.jsonl`` back into
     the parent graph as ``Run`` + ``RunObservation`` nodes, per the node
     vocabulary the daemon agent and web UI are built against.

Node vocabulary (fixed contract — do not deviate):
    Experiment{hypothesis, game, status, run_dir}
      -has_delta-> SeedDelta{skip_seeds: JSON list, add_rules: JSON list,
                              remove_rules: JSON list of rule NAMES to tombstone
                              on the dispatched copy before add_rules installs its
                              replacement — see scripts/arc_child_run.py,
                              add_concepts: JSON list of {type, attrs} nodes to add
                              on the dispatched copy (Wave 5 cue-set-edit family),
                              remove_concepts: JSON list of Concept NAMES to retract}
      -produced-> Run{run_id, game, status, frames, score}
                    -observed-> RunObservation{frame, action, score, reasoning, self_report}

``scan_and_dispatch`` is NON-BLOCKING: it spawns via ``subprocess.Popen`` (never
waits) and polls previously-spawned children with ``proc.poll()`` (never
``.wait()``). Call it from whatever tick/loop cadence the host already runs;
it is safe to call repeatedly and does nothing when there is nothing to do.

Node-id caution (see CLAUDE.md / scripts/arc_run.py): ids recycle from a
freelist with no generation counter — every raw id this module holds across a
call boundary (the in-flight pid cache) is guarded with ``has_node`` before
``node()``.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_CHILD_RUNNER = _ROOT / "scripts" / "arc_child_run.py"
# Name-keyed runner registry (the fetch_dispatch registry pattern): the
# Experiment's own `game` attr — data the AGENT's mint rule wrote — selects
# which mechanical child runner plays the episode. A game not named here is an
# ARC game and goes to arc_child_run.py exactly as before. Pure lookup on data
# already on the node, not a policy decision.
_CHILD_RUNNERS = {
    "conversation": _ROOT / "scripts" / "convo_child_run.py",
    "humanoid_development": _ROOT / "scripts" / "humanoid_child_run.py",
}
_PYTHONPATH_EXTRA = os.pathsep.join([str(_ROOT), str(_ROOT / "runners" / "dsl" / "python")])

# The offline arc3_env games (dispatch runs offline whenever `game` names one of these — a
# mechanical lookup on data already on the Experiment node, not a policy decision). Anything
# else is assumed to be a live ARC-AGI-3 game id (e.g. "ls20-9607627b") and dispatched live.
try:
    sys.path.insert(0, str(_ROOT / "scripts"))
    from arc3_env import ENVS as _OFFLINE_GAMES        # noqa: E402
except Exception:                                       # pragma: no cover - arc3_env should always import
    _OFFLINE_GAMES = {}

# Host bookkeeping cache ONLY (never the source of truth — the graph is): experiment node's
# int id -> {"proc": Popen, "run_dir": Path, "node": NodeID}. Lets repeated scan_and_dispatch
# calls in the SAME process find a child it already spawned without re-spawning it. A dispatcher
# restarted in a fresh process loses this cache — since Wave 6 that is RECOVERABLE, not fatal:
# `_spawn` persists `child_pid` + `result_path` onto the Experiment node (graph state), and
# `scan_and_dispatch`'s `status == "running"` recovery branch ingests the finished child's
# result.json (or marks a dead-with-no-result child failed{orphaned}).
_INFLIGHT: dict = {}


def _run_dir_for(runs_dir, exp_id: int) -> Path:
    n = 0
    while True:
        d = Path(runs_dir) / f"{exp_id}-{n}"
        if not d.exists():
            return d
        n += 1


def mint_experiment(agent, hypothesis: str, game: str, skip_seeds=(), add_rules=(),
                    remove_rules=(), add_concepts=(), remove_concepts=(),
                    set_node_attrs=()) -> "object":
    """Hand-mint an Experiment + SeedDelta node. A test/authoring helper — the agent will
    later mint these itself via its own rules (not this function's concern); this exists so
    the dispatch MECHANISM can be exercised/tested without that agent-authoring machinery."""
    S, I = agent.s, agent.inner
    exp = S.add_node("Experiment", {"hypothesis": str(hypothesis), "game": str(game),
                                    "status": "requested", "run_dir": ""})
    delta = S.add_node("SeedDelta", {"skip_seeds": json.dumps(list(skip_seeds)),
                                     "add_rules": json.dumps(list(add_rules)),
                                     "remove_rules": json.dumps(list(remove_rules)),
                                     "add_concepts": json.dumps(list(add_concepts)),
                                     "remove_concepts": json.dumps(list(remove_concepts)),
                                     "set_node_attrs": json.dumps(list(set_node_attrs))})
    I.add_edge_unchecked(exp, "has_delta", delta)
    return exp


def _seed_delta_of(agent, exp) -> dict:
    S, I = agent.s, agent.inner
    for d in I.neighbours(exp, "has_delta"):
        if not I.has_node(d):
            continue
        a = S.node(d)["attrs"]
        try:
            skip = json.loads(a.get("skip_seeds") or "[]")
        except Exception:
            skip = []
        try:
            rules = json.loads(a.get("add_rules") or "[]")
        except Exception:
            rules = []
        try:
            remove = json.loads(a.get("remove_rules") or "[]")
        except Exception:
            remove = []
        try:
            add_concepts = json.loads(a.get("add_concepts") or "[]")
        except Exception:
            add_concepts = []
        try:
            remove_concepts = json.loads(a.get("remove_concepts") or "[]")
        except Exception:
            remove_concepts = []
        try:
            set_node_attrs = json.loads(a.get("set_node_attrs") or "[]")
        except Exception:
            set_node_attrs = []
        # WHERE-CLAUSE-VARIATION (rule_literal_edit family): the marker +
        # structural witness convo_child_run's controlled double-pass reads
        # to decide whether to DEFER add_rules/remove_rules and what to count
        # fires of — see reflective_faculty._compose_rule_literal_variant /
        # _rule_effect_witness. Mechanical copy of node attrs already written
        # by the agent's own mint rule, same as every other key here.
        # COMPOSER-CAPABILITY (datum_feedback_rule / shape_mint families):
        # the SAME class of marker copy — convo_child_run's controlled
        # double-pass reads these to decide whether to defer add_rules
        # (datum_feedback_rule) or add_concepts (shape_mint) and which attr
        # names the belief/fit witness it reads before/after.
        return {"skip_seeds": skip, "add_rules": rules, "remove_rules": remove,
                "add_concepts": add_concepts, "remove_concepts": remove_concepts,
                "set_node_attrs": set_node_attrs,
                "rule_literal_edit": float(a.get("rule_literal_edit") or 0.0),
                "rule_literal_witness": a.get("rule_literal_witness") or "",
                "datum_feedback_edit": float(a.get("datum_feedback_edit") or 0.0),
                "datum_feedback_datum_attr": a.get("datum_feedback_datum_attr") or "",
                "datum_feedback_belief_attr": a.get("datum_feedback_belief_attr") or "",
                "shape_mint_edit": float(a.get("shape_mint_edit") or 0.0),
                "shape_mint_name": a.get("shape_mint_name") or "",
                "shape_mint_party": a.get("shape_mint_party") or ""}
    return {"skip_seeds": [], "add_rules": [], "remove_rules": [],
            "add_concepts": [], "remove_concepts": [], "set_node_attrs": [],
            "rule_literal_edit": 0.0, "rule_literal_witness": "",
            "datum_feedback_edit": 0.0, "datum_feedback_datum_attr": "",
            "datum_feedback_belief_attr": "", "shape_mint_edit": 0.0,
            "shape_mint_name": "", "shape_mint_party": ""}


def _stamp_performance_baseline(agent, exp) -> None:
    """SELF-OPTIMISATION (efficiency objective, Wave: 2026-07-10). Mechanical copy,
    not a decision: IF this Experiment's driving concern is a promoted 'performance'
    or 'comprehension' SelfConcern (found by axis_tag == StandingConcern.name, the
    same string key reflective_faculty._compose_experiment_rule's mint rule already
    stamps onto every authored Experiment), copy the agent's OWN current shadow-read
    latency rolling average (world_adapter._record_shadow_health's
    shadow_latency_recent_avg datum) onto the dispatched SeedDelta as
    baseline_avg_turn_ms + a performance_objective marker. WHAT this comparison
    means is entirely seeds/self_optimisation.json's judge_performance_experiment_
    outcome rule's call — this only records the number the rule will read, at the
    moment of dispatch (so a later-changing live average never contaminates an
    in-flight trial's baseline)."""
    S, I = agent.s, agent.inner
    tag = str(S.node(exp)["attrs"].get("axis_tag") or "")
    if not tag:
        return
    kind = None
    for sc in S.nodes("StandingConcern"):
        if not I.has_node(sc):
            continue
        if S.node(sc)["attrs"].get("name") == tag:
            kind = S.node(sc)["attrs"].get("kind")
            break
    if kind not in ("performance", "comprehension"):
        return
    baseline = S.node(agent.agent)["attrs"].get("shadow_latency_recent_avg")
    if baseline is None:
        return
    for d in I.neighbours(exp, "has_delta"):
        if I.has_node(d):
            try:
                I.set_attr(d, "baseline_avg_turn_ms", float(baseline))
                I.set_attr(d, "performance_objective", 1.0)
            except Exception:  # noqa: BLE001 — a malformed baseline never blocks dispatch
                pass
            break


def _spawn(agent, runs_dir, exp) -> None:
    """Snapshot the parent + write the delta + launch the child, detached. Mechanical: every
    value written here is read straight off the Experiment/SeedDelta nodes or is I/O plumbing
    (paths, pids) — no decision about what the experiment should try."""
    try:
        from evaluation.p0a.legacy_io_guard import deny_direct_io
        deny_direct_io("experiment.spawn")
    except ImportError:
        pass
    S, I = agent.s, agent.inner
    a = S.node(exp)["attrs"]
    exp_int = int(exp.value)
    run_dir = _run_dir_for(runs_dir, exp_int)
    run_dir.mkdir(parents=True, exist_ok=True)
    _stamp_performance_baseline(agent, exp)

    snapshot_path = run_dir / "parent_snapshot.json"
    agent.save(str(snapshot_path))                      # mechanical: snapshot the CURRENT parent mind

    delta = _seed_delta_of(agent, exp)
    # Child-world configuration is graph data written on the Experiment.  Copy
    # it across the process boundary verbatim; the dispatcher neither chooses
    # nor interprets these values.  Existing children ignore this additive key.
    delta["experiment_attrs"] = {
        key: a.get(key)
        for key in ("protocol_path", "motor_library_path")
        if a.get(key) is not None
    }
    # PARENT-FIDELITY FLAG (RESIDUAL-CLOSURE wave): `WorldAdapter.load()`
    # deliberately restores `shadow_read=False` (bench cost); an experiment
    # child REPLAYING the parent's recorded behaviour must run the same
    # comprehension the parent ran, or a reading-layer delta (knob_edit) is
    # inert in the trial. Mechanical copy of the parent's own flag — the
    # child applies it after boot, exactly like the daemon's CLI flag does.
    delta["parent_shadow_read"] = bool(getattr(agent, "shadow_read", False))
    delta_path = run_dir / "delta.json"
    with open(delta_path, "w") as f:
        json.dump(delta, f)

    game = str(a.get("game") or "")
    runner = _CHILD_RUNNERS.get(game, _CHILD_RUNNER)
    offline = game in _OFFLINE_GAMES
    log_path = run_dir / "log.txt"
    cmd = [sys.executable, str(runner),
           "--snapshot", str(snapshot_path), "--delta", str(delta_path),
           "--game", game, "--out", str(run_dir)]
    if offline:
        cmd.append("--offline")
    child_env = dict(os.environ)
    child_env["PYTHONPATH"] = _PYTHONPATH_EXTRA + os.pathsep + child_env.get("PYTHONPATH", "")
    logf = open(log_path, "w")
    proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, cwd=str(_ROOT), env=child_env)

    I.set_attr(exp, "status", "running")
    I.set_attr(exp, "run_dir", str(run_dir))
    # Restart survivability (mechanical bookkeeping, mirrored into the GRAPH so a
    # dispatcher restarted in a fresh process — which loses the in-memory _INFLIGHT
    # cache — can recover this child: see the `status == "running"` recovery branch
    # in scan_and_dispatch below.
    I.set_attr(exp, "child_pid", int(proc.pid))
    I.set_attr(exp, "result_path", str(run_dir / "result.json"))
    _INFLIGHT[exp_int] = {"proc": proc, "run_dir": run_dir, "node": exp, "logf": logf}


def _ingest_result(agent, exp, run_dir: Path) -> None:
    """Read a finished child's result.json + trace.jsonl -> mint Run + RunObservation nodes
    into the PARENT graph, per the node-vocabulary contract. Pure mechanical I/O: read bytes,
    write graph data. The child already decided the outcome (done/failed); this only reports
    it. Always mints a Run node (even for a child that crashed before writing result.json),
    so the contract ("Experiment -produced-> Run") holds unconditionally."""
    S, I = agent.s, agent.inner
    result_path = run_dir / "result.json"
    trace_path = run_dir / "trace.jsonl"
    try:
        with open(result_path) as f:
            result = json.load(f)
    except Exception as e:
        result = {"status": "failed", "frames": 0, "score": 0,
                  "error": f"no result.json ({type(e).__name__}: {e})"}
    status = result.get("status") or "failed"
    a = S.node(exp)["attrs"]
    err = result.get("error")
    run = S.add_node("Run", {"run_id": str(run_dir.name), "game": str(a.get("game") or ""),
                             "status": str(status), "frames": int(result.get("frames") or 0),
                             "score": result.get("score") or 0,
                             **({"error": str(err)} if err else {})})
    I.add_edge_unchecked(exp, "produced", run)

    # Carry the child's own per-probe accounting (result.json extras the
    # conversation runner reports; an ARC child reports none of these) onto the
    # Run AND — for `regressions` — onto the Experiment itself, so the agent's
    # OWN rules can read it (seeds/adoption_safety.json's regression veto).
    # Mechanical copy of what the child already decided/reported: only keys
    # actually present in result.json are carried, no defaults invented.
    for key in ("flagged", "flagged_changed", "regressions"):
        if key in result:
            try:
                I.set_attr(run, key, int(result.get(key) or 0))
            except Exception:  # noqa: BLE001 — a malformed extra never blocks ingest
                pass
    if "regressions" in result:
        try:
            I.set_attr(exp, "regressions", int(result.get("regressions") or 0))
        except Exception:  # noqa: BLE001
            pass
    # SELF-OPTIMISATION (efficiency objective): the conversation child's own
    # wall-time report (scripts/convo_child_run.py) — carried onto the Run AND
    # the Experiment exactly like `regressions`, so seeds/self_optimisation.json's
    # judge_performance_experiment_outcome can read it.
    if "avg_turn_ms" in result:
        try:
            avg_ms = float(result.get("avg_turn_ms") or 0.0)
            I.set_attr(run, "avg_turn_ms", avg_ms)
            I.set_attr(exp, "avg_turn_ms", avg_ms)
        except Exception:  # noqa: BLE001
            pass
    # RESIDUAL-CLOSURE (knob_edit family): the child's CONTROLLED double-pass
    # report — reform marks minted per pass (the verdict inputs
    # seeds/self_optimisation.json's judge_knob_experiment_outcome reads:
    # variant_reforms vs control_reforms, same process, same warm caches) plus
    # per-pass shadow-latency means (informational). Mechanical copy, exactly
    # like avg_turn_ms above.
    # WHERE-CLAUSE-VARIATION (rule_literal_edit family): the SAME controlled
    # double-pass shape, reporting the picked rule's own structural WITNESS
    # fire-count per pass instead of reform marks — the verdict input
    # seeds/self_optimisation.json's judge_rule_literal_outcome reads:
    # variant_witness_fires vs control_witness_fires, compared against the
    # delta's own rule_literal_direction. Mechanical copy, same shape as
    # control_reforms/variant_reforms above.
    for key in ("control_reforms", "variant_reforms",
                "control_witness_fires", "variant_witness_fires"):
        if key in result:
            try:
                I.set_attr(run, key, int(result.get(key) or 0))
                I.set_attr(exp, key, int(result.get(key) or 0))
            except Exception:  # noqa: BLE001
                pass
    # COMPOSER-CAPABILITY (datum_feedback_rule / shape_mint families): the
    # SAME controlled double-pass shape, reporting the interlocutor
    # belief/shape-fit witness per pass instead of reform marks or rule-effect
    # fires — the verdict input seeds/self_optimisation.json's
    # judge_datum_feedback_outcome / judge_shape_mint_outcome reads:
    # variant_belief vs control_belief. Mechanical copy, same shape as
    # control_reforms/variant_reforms above.
    for key in ("control_belief", "variant_belief"):
        if key in result:
            try:
                I.set_attr(run, key, float(result.get(key) or 0.0))
                I.set_attr(exp, key, float(result.get(key) or 0.0))
            except Exception:  # noqa: BLE001
                pass
    for key in ("avg_shadow_ms", "control_shadow_ms"):
        if key in result:
            try:
                I.set_attr(run, key, float(result.get(key) or 0.0))
                I.set_attr(exp, key, float(result.get(key) or 0.0))
            except Exception:  # noqa: BLE001
                pass

    if trace_path.exists():
        with open(trace_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                obs = S.add_node("RunObservation", {
                    "frame": int(rec.get("frame") or 0), "action": str(rec.get("action") or ""),
                    "score": rec.get("score") or 0, "reasoning": str(rec.get("reasoning") or ""),
                    "self_report": str(rec.get("self_report") or "")})
                I.add_edge_unchecked(run, "observed", obs)

    I.set_attr(exp, "status", str(status))
    if err:
        I.set_attr(exp, "error", str(err))


def _pid_alive(pid: int) -> bool:
    """Mechanical liveness probe: signal-0 the pid. False for pid<=0, a dead
    pid, or a pid we cannot see. (PID recycling can in principle alias a dead
    child to an unrelated live process — the recovery branch then just keeps
    waiting for result.json, which the child's own `finally` always writes,
    so the worst case is a delayed recovery, never a wrong ingest.)"""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:                                 # exists, not ours
        return True
    except Exception:  # noqa: BLE001
        return False
    # Signal-0 SUCCEEDS on a ZOMBIE (exited but unreaped — e.g. a child whose
    # Popen was dropped without poll()/wait() after an in-process _INFLIGHT
    # reset). A zombie is dead for our purposes: its result.json, if any, is
    # final. Linux /proc read; anywhere it's unreadable, trust signal-0.
    try:
        with open(f"/proc/{pid}/stat") as f:
            # the state char is the field after the parenthesised comm (which
            # may itself contain spaces/parens — split on the LAST ')').
            state = f.read().rsplit(")", 1)[1].split()[0]
        return state != "Z"
    except Exception:  # noqa: BLE001
        return True


_PROGRESS_ATTRS = frozenset({
    "phase", "action", "action_count", "closed_receipts", "elapsed_ms",
    "decision_kind", "stage_ordinal", "goal", "active_capability",
    "mastery_count", "retained_experience_count", "selected_learning_step",
    "checkin_count", "replan_count", "continuation_authority",
})


def _sync_child_progress(agent, exp, run_dir: Path) -> bool:
    """Copy a child's atomic receipt projection into its Experiment node.

    The child has already closed the embodied receipt and the parent graph owns
    the resulting status facts.  This function performs no classification or
    control decision; it only transports an allowlisted set of scalar values.
    """
    path = run_dir / "progress.json"
    try:
        with path.open(encoding="utf-8") as handle:
            progress = json.load(handle)
    except (OSError, ValueError, TypeError):
        return False
    changed = False
    attrs = agent.s.node(exp)["attrs"]
    for key in _PROGRESS_ATTRS:
        if key not in progress or attrs.get(key) == progress[key]:
            continue
        agent.inner.set_attr(exp, key, progress[key])
        changed = True
    return changed


def scan_and_dispatch(agent, runs_dir) -> list:
    """NON-BLOCKING: dispatch every REQUESTED Experiment as a detached child process, and
    ingest results from any previously-dispatched child that has since exited. Never spawns
    a subprocess twice for the same Experiment (tracked in the module-level `_INFLIGHT` host
    cache) and never blocks waiting on one. Returns the run_dir (str) of every experiment
    touched (spawned OR completed) this call, for a caller that wants to log activity —
    scan_and_dispatch itself makes no decisions: it only reacts to `status == "requested"`
    (the agent's own prior decision) and to a child process's exit (the child's own prior
    decision, already written to result.json)."""
    S, I = agent.s, agent.inner
    Path(runs_dir).mkdir(parents=True, exist_ok=True)
    touched: list = []

    for exp in list(S.nodes("Experiment")):
        if not I.has_node(exp):
            continue
        if int(exp.value) in _INFLIGHT:
            info = _INFLIGHT[int(exp.value)]
            if _sync_child_progress(agent, exp, info["run_dir"]):
                touched.append(str(info["run_dir"]))
            continue                                    # already dispatched, awaiting completion
        status = S.node(exp)["attrs"].get("status")
        if status == "requested":
            _spawn(agent, runs_dir, exp)
            touched.append(str(_INFLIGHT[int(exp.value)]["run_dir"]))
        elif status == "running":
            # RECOVERY: an Experiment left `running` with no _INFLIGHT entry is a
            # child this PROCESS never spawned — the dispatcher was restarted (the
            # in-memory cache is documented as lost across restarts). Recover it
            # from the graph-persisted bookkeeping `_spawn` wrote (`run_dir`,
            # `child_pid`): ingest result.json once the child is finished (its own
            # `finally` always writes one), keep waiting while the pid is alive,
            # and mark a dead-with-no-result child failed{orphaned}. Mechanical:
            # reacts only to recorded facts (attrs, file existence, pid liveness).
            a = S.node(exp)["attrs"]
            rd = str(a.get("run_dir") or "")            # NB: Path("") is ".", so gate on the raw string
            run_dir = Path(rd) if rd else None
            try:
                pid = int(a.get("child_pid") or 0)
            except (TypeError, ValueError):
                pid = 0
            alive = _pid_alive(pid)
            if run_dir is not None:
                _sync_child_progress(agent, exp, run_dir)
            has_result = run_dir is not None and (run_dir / "result.json").exists()
            if has_result and not alive:
                _ingest_result(agent, exp, run_dir)
                touched.append(str(run_dir))
            elif not alive:
                # dead child, no result.json (or no run_dir recorded at all)
                if run_dir is not None and run_dir.exists():
                    _ingest_result(agent, exp, run_dir)     # mints the failed Run (contract holds)
                else:
                    I.set_attr(exp, "status", "failed")
                I.set_attr(exp, "error",
                           "orphaned: dispatcher restarted; child process is dead "
                           "and left no result.json")
                touched.append(rd if rd else f"exp-{int(exp.value)}")
            # else: pid still alive -> keep waiting; a later scan ingests it.

    for exp_int, info in list(_INFLIGHT.items()):
        proc = info["proc"]
        if proc.poll() is None:
            continue                                    # still running — non-blocking, check next call
        exp, run_dir = info["node"], info["run_dir"]
        try:
            info["logf"].close()
        except Exception:
            pass
        if I.has_node(exp):
            _ingest_result(agent, exp, run_dir)
        del _INFLIGHT[exp_int]
        touched.append(str(run_dir))

    return touched


_RESTARTABLE = frozenset({"failed", "done", "supported", "refuted", "inconclusive"})


def restart_experiment(agent, id_str: str) -> dict:
    """Mechanical re-queue: reset a finished Experiment to ``status='requested'`` so
    ``scan_and_dispatch`` spawns a fresh child on the next call. Uses the next free
    ``<id>-N`` run_dir (see ``_run_dir_for``). Does not re-mint — the same Experiment
    node is re-run. Human/host-initiated retry only."""
    import substrate_rs as srs
    S, I = agent.s, agent.inner
    try:
        exp_int = int(id_str)
    except (ValueError, TypeError):
        return {"ok": False, "error": "bad id"}
    exp = srs.NodeID(exp_int)
    if not I.has_node(exp):
        return {"ok": False, "error": "not found"}
    if S.node(exp).get("type") != "Experiment":
        return {"ok": False, "error": "not an experiment"}
    if exp_int in _INFLIGHT:
        return {"ok": False, "error": "dispatch in flight"}
    status = str(S.node(exp)["attrs"].get("status") or "")
    if status == "running":
        return {"ok": False, "error": "still running"}
    if status == "requested":
        return {"ok": True, "id": exp_int, "status": "requested", "already_queued": True}
    if status not in _RESTARTABLE:
        return {"ok": False, "error": f"cannot restart from status {status!r}"}
    I.set_attr(exp, "status", "requested")
    # Reset the verdict/adoption bookkeeping a fresh run must re-earn. Note the
    # Wave 6 keys: `regressions` resets to 0 (an int — the veto rule compares
    # numerically; an empty string would compare ABOVE 0 in the DSL's
    # cross-type ordering and spuriously re-veto) and the veto's own
    # adopt_denied/adopt_denied_reason clear so a re-run is judged on its own
    # child's report, never a stale one.
    for key, blank in (("error", ""), ("outcome", ""), ("conclusion_ready", False),
                       ("taught", ""), ("adopt_ready", ""),
                       ("regressions", 0), ("adopt_denied", ""), ("adopt_denied_reason", ""),
                       ("avg_turn_ms", ""), ("performance_judged", ""),
                       ("avg_shadow_ms", ""), ("control_shadow_ms", ""),
                       ("control_reforms", ""), ("variant_reforms", ""),
                       ("knob_judged", ""),
                       ("control_belief", ""), ("variant_belief", ""),
                       ("datum_feedback_judged", ""), ("shape_mint_judged", "")):
        try:
            I.set_attr(exp, key, blank)
        except Exception:  # noqa: BLE001
            pass
    return {"ok": True, "id": exp_int, "status": "requested", "previous_status": status}


def cancel_experiment(agent, id_str: str) -> dict:
    """Mechanical cancel: terminate an inflight child (if any) and mark the
    Experiment ``status='cancelled'``. Human/host-initiated teardown only."""
    import substrate_rs as srs
    S, I = agent.s, agent.inner
    try:
        exp_int = int(id_str)
    except (ValueError, TypeError):
        return {"ok": False, "error": "bad id"}
    exp = srs.NodeID(exp_int)
    if not I.has_node(exp):
        return {"ok": False, "error": "not found"}
    if S.node(exp).get("type") != "Experiment":
        return {"ok": False, "error": "not an experiment"}
    prev = str(S.node(exp)["attrs"].get("status") or "")
    if prev == "cancelled":
        return {"ok": True, "id": exp_int, "status": "cancelled", "already_cancelled": True}
    info = _INFLIGHT.pop(exp_int, None)
    if info is not None:
        proc = info.get("proc")
        try:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except Exception:  # noqa: BLE001
                    proc.kill()
        except Exception:  # noqa: BLE001
            pass
        try:
            info.get("logf").close()
        except Exception:  # noqa: BLE001
            pass
    I.set_attr(exp, "status", "cancelled")
    return {"ok": True, "id": exp_int, "status": "cancelled", "previous_status": prev}
