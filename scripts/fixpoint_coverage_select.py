"""SELECTION RULE, EXECUTED. Map every script to the results/*.json it WRITES.

Rule: a script S 'produces' document D iff S contains a string literal
resolving to 'results/D' AND that literal reaches a write (open(...,'w') /
write_text / json.dump).  Found by AST, never by substring grep (PROTOCOL §12).
"""
import ast, json, pathlib, sys

ROOT = pathlib.Path(sys.argv[1]).resolve()
assert (ROOT / "VISION_PROTOCOL.md").exists(), ROOT

def literals(tree):
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            v = n.value
            if v.endswith(".json"):
                out.add(v)
    return out

rows = {}
for p in sorted((ROOT / "scripts").glob("*.py")):
    try:
        tree = ast.parse(p.read_text(errors="replace"))
    except SyntaxError:
        continue
    src = p.read_text(errors="replace")
    # does this file WRITE at all?
    writes = any(
        (isinstance(n, ast.Call) and (
            (isinstance(n.func, ast.Attribute) and n.func.attr in
             ("write_text", "dump", "write_bytes"))
            or (isinstance(n.func, ast.Name) and n.func.id == "open"
                and any(isinstance(a, ast.Constant) and isinstance(a.value, str)
                        and "w" in a.value for a in n.args))))
        for n in ast.walk(tree))
    if not writes:
        continue
    for lit in literals(tree):
        base = lit.split("/")[-1]
        if (ROOT / "results" / base).exists() or "results" in lit:
            rows.setdefault(base, set()).add(p.name)

docs = sorted(p.name for p in (ROOT / "results").glob("*.json"))
mapped = {d: sorted(rows[d]) for d in docs if d in rows}
unmapped = [d for d in docs if d not in rows]
print(json.dumps({
    "n_result_docs": len(docs),
    "n_mapped": len(mapped),
    "n_unmapped": len(unmapped),
    "mapped": mapped,
    "unmapped": unmapped,
}, indent=1))
