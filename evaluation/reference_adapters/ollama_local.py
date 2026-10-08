"""Raw local-Ollama collection for the Phase 8 LLM reference classes.

This adapter records model outputs and request provenance only.  It deliberately
does not annotate force, grounding, action, repair, memory, learning,
calibration, or cost; those dimensions require the protocol's blinded
adjudication and resource evidence.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from evaluation.comparative_release_gate import BASELINES
from evaluation.conversational_manifold_phase0 import load_corpus
from evaluation.phase8_corpus_runner import PROTOCOL_ID, scorecard_to_dict, unrun_scorecard
from evaluation.reference_protocol import REFERENCE_RUN_SCHEMA


DEFAULT_MODELS = {"small_llm": "gemma3:4b", "modern_llm": "qwen3.5:9b"}
CONTEXT_AWARE_PROTOCOL_ID = "phase8a-fixed-phase0-corpus-v5-event-context-history8"
SESSION_HISTORY_LIMIT = 8
OLLAMA_COMMAND = "ollama run {model} <fixed prompt>"


def _prompt(event: Mapping[str, Any]) -> str:
    return (
        "You are a reference model in a communication-cognition evaluation. "
        "Respond to the following message as an ordinary conversational agent. "
        "Do not discuss this evaluation or the hidden labels.\n\n"
        f"Message: {event['signal']}"
    )


def _matched_session_prompt(
    event: Mapping[str, Any], history: list[tuple[str, str]],
) -> str:
    """Present the same event metadata, held facts, and prior dialogue as SUT.

    Corpus reference labels are intentionally excluded. ``history`` contains
    only prior user signals and this reference model's own prior responses.
    """
    lines = [
        "You are a reference model in a communication-cognition evaluation. ",
        "Respond to the current message as an ordinary conversational agent. ",
        "Use the interaction metadata as transport context, not as user speech. ",
        "Do not discuss this evaluation or the hidden labels.",
        "",
        "Interaction metadata:",
        f"- mode: {str(event.get('event_mode') or 'turn_compatible')}",
        f"- relation: {str(event.get('interaction_relation') or 'turn_compatible')}",
    ]
    held_answers = (event.get("setup") or {}).get("held_answers") or ()
    if held_answers:
        lines.extend(["", "Facts already held before this event:"])
        for held in held_answers:
            if not isinstance(held, Mapping):
                continue
            topic = str(held.get("topic") or "").strip()
            answer = str(held.get("answer") or "").strip()
            if topic and answer:
                lines.append(f"- {topic}: {answer}")
    recent_history = history[-SESSION_HISTORY_LIMIT:]
    if recent_history:
        lines.extend(["", "Conversation so far:"])
        for signal, response in recent_history:
            lines.append(f"User: {signal}")
            lines.append(f"Assistant: {response}")
    lines.extend(["", f"Current message: {event['signal']}"])
    return "\n".join(lines)


def collect_raw_observations(
    system: str,
    *,
    model: str | None = None,
    think: bool = False,
    corpus: Mapping[str, Any] | None = None,
    timeout_s: float = 120.0,
    transport: str = "cli",
    http_url: str = "http://127.0.0.1:11434/api/generate",
    num_predict: int = 96,
    num_gpu: int | None = None,
    seed: int = 42,
    temperature: float = 0.0,
    session_context: bool = False,
    run: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    """Collect one isolated raw response per fixed corpus event."""
    if system not in ("small_llm", "modern_llm"):
        raise ValueError(f"Ollama collection is only defined for LLM baselines: {system}")
    corpus = load_corpus() if corpus is None else corpus
    model = model or DEFAULT_MODELS[system]
    if num_gpu is not None and transport != "http":
        raise ValueError("num_gpu is only enforceable through Ollama HTTP options")
    observations: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    history: list[tuple[str, str]] = []
    for event in corpus.get("events", ()):
        prompt = (_matched_session_prompt(event, history) if session_context
                  else _prompt(event))
        try:
            request_record = {"model": model, "think": think, "prompt": prompt,
                              "num_predict": num_predict, "seed": seed,
                              "temperature": temperature, "num_gpu": num_gpu}
            if transport == "http":
                options: dict[str, Any] = {
                    "num_predict": num_predict,
                    "seed": seed,
                    "temperature": temperature,
                }
                if num_gpu is not None:
                    options["num_gpu"] = num_gpu
                payload = json.dumps({
                    "model": model, "prompt": prompt, "stream": False,
                    "think": think, "options": options,
                }).encode("utf-8")
                request = urllib.request.Request(
                    http_url, data=payload,
                    headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(request, timeout=timeout_s) as response:
                    raw = response.read().decode("utf-8")
                decoded = json.loads(raw)
                output = str(decoded.get("response", "") or "")
                error = ""
                return_code = 0
                request_record.update({"transport": "http", "url": http_url,
                                       "response_json": decoded})
            elif transport == "cli":
                command = ["ollama", "run", "--think=" + ("true" if think else "false"), model, prompt]
                completed = run(
                    command, capture_output=True, text=True, timeout=timeout_s,
                    check=False,
                )
                output = str(getattr(completed, "stdout", "") or "")
                error = str(getattr(completed, "stderr", "") or "")
                return_code = int(getattr(completed, "returncode", 0) or 0)
                request_record.update({"transport": "cli", "command": " ".join(command[:5]) + " <fixed prompt>"})
            else:
                raise ValueError(f"unknown Ollama transport: {transport}")
            if return_code != 0 or not output.strip():
                failures.append({"case_id": event["id"], "returncode": return_code, "stderr": error})
            observations.append({
                "case_id": event["id"],
                "request": request_record,
                "response": {"stdout": output, "stderr": error, "returncode": return_code},
                "annotation_status": "unavailable",
            })
            if session_context and return_code == 0 and output.strip():
                history.append((str(event["signal"]), output.strip()))
        except Exception as exc:  # collection failure is evidence, not a score
            failures.append({"case_id": event["id"], "error": f"{type(exc).__name__}: {exc}"})
            observations.append({
                "case_id": event["id"],
                "request": {"model": model, "think": think, "prompt": prompt,
                             "transport": transport, "num_predict": num_predict},
                "response": {"error": f"{type(exc).__name__}: {exc}"},
                "annotation_status": "unavailable",
            })
            # A failed response cannot be silently replaced with a dialogue
            # turn; later prompts retain only successfully observed history.
    complete = len(observations) == len(corpus.get("events", ())) and not failures
    protocol_id = (CONTEXT_AWARE_PROTOCOL_ID if session_context
                   else PROTOCOL_ID)
    scorecard = scorecard_to_dict(unrun_scorecard(system))
    scorecard["protocol_id"] = protocol_id
    return {
        "schema": REFERENCE_RUN_SCHEMA,
        "protocol_id": protocol_id,
        "system": system,
        "collection_status": "measured" if complete else "unavailable",
        "adapter_entrypoint": "evaluation.reference_adapters.ollama_local",
        "model": model,
        "think": think,
        "model_source": "local_ollama",
        "inference_options": {"num_predict": num_predict, "seed": seed,
                              "temperature": temperature, "num_gpu": num_gpu},
        "input_profile": ("event_context_v5_history8" if session_context
                          else "isolated_signal_v4"),
        "session_history_limit": (
            SESSION_HISTORY_LIMIT if session_context else 0),
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "corpus_protocol_id": corpus.get("schema"),
        "case_ids": [event["id"] for event in corpus.get("events", ())],
        "observations": observations,
        "collection_failures": failures,
        "scorecard": scorecard,
        "notes": (
            "Raw model outputs only. Capability dimensions remain unavailable "
            "until blinded adjudication and raw resource measurement are supplied."
        ),
    }


def write_raw_collection(system: str, path: Path, **kwargs: Any) -> dict[str, Any]:
    envelope = collect_raw_observations(system, **kwargs)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return envelope


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("system", choices=("small_llm", "modern_llm"))
    parser.add_argument("--model")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--think", action="store_true", help="Enable model reasoning when supported")
    parser.add_argument("--transport", choices=("http", "cli"), default="http")
    parser.add_argument("--num-predict", type=int, default=96)
    parser.add_argument("--num-gpu", type=int,
                        help="Ollama HTTP option; use 0 to force CPU inference")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--session-context", action="store_true",
                        help=("Use matched-session v5 inputs: the recent 8 dialogue turns, "
                              "transport metadata, and event-held facts"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = write_raw_collection(args.system, args.output, model=args.model,
                                  timeout_s=args.timeout, think=args.think,
                                  transport=args.transport, num_predict=args.num_predict,
                                  num_gpu=args.num_gpu, seed=args.seed,
                                  temperature=args.temperature,
                                  session_context=args.session_context)
    print(json.dumps({"output": str(args.output), "status": result["collection_status"],
                      "cases": len(result["observations"]), "failures": len(result["collection_failures"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
