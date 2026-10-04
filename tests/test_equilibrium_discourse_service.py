"""Equilibrium sidecar POST /v1/discourse (stream T3b): shared HTTP contract,
closed validation without input echo, base-unchanged replay, throughput / RSS.

Synthetic windows only (pseudonyms member_###); no corpus, no LLM (OZMA_NO_LLM=1).
Servers run as subprocesses on 127.0.0.1 with cwd/TMPDIR = a pytest tmp dir.
Measurements are printed (run with -s to see them).
"""
from __future__ import annotations

import http.client
import json
import random
import re
import socket
import time
from pathlib import Path

import pytest

from test_equilibrium_classifier_service import (  # shared harness (same directory)
    ROOT, SECRET, _CODE, _client_parse, _free_port, _req, _start, _stop, _strace_ok,
    _strace_writes, _tree_state, synthetic_messages)

TAX = "eq-tax-0.7.0"
# The Equilibrium worker client's reply checks (equilibrium_worker/classify.py parse_discourse).
_ID = re.compile(r"^[A-Za-z0-9_.:@!+=-]{1,255}$")
_TRAIT = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){0,7}$")
_TAXONOMY = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.+_-]{0,63}$")
_DISCOURSE_KEYS = {"ok", "taxonomy_version", "window_id", "messages", "quanta", "episodes"}
_Q_REQ = {"actor_ref", "trait", "polarity", "match", "evidence", "counter_evidence", "rule_ids"}
_E_KEYS = {"episode_id", "kind", "actor_refs", "turns", "facets", "generative", "rule_ids"}


def client_parse_discourse(doc: dict, window: dict, turns: list[dict]) -> None:
    """Mirror of equilibrium_worker.classify.parse_discourse acceptance."""
    assert set(doc) == _DISCOURSE_KEYS and doc["ok"] is True
    assert doc["window_id"] == window["window_id"] and _TAXONOMY.fullmatch(doc["taxonomy_version"])
    ids = [t["id"] for t in turns]
    actors = {t["actor_ref"] for t in turns}
    assert [m["id"] for m in doc["messages"]] == ids
    for m in doc["messages"]:
        _client_parse(m)
    assert len(doc["quanta"]) <= 5000 and len(doc["episodes"]) <= 5000
    for q in doc["quanta"]:
        assert _Q_REQ <= set(q) <= _Q_REQ | {"target_ref"}, q
        assert q["actor_ref"] in actors and q["polarity"] in ("+", "-")
        assert q["match"] in ("exact", "partial", "weak") and _TRAIT.fullmatch(q["trait"])
        if "target_ref" in q:
            assert q["target_ref"] in actors and q["target_ref"] != q["actor_ref"]
        ev, cev = q["evidence"], q["counter_evidence"]
        assert set(ev) <= set(ids) and set(cev) <= set(ids) and (ev or cev)
        assert not set(ev) & set(cev)
        assert len(q["rule_ids"]) <= 64 and all(_CODE.fullmatch(r) and "@" not in r for r in q["rule_ids"])
    seen = set()
    for e in doc["episodes"]:
        assert set(e) == _E_KEYS and _ID.fullmatch(e["episode_id"]) and e["episode_id"] not in seen
        seen.add(e["episode_id"])
        assert e["generative"] in (True, False, None)
        assert len(e["facets"]) <= 32
        assert all(set(f) == {"code", "match"} and _TRAIT.fullmatch(f["code"])
                   and f["match"] in ("exact", "partial", "weak") for f in e["facets"])
        assert _TRAIT.fullmatch(e["kind"]) and e["actor_refs"] and set(e["actor_refs"]) <= actors
        assert e["turns"] and set(e["turns"]) <= set(ids)
        assert all(_CODE.fullmatch(r) for r in e["rule_ids"])


MEETING = [
    ("t01", "actor_a", "Trust me, in my 20 years this has never been the problem."),
    ("t02", "member_003", "Could the cache be cold after the deploy?"),
    ("t03", "actor_a", "That is ridiculous, I know what I'm doing."),
    ("t04", "member_003", "Never mind, I'll leave it there."),
    ("t05", "actor_a", "We ship it as is."),
    ("t06", "expert_e", "However, the benchmark shows p99 latency doubled, see https://example.org/bench/42"),
    ("t07", "actor_a", "Fair point, I hadn't considered that."),
    ("t08", "member_002", "Let's step back and look at the data together."),
    ("t09", "actor_a", "Agreed, let's look at it."),
]
WINDOW = {"window_id": "w_meet_1", "kind": "meeting"}
# 0.5.0: adjacency is not structure, so the golden meeting DECLARES the replies the
# pre-0.5.0 adjacency rule inferred (each turn replies to the previous one)
TURNS = [{"id": i, "actor_ref": a, "text": t, **({"reply_to": MEETING[k - 1][0]} if k else {})}
         for k, (i, a, t) in enumerate(MEETING)]

