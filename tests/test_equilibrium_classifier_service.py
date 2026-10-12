"""Equilibrium classifier sidecar v0 (track T3): HTTP contract + Phase 9 exit test.

Synthetic data only (pseudonyms member_###); no corpus, no LLM (OZMA_NO_LLM=1).
Servers run as subprocesses on 127.0.0.1 with cwd/TMPDIR = a pytest tmp dir.
Measurements are printed (run with -s to see them).
"""
from __future__ import annotations

import http.client
import json
import os
import random
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "services" / "equilibrium_classifier" / "server.py"

# The Equilibrium worker client's reply checks (equilibrium_worker/classify.py).
_CODE = re.compile(r"^[a-z0-9][a-z0-9_.:/-]{0,127}$")
_VERSIONISH = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.+_:-]{0,127}$")
_SCORE_KEYS = ("valence", "hostility", "person_targeting", "deescalation", "confidence")
SECRET = "zz_canary_input_9f3a"  # must never be echoed back in any error


# ---------------------------------------------------------------- helpers ---
def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _env(tmp: Path, **over) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in ("OZMA_NO_LLM",)}
    env.update(OZMA_NO_LLM="1", PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(tmp))
    for k, v in over.items():
        if v is None:
            env.pop(k, None)
        else:
            env[k] = v
    return env


def _req(port, method, path, body=None, headers=None, raw=None, timeout=60):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        data = raw if raw is not None else (None if body is None else json.dumps(body).encode())
        h = {"Content-Type": "application/json", **(headers or {})}
        c.request(method, path, body=data, headers=h)
        r = c.getresponse()
        txt = r.read()
        return r.status, (json.loads(txt) if txt else None), txt
    finally:
        c.close()


def _wait_up(proc, port, deadline_s=120):
    t0 = time.time()
    while time.time() - t0 < deadline_s:
        if proc.poll() is not None:
            raise AssertionError(f"server exited early rc={proc.returncode}")
        try:
            st, doc, _ = _req(port, "GET", "/healthz", timeout=2)
            if st == 200:
                return time.time() - t0
        except OSError:
            pass
        time.sleep(0.1)
    raise AssertionError("server did not come up")


def _start(tmp: Path, port: int, prefix: list[str] | None = None, **env_over):
    log = open(tmp / f"server_{port}.stderr", "wb")
    # Own process group: when the server runs under `strace -f`, signalling only strace detaches it and leaves the
    # server orphaned (observed: dozens of leaked sidecars after repeated 10k-turn runs). _stop signals the group.
    proc = subprocess.Popen((prefix or []) + [sys.executable, str(SERVER), "--port", str(port)],
                            cwd=tmp, env=_env(tmp, **env_over), stdout=log, stderr=log, start_new_session=True)
    boot_s = _wait_up(proc, port)
    return proc, boot_s


def _signal_group(proc, sig) -> None:
    try:
        os.killpg(proc.pid, sig)
    except ProcessLookupError:
        pass


def _stop(proc):
    """Stop the server and everything in its process group (strace and the server it traces)."""
    _signal_group(proc, signal.SIGINT)
    try:
        proc.wait(15)
    except subprocess.TimeoutExpired:
        pass
    _signal_group(proc, signal.SIGTERM)
    time.sleep(0.2)
    _signal_group(proc, signal.SIGKILL)
    if proc.poll() is None:
        proc.wait(5)


def _client_parse(item: dict) -> None:
    """Mirror of equilibrium_worker.classify._parse_labels acceptance."""
    assert isinstance(item.get("id"), str)
    act = item.get("speech_act")
    assert act is None or (isinstance(act, str) and _CODE.fullmatch(act))
    for k in _SCORE_KEYS:
        v = item.get(k)
        if v is not None:
            assert not isinstance(v, bool) and isinstance(v, (int, float)) and -1.0 <= v <= 1.0
    for k in ("domains", "substantive_markers", "rule_ids"):
        v = item.get(k, [])
        assert isinstance(v, list) and len(v) <= 64
        assert all(isinstance(x, str) and _CODE.fullmatch(x) for x in v), (k, v)


_THINGS = ["build", "config", "parser", "cache", "test suite", "release", "docs page", "index"]
_VERBS = ["fix", "reset", "configure", "update", "debug", "rebuild"]
_FILL = ["really", "again", "today", "here", "for now", "on main", "after the merge", "locally"]


