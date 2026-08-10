"""Bake the LLVM vocabulary as a JSON seed.

`llvm_teacher.LLVMTeacher` is a runtime callable — the agent's
impasse-resolver invokes it on misses. For an agent that boots already
knowing LLVM concepts, we'd prefer NOT to wait for a question to arrive
before learning. This module front-loads the work:

  bake_vocab() iterates `llvm_teacher._ENTRIES` and produces a manifest
  dict matching the seed-shape this project uses elsewhere
  (`id`, `version`, `depends_on`, `description`, `lessons`).

  install_vocab_seed(agent, path) reads the manifest from disk and
  replays each lesson through `agent.learn_from_teacher`. The agent
  ends up with one Frame per concept — exactly the same Frames the
  teacher would have built lazily, just installed at boot.

Aliases (gep → getelementptr, i32 → integer type) are deliberately
NOT baked. They remain a runtime teacher concern: an alias is a
look-up redirect, not a separate concept. If the agent encounters an
alias phrase, the teacher chain returns the canonical's payload and
the agent learns the alias as its own Frame at that moment. Baking
all 149 reachable phrases would create alias Frames that point at
the canonical's content — harmless but redundant; canonicals alone
are the foundational vocabulary.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import llvm_teacher


# ---------------------------------------------------------------------------
# bake
# ---------------------------------------------------------------------------

def bake_vocab(
    version: str = "0.1.0",
    description: str = (
        "LLVM IR vocabulary as graph data. Each lesson is a "
        "`learn_from_teacher`-shaped payload; the loader replays them "
        "into the agent at boot so the standard Frame layer answers "
        "LLVM-concept questions without a teacher round-trip."
    ),
) -> dict[str, Any]:
    """Generate a vocabulary-seed manifest dict.

    For each canonical entry in `llvm_teacher._ENTRIES`, calls
    `entry_to_payload` to produce the standard teaching payload, then
    bundles them under a `lessons` array.
    """
    lessons = []
    for entry in llvm_teacher._ENTRIES:
        payload = llvm_teacher.entry_to_payload(entry, subject=entry.phrase)
        lessons.append({
            "phrase": entry.phrase,
            "payload": payload,
        })
    return {
        "id": "llvm_ir_vocabulary",
        "version": version,
        "depends_on": [],
        "description": description,
        "source": "llvm_langref",
        "entries_count": len(lessons),
        "lessons": lessons,
    }


def write_vocab_seed(path: str | Path, manifest: dict | None = None) -> Path:
    """Write the baked vocabulary to `path`. Default `manifest` calls
    `bake_vocab()`. Returns the absolute Path written."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    m = manifest if manifest is not None else bake_vocab()
    p.write_text(json.dumps(m, indent=2, sort_keys=False) + "\n")
    return p.resolve()


# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------

def load_vocab_seed(path: str | Path) -> dict:
    """Read a vocabulary-seed manifest from disk. Returns the dict."""
    p = Path(path)
    with p.open("r") as f:
        manifest = json.load(f)
    if "lessons" not in manifest:
        raise ValueError(
            f"{p}: missing 'lessons' key — not a vocab-seed manifest"
        )
    return manifest


def install_vocab_seed(agent, path: str | Path) -> int:
    """Read the vocabulary seed at `path` and replay every lesson into
    the agent via `agent.learn_from_teacher`. Returns the count of
    lessons installed.

    `agent` is any object with a `learn_from_teacher(question, payload)`
    method — `CuriousAgent` is the typical target.
    """
    manifest = load_vocab_seed(path)
    n = 0
    for lesson in manifest["lessons"]:
        # The first call's question_text shape is what the runtime
        # teacher receives — "what is <phrase>" is one canonical form.
        # The agent's `learn_from_teacher` doesn't care about the exact
        # text; it reads the payload's `learn` entries directly.
        question = f"what is {lesson['phrase']}"
        agent.learn_from_teacher(question, lesson["payload"])
        n += 1
    return n


__all__ = [
    "bake_vocab",
    "write_vocab_seed",
    "load_vocab_seed",
    "install_vocab_seed",
]
