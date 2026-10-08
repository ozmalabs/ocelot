"""
model_endpoint_typer — Typer B: claim typing via the organizer's house MODEL_ENDPOINT.

Implements the CALL PATH a real Track 2 submission would use at run time (PHASE0 §1):
  - egress ONLY via the audited proxy (HTTP_PROXY / HTTPS_PROXY env), never a vendor API;
  - target = MODEL_ENDPOINT (organizer-hosted, OpenAI-compatible), model id = MODEL_NAME;
  - env-driven, nothing hardcoded; vendor tools off; no participant API keys.

*** NO NETWORK IS AVAILABLE LOCALLY *** (T2 net is restricted; local smoke is --network=none;
vendor APIs are refused; no keys exist). So this module PROVES THE ARCHITECTURE end-to-end
(build request -> send via transport -> parse JSON -> map to {up,down,none}) by running the
exact same code against a MOCK transport that returns a canned OpenAI-shaped response.

The live accuracy number is NOT produced here and is NOT fabricated. It requires the house
endpoint. See PHASE3_DERISK_PREREG.md §4 and PHASE3_DERISK_RESULTS.md.

Transport seam: `send_fn(url, headers, payload) -> dict`. Real runs pass the proxy-aware
HTTP sender; this de-risk passes `mock_transport`.
"""
from __future__ import annotations

import json
import os
import re
from typing import Callable

SYSTEM_PROMPT = (
    "You are a monetary-policy claim typer. Given one snippet of central-bank or macro text, "
    "decide the FORECAST-RELEVANT direction for the rate/FX target: the forward-guidance/regime "
    "tone, NOT the surface action verb. A cut delivered with a shallower path is hawkish (up). "
    "Tapering/QT (reducing asset purchases) is hawkish (up). QE (increasing purchases) is dovish "
    "(down). Reply with STRICT JSON only: "
    '{"direction": "up|down|none", "confidence": 0.0-1.0}. '
    "up=hawkish/tightening/less-easing, down=dovish/easing/backstop, none=neutral/balanced/pure-data."
)


def build_request(snippet_text: str) -> tuple[str, dict, dict]:
    """Return (url, headers, payload) for an OpenAI-compatible /v1/chat/completions call
    through the audited proxy. Everything env-driven per PHASE0 §1."""
    endpoint = os.environ.get("MODEL_ENDPOINT", "http://model-endpoint.invalid")
    model = os.environ.get("MODEL_NAME", "house-model")
    url = endpoint.rstrip("/") + "/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    # NOTE: no Authorization / vendor key — the audited proxy injects auth; participants have none.
    payload = {
        "model": model,
        "temperature": 0.0,
        "max_tokens": 40,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": snippet_text},
        ],
        "response_format": {"type": "json_object"},
    }
    return url, headers, payload


def _proxies() -> dict:
    """The proxy config a live run would honor (PHASE0: egress only via HTTP_PROXY/HTTPS_PROXY)."""
    p = {}
    if os.environ.get("HTTP_PROXY"):
        p["http"] = os.environ["HTTP_PROXY"]
    if os.environ.get("HTTPS_PROXY"):
        p["https"] = os.environ["HTTPS_PROXY"]
    return p


def parse_response(resp: dict) -> tuple[str, dict]:
    """Extract {up,down,none} from an OpenAI-compatible chat completion. Robust to the model
    wrapping JSON in prose or code fences."""
    try:
        content = resp["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        return "none", {"parse_error": f"bad response shape: {e}"}
    # find the first JSON object in the content
    m = re.search(r"\{.*\}", content, re.S)
    raw = m.group(0) if m else content
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        # fallback: scan for a bare direction word
        low = content.lower()
        for d in ("up", "down", "none"):
            if d in low:
                return d, {"parse": "fallback-word", "content": content[:80]}
        return "none", {"parse_error": "no json, no word", "content": content[:80]}
    direction = str(obj.get("direction", "none")).lower().strip()
    if direction not in ("up", "down", "none"):
        direction = "none"
    return direction, {"parse": "json", "confidence": obj.get("confidence")}


def type_claim(snippet_text: str, send_fn: Callable[[str, dict, dict], dict]) -> tuple[str, dict]:
    """Full path: build -> send (via injected transport) -> parse -> map. send_fn is the
    proxy-aware HTTP sender in production, or mock_transport in this de-risk."""
    url, headers, payload = build_request(snippet_text)
    resp = send_fn(url, headers, payload)
    direction, dbg = parse_response(resp)
    dbg["proxies_configured"] = bool(_proxies())
    dbg["endpoint"] = url
    return direction, dbg


# ---------------------------------------------------------------------------------------
# MOCK transport. Returns a canned OpenAI-shaped response. It uses the same rules_typer
# lexicon to pick a plausible direction so the mock is not a constant, but this is a STUB:
# it does NOT represent live model quality. Clearly labelled as mock.
# ---------------------------------------------------------------------------------------
def mock_transport(url: str, headers: dict, payload: dict) -> dict:
    """A stubbed OpenAI /v1/chat/completions response. NOT a live model. Labelled mock."""
    user_text = payload["messages"][-1]["content"]
    # Deterministic stand-in direction so the parse path has something to chew on.
    # (Uses the rules lexicon purely to avoid a constant; the number this yields is NOT
    #  a model-quality measurement and is not reported as accuracy.)
    try:
        from rules_typer import type_claim as _rules
        d, _ = _rules(user_text)
    except Exception:
        d = "none"
    content = json.dumps({"direction": d, "confidence": 0.5, "_mock": True})
    return {
        "id": "chatcmpl-mock", "object": "chat.completion", "model": payload["model"],
        "choices": [{"index": 0, "finish_reason": "stop",
                     "message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "_transport": "MOCK — no network; architecture proof only",
    }


def real_http_transport(url: str, headers: dict, payload: dict) -> dict:  # pragma: no cover
    """Proxy-aware sender for a LIVE run (needs network + house endpoint). Not exercised here."""
    import urllib.request
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    # urllib honors HTTP_PROXY/HTTPS_PROXY from env via ProxyHandler by default.
    with urllib.request.urlopen(req, timeout=30) as fh:
        return json.loads(fh.read().decode())


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sample = ("The Committee anticipates that it will be appropriate to raise the target range "
              "for the federal funds rate ...")
    url, headers, payload = build_request(sample)
    print("REQUEST url:", url)
    print("REQUEST payload (truncated):",
          json.dumps({**payload, "messages": "<omitted>"}, indent=2)[:300])
    resp = mock_transport(url, headers, payload)
    print("MOCK RESPONSE:", json.dumps(resp)[:200])
    d, dbg = type_claim(sample, mock_transport)
    print("PARSED direction:", d, "dbg:", dbg)
