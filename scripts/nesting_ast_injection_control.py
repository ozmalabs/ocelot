"""M-D2 -- POSITIVE CONTROL BY INJECTION for the §13 AST gate.

"A test that can only be passed is not a test." Plant a `Count`-bounded SIZE
test into the SELECTED subtree, assert the gate goes RED, revert, assert GREEN.

AND THE INJECTION IS ITSELF VERIFIED TO LAND. At the previous rung the
supervisor's FIRST injection PASSED because it landed on a DIFFERENT
`Not>Exists>Exists` in the same rule -- the gate was right and the control was
wrong. So this harness:

  * asks the gate module ITSELF for the path it selects (`conjunct_paths`),
    never guesses a path;
  * mutates at exactly that path;
  * RE-READS the mutated seed through the SAME selector and asserts the plant
    is inside what the selector returns -- a no-op injection is a FAILURE, not
    a pass;
  * restores from an in-memory copy of the original bytes and verifies the
    file is byte-identical afterwards.

Run: python scripts/nesting_ast_injection_control.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SEED = os.path.join(ROOT, "seeds", "vision_border_ownership.json")
GATE = os.path.join(ROOT, "tests", "test_figadj_nesting_ast_migrated.py")

from tests import test_figadj_nesting_ast_migrated as gate     # noqa: E402

# A MINIMUM-SIZE THRESHOLD -- the refused fix, in its most obvious form.
SIZE_BOUND = {
    "type": "Gt",
    "a": {"type": "Count",
          "source": {"type": "Filter",
                     "source": {"type": "NodesOfType", "node_type": "Cell"},
                     "var_name": "zz",
                     "predicate": {"type": "Eq",
                                   "a": {"type": "Attr",
                                         "node": {"type": "Var", "name": "zz"},
                                         "key": "glabel"},
                                   "b": {"type": "Attr",
                                         "node": {"type": "Var", "name": "R"},
                                         "key": "glabel"}}}},
    "b": {"type": "Lit", "value": 3}}


def run_gate():
    p = subprocess.run([sys.executable, "-m", "pytest", GATE, "-q"],
                       cwd=ROOT, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip().splitlines()[-1]


def at(root, path):
    node = root
    for key in path:
        node = node[key]
    return node


def main():
    with open(SEED, "rb") as fh:
        original = fh.read()

    rc, line = run_gate()
    print(f"[baseline]  rc={rc}  {line}")
    assert rc == 0, "gate is not green BEFORE the injection -- fix that first"

    # --- ask the SELECTOR where it looks; never guess ---------------------
    seed = json.loads(original)
    paths = [p for p, _n in gate.conjunct_paths(seed)]
    assert paths, "selector found nothing to inject into"
    target = paths[0]
    print(f"[selector]  {len(paths)} sites; injecting at "
          f"bo_mint_owned.where{list(target)}")

    owned = {r["name"]: r for r in seed["rules"]}["bo_mint_owned"]
    conj = at(owned["where"], target)
    assert conj["type"] == "Or"
    body = [i for i in conj["items"] if i.get("type") != "Lt"][0]
    # plant the size bound INSIDE the selected predicate
    body["predicate"]["predicate"]["items"].append(SIZE_BOUND)

    with open(SEED, "w") as fh:
        json.dump(seed, fh, indent=1)
        fh.write("\n")

    try:
        # --- VERIFY THE PLANT LANDED INSIDE WHAT THE SELECTOR RETURNS -----
        mutated = json.loads(open(SEED).read())
        found = [n for _p, b in
                 [(p, b) for p, b in zip(
                     [p for p, _ in gate.conjunct_paths(mutated)],
                     gate._bodies(mutated))]
                 for _q, n in gate._walk(b)
                 if isinstance(n, dict) and n.get("type") == "Count"]
        landed = bool(found)
        print(f"[landing]   plant visible to the selector: {landed}")
        if not landed:
            raise SystemExit("INJECTION DID NOT LAND IN THE SELECTED SUBTREE "
                             "-- THE CONTROL IS WRONG, NOT THE GATE")

        rc_bad, line_bad = run_gate()
        print(f"[injected]  rc={rc_bad}  {line_bad}")
        if rc_bad == 0:
            raise SystemExit("GATE PASSED WITH A SIZE THRESHOLD PLANTED "
                             "-- THE GATE IS VACUOUS")
    finally:
        with open(SEED, "wb") as fh:
            fh.write(original)

    assert open(SEED, "rb").read() == original, "seed not restored byte-exactly"
    rc2, line2 = run_gate()
    print(f"[reverted]  rc={rc2}  {line2}")
    assert rc2 == 0, "gate did not go green again after revert"
    print("\nM-D2 PASS: green -> plant LANDS -> RED -> revert -> green")


if __name__ == "__main__":
    main()
