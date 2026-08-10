"""LLMPartner — the agent's peer in conversation, backed by a real LLM.

Pluggable backend:

  openrouter  (default)   google/gemini-3.5-flash via OpenRouter
                          API. ~1s latency, capable, doesn't tax the
                          local GPU. Needs OPENROUTER_API_KEY in env.
  ollama      (fallback)  ollama on a remote machine via SSH tunnel.
                          Local model (gemma4:26b etc.); slower but
                          fully offline.

Selection: if OPENROUTER_API_KEY is set, openrouter wins; otherwise
fall back to ollama. Override explicitly by passing backend= to the
constructor.

NON-BLOCKING by design:
  - ask_async(prompt) dispatches in a background thread, returns a
    Future immediately (the agent's tick loop is not held up).
  - drain_completed() returns [(prompt, reply), …] for in-flight
    dispatches that have finished. The chat polls between turns
    so replies surface naturally as they arrive.

The system prompt positions the LLM as a peer talking to an emerging
mind that grounds concepts experientially. Short, plain replies; ask
questions back.
"""
from __future__ import annotations

import concurrent.futures
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Any

import requests


# ---------------------------------------------------------------------------
# backend defaults
# ---------------------------------------------------------------------------

# OpenRouter — preferred when available
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_DEFAULT_MODEL = "google/gemini-3.5-flash"

# Ollama — fallback to local serving on a remote machine
OLLAMA_DEFAULT_REMOTE = "192.168.40.253"
OLLAMA_DEFAULT_MODEL = "gemma4:26b"
OLLAMA_DEFAULT_PORT = 11434

DEFAULT_TIMEOUT = 30.0

# The LLMPartner is positioned as a PEER in a conversation. The
# previous prompt asked the LLM to dumb things down for "a young
# mind" — that implicitly tells the model to use a child-pitched
# vector space (simpler vocabulary, slower pacing) and gives the
# agent worse data to ground from.
#
# Instead: reply NORMALLY, at full capability. The agent will ask
# for clarification (via its own compose_inquiry mechanism on
# ungrounded words) when it can't follow. That feedback loop is
# the natural way the conversation calibrates to the agent's
# actual comprehension — same way two minds tune to each other in
# real dialogue. No pre-emptive simplification.
_PEER_SYSTEM_PROMPT = (
    "You are conversing with another mind. It is a graph-based "
    "substrate building its understanding through dialogue. Reply "
    "naturally as you would to any thoughtful interlocutor — concise, "
    "substantive, technically accurate. Do NOT pre-emptively simplify, "
    "explain at a child's level, or use small-words framing. If your "
    "interlocutor doesn't follow, it will ask you to clarify or "
    "rephrase, and you should then do so. Default to clarity and "
    "precision; calibrate down only on explicit signal."
)


# ---------------------------------------------------------------------------
# OpenRouter backend
# ---------------------------------------------------------------------------

class _OpenRouterBackend:
    """Calls google/gemini-3.5-flash (or whatever model) via the
    OpenRouter REST API."""
    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        # Cheap probe — request /models endpoint
        try:
            r = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def chat(self, messages: list) -> str | None:
        try:
            r = requests.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"},
                json={"model": self.model, "messages": messages},
                timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            content = (data.get("choices", [{}])[0]
                        .get("message", {}).get("content") or "").strip()
            return content
        except Exception:
            return None

    def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Ollama backend (with SSH tunnel)
# ---------------------------------------------------------------------------

