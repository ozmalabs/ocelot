"""A teacher hook — the agent asks for help WHEN IT NEEDS it, and only then.

The point is the agent decides it's stuck — not me deciding to teach. A genuine NEED
is a confusion it has tried and failed to crack on its OWN: a pair it keeps confusing
(persistent count) for which NO sound feature it has found separates them (best Fisher
below a floor). Self-invention has been exhausted there; a teacher is warranted. When
that's true, the agent formulates a question FROM ITS OWN STATE and asks through this
hook; the reply is recorded as a TaughtHint linked to the pair, for the agent to
ground later (the language-bootstrap path — the teacher's words in the agent's own
grounded vocabulary).

The agent decides WHEN and WHAT to ask. The hook is only the channel. The teacher
backend is pluggable — an LLM partner, a spawned Agent peer, or a human — passed as a
plain `ask(question) -> answer` callable, so nothing about the teacher lives on the
agent. See [[ozma_language_bootstrap]] / [[ozma_meta_abilities_are_leverage]] /
[[ozma_entity_not_program]].
"""
from __future__ import annotations


def needs_teacher(substrate, fisher_floor: float = 0.6,
                  min_count: int = 8) -> list:
    """The confusions the agent cannot resolve by itself: persistent (count >=
    min_count) AND no band it found separates the pair (best Fisher < floor). Read
    from its own state — these are where it has genuinely failed and a teacher helps.
    Returns [(X, Y, count, best_fisher)] worst-first."""
    confs = {}
    for c in substrate.nodes("Confusion"):
        a = substrate.node(c)["attrs"]
        confs[(a.get("true_word"), a.get("pred_word"))] = int(a.get("count", 0))
    best = {}
    for cb in substrate.nodes("ConfusionBand"):
        a = substrate.node(cb)["attrs"]
        am, bm = a.get("a_mean"), a.get("b_mean")
        if am is None or bm is None:
            continue
        f = abs(am - bm) / (float(a.get("a_std", 0.0)) + float(a.get("b_std", 0.0)) + 1e-6)
        k = (a.get("true_word"), a.get("pred_word"))
        best[k] = max(best.get(k, 0.0), f)
    needs = [(X, Y, n, best.get((X, Y), 0.0)) for (X, Y), n in confs.items()
             if n >= min_count and best.get((X, Y), 0.0) < fisher_floor]
    return sorted(needs, key=lambda t: -t[2])


def _question(X, Y, n) -> str:
    """The agent's question, formed from its own confusion — its words, its need."""
    return (f"I keep hearing '{X}' as '{Y}' ({n} times) and no sound difference I can "
            f"find tells them apart. What should I listen for to tell '{X}' from "
            f"'{Y}'?")


def ask_if_needed(substrate, ask, max_asks: int = 1) -> list:
    """If — and only if — the agent has needs, it asks the teacher its own question
    and records each reply as a TaughtHint(for_pair, question, answer, grounded=0) for
    it to ground. `ask(question) -> answer` is the teacher channel (pluggable; nothing
    of the teacher is stored on the agent). Returns [(question, answer)]."""
    needs = needs_teacher(substrate)
    if not needs:
        return []
    out = []
    for X, Y, n, f in needs[:max_asks]:
        q = _question(X, Y, n)
        try:
            a = ask(q)
        except Exception:
            a = None
        if a:
            substrate.add_node("TaughtHint", {
                "for_pair": f"{X}/{Y}", "question": q, "answer": str(a),
                "origin": "teacher_hook", "grounded": 0})
            out.append((q, a))
    return out


__all__ = ["needs_teacher", "ask_if_needed"]
