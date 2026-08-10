#!/usr/bin/env python3
"""jabberwock_extends_itself — SELF-IMPROVEMENT #4 demonstration: the agent extends
its OWN substrate as far as its held primitives reach, and SPECS the residual it
cannot reach.

Two capabilities, one honest boundary between them:

  COMPOSE — a CapabilityGap solvable by a COMPOSITION of held primitives becomes a
            WHOLE FACULTY: a multi-rule CHAIN the agent's composer authors + installs.
            The gap's challenge, which failed before, SUCCEEDS after the faculty runs.
            Then self_verification checks it BEFORE it is trusted.

  SPEC    — a CapabilityGap that CANNOT be expressed by held primitives becomes a
            PrimitiveRequest: an actionable spec of the primitive a host must add,
            instead of a silent wall or a faked composition.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_extends_itself.py
donkey=0 (no LLM): the composition is the agent's composer's, the verdict the held
verifier's Rust rule, the boundary a graph node.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.world_adapter import WorldAdapter
from domains import substrate_extension as se


def _line(c="-"):
    print(c * 72)


def main() -> int:
    a = WorldAdapter(seeds=())

    _line("=")
    print("SELF-IMPROVEMENT #4 — the agent extends its own substrate")
    _line("=")

    # ================================================================
    # 1. COMPOSE — a gap solvable by composition of held primitives.
    #    The gap names a needed capability: classify an incoming item,
    #    route it to a handler, mark it handled. No single held rule does
    #    this — it needs a CHAIN.
    # ================================================================
    print("\n[1] COMPOSE — a gap solvable by composition (a multi-stage need)\n")
    gap_compose = a.s.add_node("CapabilityGap", {
        "faculty": "input_handling",
        "observation": [["classify the item", "self", "input"],
                        ["route to a handler", "input", "handler"],
                        ["mark handled", "handler", "done"]],
        "status": "perceived",
    })
    print("  perceived gap:", a.s.node(gap_compose)["attrs"]["faculty"],
          "->", a.s.node(gap_compose)["attrs"]["observation"])

    # BEFORE: the gap's challenge (an unhandled item) is NOT handled.
    hub0 = a.s.add_node("Hub", {})
    it0 = a.s.add_node("Item", {"raw": "before-probe"})
    a.inner.add_edge_unchecked(hub0, "has_item", it0)
    a.inner.run_rules()
    before = a.s.node(it0)["attrs"].get("handled")
    print(f"  BEFORE (no faculty): item.handled = {before!r}  (the gap: nothing handles it)")

    res = se.extend_for_gap(a, gap_compose)
    print(f"\n  outcome: {res['outcome']}  (composition={res['composition']}, n_rules={res['n_rules']})")
    print("  the composer authored a WHOLE FACULTY — a multi-rule chain:")
    for r in res["rules"]:
        w = r.get("where")
        print(f"    - {r['name']}")
        print(f"        match:   {r['match']}")
        print(f"        where:   {w}")
        print(f"        effects: {r['effects']}")

    # AFTER: a fresh unhandled item now becomes handled by the installed chain.
    it1 = a.s.add_node("Item", {"raw": "after-probe"})
    a.inner.add_edge_unchecked(hub0, "has_item", it1)
    a.inner.run_rules()
    after = a.s.node(it1)["attrs"].get("handled")
    print(f"\n  AFTER (faculty installed): item.handled = {after!r}  (the gap's challenge now SUCCEEDS)")

    # VERIFY-BEFORE-TRUST
    v = res["verified"]
    print("\n  verify-before-trust (self_verification, discriminative control):")
    print(f"    accepted={v['accepted']}  discriminates={v['discriminates']}  "
          f"no_regression={v['no_regression']}  grounded={v['grounded']}")
    print(f"    reason: {v['reason']}")
    print(f"  => gap status: {a.s.node(gap_compose)['attrs'].get('status')}")

    # ================================================================
    # 2. VERIFY HAS TEETH — an INCOMPLETE composition that does NOT fill
    #    the gap is REJECTED (the control fails on it).
    # ================================================================
    print("\n[2] VERIFY HAS TEETH — an incomplete faculty is caught + rejected\n")
    a2 = WorldAdapter(seeds=())   # fresh agent: no complete faculty already installed
    a = a2
    gap_partial = a.s.add_node("CapabilityGap", {
        "faculty": "partial_pipe",
        "observation": [["classify the item", "self", "input"],
                        ["route to a handler", "input", "handler"]],  # NO finalize stage
        "status": "perceived",
    })
    rp = se.extend_for_gap(a, gap_partial)
    print(f"  authored {rp['n_rules']} rules (classify+route, NO finalize) — never sets handled")
    print(f"  accepted={rp['accepted']}  (rejected: the control's positive case is not handled)")
    print(f"    reason: {rp['verified']['reason']}")
    print(f"  => gap status: {a.s.node(gap_partial)['attrs'].get('status')}")

    # ================================================================
    # 3. SPEC — a gap that CANNOT be composed from held primitives.
    #    Instead of a silent wall or a fake composition, mint an actionable
    #    PrimitiveRequest (the honest autopoiesis boundary).
    # ================================================================
    print("\n[3] SPEC — a gap held primitives cannot express -> PrimitiveRequest\n")
    gap_spec = a.s.add_node("CapabilityGap", {
        "faculty": "spectrum",
        "observation": [["fourier_transform", "audio_buffer", "spectrum"],
                        ["spectral_magnitude", "spectrum", "bins"]],
        "needed_primitive": "fourier_transform",
        "inputs": ["audio_buffer"], "outputs": ["spectrum"],
        "example": "given a 1024-sample audio buffer, produce its magnitude spectrum",
        "status": "perceived",
    })
    rs = se.extend_for_gap(a, gap_spec)
    print(f"  outcome: {rs['outcome']}")
    spec = rs["spec"]
    print("  minted PrimitiveRequest (a graph node — actionable spec for a host):")
    for k in ("name", "operation", "inputs", "outputs", "example"):
        print(f"    {k:12s}: {spec[k]}")
    print(f"    {'why':12s}: {spec['why_uncomposable'][:110]}...")
    print(f"  => gap status: {a.s.node(gap_spec)['attrs'].get('status')}")

    # ================================================================
    # 4. DISCRIMINATIVE — the SAME loop routes a composable gap to a
    #    composition and a primitive-needing gap to a spec.
    # ================================================================
    print("\n[4] DISCRIMINATIVE — one loop, two honest outcomes\n")
    print(f"  composable gap        -> {res['outcome']:18s} (multi-rule faculty, verified, accepted)")
    print(f"  primitive-needing gap -> {rs['outcome']:18s} (actionable PrimitiveRequest spec)")

    print("\n  HONEST SCOPE: COMPOSE reaches exactly as far as held primitives compose")
    print("  (it authors faculties expressible as chained match/where/effect rules); it")
    print("  does NOT invent a primitive. SPEC is that boundary, made actionable. This is")
    print("  NOT full meta-circularity (authoring a primitive as graph data) — not claimed.")
    _line("=")
    ok = (res["outcome"] == "composed" and res["composition"] and res["accepted"]
          and after == 1.0 and (before is None or before != 1.0)
          and rp["accepted"] is False
          and rs["outcome"] == "primitive_request" and spec["name"] == "fourier_transform")
    print("DEMONSTRATION:", "PASS" if ok else "FAIL")
    _line("=")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
