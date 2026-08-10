"""Training dispatcher — the agent trains a reflex net as a BACKGROUND
process, end to end. The exact mirror of `domains/experiment_dispatch.py`:
scan for `TrainingJob{status:"requested"}` (the agent's own graph-native
decision), spawn a DETACHED child trainer (`scripts/train_child.py`) via
`Popen`, never block, poll with `proc.poll()`, and on exit INGEST the
trained weights back into the graph as a `NetForward`-readable net wrapped
by a (disabled) `ReflexNet`.

Mechanical host I/O only — no agent decisions. WHAT to train and WHETHER
to adopt are graph decisions (the `reflex_request_training` rule mints the
job; the `reflex_trial_judge` rule adopts). This module only: read the
job's traces, launch the process, poll it, and translate its weight
matrices into graph nodes.

Ticked from the daemon loop exactly like `_dispatch_tick` (add a
`_train_tick` at the same `--dispatch-every` cadence). Because it spawns
and polls (never waits), the agent keeps ticking while training runs in
the background — training is a background process, not an offline batch.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from domains.reflex_net import mint_reflex_net

_ROOT = Path(__file__).resolve().parent.parent
_TRAIN_CHILD = _ROOT / "scripts" / "train_child.py"
_PYTHONPATH_EXTRA = os.pathsep.join([str(_ROOT), str(_ROOT / "runners" / "dsl" / "python")])

# Host-only bookkeeping of live child processes (never graph truth) — same
# posture and same limitation as experiment_dispatch._INFLIGHT.
_INFLIGHT: dict = {}


def mint_training_job(agent, *, name, traces, fit_lo=-1.0, fit_hi=1.0,
                      hidden_dim=64, seed=0):
    """Mechanical helper: mint a TrainingJob{requested} with its training
    traces + numeric fit range attached. (In production the traces are the
    (input, verdict) pairs the adapter collected during cognition; the
    DECISION to train is the reflex_request_training rule — this is the I/O
    that attaches the data.)"""
    s = agent.s if hasattr(agent, "s") else agent
    job = s.add_node("TrainingJob", {
        "status": "requested", "name": str(name),
        "traces": [[list(x) if isinstance(x, (list, tuple)) else [x], t] for x, t in traces],
        "fit_lo": float(fit_lo), "fit_hi": float(fit_hi),
        "hidden_dim": int(hidden_dim), "seed": int(seed), "run_dir": "",
    })
    return job


def attach_traces(agent, job, traces, *, fit_lo=-1.0, fit_hi=1.0,
                  hidden_dim=64, seed=0):
    """Mechanical I/O: attach the collected (input, verdict) traces + numeric
    fit range to a trace_pending TrainingJob and flip it to `requested` so
    the dispatcher trains it. In production the traces are the (input,
    verdict) pairs the adapter recorded while active cognition ran the slow
    path — collecting them is host I/O, not a decision."""
    s = agent.s if hasattr(agent, "s") else agent
    I = agent.inner if hasattr(agent, "inner") else agent
    I.set_attr(job, "traces",
               [[list(x) if isinstance(x, (list, tuple)) else [x], t] for x, t in traces])
    I.set_attr(job, "fit_lo", float(fit_lo))
    I.set_attr(job, "fit_hi", float(fit_hi))
    I.set_attr(job, "hidden_dim", int(hidden_dim))
    I.set_attr(job, "seed", int(seed))
    I.set_attr(job, "status", "requested")
    return job


def _run_dir_for(runs_dir, job_int) -> Path:
    return Path(runs_dir) / f"train_{job_int}"


def _spawn_trainer(agent, runs_dir, job) -> None:
    """Write the training config off the job node + launch the child,
    detached. Every value is read straight off the TrainingJob node."""
    S, I = agent.s, agent.inner
    a = S.node(job)["attrs"]
    job_int = int(job.value)
    run_dir = _run_dir_for(runs_dir, job_int)
    run_dir.mkdir(parents=True, exist_ok=True)

    cfg = {
        "traces": a.get("traces") or [],
        "hidden_dim": int(a.get("hidden_dim") or 64),
        "seed": int(a.get("seed") or 0),
    }
    cfg_path = run_dir / "train_config.json"
    cfg_path.write_text(json.dumps(cfg))

    log_path = run_dir / "log.txt"
    cmd = [sys.executable, str(_TRAIN_CHILD),
           "--config", str(cfg_path), "--out", str(run_dir)]
    child_env = dict(os.environ)
    child_env["PYTHONPATH"] = _PYTHONPATH_EXTRA + os.pathsep + child_env.get("PYTHONPATH", "")
    logf = open(log_path, "w")
    proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT,
                            cwd=str(_ROOT), env=child_env)

    I.set_attr(job, "status", "running")
    I.set_attr(job, "run_dir", str(run_dir))
    _INFLIGHT[job_int] = {"proc": proc, "run_dir": run_dir, "node": job, "logf": logf}


def _weights_to_assemblage(agent, steps, input_dim, output_dim):
    """Mechanical translator: trained weight matrices -> a
    NetworkAssemblage -has_step-> AssemblageStep -has_weight->
    WeightTensor{role,data} subgraph, the exact layout NetForward reads.
    Pure host I/O (tensor -> graph attrs), same spirit as the cortex's
    'write, not train' construct_weights, but from arbitrary fitted arrays."""
    s = agent.s if hasattr(agent, "s") else agent
    asm = s.add_node("NetworkAssemblage", {
        "input_dim": int(input_dim), "output_dim": int(output_dim),
        "origin": "trained"})
    for step in steps:
        sid = s.add_node("AssemblageStep", {
            "order": int(step.get("order", 0)), "dim_behavior": "transform"})
        s.add_edge(asm, "has_step", sid, {})
        for role in ("W1", "b1", "W2", "b2"):
            wt = s.add_node("WeightTensor", {
                "role": role, "data": step[role], "constructed_by": "trained"})
            s.add_edge(sid, "has_weight", wt, {})
    return asm


def _ingest_trained(agent, job, run_dir) -> None:
    """Read the child's result.json/weights.json and fold the trained net
    into the graph: build the assemblage, mint a DISABLED ReflexNet wrapping
    it (with the job's numeric fit range for grounding), link the job to it,
    and set the job's status from the child's verdict. On failure, the job
    is marked failed (the contract holds unconditionally)."""
    S, I = agent.s, agent.inner
    a = S.node(job)["attrs"]
    result_path = Path(run_dir) / "result.json"
    try:
        result = json.loads(result_path.read_text())
    except Exception as e:  # noqa: BLE001
        result = {"status": "failed", "error": f"no result.json: {e}"}

    status = result.get("status", "failed")
    if status == "done":
        try:
            w = json.loads((Path(run_dir) / "weights.json").read_text())
            asm = _weights_to_assemblage(agent, w["steps"],
                                         w.get("input_dim", 1), w.get("output_dim", 1))
            rn = mint_reflex_net(S, asm,
                                 name=f"trained_{a.get('name') or int(job.value)}",
                                 basin_threshold=float(a.get("fit_hi", 1.0)) -
                                 float(a.get("fit_lo", -1.0)))
            # numeric basin from the training range (for reflex_ground_numeric_residual)
            I.set_attr(rn, "fit_lo", float(a.get("fit_lo", -1.0)))
            I.set_attr(rn, "fit_hi", float(a.get("fit_hi", 1.0)))
            S.add_edge(job, "trained_net", rn, {})
            I.set_attr(job, "train_mse", float(result.get("train_mse", 0.0)))
        except Exception as e:  # noqa: BLE001
            status = "failed"
            I.set_attr(job, "ingest_error", f"{type(e).__name__}: {e}")
    I.set_attr(job, "status", str(status))


def scan_and_train(agent, runs_dir) -> list:
    """NON-BLOCKING: spawn every requested TrainingJob as a detached child,
    and ingest results from any child that has exited. Mirrors
    experiment_dispatch.scan_and_dispatch exactly. Returns run_dirs touched."""
    S, I = agent.s, agent.inner
    Path(runs_dir).mkdir(parents=True, exist_ok=True)
    touched: list = []

    for job in list(S.nodes("TrainingJob")):
        if not I.has_node(job):
            continue
        if int(job.value) in _INFLIGHT:
            continue
        if S.node(job)["attrs"].get("status") == "requested":
            _spawn_trainer(agent, runs_dir, job)
            touched.append(str(_INFLIGHT[int(job.value)]["run_dir"]))

    for job_int, info in list(_INFLIGHT.items()):
        proc = info["proc"]
        if proc.poll() is None:
            continue
        job, run_dir = info["node"], info["run_dir"]
        try:
            info["logf"].close()
        except Exception:
            pass
        if I.has_node(job):
            _ingest_trained(agent, job, run_dir)
        del _INFLIGHT[job_int]
        touched.append(str(run_dir))

    return touched
