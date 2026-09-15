"""LLM harness for the capability suite — OFF BY DEFAULT, TEACHER-FREE.

This harness lets a user OPTIONALLY put an LLM on the SAME battery the substrate and
human runners use, so its Spearman rho / AMI can be placed next to the substrate's on
the unified scorecard. It does two things and NOTHING else by default:

  1. emit_prompt_bundle(...) — writes a self-contained prompt file (the category items
     + the exact typicality question) that a user can paste into ANY model, offline.
  2. read_results(path)      — reads a results JSON the user pastes back (per-item
     ordering) so the scorer can consume it.

IT NEVER CALLS A NETWORK OR A MODEL ON ITS OWN. There is no API client here, no
requests import, no key handling. The substrate's minting loop is never fed an LLM at
run time — the whole point of the arc is that the loop is teacher-free. Any actual
model call is a manual, user-initiated step OUTSIDE this file (the user runs their own
model on the emitted prompt and pastes the answer back). A `call_fn` hook exists ONLY
so a user who wants to automate their own local model can inject it explicitly; it is
never populated by this module and defaults to None (raising if invoked without being
supplied).

Published LLM reference numbers (arXiv:2505.17117) are already in
scoring/metrics.LLM_REFERENCE for side-by-side reporting without running anything.
"""
from __future__ import annotations

import json
import os
from typing import Any, Callable, Optional


PROMPT_TEMPLATE = """\
TASK: rank the members of a category by how TYPICAL each is as an example of the
category (1 = most typical / best example). This mirrors the Rosch (1975)
goodness-of-example task and the RQ2 typicality metric of arXiv:2505.17117.

Category: {category}
Members (in arbitrary order): {members}

Respond with a JSON object mapping each member to an integer rank starting at 1
(1 = most typical), e.g. {{"robin": 1, "sparrow": 2, ...}}. Rank ALL members; no ties.
Do not explain; output only the JSON object.
"""


def emit_prompt_bundle(fixture: dict, out_path: str) -> str:
    """Write a prompt file (one prompt per category) a user can run against ANY model
    offline. Returns the path written. Emits data only — no model is contacted."""
    lines = []
    for cat, items in fixture["categories"].items():
        members = ", ".join(sorted(it["item"] for it in items))
        lines.append("=" * 70)
        lines.append("CATEGORY: %s" % cat)
        lines.append("-" * 70)
        lines.append(PROMPT_TEMPLATE.format(category=cat, members=members))
        lines.append("")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))
    return out_path


def read_results(path: str) -> dict:
    """Read a pasted-back results JSON of the form
    {category: {item: rank_int, ...}, ...} that a user produced by running their own
    model on the emitted prompt bundle. Returns it as-is for the scorer. Pure file I/O
    — no model contacted."""
    with open(path) as fh:
        return json.load(fh)


def run(fixture: dict, *, enable: bool = False,
        call_fn: Optional[Callable[[str], Any]] = None) -> dict:
    """The guarded entry point. With `enable=False` (the DEFAULT) this does NOT run any
    model — it returns a directive telling the caller to emit a prompt bundle and paste
    results back, plus the published LLM reference numbers for the scorecard. With
    `enable=True` the caller MUST supply their own `call_fn(prompt)->response` (their
    own local model); this module never provides one. Teacher-free by construction: the
    substrate loop is never fed an LLM; this is a SEPARATE, opt-in, user-driven
    comparison arm."""
    if not enable:
        return {"enabled": False,
                "note": ("LLM arm is OFF by default (teacher-free). To add an LLM "
                         "column: emit_prompt_bundle() -> run your own model offline "
                         "-> read_results(). Published reference numbers are in "
                         "scoring/metrics.LLM_REFERENCE."),
                "reference": None}
    if call_fn is None:
        raise RuntimeError(
            "LLM arm enabled but no call_fn supplied. This harness never contacts a "
            "model itself; inject your own local model as call_fn(prompt)->response.")
    results = {}
    for cat, items in fixture["categories"].items():
        members = ", ".join(sorted(it["item"] for it in items))
        prompt = PROMPT_TEMPLATE.format(category=cat, members=members)
        results[cat] = call_fn(prompt)          # user's own model; explicit + local
    return {"enabled": True, "results": results}
