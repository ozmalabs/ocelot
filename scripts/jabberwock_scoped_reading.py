"""jabberwock_scoped_reading — the SCOPED, RESIDUAL-PRESERVING, BACKTRACKING
collapse, demonstrated end-to-end.

The reading stack is greedy bottom-up (commit each layer's winner, discard the
residual). This driver (domains/reading_scope.py) holds the SENTENCE scope's
lattice open, judges coherence at the assembled scope, and BACKTRACKS to a LOWER
re-decode (a different SEGMENTATION at order N, a different CONSTRUCTION at order
1) when the assembly does not cohere — then COMMITS by SUPPRESS + RETAIN (Sturt
2007 / Christianson 2001) into a salience-ordered bounded buffer, REACTIVATES the
retained trace on a later non-sequitur, and falls back to a cold RE-READ FROM
SOURCE only when the trace was evicted.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_scoped_reading.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import reading_scope as rs               # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _rule(t):
    print("\n" + "=" * 72 + "\n" + t + "\n" + "=" * 72)


def main():
    dl.warm_wordnet("en")
    s, node = boot_core()
    ag = _Agent(s, node)

    _rule("HEADLINE — BACKTRACK TO A LOWER RE-DECODE (not a word swap)")
    sent = "miners extract ore furnaces smelt metal"
    print("sentence:", repr(sent))
    r = rs.read_scope(ag, sent)
    for L in r["ladder"]:
        tag = L["layer"] + (" #%d" % L["revisit"] if "revisit" in L else "")
        print("  [%-24s] incoh=%.2f  %s" % (tag, L["incoherence"], L["predications"]))
    print("  GREEDY (commit-lower) is INCOHERENT: a clause folded into the object.")
    print("  BACKTRACK pulled a LOWER SEGMENTATION from the residual -> COHERENT:")
    print("    committed:", r["predications"])
    print("    same words, %d clauses vs greedy's %d — a lower re-decode, not a word swap."
          % (len(r["segmentation"]), 1))

    _rule("COMMIT = SUPPRESS + RETAIN (Sturt/Christianson — not a hard flush)")
    gist = ag.s.node(r["gist_node"])["attrs"]
    trace = ag.s.node(r["trace_node"])["attrs"]
    print("  GIST (stable lossy summary, NO lattice):", repr(gist["summary"]))
    print("  gist fields:", sorted(gist.keys()), "-> no 'alternatives'/'residual'")
    print("  RetainedTrace: suppressed=%.0f resident=%.0f evicted=%.0f activation=%.2f salience=%.2f"
          % (trace["suppressed"], trace["resident"], trace["evicted"],
             trace["activation"], trace["salience"]))
    print("  -> the %d abandoned alternatives are RETAINED (demoted), not purged."
          % r["n_retained_alternatives"])

    _rule("RE-READ ON NON-SEQUITUR — reactivate the retained trace (R1 -> R2)")
    s2, n2 = boot_core()
    ag2 = _Agent(s2, n2)
    para = "miners extract ore metal smelters process alloys. smelters melt iron."
    print("paragraph:", repr(para))
    out = rs.read_paragraph(ag2, para, trace_capacity=8)
    for c in out["commits"]:
        print("  COMMIT %-52r -> %s" % (c["sentence"], c["gist"]))
    ra = out["reanalyses"][0]
    print("  NON-SEQUITUR: 'smelters melt iron' shares no referent with A's gist.")
    print("  path:", ra["path"], "(decode cost %d)" % ra["reactivate_decode_cost"])
    print("    R1 (committed) :", ra["r1"], "refs", ra["r1_referents"])
    print("    R2 (reactivated):", ra["r2"], "refs", ra["r2_referents"])
    print("    -> reactivation re-collapsed A (not B) to share 'smelters' with B.")

    _rule("COLD MISS — evicted trace forces a RE-READ FROM SOURCE (costlier)")
    s3, n3 = boot_core()
    ag3 = _Agent(s3, n3)
    recA = rs.read_scope(ag3, "miners extract ore metal smelters process alloys")
    rs.enforce_trace_buffer(ag3, 0)                 # wrap A out of the ring
    b = rs.read_scope(ag3, "smelters melt iron")
    trig = {"sentence": "smelters melt iron", "predications": b["predications"]}
    res = rs._reanalyse(ag3, recA, trig, 8)
    print("  A's trace EVICTED (ring wrapped) -> reactivation is a cold miss.")
    print("  path:", res["path"])
    print("  reactivate cost=%d  |  re-read-from-source cost=%d  (source is costlier)"
          % (res["reactivate_decode_cost"], res["reread_decode_cost"]))
    print("  re-read result:", res["r2"])

    _rule("SALIENCE-ORDERED BOUNDED BUFFER — lowest-salience evicts first")
    s4, n4 = boot_core()
    ag4 = _Agent(s4, n4)
    clean = rs.read_scope(ag4, "smelters melt iron")           # greedy coheres -> salience 0
    hard = rs.read_scope(ag4, "miners extract ore furnaces smelt metal")  # backtracked -> high
    print("  clean commit salience=%.2f  hard(backtracked) commit salience=%.2f"
          % (clean["salience"], hard["salience"]))
    rs.enforce_trace_buffer(ag4, 1)                 # capacity 1
    print("  capacity=1 -> retained:",
          "HARD" if rs._trace_resident(ag4.s, hard["trace_node"]) else "-",
          "| evicted:", "CLEAN" if not rs._trace_resident(ag4.s, clean["trace_node"]) else "-")
    print("  (surprising/ambiguous commits are retained longer — the residual=surprise")
    print("   currency is the retention key, mirroring the Rust forget_over_budget loop.)")

    _rule("HOLD-OPEN — no alternative coheres -> flagged, not force-collapsed")
    s5, n5 = boot_core()
    ag5 = _Agent(s5, n5)
    hr = rs.read_scope(ag5, "glorp flonk zibble wug")
    print("  'glorp flonk zibble wug' -> committed=%s held_open=%s best_incoh=%.2f"
          % (hr["committed"], hr["held_open"], hr["best_incoherence"]))
    print("  (eager commit then revise; the bounded residual exhausted with nothing")
    print("   coherent, so the scope is HELD OPEN — not force-collapsed.)")

    print("\nDONE.\n")


if __name__ == "__main__":
    main()
