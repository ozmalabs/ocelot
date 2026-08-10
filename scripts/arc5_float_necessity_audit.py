"""Measure: do MBPP tasks actually need IN-FRAME floats, or only
rational parameters + a CROSS-FRAME map (pi, sqrt, division)?

Contamination note: reads test-split reference `code` for MEASUREMENT only
(the same allowance the arc-2 blocker histogram operated under). Nothing
here feeds any codebook, cue table, or learning path.
"""
import ast, json, math
from fractions import Fraction

TASKS = "tests/fixtures/mbpp/sanitized-mbpp.json"
tasks = json.load(open(TASKS))

def literal_floats(tree):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, float):
            out.append(n.value)
    return out

def names_used(tree):
    got = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute):
            got.add(n.attr)
        elif isinstance(n, ast.Name):
            got.add(n.id)
    return got

def ops_used(tree):
    got = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.BinOp):
            got.add(type(n.op).__name__)
    return got

def is_small_rational(x, max_den=64):
    if x != x or x in (float("inf"), float("-inf")):
        return False
    f = Fraction(x).limit_denominator(max_den)
    return math.isclose(float(f), x, rel_tol=1e-12, abs_tol=1e-12)

def assert_has_float(t):
    txt = " ".join(t.get("test_list", []))
    # a float appears if any numeric literal in the asserts has a '.' or math.isclose is used
    try:
        for a in t.get("test_list", []):
            tree = ast.parse(a)
            for n in ast.walk(tree):
                if isinstance(n, ast.Constant) and isinstance(n.value, float):
                    return True
            if "isclose" in a:
                return True
    except SyntaxError:
        return "." in txt
    return False

CROSS_FRAME_NAMES = {"pi", "e", "sqrt", "tau", "hypot", "sin", "cos", "tan",
                     "log", "log2", "log10", "exp", "atan", "atan2", "acos", "asin",
                     "degrees", "radians", "isclose", "pow", "ceil", "floor", "round"}

rows = []
for t in tasks:
    tid = t["task_id"]
    if not assert_has_float(t):
        continue
    try:
        tree = ast.parse(t["code"])
    except SyntaxError:
        rows.append({"task_id": tid, "class": "unparseable"}); continue
    lits = literal_floats(tree)
    nms  = names_used(tree) & CROSS_FRAME_NAMES
    ops  = ops_used(tree)
    irrational_lits = [x for x in lits if not is_small_rational(x)]
    rational_lits   = [x for x in lits if is_small_rational(x)]
    has_div  = "Div" in ops
    has_pow  = "Pow" in ops
    # classification
    if irrational_lits:
        cls = "irreducible_float_literal"
    elif nms or has_div or has_pow or rational_lits:
        cls = "rational_plus_crossframe"
    else:
        cls = "float_only_in_output"
    rows.append({"task_id": tid, "class": cls,
                 "cross_frame_names": sorted(nms),
                 "rational_literals": rational_lits,
                 "irrational_literals": irrational_lits,
                 "div": has_div, "pow": has_pow})

n = len(rows)
from collections import Counter
c = Counter(r["class"] for r in rows)
print(f"MBPP tasks whose ASSERTS involve floats: {n} / {len(tasks)}")
print()
for k, v in c.most_common():
    print(f"  {k:<28} {v:>4}  ({100*v/n:.1f}%)")
print()
irr = [r for r in rows if r["class"] == "irreducible_float_literal"]
print(f"IRREDUCIBLE in-frame floats: {len(irr)} tasks -> ids {[r['task_id'] for r in irr]}")
for r in irr[:12]:
    print(f"    {r['task_id']}: literals={r['irrational_literals']}")
print()
allnames = Counter()
for r in rows:
    for nm in r.get("cross_frame_names", []): allnames[nm] += 1
print("cross-frame maps invoked (the part that legitimately lives in Hom):")
for k, v in allnames.most_common(12):
    print(f"    {k:<10} {v}")
allrats = Counter()
for r in rows:
    for x in r.get("rational_literals", []): allrats[x] += 1
print()
print("float LITERALS in reference code, and whether each is a small rational:")
for x, v in allrats.most_common(14):
    print(f"    {x:<10} x{v:<3} -> {Fraction(x).limit_denominator(64)}")
json.dump(rows, open("/tmp/float_audit_rows.json","w"), indent=1)
