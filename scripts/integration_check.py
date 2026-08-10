#!/usr/bin/env python3
"""integration_check — full-stack bring-up check for jabberwock_daemon.py
(host I/O only, CLAUDE.md: this script drives processes and reads/writes
files; it makes no agent decisions).

Exercises the deliverable end-to-end against a SCRATCH checkpoint dir (never
touches ~/.jabberwock):

  (a) launch --seeds full, GET /api/status ok, booted_from == "seeds"
  (b) POST /api/chat round-trips with a non-empty reply
  (c) mint a real Experiment{requested} via the CHECKPOINT-EDIT flow (stop
      the daemon -> load its checkpoint -> mint_experiment -> checkpoint() ->
      restart) since persistence IS the sanctioned IPC (see module docstring
      below and CLAUDE.md) -- confirm the dispatch hook picks it up, the
      offline "navigate" child runs, and GET /api/sessions then
      /api/sessions/<id> show the finished run with a trace whose shape
      matches what web/app.js expects (frame/action/score/reasoning/
      self_report per row; id/game/status/hypothesis/frames/score/run_dir
      per session)
  (d) SIGTERM -> restart -> resumes from checkpoint (booted_from ==
      "checkpoint"), sessions still listed, chat still works
  (e) mint a FetchRequest via the same checkpoint-edit flow against a LOCAL
      http.server this script itself runs -> restart -> fetch hook
      completes it

Why checkpoint-edit and not a live admin route: the daemon's HTTP API is a
FIXED CONTRACT (see jabberwock_daemon.py's module docstring) a companion web
UI is built against -- adding an ad hoc admin-mint route to poke internal
graph state widens that contract for a one-off test need. The daemon already
exposes exactly one sanctioned way to hand it new graph state out-of-band:
stop it, `WorldAdapter.load()` its own checkpoint (the same function `boot()`
uses), mutate via the SAME mint_* helpers the real seeded rules will one day
call themselves (`mint_experiment` / `mint_fetch_request` -- authoring
helpers, not host decisions, see their docstrings), `checkpoint()` it back
(the same rotated/atomic save the daemon's own interval-checkpoint uses), and
restart. This IS how a human operator or an offline authoring tool is meant
to hand the running agent new state today; scripting it here is exactly
"persistence as the IPC", not a workaround.

Idempotent / rerunnable: every scratch path is wiped at the start of each
run. Exits 0 if every step PASSes, 1 otherwise (prints a PASS/FAIL line per
step either way, plus a summary).

Usage:
    PYTHONPATH=runners/dsl/python:. python3 scripts/integration_check.py
"""
from __future__ import annotations

import http.server
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

SCRATCH = Path(os.environ.get("JBW_INTEGRATION_SCRATCH", "/tmp/jbw_integration_check"))
CKPT_DIR = SCRATCH / "ckpt"
RUNS_DIR = SCRATCH / "runs"
SOCK_PATH = SCRATCH / "jbw.sock"
HTTP_PORT = int(os.environ.get("JBW_INTEGRATION_PORT", "8797"))
BASE = f"http://127.0.0.1:{HTTP_PORT}"
PY = sys.executable
DAEMON = str(ROOT / "scripts" / "jabberwock_daemon.py")
ENV = dict(os.environ)
ENV["PYTHONPATH"] = os.pathsep.join([str(ROOT), str(ROOT / "runners" / "dsl" / "python")])

RESULTS: list[tuple[str, bool, str]] = []


def report(name: str, ok: bool, detail: str = "") -> None:
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name}" + (f" -- {detail}" if detail else ""))
    RESULTS.append((name, ok, detail))