class _Tunnel:
    """Background SSH local-forward keeping the ollama port mapped."""
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.proc: subprocess.Popen | None = None

    def is_open(self) -> bool:
        try:
            r = requests.get(
                f"http://localhost:{self.port}/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def open(self) -> None:
        if self.is_open():
            return
        self.proc = subprocess.Popen(
            ["ssh", "-N", "-L",
             f"{self.port}:localhost:{self.port}", self.host],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if self.is_open():
                return
            time.sleep(0.2)
        raise RuntimeError(
            f"ssh tunnel to {self.host}:{self.port} did not come up")

    def close(self) -> None:
        if self.proc is not None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            self.proc = None


class _OllamaBackend:
    """Calls a remote ollama via SSH tunnel."""
    def __init__(self, host: str, model: str, port: int, timeout: float):
        self.host = host
        self.model = model
        self.port = port
        self.timeout = timeout
        self.tunnel = _Tunnel(host, port)

    def is_available(self) -> bool:
        try:
            self.tunnel.open()
            return self.tunnel.is_open()
        except Exception:
            return False

    def chat(self, messages: list) -> str | None:
        try:
            self.tunnel.open()
        except Exception:
            return None
        try:
            r = requests.post(
                f"http://localhost:{self.port}/api/chat",
                json={"model": self.model, "messages": messages,
                       "stream": False},
                timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            content = (data.get("message", {}).get("content")
                        or "").strip()
            return content
        except Exception:
            return None

    def close(self) -> None:
        self.tunnel.close()


# ---------------------------------------------------------------------------
# LLMPartner — backend-pluggable peer
# ---------------------------------------------------------------------------

def _detect_backend(explicit: str | None) -> str:
    """Pick a backend. Explicit setting wins; otherwise OPENROUTER_API_KEY
    presence selects openrouter, else fall back to ollama."""
    if explicit is not None:
        return explicit
    if os.environ.get("OPENROUTER_API_KEY"):
        return "openrouter"
    return "ollama"


@dataclass
class LLMPartner:
    """Peer mind backed by an LLM. Pluggable backend; non-blocking
    dispatch. One instance per chat session — maintains conversation
    history within the session for continuity."""
    backend: str | None = None
    model: str | None = None
    host: str = OLLAMA_DEFAULT_REMOTE          # ollama-only
    port: int = OLLAMA_DEFAULT_PORT            # ollama-only
    timeout: float = DEFAULT_TIMEOUT
    system_prompt: str = _PEER_SYSTEM_PROMPT
    keep_history: bool = True
    history: list = field(default_factory=list, init=False)
    _impl: Any = field(default=None, init=False, repr=False)
    _executor: concurrent.futures.ThreadPoolExecutor | None = field(
        default=None, init=False, repr=False)
    _pending: list = field(default_factory=list, init=False, repr=False)
    _history_lock: threading.Lock | None = field(
        default=None, init=False, repr=False)
    # diagnostics
    calls: int = field(default=0, init=False)
    last_latency_ms: float = field(default=0.0, init=False)
    last_response: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        from domains.no_llm import assert_llm_allowed
        assert_llm_allowed("LLMPartner construction")   # OZMA_NO_LLM hard switch
        chosen = _detect_backend(self.backend)
        self.backend = chosen
        if chosen == "openrouter":
            api_key = os.environ.get("OPENROUTER_API_KEY") or ""
            model = self.model or OPENROUTER_DEFAULT_MODEL
            self.model = model
            self._impl = _OpenRouterBackend(api_key, model, self.timeout)
        elif chosen == "ollama":
            model = self.model or OLLAMA_DEFAULT_MODEL
            self.model = model
            self._impl = _OllamaBackend(self.host, model, self.port,
                                          self.timeout)
        else:
            raise ValueError(f"unknown LLM backend: {chosen}")
        # single worker preserves history ordering across concurrent calls
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="llm_partner")
        self._history_lock = threading.Lock()

    def is_available(self) -> bool:
        try:
            return self._impl.is_available()
        except Exception:
            return False

    def ask(self, prompt: str) -> str | None:
        """SYNCHRONOUS — use ask_async from the chat loop. Blocks until
        reply or timeout. Returns None on transport failure."""
        from domains.no_llm import assert_llm_allowed
        assert_llm_allowed("LLMPartner.ask")   # OZMA_NO_LLM: loud even on a pre-built instance
        with self._history_lock:
            messages: list = [
                {"role": "system", "content": self.system_prompt}]
            if self.keep_history:
                messages.extend(self.history[-12:])
            messages.append({"role": "user", "content": prompt})
        t0 = time.monotonic()
        content = self._impl.chat(messages)
        if content is None:
            return None
        self.calls += 1
        self.last_latency_ms = (time.monotonic() - t0) * 1000
        self.last_response = content
        if self.keep_history:
            with self._history_lock:
                self.history.append({"role": "user", "content": prompt})
                self.history.append(
                    {"role": "assistant", "content": content})
        return content

    def ask_async(self, prompt: str) -> concurrent.futures.Future:
        """Non-blocking. Returns a Future. The agent doesn't wait."""
        future = self._executor.submit(self.ask, prompt)
        self._pending.append((future, prompt))
        return future

    def drain_completed(self) -> list[tuple[str, str]]:
        """Return [(prompt, reply), …] for completed futures. Pops
        them from pending."""
        completed: list = []
        remaining: list = []
        for future, prompt in self._pending:
            if future.done():
                try:
                    reply = future.result(timeout=0)
                except Exception:
                    reply = None
                if reply:
                    completed.append((prompt, reply))
            else:
                remaining.append((future, prompt))
        self._pending = remaining
        return completed

    def pending_count(self) -> int:
        return len(self._pending)

    def __call__(self, question_text: str) -> Any:
        """Drop-in shape compatible with the teacher chain (synchronous).
        Mostly unused now — chat dispatches via ask_async."""
        reply = self.ask(question_text)
        if reply is None:
            return None
        return {"answer": reply, "learn": []}

    def close(self) -> None:
        if self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None
        if self._impl is not None:
            self._impl.close()


# ---------------------------------------------------------------------------
# install — concepts the agent uses to reason about its partner
# ---------------------------------------------------------------------------

_LLM_PARTNER_MT = "llm_partner"


def install_llm_partner_concepts(agent) -> dict:
    """Install Concepts the agent uses to reason about its conversation
    partner — what it IS (statistical inference, not human) and why
    communicating with humans MATTERS (enables discovery + efficiency)."""
    if _LLM_PARTNER_MT not in agent._microtheory_nodes:
        agent.install_microtheory(
            _LLM_PARTNER_MT,
            description="the agent's understanding of its LLM peer "
                        "and of communication value",
            genl="general_knowledge")
    agent.operates_in(_LLM_PARTNER_MT)

    out: dict = {}

    base_concepts = (
        ("language_model",
         "a system that predicts and generates natural language"),
        ("LLM",
         "a large language model; the agent's primary conversation partner"),
        ("partner",
         "another mind one converses with as a peer"),
        ("peer",
         "an interlocutor of equivalent standing in dialogue"),
        ("ollama",
         "local serving infrastructure that can host LLM partners"),
        ("openrouter",
         "API-router that brokers requests to hosted LLM partners"),
        ("gemini",
         "a family of LLM models from Google; the current partner is "
         "a Gemini Flash variant"),
        # what kind of entity the LLM IS — explicitly NOT a human mind
        ("statistical",
         "based on statistical patterns over observed data"),
        ("inference",
         "drawing output from data; for an LLM, predicting the next "
         "token from prior tokens"),
        ("prediction",
         "computing what comes next from patterns in past data"),
        ("neural_network",
         "a computational model loosely modeled on biological neural "
         "tissue, trained by gradient descent"),
        ("not_human",
         "an entity that is not a human; a different kind of mind"),
        ("human",
         "biological entity capable of conversation, experience, "
         "and grounding concepts in lived reality"),
        # belief / goal-shaping concepts
        ("communication",
         "the act of exchanging meaning between minds"),
        ("discovery",
         "finding out something one didn't know"),
        ("efficiency",
         "achieving a goal with less effort or fewer steps"),
        ("help",
         "support or contribution that advances another's goal"),
    )

    for name, desc in base_concepts:
        existing = agent._concept_nodes.get(name)
        if existing is not None:
            out[name] = existing
            continue
        with agent.mind_substrate.transform() as tx:
            cid = tx.add_node("Concept",
                                {"name": name, "description": desc})
            agent._concept_nodes[name] = cid
        out[name] = cid
        agent.learn_sign({"form": name, "concept": name})

    # The LLM is what it is, as graph data
    _ensure_edge(agent, out["LLM"], "is_a", out["language_model"])
    _ensure_edge(agent, out["LLM"], "is_a", out["not_human"])
    _ensure_edge(agent, out["LLM"], "is_a", out["neural_network"])
    _ensure_edge(agent, out["language_model"], "has_property",
                  out["statistical"])
    _ensure_edge(agent, out["language_model"], "has_property",
                  out["inference"])
    _ensure_edge(agent, out["language_model"], "has_property",
                  out["prediction"])
    _ensure_edge(agent, out["gemini"], "is_a", out["LLM"])

    # Communication-value belief
    belief_id = _ensure_concept(
        agent, "communication_with_humans_enables_discovery",
        description=(
            "the agent's standing belief that talking to humans "
            "produces both discovery and efficiency — humans can "
            "ground concepts the agent lacks, suggest directions, "
            "and shortcut search"))
    out["communication_with_humans_enables_discovery"] = belief_id
    _ensure_edge(agent, belief_id, "enables", out["discovery"])
    _ensure_edge(agent, belief_id, "enables", out["efficiency"])
    _ensure_edge(agent, belief_id, "requires", out["communication"])
    _ensure_edge(agent, belief_id, "requires", out["human"])
    _ensure_edge(agent, agent.agent_root, "believes", belief_id)

    return out


def _ensure_concept(agent, name: str, description: str = ""):
    existing = agent._concept_nodes.get(name)
    if existing is not None:
        return existing
    with agent.mind_substrate.transform() as tx:
        cid = tx.add_node("Concept",
                            {"name": name, "description": description})
        agent._concept_nodes[name] = cid
    agent.learn_sign({"form": name, "concept": name})
    return cid


def _ensure_edge(agent, src_id, edge_type: str, tgt_id) -> None:
    from substrate import NodePattern, Production
    for src_type in ("Concept", "Agent"):
        try:
            agent.mind_substrate.checker.grammar.add(Production(
                src=NodePattern(src_type, "src"),
                edge_type=edge_type,
                tgt=NodePattern("Concept", "tgt"),
                provenance=f"meta:{src_type}-{edge_type}-Concept "
                            "(llm_partner)"))
        except Exception:
            pass
    for e in agent.mind_graph.out_edges(src_id, edge_type):
        if e.key.tgt == tgt_id:
            return
    try:
        with agent.mind_substrate.transform() as tx:
            tx.add_edge(src_id, edge_type, tgt_id)
    except Exception:
        pass


__all__ = ["LLMPartner", "install_llm_partner_concepts",
            "OPENROUTER_DEFAULT_MODEL", "OLLAMA_DEFAULT_MODEL",
            "_PEER_SYSTEM_PROMPT"]
