"""is_question — the chat world-adapter's I/O-boundary classifier.

A thin heuristic that decides whether a line is a question/imperative (route it
through the answer_within / capability-dispatch pipeline) or a statement. Pure
text classification, no agent state — exactly the kind of opaque-form -> graph-
token split a world adapter is allowed to do. Lifted out of the old
scripts/chat.py driver (retired with the CuriousAgent hull) so it survives
independently of it.
"""
from __future__ import annotations

_QUESTION_LEADS = {
    "what", "who", "where", "when", "why", "how", "which",
    "is", "are", "was", "were", "do", "does", "did",
    "can", "could", "will", "would", "should", "may", "might",
    "tell",
}


def is_question(line: str) -> bool:
    """Heuristic split. Endswith '?' is the strongest signal; otherwise look at
    the first token. Imperatives like 'run echo' and 'read hello' are
    intentionally classified as questions — they route through the
    capability-dispatch pipeline."""
    s = line.strip()
    if s.endswith("?"):
        return True
    first = s.lower().split(None, 1)[0] if s else ""
    if first in _QUESTION_LEADS:
        return True
    if first in {"read", "write", "run", "execute", "open", "show"}:
        return True
    return False
