#!/usr/bin/env python
"""build_exemplar_store — Arc 3 R1: the EXEMPLAR STORE build.

`PROGRAM_SYNTHESIS_ARC3_PLAN.md` (R1), `PROGRAM_SYNTHESIS_ARC3_PREREG.md` /
`PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md` (the 90/120 = 75.0% train-emittable pool
this script reproduces BYTE-IDENTICALLY — same `resolve_entry` +
`emit_prog_ir` calls, same pool composition), `scripts/retrieval_oracle_
ceiling.py` (`build_pool`, reused verbatim for pool composition),
`domains/mbpp_spec.py` (`request_facts`/`signature_facts` — the retrieval
scoring inputs), `domains/prog_ir_emit.py` (`emit_prog_ir`).

THE JOB. Every MBPP train-split (task_id >= 601) program that
`emit_prog_ir` accepts whole becomes ONE graph-resident `Exemplar` node,
carrying:

  - `ir_json`      the WHOLE program's Term-JSON string (never abstracted
                    into a codebook shape — arc 3's entire premise).
  - `params`/`arity` the emitted function's own parameter list.
  - `prompt_tokens`  the train task's OWN prompt, tokenised via
                     `mbpp_spec.request_facts` (`request_body`, tokenised on
                     the same `[a-z']+` pattern `mbpp_blocker_histogram`
                     already uses) -- never the reference `code`.
  - `tfidf`          a token -> weight dict, computed as CORPUS TF-IDF over
                     the 90-exemplar pool's own prompt tokens (mechanical
                     arithmetic: idf = ln(N / df), tf = raw count in this
                     exemplar's own prompt) -- a fixed formula, no decision.
  - `arg_types`/`return_type` -- `mbpp_spec.signature_facts` on the train
                     task's OWN `test_list` rows (never prose, never `code`).
  - `task_id`/`provenance:"train"` -- per-exemplar provenance
                     (`tests/fixtures/mbpp/provenance.json`'s contamination
                     rule: train content is the legal, intended source for
                     this store; a downstream contamination gate asserts
                     every Exemplar's provenance is "train" and every
                     task_id is in the train range).

This script performs NO agent decisions -- it is a MEASUREMENT-class /
seed-authoring script (the `tools/capture_seed.py` precedent: "one-off
authoring scripts that emit seed manifests" are explicitly sanctioned
Python under CLAUDE.md). Ranking/selection at RUN time is a graph RULE
(`seeds/program_synthesis.json`'s `pr_select_candidate` — Argmax over
recorded score facts); this script only builds the STATIC store the
retrieval rules score against.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
  OZMA_SEED_PERSIST_DISABLED=1 python scripts/build_exemplar_store.py
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import time
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from domains import mbpp_spec as ms  # noqa: E402

from retrieval_oracle_ceiling import build_pool  # noqa: E402 — byte-identical pool
from mbpp_zero_shot_baseline import split_tasks as q0_split_tasks  # noqa: E402

FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
OUT_PATH = os.path.join(ROOT, "seeds", "mbpp_exemplars.json")
SEED_ID = "mbpp_exemplars"
SEED_VERSION = "1.0.0"

_WORD_RE = re.compile(r"[a-z']+")
_STOPWORDS = frozenset({
    "a", "an", "the", "to", "of", "in", "is", "that", "which", "and", "or",
    "for", "from", "with", "as", "this", "on", "if", "given", "return",
    "returns", "write", "function", "python",
})


def _prompt_tokens(prompt: str) -> List[str]:
    """Mechanical tokenisation of the (train) prompt's REQUEST BODY (the
    residual after `mbpp_spec.request_facts` strips the verb-frame prefix
    — "write a python function to" etc. never itself a content token) —
    lower-cased word tokens, stopwords removed, the `mbpp_blocker_
    histogram` `[a-z']+` pattern. `agent=None` -> the module's closed
    fallback cue vocabulary (no live agent at build time, matching every
    other offline measurement script in this arc)."""
    facts = ms.request_facts(prompt, agent=None)
    toks = _WORD_RE.findall(facts["request_body"].lower())
    return [t for t in toks if t not in _STOPWORDS and len(t) > 1]


def _tfidf(token_lists: List[List[str]]) -> List[Dict[str, float]]:
    """Corpus TF-IDF over the pool's own prompt tokens (fixed formula, no
    decision): idf(t) = ln(N / df(t)) (natural log, +1 floor so a token
    present in every document never scores exactly zero — the standard
    smoothed-idf reading); tf(t, doc) = raw count of t in that doc's own
    token list. Returns one {token: weight} dict per input list, same
    order."""
    n = len(token_lists)
    df: Dict[str, int] = {}
    for toks in token_lists:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log(n / c) + 1.0 for t, c in df.items()}
    out: List[Dict[str, float]] = []
    for toks in token_lists:
        tf: Dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        out.append({t: round(c * idf[t], 6) for t, c in tf.items()})
    return out


def build_exemplars(train_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pool, emit_rows = build_pool(train_tasks)
    by_id = {t["task_id"]: t for t in train_tasks}
    token_lists = []
    for ex in pool:
        task = by_id[ex["task_id"]]
        token_lists.append(_prompt_tokens(task["prompt"]))
    tfidf_rows = _tfidf(token_lists)

    exemplars: List[Dict[str, Any]] = []
    for ex, toks, tfidf in zip(pool, token_lists, tfidf_rows):
        task = by_id[ex["task_id"]]
        sig = ms.signature_facts(task)
        exemplars.append({
            "task_id": ex["task_id"],
            "entry": ex["entry"],
            "arity": ex["arity"],
            "params": ex["params"],
            "predictable": bool(ex["predictable"]),
            "ir_json": json.dumps(ex["ir"], sort_keys=True),
            "prompt_tokens": sorted(set(toks)),
            "tfidf": tfidf,
            "arg_types": sig.get("arg_types"),
            "return_type": sig.get("return_type"),
            "consistent_types": bool(sig.get("consistent_types")),
            "provenance": "train",
        })
    return exemplars, emit_rows


def to_manifest(exemplars: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes = []
    for i, ex in enumerate(exemplars, start=1):
        attrs = dict(ex)
        attrs["kind"] = "mbpp_exemplar"
        nodes.append({"local_id": i, "type": "Exemplar", "attrs": attrs})
    return {
        "id": SEED_ID,
        "version": SEED_VERSION,
        "depends_on": [],
        "capability_keys": ["mbpp_exemplar_store"],
        "description": (
            "Arc 3 R1: the ~90 emittable MBPP train-split programs, kept "
            "WHOLE (never abstracted into a codebook shape), as graph-"
            "resident Exemplar nodes carrying their own Term-JSON IR, "
            "paired prompt-token TF-IDF weights, and signature facts -- "
            "the retrieval store `seeds/program_synthesis.json`'s "
            "pr_select_candidate/pr_screen_* rules score and adapt "
            "against. Built by scripts/build_exemplar_store.py; train-"
            "content-only (contamination-legal, tests/fixtures/mbpp/"
            "provenance.json)."),
        "microtheory": {
            "name": "mbpp_exemplars",
            "description": ("a bank of whole, executable, worked programs "
                            "the agent can retrieve, adapt (as-is / "
                            "permuted / one-leaf-edited / re-opened-hole), "
                            "and verify by execution -- case-based "
                            "reasoning at program grain."),
        },
        "nodes": nodes,
        "edges": [],
        "productions": [],
        "rules": [],
    }


def main() -> None:
    t0 = time.time()
    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    splits = q0_split_tasks(all_tasks)
    train_tasks = splits["train"]
    assert len(train_tasks) == 120

    exemplars, emit_rows = build_exemplars(train_tasks)
    manifest = to_manifest(exemplars)

    # determinism: build twice, compare the serialised node list byte-for-byte.
    exemplars2, _ = build_exemplars(train_tasks)
    manifest2 = to_manifest(exemplars2)
    identical = json.dumps(manifest["nodes"], sort_keys=True) == \
        json.dumps(manifest2["nodes"], sort_keys=True)

    with open(OUT_PATH, "w") as f:
        json.dump(manifest, f, indent=1, sort_keys=False)
        f.write("\n")

    n_train = len(train_tasks)
    n_pool = len(exemplars)
    print("train tasks:", n_train, "emitted exemplars:", n_pool,
          "emit_rate: %.4f" % (n_pool / n_train))
    print("twin-build identical:", identical)
    print("wrote", OUT_PATH)
    print("elapsed: %.2fs" % (time.time() - t0))
    if not identical:
        raise SystemExit("build_exemplar_store: non-deterministic build!")


if __name__ == "__main__":
    main()