def synthetic_messages(n: int, seed: int = 9) -> list[dict]:
    """Deterministic synthetic chat lines (no corpus). Varied lengths/shapes."""
    rnd = random.Random(seed)
    T = [
        lambda: f"how do I {rnd.choice(_VERBS)} the {rnd.choice(_THINGS)}?",
        lambda: f"sorry, my bad, the {rnd.choice(_THINGS)} was wrong",
        lambda: f"according to the docs, `make {rnd.choice(_VERBS)}` works",
        lambda: f"see https://example.org/page/{rnd.randint(1, 999)} for the {rnd.choice(_THINGS)}",
        lambda: f"```\nmake {rnd.choice(_VERBS)}\n```\nthat should do it",
        lambda: f"fair point member_{rnd.randint(1, 999):03d}, I understand",
        lambda: f"the {rnd.choice(_THINGS)} is broken {rnd.choice(_FILL)}",
        lambda: f"Run the tests before you push the {rnd.choice(_THINGS)}",
        lambda: "ok",
        lambda: f"compare the {rnd.choice(_THINGS)} with the old one",
    ]
    out = []
    for i in range(n):
        text = rnd.choice(T)()
        for _ in range(rnd.choice([0, 0, 1, 3, 8])):
            text += " " + rnd.choice(_FILL)
        out.append({"id": f"s{i:06d}", "text": text, "reply_to": f"s{i - 1:06d}" if i and i % 4 == 0 else None})
    return out


def _tree_state(root: Path) -> dict:
    skip = {".git", "__pycache__", ".pytest_cache", "target", "node_modules"}
    st = {}
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in skip and not (Path(dp) == root and d in (".worktrees", "data"))]
        for f in fns:
            p = Path(dp) / f
            try:
                s = p.lstat()
            except OSError:
                continue
            st[str(p.relative_to(root))] = (s.st_size, s.st_mtime_ns)
    return st


def _replay(port: int, msgs: list[dict], batch: int = 100) -> list[float]:
    lat = []
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=120)
    try:
        for i in range(0, len(msgs), batch):
            body = json.dumps({"messages": msgs[i:i + batch]}).encode()
            t = time.perf_counter()
            c.request("POST", "/v1/classify", body=body, headers={"Content-Type": "application/json"})
            r = c.getresponse()
            doc = json.loads(r.read())
            lat.append(time.perf_counter() - t)
            assert r.status == 200, doc
            assert [x["id"] for x in doc["labels"]] == [m["id"] for m in msgs[i:i + batch]]
    finally:
        c.close()
    return lat


# --------------------------------------------------------- refusal tests ---
@pytest.mark.parametrize("val", [None, "0", "", "true"])
def test_refuses_without_ozma_no_llm(tmp_path, val):
    r = subprocess.run([sys.executable, str(SERVER), "--port", str(_free_port())], cwd=tmp_path,
                       env=_env(tmp_path, OZMA_NO_LLM=val), capture_output=True, text=True, timeout=60)
    assert r.returncode == 2 and "OZMA_NO_LLM" in r.stderr


@pytest.mark.parametrize("host", ["0.0.0.0", "localhost", "::1", "::", "192.168.1.10", "127.0.0.2"])
def test_refuses_non_loopback_host(tmp_path, host):
    r = subprocess.run([sys.executable, str(SERVER), "--host", host, "--port", str(_free_port())],
                       cwd=tmp_path, env=_env(tmp_path), capture_output=True, text=True, timeout=60)
    assert r.returncode == 2 and "bind host must be 127.0.0.1" in r.stderr


