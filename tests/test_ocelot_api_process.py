"""Process-level acceptance test for the documented API entry point."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
TOKEN = "process-test-secret"
PRINCIPAL = "process-test-user"


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _start_api(port: int, storage_dir: Path) -> subprocess.Popen:
    environment = os.environ.copy()
    environment.update({
        "OCELOT_API_TOKENS": json.dumps({TOKEN: PRINCIPAL}),
        "OCELOT_STATE_DIR": str(storage_dir),
        "OCELOT_API_HOST": "127.0.0.1",
        "OCELOT_API_PORT": str(port),
        "PYTHONPATH": os.pathsep.join((
            str(ROOT / "runners" / "dsl" / "python"), str(ROOT),
            environment.get("PYTHONPATH", ""))),
    })
    process = subprocess.Popen(
        [sys.executable, "-m", "scripts.ocelot_api"],
        cwd=ROOT, env=environment, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise AssertionError(f"Ocelot API exited during startup: {output}")
        try:
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/health", timeout=1) as response:
                if response.status == 200:
                    return process
        except (OSError, urllib.error.URLError):
            time.sleep(0.1)
    process.terminate()
    output, _ = process.communicate(timeout=5)
    raise AssertionError(f"Ocelot API did not become healthy: {output}")


def _stop_api(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    if process.stdout:
        process.stdout.close()


def _request(port: int, method: str, route: str, body: dict | None = None):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{route}", data=data,
        headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, json.loads(response.read())


def test_documented_api_process_serves_and_recovers_real_session(tmp_path):
    port = _free_port()
    process = _start_api(port, tmp_path)
    try:
        status, models = _request(port, "GET", "/v1/models")
        assert status == 200
        assert [row["id"] for row in models["data"]] == ["ocelot"]

        status, completion = _request(port, "POST", "/v1/chat/completions", {
            "model": "ocelot",
            "messages": [{"role": "user", "content": "Hello from process test."}],
        })
        assert status == 200
        assert completion["object"] == "chat.completion"
        assert completion["choices"][0]["message"]["content"]

        status, sessions = _request(port, "GET", "/v1/ocelot/sessions")
        assert status == 200
        session = sessions["data"][0]
        assert session["revision"] == 2
        session_id = session["id"]
    finally:
        _stop_api(process)

    restarted = _start_api(port, tmp_path)
    try:
        status, sessions = _request(port, "GET", "/v1/ocelot/sessions")
        assert status == 200
        recovered = sessions["data"][0]
        assert recovered["id"] == session_id
        assert recovered["revision"] == 2

        status, completion = _request(port, "POST", "/v1/chat/completions", {
            "model": "ocelot",
            "messages": [{"role": "user", "content": "Continue after restart."}],
        })
        assert status == 200
        status, sessions = _request(port, "GET", "/v1/ocelot/sessions")
        assert status == 200
        assert sessions["data"][0]["id"] == session_id
        assert sessions["data"][0]["revision"] == 3
    finally:
        _stop_api(restarted)
