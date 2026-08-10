"""CLAUDE-SESSION TEACHER — the pluggable ask(question)->answer backend for teacher_hook.

The agent decides WHEN and WHAT to ask (domains/teacher_hook.py: it asks only about a confusion
it has tried and failed to crack on its own). This module is ONLY the channel: it wraps a Claude
session as the teacher by shelling `claude -p <question>` (non-interactive; uses the logged-in
session, no API key). Boundary I/O per CLAUDE.md — no agent logic lives here.

    from scripts.claude_teacher import make_ask
    teacher_hook.ask_if_needed(substrate, ask=make_ask())
"""
from __future__ import annotations
import shutil
import subprocess

_PREAMBLE = (
    "You are a patient speech-science tutor for a learning agent that hears sound but has no "
    "language yet. Answer in 2-3 plain sentences, concrete and grounded in what distinguishes "
    "the sounds (formants, timing, place/manner). No preamble.\n\nQuestion: ")


def make_ask(model: str | None = None, timeout: float = 180.0, preamble: str = _PREAMBLE):
    """Return ask(question)->answer wrapping `claude -p`. Returns "" on failure/timeout so the
    teacher_hook records 'no help' rather than crashing the autonomous loop."""
    exe = shutil.which("claude")

    def ask(question: str) -> str:
        # OZMA_NO_LLM hard switch — any attempt to shell `claude -p` under the
        # switch must be LOUD, never a silent "" (which would read as 'no help').
        from domains.no_llm import assert_llm_allowed
        assert_llm_allowed("scripts.claude_teacher.make_ask (`claude -p` shell-out)")
        if not exe or not question:
            return ""
        cmd = [exe, "-p", preamble + question]
        if model:
            cmd[1:1] = ["--model", model]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except (subprocess.TimeoutExpired, OSError):
            return ""
        return (out.stdout or "").strip() if out.returncode == 0 else ""

    return ask


if __name__ == "__main__":
    ask = make_ask()
    print("teacher reply:", repr(ask("In one sentence, what most distinguishes /b/ from /p/?")))
