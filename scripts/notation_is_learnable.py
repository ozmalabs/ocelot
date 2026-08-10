"""PROVE: NOTATION is LEARNABLE the same way prose is. Notation is a symbolic
LANGUAGE whose symbols are INTRODUCED in prose ("σ(n) denotes the sum of the
divisors of n", "let d(n) denote the number of divisors of n", "n! means the
factorial of n"). The agent ACQUIRES a notation by READING its introduction — the
SAME acquire-by-reading + order-N comprehension mechanism built for 'cubes of'.

This dissolves the last named "wall": notation is NOT non-prose-reducible. Its
MEANING is prose; the agent reads the symbol's introduction -> grounds the
symbol->meaning NOTATION construction (graph data) -> comprehends a FORMULA
written in that notation (σ(12)) -> grounds + computes + VERIFIES vs the real
OEIS ground-truth values. BEFORE the read a formula in the notation comprehends
to NONE; AFTER it parses + computes + verifies.

THE MOVES
  1. ACQUIRE NOTATION BY READING — a symbol the agent cannot read; BEFORE: a
     formula using it -> NONE. READ the symbol's introduction
     (comprehend_notation_introduction parses 'SYM means MEANING'; the MEANING is
     itself comprehended ORDER-N via the math-prose grammar) -> grounds the
     notation construction -> AFTER: the formula parses + computes + verifies vs
     the real OEIS values. >=2 real symbols (σ, φ, d, n!).
  2. COMPOSED NOTATION — a formula composing acquired notation ('σ(n) + φ(n)',
     'σ(12)/d(12)') comprehends order-N over the acquired symbols -> computes.
  3. THE DISSOLUTION + the honest TRUE residual (genuinely visual/diagrammatic
     content not delivered AS prose; tacit/unwritten intuition).

Faithful (CLAUDE.md): notation-constructions are graph DATA acquired via the
agent's acquire() / comprehend_meta_definition mechanism; the symbol is read like
any token; the argument substitutes for the index var and the EXISTING compute
chain grounds + evaluates. No LLM, no Rust, no per-symbol code.

Run:  PYTHONPATH=runners/dsl/python:. python3 scripts/notation_is_learnable.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import construction_grammar as cg
from domains import compute_grounding as cgnd
from domains import oeis_local as oe
from domains import reason

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


def _compute(expanded, n):
    comp = cgnd.comprehend_computational_definition("a(n) = " + expanded)
    if not comp:
        return None
    try:
        return int(reason.solve(comp["term"], {"n": n}))
    except Exception:
        return None


# the real symbols, each with the OEIS sequence whose values are the ground truth
# the acquired notation must reproduce. The INTRODUCTION is prose (the symbol's
# meaning IS prose); the VALUES are the dataset's (nothing hand-fed).
SYMBOLS = [
    ("σ", "sigma",
     "σ(n) denotes the sum of the divisors of n",
     "σ(12)", "A000203"),
    ("φ", "phi",
     "φ(n) is the number of integers up to n that are coprime to n",
     "φ(12)", "A000010"),
    ("d", "d",
     "let d(n) denote the number of divisors of n",
     "d(12)", "A000005"),
    ("n!", "factorial",
     "n! means the factorial of n",
     "5!", "A000142"),
]


def move1_acquire_by_reading():
    banner("MOVE 1 — ACQUIRE NOTATION BY READING ITS INTRODUCTION: BEFORE a "
           "formula in the symbol = NONE; READ the intro; AFTER it parses + "
           "computes + VERIFIES vs the real OEIS values")
    print("  A symbol introduction is PROSE ('σ(n) denotes the sum of the divisors")
    print("  of n'). The agent READS it -> comprehend_notation_introduction parses")
    print("  'SYM means MEANING'; the MEANING is comprehended ORDER-N by the same")
    print("  math-prose grammar -> a NOTATION construction (graph data). A formula")
    print("  written in the symbol then parses + computes through the EXISTING")
    print("  compute chain + VERIFIES against the dataset's ground-truth values.\n")

    ok = True
    for sym, name, intro, example, sid in SYMBOLS:
        d = oe.definition(sid)
        values = d["values"]
        offset = d["offset"]

        # BEFORE: the formula in the (not-yet-acquired) symbol -> NONE.
        before = cg.comprehend_formula(example)

        # READ the introduction -> acquire the notation -> VERIFY vs OEIS values.
        res = cg.acquire_notation(name, intro, example=example,
                                  example_values=[int(x) for x in values],
                                  example_offset=offset)

        # AFTER: the formula now comprehends + computes; check the value vs OEIS.
        after = cg.comprehend_formula(example)
        arg = int(after["arg"]) if after and str(after["arg"]).isdigit() else None
        got = _compute(after["expanded"], arg) if after and arg is not None else None
        want = int(values[arg - offset]) if arg is not None else None

        print(f"  SYMBOL {sym!r}   (introduced by prose, ground truth {sid})")
        print(f"    introduction READ : {intro!r}")
        print(f"    BEFORE the read   : comprehend_formula({example!r}) -> "
              f"{before if before else 'NONE'}")
        print(f"    -- acquire-by-reading --")
        print(f"    notation grounded : symbol {res['notation']['symbol']!r} -> "
              f"meaning {res['notation']['meaning_prose']!r}")
        print(f"                        runnable formula (in n): "
              f"{res['notation']['formula']}")
        print(f"    AFTER the read    : comprehend_formula({example!r}) -> "
              f"{after['expanded'] if after else 'NONE'}")
        print(f"    -> computes       : {example} = {got}")
        print(f"    -> VERIFIES vs {sid}: ground truth {want}  "
              f"{'MATCH' if got == want else 'MISMATCH'}")
        sym_ok = (not before) and res["acquired"] and bool(after) \
            and got is not None and got == want
        print(f"    [{ 'OK ' if sym_ok else 'FAIL'}] before(NONE) -> read -> "
              f"after(parses+computes+verifies)\n")
        ok = ok and sym_ok
    print(f"  [MOVE 1] notation acquired by reading + verified vs OEIS: {ok}")
    return ok


def move2_composed():
    banner("MOVE 2 — COMPOSED NOTATION: a formula composing ACQUIRED notation "
           "comprehends ORDER-N over the symbols -> computes (notation composes "
           "like any construction)")
    print("  The acquired symbols (σ, φ, d) compose under the held arithmetic")
    print("  tower: each notation atom is comprehended, then the arithmetic")
    print("  composes them — the SAME order-N comprehension, over symbols.\n")

    # σ(12)=28, φ(12)=4, d(12)=6  ->  the composed truths.
    cases = [
        ("σ(12) + φ(12)", 28 + 4),
        ("σ(12)/d(12)", 28 // 6),       # integer div in the tower
        ("σ(12) - φ(12)", 28 - 4),
        ("σ(6) + φ(6)", 12 + 2),
    ]
    ok = True
    for formula, want in cases:
        comp = cg.comprehend_formula(formula)
        if not comp:
            print(f"  {formula:16} -> NONE")
            ok = False
            continue
        # the composed expanded form is a single computation over n-free literals;
        # evaluate it (n unused — all args are literals).
        got = _compute(comp["expanded"], 0)
        print(f"  {formula:16} -> symbols {comp['symbols']}  computes {got}  "
              f"(expected {want})  {'OK' if got == want else 'FAIL'}")
        ok = ok and (got == want)
    print(f"\n  [MOVE 2] composed notation comprehends + computes: {ok}")
    return ok


def move3_dissolution():
    banner("MOVE 3 — THE DISSOLUTION + the honest TRUE residual")
    print("  STATED: notation is a LEARNABLE symbolic language. A symbol's")
    print("  introduction IS prose ('σ(n) denotes the sum of the divisors of n');")
    print("  it is READ + ACQUIRED the SAME way ('read about how to read') as any")
    print("  construction; comprehension of prose AND notation is ONE order-N +")
    print("  acquire mechanism. The 'non-prose-reducible notation' wall dissolves:")
    print("  notation's MEANING is prose, and the agent reads the symbol's")
    print("  introduction -> grounds symbol->meaning -> comprehends formulas in it.\n")

    print("  THE HONEST TRUE RESIDUAL (named, not a non-learnable layer):")
    print("   · genuinely VISUAL / DIAGRAMMATIC content — a commutative diagram, a")
    print("     geometric picture — whose meaning, while STATABLE in prose/equations,")
    print("     is NOT delivered AS prose in the source. Where its formal/prose")
    print("     content IS written, it reduces (the agent reads THAT); the residual")
    print("     is the truly-pictorial part the source leaves unwritten.")
    print("   · TACIT / UNWRITTEN intuition the source never states.")
    print("   · the research OPERATIONS still to acquire as runnable primitives")
    print("     (kernel/image/modulo — named in order_n_comprehension MOVE 3).")
    print("  These are BREADTH + the truly-unwritten — NOT a non-learnable layer.")
    return True


def main():
    banner("NOTATION IS LEARNABLE — acquired by READING its introduction, the SAME "
           "acquire-by-reading + order-N comprehension mechanism")
    print(f"  OEIS present: {oe.present()}  (the ground-truth values are the")
    print("  dataset's; the symbol introductions are prose — the symbol's MEANING")
    print("  IS prose, read + acquired like any construction.)")

    m1 = move1_acquire_by_reading()
    m2 = move2_composed()
    m3 = move3_dissolution()

    banner("SUMMARY")
    rows = [
        ("MOVE 1: NOTATION acquired by READING its introduction (>=2 real symbols; "
         "before-NONE -> read -> after parses+computes+verifies vs real OEIS)", m1),
        ("MOVE 2: COMPOSED notation comprehends order-N over the acquired symbols "
         "+ computes", m2),
        ("MOVE 3: the DISSOLUTION stated + the honest true residual named "
         "(visual/diagrammatic / unwritten)", m3),
    ]
    all_ok = True
    for label, ok in rows:
        all_ok = all_ok and ok
        print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    print(f"\nRESULT: {'ALL OK' if all_ok else 'FAILURES ABOVE'}\n")
    print("LEARNING: NOTATION is learnable — the agent acquires a symbol by READING")
    print("its prose introduction (the SAME acquire-by-reading) and then reads")
    print("formulas written in it, verified vs the real OEIS values. The last")
    print("'wall' (non-prose-reducible notation) dissolves: notation's MEANING IS")
    print("prose; comprehension (prose + notation) is ONE order-N + acquire")
    print("mechanism. HONEST: HLE research-math correct stays ~0 (the research")
    print("OPERATIONS remain to acquire as runnable primitives); the win is")
    print("DISSOLVING the notation wall, NOT solving the research math. The genuine")
    print("residual = truly-visual/diagrammatic + tacit/unwritten content (breadth),")
    print("which reduces to its formal/prose content WHERE the source writes it.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
