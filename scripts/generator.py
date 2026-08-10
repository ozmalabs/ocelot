"""Brick 6 demo — THE GENERATOR, working and honestly bounded.

Synthesizes Term-trees for specs the agent has NO template/primitive for,
FROM EXAMPLES ONLY (no LLM, no hint of the answer). For each spec: prints the
examples, the synthesized term, its size, search stats, and a GENERALIZATION
test on HELD-OUT inputs (proving it found the STRUCTURE, not memorized output).

Then the HONEST BOUND: push size/arity until it explodes; report where it
becomes intractable with numbers.

Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/generator.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "runners", "dsl", "python"))

from substrate_rs import Substrate
from domains.generator import synthesize, DEFAULT_OPS


def banner(s):
    print("\n" + "=" * 70)
    print(s)
    print("=" * 70)


def show(name, true_fn, train_envs, heldout_envs, ops=DEFAULT_OPS,
         max_size=8, timeout_s=30.0, beam=None):
    s = Substrate()
    examples = [(env, true_fn(**env)) for env in train_envs]
    print(f"\n--- SPEC: {name} ---")
    print("  given ONLY these (input -> output) examples (no target structure):")
    for env, out in examples[:6]:
        print(f"    {env} -> {out}")
    if len(examples) > 6:
        print(f"    ... ({len(examples)} total)")

    r = synthesize(s, examples, ops=ops, max_size=max_size,
                   timeout_s=timeout_s, beam=beam)
    if r is None or not r["fits"]:
        print(f"  NO SOLUTION (halt={r and r['halt_reason']}, "
              f"explored={r and r['explored']}, distinct={r and r['distinct']}, "
              f"{r and r['elapsed_s']}s)")
        return r

    print(f"  SYNTHESIZED: {r['term_str']}")
    print(f"    size={r['size']}  explored={r['explored']}  "
          f"distinct-behaviours={r['distinct']}  "
          f"halt={r['halt_reason']}  time={r['elapsed_s']}s"
          + (f"  beam-bit={r['beam_bit']}" if beam else ""))

    # GENERALIZATION: evaluate the synthesized term on HELD-OUT inputs.
    ok = True
    print("  GENERALIZATION on held-out inputs (NOT in the spec):")
    for env in heldout_envs:
        got = r["term"].evaluate(env, s)
        want = true_fn(**env)
        gotn = (1 if got is True else 0) if isinstance(got, bool) else got
        match = abs(float(gotn) - float(want)) < 1e-9
        ok = ok and match
        print(f"    {env} -> {got}  (true {want})  {'OK' if match else 'MISMATCH'}")
    print(f"  GENERALIZES: {'YES — found the STRUCTURE, not memorized' if ok else 'NO'}")
    return r


def main():
    banner("BRICK 6 — THE GENERATOR (bottom-up enumerative synthesizer)")
    print("""\
  SEARCH over the production space (DSL ops), ordered by SIZE (MDL/Occam),
  pruned by OBSERVATIONAL EQUIVALENCE (one term per distinct behaviour),
  early-stopped by SATURATION. No weights, no gradient, no LLM, no templates.
  Evaluation is the existing Rust engine (substrate.evaluate).
  Inputs given to the synthesizer: EXAMPLES ONLY. The target structure is
  never shown.""")

    # ----- 1. f(x) = x*x + 1 -----
    show(
        "f(x) = x*x + 1",
        lambda x: x * x + 1,
        train_envs=[{"x": v} for v in (0, 1, 2, 3, 4)],
        heldout_envs=[{"x": v} for v in (5, 7, 10, -3, 12)],
        max_size=7,
    )

    # ----- 2. f(a,b) = max(a,b) -----
    show(
        "f(a,b) = max(a,b)",
        lambda a, b: max(a, b),
        train_envs=[{"a": a, "b": b} for (a, b) in
                    [(1, 2), (5, 3), (0, 0), (7, 9), (4, 1), (2, 8)]],
        heldout_envs=[{"a": a, "b": b} for (a, b) in
                      [(11, 4), (3, 30), (-5, -2), (100, 99)]],
        max_size=7,
    )

    # ----- 3. f(a,b,c) = a*b + c -----
    show(
        "f(a,b,c) = a*b + c",
        lambda a, b, c: a * b + c,
        train_envs=[{"a": a, "b": b, "c": c} for (a, b, c) in
                    [(1, 2, 3), (2, 3, 1), (0, 5, 4), (3, 3, 0),
                     (2, 2, 2), (4, 1, 5)]],
        heldout_envs=[{"a": a, "b": b, "c": c} for (a, b, c) in
                      [(5, 5, 5), (7, 2, 1), (10, 0, 3), (6, 6, 6)]],
        max_size=7,
    )

    # ----- 4. f(x) = |x - 2| -----
    show(
        "f(x) = |x - 2|",
        lambda x: abs(x - 2),
        train_envs=[{"x": v} for v in (-3, -1, 0, 1, 2, 3, 5)],
        heldout_envs=[{"x": v} for v in (10, -8, 6, 2, -20)],
        max_size=7,
    )

    # ----- HONEST BOUND: push until it explodes -----
    banner("HONEST TRACTABILITY BOUNDARY — push size/arity until it explodes")
    print("""\
  The bounded generator works (above). The UNBOUNDED case is the open core.
  Here we push depth (max_size) and arity and report where it becomes
  intractable: #terms explored, #distinct behaviours, wall-time.""")

    s = Substrate()

    # A deeper 2-var target: a*a + b*b  (min size 7: Plus(Times(a,a),Times(b,b)))
    print("\n--- deeper target: f(a,b) = a*a + b*b (min size 7) ---")
    ex = [({"a": a, "b": b}, a * a + b * b) for (a, b) in
          [(1, 2), (2, 3), (0, 4), (3, 1), (2, 2), (5, 0), (4, 3)]]
    for ms in (7, 8, 9):
        r = synthesize(s, ex, max_size=ms, timeout_s=60)
        tag = "SOLVED " + str(r["term_str"]) if r["fits"] else f"no-fit ({r['halt_reason']})"
        print(f"  max_size={ms}: explored={r['explored']:>9}  "
              f"distinct={r['distinct']:>6}  time={r['elapsed_s']:>7}s  -> {tag}")
        if r["fits"]:
            break

    # A target with NO small solution to force exhaustion across sizes.
    print("\n--- unsatisfiable-by-small target: f(a,b)= a*a*a + b (forces deep search) ---")
    ex2 = [({"a": a, "b": b}, a * a * a + b) for (a, b) in
           [(1, 2), (2, 1), (3, 0), (2, 3), (0, 5), (4, 1), (2, 2)]]
    for ms in (7, 8, 9, 10):
        r = synthesize(s, ex2, max_size=ms, timeout_s=90)
        tag = "SOLVED " + str(r["term_str"]) if r["fits"] else f"no-fit ({r['halt_reason']})"
        print(f"  max_size={ms}: explored={r['explored']:>10}  "
              f"distinct={r['distinct']:>6}  time={r['elapsed_s']:>7}s  -> {tag}")
        if r["fits"] or r["elapsed_s"] > 60:
            break

    # Arity blow-up: 4 variables, large op set, modest depth.
    print("\n--- arity blow-up: 4 vars (a,b,c,d), full op set ---")
    ex4 = [({"a": a, "b": b, "c": c, "d": d}, a * b + c * d) for (a, b, c, d) in
           [(1, 2, 3, 4), (2, 1, 0, 5), (3, 0, 2, 2), (1, 1, 1, 1),
            (4, 2, 1, 3), (0, 5, 2, 2), (2, 2, 2, 2)]]
    full_ops = DEFAULT_OPS + ("Min", "Gte", "Lt", "Abs", "Neg")
    for ms in (7, 8):
        r = synthesize(s, ex4, ops=full_ops, max_size=ms, timeout_s=90)
        tag = "SOLVED " + str(r["term_str"]) if r["fits"] else f"no-fit ({r['halt_reason']})"
        print(f"  max_size={ms} (ops={len(full_ops)}): explored={r['explored']:>10}  "
              f"distinct={r['distinct']:>6}  time={r['elapsed_s']:>7}s  -> {tag}")
        if r["fits"] or r["elapsed_s"] > 60:
            break

    banner("FRAMING")
    print("""\
  This IS the generator the agent flagged (brick 5): a search over the
  production space (DSL ops) selected by compression (size-ordered MDL +
  observational-equivalence collapse), early-stopped by saturation.

  GRAM mapping (weightless dual):
    MDL / size-ordered enumeration   <-  GRAM's learned reward model (LPRM)
    observational-equivalence collapse <- GRAM's latent sampling
    saturation halt                  <-  GRAM's ACT (adaptive compute) halting

  It composes NOVEL Term-trees (verified by generalization), no template,
  no LLM. A synthesized term is immediately usable (the engine evaluates it)
  and could become a named primitive via specify->emit->activate.

  HONEST BOUND: tractable for small programs (sizes ~3-7, 1-3 vars, seconds);
  beyond that the distinct-behaviour count and explored-term count grow
  combinatorially -> the unbounded generator is the open problem.""")


if __name__ == "__main__":
    main()
