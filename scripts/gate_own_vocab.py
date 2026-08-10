"""THE SECOND PASS -- plant a defect built from THE GATE'S OWN VOCABULARY.

WHY THIS EXISTS, AND IT IS A CORRECTION OF MY OWN FIRST PASS
-----------------------------------------------------------
The Scope B sweep plants four generic instantiations of the invariant. That is
the right first instrument -- it is not a checklist of recorded spellings -- but
it produces a verdict of the form "INERT ON MY PLANT", and I classified which
gates that verdict was fair to using a TOKEN test (`in_scope_plants`).

**A token test for scope is the SOURCE-approximated-by-a-TOKEN error, committed
by the instrument built to find it.** Measured: `test_trope_theme.py::
test_no_python_if_else_names_a_trope` forbids an `if` branch containing a
literal from `_TROPE_NAME_STRINGS`. My plant branched on a graph read, which
that gate does not claim to catch, and it was recorded INERT. That is a FALSE
ACCUSATION of a landed gate -- the exact failure three provenance gates in this
tree committed, pointed the other way.

So the second pass reads the gate's OWN forbidden vocabulary out of the test
module -- the module-level string collections its assertion tests membership in
-- and plants a defect made of THAT. If the gate reddens, my first-pass INERT
was mine, not its.
"""
from __future__ import annotations

import ast
import os
import sys

ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from gate_inject import probe  # noqa: E402


def forbidden_vocab(test_file: str) -> list[str]:
    """Module-level string collections in the TEST file -- the hand-enumerated
    ground truth these gates are built on. Returned in definition order, which
    is deliberate: the previous rung's suite passed a probe BY LUCK because a
    fixture's definition order made a substring selector right, so order is
    never relied on for correctness here, only for reproducibility."""
    with open(os.path.join(ROOT, "tests", test_file), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    out: list[str] = []
    # MODULE LEVEL FIRST, THEN ANYWHERE. A first version read only `tree.body`
    # and returned NO-VOCAB for 22 of 25 gates -- but most of these gates build
    # their forbidden list INSIDE the test function. Reporting NO-VOCAB there
    # would have been my resolver's limit reported as the gate's property,
    # which is the same error as inferring what code selects from a count of
    # its selectors (§12.1). Measured, then widened.
    nodes = list(tree.body) + [n for n in ast.walk(tree)
                               if isinstance(n, (ast.Assign, ast.AnnAssign))]
    for n in nodes:
        if not isinstance(n, (ast.Assign, ast.AnnAssign)):
            continue
        val = n.value
        if isinstance(val, ast.Call):                      # set(...) / frozenset(...)
            val = val.args[0] if val.args else None
        if isinstance(val, (ast.List, ast.Set, ast.Tuple)):
            for el in val.elts:
                if isinstance(el, ast.Constant) and isinstance(el.value, str) \
                        and el.value.isidentifier():
                    out.append(el.value)
    return list(dict.fromkeys(out))


def probe_own_vocab(nodeid: str, target: str, word: str) -> dict:
    """Plant an `if` branch that RETURNS the forbidden literal -- the shape
    every one of these gates says it forbids."""
    src_path = os.path.join(ROOT, target)
    with open(src_path, encoding="utf-8") as fh:
        anchor = fh.read()[-60:]
    body = (f'def _gp_vocab(x):\n'
            f'    if x == 1:\n'
            f'        return "{word}"\n'
            f'    return "{word}"\n')
    return probe(nodeid, target, anchor, anchor + "\n\n" + body, marker="_gp_vocab")


if __name__ == "__main__":
    import json
    for line in sys.stdin:
        node, target = json.loads(line)
        tf = node.split("::")[0].split("/")[-1]
        vocab = forbidden_vocab(tf)
        if not vocab:
            print(f"{'NO-VOCAB':16s} {node}")
            continue
        r = probe_own_vocab(node, target, vocab[0])
        print(f"{r['verdict']:16s} {node}   (word={vocab[0]!r}, vocab n={len(vocab)})")
