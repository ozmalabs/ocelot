"""The English vocabulary base (seeds/vocabulary_base_en.json): mechanical
lookup over VocabEntry{form, pos, klass, share, rank, expands} nodes.

The graph is the source: entries are read from the agent's own VocabEntry
nodes (so a taught entry counts), indexed once per graph and node count. A
caller with no graph -- or a graph that does not hold the seed -- reads the
same seed file, so a bare parse is typed by the same vocabulary.
OZMA_VOCABULARY_BASE=0 disables the lookup (measurement arms only).
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

SEED = Path(__file__).resolve().parents[1] / "seeds/vocabulary_base_en.json"
CLOSED_POS = frozenset({"determiner", "pronoun", "preposition", "conjunction", "auxiliary", "modal", "particle",
                        "qualifier", "interjection", "contraction", "negation", "adverb"})
_GRAPH_INDEX: dict = {}


def norm(form: str) -> str:
    return str(form or "").lower().replace("\u2019", "'").replace("\u2018", "'").strip(".,;:!?\"()")


@lru_cache(maxsize=1)
def _file_index() -> dict:
    try:
        d = json.loads(SEED.read_text())
    except Exception:  # noqa: BLE001 -- no seed file: no vocabulary
        return {}
    return {n["attrs"]["form"]: dict(n["attrs"]) for n in d.get("nodes") or [] if n.get("type") == "VocabEntry"}


def _graph_index(substrate) -> Optional[dict]:
    graph = getattr(substrate, "s", substrate)
    try:
        nodes = graph.nodes("VocabEntry")
    except Exception:  # noqa: BLE001
        return None
    if not nodes:
        return None
    key = (id(graph), len(nodes))
    idx = _GRAPH_INDEX.get(key)
    if idx is None:
        idx = {}
        for n in nodes:
            at = graph.node(n)["attrs"]
            if at.get("form"):
                idx[str(at["form"])] = dict(at)
        _GRAPH_INDEX.clear()
        _GRAPH_INDEX[key] = idx
    return idx


def index(substrate=None) -> dict:
    if os.environ.get("OZMA_VOCABULARY_BASE") == "0":
        return {}
    idx = _graph_index(substrate) if substrate is not None else None
    return idx if idx is not None else _file_index()


def lookup(form: str, substrate=None) -> Optional[dict]:
    return index(substrate).get(norm(form))


def is_function_word(entry: Optional[dict]) -> bool:
    """A closed-class entry, or a mixed one whose dominant reading is closed."""
    if not entry:
        return False
    return entry.get("klass") == "closed" or (entry.get("klass") == "mixed" and entry.get("pos") in CLOSED_POS)


@lru_cache(maxsize=8)
def function_words(klasses=("closed",)) -> frozenset:
    """The function-word forms of the seed file (for the reply-quality criterion)."""
    return frozenset(f for f, e in _file_index().items() if e.get("klass") in klasses)
