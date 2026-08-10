"""code_growth_run — CODE-4's live growth transcript, sanctioned surfaces only.

Runs the end-to-end loop the gate (tests/test_code_growth_migrated.py) asserts,
printed as a chat transcript (OZMA_NO_LLM honoured; seed persistence disabled so
a demo run never mutates the real boot seeds):

  (a) TEACH-BY-EXAMPLE (the deepest close — reading closes the write gap):
      OOV request -> honest abstain + SelfConcern{kind:'code_write'} filed by
      the note_code_write_gap rule -> the human pastes a real example function
      in chat -> the agent READS it (code_reading, CODE-1/2), validates the
      read Term by running, TEACHES it as a new write shape (teach(), the cue
      adoption precedent) -> the ORIGINAL request now succeeds -> the
      resolve_code_write_gap rule marks the gap resolved in the agent's own
      rule pass.

  (b) COMPOSE-FROM-PREDICATION (the narrow example-free close): another OOV
      request ("triples") -> gap -> NL-promote ("Work on the triples gap.")
      -> the held morphological vocabulary (seeds/write_shape_predication.json)
      resolves the predicate and composes Times(Var,3) from held Terms ->
      validate-by-running -> taught -> request succeeds; outside the family
      the trail exhausts honestly, naming teach-by-example as the close.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
     python3 scripts/code_growth_run.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds             # noqa: E402
from domains import code_write_growth as cwg              # noqa: E402


def _say(who: str, text: str) -> None:
    pad = "\n           ".join(str(text).splitlines())
    print(f"  {who:>8}: {pad}")


def main() -> int:
    print("== boot (full seed set) ==")
    a = WorldAdapter(seeds=())
    load_all_seeds(a)

    print("\n== (a) TEACH-BY-EXAMPLE ==")
    req = "Write a function that doubles a number."
    _say("human", req)
    _say("agent", a.converse(req))
    gaps = cwg.pending_code_write_gaps(a)
    print("  [graph] code_write gaps:", [(g["content"], g["status"]) for g in gaps])

    example = "def double(n):\n    return n * 2\n"
    _say("human", example.rstrip())
    _say("agent", a.converse(example))

    _say("human", req)
    _say("agent", a.converse(req))
    a.comprehend()
    gaps = [(g["content"], g["status"]) for g in cwg.pending_code_write_gaps(a)]
    print("  [graph] code_write gaps after rule pass:", gaps)

    print("\n== (b) COMPOSE-FROM-PREDICATION ==")
    req2 = "Write a function that triples a number."
    _say("human", req2)
    _say("agent", a.converse(req2))
    _say("human", "Work on the triples gap.")
    res = cwg.work_on_code_write_gap(a, "Work on the triples gap.")
    _say("agent", ("I composed the shape %r from what I hold (validated by "
                   "running)." % res["shape"]) if res.get("ok")
                  else res.get("reason", "?"))
    a.comprehend()
    _say("human", req2)
    _say("agent", a.converse(req2))

    print("\n== (b') THE HONEST BOUNDARY ==")
    req3 = "Write a function that reverses a string."
    _say("human", req3)
    _say("agent", a.converse(req3))
    _say("human", "Work on the reverses gap.")
    res3 = cwg.work_on_code_write_gap(a, "Work on the reverses gap.")
    _say("agent", res3.get("reason", "?"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
