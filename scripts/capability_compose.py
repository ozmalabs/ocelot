"""Autonomous capability-scope extension — the reason tower grows ITSELF.

Demonstrates: the committed GENERATOR (order-n collapse) COMPOSES new
computational capabilities the reason tower LACKS (closed-form summations),
registers them as GRAPH-RESIDENT capabilities (Capability nodes carrying the
synthesized Term-tree), and the tower DISPATCHES + COMPUTES them — by
composition, not by hand-authored Python math.

  - SYNTHESIZE each capability as a Term-tree FROM I/O EXAMPLES ONLY.
  - GENERALIZE on held-out n.
  - REGISTER graph-resident (Capability node + Term-tree as graph data).
  - VERIFY end-to-end: a bound query dispatches to the synthesized capability
    and returns the correct value; and the concept was OUT OF SCOPE before.
  - NO REGRESSION: existing capabilities still dispatch.

HONEST SCOPE: this extends the COMPUTABLE / ALGEBRAIC frontier by composition.
It does NOT reach research-math HLE — that is a knowledge / proof problem for the
reference route, not composition.

Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/capability_compose.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "runners", "dsl", "python"))

from substrate_rs import Substrate
from domains import reason
from domains.capability_compose import (
    compose_summation_capabilities, install_into_capabilities,
    HELDOUT_NS,
)


def banner(s):
    print("\n" + "=" * 76)
    print(s)
    print("=" * 76)


# The reference closed forms — used ONLY to state the expected end-to-end value
# in the verification (the generator never saw them).
REF = {
    "sum_first_n": lambda n: n * (n + 1) // 2,
    "sum_first_n_squares": lambda n: n * (n + 1) * (2 * n + 1) // 6,
    "sum_first_n_cubes": lambda n: (n * (n + 1) // 2) ** 2,
}


def main():
    s = Substrate()

    banner("BEFORE — the new concepts are OUT OF SCOPE of the reason tower")
    for concept in REF:
        present = concept in reason.CAPABILITIES
        print(f"  {concept:22} in CAPABILITIES? {present}")
    assert all(c not in reason.CAPABILITIES for c in REF), \
        "expected the summation concepts to be absent before composition"
    print(f"\n  tower size before: {len(reason.CAPABILITIES)} capabilities")

    banner("SYNTHESIZE — the generator (order-n collapse) composes each "
           "capability as a Term-tree FROM I/O EXAMPLES ONLY")
    records = compose_summation_capabilities(s)
    for concept, rec in records.items():
        print(f"\n  {concept}")
        print(f"    synthesized Term-tree : {rec['term_str']}")
        print(f"    fits spec             : {rec['fits']}  "
              f"(size {rec['size']}, explored {rec['explored']}, {rec['halt']})")
        print(f"    generalizes (held-out): {rec['generalizes']}  "
              f"on n in {list(HELDOUT_NS)}")

    banner("REGISTER — each synthesized Term-tree becomes a GRAPH-RESIDENT "
           "Capability node; the tower's dispatch dict is extended additively")
    # extend a COPY of the tower's registry (additive; never mutate the import).
    caps = dict(reason.CAPABILITIES)
    installed = install_into_capabilities(s, caps, records)
    for concept, node_id in installed.items():
        node = s.node(node_id)["attrs"]
        print(f"  {concept:22} -> Capability node {node_id}  "
              f"(kind={node['kind']}, composed_by={node['composed_by']}, "
              f"arg_role={node['arg_role']})")
        # the capability IS the stored Term-tree (graph data), not a lambda:
        assert isinstance(node["term"], dict) and "type" in node["term"]
    print(f"\n  graph-resident Capability nodes: {len(installed)}")
    print(f"  tower size after : {len(caps)} capabilities "
          f"(+{len(caps) - len(reason.CAPABILITIES)})")

    banner("VERIFY END-TO-END — a bound query for each new concept dispatches "
           "to the synthesized capability and returns the correct value")
    print(f"  {'concept':22} {'n':>4} {'dispatched':>12} {'reference':>12} "
          f"{'ok':>4}")
    print("  " + "-" * 60)
    all_ok = True
    for concept in installed:
        for n in (7, 10, 20, 100):
            # route through solve() exactly as an existing capability is routed:
            # a meaning Term {concept: {of: n}} -> caps[concept]({of: n}).
            meaning = {concept: {"of": n}}
            got = reason.solve(meaning, {}, capabilities=caps)
            want = REF[concept](n)
            ok = (got == want)
            all_ok = all_ok and ok
            print(f"  {concept:22} {n:>4} {got:>12} {want:>12} "
                  f"{'OK' if ok else 'X':>4}")
    print(f"\n  all dispatched values correct: {all_ok}")
    assert all_ok

    banner("NO REGRESSION — the existing capabilities still dispatch")
    checks = [
        ("gcd of 48,36", {"gcd": {"a": 48, "b": 36}}, 12),
        ("91 prime", {"prime": {"arg": 91}}, False),
        ("factorial 6", {"factorial": {"of": 6}}, 720),
        ("13th fibonacci", {"nth_fibonacci": {"of": 13}}, 233),
    ]
    for label, meaning, want in checks:
        got = reason.solve(meaning, {}, capabilities=caps)
        ok = (got == want)
        print(f"  {label:18} -> {got!r:>8}  (want {want!r}) {'OK' if ok else 'X'}")
        assert ok, f"REGRESSION: {label} gave {got!r}, want {want!r}"
    # and the untouched module registry is unchanged.
    assert all(c not in reason.CAPABILITIES for c in REF), \
        "the import-level CAPABILITIES must remain unmutated (additive only)"
    print("\n  reason.CAPABILITIES (module-level) unmodified — extension was "
          "additive on a copy.")

    banner("HEADLINE + HONEST SCOPE")
    grew = [c for c in installed if records[c]["generalizes"]]
    print(f"""\
  HEADLINE : the reason tower grew by {len(grew)} capabilities the AGENT
    composed — generator-synthesized (order-n collapse), graph-resident
    (Capability nodes carrying the Term-tree), dispatched + verified — with
    ZERO hand-authored math. Autonomous scope extension demonstrated.
      {', '.join(grew)}
    sum_first_n was synthesized DIRECTLY; squares + cubes were COMPOSED ON the
    just-built sum_first_n capability (the tower growing by accretion), then the
    sub-capability was INLINED so each registered capability is a single
    self-contained Term-tree over {{n}}, evaluated on the native engine.

  HONEST SCOPE : the order-n collapse composes POLYNOMIAL / algebraic structure,
    so this extends the COMPUTABLE / ALGEBRAIC frontier by composition. It does
    NOT reach research-math HLE (bordism / cohomology / open conjectures) — those
    are KNOWLEDGE / PROOF problems for the REFERENCE route (concept coverage),
    NOT composition. This is the autonomous-growth MECHANISM, not an HLE lift.

  REMAINING STEP : the NL-parse hookup. Dispatch here is by bound concept+arg
    (the same meaning-Term path solve()/answer_within route to). Recognising the
    phrase "sum of the first n squares" -> the concept needs a Frame/lexicon
    entry; that NL surface hookup is the separate, remaining step (not faked).""")


if __name__ == "__main__":
    main()