_CUE_LINES = [
    "That's not a fair point.", "Fair point, I hadn't considered that.", "Trust me, I know what I'm doing.",
    "This is ridiculous.", "However, see https://example.org/x for the numbers.", "Let's step back.",
    "Perhaps you're right.", "As a nurse I see this weekly.", "Never mind, I'll leave it there.",
    "Why would that matter here?", "The p99 latency doubled.", "You people never listen.",
]
# 0.4.0 space-climate cue lines (dissent, error admission, challenge, questions, dismissal)
_CLIMATE_LINES = [
    "I disagree, the cache is warm.", "The cache isn't cold.", "I was wrong about the deploy.",
    "I was not wrong.", "What's the evidence for that?", "But why should we trust it?",
    "Stay in your lane.", "Who owns the warmup job?", "Is the queue drained yet?",
    "Perhaps that's not the case.", "I don't disagree.", "Good point, see https://example.org/y",
]
CLIMATE_TRAITS = ("voice.dissent", "voice.error_admission", "inquiry.challenge", "inquiry.answered",
                  "inquiry.unanswered", "response.dismissal", "response.engagement")


def synthetic_window(n: int, seed: int, kind: str = "thread", actors: int = 12,
                     lines: list[str] | None = None) -> tuple[dict, list[dict]]:
    """Deterministic synthetic window (no corpus): chat lines + cue lines, pseudonymous
    actors, threads reply to an earlier turn, meetings carry no reply edges."""
    rnd = random.Random(seed)
    base = synthetic_messages(n, seed=seed)
    turns = []
    for i, m in enumerate(base):
        text = rnd.choice(lines or _CUE_LINES) if rnd.random() < 0.35 else m["text"]
        t = {"id": f"w{seed}_{i:04d}", "actor_ref": f"member_{rnd.randint(1, actors):03d}", "text": text,
             "ts_ms": 1_700_000_000_000 + i * 1000}
        if kind == "thread" and i and rnd.random() < 0.7:
            t["reply_to"] = f"w{seed}_{rnd.randint(max(0, i - 8), i - 1):04d}"
        turns.append(t)
    return {"window_id": f"w_syn_{seed}", "kind": kind}, turns


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("eqdisc")
    port = _free_port()
    proc, _ = _start(tmp, port)
    yield port
    _stop(proc)


def _post(port, body, **kw):
    return _req(port, "POST", "/v1/discourse", body, **kw)


def test_info_lists_trait_vocabulary(server):
    st, doc, _ = _req(server, "GET", "/v1/info")
    assert st == 200 and doc["taxonomy_version"] == TAX and doc["seed_pack_version"] == "0.7.0"
    assert doc["endpoints"]["/v1/discourse"] == "ok"
    ts = doc["trait_status"]
    assert ts["competence.claimed"] == "shadow" and ts["interaction.floor"] == "shadow"
    # 0.4.0 space-climate traits, all shadow
    assert {k: ts.get(k) for k in CLIMATE_TRAITS} == {k: "shadow" for k in CLIMATE_TRAITS}
    assert all(v == "disabled" for k, v in ts.items() if k.startswith("pattern."))
    assert all(v == "shadow" for k, v in ts.items() if not k.startswith("pattern."))
    assert all(_TRAIT.fullmatch(k) for k in ts)
    assert doc["episode_kind_status"] == {"dispute": "shadow"}
    assert set(doc["facet_codes"]) == {"epistemic", "status", "procedural", "affective", "tribal"}
    assert doc["limits"]["max_turns"] == 500


def test_discourse_contract_golden_meeting(server):
    st, doc, _ = _post(server, {"taxonomy_version": TAX, "window": WINDOW, "turns": TURNS})
    assert st == 200, doc
    client_parse_discourse(doc, WINDOW, TURNS)
    assert doc["taxonomy_version"] == TAX and doc["window_id"] == "w_meet_1"
    keys = {(q["actor_ref"], q["trait"], q["polarity"], q.get("target_ref")) for q in doc["quanta"]}
    assert ("actor_a", "interaction.floor", "+", None) in keys
    assert ("actor_a", "competence.claim_grounding", "-", None) in keys
    assert ("member_003", "interaction.withdrawal", "+", None) in keys
    assert all(r.endswith(":0.7.0") for q in doc["quanta"] for r in q["rule_ids"])
    assert [e["episode_id"] for e in doc["episodes"]] == ["ep:t02", "ep:t05"]
    # messages[] are byte-identical in shape to /v1/classify items for the same text
    st2, cdoc, _ = _req(server, "POST", "/v1/classify",
                        {"messages": [{"id": t["id"], "text": t["text"]} for t in TURNS]})
    assert st2 == 200
    for dm, cm in zip(doc["messages"], cdoc["labels"]):
        assert set(dm) == set(cm)
        for k in dm:
            if k != "rule_ids":
                assert dm[k] == cm[k], (dm["id"], k)
    # deterministic across requests (fork per request)
    assert _post(server, {"window": WINDOW, "turns": TURNS})[1] == doc


