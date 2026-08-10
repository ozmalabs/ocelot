#!/usr/bin/env python3
"""jabberwock_research_agenda — SELF-IMPROVEMENT #5: the agent runs the session's
META-PROCESS on ITSELF, autonomously, on a small scale.

The driver (domains/research_agenda.py) chains the four held self-improvement
faculties into one cycle:

    PERCEIVE (#1 self_capability_collapse)  a queue of CapabilityGaps
      -> PRIORITIZE  by a residual salience (over graph state)
      -> per gap:  ROUTE by KIND (a GRAPH dispatch: route_pick over GapRouteCue)
                   -> FILL  (#3 gap_driven_acquisition / #4 substrate_extension)
                   -> VERIFY (#2 self_verification: a discriminative control)
                   -> ACCEPT (close) / REJECT (leave open, honestly)
      -> LOOP to the next
      -> STOP  when the queue drains (a clean resting point)

This script mints a small battery of gaps -- some KNOWLEDGE-kind (a thin/ungrounded
dimension with a reference to read), some CAPABILITY-kind (a behavioral need that
composes), plus a FAKE gap (no readable source) -- and drives the cycle, printing
the run: gaps perceived -> per-gap [kind -> filler -> verify verdict -> closed/open]
-> the final state. donkey=0: no LLM; extraction is arithmetic over a fed source,
the route is a Rust Program, the accept is #2's Rust verdict rule.

HONEST SCOPE: this drives the gaps #1 can PERCEIVE and #3/#4 can FILL. It is not an
open-ended researcher; it closes the loop end-to-end on a small scale.

    PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_research_agenda.py
"""
from __future__ import annotations

import os
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "runners", "dsl", "python"), os.path.join(_ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import concept_graph as cg
from domains import research_agenda as ra

# A real reference document — the extractor reads it, never invents (donkey=0).
CRYPTO_DOC = (
    "In cryptography, the main primitives are: cipher, key, plaintext, ciphertext, hash function, "
    "digital signature, key exchange, and message authentication code. Other concepts include: nonce, "
    "salt, initialization vector, and block cipher. A cipher transforms plaintext into ciphertext.")


def _mint_battery(a):
    """A small battery of gaps the agent will run its meta-process over."""
    # KNOWLEDGE gap: a thin/ungrounded dimension with a reference to read -> acquire.
    a.s.add_node("CapabilityGap", {
        "faculty": "cryptography_knowledge", "topic": "cryptography",
        "source_text": CRYPTO_DOC,
        "observation": [["capability_gap", "self", "cryptography"]], "status": "perceived"})
    # CAPABILITY gap: a behavioral need solvable by composition -> substrate_extension.
    a.s.add_node("CapabilityGap", {
        "faculty": "input_handling",
        "observation": [["classify the item", "self", "input"],
                        ["route to a handler", "input", "handler"],
                        ["mark handled", "handler", "done"]], "status": "perceived"})
    # FAKE knowledge gap: no readable source -> acquisition cannot fill -> #2 rejects.
    a.s.add_node("CapabilityGap", {
        "faculty": "zzq_knowledge", "topic": "zzq_no_such_domain_qzz",
        "observation": [["capability_gap", "self", "zzq"]], "status": "perceived"})


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    cg._CACHE.clear()
    _mint_battery(a)

    out = ra.run_cycle(a, seeds_dir=tempfile.mkdtemp(prefix="ra_demo_"))

    print("\n" + "=" * 72)
    print("THE JABBERWOCK RUNS THE SESSION'S META-PROCESS ON ITSELF")
    print("=" * 72)
    print(f"\nPERCEIVED {out['perceived']} capability gaps -> a prioritized queue.\n")
    for i, r in enumerate(out["processed"], 1):
        subject = r.get("domain") or r.get("faculty")
        verdict = (r.get("verdict") or "").split(":", 1)[0] or ("ACCEPTED" if r["accepted"] else "REJECTED")
        mark = "CLOSED" if r["status"] == "closed" else "OPEN  "
        print(f"  {i}. gap={subject!r:<34} salience={r.get('salience') or 0:.3f}")
        print(f"       KIND={r['kind']:<11} -> FILLER={r['filler']:<20} "
              f"-> outcome={r.get('outcome')}")
        print(f"       VERIFY: {verdict}  ==>  [{mark}]")
    print("\n" + "-" * 72)
    print(f"CLEAN STOP: queue drained={out['drained']}  "
          f"(iterations={out['iterations']}, no infinite loop).")
    closed = [r.get("domain") or r.get("faculty") for r in out["closed"]]
    open_ = [r.get("domain") or r.get("faculty") for r in out["open"]]
    print(f"FINAL STATE: {len(closed)} closed {closed}  |  {len(open_)} left open {open_}")
    print("            (the fake fill was rejected by #2 and honestly left OPEN.)")
    print("=" * 72)
    ok = (len(out["closed"]) == 2 and len(out["open"]) == 1 and out["drained"])
    print("GATE:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