def http_get(path: str, timeout: float = 10.0) -> dict:
    with urllib.request.urlopen(f"{BASE}{path}", timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def http_get_status(path: str, timeout: float = 10.0) -> int:
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def http_post_json(path: str, obj: dict, timeout: float = 20.0) -> dict:
    body = json.dumps(obj).encode("utf-8")
    req = urllib.request.Request(f"{BASE}{path}", data=body,
                                  headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def wait_for_http(timeout: float = 30.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            d = http_get("/api/status", timeout=2.0)
            if d.get("ok"):
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


def start_daemon(extra_args: list[str]) -> subprocess.Popen:
    args = [PY, DAEMON,
            "--seeds", "full",
            "--ckpt-dir", str(CKPT_DIR),
            "--runs-dir", str(RUNS_DIR),
            "--socket", str(SOCK_PATH),
            "--http-port", str(HTTP_PORT),
            "--interval", "3600",       # don't let the periodic timer race our checkpoint-edit flow
            "--dispatch-every", "3",
            "--fetch-every", "3",
            "--tick-hz", "20",
            ] + extra_args
    proc = subprocess.Popen(args, cwd=str(ROOT), env=ENV,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, bufsize=1)
    return proc


def stop_daemon(proc: subprocess.Popen, timeout: float = 20.0) -> str:
    """SIGTERM -> wait for the final checkpoint + clean exit; returns
    captured stdout/stderr (for diagnostics on a failed stop)."""
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    out = proc.stdout.read() if proc.stdout else ""
    return out


def _drain_output(proc: subprocess.Popen, buf: list[str]) -> None:
    if proc.stdout is None:
        return
    for line in proc.stdout:
        buf.append(line)


def checkpoint_edit(mutate) -> None:
    """The sanctioned out-of-band mutation path (see module docstring):
    load the daemon's OWN newest checkpoint with its OWN boot()/checkpoint()
    functions, run `mutate(adapter)`, save. Caller is responsible for the
    daemon being stopped before, and restarted after, calling this."""
    from scripts.jabberwock_daemon import boot as daemon_boot, checkpoint as daemon_checkpoint
    adapter, booted_from = daemon_boot(CKPT_DIR, "full")
    assert booted_from == "checkpoint", f"checkpoint_edit expected an existing checkpoint, got booted_from={booted_from!r}"
    mutate(adapter)
    daemon_checkpoint(adapter, CKPT_DIR, keep=10)


def checkpoint_read(inspect):
    """Read-only twin of checkpoint_edit: load the newest checkpoint, run
    `inspect(adapter)` for its return value, do NOT write anything back.
    Caller is responsible for the daemon being stopped before calling this
    (same discipline as checkpoint_edit -- concurrent readers/writers of the
    same checkpoint file are not part of this contract)."""
    from scripts.jabberwock_daemon import boot as daemon_boot
    adapter, booted_from = daemon_boot(CKPT_DIR, "full")
    assert booted_from == "checkpoint", f"checkpoint_read expected an existing checkpoint, got booted_from={booted_from!r}"
    return inspect(adapter)


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *a):  # quiet
        pass


def start_local_http_server(tmp_dir: Path) -> tuple[http.server.HTTPServer, threading.Thread, str]:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    (tmp_dir / "index.html").write_text(
        "<html><head><title>Integration Check</title></head><body>"
        "<p>Hello from the integration_check local fetch target.</p>"
        "<p>Second paragraph so the extractor has more than one node.</p>"
        "</body></html>"
    )

    def handler_factory(*a, **kw):
        return _QuietHandler(*a, directory=str(tmp_dir), **kw)

    srv = http.server.HTTPServer(("127.0.0.1", 0), handler_factory)
    port = srv.server_port
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, t, f"http://127.0.0.1:{port}/index.html"


def main() -> int:
    print(f"=== integration_check: scratch={SCRATCH} http_port={HTTP_PORT} ===")
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH)
    SCRATCH.mkdir(parents=True)
    CKPT_DIR.mkdir(parents=True)
    RUNS_DIR.mkdir(parents=True)

    local_srv, local_thread, local_url = start_local_http_server(SCRATCH / "fetch_site")

    daemon_out: list[str] = []
    proc = start_daemon([])
    drain_t = threading.Thread(target=_drain_output, args=(proc, daemon_out), daemon=True)
    drain_t.start()

    try:
        # --- (a) boot + status ------------------------------------------------
        up = wait_for_http(timeout=30.0)
        report("(a) daemon boots + HTTP comes up", up)
        if not up:
            report("(a) daemon log tail", False, "".join(daemon_out[-40:]))
            return _finish()

        status = http_get("/api/status")
        ok_a = bool(status.get("ok")) and status.get("booted_from") == "seeds" and status.get("node_count", 0) > 0
        report("(a) /api/status ok, booted_from == 'seeds', node_count > 0", ok_a, str(status))

        # --- (b) chat round-trip -----------------------------------------------
        try:
            chat = http_post_json("/api/chat", {"text": "hello, are you there?"})
            ok_b = bool(chat.get("ok")) and isinstance(chat.get("reply"), str) and len(chat["reply"]) > 0
        except Exception as e:  # noqa: BLE001
            chat = {"error": str(e)}
            ok_b = False
        report("(b) POST /api/chat round-trips with a non-empty reply", ok_b, str(chat)[:200])

        # --- (c) mint a real Experiment, confirm dispatch picks it up ----------
        exp_id_holder: dict = {}

        def _mint_exp(adapter):
            from domains.experiment_dispatch import mint_experiment
            exp = mint_experiment(adapter, "integration_check: does a trivial navigate run cleanly?",
                                   "navigate", skip_seeds=[], add_rules=[])
            exp_id_holder["id"] = exp.value if hasattr(exp, "value") else int(exp)

        out = stop_daemon(proc)
        daemon_out.append(out)
        try:
            checkpoint_edit(_mint_exp)
            ok_mint = True
        except Exception as e:  # noqa: BLE001
            ok_mint = False
            report("(c) checkpoint-edit: mint Experiment", False, f"{type(e).__name__}: {e}")
        if ok_mint:
            report("(c) checkpoint-edit: mint Experiment", True, f"exp id={exp_id_holder.get('id')}")

        proc = start_daemon([])
        drain_t = threading.Thread(target=_drain_output, args=(proc, daemon_out), daemon=True)
        drain_t.start()
        up2 = wait_for_http(timeout=30.0)
        report("(c) daemon restarts after checkpoint-edit", up2)

        exp_done = False
        session_json = None
        detail_json = None
        if up2 and ok_mint:
            t0 = time.time()
            while time.time() - t0 < 120.0:
                try:
                    sessions = http_get("/api/sessions").get("sessions", [])
                except Exception:
                    sessions = []
                match = next((s for s in sessions if s.get("id") == exp_id_holder.get("id")), None)
                if match is not None and match.get("status") not in ("requested", "running", None):
                    session_json = match
                    exp_done = match.get("status") == "done"
                    break
                time.sleep(1.0)
        report("(c) dispatch hook picks up the Experiment; offline 'navigate' child completes",
               exp_done, str(session_json))

        if exp_done:
            detail_json = http_get(f"/api/sessions/{exp_id_holder['id']}")
            sess = detail_json.get("session", {})
            trace = detail_json.get("trace", [])
            shape_ok = (
                detail_json.get("ok") is True
                and all(k in sess for k in ("id", "game", "status", "hypothesis", "frames", "score", "run_dir"))
                and len(trace) > 0
                and all(set(t.keys()) == {"frame", "action", "score", "reasoning", "self_report"} for t in trace)
            )
            report("(c) /api/sessions/<id> shape matches web/app.js's contract", shape_ok,
                   f"session_keys={sorted(sess.keys())} trace_len={len(trace)}")
        else:
            report("(c) /api/sessions/<id> shape matches web/app.js's contract", False, "experiment never finished")

        # --- (d) SIGTERM -> restart -> resumes from checkpoint ------------------
        node_count_before = http_get("/api/status").get("node_count")
        out = stop_daemon(proc)
        daemon_out.append(out)

        proc = start_daemon([])
        drain_t = threading.Thread(target=_drain_output, args=(proc, daemon_out), daemon=True)
        drain_t.start()
        up3 = wait_for_http(timeout=30.0)
        status3 = http_get("/api/status") if up3 else {}
        ok_resume = up3 and status3.get("booted_from") == "checkpoint" and status3.get("node_count", 0) >= (node_count_before or 0)
        report("(d) SIGTERM -> restart resumes from checkpoint", ok_resume,
               f"booted_from={status3.get('booted_from')} node_count={status3.get('node_count')} (was {node_count_before})")

        sessions_after_restart = http_get("/api/sessions").get("sessions", []) if up3 else []
        still_listed = any(s.get("id") == exp_id_holder.get("id") for s in sessions_after_restart) if exp_done else False
        report("(d) sessions still listed after restart", still_listed if exp_done else up3,
               f"{len(sessions_after_restart)} sessions")

        try:
            chat2 = http_post_json("/api/chat", {"text": "still there after restart?"})
            ok_chat2 = bool(chat2.get("ok")) and len(chat2.get("reply", "")) > 0
        except Exception as e:  # noqa: BLE001
            chat2 = {"error": str(e)}
            ok_chat2 = False
        detail2 = str(chat2)[:200]
        if not ok_chat2 and isinstance(chat2, dict) and chat2.get("ok") and not chat2.get("reply"):
            # KNOWN BUG (found by this check, 2026-07-02): WorldAdapter.save()
            # persists the graph + Γ grammar + adapter indexes but NOT the Rust
            # rule engine's installed Rules -- after WorldAdapter.load() the
            # engine's rule_count() drops (measured: 350 -> 0 on a full-seed
            # boot), so comprehend() fires nothing and converse() returns None
            # on a RESUMED agent while working fine on a fresh seed boot. The
            # fix belongs in substrate/world_adapter.py save/load (needs a
            # rules serialisation on the Rust Substrate), not in the daemon.
            detail2 += " [known bug: checkpoint load drops installed rules, rule_count 350->0]"
        report("(d) chat still works after restart", ok_chat2, detail2)

        # --- (e) mint a FetchRequest against the local test server --------------
        def _mint_fetch(adapter):
            from domains.fetch_dispatch import mint_fetch_request
            req = mint_fetch_request(adapter, local_url, purpose="integration_check")
            exp_id_holder["fetch_id"] = req.value if hasattr(req, "value") else int(req)

        out = stop_daemon(proc)
        daemon_out.append(out)
        try:
            checkpoint_edit(_mint_fetch)
            ok_mint_fetch = True
        except Exception as e:  # noqa: BLE001
            ok_mint_fetch = False
            report("(e) checkpoint-edit: mint FetchRequest", False, f"{type(e).__name__}: {e}")
        if ok_mint_fetch:
            report("(e) checkpoint-edit: mint FetchRequest", True, f"req id={exp_id_holder.get('fetch_id')} url={local_url}")

        proc = start_daemon([])
        drain_t = threading.Thread(target=_drain_output, args=(proc, daemon_out), daemon=True)
        drain_t.start()
        up4 = wait_for_http(timeout=30.0)
        report("(e) daemon restarts after fetch checkpoint-edit", up4)

        fetch_result = {}
        if up4 and ok_mint_fetch:
            # Give the tick loop several cycles to hit the fetch-dispatch
            # hook (--fetch-every 3, tick-hz 20, chat above already primed
            # `dirty`) before stopping to inspect -- fetches are synchronous
            # (domains/fetch_dispatch.py: "seconds, no subprocess"), so a
            # short fixed wait is enough rather than a real poll loop (there
            # is no /api/fetch route -- reading mid-flight state needs the
            # same stop-then-checkpoint_read discipline as the mutate path).
            time.sleep(5.0)

        out = stop_daemon(proc)
        daemon_out.append(out)

        fetch_done = False
        if ok_mint_fetch:
            def _read_fetch(adapter):
                fid = exp_id_holder.get("fetch_id")
                if fid is None:
                    return None
                import substrate_rs as _srs
                nid = _srs.NodeID(fid)
                if not adapter.s.has_node(nid):
                    return None
                a = adapter.s.node(nid)["attrs"]
                return {"status": a.get("status"), "error": a.get("error")}

            try:
                fetch_result = checkpoint_read(_read_fetch) or {}
            except Exception as e:  # noqa: BLE001
                fetch_result = {"error": f"{type(e).__name__}: {e}"}
            fetch_done = fetch_result.get("status") == "done"
        report("(e) fetch hook completes the FetchRequest", fetch_done, str(fetch_result))

    finally:
        if proc.poll() is None:
            stop_daemon(proc)
        try:
            local_srv.shutdown()
            local_srv.server_close()
        except Exception:  # noqa: BLE001
            pass

    return _finish()


def _finish() -> int:
    print("\n=== summary ===")
    n_pass = sum(1 for _, ok, _ in RESULTS if ok)
    n_fail = sum(1 for _, ok, _ in RESULTS if not ok)
    for name, ok, detail in RESULTS:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"{n_pass} passed, {n_fail} failed")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