def test_discourse_contract_climate_window(server):
    """0.4.0: the /v1/discourse contract is unchanged; quanta just carry the new codes."""
    from test_equilibrium_climate import CLIMATE
    win = {"window_id": "w_climate_1", "kind": "thread"}
    turns = [{"id": i, "actor_ref": a, "text": t, **({"reply_to": r} if r else {})} for i, a, t, r in CLIMATE]
    st, doc, _ = _post(server, {"taxonomy_version": TAX, "window": win, "turns": turns})
    assert st == 200, doc
    client_parse_discourse(doc, win, turns)
    got = {q["trait"] for q in doc["quanta"]} & set(CLIMATE_TRAITS)
    assert got == set(CLIMATE_TRAITS)
    ans = next(q for q in doc["quanta"] if q["trait"] == "inquiry.answered")
    assert (ans["actor_ref"], ans["target_ref"], ans["evidence"]) == ("expert_e", "member_m", ["c06", "c07"])
    un = next(q for q in doc["quanta"] if q["trait"] == "inquiry.unanswered")
    assert (un["actor_ref"], un["evidence"], "target_ref" in un) == ("member_n", ["c08"], False)
    assert all(r.endswith(":0.7.0") for q in doc["quanta"] for r in q["rule_ids"])


def test_dangling_reply_and_no_cue_window(server):
    turns = [{"id": "d1", "actor_ref": "member_010", "text": "ok", "reply_to": "outside_window_7"},
             {"id": "d2", "actor_ref": "member_011", "text": "the build is green", "ts_ms": 5}]
    win = {"window_id": "w_d", "kind": "thread"}
    st, doc, _ = _post(server, {"window": win, "turns": turns})
    # 0.7.0: no cue quanta, no episodes -- only each speaker's interaction.floor_share
    assert st == 200 and doc["episodes"] == []
    assert [(q["trait"], q["actor_ref"], q["evidence"]) for q in doc["quanta"]] == [
        ("interaction.floor_share", "member_010", ["d1"]), ("interaction.floor_share", "member_011", ["d2"])]
    client_parse_discourse(doc, win, turns)


_OK_T = {"id": "e1", "actor_ref": "member_001", "text": SECRET}
_OK_W = {"window_id": "w_e", "kind": "thread"}