# --------------------------------------------------------- contract tests ---
@pytest.fixture(scope="module")
def server(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("eqsc")
    port = _free_port()
    proc, _ = _start(tmp, port)
    yield port
    _stop(proc)


def test_healthz(server):
    st, doc, _ = _req(server, "GET", "/healthz")
    assert st == 200 and doc == {"ok": True}


def test_info_contract(server):
    from services.equilibrium_classifier import server as srv
    st, doc, _ = _req(server, "GET", "/v1/info")
    assert st == 200 and doc["ok"] is True
    assert doc["mode"] == "fork_per_batch" and doc["no_llm"] is True
    assert doc["taxonomy_version"] == "eq-tax-0.7.0" and doc["seed_pack_version"] == "0.7.0"
    assert doc["seed_pack_sha256"] == doc["seed_pack_digest"] == srv.seed_pack_sha256()
    assert doc["seed_pack_files"] == [p.name for p in sorted((ROOT / "seeds").glob("equilibrium_*.json"))]
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                          text=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS="0")).stdout.strip()
    assert doc["ocelot_commit"] == head
    for k in ("ocelot_commit", "seed_pack_digest", "taxonomy_version"):  # client describe()
        assert _VERSIONISH.fullmatch(doc[k])
    assert doc["labels"]["msg.speech_act"] == "shadow"
    for lab in ("deescalation", "concession", "status_claim", "hostility", "domain"):
        assert doc["labels"][f"msg.{lab}"] == "shadow", lab
    pats = [k for k in doc["labels"] if k.startswith("pattern.")]
    assert pats and all(doc["labels"][k] == "disabled" for k in pats)
    assert not any(k.startswith("pat.") for k in doc["labels"])
    assert doc["limits"]["max_messages"] == 100
    assert doc["endpoints"] == {"/v1/classify": "ok", "/v1/discourse": "ok",
                                "/v1/conversations/{id}/turns": "ok", "/v1/conversations/{id}/close": "ok",
                                "GET /v1/conversations/{id}": "ok",
                                "/v1/conversations/_batch": "ok"}


def test_classify_contract(server):
    msgs = [{"id": "m1", "text": "how do I reset the cache?", "reply_to": None},
            {"id": "m2", "text": "sorry, my bad. see https://example.org and run `make`", "reply_to": "m1"},
            {"id": "m3", "text": "", "reply_to": None}]
    st, doc, _ = _req(server, "POST", "/v1/classify", {"messages": msgs})
    assert st == 200 and doc["ok"] is True
    assert doc["provenance"]["mode"] == "fork_per_batch"
    labels = doc["labels"]
    assert [x["id"] for x in labels] == ["m1", "m2", "m3"]
    for item in labels:
        _client_parse(item)
    assert labels[0]["speech_act"] == "question" and "question" in labels[0]["substantive_markers"]
    assert labels[0]["deescalation"] == 0.0
    assert labels[1]["deescalation"] == 1.0
    assert {"code", "link"} <= set(labels[1]["substantive_markers"])
    assert "eq.msg.speech_act.sak_question:0.7.0" in labels[0]["rule_ids"]
    # taxonomy_version optional; when present it must match
    st, _, _ = _req(server, "POST", "/v1/classify", {"taxonomy_version": "eq-tax-0.7.0", "messages": msgs[:1]})
    assert st == 200


_CUE_FIELDS = ("deescalation", "concession", "status_claim", "hostility")


def test_classify_v2_cue_fields(server):
    """0.2.0: concession / status_claim / hostility are 0.0/1.0 floats like
    deescalation; domains carries "technical" when the technical cue fires.
    Cues inside code spans do not count."""
    msgs = [{"id": "v1", "text": "Good catch, I stand corrected."},
            {"id": "v2", "text": "In my 20 years as the architect, trust me."},
            {"id": "v3", "text": "This is ridiculous, you don't understand."},
            {"id": "v4", "text": "The p99 latency spikes when the connection pool drains."},
            {"id": "v5", "text": "Let's step back and hear from member_042."},
            {"id": "v6", "text": "Run `ridiculous --trust-me --cache` on the box."},
            {"id": "v7", "text": "the build is green"}]
    st, doc, _ = _req(server, "POST", "/v1/classify", {"messages": msgs})
    assert st == 200
    lab = {x["id"]: x for x in doc["labels"]}
    for item in doc["labels"]:
        _client_parse(item)
        for f in _CUE_FIELDS:
            assert type(item[f]) is float and item[f] in (0.0, 1.0), (item["id"], f)
        assert isinstance(item["domains"], list)
    fired = {i: {f for f in _CUE_FIELDS if lab[i][f] == 1.0} for i in lab}
    assert fired == {"v1": {"concession"}, "v2": {"status_claim"}, "v3": {"hostility"},
                     "v4": set(), "v5": {"deescalation"}, "v6": set(), "v7": set()}
    assert {i: lab[i]["domains"] for i in lab} == {
        "v1": [], "v2": [], "v3": [], "v4": ["technical"], "v5": [], "v6": [], "v7": []}
    assert "eq.msg.status_claim.cue_4gram:0.7.0" in lab["v2"]["rule_ids"]
    assert "eq.msg.domain.technical_cue_bigram:0.7.0" in lab["v4"]["rule_ids"]
    assert all(r.endswith(":0.7.0") for x in doc["labels"] for r in x["rule_ids"])


