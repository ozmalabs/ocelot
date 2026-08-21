"""Census: which selectors in the seed corpus can actually rank?

An Argmax/Argmin whose `value` is a literal constant cannot discriminate its
candidates; nor can one whose `value` reads an attribute that every writer sets
to the same literal. Both degenerate to first-encountered-wins.
"""
import json, glob, collections, re

SEL = {"Argmax", "Argmin", "ArgminUnique", "ArgminRefusal"}

def walk(o, fn, path=()):
    if isinstance(o, dict):
        fn(o, path)
        for k, v in o.items(): walk(v, fn, path + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o): walk(v, fn, path + (i,))

# 1. every selector and the shape of its value term
selectors = []          # (file, rule, selector, kind, detail)
def classify(v):
    if not isinstance(v, dict): return ("missing", None)
    t = v.get("type")
    if t == "Lit": return ("literal", repr(v.get("value")))
    if t == "Attr":
        n = v.get("node", {})
        return ("attr", v.get("key"))
    return ("computed", t)

for f in sorted(glob.glob("seeds/*.json")):
    try: d = json.load(open(f))
    except Exception: continue
    if not isinstance(d, dict): continue
    for r in d.get("rules", []) or []:
        if not isinstance(r, dict): continue
        def visit(o, path, _f=f, _r=r):
            if o.get("type") in SEL and "value" in o:
                kind, detail = classify(o["value"])
                selectors.append((_f.split("/")[-1], _r.get("name"), o["type"], kind, detail))
        walk(r, visit)

# 2. for attr-ranked selectors: how is that key written across the corpus?
writes = collections.defaultdict(lambda: {"lit": set(), "derived": set()})
for f in sorted(glob.glob("seeds/*.json")):
    try: d = json.load(open(f))
    except Exception: continue
    if not isinstance(d, dict): continue
    for r in d.get("rules", []) or []:
        if not isinstance(r, dict): continue
        for e in r.get("effects", []) or []:
            if not isinstance(e, list) or not e: continue
            op = e[0]
            if op == "set_attr" and len(e) >= 4:
                key, val = e[2], e[3]
            elif op in ("add_node", "add_node_if_absent") and len(e) >= 4 and isinstance(e[3], dict):
                for key, val in e[3].items():
                    inner = val.get("__term__") if isinstance(val, dict) else None
                    bucket = "lit" if (inner is None or inner.get("type") == "Lit") else "derived"
                    writes[key][bucket].add(f"{f.split('/')[-1]}::{r.get('name')}")
                continue
            else:
                continue
            inner = val.get("__term__") if isinstance(val, dict) else None
            bucket = "lit" if (inner is None or inner.get("type") == "Lit") else "derived"
            writes[key][bucket].add(f"{f.split('/')[-1]}::{r.get('name')}")

print(f"selectors found: {len(selectors)}")
by_kind = collections.Counter(k for *_, k, _ in selectors)
print("by value shape:", dict(by_kind))

print("\n=== A. ranks by a LITERAL — cannot discriminate, by construction ===")
lits = [s for s in selectors if s[3] == "literal"]
for f, rule, sel, _, det in sorted(lits):
    print(f"  {f}::{rule}  {sel} value={det}")
print(f"  ({len(lits)} total)")

print("\n=== B. ranks by an ATTR every writer sets to a literal — cannot discriminate in practice ===")
n = 0
for f, rule, sel, kind, key in sorted(selectors):
    if kind != "attr" or key is None: continue
    w = writes.get(key)
    if not w: 
        continue
    if w["derived"]:
        continue          # some writer derives it -> can discriminate somewhere
    if not w["lit"]:
        continue
    n += 1
    print(f"  {f}::{rule}  {sel} ranks .{key}")
    for src in sorted(w['lit'])[:3]:
        print(f"      written literal-only by {src}")
print(f"  ({n} total)")

print("\n=== C. ranks by an ATTR NO rule in seeds/ ever writes ===")
n = 0
for f, rule, sel, kind, key in sorted(selectors):
    if kind != "attr" or key is None: continue
    if key in writes: continue
    n += 1
    print(f"  {f}::{rule}  {sel} ranks .{key}  (no seed writer)")
print(f"  ({n} total)")
