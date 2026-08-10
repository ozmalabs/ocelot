"""Migrate the cortex + test callers of the knowledge-Mt builders from
install_X_seed(s) -> load_one_seed(s, "X"), so the bespoke domains/X.py builders
become unreferenced and burnable. Only SINGLE-ARG calls are rewritten;
parameterised calls install_X_seed(s, custom_data) are LEFT (genuine test infra).

Each builder was proven load_one_seed-equivalent first (see the discovery step /
capture-to-seed). The rewrite is mechanical: swap the call + fix the import.

Run: PYTHONPATH=...:. python3 scripts/migrate_builders_to_load_one_seed.py [--apply]
"""
from __future__ import annotations
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORTEX = os.path.join(ROOT, "domains", "code_writing_cortex.py")

# (module, install fn) for the cortex's knowledge builders — all proven
# load_one_seed-equivalent (seed_id == module name).
cortex_src = open(CORTEX).read()
PAIRS = re.findall(r"from \.(\w+) import (install_\w+_seed)", cortex_src)
MODS = {mod: fn for mod, fn in PAIRS}


def migrate_text(text: str, in_cortex: bool):
    changed = False
    used_load_one = False
    for mod, fn in MODS.items():
        # single-arg call: install_X_seed( ident )  ->  load_one_seed(ident, "X")
        pat = re.compile(re.escape(fn) + r"\(\s*([^,()]+?)\s*\)")
        if pat.search(text):
            text = pat.sub(lambda m: f'load_one_seed({m.group(1)}, "{mod}")', text)
            changed = True
            used_load_one = True
        # imports
        imp_rel = re.compile(r"^from \." + re.escape(mod) + r" import " + re.escape(fn) + r"\n", re.M)
        imp_abs = re.compile(r"^(\s*)from domains\." + re.escape(mod) + r" import " + re.escape(fn) + r"\n", re.M)
        if imp_rel.search(text):
            text = imp_rel.sub("", text); changed = True
        if imp_abs.search(text):
            text = imp_abs.sub(lambda m: f"{m.group(1)}from substrate.boot_all import load_one_seed\n", text)
            changed = True; used_load_one = True
    # ensure the import exists if we introduced a call and there's no abs import yet
    if used_load_one and "from substrate.boot_all import load_one_seed" not in text:
        if in_cortex:
            text = text.replace("from __future__ import annotations\n",
                                "from __future__ import annotations\n\nfrom substrate.boot_all import load_one_seed\n", 1)
    return text, changed


def main() -> int:
    apply = "--apply" in sys.argv
    print(f"knowledge builders to migrate: {len(MODS)}")
    files = [CORTEX] + glob.glob(os.path.join(ROOT, "tests", "*.py"))
    touched = []
    # detect multi-arg (parameterised) usages we must NOT burn
    parameterised = set()
    for mod, fn in MODS.items():
        for p in files:
            if re.search(re.escape(fn) + r"\(\s*[^,()]+,\s*", open(p).read()):
                parameterised.add(mod)
    for p in files:
        src = open(p).read()
        new, changed = migrate_text(src, in_cortex=(p == CORTEX))
        if changed:
            touched.append(os.path.relpath(p, ROOT))
            if apply:
                open(p, "w").write(new)
    print(f"files {'rewritten' if apply else 'to rewrite'}: {len(touched)}")
    for t in touched:
        print("   ", t)
    if parameterised:
        print(f"\n  parameterised (multi-arg) builders LEFT (kept as infra): {sorted(parameterised)}")
    # residual references per builder after migration (dry estimate)
    print("\n  builders still referenced after migration (would block burn):")
    for mod, fn in MODS.items():
        if mod in parameterised:
            continue
        refs = sum(1 for p in glob.glob(os.path.join(ROOT, "**", "*.py"), recursive=True)
                   if p not in (CORTEX,) and re.search(r"\b" + re.escape(fn) + r"\b", open(p).read())
                   and (apply or True))
    print("  (run with --apply, then the burn script confirms which are unreferenced)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