def test_classify_deterministic_across_requests(server):
    msgs = synthetic_messages(100, seed=3)
    a = _req(server, "POST", "/v1/classify", {"messages": msgs})[1]["labels"]
    b = _req(server, "POST", "/v1/classify", {"messages": msgs})[1]["labels"]
    assert a == b


@pytest.mark.parametrize("case", [
    "bad_json", "not_object", "unknown_top", "unknown_msg_key", "missing_messages", "empty", "too_many",
    "id_type", "id_long", "dup_id", "text_type", "text_long", "reply_to_type", "taxonomy_mismatch",
    "nan", "dup_key",
])
def test_classify_errors_closed_and_no_echo(server, case):
    ok = {"id": "e1", "text": SECRET}
    bodies = {
        "bad_json": (b"{" + SECRET.encode(), 400, "bad_json"),
        "not_object": ([SECRET], 400, "schema_violation"),
        "unknown_top": ({"messages": [ok], SECRET: 1}, 400, "schema_violation"),
        "unknown_msg_key": ({"messages": [{**ok, SECRET: 1}]}, 400, "schema_violation"),
        "missing_messages": ({"taxonomy_version": "eq-tax-0.7.0"}, 400, "schema_violation"),
        "empty": ({"messages": []}, 400, "schema_violation"),
        "too_many": ({"messages": [{"id": f"x{i}", "text": SECRET} for i in range(101)]}, 413, "too_large"),
        "id_type": ({"messages": [{"id": 5, "text": SECRET}]}, 400, "schema_violation"),
        "id_long": ({"messages": [{"id": SECRET * 5, "text": "x"}]}, 400, "schema_violation"),
        "dup_id": ({"messages": [ok, ok]}, 400, "schema_violation"),
        "text_type": ({"messages": [{"id": "e1", "text": [SECRET]}]}, 400, "schema_violation"),
        "text_long": ({"messages": [{"id": "e1", "text": SECRET * 300}]}, 400, "schema_violation"),
        "reply_to_type": ({"messages": [{**ok, "reply_to": 7}]}, 400, "schema_violation"),
        "taxonomy_mismatch": ({"taxonomy_version": SECRET, "messages": [ok]}, 409, "taxonomy_mismatch"),
        "nan": (b'{"messages":[{"id":"e1","text":"' + SECRET.encode() + b'","reply_to":NaN}]}', 400, "bad_json"),
        "dup_key": (b'{"messages":[],"messages":[{"id":"e1","text":"' + SECRET.encode() + b'"}]}', 400, "bad_json"),
    }
    body, want_status, want_code = bodies[case]
    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    st, doc, txt = _req(server, "POST", "/v1/classify", raw=raw)
    assert st == want_status and doc["ok"] is False and doc["error"]["code"] == want_code
    assert SECRET.encode() not in txt
    assert set(doc["error"]) == {"code", "message", "retryable"}


def test_body_cap_and_content_length(server):
    # declared oversize Content-Length: refused from the header alone (body never read)
    with socket.create_connection(("127.0.0.1", server), timeout=10) as s:
        s.sendall(b"POST /v1/classify HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n"
                  b"Content-Length: 1048577\r\n\r\n{")
        resp = b""
        while chunk := s.recv(4096):
            resp += chunk
    assert resp.startswith(b"HTTP/1.1 413") and b"too_large" in resp
    # exactly at the cap is accepted as far as the cap goes (then fails validation, not size)
    at_cap = b'{"messages":[{"id":"b1","text":"' + b"x" * (1_048_576 - 40) + b'"}]}'
    at_cap += b" " * (1_048_576 - len(at_cap))
    st, doc, _ = _req(server, "POST", "/v1/classify", raw=at_cap)
    assert len(at_cap) == 1_048_576 and st == 400 and doc["error"]["code"] == "schema_violation"
    # missing Content-Length (raw socket)
    with socket.create_connection(("127.0.0.1", server), timeout=10) as s:
        s.sendall(b"POST /v1/classify HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n\r\n")
        resp = s.recv(4096)
    assert resp.startswith(b"HTTP/1.1 413")
    st, doc, _ = _req(server, "POST", "/v1/classify", raw=b"{}", headers={"Content-Length": "abc"})
    assert st in (400, 413)