@pytest.mark.parametrize("case", [
    "bad_json", "not_object", "unknown_top", "no_window", "window_extra", "window_kind", "window_id_chars",
    "turns_type", "empty", "too_many", "turn_type", "turn_unknown_key", "id_type", "id_chars", "id_long",
    "dup_id", "actor_missing", "actor_chars", "text_type", "text_long", "reply_to_type", "ts_bool",
    "ts_negative", "ts_float", "taxonomy_mismatch", "nan", "dup_key",
])
def test_discourse_errors_closed_and_no_echo(server, case):
    S = SECRET
    bodies = {
        "bad_json": (b"{" + S.encode(), 400, "bad_json"),
        "not_object": ([S], 400, "bad_request"),
        "unknown_top": ({"window": _OK_W, "turns": [_OK_T], S: 1}, 400, "bad_request"),
        "no_window": ({"turns": [_OK_T]}, 400, "bad_request"),
        "window_extra": ({"window": {**_OK_W, S: 1}, "turns": [_OK_T]}, 400, "bad_request"),
        "window_kind": ({"window": {**_OK_W, "kind": S}, "turns": [_OK_T]}, 400, "bad_request"),
        "window_id_chars": ({"window": {**_OK_W, "window_id": S + " /x"}, "turns": [_OK_T]}, 400, "bad_request"),
        "turns_type": ({"window": _OK_W, "turns": {S: 1}}, 400, "bad_request"),
        "empty": ({"window": _OK_W, "turns": []}, 400, "bad_request"),
        "too_many": ({"window": _OK_W, "turns": [{**_OK_T, "id": f"x{i}"} for i in range(501)]}, 413, "too_large"),
        "turn_type": ({"window": _OK_W, "turns": [S]}, 400, "bad_request"),
        "turn_unknown_key": ({"window": _OK_W, "turns": [{**_OK_T, S: 1}]}, 400, "bad_request"),
        "id_type": ({"window": _OK_W, "turns": [{**_OK_T, "id": 5}]}, 400, "bad_request"),
        "id_chars": ({"window": _OK_W, "turns": [{**_OK_T, "id": S + " x"}]}, 400, "bad_request"),
        "id_long": ({"window": _OK_W, "turns": [{**_OK_T, "id": "a" * 253}]}, 400, "bad_request"),
        "dup_id": ({"window": _OK_W, "turns": [_OK_T, _OK_T]}, 400, "bad_request"),
        "actor_missing": ({"window": _OK_W, "turns": [{"id": "e1", "text": S}]}, 400, "bad_request"),
        "actor_chars": ({"window": _OK_W, "turns": [{**_OK_T, "actor_ref": S + "?"}]}, 400, "bad_request"),
        "text_type": ({"window": _OK_W, "turns": [{**_OK_T, "text": [S]}]}, 400, "bad_request"),
        "text_long": ({"window": _OK_W, "turns": [{**_OK_T, "text": S * 300}]}, 400, "bad_request"),
        "reply_to_type": ({"window": _OK_W, "turns": [{**_OK_T, "reply_to": 7}]}, 400, "bad_request"),
        "ts_bool": ({"window": _OK_W, "turns": [{**_OK_T, "ts_ms": True}]}, 400, "bad_request"),
        "ts_negative": ({"window": _OK_W, "turns": [{**_OK_T, "ts_ms": -1}]}, 400, "bad_request"),
        "ts_float": ({"window": _OK_W, "turns": [{**_OK_T, "ts_ms": 1.5}]}, 400, "bad_request"),
        "taxonomy_mismatch": ({"taxonomy_version": S, "window": _OK_W, "turns": [_OK_T]}, 409, "taxonomy_mismatch"),
        "nan": (b'{"window":{"window_id":"w","kind":"thread"},"turns":[{"id":"e1","actor_ref":"m",'
                b'"text":"' + S.encode() + b'","ts_ms":NaN}]}', 400, "bad_json"),
        "dup_key": (b'{"turns":[],"turns":[{"id":"e1","text":"' + S.encode() + b'"}]}', 400, "bad_json"),
    }
    body, want_status, want_code = bodies[case]
    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    st, doc, txt = _req(server, "POST", "/v1/discourse", raw=raw)
    assert st == want_status and doc["ok"] is False and doc["error"]["code"] == want_code, (st, doc)
    assert SECRET.encode() not in txt
    assert set(doc["error"]) == {"code", "message", "retryable"} and doc["error"]["retryable"] is False


def test_discourse_body_cap(server):
    from services.equilibrium_classifier.server import MAX_DISCOURSE_BODY_BYTES as CAP
    with socket.create_connection(("127.0.0.1", server), timeout=10) as s:
        s.sendall(b"POST /v1/discourse HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n"
                  b"Content-Length: " + str(CAP + 1).encode() + b"\r\n\r\n{")
        resp = b""
        while chunk := s.recv(4096):
            resp += chunk
    assert resp.startswith(b"HTTP/1.1 413") and b"too_large" in resp
    # a full 500-turn window of 4000-char texts fits under the cap and is served
    win = {"window_id": "w_big", "kind": "meeting"}
    turns = [{"id": f"b{i}", "actor_ref": f"member_{i % 7:03d}", "text": ("ok then " * 500)[:4000]}
             for i in range(500)]
    st, doc, _ = _post(server, {"window": win, "turns": turns}, timeout=300)
    assert st == 200, doc
    client_parse_discourse(doc, win, turns)


