"""uniqueness_world — the world-adapter surface for RUNG L1b (the UNIQUENESS GATE).

Mechanical I/O ONLY (PROTOCOL §0 / CLAUDE.md). This file contains exactly two
things: a BLIND WRITE of the gate's flag, and a READBACK of the `uq_*` attributes
the seed rules wrote. There is no conditional over graph state, no threshold, no
comparison, and no decision — the gate's entire content (count the candidates
inside the verdict bound; admit iff unique, refuse iff not) lives in the
`vision_uniqueness` seed rules.

It is a SEPARATE file from `lighting_world` on purpose: rung L1's adapter belongs to
rung L1 and is not this rung's to edit (PROTOCOL §11.4).

Note what `verdict()` deliberately does NOT do: it does not combine `l1_recognized`
with an ambiguity marker to derive an answer. That combination WOULD be a decision,
and it is made in the graph — `uq_admit` / `uq_refuse_ambiguous` partition the
claimed surfaces and write a single definitive `uq_status`. This function reads that
one attribute back.
"""
from __future__ import annotations


def set_flag(s, *, uniqueness: float) -> None:
    """Blind-write the gate flag on every UniquenessParams node. No read, no branch."""
    for p in s.nodes("UniquenessParams"):
        s.set_attr(p, "uniqueness", float(uniqueness))


def verdict(s, nid: int) -> dict:
    """The GATED recognition readback for one ObjSurface (pure mechanical query).

    `uq_status` is written by the seed rules and is one of:
      * `uq_recognized` — L1 claimed it AND the winner was unique within the bound;
      * `uq_ambiguous`  — L1 claimed it AND ≥2 candidates lay inside the bound, so
                          the gate refused rather than let `Argmin` pick silently;
      * `""` (absent)   — the gate did not fire, because L1 itself never claimed
                          this surface (it refused, or the flag is off). Kept
                          DISTINGUISHABLE from an explicit refusal so "refused" and
                          "never ran" are never confused (§1.1's dead-arm lesson).

    `uq_ncand` is how many candidates were inside the bound — the ambiguity made
    into a POSITIVE datum rather than an absence.
    """
    a = s.node(nid)["attrs"]
    return {
        "uq_recognized": int(round(float(a.get("uq_recognized", 0.0)))),
        "uq_id": int(round(float(a.get("uq_id", -1.0)))),
        "uq_status": a.get("uq_status", ""),
        "uq_ncand": int(round(float(a.get("uq_ncand", 0.0)))),
    }