def test_discourse_served_and_routing(server):
    """0.3.0: /v1/discourse is served (full contract tests in
    tests/test_equilibrium_discourse_service.py); a classify-shaped body is refused closed."""
    st, doc, txt = _req(server, "POST", "/v1/discourse", {"messages": [{"id": "d1", "text": SECRET}]})
    assert st == 400 and doc["error"]["code"] == "bad_request" and SECRET.encode() not in txt
    assert _req(server, "GET", "/v1/nope")[0] == 404
    assert _req(server, "POST", "/v1/nope", {})[0] == 404
    assert _req(server, "PUT", "/v1/classify", {})[0] == 405
    assert _req(server, "GET", "/v1/classify")[0] == 404


# ------------------------------------------- in-process service invariants ---
@pytest.fixture(scope="module")
def service():
    os.environ["OZMA_NO_LLM"] = "1"
    from services.equilibrium_classifier import server as srv
    return srv, srv.ClassifierService()


def test_strong_digest_checked_every_1000_batches(service):
    srv, svc = service
    msgs = synthetic_messages(1000, seed=11)
    for i, m in enumerate(msgs):
        svc.classify([m])
        if i == 998:
            assert svc.last_strong["batch"] == 0
    assert svc.batches == 1000 and svc.last_strong == {"batch": 1000, "digest": svc.digest0, "ok": True}
    assert tuple(svc.snap.source_revision) == svc.rev0
    assert srv.strong_digest(svc.base) == svc.digest0


def test_drift_is_fatal(service):
    srv, _ = service
    svc = srv.ClassifierService()

    class DriftingSnap:  # simulates a base whose revision moved after boot
        def __init__(self, real):
            self.real = real

        @property
        def source_revision(self):
            r = tuple(self.real.source_revision)
            return (r[0] + 1, r[1], r[2])

        def fork(self):
            return self.real.fork()

    svc.snap = DriftingSnap(svc.snap)
    with pytest.raises(srv.BaseDrift):
        svc.classify([{"id": "d1", "text": "hello"}])
    assert svc.healthy is False and svc.health() is False
    with pytest.raises(srv.BaseDrift):
        svc.classify([{"id": "d2", "text": "hello"}])


def test_to_wire_never_chooses_between_speech_acts():
    from services.equilibrium_classifier import server as srv
    two = {"id": "x", "rule_ids": ["a@0.1.0"], "labels": {"msg.speech_act": {"values": ["question", "assertion"]}}}
    w = srv.to_wire(two)
    assert "speech_act" not in w and w["rule_ids"] == ["a:0.1.0"] and w["deescalation"] == 0.0
    assert all(w[f] == 0.0 for f in _CUE_FIELDS) and w["domains"] == []


# --------------------------------------------------------- Phase 9 exit ---
_WRITE_CALL = re.compile(r'^\d+\s+(open|openat|creat|mkdir|mkdirat|rename|renameat2?|unlink|unlinkat|'
                         r'truncate|link|linkat|symlink|symlinkat)\((.*)$')


def _strace_writes(log: Path, tmp: Path) -> list[str]:
    """Paths the server tree created/modified outside tmp (strace -f log)."""
    bad = []
    for line in log.read_text(errors="replace").splitlines():
        m = _WRITE_CALL.match(line)
        if not m or "= -1" in line.rsplit(")", 1)[-1]:
            continue
        call, args = m.groups()
        if call in ("open", "openat") and not re.search(r"O_WRONLY|O_RDWR|O_CREAT|O_TRUNC", args):
            continue
        for p in re.findall(r'"([^"]*)"', args):
            if p.startswith(("/dev/null", "/dev/tty", "/dev/pts")) or p.startswith(str(tmp)):
                continue
            if not p.startswith("/"):  # relative to cwd == tmp
                continue
            bad.append(f"{call}: {p}")
    return bad


def _strace_ok(tmp) -> bool:
    if not shutil.which("strace"):
        return False
    r = subprocess.run(["strace", "-f", "-o", str(tmp / "probe.log"), "true"], capture_output=True)
    return r.returncode == 0