# ---- PREREG P7: base unchanged after >= 10k turns via /v1/discourse ---------
def test_base_unchanged_after_10k_discourse_turns(tmp_path):
    use_strace = _strace_ok(tmp_path)
    before_tree = _tree_state(ROOT)
    port = _free_port()
    prefix = (["strace", "-f", "-qq", "-o", str(tmp_path / "strace.log"), "-e",
               "trace=open,openat,creat,mkdir,mkdirat,rename,renameat,renameat2,unlink,unlinkat,"
               "truncate,link,linkat,symlink,symlinkat"] if use_strace else None)
    proc, _ = _start(tmp_path, port, prefix=prefix)
    try:
        info0 = _req(port, "GET", "/v1/info")[1]
        plan = [(500, 100 + k) for k in range(20)] + [(100, 200 + k) for k in range(100)]
        for k, (n, seed) in enumerate(plan):  # PREREG P7: 20 x 500 + 100 x 100 turns
            win, turns = synthetic_window(n, seed=seed, kind="thread" if k % 2 else "meeting",
                                          lines=_CUE_LINES + _CLIMATE_LINES)  # 0.4.0: exercise climate rules
            st, doc, _ = _post(port, {"window": win, "turns": turns}, timeout=300)
            assert st == 200, doc
            client_parse_discourse(doc, win, turns)
        assert _req(port, "GET", "/healthz")[0] == 200  # forces a strong re-digest
        info1 = _req(port, "GET", "/v1/info")[1]
    finally:
        _stop(proc)
    b0, b1 = info0["base"], info1["base"]
    assert b1["turns_served"] - b0["turns_served"] == 20_000 and b1["windows_served"] == 120
    assert b0["source_revision"] == b1["source_revision"] == b1["boot_source_revision"]
    assert b1["strong_digest_last"]["ok"] is True
    assert b1["strong_digest_last"]["digest"] == b0["strong_digest_boot"] == b1["strong_digest_boot"]
    after_tree = _tree_state(ROOT)
    changed = sorted(k for k in set(before_tree) | set(after_tree) if before_tree.get(k) != after_tree.get(k))
    assert changed == [], changed
    if use_strace:
        log = (tmp_path / "strace.log").read_text(errors="replace")
        assert "equilibrium_quanta.json" in log and "O_RDONLY" in log  # trace is live
        bad = _strace_writes(tmp_path / "strace.log", tmp_path)
        assert bad == [], bad[:20]
    print(f"\nP7 discourse turns=20000 windows=120 source_revision={b1['source_revision']} "
          f"digest={b1['strong_digest_boot'][:16]} strace={'yes' if use_strace else 'NO (tree snapshot only)'}")


# ---- PREREG P6: throughput / RSS at concurrency 1 (reported, not gated) ------
def _replay_windows(port, windows):
    lat = []
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=300)
    try:
        for win, turns in windows:
            body = json.dumps({"window": win, "turns": turns}).encode()
            t = time.perf_counter()
            c.request("POST", "/v1/discourse", body=body, headers={"Content-Type": "application/json"})
            r = c.getresponse()
            doc = json.loads(r.read())
            lat.append(time.perf_counter() - t)
            assert r.status == 200, doc
    finally:
        c.close()
    return lat


def test_measure_discourse_throughput_and_rss_concurrency1(tmp_path):
    port = _free_port()
    proc, boot_s = _start(tmp_path, port)
    try:
        status = Path(f"/proc/{proc.pid}/status")
        rss_boot = int(re.search(r"VmHWM:\s+(\d+)", status.read_text()).group(1))
        _replay_windows(port, [synthetic_window(200, seed=1)])  # warm-up
        res = {}
        for n, reps in ((50, 20), (200, 10), (500, 10)):
            wins = [synthetic_window(n, seed=1000 + n + i, kind="thread" if i % 2 else "meeting")
                    for i in range(reps)]
            lat = sorted(_replay_windows(port, wins))
            res[n] = (lat[len(lat) // 2], lat[int(len(lat) * 0.95) - 1], lat[-1], n * reps / sum(lat), reps)
        for n, reps in ((200, 10), (500, 10)):  # 0.4.0: climate-cue mix (not comparable to slice 1)
            wins = [synthetic_window(n, seed=3000 + n + i, kind="thread" if i % 2 else "meeting",
                                     lines=_CUE_LINES + _CLIMATE_LINES) for i in range(reps)]
            lat = sorted(_replay_windows(port, wins))
            res[f"{n} climate-mix"] = (lat[len(lat) // 2], lat[int(len(lat) * 0.95) - 1], lat[-1],
                                       n * reps / sum(lat), reps)
        hwm = int(re.search(r"VmHWM:\s+(\d+)", status.read_text()).group(1))
    finally:
        _stop(proc)
    for n, (p50, p95, mx, rate, reps) in res.items():
        print(f"\nMEASURE discourse c=1 window={n} turns x{reps}: p50 {p50 * 1000:.0f} ms p95 {p95 * 1000:.0f} ms "
              f"max {mx * 1000:.0f} ms, {rate:.0f} turns/s")
    print(f"MEASURE boot-to-healthy {boot_s:.2f}s, peak RSS (VmHWM) boot {rss_boot / 1024:.1f} MiB -> "
          f"after {hwm / 1024:.1f} MiB; PREREG P6 targets: 500-turn p95 <= 1.5 s, 200-turn <= 0.5 s, 384 MB")
    assert hwm > 0