def test_phase9_exit_10k_base_unchanged_no_writes(tmp_path):
    """10,000 synthetic messages in 100-message batches: base source_revision AND
    strong digest unchanged; no file written outside tmp_path."""
    use_strace = _strace_ok(tmp_path)
    before_tree = _tree_state(ROOT)
    port = _free_port()
    prefix = (["strace", "-f", "-qq", "-o", str(tmp_path / "strace.log"), "-e",
               "trace=open,openat,creat,mkdir,mkdirat,rename,renameat,renameat2,unlink,unlinkat,"
               "truncate,link,linkat,symlink,symlinkat"] if use_strace else None)
    proc, _ = _start(tmp_path, port, prefix=prefix)
    try:
        info0 = _req(port, "GET", "/v1/info")[1]
        msgs = synthetic_messages(10_000)
        _replay(port, msgs)
        assert _req(port, "GET", "/healthz")[0] == 200  # forces a strong re-digest
        info1 = _req(port, "GET", "/v1/info")[1]
    finally:
        _stop(proc)
    b0, b1 = info0["base"], info1["base"]
    assert b1["messages_served"] - b0["messages_served"] == 10_000
    assert b1["batches_served"] - b0["batches_served"] == 100
    assert b0["source_revision"] == b1["source_revision"] == b1["boot_source_revision"]
    assert b1["strong_digest_last"]["batch"] == b1["batches_served"]
    assert b1["strong_digest_last"]["ok"] is True
    assert b1["strong_digest_last"]["digest"] == b0["strong_digest_boot"] == b1["strong_digest_boot"]
    after_tree = _tree_state(ROOT)
    changed = sorted(k for k in set(before_tree) | set(after_tree) if before_tree.get(k) != after_tree.get(k))
    assert changed == [], changed
    if use_strace:
        log = (tmp_path / "strace.log").read_text(errors="replace")
        assert "equilibrium_msg.json" in log and "O_RDONLY" in log  # trace is live, not vacuous
        probe = f'1 openat(AT_FDCWD, "{ROOT}/seeds/x.json", O_WRONLY|O_CREAT, 0644) = 3'
        (tmp_path / "probe_neg.log").write_text(probe + "\n")
        assert _strace_writes(tmp_path / "probe_neg.log", tmp_path)  # parser catches a write
        bad = _strace_writes(tmp_path / "strace.log", tmp_path)
        assert bad == [], bad[:20]
    print(f"\nPHASE9 source_revision={b1['source_revision']} digest={b1['strong_digest_boot'][:16]} "
          f"batches={b1['batches_served']} strace={'yes' if use_strace else 'NO (tree snapshot only)'}")


def test_measure_throughput_and_rss_concurrency1(tmp_path):
    """Concurrency 1, batch 100, 10,000 synthetic msgs over loopback HTTP. Reported,
    not gated: Equilibrium targets are 4,000 msgs/s pool-wide and 384 MB."""
    port = _free_port()
    proc, boot_s = _start(tmp_path, port)
    try:
        status = Path(f"/proc/{proc.pid}/status")
        rss_boot = int(re.search(r"VmHWM:\s+(\d+)", status.read_text()).group(1))
        _replay(port, synthetic_messages(1_000, seed=1))  # warm-up (lazy imports)
        msgs = synthetic_messages(10_000, seed=2)
        t = time.perf_counter()
        lat = _replay(port, msgs)
        wall = time.perf_counter() - t
        hwm = int(re.search(r"VmHWM:\s+(\d+)", status.read_text()).group(1))
    finally:
        _stop(proc)
    lat.sort()
    p50, p95 = lat[len(lat) // 2], lat[int(len(lat) * 0.95) - 1]
    rate = len(msgs) / wall
    print(f"\nMEASURE c=1 batch=100 n=10000: {rate:.0f} msgs/s, wall {wall:.2f}s, "
          f"batch p50 {p50 * 1000:.1f} ms p95 {p95 * 1000:.1f} ms, boot-to-healthy {boot_s:.2f}s, "
          f"peak RSS (VmHWM) boot {rss_boot / 1024:.1f} MiB -> after {hwm / 1024:.1f} MiB; "
          f"targets 4000 msgs/s pool-wide, 384 MB")
    assert rate > 0 and hwm > 0
